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
        # Explicit no-op until LSEG IPA surface call is wired.
        # Do not invent numbers. Do not call any public data source.
        self.status = "LSEG IPA surface not yet called. Fields remain blank. No fallback used."
        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M")

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

def term_skew_page() -> rx.Component:
    term_rows = [
        {"Tenor": t, "SPX ATM": s, "QQQ ATM": q, "Premium": p}
        for t, s, q, p in zip(
            State.tenors, State.spx_atm, State.qqq_atm, State.premium_by_tenor
        )
    ]
    skew_rows = [
        {"Tenor": t, "SPX 25Δ RR": sr, "QQQ 25Δ RR": qr}
        for t, sr, qr in zip(State.tenors, State.spx_rr25, State.qqq_rr25)
    ]

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
                    rx.foreach(
                        term_rows,
                        lambda row: rx.table.row(
                            rx.table.cell(row["Tenor"]),
                            rx.table.cell(row["SPX ATM"]),
                            rx.table.cell(row["QQQ ATM"]),
                            rx.table.cell(row["Premium"]),
                        )
                    )
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
                    rx.foreach(
                        skew_rows,
                        lambda row: rx.table.row(
                            rx.table.cell(row["Tenor"]),
                            rx.table.cell(row["SPX 25Δ RR"]),
                            rx.table.cell(row["QQQ 25Δ RR"]),
                        )
                    )
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
    theme=rx.theme(appearance="dark", accent_color="teal", radius="large"),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
    ],
)
app.add_page(vrp_page, route="/", title="Helios — VRP")
app.add_page(term_skew_page, route="/term-skew", title="Helios — Term & Skew")
