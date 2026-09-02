#!/usr/bin/env python3
"""Export Options Surface Lab as a static GitHub Pages site.

Reflex `reflex export --frontend-only` still expects a Python backend for
every switch and date change. GitHub Pages has no backend, so this script
does not ship the Reflex runtime.

It loads option_pipeline_data.pkl, builds the same figures the Reflex app
shows, and writes a self-contained Plotly site:

    gh-pages/
      index.html      # UI + Plotly.js
      data.js         # precomputed figure JSON
      .nojekyll
      README.md

Toggles (MID / last trade / interpolated sheet, C vs P, as-of date) run
entirely in the browser. There is no LSEG call.

Usage
-----
    python export_gh_pages.py
    python export_gh_pages.py --pickle option_pipeline_data.pkl --out gh-pages
    python export_gh_pages.py --base-path /my-repo/

Then push `gh-pages/` to the `gh-pages` branch, or set Pages to serve that
folder. For a project site the pages URL is
https://<user>.github.io/<repo>/ — pass --base-path /<repo>/ if assets 404.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_json

CACHE_DEFAULTS = [
    Path("option_pipeline_data.pkl"),
    Path(__file__).resolve().parent / "option_pipeline_data.pkl",
]

_RIC_BODY = re.compile(
    r"^(?P<root>[A-Z]+)(?P<body>[A-X])(?P<dd>\d{2})(?P<yy>\d{2})(?P<strike>\d{5})"
    r"(?:\.[A-Z])?(?:\^[A-L]\d{2})?$",
    re.IGNORECASE,
)
_CALL_LETTERS = "ABCDEFGHIJKL"
_PUT_LETTERS = "MNOPQRSTUVWX"

DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    font=dict(color="#e6edf3", family="Inter, system-ui, sans-serif"),
    margin=dict(l=40, r=20, t=50, b=40),
)


def _as_naive_midnight(values) -> pd.DatetimeIndex:
    if isinstance(values, pd.Series):
        s = pd.to_datetime(values, errors="coerce")
        tz = getattr(getattr(s, "dt", None), "tz", None)
        if tz is not None:
            s = s.dt.tz_convert("UTC").dt.tz_localize(None)
        return pd.DatetimeIndex(s).normalize()
    idx = pd.Index(values)
    parsed = pd.to_datetime(idx, errors="coerce")
    if not isinstance(parsed, pd.DatetimeIndex):
        parsed = pd.DatetimeIndex(parsed)
    if parsed.tz is not None:
        parsed = parsed.tz_convert("UTC").tz_localize(None)
    return parsed.normalize()


def cp_from_ric(ric: str) -> str | None:
    if not isinstance(ric, str):
        return None
    m = _RIC_BODY.match(ric.strip().upper())
    if not m:
        return None
    letter = m.group("body")
    if letter in _CALL_LETTERS:
        return "C"
    if letter in _PUT_LETTERS:
        return "P"
    return None


def parse_ric(ric: str) -> dict:
    m = _RIC_BODY.match(str(ric).strip().upper())
    if not m:
        return {"cp": None, "strike": np.nan, "expiry": pd.NaT}
    letter = m.group("body")
    cp = "C" if letter in _CALL_LETTERS else "P" if letter in _PUT_LETTERS else None
    month = (_CALL_LETTERS.find(letter) + 1) if letter in _CALL_LETTERS else (
        _PUT_LETTERS.find(letter) + 1
    )
    year = 2000 + int(m.group("yy"))
    day = int(m.group("dd"))
    try:
        expiry = pd.Timestamp(year=year, month=month, day=day)
    except ValueError:
        expiry = pd.NaT
    return {
        "cp": cp,
        "strike": int(m.group("strike")) / 100.0,
        "expiry": expiry,
    }


def flat_stock(stock: pd.DataFrame) -> pd.DataFrame:
    out = stock.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [str(c).upper() for c in out.columns.get_level_values(-1)]
    else:
        out.columns = [str(c).upper() for c in out.columns]
    out.index = _as_naive_midnight(out.index)
    out.index.name = "date"
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def add_dte(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "date" not in out.columns or "expiry" not in out.columns:
        raise SystemExit(f"Cannot compute dte; columns={list(out.columns)}")
    exp = pd.to_datetime(out["expiry"], errors="coerce")
    asof = pd.to_datetime(out["date"], errors="coerce")
    out["dte"] = (exp.dt.normalize() - asof.dt.normalize()).dt.days
    out["DTE"] = out["dte"]
    out["days_to_expiry"] = out["dte"]
    return decorate_quotes(out)


def decorate_quotes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "MID_PRICE" in out.columns:
        out["has_mid"] = out["MID_PRICE"].notna()
        out["mid"] = out["MID_PRICE"]
    if "TRDPRC_1" in out.columns:
        out["has_trade"] = out["TRDPRC_1"].notna()
        out["has_trd"] = out["has_trade"]
        out["has_print"] = out["has_trade"]
        out["trade"] = out["TRDPRC_1"]
        out["last"] = out["TRDPRC_1"]
    if "has_mid" in out.columns and "has_trade" in out.columns:
        out["has_both"] = out["has_mid"] & out["has_trade"]
        out["mid_only"] = out["has_mid"] & ~out["has_trade"]
    return out


def flatten_options(options: pd.DataFrame) -> pd.DataFrame:
    df = options.copy()
    df.index = _as_naive_midnight(df.index)
    df.index.name = "date"
    pieces = []
    pairs = list(df.columns) if isinstance(df.columns, pd.MultiIndex) else [
        (c, "VALUE") for c in df.columns
    ]
    for ric, field in pairs:
        col = df.loc[:, (ric, field)] if isinstance(df.columns, pd.MultiIndex) else df[ric]
        ser = pd.to_numeric(col, errors="coerce").dropna()
        if ser.empty:
            continue
        piece = ser.rename("value").to_frame()
        piece["ric"] = str(ric)
        piece["field"] = str(field).upper()
        pieces.append(piece.reset_index())
    if not pieces:
        raise SystemExit("Pickle has no option quotes to export.")
    long = pd.concat(pieces, ignore_index=True)
    if "Date" in long.columns and "date" not in long.columns:
        long = long.rename(columns={"Date": "date"})
    long["date"] = _as_naive_midnight(long["date"])
    parsed = long["ric"].map(parse_ric)
    long["cp"] = parsed.map(lambda d: d["cp"])
    long["strike"] = parsed.map(lambda d: d["strike"])
    long["expiry"] = parsed.map(lambda d: d["expiry"])
    return add_dte(long)


def attach_spot(tidy: pd.DataFrame, stock: pd.DataFrame) -> pd.DataFrame:
    spot_col = "TRDPRC_1" if "TRDPRC_1" in stock.columns else stock.columns[-1]
    spot = pd.to_numeric(stock[spot_col], errors="coerce")
    spot.index = _as_naive_midnight(spot.index)
    out = tidy.copy()
    out["date"] = _as_naive_midnight(out["date"])
    mapped = out["date"].map(spot)
    keep = mapped.notna()
    if not bool(keep.all()):
        dropped = int((~keep).sum())
        print(f"[export] dropping {dropped} option rows with no same-day stock print")
        out = out.loc[keep].copy()
        mapped = out["date"].map(spot)
    out["underlying"] = mapped.to_numpy()
    out["spot"] = out["underlying"]
    return out


def pivot_wide(tidy: pd.DataFrame) -> pd.DataFrame:
    keys = [c for c in ("date", "ric", "cp", "strike", "expiry", "underlying", "spot") if c in tidy.columns]
    wide = tidy.pivot_table(index=keys, columns="field", values="value", aggfunc="last")
    wide.columns = [str(c).upper() for c in wide.columns]
    return add_dte(wide.reset_index())


def require_package_plots():
    try:
        from fintech535.fintech535_plots import (
            candlestick_figure,
            coverage_heatmap,
            mid_vs_trade_figure,
            price_surface_figure,
        )
    except Exception as e:
        raise SystemExit(
            f"fintech535.fintech535_plots is required for export (no fallback figures): {e}"
        ) from e
    return {
        "candlestick": candlestick_figure,
        "surface": price_surface_figure,
        "compare": mid_vs_trade_figure,
        "heat": coverage_heatmap,
    }


def _call(fn, *args, **kwargs):
    """Pass only kwargs the course helper actually accepts."""
    import inspect
    try:
        params = inspect.signature(fn).parameters
        accepts_var = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        if not accepts_var:
            kwargs = {k: v for k, v in kwargs.items() if k in params}
    except (TypeError, ValueError):
        pass
    return fn(*args, **kwargs)


def stamp_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Give the course plotters every name they have used for the same fields."""
    out = df.copy()
    if "underlying" in out.columns and "spot" not in out.columns:
        out["spot"] = out["underlying"]
    if "spot" in out.columns and "underlying" not in out.columns:
        out["underlying"] = out["spot"]
    if "cp" in out.columns:
        out["right"] = out["cp"]
        out["option_type"] = out["cp"]
    if "date" in out.columns:
        out["date"] = _as_naive_midnight(out["date"])
        out["Date"] = out["date"]
    return add_dte(out)


def fig_candlestick(stock: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure(
        go.Candlestick(
            x=stock.index,
            open=stock.get("OPEN_PRC"),
            high=stock.get("HIGH_1"),
            low=stock.get("LOW_1"),
            close=stock.get("TRDPRC_1"),
            name=ticker,
            increasing_line_color="#00ffcc",
            decreasing_line_color="#ff0055",
        )
    )
    fig.update_layout(title=f"{ticker} daily", xaxis_rangeslider_visible=False, **DARK)
    return fig


def _dte(row) -> float:
    if pd.isna(row.get("expiry")):
        return np.nan
    return (pd.Timestamp(row["expiry"]) - pd.Timestamp(row["date"])).days


def fig_surface(wide: pd.DataFrame, asof: str, cp: str, ticker: str) -> go.Figure:
    sl = wide[(wide["date"] == pd.Timestamp(asof)) & (wide["cp"] == cp)].copy()
    sl["dte"] = sl.apply(_dte, axis=1)
    fig = go.Figure()
    if sl.empty:
        fig.update_layout(title=f"{ticker} {asof} {cp} — no quotes", **DARK)
        return fig

    if "MID_PRICE" in sl.columns:
        m = sl.dropna(subset=["MID_PRICE", "strike", "dte"])
        fig.add_trace(
            go.Scatter3d(
                x=m["strike"], y=m["dte"], z=m["MID_PRICE"],
                mode="markers", name="MID_PRICE",
                marker=dict(size=4, color="#00ffcc"),
            )
        )
    if "TRDPRC_1" in sl.columns:
        t = sl.dropna(subset=["TRDPRC_1", "strike", "dte"])
        fig.add_trace(
            go.Scatter3d(
                x=t["strike"], y=t["dte"], z=t["TRDPRC_1"],
                mode="markers", name="TRDPRC_1",
                marker=dict(size=5, color="#ff0055", symbol="diamond"),
            )
        )
    # Interpolated sheet on the mid grid — teaching artifact, not a market.
    if "MID_PRICE" in sl.columns:
        grid = sl.dropna(subset=["MID_PRICE", "strike", "dte"])
        if len(grid) >= 4:
            strikes = np.sort(grid["strike"].unique())
            dtes = np.sort(grid["dte"].unique())
            Z = np.full((len(dtes), len(strikes)), np.nan)
            lookup = {(r.dte, r.strike): r.MID_PRICE for r in grid.itertuples()}
            for i, d in enumerate(dtes):
                for j, k in enumerate(strikes):
                    Z[i, j] = lookup.get((d, k), np.nan)
            # fill holes along strike then dte so the sheet is visible
            Z = pd.DataFrame(Z).interpolate(axis=1, limit_direction="both").to_numpy()
            Z = pd.DataFrame(Z).interpolate(axis=0, limit_direction="both").to_numpy()
            fig.add_trace(
                go.Surface(
                    x=strikes, y=dtes, z=Z, name="Interpolated sheet",
                    opacity=0.35, showscale=False,
                    colorscale=[[0, "#30363d"], [1, "#00ffcc"]],
                )
            )
    fig.update_layout(
        title=f"{ticker} {cp} surface  {asof}",
        scene=dict(
            xaxis_title="strike",
            yaxis_title="DTE",
            zaxis_title="price",
            bgcolor="#0d1117",
        ),
        **DARK,
    )
    return fig


def fig_compare(wide: pd.DataFrame, asof: str, ticker: str) -> go.Figure:
    sl = wide[wide["date"] == pd.Timestamp(asof)].copy()
    fig = go.Figure()
    if sl.empty or "MID_PRICE" not in sl.columns or "TRDPRC_1" not in sl.columns:
        fig.update_layout(title=f"{ticker} mid vs trade  {asof}", **DARK)
        return fig
    both = sl.dropna(subset=["MID_PRICE", "TRDPRC_1"])
    fig.add_trace(
        go.Scatter(
            x=both["MID_PRICE"], y=both["TRDPRC_1"],
            mode="markers", name="quotes",
            marker=dict(color="#00ffcc", size=8),
        )
    )
    if len(both):
        lo = float(min(both["MID_PRICE"].min(), both["TRDPRC_1"].min()))
        hi = float(max(both["MID_PRICE"].max(), both["TRDPRC_1"].max()))
        fig.add_trace(
            go.Scatter(
                x=[lo, hi], y=[lo, hi], mode="lines", name="y = x",
                line=dict(color="#8b949e", dash="dash"),
            )
        )
    fig.update_layout(
        title=f"{ticker} MID_PRICE vs TRDPRC_1  {asof}",
        xaxis_title="MID_PRICE",
        yaxis_title="TRDPRC_1",
        **DARK,
    )
    return fig


def fig_heat(wide: pd.DataFrame, asof: str, cp: str, field: str) -> go.Figure:
    sl = wide[(wide["date"] == pd.Timestamp(asof)) & (wide["cp"] == cp)].copy()
    sl["dte"] = sl.apply(_dte, axis=1)
    fig = go.Figure()
    if sl.empty or field not in sl.columns:
        fig.update_layout(title=f"{field} coverage {asof} {cp}", **DARK)
        return fig
    sl["hit"] = sl[field].notna().astype(float)
    piv = sl.pivot_table(index="dte", columns="strike", values="hit", aggfunc="max")
    fig.add_trace(
        go.Heatmap(
            z=piv.values, x=list(piv.columns), y=list(piv.index),
            colorscale=[[0, "#161b22"], [1, "#00ffcc"]],
            showscale=False,
        )
    )
    fig.update_layout(
        title=f"{field} coverage  {asof}  {cp}",
        xaxis_title="strike",
        yaxis_title="DTE",
        **DARK,
    )
    return fig


def summarize(sl: pd.DataFrame) -> dict:
    n = int(len(sl))
    has_mid = sl["MID_PRICE"].notna() if "MID_PRICE" in sl.columns else pd.Series(False, index=sl.index)
    has_trd = sl["TRDPRC_1"].notna() if "TRDPRC_1" in sl.columns else pd.Series(False, index=sl.index)
    n_mid_only = int((has_mid & ~has_trd).sum())
    n_both = int((has_mid & has_trd).sum())
    n_quotes = int((has_mid | has_trd).sum())
    pct = 100.0 * n_mid_only / n_quotes if n_quotes else 0.0
    if n_both:
        diff = (sl.loc[has_mid & has_trd, "MID_PRICE"] - sl.loc[has_mid & has_trd, "TRDPRC_1"]).abs()
        med = float(diff.median())
        mid = sl.loc[has_mid & has_trd, "MID_PRICE"].replace(0, np.nan)
        rel = float((diff / mid).median() * 100) if mid.notna().any() else None
        gap = f"${med:.3f}" + (f" ({rel:.1f}%)" if rel is not None and np.isfinite(rel) else "")
    else:
        gap = "n/a"
    return {
        "n_quotes": n_quotes,
        "n_mid_only": n_mid_only,
        "n_both": n_both,
        "pct_mid_no_trade": f"{pct:.0f}%",
        "median_gap": gap,
        "n_rows": n,
    }


def fig_to_obj(fig: go.Figure) -> dict:
    return json.loads(to_json(fig, pretty=False, engine="json"))


def load_payload(pickle_path: Path) -> dict:
    with pickle_path.open("rb") as f:
        return pickle.load(f)


def build_bundle(payload: dict, plots: dict) -> dict:
    ticker = payload.get("ticker", "UUUU")
    stock = flat_stock(payload["stock"])
    tidy = attach_spot(flatten_options(payload["options"]), stock)
    wide = add_dte(stamp_aliases(pivot_wide(tidy)))
    if "dte" not in wide.columns:
        raise SystemExit(f"dte missing after stamp; columns={list(wide.columns)}")
    if wide.empty:
        raise SystemExit("Pickle flattened to zero option rows.")
    dates = sorted({pd.Timestamp(d).strftime("%Y-%m-%d") for d in wide["date"]})
    print(f"[export] {ticker}: {wide['ric'].nunique()} RICs, {len(dates)} dates, "
          f"cols={list(wide.columns)}")

    stock_fig = _call(plots["candlestick"], stock, ticker)

    panels = {}
    for asof in dates:
        for cp in ("C", "P"):
            sl = wide[(wide["date"] == pd.Timestamp(asof)) & (wide["cp"] == cp)]
            sl_all = wide[wide["date"] == pd.Timestamp(asof)]
            try:
                surface = _call(
                    plots["surface"], wide, asof,
                    cp=cp, right=cp,
                    show_trade=True, show_mid=True, show_interpolated=True,
                    ticker=ticker,
                )
                compare = _call(plots["compare"], wide, asof, ticker=ticker)
                heat_mid = _call(plots["heat"], wide, asof, cp=cp, field="MID_PRICE")
                heat_trd = _call(plots["heat"], wide, asof, cp=cp, field="TRDPRC_1")
            except Exception as e:
                raise SystemExit(
                    f"Course plotter failed on {asof} {cp}: {type(e).__name__}: {e}\n"
                    f"wide columns: {list(wide.columns)}"
                ) from e
            panels[f"{asof}|{cp}"] = {
                "stats": summarize(sl if len(sl) else sl_all),
                "surface": fig_to_obj(surface),
                "compare": fig_to_obj(compare),
                "heat_mid": fig_to_obj(heat_mid),
                "heat_trade": fig_to_obj(heat_trd),
            }

    return {
        "ticker": ticker,
        "fetched_at": payload.get("fetched_at", ""),
        "option_count": int(wide["ric"].nunique()) if len(wide) else 0,
        "dates": dates,
        "default_asof": dates[0] if dates else "",
        "stock": fig_to_obj(stock_fig),
        "panels": panels,
    }


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Options Surface Lab</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <script src="__BASE__data.js"></script>
  <style>
    :root { color-scheme: dark; }
    * { box-sizing: border-box; }
    body {
      margin: 0; font-family: Inter, system-ui, sans-serif;
      background: #0d1117; color: #e6edf3; padding: 2rem;
    }
    h1 { color: #00ffcc; letter-spacing: 2px; font-weight: 700; margin: 0; }
    .row { display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
    .metric {
      background: #161b22; border: 1px solid #30363d; border-radius: 8px;
      padding: 1rem 1.25rem; min-width: 9rem;
    }
    .metric .lbl { color: #8b949e; font-size: 13px; }
    .metric .val { color: #00ffcc; font-size: 22px; font-weight: 700; }
    .pane {
      background: #161b22; border: 1px solid #30363d; border-radius: 8px;
      padding: 0.75rem; margin-top: 1rem;
    }
    .heats { display: flex; gap: 0.75rem; }
    .heats .pane { flex: 1; min-width: 280px; }
    label { color: #8b949e; font-size: 13px; margin-right: 0.35rem; }
    select, input[type=date] {
      background: #161b22; color: #e6edf3; border: 1px solid #30363d;
      border-radius: 6px; padding: 0.35rem 0.5rem;
    }
    .note { color: #8b949e; font-size: 13px; margin: 0.75rem 0; }
    .badge { background: #0e7490; color: white; border-radius: 999px; padding: 0.2rem 0.7rem; font-size: 12px; }
    @media (max-width: 800px) { .heats { flex-direction: column; } }
  </style>
</head>
<body>
  <div class="row" style="margin-bottom:1rem">
    <h1>OPTIONS SURFACE LAB</h1>
    <span style="flex:1"></span>
    <span class="badge" id="status">static snapshot</span>
  </div>
  <p class="note" id="note"></p>
  <div class="row" id="metrics"></div>
  <div class="pane"><div id="fig_stock" style="height:420px"></div></div>
  <div class="row" style="margin-top:1rem">
    <label>As-of date</label>
    <input type="date" id="asof"/>
    <label>Right</label>
    <select id="cp"><option value="C">C</option><option value="P">P</option></select>
    <label><input type="checkbox" id="show_mid" checked/> <span style="color:#00ffcc">MID_PRICE</span></label>
    <label><input type="checkbox" id="show_trade" checked/> <span style="color:#ff0055">TRDPRC_1</span></label>
    <label><input type="checkbox" id="show_sheet" checked/> Interpolated sheet</label>
  </div>
  <p class="note">
    Cyan = closing NBBO mid (MID_PRICE). Magenta = last trade (TRDPRC_1).
    The translucent sheet is linearly interpolated and will invent prices in
    strikes that never printed. Turn it off.
  </p>
  <div class="pane"><div id="fig_surface" style="height:640px"></div></div>
  <div class="pane"><div id="fig_compare" style="height:460px"></div></div>
  <div class="heats">
    <div class="pane"><div id="fig_heat_mid" style="height:380px"></div></div>
    <div class="pane"><div id="fig_heat_trade" style="height:380px"></div></div>
  </div>
<script>
const D = window.SURFACE_LAB;
const $ = (id) => document.getElementById(id);

function metric(label, value) {
  return `<div class="metric"><div class="lbl">${label}</div><div class="val">${value}</div></div>`;
}

function snapDate(value) {
  const dates = D.dates;
  if (dates.includes(value)) return value;
  const t = Date.parse(value);
  let best = dates[0], bestAbs = Infinity;
  for (const d of dates) {
    const a = Math.abs(Date.parse(d) - t);
    if (a < bestAbs) { bestAbs = a; best = d; }
  }
  return best;
}

function restyleSurface(fig) {
  if (!fig || !fig.data) return fig;
  const mid = $("show_mid").checked;
  const trd = $("show_trade").checked;
  const sheet = $("show_sheet").checked;
  fig.data.forEach((tr) => {
    const n = (tr.name || "").toUpperCase();
    if (n.includes("MID")) tr.visible = mid;
    else if (n.includes("TRD") || n.includes("TRADE")) tr.visible = trd;
    else if (n.includes("SHEET") || n.includes("INTERPOL") || tr.type === "surface") tr.visible = sheet;
  });
  return fig;
}

function render() {
  const asof = snapDate($("asof").value);
  if ($("asof").value !== asof) $("asof").value = asof;
  const cp = $("cp").value;
  const key = asof + "|" + cp;
  const panel = D.panels[key];
  const stats = panel ? panel.stats : {};
  $("note").textContent = "Static snapshot from " + (D.fetched_at || "cache") + " — no LSEG live pull.";
  $("metrics").innerHTML = [
    metric("Underlying", D.ticker),
    metric("Option series", D.option_count),
    metric("Quotes on as-of date", stats.n_quotes ?? "—"),
    metric("Mid with no print", stats.n_mid_only ?? "—"),
    metric("Median |mid − trade|", stats.median_gap ?? "—"),
  ].join("");
  Plotly.react("fig_stock", D.stock.data, D.stock.layout, {responsive: true, displaylogo: false});
  if (!panel) return;
  Plotly.react("fig_surface", restyleSurface(panel.surface).data, panel.surface.layout, {responsive: true, displaylogo: false});
  Plotly.react("fig_compare", panel.compare.data, panel.compare.layout, {responsive: true, displaylogo: false});
  Plotly.react("fig_heat_mid", panel.heat_mid.data, panel.heat_mid.layout, {responsive: true, displaylogo: false});
  Plotly.react("fig_heat_trade", panel.heat_trade.data, panel.heat_trade.layout, {responsive: true, displaylogo: false});
}

$("asof").min = D.dates[0];
$("asof").max = D.dates[D.dates.length - 1];
$("asof").value = D.default_asof;
["asof","cp","show_mid","show_trade","show_sheet"].forEach((id) => $(id).addEventListener("change", render));
render();
</script>
</body>
</html>
"""


WORKFLOW = """name: pages
on:
  workflow_dispatch:
  push:
    branches: [main]
    paths:
      - gh-pages/**
      - option_pipeline_data.pkl
      - export_gh_pages.py
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.pub.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: gh-pages
      - id: pub
        uses: actions/deploy-pages@v4
"""


README = """# Options Surface Lab — static snapshot

This folder is a GitHub Pages site generated by `export_gh_pages.py`.
It is **not** a live Reflex app. There is no LSEG session and no Python
backend. Date / right / trace toggles run in the browser against figures
baked in from `option_pipeline_data.pkl`.

## Publish

1. Run `python export_gh_pages.py` from the project root (pickle must exist).
2. Repo Settings → Pages → Source: GitHub Actions, **or**
   deploy the `gh-pages/` folder as the Pages artifact.
3. For a project site (`https://USER.github.io/REPO/`) rebuild with
   `python export_gh_pages.py --base-path /REPO/`.

Do not run Jekyll on this folder (`.nojekyll` is already here).
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Export Options Surface Lab for GitHub Pages")
    p.add_argument("--pickle", type=Path, default=None, help="Path to option_pipeline_data.pkl")
    p.add_argument("--out", type=Path, default=Path("gh-pages"), help="Output directory")
    p.add_argument(
        "--base-path",
        default="/",
        help="URL prefix for project Pages, e.g. /options-surface-lab/",
    )
    p.add_argument("--workflow", action="store_true", help="Also write .github/workflows/pages.yml")
    args = p.parse_args(argv)

    pickle_path = args.pickle
    if pickle_path is None:
        pickle_path = next((c for c in CACHE_DEFAULTS if c.exists()), None)
    if pickle_path is None or not pickle_path.exists():
        print("No option_pipeline_data.pkl found. Run the Reflex app once to cache data.", file=sys.stderr)
        return 2

    print(f"[export] loading {pickle_path}")
    payload = load_payload(pickle_path)
    plots = require_package_plots()
    bundle = build_bundle(payload, plots)

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "README.md").write_text(README, encoding="utf-8")
    js = "window.SURFACE_LAB = " + json.dumps(bundle, default=str) + ";\n"
    (out / "data.js").write_text(js, encoding="utf-8")

    base = args.base_path
    if not base.endswith("/"):
        base += "/"
    html = INDEX_HTML.replace("__BASE__", "" if base == "/" else base)
    (out / "index.html").write_text(html, encoding="utf-8")

    if args.workflow:
        wf = Path(".github/workflows/pages.yml")
        wf.parent.mkdir(parents=True, exist_ok=True)
        wf.write_text(WORKFLOW, encoding="utf-8")
        print(f"[export] wrote {wf}")

    n_panels = len(bundle["panels"])
    print(f"[export] {bundle['ticker']}  {len(bundle['dates'])} dates  {n_panels} panels")
    print(f"[export] wrote {out}/index.html  {out}/data.js")
    print("[export] Reflex frontend-only export is NOT used: switches need a backend.")
    print("[export] Push this folder to GitHub Pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())