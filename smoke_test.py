from __future__ import annotations
 
from typing import Any
 
import pandas as pd
import lseg.data as ld
 
# ---------------------------------------------------------------------------
# contract
# ---------------------------------------------------------------------------
UNDERLYING_TICKER = "UUUU"
UNDERLYING_RICS = ["UUUU.A", "EFR.TO"]
EXPIRY = pd.Timestamp("2026-08-21")
STRIKE = 14.5
OPT_TYPE = "C"
QUERY_DAY = "2026-08-17"
 
RIC_CANDIDATES = [
    "UUUUH212601450.U^H26",
    "UUUUH212601450.U",
    "UUUUH21261450.U^H26",
    "UUUUH212601450.A^H26",
]
 
INTERVALS = ["tick", "tas", "taq", "1min", "5min", "10min", "30min", "1h", "1d"]
 
PRICE_FIELDS = [
    "BID", "ASK", "MID_PRICE",
    "TRDPRC_1", "OPEN_PRC", "HIGH_1", "LOW_1",
    "BIDSIZE", "ASKSIZE",
    "ACVOL_UNS", "NUM_MOVES", "VWAP",
    "SETTLE", "OPINT_1",
]
GREEK_RT_FIELDS = ["DELTA", "GAMMA", "THETA", "VEGA", "RHO", "IMP_VOLT"]
TR_FIELDS = [
    "TR.BIDPRICE", "TR.ASKPRICE", "TR.CLOSEPRICE",
    "TR.SETTLEMENTPRICE", "TR.IMPLIEDVOLATILITY", "TR.OPENINTEREST",
    "TR.DELTA", "TR.GAMMA", "TR.THETA", "TR.VEGA", "TR.RHO",
]
_DATEISH = {"date", "datetime", "timestamp", "time", "gmt", "tradedate"}
 
# ---------------------------------------------------------------------------
# raw buckets
# ---------------------------------------------------------------------------
errors: dict[str, str] = {}
ric_daily: dict[str, pd.DataFrame] = {}
interval_raw: dict[str, pd.DataFrame] = {}
price_fields_1min: dict[str, pd.DataFrame] = {}
price_fields_1d: dict[str, pd.DataFrame] = {}
greeks_1min: pd.DataFrame | None = None
greeks_1d: pd.DataFrame | None = None
tr_snapshot: pd.DataFrame | None = None
underlying: dict[str, pd.DataFrame] = {}
winner: str | None = None
session = None
 
ric_daily_df: pd.DataFrame | None = None
interval_raw_df: pd.DataFrame | None = None
price_fields_1min_df: pd.DataFrame | None = None
price_fields_1d_df: pd.DataFrame | None = None
greeks_1min_df: pd.DataFrame | None = None
greeks_1d_df: pd.DataFrame | None = None
tr_snapshot_df: pd.DataFrame | None = None
underlying_df: pd.DataFrame | None = None
 
 
def _err(key: str, exc: BaseException) -> None:
    msg = f"{type(exc).__name__}: {exc}"
    errors[key] = msg
    print(f"    FAIL {key}: {msg}")
 
 
def window_for(interval: str) -> tuple[str, str]:
    if interval in {"tick", "tas", "taq"}:
        return f"{QUERY_DAY}T13:00:00", f"{QUERY_DAY}T21:00:00"
    if interval in {"1min", "5min", "10min", "30min", "1h"}:
        return f"{QUERY_DAY}T00:00:00", f"{QUERY_DAY}T23:59:59"
    return "2026-08-10", "2026-08-22"
 
 
def summarize(df: pd.DataFrame | None) -> str:
    if df is None or df.empty:
        return "EMPTY"
    cols = list(df.columns)
    if isinstance(df.columns, pd.MultiIndex):
        cols = list(df.columns.get_level_values(-1).unique())
    return (
        f"rows={len(df)} cols={len(df.columns)} "
        f"nonempty={int(df.notna().to_numpy().sum())} names={cols}"
    )
 
 
def hist(ric: str, interval: str, fields=None) -> pd.DataFrame | None:
    start, end = window_for(interval)
    return ld.get_history(
        universe=ric,
        fields=fields,
        interval=interval,
        start=start,
        end=end,
    )
 
 
def to_dtindex(df: pd.DataFrame | None, dedupe: str = "last") -> pd.DataFrame | None:
    """Copy onto a unique DatetimeIndex when possible."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
 
    out = df.copy()
 
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [str(x) for x in out.columns.get_level_values(-1)]
 
    if not isinstance(out.index, pd.DatetimeIndex):
        date_col = None
        for c in out.columns:
            name = str(c).lower().replace(" ", "")
            if name in _DATEISH or name.endswith(".date") or "datetime" in name:
                date_col = c
                break
        if date_col is not None:
            out = out.set_index(date_col)
        parsed = pd.to_datetime(out.index, errors="coerce")
        if parsed.notna().any():
            out = out.loc[parsed.notna()].copy()
            out.index = parsed[parsed.notna()]
        else:
            return out
 
    out = out.sort_index()
    out.index.name = out.index.name or "datetime"
    if isinstance(out.index, pd.DatetimeIndex) and out.index.tz is not None:
        out.index = out.index.tz_convert("America/New_York")
 
    if isinstance(out.index, pd.DatetimeIndex) and not out.index.is_unique:
        if dedupe == "last":
            out = out.groupby(level=0).last()
        elif dedupe == "first":
            out = out.groupby(level=0).first()
    return out
 
 
def bucket_to_df(bucket, dedupe: str = "last") -> pd.DataFrame | None:
    """Dict[str, DataFrame] -> one DataFrame with unique datetime index."""
    if bucket is None:
        return None
    if isinstance(bucket, pd.DataFrame):
        return to_dtindex(bucket, dedupe=dedupe)
    if not isinstance(bucket, dict) or not bucket:
        return pd.DataFrame()
 
    pieces = []
    for k, v in bucket.items():
        if not isinstance(v, pd.DataFrame):
            continue
        framed = to_dtindex(v, dedupe=dedupe)
        if framed is None or framed.empty:
            continue
        framed = framed.copy()
        framed.columns = pd.MultiIndex.from_tuples(
            [(str(k), str(c)) for c in framed.columns]
        )
        pieces.append(framed)
 
    if not pieces:
        return pd.DataFrame()
 
    out = pieces[0]
    for extra in pieces[1:]:
        out = out.join(extra, how="outer")
    return out.sort_index()
 
 
# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
print("open_session()")
session = ld.open_session()
 
print("\n=== 1) RIC probe (daily, all fields) ===")
for ric in RIC_CANDIDATES:
    print(f"\n-- {ric}")
    try:
        df = hist(ric, "1d")
        ric_daily[ric] = df
        print("   ", summarize(df))
        if df is not None and not df.empty and winner is None:
            winner = ric
            print(df.tail(8))
    except Exception as e:
        _err(f"ric_daily:{ric}", e)
 
print(f"\nwinner = {winner!r}")
 
if winner:
    print("\n=== 2) Interval probe (fields=None) ===")
    for interval in INTERVALS:
        print(f"\n[{interval}] {window_for(interval)}")
        try:
            df = hist(winner, interval, fields=None)
            interval_raw[interval] = df
            print("   ", summarize(df))
            if df is not None and not df.empty:
                print(df.head(2))
        except Exception as e:
            _err(f"interval:{interval}", e)
 
    print("\n=== 3) Price fields one-by-one ===")
    for interval, bucket in (("1min", price_fields_1min), ("1d", price_fields_1d)):
        print(f"\n[{interval}]")
        for f in PRICE_FIELDS:
            try:
                df = hist(winner, interval, fields=[f])
                bucket[f] = df
                ok = df is not None and not df.empty and df.notna().any().any()
                print(f"    {f:12s} {'OK' if ok else '—'}")
            except Exception as e:
                _err(f"price:{interval}:{f}", e)
 
    print("\n=== 4) Greek RT fields ===")
    try:
        greeks_1min = hist(winner, "1min", fields=GREEK_RT_FIELDS)
        print("1min", summarize(greeks_1min))
    except Exception as e:
        _err("greeks_1min", e)
    try:
        greeks_1d = hist(winner, "1d", fields=GREEK_RT_FIELDS)
        print("1d  ", summarize(greeks_1d))
        if greeks_1d is not None and not greeks_1d.empty:
            print(greeks_1d.head())
    except Exception as e:
        _err("greeks_1d", e)
 
    print("\n=== 5) get_data TR.* ===")
    try:
        tr_snapshot = ld.get_data(
            universe=winner,
            fields=TR_FIELDS,
            parameters={"SDate": QUERY_DAY, "EDate": QUERY_DAY, "Frq": "D"},
        )
        print(tr_snapshot)
    except Exception as e:
        _err("tr_snapshot", e)
else:
    print("no winning option RIC; skipping 2–5")
 
print("\n=== 6) Underlying ===")
for u in UNDERLYING_RICS:
    print(f"\n-- {u}")
    try:
        df = ld.get_history(
            universe=u,
            fields=["TRDPRC_1", "BID", "ASK"],
            interval="1d",
            start="2026-08-14",
            end="2026-08-22",
        )
        underlying[u] = df
        print(summarize(df))
        print(df)
    except Exception as e:
        _err(f"underlying:{u}", e)
 
print("\n=== 7) *_df conversions ===")
ric_daily_df = bucket_to_df(ric_daily)
interval_raw_df = bucket_to_df(interval_raw)
price_fields_1min_df = bucket_to_df(price_fields_1min)
price_fields_1d_df = bucket_to_df(price_fields_1d)
greeks_1min_df = bucket_to_df(greeks_1min)
greeks_1d_df = bucket_to_df(greeks_1d)
tr_snapshot_df = bucket_to_df(tr_snapshot)
underlying_df = bucket_to_df(underlying)
 
for name, frame in [
    ("ric_daily_df", ric_daily_df),
    ("interval_raw_df", interval_raw_df),
    ("price_fields_1min_df", price_fields_1min_df),
    ("price_fields_1d_df", price_fields_1d_df),
    ("greeks_1min_df", greeks_1min_df),
    ("greeks_1d_df", greeks_1d_df),
    ("tr_snapshot_df", tr_snapshot_df),
    ("underlying_df", underlying_df),
]:
    if frame is None:
        print(f"{name}: None")
    else:
        tz = getattr(frame.index, "tz", None) if isinstance(frame.index, pd.DatetimeIndex) else None
        print(f"{name}: {summarize(frame)} index={type(frame.index).__name__} tz={tz}")