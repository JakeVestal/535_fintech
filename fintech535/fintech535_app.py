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
import re
import traceback
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import reflex as rx

from fintech535.fintech535_utils import (
    attach_underlying,
    flatten_lseg_options,
    pivot_trade_mid,
    summarize_sparsity,
)
from fintech535.fintech535_plots import (
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
):
    """Load the LSEG pickle if present, else pull fresh from LSEG.

    Generator: yields ("progress", pct, label, detail) then ("result", payload).
    No synthetic fallback — a missing library or a failed session raises.
    """
    if os.path.exists(CACHE_FILE):
        yield ("progress", 20, "Reading local cache", CACHE_FILE)
        print(f"Loading cached dataset from {CACHE_FILE}...")
        with open(CACHE_FILE, "rb") as f:  # trusted: pickle we wrote ourselves
            payload = pickle.load(f)
        yield ("progress", 90, "Cache loaded", CACHE_FILE)
        yield ("result", payload)
        return

    # No fallback: if lseg.data is missing, that is a real error — do not
    # silently degrade to a synthetic panel.
    import lseg.data as ld

    print("Cache not found. Initializing LSEG data pull...")
    yield ("progress", 5, "Opening LSEG session", ticker_root)
    ld.open_session()

    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(weeks=weeks_back)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        yield ("progress", 10, "Pulling underlying history", ticker_stock)
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

        # OPRA month letter in the *body* of the RIC depends on right:
        #   calls A–L (Jan–Dec), puts M–X (Jan–Dec). Jul put = S, Aug put = T.
        # The expired-option suffix after "^" is ALWAYS the call/expiry letter
        # A–L, never the put letter. LSEG rejects e.g. UUUUS172601400.U^S26
        # and accepts UUUUS172601400.U^G26.
        # Ref: community.developers.lseg.com — "only month code letter is
        # different depending on the option type, whereas the Expiry month
        # after the '^' symbol is a letter from A to L no matter the option type."
        CALL_MONTH = "ABCDEFGHIJKL"  # Jan..Dec
        PUT_MONTH = "MNOPQRSTUVWX"   # Jan..Dec
        candidate_rics = []
        for d in friday_dates:
            year_str = d.strftime("%y")
            day_str = d.strftime("%d")
            expiry_code = CALL_MONTH[d.month - 1]  # A–L after the caret
            call_code = CALL_MONTH[d.month - 1]
            put_code = PUT_MONTH[d.month - 1]
            for strike in strikes:
                strike_str = f"{int(round(strike * 100)):05d}"
                call_base = f"{ticker_root.upper()}{call_code}{day_str}{year_str}{strike_str}.U"
                candidate_rics.append(f"{call_base}^{expiry_code}{year_str}")
                put_base = f"{ticker_root.upper()}{put_code}{day_str}{year_str}{strike_str}.U"
                candidate_rics.append(f"{put_base}^{expiry_code}{year_str}")

        # LSEG does NOT expose a `SETTLE` field on expired-option RICs
        # (returns UserRequestError 90006). The closest analogue we can pull
        # is MID_PRICE, the closing NBBO mid — that is what we plot as the
        # "exchange mark" alongside TRDPRC_1 (last trade).
        fields = ["TRDPRC_1", "MID_PRICE"]

        batches = [candidate_rics[i : i + batch_size]
                   for i in range(0, len(candidate_rics), batch_size)]
        n_batches = max(len(batches), 1)
        history_frames = []
        batch_failures = []       # (batch_index, exception message)
        single_failures = []      # (ric, exception message)

        yield (
            "progress",
            15,
            f"Requesting {len(candidate_rics)} option RICs",
            f"{n_batches} batches × {batch_size}",
        )

        for bi, batch in enumerate(batches):
            # 15% → 88% reserved for the batch loop
            pct = 15 + int(73 * (bi / n_batches))
            yield (
                "progress",
                pct,
                f"LSEG batch {bi + 1} of {n_batches}",
                f"{len(history_frames)} series so far · {len(batch_failures)} batch misses",
            )
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
                yield (
                    "progress",
                    pct,
                    f"Batch {bi + 1} failed — retrying RICs one-by-one",
                    f"{type(e).__name__}",
                )
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

    yield ("progress", 90, "Assembling option panel", f"{len(history_frames)} frames")
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
    yield ("progress", 98, "Wrote cache", CACHE_FILE)
    yield ("result", data_payload)


# Body letter immediately after the root: A–L = call, M–X = put.
# Do NOT use the letter after "^" — that is always the expiry month (A–L).
_RIC_BODY = re.compile(
    r"^(?P<root>[A-Z]+)(?P<body>[A-X])(?P<dd>\d{2})(?P<yy>\d{2})(?P<strike>\d{5})"
    r"(?:\.[A-Z])?(?:\^[A-L]\d{2})?$",
    re.IGNORECASE,
)
_CALL_LETTERS = set("ABCDEFGHIJKL")
_PUT_LETTERS = set("MNOPQRSTUVWX")


def cp_from_ric(ric: str) -> str | None:
    """Classify C/P from the OPRA month letter in the RIC body."""
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


def _stamp_cp_from_body(df: pd.DataFrame) -> pd.DataFrame:
    """Overwrite any existing right/cp column using the RIC body letter."""
    if df is None or df.empty or "ric" not in df.columns:
        return df
    out = df.copy()
    body_cp = out["ric"].map(cp_from_ric)
    out["cp"] = body_cp
    if "right" in out.columns:
        out["right"] = body_cp
    if "option_type" in out.columns:
        out["option_type"] = body_cp
    return out


def _as_naive_midnight(values) -> pd.DatetimeIndex:
    """Coerce any date-like sequence to tz-naive midnight. Never call
    tz_localize on a RangeIndex — that is the TypeError we just hit."""
    if isinstance(values, pd.Series):
        s = pd.to_datetime(values, errors="coerce")
        tz = getattr(getattr(s, "dt", None), "tz", None)
        if tz is not None:
            s = s.dt.tz_convert("UTC").dt.tz_localize(None)
        return pd.DatetimeIndex(s).normalize()
    idx = pd.Index(values)
    dt = pd.to_datetime(idx, errors="coerce")
    if not isinstance(dt, pd.DatetimeIndex):
        dt = pd.DatetimeIndex(dt)
    if dt.tz is not None:
        dt = dt.tz_convert("UTC").tz_localize(None)
    return dt.normalize()


def _flat_stock(stock: pd.DataFrame) -> pd.DataFrame:
    """Drop the LSEG ticker MultiIndex so attach_underlying can see TRDPRC_1."""
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


def _align_tidy_dates(tidy: pd.DataFrame) -> pd.DataFrame:
    out = tidy.copy()
    date_col = next((c for c in ("date", "Date", "DATE") if c in out.columns), None)
    if date_col is None:
        return out
    out[date_col] = _as_naive_midnight(out[date_col])
    if date_col != "date":
        out = out.rename(columns={date_col: "date"})
    return out


def _flatten_options_local(options: pd.DataFrame) -> pd.DataFrame:
    """Melt LSEG (date × (RIC, field)) into tidy rows. Does not touch tz."""
    df = options.copy()
    df.index = _as_naive_midnight(df.index)
    df.index.name = "date"
    pieces = []
    if isinstance(df.columns, pd.MultiIndex):
        pairs = list(df.columns)
    else:
        pairs = [(c, "VALUE") for c in df.columns]
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
        raise RuntimeError("No option quotes after flattening the LSEG panel.")
    long = pd.concat(pieces, ignore_index=True)
    if "Date" in long.columns and "date" not in long.columns:
        long = long.rename(columns={"Date": "date"})
    long["date"] = _as_naive_midnight(long["date"])
    long["cp"] = long["ric"].map(cp_from_ric)
    parsed = long["ric"].str.upper().str.extract(_RIC_BODY)
    if "strike" in parsed.columns:
        long["strike"] = pd.to_numeric(parsed["strike"], errors="coerce") / 100.0
    return long


def _attach_spot_local(tidy: pd.DataFrame, stock: pd.DataFrame) -> pd.DataFrame:
    """Same-session join only. No prior-close fill."""
    out = tidy.copy()
    if "date" not in out.columns:
        raise RuntimeError("tidy frame has no date column")
    spot_col = "TRDPRC_1" if "TRDPRC_1" in stock.columns else stock.columns[-1]
    spot = pd.to_numeric(stock[spot_col], errors="coerce")
    spot.index = _as_naive_midnight(spot.index)
    out["date"] = _as_naive_midnight(out["date"])
    mapped = out["date"].map(spot)
    missing = mapped.isna()
    if missing.any():
        gaps = sorted({d.strftime("%Y-%m-%d") for d in out.loc[missing, "date"]})
        print(f"[prepare] dropping {int(missing.sum())} option rows with no "
              f"same-day stock print. Gaps: {gaps[:8]}")
        out = out.loc[~missing].copy()
        mapped = out["date"].map(spot)
    out["underlying"] = mapped.to_numpy()
    out["spot"] = out["underlying"]
    return out


def _pivot_trade_mid_local(tidy: pd.DataFrame) -> pd.DataFrame:
    if "field" not in tidy.columns:
        return tidy.copy()
    keys = [c for c in ("date", "ric", "cp", "strike", "underlying", "spot") if c in tidy.columns]
    wide = tidy.pivot_table(
        index=keys,
        columns="field",
        values="value",
        aggfunc="last",
    )
    wide.columns = [str(c).upper() for c in wide.columns]
    return wide.reset_index()


def _prepare(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    # Package flatten/attach have been calling tz_localize on a RangeIndex.
    # Build the panel locally so a valid LSEG pickle actually loads.
    stock = _flat_stock(payload["stock"])
    try:
        tidy = flatten_lseg_options(payload["options"])
        tidy = _stamp_cp_from_body(tidy)
        tidy = _align_tidy_dates(tidy)
    except Exception as e:
        print(f"[prepare] package flatten failed ({type(e).__name__}: {e}); using local flatten")
        tidy = _flatten_options_local(payload["options"])
        tidy = _stamp_cp_from_body(tidy)

    try:
        tidy = attach_underlying(tidy, stock)
    except Exception as e:
        print(f"[prepare] package attach failed ({type(e).__name__}: {e}); using local attach")
        tidy = _attach_spot_local(tidy, stock)

    try:
        wide = pivot_trade_mid(tidy)
    except Exception as e:
        print(f"[prepare] package pivot failed ({type(e).__name__}: {e}); using local pivot")
        wide = _pivot_trade_mid_local(tidy)

    wide = _stamp_cp_from_body(wide)
    if "date" in wide.columns:
        wide["date"] = _as_naive_midnight(wide["date"])
    return tidy, wide, payload


def _nearest_asof(requested: str, available: list[str]) -> str:
    """Snap a calendar pick onto the nearest date that actually has quotes."""
    if not available:
        return ""
    if requested in available:
        return requested
    try:
        target = datetime.date.fromisoformat(requested)
    except ValueError:
        return available[0]
    best = min(
        available,
        key=lambda d: abs((datetime.date.fromisoformat(d) - target).days),
    )
    return best


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
    asof_min: str = ""
    asof_max: str = ""
    busy: bool = False
    progress_pct: int = 0
    progress_label: str = ""
    progress_detail: str = ""
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
        self.busy = True
        self.progress_pct = 2
        self.progress_label = "Starting…"
        self.progress_detail = ""
        self.status_msg = "Loading data..."
        yield

        try:
            payload = None
            for event in load_or_fetch_pipeline_data():
                kind = event[0]
                if kind == "progress":
                    _, pct, label, detail = event
                    self.progress_pct = int(pct)
                    self.progress_label = label
                    self.progress_detail = detail
                    self.status_msg = label
                    yield
                elif kind == "result":
                    payload = event[1]
            if payload is None:
                raise RuntimeError("Pipeline finished without a result payload.")
            self.progress_pct = 94
            self.progress_label = "Building figures"
            self.progress_detail = ""
            yield
            tidy, wide, payload = _prepare(payload)
        except Exception as e:
            # Surface the real failure — never fall back to synthetic data.
            self.status_msg = f"ERROR: {type(e).__name__}: {e}"
            self.data_note = str(e)
            self.progress_label = "Pull failed"
            self.progress_detail = str(e)
            self.busy = False
            print(f"[load_data] FAILED: {type(e).__name__}: {e}")
            traceback.print_exc()
            return

        self._wide = wide
        self._stock = _flat_stock(payload["stock"])
        self.ticker = payload.get("ticker", DEFAULT_TICKER_ROOT)
        self.option_count = int(wide["ric"].nunique()) if len(wide) else 0
        self.data_note = f"LSEG cache from {payload.get('fetched_at', '?')}"

        dates = sorted({pd.Timestamp(d).strftime("%Y-%m-%d") for d in wide["date"]}) if len(wide) else []
        self.asof_options = dates
        self.asof_min = dates[0] if dates else ""
        self.asof_max = dates[-1] if dates else ""
        # First available date — the start of the window, not the last print.
        self.asof = dates[0] if dates else ""

        try:
            self.fig_stock = candlestick_figure(self._stock, self.ticker)
        except Exception as e:
            print(f"[load_data] candlestick failed ({e}); drawing empty stock pane")
            traceback.print_exc()
            empty = go.Figure()
            empty.update_layout(template="plotly_dark", paper_bgcolor="#0d1117")
            self.fig_stock = empty
        self._rebuild_option_figs()
        self.status_msg = f"Loaded {self.option_count} series"
        self.progress_pct = 100
        self.progress_label = self.status_msg
        self.busy = False

    def set_cp(self, value: str):
        self.cp = value
        self._rebuild_option_figs()

    def set_asof(self, value: str):
        if not value:
            return
        self.asof = _nearest_asof(value, self.asof_options)
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


def _progress_modal() -> rx.Component:
    return rx.cond(
        State.busy,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.spinner(size="3", color="#00ffcc"),
                    rx.heading("Working", size="6", color="#00ffcc"),
                    rx.text(
                        State.progress_label,
                        color="#e6edf3",
                        size="3",
                        weight="medium",
                    ),
                    rx.progress(
                        value=State.progress_pct,
                        max=100,
                        width="100%",
                        color_scheme="cyan",
                        size="2",
                    ),
                    rx.hstack(
                        rx.text(State.progress_pct, color="#00ffcc", size="2", weight="bold"),
                        rx.text("%", color="#00ffcc", size="2", weight="bold"),
                        rx.spacer(),
                        rx.text(State.progress_detail, color="#8b949e", size="2"),
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align="center",
                ),
                bg="#161b22",
                border="1px solid #30363d",
                border_radius="12px",
                padding="1.75rem",
                width="28rem",
                max_width="90vw",
                box_shadow="0 24px 80px rgba(0,0,0,0.55)",
            ),
            position="fixed",
            top="0",
            left="0",
            right="0",
            bottom="0",
            background="rgba(1, 4, 9, 0.72)",
            display="flex",
            align_items="center",
            justify_content="center",
            z_index="1000",
        ),
    )


def _metric(label: str, value) -> rx.Component:
    return rx.card(
        rx.text(label, size="2", color="#8b949e"),
        rx.text(value, size="6", color="#00ffcc", weight="bold"),
        bg="#161b22",
        border="1px solid #30363d",
        padding="1rem",
    )


def index() -> rx.Component:
    return rx.box(
        _progress_modal(),
        rx.container(
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
                    disabled=State.busy,
                    loading=State.busy,
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
                rx.input(
                    type="date",
                    value=State.asof,
                    min=State.asof_min,
                    max=State.asof_max,
                    on_change=State.set_asof,
                    size="2",
                    width="11rem",
                    bg="#161b22",
                    color="#e6edf3",
                    border="1px solid #30363d",
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
        ),
        width="100%",
        min_height="100vh",
        background_color="#0d1117",
    )


app = rx.App()
app.add_page(index)