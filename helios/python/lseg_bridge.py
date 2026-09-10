#!/usr/bin/env python3
"""CLI bridge: JSON in on stdin, JSON out on stdout. Uses lseg-data desktop session."""

from __future__ import annotations

import json
import os
import socket
import sys
import time
import traceback
from datetime import date, datetime
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from option_rics import (  # noqa: E402
    build_call_ric,
    option_root,
    parse_bar_date,
    plan_expiries,
    strike_grid,
)

CACHE_DIR = os.path.join(os.getcwd(), "data", "options-cache")

WORKSPACE_PORTS = (9000, 9060)

WORKSPACE_HINTS = (
    "workspace",
    "desktop session",
    "desktop-session",
    "eikon",
    "connection refused",
    "failed to connect",
    "errno 111",
    "errno 61",
    "proxy",
    "handshake",
    "session is closed",
    "session is not opened",
    "127.0.0.1:9000",
    "localhost:9000",
    "port 9000",
    "unable to request",
    "app key",
)


class BridgeError(Exception):
    def __init__(self, code: str, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, default=str))
    sys.stdout.write("\n")
    sys.stdout.flush()


def fail(code: str, message: str, detail: str | None = None) -> None:
    emit({"ok": False, "code": code, "message": message, "detail": detail})


def port_open(host: str, port: int, timeout: float = 1.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def workspace_proxy_up() -> bool:
    return any(port_open("127.0.0.1", p) for p in WORKSPACE_PORTS)


def classify(exc: BaseException) -> tuple[str, str]:
    if isinstance(exc, BridgeError):
        return exc.code, exc.message
    text = f"{type(exc).__name__}: {exc}".lower()
    if isinstance(exc, ModuleNotFoundError) or "no module named 'lseg" in text:
        return (
            "library_missing",
            "Python package lseg-data is not installed. Install it, then retry.",
        )
    if any(h in text for h in WORKSPACE_HINTS):
        return (
            "workspace_unavailable",
            "LSEG Workspace is not running (or this process cannot reach its desktop proxy).",
        )
    return "upstream", str(exc) or type(exc).__name__


def require_workspace() -> None:
    if not workspace_proxy_up():
        raise BridgeError(
            "workspace_unavailable",
            "LSEG Workspace is not running. Start Workspace, stay signed in, then retry.",
        )


PERSIST = False
_LD = None


def open_session():
    import lseg.data as ld

    require_workspace()
    try:
        ld.open_session()
    except Exception as exc:  # noqa: BLE001 — map any session failure
        code, message = classify(exc)
        if code == "upstream":
            raise BridgeError(
                "workspace_unavailable",
                "Could not open an LSEG desktop session. Start Workspace and sign in.",
                detail=str(exc),
            ) from exc
        raise BridgeError(code, message, detail=str(exc)) from exc
    return ld


def close_session() -> None:
    global _LD
    try:
        import lseg.data as ld

        ld.close_session()
    except Exception:
        pass
    _LD = None


def get_ld():
    global _LD
    if PERSIST and _LD is not None:
        return _LD
    _LD = open_session()
    return _LD


def release_ld() -> None:
    if not PERSIST:
        close_session()


def health() -> dict[str, Any]:
    proxy = workspace_proxy_up()
    return {
        "ok": True,
        "op": "health",
        "workspace": proxy,
        "proxy": proxy,
    }


def search_equities(query: str) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        raise BridgeError("bad_request", "Enter a search string.")
    ld = get_ld()
    try:
        df = ld.discovery.search(
            query=q,
            view=ld.discovery.Views.EQUITY_QUOTES,
            filter="AssetState eq 'AC'",
            select="RIC,DocumentTitle,TickerSymbol,ExchangeCode,IssuerName,AssetType,Currency",
            top=25,
        )
        hits = []
        if df is not None and not df.empty:
            records = json.loads(df.to_json(orient="records", date_format="iso"))
            for row in records:
                ric = str(row.get("RIC") or "").strip()
                if not ric:
                    continue
                hits.append(
                    {
                        "ric": ric,
                        "title": str(row.get("DocumentTitle") or row.get("IssuerName") or ric),
                        "ticker": str(row.get("TickerSymbol") or ""),
                        "exchange": str(row.get("ExchangeCode") or ""),
                        "issuer": str(row.get("IssuerName") or ""),
                        "assetType": str(row.get("AssetType") or ""),
                        "currency": str(row.get("Currency") or ""),
                    }
                )
        return {"ok": True, "op": "search", "query": q, "hits": hits}
    finally:
        release_ld()


COLMAP = {
    "OPEN_PRC": "open",
    "OPEN": "open",
    "HIGH_1": "high",
    "HIGH": "high",
    "LOW_1": "low",
    "LOW": "low",
    "TRDPRC_1": "close",
    "CLOSE": "close",
    "CLOSE_PRC": "close",
    "ACVOL_UNS": "volume",
    "ACVOL_1": "volume",
    "VOLUME": "volume",
}

ALLOWED_INTERVALS = {"1min", "5min", "10min", "30min", "hourly", "daily"}


def _col_key(name: Any) -> str:
    if isinstance(name, tuple):
        name = name[0]
    return str(name).strip().upper()


def history(ric: str, start: str, end: str, interval: str) -> dict[str, Any]:
    ric = (ric or "").strip()
    interval = (interval or "").strip()
    if not ric:
        raise BridgeError("bad_request", "Select an equity before fetching.")
    if interval not in ALLOWED_INTERVALS:
        raise BridgeError("bad_request", f"Unsupported bar size: {interval}")
    ld = get_ld()
    try:
        from lseg.data.content._header_type import HeaderType

        fields = ["OPEN_PRC", "HIGH_1", "LOW_1", "TRDPRC_1", "ACVOL_UNS"]
        try:
            df = ld.get_history(
                universe=ric,
                fields=fields,
                interval=interval,
                start=start,
                end=end,
                header_type=HeaderType.NAME,
            )
        except Exception:
            df = ld.get_history(
                universe=ric,
                interval=interval,
                start=start,
                end=end,
                header_type=HeaderType.NAME,
            )
        if df is None or df.empty:
            return {
                "ok": True,
                "op": "history",
                "ric": ric,
                "interval": interval,
                "start": start,
                "end": end,
                "bars": [],
            }
        frame = df.copy().reset_index()
        time_col = frame.columns[0]
        bars: list[dict[str, Any]] = []
        for _, row in frame.iterrows():
            mapped: dict[str, Any] = {}
            for col, val in row.items():
                key = COLMAP.get(_col_key(col))
                if key:
                    mapped[key] = val
            t = row[time_col]
            try:
                o = float(mapped.get("open"))
                h = float(mapped.get("high"))
                low = float(mapped.get("low"))
                c = float(mapped.get("close"))
            except (TypeError, ValueError):
                continue
            vol_raw = mapped.get("volume")
            try:
                vol = float(vol_raw) if vol_raw is not None else 0.0
            except (TypeError, ValueError):
                vol = 0.0
            bars.append(
                {
                    "time": str(t),
                    "open": o,
                    "high": h,
                    "low": low,
                    "close": c,
                    "volume": vol,
                }
            )
        if len(bars) > 5000:
            bars = bars[-5000:]
        return {
            "ok": True,
            "op": "history",
            "ric": ric,
            "interval": interval,
            "start": start,
            "end": end,
            "bars": bars,
        }
    finally:
        release_ld()


def _num(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x:  # NaN
        return None
    return x


def _cache_path(root: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe = "".join(ch for ch in root.upper() if ch.isalnum() or ch in "._-")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def load_cache(root: str) -> dict[str, Any]:
    path = _cache_path(root)
    if not os.path.isfile(path):
        return {
            "root": option_root(root),
            "contracts": {},
            "misses": [],
        }
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = {"root": option_root(root), "contracts": {}, "misses": []}
    data.setdefault("contracts", {})
    data.setdefault("misses", [])
    return data


def save_cache(root: str, cache: dict[str, Any]) -> str:
    path = _cache_path(root)
    cache["updatedAt"] = datetime.utcnow().isoformat() + "Z"
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, default=str)
    os.replace(tmp, path)
    return path


def _save_cache_locked(root: str, incoming: dict[str, Any]) -> str:
    path = _cache_path(root)
    lock_path = path + ".lock"
    try:
        import fcntl
    except ImportError:
        return save_cache(root, incoming)
    with open(lock_path, "w", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        existing = load_cache(root)
        contracts = existing.get("contracts") or {}
        contracts.update(incoming.get("contracts") or {})
        miss_map = {m.get("key"): m for m in existing.get("misses") or [] if m.get("key")}
        for m in incoming.get("misses") or []:
            if m.get("key"):
                miss_map[m["key"]] = m
        for key in incoming.get("contracts") or {}:
            miss_map.pop(key, None)
        merged = {**existing, **incoming, "contracts": contracts, "misses": list(miss_map.values())}
        return save_cache(root, merged)


def contract_key(expiry: str, strike: float) -> str:
    return f"{expiry}|{strike:.2f}"


def options_plan(req: dict[str, Any]) -> dict[str, Any]:
    equity_ric = str(req.get("ric") or "")
    root = option_root(equity_ric) or option_root(str(req.get("root") or ""))
    if not root:
        raise BridgeError("bad_request", "Need an underlying RIC to plan option strikes.")
    bars = req.get("bars") or []
    highs: list[float] = []
    lows: list[float] = []
    dates: list[date] = []
    for bar in bars:
        d = parse_bar_date(bar.get("time"))
        h = _num(bar.get("high"))
        lo = _num(bar.get("low"))
        if d:
            dates.append(d)
        if h is not None:
            highs.append(h)
        if lo is not None:
            lows.append(lo)
    if not highs or not lows or not dates:
        raise BridgeError("bad_request", "Fetch underlying OHLC first so we can bound strikes and weeklies.")
    high = max(highs)
    low = min(lows)
    extra = _num(req.get("extra"))
    strikes, strike_min, strike_max, step = strike_grid(low, high, extra)
    extra_weeks = int(req.get("extraWeeks") or 5)
    expiries = plan_expiries(dates, extra_weeks=extra_weeks)
    as_of = date.today()
    candidates = []
    for exp in expiries:
        exp_s = exp.isoformat()
        expired = exp < as_of
        for k in strikes:
            ric = build_call_ric(root, exp, k, as_of=as_of)
            candidates.append(
                {
                    "ric": ric,
                    "strike": k,
                    "expiry": exp_s,
                    "expired": expired,
                    "key": contract_key(exp_s, k),
                }
            )
    return {
        "ok": True,
        "op": "options_plan",
        "underlying": equity_ric,
        "root": root,
        "high": high,
        "low": low,
        "strikeMin": strike_min,
        "strikeMax": strike_max,
        "strikeStep": step,
        "expiries": [d.isoformat() for d in expiries],
        "candidates": candidates,
        "candidateCount": len(candidates),
    }


OPT_FIELDS = ["TRDPRC_1", "OPEN_BID", "OPEN_ASK"]
OPT_FALLBACK = ["TRDPRC_1", "BID", "ASK"]
OPT_COLMAP = {
    "TRDPRC_1": "trade",
    "OPEN_BID": "bid",
    "OPEN_ASK": "ask",
    "BID": "bid",
    "ASK": "ask",
}
API_CHUNK = 25


def _history_option(ld, universe, start: str, end: str, interval: str, header_type, fields=None) -> Any:
    uni = universe if not isinstance(universe, list) or len(universe) > 1 else universe[0]
    try:
        return ld.get_history(
            universe=uni,
            fields=fields or OPT_FIELDS,
            interval=interval,
            start=start,
            end=end,
            header_type=header_type,
        )
    except Exception:
        if fields is None and (not isinstance(universe, list) or len(universe) == 1):
            return _history_option(ld, universe, start, end, interval, header_type, OPT_FALLBACK)
        raise


def _option_bars(df: Any) -> list[dict[str, Any]]:
    if df is None or getattr(df, "empty", True):
        return []
    frame = df.copy()
    if getattr(frame.index, "name", None) is not None or str(type(frame.index).__name__) != "RangeIndex":
        frame = frame.reset_index()
    time_col = frame.columns[0]
    bars: list[dict[str, Any]] = []
    records = frame.to_dict("records")
    for rec in records:
        mapped: dict[str, Any] = {}
        for col, val in rec.items():
            key = OPT_COLMAP.get(_col_key(col))
            if key:
                mapped[key] = _num(val)
        if mapped.get("trade") is None and mapped.get("bid") is None and mapped.get("ask") is None:
            continue
        bars.append(
            {
                "time": str(rec[time_col]),
                "trade": mapped.get("trade"),
                "bid": mapped.get("bid"),
                "ask": mapped.get("ask"),
            }
        )
    return bars


def _fields_only(df: Any) -> bool:
    cols = [_col_key(c) if getattr(df.columns, "nlevels", 1) == 1 else _col_key(c[-1] if isinstance(c, tuple) else c) for c in df.columns]
    useful = [c for c in cols if c not in {"DATE", "TIME", "TIMESTAMP", "INDEX"}]
    return bool(useful) and all(c in OPT_COLMAP for c in useful)


def _frame_for_ric(df: Any, ric: str) -> Any:
    if df is None:
        return None
    nlevels = getattr(df.columns, "nlevels", 1)
    if nlevels > 1:
        for level in range(nlevels):
            try:
                values = {str(v) for v in df.columns.get_level_values(level)}
            except Exception:
                continue
            if ric not in values:
                continue
            try:
                sub = df.xs(ric, axis=1, level=level, drop_level=True)
            except Exception:
                continue
            if hasattr(sub, "empty") and not getattr(sub, "columns", None):
                try:
                    sub = sub.to_frame(name=str(getattr(sub, "name", "TRDPRC_1")))
                except Exception:
                    pass
            return sub
        return None
    names = [str(c) for c in df.columns]
    if any(n == ric or n.startswith(ric) for n in names):
        return df
    return None


def _split_by_ric(df: Any, rics: list[str]) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True):
        return {r: None for r in rics}
    nlevels = getattr(df.columns, "nlevels", 1)
    if nlevels == 1 and _fields_only(df):
        if len(rics) == 1:
            return {rics[0]: df}
        return {r: None for r in rics}
    out: dict[str, Any] = {}
    for ric in rics:
        out[ric] = _frame_for_ric(df, ric)
    return out


def _fetch_chunk(ld, rics: list[str], start: str, end: str, interval: str, header_type) -> dict[str, list]:
    """One RIC per get_history. Batch universe lists abort the desktop session."""
    out: dict[str, list] = {}
    for i, ric in enumerate(rics):
        try:
            df = _history_option(ld, ric, start, end, interval, header_type)
            out[ric] = _option_bars(df)
        except Exception:
            out[ric] = []
        if i + 1 < len(rics):
            time.sleep(0.05)
    return out


def _fetch_rics(ld, rics: list[str], start: str, end: str, interval: str, header_type) -> dict[str, list]:
    result: dict[str, list] = {}
    for i in range(0, len(rics), API_CHUNK):
        chunk = rics[i : i + API_CHUNK]
        result.update(_fetch_chunk(ld, chunk, start, end, interval, header_type))
        if i + API_CHUNK < len(rics):
            time.sleep(0.12)
    return result


def options_fetch(req: dict[str, Any]) -> dict[str, Any]:
    equity_ric = str(req.get("ric") or "")
    root = option_root(str(req.get("root") or equity_ric))
    if not root:
        raise BridgeError("bad_request", "Missing option root.")
    candidates = req.get("candidates") or []
    if not isinstance(candidates, list) or not candidates:
        raise BridgeError("bad_request", "No option RICs to fetch.")
    start = str(req.get("start") or "")
    end = str(req.get("end") or "")
    interval = str(req.get("interval") or "daily")
    if interval not in ALLOWED_INTERVALS:
        interval = "daily"

    cache = load_cache(root)
    cache["underlying"] = equity_ric or cache.get("underlying")
    cache["root"] = root
    for field in ("high", "low", "strikeMin", "strikeMax", "strikeStep", "expiries"):
        if req.get(field) is not None:
            cache[field] = req[field]

    pending: list[dict[str, Any]] = []
    added: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []
    for cand in candidates:
        ric = str(cand.get("ric") or "")
        strike = _num(cand.get("strike"))
        expiry = str(cand.get("expiry") or "")
        if not ric or strike is None or not expiry:
            continue
        key = contract_key(expiry, strike)
        existing = cache.get("contracts", {}).get(key)
        if existing and existing.get("bars"):
            added.append(existing)
            continue
        pending.append({**cand, "ric": ric, "strike": strike, "expiry": expiry, "key": key})

    ld = get_ld()
    try:
        from lseg.data.content._header_type import HeaderType

        bars_by_ric = _fetch_rics(
            ld,
            [c["ric"] for c in pending],
            start,
            end,
            interval,
            HeaderType.NAME,
        )
    finally:
        release_ld()

    for cand in pending:
        ric = cand["ric"]
        bars = bars_by_ric.get(ric) or []
        key = cand["key"]
        if bars:
            rec = {
                "ric": ric,
                "strike": cand["strike"],
                "expiry": cand["expiry"],
                "expired": bool(cand.get("expired")),
                "key": key,
                "barCount": len(bars),
                "bars": bars,
            }
            cache.setdefault("contracts", {})[key] = rec
            added.append(rec)
        else:
            miss = {
                "ric": ric,
                "strike": cand["strike"],
                "expiry": cand["expiry"],
                "key": key,
                "reason": "no rows",
            }
            misses.append(miss)
            cache["misses"] = [m for m in cache.get("misses", []) if m.get("key") != key] + [miss]

    try:
        path = _save_cache_locked(root, cache)
    except OSError:
        path = ""
    return {
        "ok": True,
        "op": "options_fetch",
        "root": root,
        "underlying": equity_ric,
        "path": path,
        "added": added,
        "misses": misses,
        "addedCount": len(added),
        "missCount": len(misses),
        "contractCount": len(cache.get("contracts", {})),
    }


def options_cache(req: dict[str, Any]) -> dict[str, Any]:
    root = option_root(str(req.get("root") or req.get("ric") or ""))
    if not root:
        raise BridgeError("bad_request", "Missing option root.")
    cache = load_cache(root)
    return {"ok": True, "op": "options_cache", "root": root, "cache": cache}


def handle(req: dict[str, Any]) -> dict[str, Any]:
    op = req.get("op")
    if op == "health":
        return health()
    if op == "search":
        return search_equities(str(req.get("query") or ""))
    if op == "history":
        return history(
            str(req.get("ric") or ""),
            str(req.get("start") or ""),
            str(req.get("end") or ""),
            str(req.get("interval") or ""),
        )
    if op == "options_plan":
        return options_plan(req)
    if op == "options_fetch":
        return options_fetch(req)
    if op == "options_cache":
        return options_cache(req)
    raise BridgeError("bad_request", f"Unknown op: {op}")


def loop() -> int:
    global PERSIST
    PERSIST = True
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if not isinstance(req, dict):
                raise BridgeError("bad_request", "Request must be a JSON object.")
            emit(handle(req))
        except Exception as exc:  # noqa: BLE001
            code, message = classify(exc)
            detail = traceback.format_exc() if code == "upstream" else str(exc)
            fail(code, message, detail)
            if code in {"workspace_unavailable", "upstream"}:
                close_session()
    close_session()
    return 0


def main() -> int:
    if "--loop" in sys.argv:
        return loop()
    raw = sys.stdin.read()
    try:
        req = json.loads(raw or "{}")
        if not isinstance(req, dict):
            raise BridgeError("bad_request", "Request must be a JSON object.")
        emit(handle(req))
        return 0
    except Exception as exc:  # noqa: BLE001
        code, message = classify(exc)
        detail = traceback.format_exc() if code == "upstream" else str(exc)
        fail(code, message, detail)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
