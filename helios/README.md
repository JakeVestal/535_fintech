# Helios Tape

Example covered-call backtest app for FINTECH 535.

Two pages:

| Route | What | Needs Workspace? |
|---|---|---|
| `/` Blotter | Sample book: trades, ledger, NAV, Reg T margin | No. This is the GitHub Pages–safe turn-in. |
| `/data` Data | Search equities, fetch OHLC, pull weekly calls, midpoint vs trade | Yes. LSEG Workspace must be running locally. |

The Data page talks to `POST /api/lseg`, which spawns `python/lseg_bridge.py` against the Workspace desktop session. It will not work on GitHub Pages.

## Run locally

Needs **LSEG Workspace** open and signed in (desktop proxy on port 9000).

```bash
cd helios
python3 -m pip install -r requirements.txt
npm install
npm run dev
```

Open the URL Vite prints. Search an equity (try `UUUU`), Fetch hourly bars, then Pull weeklies.

A `AbortError` / `ssr connected` line in the terminal on restart is noise from TanStack hydrating an old tab. Watch the **status line under Fetch**, not that dump.

## Layout

- `python/lseg_bridge.py` — desktop session, search, OHLC, option RICs
- `python/option_rics.py` — expired-call RIC builder (`UUUUH212601450.U^H26`)
- `src/lib/lseg.server.ts` — one Python process, queued
- `src/lib/lseg.functions.ts` — browser `POST /api/lseg`
- `src/routes/data.tsx` — Data page
- `src/routes/index.tsx` — Blotter / ledger / NAV
- `src/lib/sample-book.ts` — example covered-call blotter (Reg T)

## Assignment shape (draft)

1. Pull stock + weekly calls for a name you choose.
2. Write a covered call (~5 DTE): buy 100 shares, sell 1 call.
3. Log fills on the blotter; track stock, short calls, and cash on the ledger.
4. Compute NAV, initial margin, maintenance, available funds under **Reg T** (not portfolio margin).
5. Turn in the Blotter page (static). Keep Data local.
