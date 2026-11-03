# VRP Simple Webpage (IBKR)

Requires TWS or IB Gateway paper trading running with API enabled on port 7497.

Run from the `helios` directory:

```
uvicorn vrp_simple.server:app --reload --port 8000
```

Open http://localhost:8000

Click "Refresh (IBKR)" to pull VIX and SPX realized vol via IBKR.
