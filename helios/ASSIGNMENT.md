# FINTECH 535 — Covered Call Backtest

**Due:** [set in Canvas]  
**Turn in:** your GitHub Pages URL.  
**The static site is 100% of the grade.** I will not grade a data fetcher, a Node app, or whether Workspace still works at turn-in time.

I grade **analysis, thoughtfulness, and how you implemented the theory** — the book, the rules, the charts, the write-up.

## Two surfaces, one grade

| Surface | Role | Graded? |
|---|---|---|
| **Pages** (`gh-pages/`) | Blotter, ledger, NAV/margin, write-up | **Yes. This is the assignment.** |
| **Local Data** | How you *get* the tape (Workspace) | No. A tool, not a deliverable. |

GitHub Pages cannot run LSEG. A Data page on Pages must fail loudly with **“Data connection required”** and tell the reader to run it locally. Helios does that at `gh-pages/helios/data.html`.

Local pull (optional, same static files):

```bash
# Workspace open and signed in
python3 helios/python/local_server.py
# http://127.0.0.1:8765/helios/data.html
```

Download JSON from Data, bake what you used into `book.js` (or equivalent), push `gh-pages/`. The published blotter must render with JavaScript off the baked file. No live endpoint.

Node / Vite / TanStack are not required. HTML, CSS, JS, JSON is the stack.

## Strategy (the theory you implement)

Backtest a **covered call** on one U.S. equity (Helios sample: `UUUU`).

1. Buy **100 shares**.
2. Sell **1 call**, target **~5 DTE**.
3. Each week: expire, assign, or **roll** — your rules, written on the site.
4. ~10 weeks of history; strikes from a bit below the window low to a bit above the high.

Show **fills you actually booked**, not a signal overlay.

## What the Pages site must contain

- **Blotter** — time, instrument, side, qty, price, notes
- **Ledger** — stock, short calls, cash over time
- **Reg T accounts** — NAV, cash, initial (50% of stock LMV; covered short call adds $0), maintenance (25% of LMV), available funds (NAV − initial), excess (NAV − maintenance)
- **NAV and margin paths** with mouseover values
- **Write-up:** fill rule, roll rule, pin/assignment, **why Reg T not portfolio margin** (computable without a broker PM engine; not broker-dependent; if it lives in Reg T it lives in PM, not the reverse)
- Optional: mid = (bid+ask)/2 vs trade and R², as a figure or table on the same site

## Rubric (100% the published site)

| | |
|---|---|
| Thoughtful rules (5 DTE, fill, roll, pin) written clearly | 25 |
| Blotter + ledger that actually implement those rules | 25 |
| Reg T NAV / IM / MM / available funds, used correctly | 20 |
| Charts / presentation that make the book readable | 15 |
| Analysis: what happened, what you’d change, where theory met tape | 15 |

A Data page that still tries LSEG on github.io is a defect. Show the disconnect banner instead.

## Example

https://jakevestal.github.io/535_fintech/helios/  
(after `add/helios` is merged to `main`)

Copy `gh-pages/helios/`, replace `book.js`, keep `data.html` as the local-only lab.
