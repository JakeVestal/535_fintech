"""Plotly figures for the options surface lab."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from option_surface_utils import surface_grid


DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    font=dict(color="#e6edf3", family="monospace"),
)


def candlestick_figure(df_stock: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df_stock.index,
                open=df_stock["OPEN_PRC"],
                high=df_stock["HIGH_1"],
                low=df_stock["LOW_1"],
                close=df_stock["TRDPRC_1"],
                increasing_line_color="#00ffcc",
                increasing_fillcolor="#00ffcc",
                decreasing_line_color="#ff0055",
                decreasing_fillcolor="#ff0055",
                name=ticker,
            )
        ]
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3", family="Inter, system-ui, sans-serif", size=12),
        title=dict(
            text=f"{ticker}  ·  underlying OHLC",
            font=dict(size=16),
            x=0.02,
            xanchor="left",
        ),
        xaxis=dict(gridcolor="#30363d", rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor="#30363d", title="Price ($)"),
        margin=dict(l=48, r=24, t=56, b=40),
        height=420,
        annotations=[
            dict(
                text="Close field is TRDPRC_1 (last trade) — not an option settle",
                xref="paper",
                yref="paper",
                x=0.0,
                y=1.02,
                showarrow=False,
                font=dict(size=11, color="#8b949e"),
            )
        ],
    )
    return fig


def _slice_wide(wide: pd.DataFrame, asof, cp: str) -> pd.DataFrame:
    sl = wide.copy()
    if asof is not None and len(sl):
        asof_ts = pd.Timestamp(asof).normalize()
        sl = sl[sl["date"] == asof_ts]
    if cp in {"C", "P"}:
        sl = sl[sl["cp"] == cp]
    return sl


def price_surface_figure(
    wide: pd.DataFrame,
    asof,
    cp: str = "C",
    show_trade: bool = True,
    show_settle: bool = True,
    show_interpolated: bool = True,
    ticker: str = "UUUU",
) -> go.Figure:
    sl = _slice_wide(wide, asof, cp)
    fig = go.Figure()

    if sl.empty:
        fig.update_layout(
            **DARK,
            title=dict(
                text="No quotes on this date / filter",
                font=dict(size=16, family="Inter, system-ui, sans-serif"),
            ),
            height=620,
        )
        return fig

    spot = sl["spot"].dropna()
    spot_val = float(spot.median()) if len(spot) else None
    cp_label = {"C": "Calls", "P": "Puts", "B": "Puts + Calls"}.get(cp, cp)
    asof_txt = str(pd.Timestamp(asof).date()) if asof is not None else "all dates"
    spot_txt = f"  ·  spot ${spot_val:.2f}" if spot_val is not None else ""

    def _axis(title: str) -> dict:
        return dict(
            title=dict(text=title, font=dict(size=12, family="Inter, system-ui, sans-serif")),
            backgroundcolor="#161b22",
            gridcolor="#30363d",
            showbackground=True,
            zeroline=False,
            tickfont=dict(size=10, family="Inter, system-ui, sans-serif"),
        )

    if show_settle and sl["SETTLE"].notna().any():
        s = sl.dropna(subset=["SETTLE"])
        fig.add_trace(
            go.Scatter3d(
                x=s["strike"],
                y=s["dte"],
                z=s["SETTLE"],
                mode="markers",
                name="SETTLE",
                marker=dict(
                    size=4,
                    color="#00ffcc",
                    opacity=0.85,
                    symbol="circle",
                    line=dict(width=0),
                ),
                hovertemplate=(
                    "<b>SETTLE</b> $%{z:.3f}<br>K=%{x:.2f}<br>DTE=%{y}"
                    "<br>%{customdata[0]}<extra></extra>"
                ),
                customdata=np.stack([s["ric"].astype(str), s["cp"].astype(str)], axis=1),
            )
        )
        if show_interpolated:
            grid = surface_grid(s, "SETTLE")
            if grid is not None:
                fig.add_trace(
                    go.Surface(
                        x=grid["x"],
                        y=grid["y"],
                        z=grid["z"],
                        name="Interpolated sheet",
                        colorscale=[[0, "#0d3d38"], [0.5, "#1a7a6e"], [1, "#00ffcc"]],
                        opacity=0.28,
                        showscale=False,
                        hoverinfo="skip",
                        contours=dict(
                            x=dict(show=False),
                            y=dict(show=False),
                            z=dict(show=False),
                        ),
                    )
                )

    if show_trade and sl["TRDPRC_1"].notna().any():
        t = sl.dropna(subset=["TRDPRC_1"])
        fig.add_trace(
            go.Scatter3d(
                x=t["strike"],
                y=t["dte"],
                z=t["TRDPRC_1"],
                mode="markers",
                name="TRDPRC_1",
                marker=dict(
                    size=6,
                    color="#ff0055",
                    opacity=1.0,
                    symbol="diamond",
                    line=dict(width=0.5, color="#ff6b9d"),
                ),
                hovertemplate=(
                    "<b>TRDPRC_1</b> $%{z:.3f}<br>K=%{x:.2f}<br>DTE=%{y}"
                    "<br>%{customdata[0]}<extra></extra>"
                ),
                customdata=np.stack([t["ric"].astype(str), t["cp"].astype(str)], axis=1),
            )
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3", family="Inter, system-ui, sans-serif", size=12),
        title=dict(
            text=f"{ticker}  {cp_label}  ·  {asof_txt}{spot_txt}",
            font=dict(size=16, color="#e6edf3", family="Inter, system-ui, sans-serif"),
            x=0.02,
            xanchor="left",
            y=0.98,
            yanchor="top",
        ),
        scene=dict(
            xaxis=_axis("Strike ($)"),
            # near-dated in front: reverse DTE so 0 sits toward the viewer
            yaxis={**_axis("Days to expiry"), "autorange": "reversed"},
            zaxis=_axis("Option price ($)"),
            bgcolor="#0d1117",
            aspectmode="manual",
            aspectratio=dict(x=1.15, y=1.0, z=0.7),
            camera=dict(
                eye=dict(x=1.55, y=-1.45, z=0.85),
                center=dict(x=0, y=0, z=-0.05),
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            x=1.0,
            xanchor="right",
            bgcolor="rgba(13,17,23,0.7)",
            bordercolor="#30363d",
            borderwidth=1,
            font=dict(size=11),
            itemsizing="constant",
        ),
        height=640,
        margin=dict(l=10, r=10, t=56, b=10),
        annotations=[
            dict(
                text="Cyan = exchange SETTLE &nbsp;·&nbsp; Magenta = last trade (TRDPRC_1) &nbsp;·&nbsp; Sheet is interpolated, not a market",
                xref="paper",
                yref="paper",
                x=0.0,
                y=1.0,
                xanchor="left",
                yanchor="bottom",
                showarrow=False,
                font=dict(size=11, color="#8b949e", family="Inter, system-ui, sans-serif"),
            )
        ],
    )
    return fig


def settle_vs_trade_figure(wide: pd.DataFrame, asof=None, ticker: str = "UUUU") -> go.Figure:
    sl = wide.copy()
    if asof is not None and len(sl):
        sl = sl[sl["date"] == pd.Timestamp(asof).normalize()]
    both = sl.dropna(subset=["TRDPRC_1", "SETTLE"])
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("SETTLE vs TRDPRC_1", "Who actually printed?"),
        horizontal_spacing=0.12,
        vertical_spacing=0.08,
    )

    if len(both):
        color = both["cp"].map({"C": "#00ffcc", "P": "#d2a8ff"})
        fig.add_trace(
            go.Scatter(
                x=both["TRDPRC_1"],
                y=both["SETTLE"],
                mode="markers",
                marker=dict(size=7, color=color, opacity=0.85),
                customdata=np.stack(
                    [
                        both["ric"].astype(str),
                        both["strike"],
                        both["dte"],
                        both["cp"],
                    ],
                    axis=1,
                ),
                hovertemplate=(
                    "trade $%{x:.3f}  settle $%{y:.3f}"
                    "<br>%{customdata[3]} K=%{customdata[1]} DTE=%{customdata[2]}"
                    "<br>%{customdata[0]}<extra></extra>"
                ),
                name="Paired quotes",
                showlegend=False,
            ),
            row=1,
            col=1,
        )
        lo = float(min(both["TRDPRC_1"].min(), both["SETTLE"].min()))
        hi = float(max(both["TRDPRC_1"].max(), both["SETTLE"].max()))
        pad = (hi - lo) * 0.06 if hi > lo else 0.05
        fig.add_trace(
            go.Scatter(
                x=[lo - pad, hi + pad],
                y=[lo - pad, hi + pad],
                mode="lines",
                line=dict(color="#8b949e", dash="dash", width=1),
                name="y = x",
                showlegend=True,
            ),
            row=1,
            col=1,
        )
        fig.update_xaxes(range=[lo - pad, hi + pad], row=1, col=1)
        fig.update_yaxes(range=[lo - pad, hi + pad], row=1, col=1)

    n_settle_only = int((sl["has_settle"] & ~sl["has_trade"]).sum())
    n_both = int((sl["has_settle"] & sl["has_trade"]).sum())
    n_trade_only = int((sl["has_trade"] & ~sl["has_settle"]).sum())
    ymax = max(n_settle_only, n_both, n_trade_only, 1)
    fig.add_trace(
        go.Bar(
            x=["Settle only", "Both", "Print only"],
            y=[n_settle_only, n_both, n_trade_only],
            marker_color=["#00ffcc", "#58a6ff", "#ff0055"],
            showlegend=False,
            text=[n_settle_only, n_both, n_trade_only],
            textposition="inside",
            textfont=dict(color="#0d1117", size=12),
            cliponaxis=False,
        ),
        row=1,
        col=2,
    )
    fig.update_yaxes(range=[0, ymax * 1.18], row=1, col=2)

    fig.update_xaxes(
        title_text="TRDPRC_1 ($)",
        row=1,
        col=1,
        gridcolor="#30363d",
        zeroline=False,
        title_font=dict(size=12),
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        title_text="SETTLE ($)",
        row=1,
        col=1,
        gridcolor="#30363d",
        zeroline=False,
        title_font=dict(size=12),
        tickfont=dict(size=11),
    )
    fig.update_xaxes(title_text=None, row=1, col=2, tickfont=dict(size=11))
    fig.update_yaxes(
        title_text="Series count",
        row=1,
        col=2,
        gridcolor="#30363d",
        title_font=dict(size=12),
        tickfont=dict(size=11),
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3", family="Inter, system-ui, sans-serif", size=12),
        title=dict(
            text=f"{ticker}  ·  last trade is not the settle",
            font=dict(size=16, family="Inter, system-ui, sans-serif"),
            x=0.02,
            xanchor="left",
            y=0.98,
            yanchor="top",
        ),
        height=460,
        margin=dict(l=56, r=24, t=72, b=52),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            x=0.0,
            xanchor="left",
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        annotations=[
            dict(
                text="Off-diagonal = mark ≠ print &nbsp;·&nbsp; Cyan calls, purple puts &nbsp;·&nbsp; Bars: listed series that day",
                xref="paper",
                yref="paper",
                x=0.0,
                y=1.02,
                xanchor="left",
                yanchor="bottom",
                showarrow=False,
                font=dict(size=11, color="#8b949e", family="Inter, system-ui, sans-serif"),
            )
        ],
    )
    fig.update_annotations(font=dict(size=13, family="Inter, system-ui, sans-serif", color="#e6edf3"))
    return fig


def coverage_heatmap(wide: pd.DataFrame, asof, cp: str = "C", field: str = "TRDPRC_1") -> go.Figure:
    """2D occupancy grid: which (strike, expiry) cells actually have a number."""
    sl = _slice_wide(wide, asof, cp)
    if sl.empty:
        return go.Figure().update_layout(
            template="plotly_dark",
            paper_bgcolor="#0d1117",
            title=dict(text="No data", font=dict(size=16, family="Inter, system-ui, sans-serif")),
            height=380,
        )

    sl = sl.copy()
    sl["expiry_label"] = sl["expiry"].dt.strftime("%b ") + sl["expiry"].dt.day.astype(int).astype(str)
    val = sl[field] if field in sl.columns else sl["SETTLE"]
    sl["_hit"] = val.notna().astype(int)
    pivot = sl.pivot_table(index="expiry_label", columns="strike", values="_hit", aggfunc="max")
    # keep expiry order chronological, not alpha on "Oct"/"Sep"
    order = (
        sl.drop_duplicates("expiry_label")
        .sort_values("expiry")["expiry_label"]
        .tolist()
    )
    pivot = pivot.reindex(order, axis=0)
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)

    accent = "#00ffcc" if field == "SETTLE" else "#ff0055"
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[f"{c:.2f}" for c in pivot.columns],
            y=list(pivot.index),
            colorscale=[[0, "#161b22"], [1, accent]],
            zmin=0,
            zmax=1,
            showscale=False,
            xgap=2,
            ygap=2,
            hovertemplate="K=%{x}  expiry=%{y}  observed=%{z}<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3", family="Inter, system-ui, sans-serif", size=12),
        title=dict(
            text=f"{field} occupancy",
            font=dict(size=16, family="Inter, system-ui, sans-serif"),
            x=0.02,
            xanchor="left",
            y=0.98,
            yanchor="top",
        ),
        xaxis=dict(
            title="Strike ($)",
            gridcolor="#30363d",
            tickangle=-45,
            tickfont=dict(size=10),
            title_font=dict(size=12),
        ),
        yaxis=dict(
            title="Expiry",
            gridcolor="#30363d",
            tickfont=dict(size=11),
            title_font=dict(size=12),
        ),
        height=380,
        margin=dict(l=72, r=16, t=56, b=56),
        annotations=[
            dict(
                text="Lit cell = a number exists &nbsp;·&nbsp; Dark cell = no quote that day",
                xref="paper",
                yref="paper",
                x=0.0,
                y=1.02,
                xanchor="left",
                yanchor="bottom",
                showarrow=False,
                font=dict(size=11, color="#8b949e", family="Inter, system-ui, sans-serif"),
            )
        ],
    )
    return fig