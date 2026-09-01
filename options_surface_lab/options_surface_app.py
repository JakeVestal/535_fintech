"""
Options Surface Lab — Reflex app

Reuses the LSEG pickle cache if present, otherwise pulls fresh from LSEG.
There is no synthetic-data fallback: if the pull fails for any reason we
raise so the failure is visible rather than being silently papered over
with a made-up panel.

Teaching targets this week
--------------------------
1. Listed options are a sparse cloud, not a filled sheet.
2. MID_PRICE (closing NBBO mid; the closest thing LSEG serves to an
   exchange settlement price on this RIC universe) is not TRDPRC_1
   (last trade).
3. An interpolated "surface" is an assumption you are imposing on holes.
"""

from __future__ import annotations

import datetime
import os
import pickle
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import reflex as rx

from options_surface_lab.option_surface_utils import (
    attach_underlying,
    flatten_lseg_options,
    pivot_trade_mid,
    summarize_sparsity,
)
from options_surface_lab.option_surface_plots import (
    candlestick_figure,
    coverage_heatmap,
    mid_vs_trade_figure,
    price_surface_figure,
)

warnings.filterwarnings("ignore", category=FutureWarning, module="lseg.data")

CACHE_FILE = "option_pipeline_data.pkl"
DEFAULT_TICKER_STOCK = "UUUU.K"
DEFAULT_TICKER_ROOT = "UUUU"
DEFAULT_WEEKS_BACK = 12
DEFAULT_STRIKE_STEP = 0.50
DEFAULT_BATCH_SIZE = 25


def load_or_fetch_pipeline_data(
    ticker_stock: str = DEFAULT_TICKER_STOCK,
    ticker_root: str = DEFAULT_TICKER_ROOT,
    weeks_back: int = DEFAULT_WEEKS_BACK,
    strike_step: float = DEFAULT_STRIKE_STEP,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    """Load the LSEG pickle if present, else pull fresh from LSEG.

    No synthetic fallback — a missing library or a failed session raises,
    and a run in which every batch and every single-RIC retry fails raises
    with a summary of how many attempts errored so the failure is visible.
    """
    if os.path.exists(CACHE_FILE):
        print(f"Loading cached dataset from {CACHE_FILE}...")
        with open(CACHE_FILE, "rb") as f:  # trusted: pickle we wrote ourselves
            payload = pickle.load(f)
        return payload

    # No fallback: if lseg.data is missing, that is a real error — do not
    # silently degrade to a synthetic panel.
    import lseg.data as ld

    print("Cache not found. Initializing LSEG data pull...")
    ld.open_session()

    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(weeks=weeks_back)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        df_stock = ld.get_history(
            universe=[ticker_stock],
            fields=["OPEN_PRC", "HIGH_1", "LOW_1", "TRDPRC_1"],
            start=start_str,
            end=end_str,
            interval="daily",
        )
        if df_stock is None or df_stock.empty:
            raise RuntimeError(f"LSEG returned no stock history for {ticker_stock}.")

        low_price = float(df_stock["LOW_1"].min())
        high_price = float(df_stock["HIGH_1"].max())

        min_strike = np.floor(low_price / strike_step) * strike_step
        max_strike = np.ceil(high_price / strike_step) * strike_step
        strikes = np.arange(min_strike, max_strike + strike_step, strike_step)
        friday_dates = pd.date_range(start=start_str, end=end_str, freq="W-FRI")

        candidate_rics = []
        for d in friday_dates:
            year_str = d.strftime("%y")
            day_str = d.strftime("%d")
            month_num = d.month
            call_code = chr(ord("A") + month_num - 1)
            put_code = chr(ord("M") + month_num - 1)
            for strike in strikes:
                strike_str = f"{int(round(strike * 100)):05d}"
                call_base = f"{ticker_root.upper()}{call_code}{day_str}{year_str}{strike_str}.U"
                candidate_rics.append(f"{call_base}^{call_code}{year_str}")
                put_base = f"{ticker_root.upper()}{put_code}{day_str}{year_str}{strike_str}.U"
                candidate_rics.append(f"{put_base}^{put_code}{year_str}")

        # LSEG does NOT expose a `SETTLE` field on expired-option RICs
        # (returns UserRequestError 90006). The closest analogue we can pull
        # is MID_PRICE, the closing NBBO mid — that is what we plot as the
        # "exchange mark" alongside TRDPRC_1 (last trade).
        fields = ["TRDPRC_1", "MID_PRICE"]

        batches = [candidate_rics[i : i + batch_size]
                   for i in range(0, len(candidate_rics), batch_size)]
        history_frames = []
        batch_failures = []       # (batch_index, exception message)
        single_failures = []      # (ric, exception message)

        for bi, batch in enumerate(batches):
            try:
                df_batch = ld.get_history(
                    universe=batch,
                    fields=fields,
                    start=start_str,
                    end=end_str,
                    interval="daily",
                )
            except Exception as e:
                batch_failures.append((bi, f"{type(e).__name__}: {e}"))
                # Not silent: retry each RIC one-by-one, and record any that also fail.
                for single_ric in batch:
                    try:
                        df_single = ld.get_history(
                            universe=[single_ric],
                            fields=fields,
                            start=start_str,
                            end=end_str,
                            interval="daily",
                        )
                    except Exception as ee:
                        single_failures.append((single_ric, f"{type(ee).__name__}: {ee}"))
                        continue
                    if (df_single is not None and not df_single.empty
                            and not df_single.dropna(how="all").empty):
                        history_frames.append(df_single)
                continue

            if df_batch is not None and not df_batch.empty:
                df_clean = df_batch.dropna(how="all", axis=1)
                if not df_clean.empty:
                    history_frames.append(df_clean)
    finally:
        try:
            ld.close_session()
        except Exception:
            pass

    if batch_failures:
        print(f"[pull] {len(batch_failures)} batches failed. First 3:")
        for bi, msg in batch_failures[:3]:
            print(f"    batch {bi}: {msg[:200]}")
    if single_failures:
        print(f"[pull] {len(single_failures)} single-RIC retries also failed "
              f"(expected — many synthetic RICs never existed).")

    if not history_frames:
        raise RuntimeError(
            f"LSEG pull returned zero option history frames. Batches failed: "
            f"{len(batch_failures)}, single-RIC retries failed: {len(single_failures)}. "
            f"No cache was written."
        )

    df_options = pd.concat(history_frames, axis=1)
    df_options = df_options.loc[:, ~df_options.columns.duplicated()]
    # Uppercase field labels for a consistent downstream schema.
    if isinstance(df_options.columns, pd.MultiIndex):
        df_options.columns = pd.MultiIndex.from_tuples(
            [(ric, str(f).upper()) for ric, f in df_options.columns],
            names=df_options.columns.names or ["RIC", "Field"],
        )

    data_payload = {
        "stock": df_stock,
        "options": df_options,
        "ticker": ticker_root,
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data_payload, f)
    print(f"Data pipeline complete. Results cached to {CACHE_FILE}.")
    return data_payload


def _prepare(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    tidy = flatten_lseg_options(payload["options"])
    tidy = attach_underlying(tidy, payload["stock"])
    wide = pivot_trade_mid(tidy)
    return tidy, wide, payload


class State(rx.State):
    ticker: str = DEFAULT_TICKER_ROOT
    status_msg: str = "Ready"
    option_count: int = 0
    n_quotes: int = 0
    n_mid_only: int = 0
    n_both: int = 0
    pct_mid_no_trade: str = "—"
    median_gap: str = "—"
    data_note: str = ""
    asof: str = ""
    asof_options: list[str] = []
    cp: str = "C"
    show_trade: bool = True
    show_mid: bool = True
    show_sheet: bool = True

    fig_stock: go.Figure = go.Figure()
    fig_surface: go.Figure = go.Figure()
    fig_compare: go.Figure = go.Figure()
    fig_heat_mid: go.Figure = go.Figure()
    fig_heat_trade: go.Figure = go.Figure()

    _wide: pd.DataFrame | None = None
    _stock: pd.DataFrame | None = None

    def load_data(self):
        self.status_msg = "Loading data..."
        try:
            payload = load_or_fetch_pipeline_data()
            tidy, wide, payload = _prepare(payload)
        except Exception as e:
            # Surface the real failure — never fall back to synthetic data.
            self.status_msg = f"ERROR: {type(e).__name__}: {e}"
            self.data_note = str(e)
            print(f"[load_data] FAILED: {type(e).__name__}: {e}")
            return

        self._wide = wide
        self._stock = payload["stock"]
        self.ticker = payload.get("ticker", DEFAULT_TICKER_ROOT)
        self.option_count = int(wide["ric"].nunique()) if len(wide) else 0
        self.data_note = f"LSEG cache from {payload.get('fetched_at', '?')}"

        dates = sorted({d.strftime("%Y-%m-%d") for d in wide["date"]}) if len(wide) else []
        self.asof_options = dates
        self.asof = dates[-1] if dates else ""

        self.fig_stock = candlestick_figure(payload["stock"], self.ticker)
        self._rebuild_option_figs()
        self.status_msg = f"Loaded {self.option_count} series"

    def set_cp(self, value: str):
        self.cp = value
        self._rebuild_option_figs()

    def set_asof(self, value: str):
        self.asof = value
        self._rebuild_option_figs()

    def toggle_trade(self, value: bool):
        self.show_trade = value
        self._rebuild_option_figs()

    def toggle_mid(self, value: bool):
        self.show_mid = value
        self._rebuild_option_figs()

    def toggle_sheet(self, value: bool):
        self.show_sheet = value
        self._rebuild_option_figs()

    def _rebuild_option_figs(self):
        wide = self._wide
        if wide is None or wide.empty or not self.asof:
            empty = go.Figure()
            empty.update_layout(template="plotly_dark", paper_bgcolor="#0d1117")
            self.fig_surface = empty
            self.fig_compare = empty
            self.fig_heat_mid = empty
            self.fig_heat_trade = empty
            return

        asof = self.asof
        sl = wide[wide["date"] == pd.Timestamp(asof)]
        stats = summarize_sparsity(sl)
        self.n_quotes = stats["n_quotes"]
        self.n_mid_only = stats["n_mid_only"]
        self.n_both = stats["n_both"]
        self.pct_mid_no_trade = f"{stats['pct_mid_no_trade']:.0f}%"
        if stats["median_abs_diff"] is None:
            self.median_gap = "n/a"
        else:
            rel = stats["median_rel_diff_pct"]
            self.median_gap = f"${stats['median_abs_diff']:.3f}" + (
                f" ({rel:.1f}%)" if rel is not None else ""
            )

        self.fig_surface = price_surface_figure(
            wide,
            asof,
            cp=self.cp,
            show_trade=self.show_trade,
            show_mid=self.show_mid,
            show_interpolated=self.show_sheet,
            ticker=self.ticker,
        )
        self.fig_compare = mid_vs_trade_figure(wide, asof, ticker=self.ticker)
        self.fig_heat_mid = coverage_heatmap(wide, asof, cp=self.cp, field="MID_PRICE")
        self.fig_heat_trade = coverage_heatmap(wide, asof, cp=self.cp, field="TRDPRC_1")


def _metric(label: str, value) -> rx.Component:
    return rx.card(
        rx.text(label, size="2", color="#8b949e"),
        rx.text(value, size="6", color="#00ffcc", weight="bold"),
        bg="#161b22",
        border="1px solid #30363d",
        padding="1rem",
    )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "OPTIONS SURFACE LAB",
                    size="8",
                    color="#00ffcc",
                    style={"letter_spacing": "2px"},
                ),
                rx.spacer(),
                rx.badge(State.status_msg, color_scheme="cyan", variant="solid"),
                width="100%",
                align="center",
                padding_y="1rem",
            ),
            rx.text(State.data_note, color="#8b949e", size="2"),
            rx.hstack(
                _metric("Underlying", State.ticker),
                _metric("Option series", State.option_count),
                _metric("Quotes on as-of date", State.n_quotes),
                _metric("Mid with no print", State.n_mid_only),
                _metric("Median |mid − trade|", State.median_gap),
                rx.button(
                    "Reload data",
                    on_click=State.load_data,
                    bg="#238636",
                    color="#ffffff",
                    _hover={"bg": "#2ea043"},
                    size="3",
                ),
                spacing="4",
                width="100%",
                align="center",
                wrap="wrap",
            ),
            rx.box(
                rx.plotly(data=State.fig_stock, style={"width": "100%", "height": "420px"}),
                width="100%",
                bg="#161b22",
                border="1px solid #30363d",
                border_radius="8px",
                padding="1rem",
            ),
            rx.hstack(
                rx.text("As-of date", color="#8b949e", size="2"),
                rx.select(
                    State.asof_options,
                    value=State.asof,
                    on_change=State.set_asof,
                    size="2",
                ),
                rx.text("Right", color="#8b949e", size="2"),
                rx.select(
                    ["C", "P"],
                    value=State.cp,
                    on_change=State.set_cp,
                    size="2",
                ),
                rx.switch(checked=State.show_mid, on_change=State.toggle_mid),
                rx.text("MID_PRICE", color="#00ffcc", size="2"),
                rx.switch(checked=State.show_trade, on_change=State.toggle_trade),
                rx.text("TRDPRC_1", color="#ff0055", size="2"),
                rx.switch(checked=State.show_sheet, on_change=State.toggle_sheet),
                rx.text("Interpolated sheet", color="#8b949e", size="2"),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            rx.text(
                "Cyan dots = closing NBBO mid (MID_PRICE). Magenta diamonds = last trade "
                "(TRDPRC_1). The translucent sheet is linearly interpolated and will "
                "happily invent prices in strikes that never printed. Turn it off.",
                color="#8b949e",
                size="2",
            ),
            rx.box(
                rx.plotly(data=State.fig_surface, style={"width": "100%", "height": "640px"}),
                width="100%",
                bg="#161b22",
                border="1px solid #30363d",
                border_radius="8px",
                padding="1rem",
            ),
            rx.box(
                rx.plotly(data=State.fig_compare, style={"width": "100%", "height": "460px"}),
                width="100%",
                bg="#161b22",
                border="1px solid #30363d",
                border_radius="8px",
                padding="1rem",
            ),
            rx.hstack(
                rx.box(
                    rx.plotly(
                        data=State.fig_heat_mid,
                        style={"width": "100%", "height": "380px"},
                    ),
                    width="50%",
                    bg="#161b22",
                    border="1px solid #30363d",
                    border_radius="8px",
                    padding="0.5rem",
                ),
                rx.box(
                    rx.plotly(
                        data=State.fig_heat_trade,
                        style={"width": "100%", "height": "380px"},
                    ),
                    width="50%",
                    bg="#161b22",
                    border="1px solid #30363d",
                    border_radius="8px",
                    padding="0.5rem",
                ),
                width="100%",
                spacing="3",
            ),
            spacing="5",
            width="100%",
        ),
        on_mount=State.load_data,
        background_color="#0d1117",
        min_height="100vh",
        max_width="100%",
        padding="2rem",
    )


app = rx.App()
app.add_page(index)
