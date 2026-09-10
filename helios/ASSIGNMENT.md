# FINTECH 535 — Covered Call Backtest

**Due:** [set in Canvas]  
**Turn in:** your GitHub Pages URL. The graded site must be **static** (HTML / JS / CSS / JSON).  
**Do not** turn in a live LSEG page. Workspace calls will not run on Pages.

## The split (non-negotiable)

| Where | What |
|---|---|
| **Your machine** | LSEG Workspace + Python (or any local tool) to pull stock and listed calls |
| **GitHub Pages** | Backtest, blotter, ledger, charts, write-up |

Node / Vite / TanStack / Reflex are **not** required. If a stack needs a server, it is a local lab only. Bake results into files under `gh-pages/` (this repo already deploys that folder).

Helios example (what Pages serves): `gh-pages/helios/` — `index.html`, `styles.css`, `app.js`, `book.js`. Replace `book.js` with your book. No build step.

## Strategy

Backtest a **covered call** on one U.S. equity (Helios uses `UUUU`).

1. Buy **100 shares**.
2. Sell **1 call**, target **~5 DTE** (weeklies).
3. Each week: **let it expire**, **get assigned**, or **roll** — write the rules down.
4. Horizon: about **10 weeks**, plus enough forward weeklies to see ~5 weeks past the last stock bar.

Strikes: from a bit below the stock’s low in the window to a bit above its high.

## Local data (not graded at the URL)

Workspace open and signed in. Prefer **hourly** bars. For each call, keep `TRDPRC_1`, `OPEN_BID`, `OPEN_ASK`. Cache by strike × expiry. Expired U.S. equity RICs look like `UUUUH212601450.U^H26`. Guess-and-check must fail soft.

Plot **mid = (bid+ask)/2** vs trade and report **R²** (can live on the Pages write-up as a figure or table).

## Pages site (graded)

Must show:

**Blotter** — trades you actually booked: time, asset, side, qty, price.

**Ledger** over time: long stock, short calls, cash.

**Accounts (Reg T):** NAV, cash, initial margin (50% of stock LMV; covered short call adds $0), maintenance (25% of LMV), available funds (NAV − initial), excess (NAV − maintenance).

NAV path and margin path with mouseover values.

**Write-up on the same site:**

- Fill rule (last? bid? skip if no print?)
- Roll rule (when, which expiry/strike)
- Pin / assignment
- Why **Reg T** not portfolio margin: computable without a broker PM engine, not broker-dependent; a book that lives in Reg T lives in PM, not the other way around.

## Practical limits

- One name, one window, hourly or daily.
- One RIC at a time against Workspace.
- If you keep a local Data explorer, it is extra. The URL must render with JavaScript off the baked `book.js` (or equivalent).

## Rubric (draft)

| | |
|---|---|
| Data actually used (and R² mid vs trade) | 20 |
| Rules in writing (5 DTE, roll, fill, pin) | 20 |
| Blotter + ledger that match those rules | 25 |
| Reg T NAV / IM / MM / available funds | 20 |
| Pages-safe static site (opens without Workspace) | 15 |

## Example

Local (optional): `helios/` Vite app if you want a Workspace UI.

Published: open `gh-pages/helios/index.html` or, after merge to `main`:

https://jakevestal.github.io/535_fintech/helios/
