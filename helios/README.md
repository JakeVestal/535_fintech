# Helios — Relative Value Monitor

Reflex dashboard for options relative value and flow monitoring.

## Data policy
No fallbacks. No yfinance. No simulated series presented as market data.
Values appear only when pulled from LSEG/Refinitiv (IPA surfaces, Workspace session) or an official government source. Otherwise the field stays blank and the status reports the missing source.

## Modules
- Variance Risk Premium (VIX / realized) — requires LSEG
- Term structure & skew — ATM term structure and 25Δ risk reversal for SPX vs QQQ; tech premium by tenor. Requires LSEG IPA ETI surfaces.

## Run
```bash
cd helios
pip install -r requirements.txt
reflex run
```
