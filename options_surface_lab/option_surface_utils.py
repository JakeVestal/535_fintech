"""
Shared utilities for the options surface lab.

Parses LSEG/Refinitiv expired-option history (TRDPRC_1 + MID_PRICE) into a
tidy long table. No synthetic fallback — if the LSEG cache is missing or
malformed, we raise so the failure is visible rather than being silently
papered over with fake data.
"""

from __future__ import annotations

import datetime as dt
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import griddata


# OPRA month codes used in the RIC constructor in the original pipeline
CALL_MONTHS = {chr(ord("A") + i): i + 1 for i in range(12)}
PUT_MONTHS = {chr(ord("M") + i): i + 1 for i in range(12)}
MONTH_CODE_TO_CP = {**{k: "C" for k in CALL_MONTHS}, **{k: "P" for k in PUT_MONTHS}}
MONTH_CODE_TO_MONTH = {**CALL_MONTHS, **PUT_MONTHS}

# UUUUA1502600650.U   or   UUUUA1502600650.U^A26
RIC_RE = re.compile(
    r"^(?P<root>[A-Z]+)(?P<code>[A-X])(?P<day>\d{2})(?P<year>\d{2})"
    r"(?P<strike>\d{5})(?:\.U)?(?:\^[A-X]\d{2})?$",
    re.IGNORECASE,
)


def parse_option_ric(ric: str) -> dict | None:
    """Extract root, put/call, expiry, strike from an expired OPRA-style RIC."""
    text = str(ric).strip()
    m = RIC_RE.match(text)
    if not m:
        return None
    code = m.group("code").upper()
    month = MONTH_CODE_TO_MONTH.get(code)
    cp = MONTH_CODE_TO_CP.get(code)
    if month is None or cp is None:
        return None
    year = 2000 + int(m.group("year"))
    day = int(m.group("day"))
    try:
        expiry = dt.date(year, month, day)
    except ValueError:
        return None
    strike = int(m.group("strike")) / 100.0
    return {
        "ric": text,
        "root": m.group("root").upper(),
        "cp": cp,
        "expiry": expiry,
        "strike": strike,
        "month_code": code,
    }


def flatten_lseg_options(df_options: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse LSEG get_history output into a tidy table.

    LSEG may return:
      - MultiIndex columns (RIC, field)
      - MultiIndex columns (field, RIC)
      - flat columns that are just RICs (single field — not expected here)
    """
    if df_options is None or df_options.empty:
        return pd.DataFrame(
            columns=["date", "ric", "field", "value", "root", "cp", "expiry", "strike"]
        )

    frame = df_options.copy()
    if not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index)

    rows = []
    cols = frame.columns

    if isinstance(cols, pd.MultiIndex):
        # Detect which level is the field name.
        level_values = [set(map(str, cols.get_level_values(i))) for i in range(cols.nlevels)]
        field_level = None
        for i, vals in enumerate(level_values):
            upper = {v.upper() for v in vals}
            if upper & {"TRDPRC_1", "MID_PRICE", "BID", "ASK"}:
                field_level = i
                break
        if field_level is None:
            raise ValueError(
                f"flatten_lseg_options: cannot identify field level in columns "
                f"{cols.tolist()[:6]}... — expected one level to contain TRDPRC_1 / MID_PRICE."
            )
        ric_level = 0 if field_level != 0 else 1

        for col in cols:
            ric = str(col[ric_level])
            field = str(col[field_level]).upper()
            series = frame[col].dropna()
            parsed = parse_option_ric(ric)
            if parsed is None:
                continue
            for ts, val in series.items():
                try:
                    num = float(val)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(num):
                    continue
                rows.append(
                    {
                        "date": pd.Timestamp(ts).normalize(),
                        "ric": ric,
                        "field": field,
                        "value": num,
                        **parsed,
                    }
                )
    else:
        # Flat columns are only unambiguous when the caller encoded the field
        # into the column label as "RIC | FIELD". A bare RIC column has no way
        # to know whether the values are trades, mids, or something else — we
        # refuse to guess (defaulting silently to TRDPRC_1 would corrupt the
        # SETTLE-vs-trade comparison in a way the app cannot detect).
        for col in cols:
            label = str(col)
            if "|" not in label:
                raise ValueError(
                    f"flatten_lseg_options: flat column {label!r} has no 'RIC | FIELD' "
                    f"separator. Refusing to guess the field. Ensure the pull returned "
                    f"a MultiIndex (RIC, Field) frame."
                )
            ric, field = [p.strip() for p in label.split("|", 1)]
            parsed = parse_option_ric(ric)
            if parsed is None:
                continue
            series = frame[col].dropna()
            for ts, val in series.items():
                try:
                    num = float(val)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(num):
                    continue
                rows.append(
                    {
                        "date": pd.Timestamp(ts).normalize(),
                        "ric": ric,
                        "field": str(field).upper(),
                        "value": num,
                        **parsed,
                    }
                )

    tidy = pd.DataFrame(rows)
    if tidy.empty:
        return tidy
    tidy["date"] = pd.to_datetime(tidy["date"])
    tidy["expiry"] = pd.to_datetime(tidy["expiry"])
    tidy["dte"] = (tidy["expiry"] - tidy["date"]).dt.days
    tidy = tidy[tidy["dte"] >= 0].copy()
    return tidy


def attach_underlying(tidy: pd.DataFrame, df_stock: pd.DataFrame) -> pd.DataFrame:
    """Join each option row to that day's underlying close (TRDPRC_1).

    If a date exists in the options frame but not in the stock frame we
    raise, rather than forward-filling from an earlier session — a silent
    gap-fill would corrupt the moneyness axis with stale spots.
    """
    if tidy.empty:
        tidy["spot"] = np.nan
        tidy["moneyness"] = np.nan
        return tidy
    if df_stock is None or df_stock.empty:
        raise ValueError("attach_underlying: stock frame is empty; cannot attach spot.")

    stock = df_stock.copy()
    if not isinstance(stock.index, pd.DatetimeIndex):
        stock.index = pd.to_datetime(stock.index)
    if "TRDPRC_1" not in stock.columns:
        raise ValueError(
            f"attach_underlying: stock frame has no TRDPRC_1 column (got "
            f"{list(stock.columns)}). Refusing to substitute another column silently."
        )
    spot = stock["TRDPRC_1"].astype(float)
    spot.index = pd.DatetimeIndex(spot.index).normalize()
    tidy = tidy.copy()
    spot_map = spot.to_dict()
    tidy["spot"] = tidy["date"].map(lambda d: spot_map.get(pd.Timestamp(d).normalize(), np.nan))
    missing = tidy["spot"].isna()
    if missing.any():
        gap_dates = sorted({str(d.date()) for d in tidy.loc[missing, "date"]})
        raise ValueError(
            f"attach_underlying: {int(missing.sum())} option rows have no matching "
            f"stock TRDPRC_1 on their date. Sample gaps: {gap_dates[:5]}. "
            f"Refusing to fill from a prior session."
        )
    tidy["moneyness"] = tidy["strike"] / tidy["spot"]
    return tidy


def pivot_trade_mid(tidy: pd.DataFrame) -> pd.DataFrame:
    """One row per (date, ric) with TRDPRC_1 and MID_PRICE side by side."""
    if tidy.empty:
        return tidy
    keep = tidy[tidy["field"].isin(["TRDPRC_1", "MID_PRICE"])].copy()
    if keep.empty:
        raise ValueError(
            f"pivot_trade_mid: tidy frame has no TRDPRC_1 / MID_PRICE rows "
            f"(fields present: {sorted(tidy['field'].unique().tolist())})"
        )
    idx_cols = ["date", "ric", "root", "cp", "expiry", "strike", "dte", "spot", "moneyness"]
    idx_cols = [c for c in idx_cols if c in keep.columns]
    wide = (
        keep.pivot_table(index=idx_cols, columns="field", values="value", aggfunc="last")
        .reset_index()
    )
    wide.columns.name = None
    if "TRDPRC_1" not in wide.columns:
        wide["TRDPRC_1"] = np.nan
    if "MID_PRICE" not in wide.columns:
        wide["MID_PRICE"] = np.nan
    wide["has_trade"] = wide["TRDPRC_1"].notna()
    wide["has_mid"] = wide["MID_PRICE"].notna()
    wide["abs_diff"] = (wide["MID_PRICE"] - wide["TRDPRC_1"]).abs()
    wide["rel_diff"] = wide["abs_diff"] / wide["MID_PRICE"].replace(0, np.nan)
    return wide


def surface_grid(points: pd.DataFrame, value_col: str, n_strike: int = 40, n_dte: int = 30):
    """
    Interpolate a sparse cloud onto a regular grid for a Plotly Surface.
    Returns None if there are too few points, or if the cloud is degenerate
    (all points on one strike or one expiry — Qhull cannot triangulate a
    flat 2D input).
    """
    cloud = points.dropna(subset=["strike", "dte", value_col])
    if len(cloud) < 8:
        return None
    x = cloud["strike"].to_numpy(float)
    y = cloud["dte"].to_numpy(float)
    z = cloud[value_col].to_numpy(float)
    # Need spread in both axes to triangulate. If one axis is flat (e.g. all
    # points are on a single expiry, so all DTE values are equal), Delaunay
    # cannot build an initial simplex and griddata crashes.
    if np.ptp(x) < 1e-9 or np.ptp(y) < 1e-9:
        return None
    xi = np.linspace(x.min(), x.max(), n_strike)
    yi = np.linspace(max(0, y.min()), y.max(), n_dte)
    XX, YY = np.meshgrid(xi, yi)
    try:
        ZZ = griddata((x, y), z, (XX, YY), method="linear")
    except Exception:
        return None
    # leave holes as None so Plotly does not invent a sheet over empty wings
    return {"x": xi, "y": yi, "z": ZZ}


def summarize_sparsity(wide: pd.DataFrame) -> dict:
    """Classroom-facing counts that make the mid ≠ last-trade point."""
    if wide is None or wide.empty:
        return {
            "n_quotes": 0,
            "n_trade_only": 0,
            "n_mid_only": 0,
            "n_both": 0,
            "pct_mid_no_trade": 0.0,
            "median_abs_diff": None,
            "median_rel_diff_pct": None,
            "n_dates": 0,
            "n_series": 0,
        }
    n = len(wide)
    both = wide["has_trade"] & wide["has_mid"]
    mid_only = wide["has_mid"] & ~wide["has_trade"]
    trade_only = wide["has_trade"] & ~wide["has_mid"]
    diffs = wide.loc[both, "abs_diff"].dropna()
    rel = wide.loc[both, "rel_diff"].dropna()
    return {
        "n_quotes": int(n),
        "n_trade_only": int(trade_only.sum()),
        "n_mid_only": int(mid_only.sum()),
        "n_both": int(both.sum()),
        "pct_mid_no_trade": float(100.0 * mid_only.mean()) if n else 0.0,
        "median_abs_diff": float(diffs.median()) if len(diffs) else None,
        "median_rel_diff_pct": float(100.0 * rel.median()) if len(rel) else None,
        "n_dates": int(wide["date"].nunique()),
        "n_series": int(wide["ric"].nunique()),
    }


def load_payload(cache_file: str = "option_pipeline_data.pkl") -> dict:
    """Load the LSEG cache. No synthetic fallback — a missing cache raises."""
    path = Path(cache_file)
    if not path.exists():
        raise FileNotFoundError(
            f"{cache_file} not found. The lab does not synthesize a fake panel; "
            f"pull data from LSEG with the pipeline in options_surface_app.py "
            f"(requires LSEG Workspace running) and try again."
        )
    with path.open("rb") as f:
        payload = pickle.load(f)
    return payload
