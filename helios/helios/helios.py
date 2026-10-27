import reflex as rx
from datetime import datetime

# Helios dark theme
BG = "#070b10"
SURFACE = "#101820"
SURFACE2 = "#161f2a"
FG = "#e8f6f3"
MUTED = "#8aa8a4"
ACCENT = "#2ee6d0"
DOWN = "#ff6b8a"
LINE = "#24313c"

class State(rx.State):
    # All market values start blank. They are populated only by a real LSEG pull.
    vix: str = "—"
    realized: str = "—"
    vrp: str = "—"
    last_update: str = "—"
    status: str = "Awaiting LSEG session. No public fallback is used."

    # Term structure / skew — empty until LSEG IPA surfaces return data
    tenors: list[str] = ["1W", "2W", "1M", "2M", "3M", "6M"]
    spx_atm: list[str] = ["—"] * 6
    qqq_atm: list[str] = ["—"] * 6
    spx_rr25: list[str] = ["—"] * 6
    qqq_rr25: list[str] = ["—"] * 6
    premium_by_tenor: list[str] = ["—"] * 6

    def refresh(self):
        """Pull real LSEG data. No fallbacks. On any failure leave blanks and report the error."""
        try:
            import lseg.data as ld
            ld.open_session()

            # --- VRP: VIX (30d implied) vs 30d realized on SPX ---
            vix_df = ld.get_data(universe=".VIX", fields=["TRDPRC_1"])
            vix_val = None
            if vix_df is not None and not vix_df.empty:
                vix_val = float(vix_df["TRDPRC_1"].iloc[0])
                self.vix = f"{vix_val:.2f}"

            # Realized from SPX closes (last ~45 calendar days)
            spx_hist = ld.get_history(
                universe=".SPX",
                fields=["TRDPRC_1"],
                interval="1D",
                count=45,
            )
            realized_val = None
            if spx_hist is not None and not spx_hist.empty and "TRDPRC_1" in spx_hist.columns:
                rets = spx_hist["TRDPRC_1"].pct_change().dropna()
                if len(rets) >= 20:
                    realized_val = float(rets.std() * (252 ** 0.5) * 100)
                    self.realized = f"{realized_val:.2f}"

            if vix_val is not None and realized_val is not None:
                self.vrp = f"{vix_val - realized_val:+.2f}"
            else:
                self.vrp = "—"

            # --- Term structure & skew via IPA ETI surfaces ---
            self._pull_surfaces(ld)

            self.status = "LSEG pull complete."
            self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            self.status = f"LSEG error: {type(e).__name__}: {e}. Fields left blank. No fallback used."
            self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M")
            # Leave all market fields as "—" (already the default)

    def _pull_surfaces(self, ld):
        """Request ATM term structure (and attempt 25Δ RR) for .SPX and QQQ.O."""
        from lseg.data.delivery import endpoint_request
        import pandas as pd

        SURFACES_URL = "https://api.refinitiv.com/data/quantitative-analytics-curves-and-surfaces/v1/surfaces"
        instruments = [(".SPX", "spx"), ("QQQ.O", "qqq")]

        # ATM via moneyness
        universe = []
        for ric, tag in instruments:
            universe.append({
                "surfaceTag": tag,
                "underlyingType": "Eti",
                "underlyingDefinition": {"instrumentCode": f"{ric}@RIC"},
                "surfaceParameters": {
                    "inputVolatilityType": "Quoted",
                    "timeStamp": "Default",
                    "priceSide": "Mid",
                    "volatilityModel": "SSVI",
                    "xAxis": "Tenor",
                    "yAxis": "Moneyness",
                },
                "surfaceLayout": {"format": "Matrix"},
            })

        req = endpoint_request.Definition(
            url=SURFACES_URL,
            method=endpoint_request.RequestMethod.POST,
            body_parameters={"universe": universe, "outputs": ["Data"]},
        )
        resp = req.get_data()
        if resp is None or not hasattr(resp, "data") or resp.data.raw is None:
            self.status = "LSEG surface response empty."
            return

        raw = resp.data.raw.get("data", [])
        surfaces = {item.get("surfaceTag"): item for item in raw}

        def atm_for(tag):
            item = surfaces.get(tag)
            if not item or "surface" not in item:
                return ["—"] * 6
            try:
                sdf = pd.DataFrame(item["surface"])
                # First row = moneyness labels, first col = tenor labels
                moneyness = [str(x) for x in sdf.iloc[0, 1:].tolist()]
                tenors_returned = [str(x) for x in sdf.iloc[1:, 0].tolist()]
                # Find column closest to 100 or 1.0 (ATM)
                target = 100.0
                cols = []
                for m in moneyness:
                    try:
                        cols.append(abs(float(m) - target))
                    except Exception:
                        cols.append(999)
                atm_idx = cols.index(min(cols)) if cols else 0
                # Map requested TENORS
                result = []
                for t in ["1W", "2W", "1M", "2M", "3M", "6M"]:
                    if t in tenors_returned:
                        row = tenors_returned.index(t)
                        val = sdf.iloc[row + 1, atm_idx + 1]
                        result.append(f"{float(val):.2f}" if val is not None else "—")
                    else:
                        result.append("—")
                return result
            except Exception:
                return ["—"] * 6

        self.spx_atm = atm_for("spx")
        self.qqq_atm = atm_for("qqq")

        # Premium = QQQ ATM - SPX ATM
        prem = []
        for s, q in zip(self.spx_atm, self.qqq_atm):
            try:
                prem.append(f"{float(q) - float(s):+.2f}")
            except Exception:
                prem.append("—")
        self.premium_by_tenor = prem

        # 25Δ risk reversal: second request with yAxis=Delta if supported
        # (many desks use Delta axis for RR)
        try:
            universe_rr = []
            for ric, tag in instruments:
                universe_rr.append({
                    "surfaceTag": f"{tag}_rr",
                    "underlyingType": "Eti",
                    "underlyingDefinition": {"instrumentCode": f"{ric}@RIC"},
                    "surfaceParameters": {
                        "priceSide": "Mid",
                        "volatilityModel": "SSVI",
                        "xAxis": "Tenor",
                        "yAxis": "Delta",
                    },
                    "surfaceLayout": {"format": "Matrix"},
                })
            req_rr = endpoint_request.Definition(
                url=SURFACES_URL,
                method=endpoint_request.RequestMethod.POST,
                body_parameters={"universe": universe_rr, "outputs": ["Data"]},
            )
            resp_rr = req_rr.get_data()
            if resp_rr and hasattr(resp_rr, "data") and resp_rr.data.raw:
                raw_rr = resp_rr.data.raw.get("data", [])
                surfaces_rr = {item.get("surfaceTag"): item for item in raw_rr}

                def rr25_for(tag):
                    item = surfaces_rr.get(tag)
                    if not item or "surface" not in item:
                        return ["—"] * 6
                    try:
                        sdf = pd.DataFrame(item["surface"])
                        deltas = [str(x) for x in sdf.iloc[0, 1:].tolist()]
                        tenors_returned = [str(x) for x in sdf.iloc[1:, 0].tolist()]
                        # Look for ~25 and ~75 (or -25 / 25 depending on convention)
                        # Simple: find columns nearest 25 and 75, compute put-call style difference
                        def nearest(target):
                            best, best_d = None, 999
                            for i, d in enumerate(deltas):
                                try:
                                    dist = abs(float(d) - target)
                                    if dist < best_d:
                                        best_d, best = dist, i
                                except Exception:
                                    pass
                            return best
                        i25 = nearest(25)
                        i75 = nearest(75)
                        if i25 is None or i75 is None:
                            return ["—"] * 6
                        result = []
                        for t in ["1W", "2W", "1M", "2M", "3M", "6M"]:
                            if t in tenors_returned:
                                row = tenors_returned.index(t)
                                v25 = sdf.iloc[row + 1, i25 + 1]
                                v75 = sdf.iloc[row + 1, i75 + 1]
                                try:
                                    # RR ≈ 25Δ put vol - 25Δ call vol (approx from the two wings)
                                    result.append(f"{float(v25) - float(v75):+.2f}")
                                except Exception:
                                    result.append("—")
                            else:
                                result.append("—")
                        return result
                    except Exception:
                        return ["—"] * 6

                self.spx_rr25 = rr25_for("spx_rr")
                self.qqq_rr25 = rr25_for("qqq_rr")
        except Exception:
            # Delta axis may not be supported for these underlyings; leave RR blank
            pass

def metric_card(label: str, value: str, hint: str = "") -> rx.Component:
    return rx.box(
        rx.text(label, font_size="0.75rem", color=MUTED, font_family="IBM Plex Mono"),
        rx.text(value, font_size="1.75rem", font_weight="600", color=FG, font_family="IBM Plex Mono"),
        rx.text(hint, font_size="0.75rem", color=MUTED, margin_top="0.25rem"),
        padding="1rem",
        border=f"1px solid {LINE}",
        border_radius="0.75rem",
        background=SURFACE,
        min_width="140px",
    )

def nav() -> rx.Component:
    return rx.hstack(
        rx.link("VRP", href="/", color=MUTED, font_size="0.85rem", font_family="IBM Plex Mono"),
        rx.link("Term & Skew", href="/term-skew", color=ACCENT, font_size="0.85rem", font_family="IBM Plex Mono"),
        spacing="4",
        padding_bottom="0.75rem",
        border_bottom=f"1px solid {LINE}",
        width="100%",
    )

def vrp_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            nav(),
            rx.hstack(
                rx.vstack(
                    rx.text("HELIOS", font_size="0.7rem", letter_spacing="0.28em", color=ACCENT, font_family="IBM Plex Mono"),
                    rx.heading("Variance Risk Premium", size="6", color=FG),
                    rx.text("Implied vs realized. Values appear only from LSEG. No fallback.", color=MUTED, font_size="0.9rem"),
                    align_items="start",
                    spacing="1",
                ),
                rx.spacer(),
                rx.badge("LSEG ONLY", variant="outline", color_scheme="teal"),
                width="100%",
                align="end",
            ),
            rx.hstack(
                metric_card("VIX", State.vix, "30d implied (LSEG)"),
                metric_card("Realized", State.realized, "Close-to-close (LSEG)"),
                metric_card("VRP", State.vrp, "Implied − realized"),
                metric_card("Updated", State.last_update, "Session"),
                spacing="3",
                wrap="wrap",
                width="100%",
            ),
            rx.button("Refresh (LSEG)", on_click=State.refresh, background=ACCENT, color=BG, font_weight="600"),
            rx.text(State.status, font_size="0.8rem", color=MUTED),
            spacing="5",
            width="100%",
            max_width="1100px",
            margin="0 auto",
            padding="1.5rem",
        ),
        background=BG,
        min_height="100vh",
        color=FG,
        font_family="IBM Plex Sans, Segoe UI, system-ui, sans-serif",
    )

# Plain Python structure for the table layout. Values are bound inside the component.
TENORS = ["1W", "2W", "1M", "2M", "3M", "6M"]

def term_skew_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            nav(),
            rx.hstack(
                rx.vstack(
                    rx.text("HELIOS", font_size="0.7rem", letter_spacing="0.28em", color=ACCENT, font_family="IBM Plex Mono"),
                    rx.heading("Term Structure & Skew", size="6", color=FG),
                    rx.text("ATM term structure and 25Δ risk reversal for SPX vs QQQ. Tech premium by tenor. Populated only from LSEG IPA ETI surfaces. No fallback.", color=MUTED, font_size="0.9rem"),
                    align_items="start",
                    spacing="1",
                ),
                rx.spacer(),
                rx.badge("LSEG ONLY", variant="outline", color_scheme="teal"),
                width="100%",
                align="end",
            ),
            rx.heading("ATM Term Structure — Tech Premium by Tenor", size="4", color=FG, margin_top="0.5rem"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Tenor"),
                        rx.table.column_header_cell("SPX ATM"),
                        rx.table.column_header_cell("QQQ ATM"),
                        rx.table.column_header_cell("Premium (pts)"),
                    )
                ),
                rx.table.body(
                    *[
                        rx.table.row(
                            rx.table.cell(TENORS[i]),
                            rx.table.cell(State.spx_atm[i]),
                            rx.table.cell(State.qqq_atm[i]),
                            rx.table.cell(State.premium_by_tenor[i]),
                        )
                        for i in range(len(TENORS))
                    ]
                ),
                width="100%",
                border=f"1px solid {LINE}",
            ),
            rx.heading("25Δ Risk Reversal (Put − Call)", size="4", color=FG, margin_top="1rem"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Tenor"),
                        rx.table.column_header_cell("SPX 25Δ RR"),
                        rx.table.column_header_cell("QQQ 25Δ RR"),
                    )
                ),
                rx.table.body(
                    *[
                        rx.table.row(
                            rx.table.cell(TENORS[i]),
                            rx.table.cell(State.spx_rr25[i]),
                            rx.table.cell(State.qqq_rr25[i]),
                        )
                        for i in range(len(TENORS))
                    ]
                ),
                width="100%",
                border=f"1px solid {LINE}",
            ),
            rx.box(
                rx.text(
                    "Status: waiting for LSEG IPA ETI volatility surfaces (.SPX and QQQ). "
                    "Once the session is available the tables will fill with ATM IVs and 25Δ risk reversals. "
                    "Until then every cell remains blank. No public data source is used.",
                    color=MUTED,
                    font_size="0.85rem",
                    line_height="1.5",
                ),
                padding="1rem",
                border=f"1px solid {LINE}",
                border_radius="0.75rem",
                background=SURFACE,
                width="100%",
                margin_top="1rem",
            ),
            rx.button("Refresh (LSEG)", on_click=State.refresh, background=ACCENT, color=BG, font_weight="600"),
            rx.text(State.status, font_size="0.8rem", color=MUTED),
            spacing="4",
            width="100%",
            max_width="1100px",
            margin="0 auto",
            padding="1.5rem",
        ),
        background=BG,
        min_height="100vh",
        color=FG,
        font_family="IBM Plex Sans, Segoe UI, system-ui, sans-serif",
    )

app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
    ],
)
app.add_page(vrp_page, route="/", title="Helios — VRP")
app.add_page(term_skew_page, route="/term-skew", title="Helios — Term & Skew")
