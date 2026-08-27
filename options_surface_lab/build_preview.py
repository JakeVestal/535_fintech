"""Generate a standalone HTML preview of the surface lab (no Reflex required)."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from option_surface_plots import (
    candlestick_figure,
    coverage_heatmap,
    price_surface_figure,
    settle_vs_trade_figure,
)
from option_surface_utils import (
    attach_underlying,
    flatten_lseg_options,
    load_payload,
    summarize_sparsity,
    pivot_trade_settle,
)


def main() -> Path:
    payload = load_payload("option_pipeline_data.pkl")
    tidy = flatten_lseg_options(payload["options"])
    tidy = attach_underlying(tidy, payload["stock"])
    wide = pivot_trade_settle(tidy)
    ticker = payload.get("ticker", "UUUU")

    asof = wide["date"].max() if len(wide) else None
    stats = summarize_sparsity(wide[wide["date"] == asof] if asof is not None else wide)

    fig_px = price_surface_figure(wide, asof, cp="C", ticker=ticker)
    fig_px_p = price_surface_figure(wide, asof, cp="P", ticker=ticker)
    fig_cmp = settle_vs_trade_figure(wide, asof, ticker=ticker)
    fig_hm_s = coverage_heatmap(wide, asof, cp="C", field="SETTLE")
    fig_hm_t = coverage_heatmap(wide, asof, cp="C", field="TRDPRC_1")
    fig_cs = candlestick_figure(payload["stock"], ticker)

    out = Path(__file__).resolve().parent / "options_surface_preview.html"

    med = stats["median_abs_diff"]
    med_txt = "n/a" if med is None else f"${med:.3f}"
    rel = stats["median_rel_diff_pct"]
    rel_txt = "n/a" if rel is None else f"{rel:.1f}%"

    banner = f"""
    <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
                background:#0d1117; color:#e6edf3; padding:28px 32px 8px 32px;">
      <div style="color:#00ffcc; letter-spacing:2px; font-size:22px; font-weight:700;">
        OPTIONS SURFACE LAB — PREVIEW
      </div>
      <p style="color:#8b949e; max-width:820px; line-height:1.5;">
        As-of <span style="color:#e6edf3;">{pd.Timestamp(asof).date() if asof is not None else 'n/a'}</span>
        for <span style="color:#39d353;">{ticker}</span>
        {'(synthetic panel — drop option_pipeline_data.pkl next to this file to use your LSEG pull)'
          if payload.get('synthetic') else '(loaded from option_pipeline_data.pkl)'}.
        Cyan marks are exchange <b>SETTLE</b>. Magenta diamonds are <b>TRDPRC_1</b> prints.
        The interpolated sheet is a convenience, not a market.
      </p>
      <div style="display:flex; gap:16px; flex-wrap:wrap; margin:12px 0 8px 0;">
        {_card('Series on this date', stats['n_quotes'])}
        {_card('Settle, no print', f"{stats['n_settle_only']} ({stats['pct_settle_no_trade']:.0f}%)")}
        {_card('Both settle &amp; print', stats['n_both'])}
        {_card('Median |settle − trade|', med_txt)}
        {_card('Median relative gap', rel_txt)}
      </div>
    </div>
    """

    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Options Surface Lab Preview</title>",
        "<style>body{margin:0;background:#0d1117;}</style></head><body>",
        banner,
    ]
    for fig in (fig_cs, fig_px, fig_px_p, fig_cmp, fig_hm_s, fig_hm_t):
        parts.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    parts.append("</body></html>")
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {out}  asof={asof}  quotes={stats['n_quotes']}  synthetic={payload.get('synthetic')}")
    return out


def _card(label: str, value) -> str:
    return (
        "<div style='background:#161b22;border:1px solid #30363d;border-radius:8px;"
        "padding:12px 16px;min-width:140px;'>"
        f"<div style='color:#8b949e;font-size:12px;'>{label}</div>"
        f"<div style='color:#00ffcc;font-size:22px;font-weight:700;'>{value}</div>"
        "</div>"
    )


if __name__ == "__main__":
    main()
