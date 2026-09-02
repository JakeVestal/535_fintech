# MENG FinTech · Algorithmic Trading II

# Assignment 1.1 — Option Surface Lab

| Field | Value |
|---|---|
| Assigned | Class 1 |
| Checkpoint | Start of Class 2 — 3-minute live demo. Show progress, ask questions. The site does not have to be published yet. |
| Due | Friday, Sep 04 at midnight |
| Collaboration | Discussion encouraged. Code must be yours (AI-assisted is yours). |
| AI use | Fully permitted and expected. You own every line you submit. |
| Submission | Push to your GitHub repo; the site must render. Submit the link on Canvas. |

This is the first layer of an app that will keep growing all semester. Every homework adds something to the same site.

The job this week is options data — including **expired** contracts — plus the workflow you will use for the rest of the course.

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
- Build an interactive  app with charts and widget switches.
- See, concretely, where the data runs out.

## What to turn in

A link to your GitHub Pages hosted site that contains a working version of 
your app. You can serve it as an html file like we discussed in class, or 
you can take a few extra steps and deploy the frontend portion of your 
app. Your choice, but the html file is probably simplest.
Your app must support the following functionality:

1. Loads the cached LSEG pickle containing your fetched data
2. Parses each RIC into `{underlying, expiry, put/call, strike}` and a tidy long table: one row per contract per date. `parse_option_ric()` already knows the scheme in Appendix A.
3. Shows a 3D figure of puts or calls for one as-of date. An example has 
   been provided for you, yours may differ
4. Plots **both** `MID_PRICE` and `TRDPRC_1` so a stranger can see they are not the same series
5. Prints two numbers on the page:
   - percent of listed series that day with a mid and **no** trade
   - median `|MID_PRICE − TRDPRC_1|` on series that have both
6. Changes the color scheme and format into a graphical identity that you 
   like and are happy with. Be as creative as you want

Write three sentences under the plot:

- Where is the cloud of price data dense, and where is it empty?
- Why is interpolating across empty cells dangerous on a $0.50 strike grid for a name like UUUU?
- Which field will you treat as the mark next week, and which field will you treat as evidence that someone traded?


## The two prices you are not allowed to confuse

- `TRDPRC_1` — last **trade** on that RIC that day. Missing on most listed strikes. When it exists it is one print, not a mark.
- `MID_PRICE` — the closing **NBBO midpoint** — `(bid + ask) / 2` at the exchange close. LSEG does not expose a true exchange settlement price for expired US equity options (the `SETTLE` field returns *"universe does not support"* on this RIC space, and `TR.SettlementPrice` comes back empty), so `MID_PRICE` is the closest mark-of-the-close we get. Exists on far more series than trades. On a name that barely trades it is still a mid of a possibly-stale quote.

If you feed `TRDPRC_1` into a surface and then read prices off the holes, you are pricing off prints that did not happen.

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

### Three things to be aware of

- The starter generates a candidate for every Friday in the window. If your name only lists monthlies, most of those come back empty. That is expected.
- If the underlying split inside your window, the synthetic RICs will not find the adjusted contracts. Check. If it split, pick something else.

If the pull is uncomfortably slow, the starter is taking the high and low across the **entire** window and generating every strike in between for every expiry. Banding strikes per expiry cuts the request count a lot. Optional, but it will save you time.
#### OPRA month codes

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
