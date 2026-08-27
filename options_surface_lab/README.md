# MENG FinTech · Algorithmic Trading II

# Assignment 1.1 — The Covered Call

| Field | Value |
|---|---|
| Assigned | Class 1 |
| Checkpoint | Start of Class 2 — 3-minute live demo. Show progress, ask questions. The site does not have to be published yet. |
| Due | Friday, Sep 04 at midnight |
| Collaboration | Discussion encouraged. Code must be yours (AI-assisted is yours). |
| AI use | Fully permitted and expected. You own every line you submit. |
| Submission | Push to your GitHub repo; the site must render. Submit the link on Canvas. |

This is the first layer of an app that will keep growing all semester. Every homework adds something to the same Reflex site.

The job this week is options data — including **expired** contracts — plus the Reflex workflow you will use for the rest of the course.

> **What you are actually going to discover:** options data is sparse. Many 
> of the contracts you want have no price on the day you want it for the 
> strike you want. That is the nature of the instrument. Simulating a realistic 
> fill on an option that barely trades requires the volatility surface, 
> which is next week. For example, what was the price of the near-the-money 
> contract on *morning*, not the close?
> This week you only need to *see* the holes. For the next assignment we 
> will fold in the volatility surface and calculate reasonable simulated fills.

## Learning objectives

- Pull and cache historical prices for expired option contracts.
- Treat options data as sparse and misleading, not as a filled sheet.
- Build an interactive Reflex app with charts and widget switches.
- See, concretely, where the data runs out.

## What to turn in

A Reflex page (AI is allowed and expected) that:

1. Loads the cached LSEG frame. Do not re-pull unless the pickle is missing.
2. Parses each RIC into `{underlying, expiry, put/call, strike}` and a tidy long table: one row per contract per date. `parse_option_ric()` already knows the scheme in Appendix A.
3. Shows a 3D figure of puts or calls for one as-of date.
4. Plots **both** `SETTLE` and `TRDPRC_1` so a stranger can see they are not the same series.
5. Prints two numbers on the page:
   - percent of listed series that day with a settle and **no** trade
   - median `|SETTLE − TRDPRC_1|` on series that have both
6. Changes the color scheme and format into a graphical identity that you 
   like and are happy with. Be as creative as you want.

Write thee sentences under the plot:

- Where is the cloud of price data dense, and where is it empty?
- Why is interpolating across empty cells dangerous on a $0.50 strike grid for a name like UUUU?
- Which field will you treat as the mark next week, and which field will you treat as evidence that someone traded?

and think to yourself:
- On a strike that has a settle and no print, what price would you actually 
  get filled at? (You do not know. That is the answer. You can take a shot 
  at this but it won't be graded until Homework 1.2 is turned in)

The site must render from your GitHub repo. Checkpoint is a live demo, not a 
finished publish. Just get as far as you can becuase its a great chance to 
ask questions. Distance students: send a teams message to the instructors 
and we'll schedule your three minutes!

## The two prices you are not allowed to confuse

- `TRDPRC_1` — last **trade** on that RIC that day. Missing on most listed strikes. When it exists it is one print, not a mark.
- `SETTLE` — exchange **settlement / official mark**. Exists on far more series than trades. Used for margining and for “the close.” On a name that barely trades it is still a model-ish number.

If you feed `TRDPRC_1` into a surface and then read prices off the holes, you are pricing off prints that did not happen.

## What the 3D plot is doing

- **X** strike, **Y** days to expiry, **Z** option price in dollars.
- Cyan: `SETTLE`.
- Magenta diamonds: `TRDPRC_1`.
- Translucent sheet: linear interpolation of the settles. That sheet is **not** the market. Toggle it off.

The occupancy heatmaps underneath are the honest picture. Dark cells never had a number.

## Files in this lab

When you build this, make sure it has the following file structure. * can be 
whatever you want it to be; e.g., "homework1", or nothing, but there must be a 
`*app.py`, a `*data.pkl` for your data, `*utils.py` for your workhorse 
functions, and a `*plot.py` for your plotting code.

| File        | What it is                                                                                                      |
|-------------|-----------------------------------------------------------------------------------------------------------------|
| `*app.py`   | Reflex page. Keep `option_surface_utils.py` and `option_surface_plots.py` next to it.                           |
| `*data.pkl` | Your LSEG cache. Used if present. If missing, the app synthesizes a sparse UUUU-like panel so you can still plot. |
| `*utils.py` | Helper functions                                                                                                |
| `*plot.py`  | Contains all your plots
You can also output a `preview.html` file if Reflex is being annoying and 
you find it helpful.

Starter script builds RICs synthetically. It does **not** query the 
derivatives chain. That endpoint does not reliably return expired contracts. 
Do not spend time on it unless you enjoy frustration.

## Helpful guidance

### Parse the RICs

The options frame comes back with RIC strings as column names. Turn each one into `(underlying, expiry, type, strike)` and melt to long format.

The starter builds identifiers instead of walking a chain, because the chain endpoint fails on expired contracts.

```
{ROOT}{M}{DD}{YY}{SSSSS}.U^{M}{YY}
```

| Element | Meaning |
|---|---|
| `ROOT` | Underlying root, uppercase (e.g. `UUUU`) |
| `M` | Month letter: `A–L` = Jan–Dec **calls**; `M–X` = Jan–Dec **puts** |
| `DD` | Two-digit expiration day |
| `YY` | Two-digit year |
| `SSSSS` | Strike × 100, zero-padded to five digits (`$12.50` → `01250`) |
| `.U` | Exchange / venue qualifier |
| `^{M}{YY}` | Expired-contract suffix; repeats the month letter and year |

Example: `UUUUA1502601250.U^A26` is the UUUU 15-Jan-2026 **call** struck at $12.50.

Synthetic construction means many of the RICs you generate never existed. Request in batches, tolerate failures, fall back to single RICs when a batch throws. The starter already does this.

### Two things to be aware of

- The starter generates a candidate for every Friday in the window. If your name only lists monthlies, most of those come back empty. That is expected.
- If the underlying split inside your window, the synthetic RICs will not find the adjusted contracts. Check. If it split, pick something else.

If the pull is uncomfortably slow, the starter is taking the high and low across the **entire** window and generating every strike in between for every expiry. Banding strikes per expiry cuts the request count a lot. Optional, but it will save you time.

## Stretch (not required)

- Slice by moneyness (`K / S`) instead of raw strike so two dates are comparable.
- Invert Black–Scholes on the settles to get a crude IV surface. Use a constant rate. Write down what you assumed. Next week: that IV still is not the price you can trade.
- Overlay the underlying close on the as-of date as a vertical plane at `K = S`.

## Do not

- Do not treat a linearly interpolated sheet as bid or ask.
- Do not drop rows with missing `TRDPRC_1` and then claim the remaining cloud is “the” surface.
- Do not use `CLOSE` and `SETTLE` as synonyms without checking the field list. This pull requested `TRDPRC_1` and `SETTLE` only.
- Do not spend time on the LSEG derivatives-chain endpoint for expired contracts. It has already been tried.

## Appendix A — OPRA month codes

| Month | Call | Put |
|---|---|---|
| Jan | A | M |
| Feb | B | N |
| Mar | C | O |
| Apr | D | P |
| May | E | Q |
| Jun | F | R |
| Jul | G | S |
| Aug | H | T |
| Sep | I | U |
| Oct | J | V |
| Nov | K | W |
| Dec | L | X |
