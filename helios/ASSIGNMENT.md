# FINTECH 535 — Covered Call Backtest

**Due:** [set in Canvas]  
**Turn in:** a GitHub Pages site (or static export) of your **Blotter** page, plus the repo link.  
**Do not** turn in a live LSEG Data page. Workspace calls will not run on Pages.

## What you are building

A two-page app, same split as the Helios example (`helios/` in this repo):

| Page | Purpose | Where it runs |
|---|---|---|
| **Data** | Pull stock + listed calls from LSEG Workspace | Your machine only |
| **Blotter** | The book you actually traded: fills, ledger, NAV, margin | What you publish |

Helios is an example, not a template you must fork. You may use it, or rebuild in whatever stack you can defend.

## Strategy

Backtest a **covered call** on one U.S. equity you choose (Helios uses `UUUU` as the walkthrough).

1. Buy **100 shares**.
2. Sell **1 call**, target **~5 DTE** (weeklies).
3. Each week: **let it expire**, **get assigned**, or **roll** (your rules — write them down).
4. Horizon: about **10 weeks** of history, plus enough forward expiries to see the next ~5 weeks of weeklies.

You need enough option history to know what you *could* have written: strikes from a bit below the stock’s low in the window to a bit above its high (Helios pads ~0.5–1.0 strike past the high).

## Data (local)

Workspace must be open and signed in. Prefer **hourly** bars for the first pull; 1-minute over 10 weeks is slow and easy to abort.

For each call you care about, store at least:

- `TRDPRC_1` (last)
- `OPEN_BID` / `OPEN_ASK`

Cache by **strike × expiry**. Expired U.S. equity calls look like the Helios example:

```
UUUUH212601450.U^H26
```

root + month code + day + YY + strike×100 + `.U` + `^` expiry suffix. Live contracts omit the `^…` suffix. Guess-and-check RICs must fail soft (empty series, not a crash).

After you have trades and quotes, plot **mid = (bid+ask)/2** vs trade price and report **R²**. That checks last week’s assumption that prints track the mid.

## Blotter (turn-in)

This is a list of **trades you actually booked**, not a signal chart.

Minimum columns: time, asset (stock or call RIC), side, qty, price, fee if you want it.

**Ledger** (snapshot over time):

- long stock (shares)
- short calls (contracts, strike, expiry)
- cash

**Accounts** (Reg T, cash account / margin account as you specify — default **Reg T**):

- NAV
- cash
- initial margin
- maintenance margin
- available funds

Why **Reg T**, not portfolio margin: it is computable without a broker SPAN/PM engine, it is not broker-dependent, and a book that survives Reg T will survive PM. The converse is false.

Include a NAV path and a margin path. Mouseover values on the plots.

## Rolling, fills, pin

Your write-up (one page in the repo README is enough) must define:

- **Fill rule** — mid? bid? last? skip if no print?
- **Roll rule** — when, to which expiry/strike, at what debit/credit
- **Pin / assignment** — what you do into expiry week if spot is near strike

## Practical limits (so this is finishable)

- One name, one 10-week window.
- Hourly (or daily) options history matching the stock bar size.
- One RIC at a time against Workspace; batch universe lists are unreliable on the desktop session.
- Ignore TanStack `AbortError` on `ssr connected` if you use the Helios stack — watch the Data page status line.
- If Workspace is down, the Data page should say so; the Blotter must still render from saved/sample data.

## Rubric (draft)

| | |
|---|---|
| Data pull + cache by strike/expiry | 20 |
| Covered-call rules in writing (5 DTE, roll, fill, pin) | 20 |
| Blotter + ledger that match those rules | 25 |
| Reg T NAV / IM / MM / available funds | 20 |
| Mid vs trade + R² | 10 |
| Pages-safe Blotter; Data not required at grade time | 5 |

## Example

```bash
cd helios
python3 -m pip install -r requirements.txt
npm install
npm run dev
```

Workspace running → Data → search `UUUU` → Fetch hourly → Pull weeklies. Blotter is the sample book at `/`.
