#!/usr/bin/env python3
"""Helios Tape class deck — dark / cyan, matching the site."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import nsmap
from pptx.util import Emu, Inches, Pt

BG = RGBColor(0x07, 0x0B, 0x10)
SURFACE = RGBColor(0x10, 0x18, 0x20)
LINE = RGBColor(0x24, 0x31, 0x3C)
FG = RGBColor(0xE8, 0xF6, 0xF3)
MUTED = RGBColor(0x8A, 0xA8, 0xA4)
ACCENT = RGBColor(0x2E, 0xE6, 0xD0)
ICE = RGBColor(0x9E, 0xF6, 0xEA)
DOWN = RGBColor(0xFF, 0x6B, 0x8A)

W = Inches(13.333)
H = Inches(7.5)
OUT = Path("/workspace/public/helios-covered-calls.pptx")


def _set_run(run, text, size, color, bold=False):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = "Calibri"
    run.font.italic = False


def fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def bar(slide, y=0):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(y), W, Inches(0.08))
    fill(s, ACCENT)
    s.shadow.inherit = False


def slide_bg(prs):
    sld = prs.slides.add_slide(prs.slide_layouts[6])
    bg = sld.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), W, H)
    fill(bg, BG)
    bg.shadow.inherit = False
    return sld


def textbox(slide, l, t, w, h, text, size=18, color=FG, bold=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    _set_run(run, text, size, color, bold)
    return box


def kicker(slide, text, top=0.28):
    textbox(slide, 0.7, top, 12, 0.35, text.upper(), 12, ACCENT, True)


def title(slide, text, top=0.55):
    textbox(slide, 0.7, top, 12, 0.7, text, 32, FG, True)


def bullets(slide, items, left=0.7, top=1.5, width=12, height=5.4, size=18):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = 0
        p.space_after = Pt(10)
        p.line_spacing = 1.15
        run = p.add_run()
        _set_run(run, "▸  " + item, size, FG if i % 5 != 4 else ICE, False)
    return box


def card(slide, l, t, w, h, head, body):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    fill(sh, SURFACE)
    sh.line.color.rgb = LINE
    sh.adjustments[0] = 0.08
    textbox(slide, l + 0.2, t + 0.12, w - 0.35, 0.35, head, 13, ACCENT, True)
    textbox(slide, l + 0.2, t + 0.48, w - 0.35, h - 0.6, body, 15, FG)


def build():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H

    # 1 title
    s = slide_bg(prs)
    bar(s, 0)
    kicker(s, "Helios Tape  ·  homework briefing")
    title(s, "Covered calls you can actually keep", 1.6)
    textbox(
        s,
        0.7,
        2.5,
        11,
        1.4,
        "Writing ~5 DTE calls against 100-share lots. Blotter, ledger, Reg T margin,\n"
        "rolling rules, fills, and pin risk — plus why we stay on Regulation T.",
        20,
        MUTED,
    )
    textbox(s, 0.7, 6.6, 11, 0.4, "Same book as the Helios Tape site  ·  dark tape, cyan ink, no glow", 14, ACCENT)

    # 2 agenda
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Agenda")
    title(s, "What we will actually do")
    bullets(
        s,
        [
            "Covered call = long 100 shares + short 1 call. Premium is income; upside is capped.",
            "Blotter is fills only. Ledger is the running book: stock, short options, cash.",
            "Roll ~5 DTE. Decide: let it expire, close, or roll. Assignment is a trade, not a surprise.",
            "Fills vs mids — we will test last week’s assumption on the Data page (R²).",
            "Reg T accounts: cash, NAV, initial, maintenance, available funds. Not portfolio margin.",
        ],
    )

    # 3 covered call
    s = slide_bg(prs)
    bar(s)
    kicker(s, "The structure")
    title(s, "A covered call is two fills")
    card(s, 0.7, 1.6, 5.8, 2.3, "Long the stock", "Buy 100 shares. This is the inventory you are willing to sell. Delta ≈ +100 shares. You fund it with cash or margin. It posts Reg T initial (50% of LMV).")
    card(s, 6.8, 1.6, 5.8, 2.3, "Short the call", "Sell 1 call, same name, ~5 DTE, typically a bit OTM. Multiplier 100. Premium hits cash today. The call is covered, so it does not post naked-option margin.")
    card(s, 0.7, 4.15, 5.8, 2.4, "If it expires OTM", "The call dies at 0. You keep the premium. You still own the shares. Next week you can write again. This is the base case for a quiet tape.")
    card(s, 6.8, 4.15, 5.8, 2.4, "If it finishes ITM", "You can be assigned: shares called away at strike. P&L = (strike − cost) + net premium. Or you roll before the bell. Pin risk lives in that last afternoon.")

    # 4 payoff
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Payoff")
    title(s, "You sold the upside above the strike")
    bullets(
        s,
        [
            "Max gain ≈ (strike − stock entry) + net premium received. You will not participate above the strike.",
            "Max loss ≈ stock can go to zero, minus premium. Covered calls are not a hedge against a crash.",
            "Breakeven ≈ stock entry − net premium. The call only cushions a little.",
            "That is why strike choice matters: too close and you get called; too far and you get paid nothing.",
            "Your backtest should report NAV, not just “premium harvested.” Called-away weeks change the stock basis.",
        ],
    )

    # 5 blotter vs ledger
    s = slide_bg(prs)
    bar(s)
    kicker(s, "The book")
    title(s, "Blotter ≠ ledger")
    card(s, 0.7, 1.6, 5.8, 4.8, "Blotter — trades you made",
         "Time, side, qty, instrument, price, cash delta, note.\n\n"
         "BUY 100 UUUU @ 12.90\n"
         "SELL 1 7/3 13.5C @ 0.22\n"
         "BTC 1 7/10 13.5C @ 0.06   (the close of a roll)\n"
         "SELL 1 7/17 14.0C @ 0.21  (the new write)\n"
         "EXPIRE @ 0.00             (OTM, still a row)\n\n"
         "Working orders and “I would have” do not go here.")
    card(s, 6.8, 1.6, 5.8, 4.8, "Ledger — the position through time",
         "After every mark: cash, shares, short calls, spot, LMV, option MV, NAV.\n\n"
         "NAV = cash + stock market value + option market value\n"
         "(short options are negative).\n\n"
         "Then the margin columns: initial, maintenance, available funds, excess equity.\n\n"
         "If the blotter and the ledger disagree, the blotter is wrong or a fill is missing.")

    # 6 rolling
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Rolling rules")
    title(s, "~5 DTE, then decide")
    bullets(
        s,
        [
            "Default: write a call that expires about five calendar days out (the next weekly).",
            "Hold into expiry only if you are happy to sell the shares at strike, and the print is not glued to it.",
            "Roll = buy to close the current short, sell a later (and maybe higher) call in one thought, two fills.",
            "Roll out: same strike, next week. Roll up: higher strike when the stock has run. Roll down is usually you paying.",
            "Write the rule before you see the tape: e.g. “if short call delta > 0.55 with one session left, BTC and roll up.”",
            "Do not invent the rule on Friday at 3:50. That is how pin risk becomes a story you tell next week.",
        ],
        size=17,
    )

    # 7 fills
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Fills")
    title(s, "A limit is not a trade")
    bullets(
        s,
        [
            "The blotter records the price you got, not the mid you wanted. Slippage is part of the strategy.",
            "Last week: we assumed the trade sits near the bid/ask midpoint. Test that on Data — scatter trade vs mid, report R².",
            "If R² is high and slope ≈ 1, marking the book on mid is honest. If not, your backtest is marking fantasy fills.",
            "Opening a short call: you are selling. You may print on the bid. Closing (BTC): you may print on the ask. That spread is a cost.",
            "Weeklies on names like UUUU can be wide. A 0.05 wide market on a 0.20 option is a lot of edge you do not have.",
        ],
        size=17,
    )

    # 8 pin risk
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Pin risk")
    title(s, "The stock loves the strike on expiry day")
    bullets(
        s,
        [
            "Pin: spot sits on your short strike into the close. Assignment is a coin toss after the bell.",
            "If assigned, you sell the shares at strike. Over the weekend you are flat stock you still wanted — or still long stock you thought was called.",
            "Monday gap is then unhedged. That is the risk, not the 0.02 of extra premium.",
            "Operational: OCC assignment is random among shorts. You will not know Friday night with certainty.",
            "Practical rule: if you are at-the-money Friday afternoon, BTC. Do not harvest the last tick of theta if you cannot live with the stock disappearing.",
            "Your sample book shows one ITM BTC on 24 Jul — that is the roll that exists to avoid the pin.",
        ],
        size=17,
    )

    # 9 Reg T accounts
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Reg T")
    title(s, "The accounts on the home page")
    card(s, 0.7, 1.55, 4.0, 2.4, "Cash", "Settled dollars. Buys spend it. Short calls credit it. BTC debits it. Expiry at 0 does nothing to cash — premium was already yours.")
    card(s, 4.85, 1.55, 4.0, 2.4, "LMV / stock", "Shares × mark. This is the collateral that covers the short call. 100 shares cover 1 call. No more.")
    card(s, 9.0, 1.55, 3.6, 2.4, "Option MV", "Short × mark × 100. Negative if you are short. NAV includes this mark-to-market.")
    card(s, 0.7, 4.15, 4.0, 2.4, "NAV / equity", "Cash + LMV + option MV. The number that should grow if the strategy works. Not “premium collected.”")
    card(s, 4.85, 4.15, 4.0, 2.4, "SMA (idea)", "Reg T leftover buying power. We show available funds instead: NAV − initial. Same spirit, fewer broker quirks.")
    card(s, 9.0, 4.15, 3.6, 2.4, "Excess equity", "NAV − maintenance. When this hits 0, you are at a margin call. Do not write size that lives here.")

    # 10 initial vs maint
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Reg T  ·  FINRA 4210")
    title(s, "Initial vs maintenance, covered")
    bullets(
        s,
        [
            "Long equity initial (Reg T): 50% of current LMV. You post this to put the shares on.",
            "Long equity maintenance (FINRA): 25% of LMV. Overnight you must stay above this.",
            "Covered short call: the shares cover the call. There is no extra naked-call haircut. Premium credits cash, which helps.",
            "Naked call (do not do this in the homework): ~20% of underlying + ITM − premium, with a 10% floor. Much heavier. Covered is the point.",
            "Available funds ≈ NAV − initial. That is what you can still put toward another 100-share lot.",
            "If NAV < maintenance → margin call. You close or deposit. Your backtest should flag this; do not pretend the broker waited.",
        ],
        size=17,
    )

    # 11 available funds
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Capacity")
    title(s, "Available funds are the speed limit")
    bullets(
        s,
        [
            "A pretty yield on one lot does not mean you can scale. The next 100 shares need initial margin too.",
            "Writing a tighter strike does not free capital — the stock is what posts. The call only changes NAV through its mark and the premium.",
            "If the stock rips, LMV rises, initial rises, available funds shrink even as NAV is up. You can be rich and tight at the same time.",
            "If the stock dumps, LMV falls (easier initial) but NAV falls faster. Maintenance is the one that bites.",
            "Track available funds on every ledger row. That is the homework-relevant risk metric, not just max-pain of the call.",
        ],
        size=17,
    )

    # 12 why not PM
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Why Regulation T")
    title(s, "Not portfolio margin")
    bullets(
        s,
        [
            "Easier to calculate. 50% / 25% of LMV, covered call adds $0. You can do it on paper without a SPAN file.",
            "Not broker-dependent. PM haircuts are house models (TIMS/SPAN + broker add-ons). Two brokers, two numbers. Reg T is the same exam question.",
            "If it works in Reg T, it will work in PM. PM is looser for hedged books. The reverse is false: a PM-sized book can be illegal / unfundable on Reg T.",
            "Your classmates will not all have PM accounts. Grade the strategy on the constraint everyone shares.",
            "We are not saying PM is bad. We are saying the homework constraint is the conservative one on purpose.",
        ],
        size=17,
    )

    # 13 data page
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Data")
    title(s, "What you pull, what you test")
    bullets(
        s,
        [
            "Data page talks to local LSEG Workspace. GitHub Pages will not. The blotter page is the turn-in surface.",
            "Search the name, fetch OHLC, then pull weeklies in the traded high/low (plus a step of OTM).",
            "Cache is keyed expiry|strike so you can build a daily surface and pick ~5 DTE calls.",
            "Then the scatter: every bar with a trade and a two-sided quote. Mid = (bid+ask)/2 vs TRDPRC_1. OLS + R².",
            "If trades do not track the mid, your fill model is the first thing to fix — before rolling rules.",
        ],
        size=17,
    )

    # 14 turn-in
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Turn-in")
    title(s, "What I want to see")
    bullets(
        s,
        [
            "A blotter of fills: stock + written calls + any BTC/rolls/expiries. No phantom trades.",
            "A ledger that still adds up: cash, shares, short calls, NAV, initial, maintenance, available funds.",
            "A rule for ~5 DTE writes and a rule for rolling vs pin. Written before the results.",
            "The midpoint scatter and R² from your name. Tell me whether last week’s assumption survived.",
            "Host the static blotter/results. Keep the LSEG fetch page for local work only.",
        ],
        size=18,
    )

    # 15 close
    s = slide_bg(prs)
    bar(s)
    kicker(s, "Helios Tape")
    title(s, "Write it small, mark it honest, roll on purpose.", 2.2)
    textbox(
        s,
        0.7,
        3.3,
        11,
        1.2,
        "Questions: blotter vs ledger, Reg T vs PM, or the midpoint test.\nThe sample book on the site is a template — not the answer.",
        20,
        MUTED,
    )
    textbox(s, 0.7, 6.5, 11, 0.4, "Deck matches the site: #070b10  ·  #2EE6D0  ·  no glow", 14, ACCENT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    build()
