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
    status: str = "Awaiting LSEG session."
    loading: bool = False

    # Term structure / skew — empty until LSEG IPA surfaces return data
    tenors: list[str] = ["1W", "2W", "1M", "2M", "3M", "6M"]
    spx_atm: list[str] = ["—"] * 6
    qqq_atm: list[str] = ["—"] * 6
    spx_rr25: list[str] = ["—"] * 6
    qqq_rr25: list[str] = ["—"] * 6
    premium_by_tenor: list[str] = ["—"] * 6

    # Gamma / clustering
    gamma_status: str = "Awaiting LSEG session."
    spot: str = "—"
    gamma_flip: str = "—"
    put_call_oi: str = "—"
    put_call_vol: str = "—"
    top_oi: list[dict] = []
    gamma_chart: list[dict] = []

    def refresh(self):
        """Pull real LSEG data. On any failure leave blanks and report the error."""
        self.loading = True
        self.status = "Opening LSEG session…"
        try:
            import lseg.data as ld
            # Raise HTTP timeout for IPA surfaces (desktop proxy can be slow)
            try:
                cfg = ld.get_config()
                cfg.set_param("http.request-timeout", 120)
            except Exception:
                pass
            ld.open_session()

            # --- VRP: VIX (30d implied) vs 30d realized on SPX ---
            self.status = "Pulling VIX…"
            vix_val = None
            for ric in (".VIX", "/.VIX"):
                try:
                    vix_df = ld.get_data(universe=ric, fields=["TRDPRC_1"])
                    if vix_df is not None and not vix_df.empty and "TRDPRC_1" in vix_df.columns:
                        vix_val = float(vix_df["TRDPRC_1"].iloc[0])
                        self.vix = f"{vix_val:.2f}"
                        break
                except Exception:
                    continue

            # Realized from SPX closes (last ~45 calendar days)
            self.status = "Pulling SPX history…"
            spx_hist = None
            for ric in (".SPX", "/.SPX"):
                try:
                    spx_hist = ld.get_history(
                        universe=ric,
                        fields=["TRDPRC_1"],
                        interval="1D",
                        count=45,
                    )
                    if spx_hist is not None and not spx_hist.empty:
                        break
                except Exception:
                    continue
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
            self.status = "Pulling IPA surfaces…"
            try:
                self._pull_surfaces(ld)
            except Exception as surf_e:
                self.status = f"Surfaces timed out or failed: {type(surf_e).__name__}: {surf_e}. VRP still updated."

            if "Surfaces" not in self.status:
                self.status = "LSEG pull complete."
            self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            self.status = f"LSEG error: {type(e).__name__}: {e}"
            self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M")
        finally:
            self.loading = False

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


    def refresh_gamma(self):
        """Pull SPX option chain data and compute gamma proxy / OI clusters."""
        self.loading = True
        self.gamma_status = "Opening LSEG session…"
        try:
            import lseg.data as ld
            try:
                cfg = ld.get_config()
                cfg.set_param("http.request-timeout", 120)
            except Exception:
                pass
            import pandas as pd
            import math
            from datetime import timedelta
            from lseg.data.discovery import Chain
            ld.open_session()

            self.gamma_status = "Pulling .SPX spot…"
            spot_df = ld.get_data(universe=".SPX", fields=["TRDPRC_1"])
            if spot_df is None or spot_df.empty or "TRDPRC_1" not in spot_df.columns:
                self.gamma_status = "Could not retrieve .SPX spot."
                return
            spot = float(spot_df["TRDPRC_1"].iloc[0])
            self.spot = f"{spot:.2f}"

            self.gamma_status = "Expanding option chain…"
            rics = []
            chain_used = None
            for chain_name in ("0#SPXW*.U", "0#SPX*.U", "0#/SPX*.U", "0#/SPXW*.U"):
                try:
                    chain = Chain(name=chain_name)
                    rics = list(chain.constituents)[:600]
                    if rics:
                        chain_used = chain_name
                        break
                except Exception:
                    continue
            if not rics:
                self.gamma_status = "Empty or unavailable option chain. Tried 0#SPXW*.U, 0#SPX*.U, 0#/SPX*.U."
                return

            self.gamma_status = f"Pulling {len(rics)} contracts…"
            fields = ["STRIKE_PRC", "EXPIR_DATE", "PUT_CALL", "OPINT_1", "ACVOL_1", "TR.IMPLIEDVOLATILITY"]
            df = ld.get_data(universe=rics, fields=fields)
            if df is None or df.empty:
                self.gamma_status = "get_data returned empty chain."
                return

            df = df.dropna(subset=["STRIKE_PRC"])
            df["STRIKE_PRC"] = pd.to_numeric(df["STRIKE_PRC"], errors="coerce")
            df = df.dropna(subset=["STRIKE_PRC"])
            lo, hi = spot * 0.88, spot * 1.12
            df = df[(df["STRIKE_PRC"] >= lo) & (df["STRIKE_PRC"] <= hi)]

            if "EXPIR_DATE" in df.columns:
                df["EXPIR_DATE"] = pd.to_datetime(df["EXPIR_DATE"], errors="coerce")
                cutoff = datetime.now() + timedelta(days=45)
                df = df[df["EXPIR_DATE"] <= cutoff]

            if df.empty:
                self.gamma_status = "No near-term near-spot options after filter."
                return

            df["OPINT_1"] = pd.to_numeric(df["OPINT_1"], errors="coerce").fillna(0)
            df["ACVOL_1"] = pd.to_numeric(df["ACVOL_1"], errors="coerce").fillna(0)
            if "TR.IMPLIEDVOLATILITY" in df.columns:
                df["IV"] = pd.to_numeric(df["TR.IMPLIEDVOLATILITY"], errors="coerce").fillna(0.20)
            else:
                df["IV"] = 0.20

            def bs_gamma(S, K, iv, T=21/365, r=0.04):
                if iv <= 0 or T <= 0 or S <= 0:
                    return 0.0
                try:
                    d1 = (math.log(S/K) + (r + 0.5*iv*iv)*T) / (iv * math.sqrt(T))
                    pdf = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
                    return pdf / (S * iv * math.sqrt(T))
                except Exception:
                    return 0.0

            rows = []
            for _, row in df.iterrows():
                K = float(row["STRIKE_PRC"])
                oi = float(row["OPINT_1"])
                vol = float(row["ACVOL_1"])
                iv = float(row["IV"]) if row["IV"] > 0 else 0.20
                g = bs_gamma(spot, K, iv)
                cp = str(row.get("PUT_CALL", ""))
                sign = 1.0 if cp.upper().startswith("C") else -1.0
                gamma_notional = g * oi * 100 * sign
                rows.append({
                    "strike": K,
                    "oi": oi,
                    "vol": vol,
                    "call_put": cp,
                    "expiry": str(row.get("EXPIR_DATE", ""))[:10],
                    "gamma": gamma_notional,
                    "dist": (K - spot) / spot * 100,
                })

            if not rows:
                self.gamma_status = "No usable rows after computation."
                return

            top = sorted(rows, key=lambda r: r["oi"], reverse=True)[:12]
            self.top_oi = [
                {
                    "Strike": f"{r['strike']:.0f}",
                    "Dist %": f"{r['dist']:+.1f}",
                    "OI": f"{r['oi']:,.0f}",
                    "Vol": f"{r['vol']:,.0f}",
                    "C/P": r["call_put"],
                    "Expiry": r["expiry"],
                }
                for r in top
            ]

            by_strike = {}
            for r in rows:
                by_strike.setdefault(r["strike"], 0.0)
                by_strike[r["strike"]] += r["gamma"]
            gamma_list = sorted(
                [{"strike": k, "gamma": v} for k, v in by_strike.items()],
                key=lambda x: x["strike"],
            )
            self.gamma_chart = gamma_list

            cum = 0.0
            flip = None
            for i, g in enumerate(gamma_list):
                prev = cum
                cum += g["gamma"]
                if prev * cum <= 0 and abs(prev) + abs(cum) > 0:
                    if abs(g["gamma"]) > 0 and i > 0:
                        prev_strike = gamma_list[i-1]["strike"]
                        frac = abs(prev) / (abs(prev) + abs(g["gamma"]))
                        flip = prev_strike + (g["strike"] - prev_strike) * frac
                    else:
                        flip = g["strike"]
                    break
            self.gamma_flip = f"{flip:.0f}" if flip else "—"

            put_oi = sum(r["oi"] for r in rows if str(r["call_put"]).upper().startswith("P"))
            call_oi = sum(r["oi"] for r in rows if str(r["call_put"]).upper().startswith("C"))
            put_vol = sum(r["vol"] for r in rows if str(r["call_put"]).upper().startswith("P"))
            call_vol = sum(r["vol"] for r in rows if str(r["call_put"]).upper().startswith("C"))
            self.put_call_oi = f"{put_oi/call_oi:.2f}" if call_oi else "—"
            self.put_call_vol = f"{put_vol/call_vol:.2f}" if call_vol else "—"

            self.gamma_status = f"Loaded {len(rows)} contracts from {chain_used}. Spot {self.spot}."
        except Exception as e:
            self.gamma_status = f"LSEG error: {type(e).__name__}: {e}"
        finally:
            self.loading = False

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
        rx.link("Term & Skew", href="/term-skew", color=MUTED, font_size="0.85rem", font_family="IBM Plex Mono"),
        rx.link("Gamma", href="/gamma", color=MUTED, font_size="0.85rem", font_family="IBM Plex Mono"),
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
                    rx.text("Implied vs realized. Values appear only from LSEG.", color=MUTED, font_size="0.9rem"),
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
            rx.hstack(
                rx.button("Refresh (LSEG)", on_click=State.refresh, background=ACCENT, color=BG, font_weight="600", disabled=State.loading),
                rx.cond(State.loading, rx.spinner(color=ACCENT, size="2")),
                spacing="3",
                align="center",
            ),
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
                    rx.text("ATM term structure and 25Δ risk reversal for SPX vs QQQ. Tech premium by tenor. Populated only from LSEG IPA ETI surfaces.", color=MUTED, font_size="0.9rem"),
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
            rx.hstack(
                rx.button("Refresh (LSEG)", on_click=State.refresh, background=ACCENT, color=BG, font_weight="600", disabled=State.loading),
                rx.cond(State.loading, rx.spinner(color=ACCENT, size="2")),
                spacing="3",
                align="center",
            ),
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


def gamma_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            nav(),
            rx.hstack(
                rx.vstack(
                    rx.text("HELIOS", font_size="0.7rem", letter_spacing="0.28em", color=ACCENT, font_family="IBM Plex Mono"),
                    rx.heading("Vol Clustering / Gamma Proxy", size="6", color=FG),
                    rx.text("SPX open-interest clusters and estimated gamma profile. Near-term expiries, strikes ±12% of spot. Data from LSEG only.", color=MUTED, font_size="0.9rem"),
                    align_items="start",
                    spacing="1",
                ),
                rx.spacer(),
                rx.badge("LSEG ONLY", variant="outline", color_scheme="teal"),
                width="100%",
                align="end",
            ),
            rx.hstack(
                metric_card("Spot", State.spot, ".SPX"),
                metric_card("Gamma Flip", State.gamma_flip, "cum gamma zero-cross"),
                metric_card("P/C OI", State.put_call_oi, "put / call"),
                metric_card("P/C Vol", State.put_call_vol, "put / call"),
                spacing="3",
                wrap="wrap",
                width="100%",
            ),
            rx.heading("Largest OI Strikes", size="4", color=FG, margin_top="0.5rem"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Strike"),
                        rx.table.column_header_cell("Dist %"),
                        rx.table.column_header_cell("OI"),
                        rx.table.column_header_cell("Vol"),
                        rx.table.column_header_cell("C/P"),
                        rx.table.column_header_cell("Expiry"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        State.top_oi,
                        lambda row: rx.table.row(
                            rx.table.cell(row["Strike"]),
                            rx.table.cell(row["Dist %"]),
                            rx.table.cell(row["OI"]),
                            rx.table.cell(row["Vol"]),
                            rx.table.cell(row["C/P"]),
                            rx.table.cell(row["Expiry"]),
                        ),
                    )
                ),
                width="100%",
                border=f"1px solid {LINE}",
            ),
            rx.heading("Estimated Gamma by Strike", size="4", color=FG, margin_top="1rem"),
            rx.box(
                rx.text(
                    "Gamma profile is Black-Scholes gamma × OI × 100, signed by call (+)/put (−). "
                    "Series is stored in State.gamma_chart for Plotly rendering. "
                    "Gamma flip is the approximate zero-crossing of the cumulative curve.",
                    color=MUTED,
                    font_size="0.85rem",
                    line_height="1.5",
                ),
                padding="1rem",
                border=f"1px solid {LINE}",
                border_radius="0.75rem",
                background=SURFACE,
                width="100%",
            ),
            rx.hstack(
                rx.button("Refresh Gamma (LSEG)", on_click=State.refresh_gamma, background=ACCENT, color=BG, font_weight="600", disabled=State.loading),
                rx.cond(State.loading, rx.spinner(color=ACCENT, size="2")),
                spacing="3",
                align="center",
            ),
            rx.text(State.gamma_status, font_size="0.8rem", color=MUTED),
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
app.add_page(gamma_page, route="/gamma", title="Helios — Gamma")
