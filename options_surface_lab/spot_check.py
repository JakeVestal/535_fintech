"""Spot-check the app against the raw dataframes for one as-of date.

Prints only — no charts. All values match what the app should display on
its Overview metrics and (implicitly) in the surface / compare / heatmap
figures for the chosen as-of date. Use this to eyeball individual rows.

Run from anywhere:
    ..\\venv\\Scripts\\python.exe HW1\\options_surface_lab\\spot_check.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Name-collision workaround: `options_surface_lab/` (the package) also
# contains `options_surface_lab.py` (the Reflex entry-point shim). Put
# HW1/ on sys.path so the package always wins the import, and chdir to
# HW1 so the pickle cache resolves by its relative filename.
_HW1 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HW1))
os.chdir(_HW1)

import pandas as pd

from options_surface_lab.options_surface_app import load_or_fetch_pipeline_data, _prepare

# ---------------------------------------------------------------------------
# what to spot-check
# ---------------------------------------------------------------------------
ASOF = pd.Timestamp("2026-07-15")

# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------
payload = load_or_fetch_pipeline_data()
tidy, wide, payload = _prepare(payload)

if ASOF not in set(wide["date"]):
    available = sorted({str(d.date()) for d in wide["date"]})
    raise SystemExit(f"{ASOF.date()} not in data. Available: {available[:12]} ...")

pd.set_option("display.max_rows", 400)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 30)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")

# ---------------------------------------------------------------------------
# 1. Overview metrics — match these against the app's Overview cards
# ---------------------------------------------------------------------------
sl = wide[wide["date"] == ASOF].copy()
spot = float(payload["stock"].loc[ASOF, "TRDPRC_1"]) if ASOF in payload["stock"].index else None

n = len(sl)
n_both = int((sl["has_trade"] & sl["has_mid"]).sum())
n_mid_only = int((sl["has_mid"] & ~sl["has_trade"]).sum())
n_trade_only = int((sl["has_trade"] & ~sl["has_mid"]).sum())
gaps = sl.loc[sl["has_trade"] & sl["has_mid"], "abs_diff"].dropna()
rel = sl.loc[sl["has_trade"] & sl["has_mid"], "rel_diff"].dropna()

print("=" * 78)
print(f"OVERVIEW METRICS  ·  as-of {ASOF.date()}  ·  ticker {payload.get('ticker')}")
print("=" * 78)
print(f"  Spot (stock TRDPRC_1 on {ASOF.date()}): {spot}")
print(f"  Quotes on as-of date (all C+P):        {n}")
print(f"    both mid & trade:                    {n_both}")
print(f"    mid only (no print):                 {n_mid_only}")
print(f"    trade only (no mid):                 {n_trade_only}")
if n:
    print(f"    % mid with no trade:                 {100*n_mid_only/n:.0f}%")
if len(gaps):
    print(f"  Median |mid - trade|                    ${gaps.median():.3f}")
    print(f"  Median relative diff                    {100*rel.median():.2f}%")
    print(f"  |mid - trade| range                     "
          f"${gaps.min():.3f} .. ${gaps.max():.3f}")

# ---------------------------------------------------------------------------
# 2. Full slice — every contract on the as-of date, one row each
# ---------------------------------------------------------------------------
show_cols = ["ric", "expiry", "cp", "strike", "dte",
             "TRDPRC_1", "MID_PRICE", "abs_diff", "rel_diff", "moneyness"]
show_cols = [c for c in show_cols if c in sl.columns]

for cp_label, cp in (("CALLS", "C"), ("PUTS", "P")):
    part = sl[sl["cp"] == cp].sort_values(["expiry", "strike"])
    print("\n" + "=" * 78)
    print(f"FULL {cp_label} SLICE  ({len(part)} contracts)")
    print("=" * 78)
    if part.empty:
        print("  (no rows)")
        continue
    print(part[show_cols].to_string(index=False))

# ---------------------------------------------------------------------------
# 3. The two interesting cells for the teaching point
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print(f"MID_PRICE with NO trade  (n = {n_mid_only})")
print("=" * 78)
mo = sl[sl["has_mid"] & ~sl["has_trade"]].sort_values(["cp", "expiry", "strike"])
if mo.empty:
    print("  (none)")
else:
    print(mo[["ric", "expiry", "cp", "strike", "dte", "MID_PRICE", "moneyness"]]
          .to_string(index=False))

print("\n" + "=" * 78)
print(f"TRDPRC_1 with NO mid  (n = {n_trade_only})")
print("=" * 78)
to = sl[sl["has_trade"] & ~sl["has_mid"]].sort_values(["cp", "expiry", "strike"])
if to.empty:
    print("  (none)")
else:
    print(to[["ric", "expiry", "cp", "strike", "dte", "TRDPRC_1", "moneyness"]]
          .to_string(index=False))

# ---------------------------------------------------------------------------
# 4. The 10 largest |mid - trade| gaps — where the mark and print disagree most
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("TOP 10 |mid - trade| gaps (on rows with both)")
print("=" * 78)
both = sl[sl["has_mid"] & sl["has_trade"]].copy()
if not both.empty:
    top = both.sort_values("abs_diff", ascending=False).head(10)
    print(top[["ric", "expiry", "cp", "strike", "dte",
               "TRDPRC_1", "MID_PRICE", "abs_diff", "rel_diff"]]
          .to_string(index=False))
else:
    print("  (no paired rows)")

# ---------------------------------------------------------------------------
# 5. Raw stock row for the as-of date (spot-check the OHLC candle for that day)
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("RAW STOCK ROW (OHLC on the as-of date)")
print("=" * 78)
if ASOF in payload["stock"].index:
    print(payload["stock"].loc[[ASOF]].to_string())
else:
    print(f"  {ASOF.date()} not in stock frame.")

# ---------------------------------------------------------------------------
# 6. Sanity: pre-pivot tidy rows — the source of truth before the pivot
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("PRE-PIVOT tidy rows on this date  (source of truth before pivot_trade_mid)")
print("=" * 78)
tidy_slice = tidy[tidy["date"] == ASOF].sort_values(
    ["cp", "expiry", "strike", "field"]
)
print(f"  row counts by field: {tidy_slice['field'].value_counts().to_dict()}")
print(f"  distinct RICs:       {tidy_slice['ric'].nunique()}")
print(f"  distinct expiries:   {sorted({str(d.date()) for d in tidy_slice['expiry']})}")
