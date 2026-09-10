"""US equity call RIC construction (OPRA / .U), matching LSEG expired-option rules."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable

# Call month codes A–L; expired suffix uses the same letter.
CALL_MONTH = {
    1: "A",
    2: "B",
    3: "C",
    4: "D",
    5: "E",
    6: "F",
    7: "G",
    8: "H",
    9: "I",
    10: "J",
    11: "K",
    12: "L",
}


def option_root(equity_ric: str) -> str:
    token = (equity_ric or "").strip()
    if not token:
        return ""
    return token.split(".", 1)[0].upper()


def parse_bar_date(raw: Any) -> date | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")[:19]).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            continue
    return None


def week_endings(dates: Iterable[date]) -> list[date]:
    by_week: dict[tuple[int, int], date] = {}
    for d in sorted(dates):
        iso = d.isocalendar()
        by_week[(iso.year, iso.week)] = d
    return list(by_week.values())


def next_fridays(after: date, count: int) -> list[date]:
    d = after + timedelta(days=1)
    while d.weekday() != 4:
        d += timedelta(days=1)
    return [d + timedelta(weeks=i) for i in range(count)]


def strike_step(high: float) -> float:
    return 0.5 if high < 25 else 1.0


def round_step(value: float, step: float, mode: str) -> float:
    import math

    n = math.floor(value / step) if mode == "floor" else math.ceil(value / step)
    return round(n * step, 4)


def strike_grid(low: float, high: float, extra: float | None = None) -> tuple[list[float], float, float, float]:
    step = strike_step(high)
    if extra is None:
        extra = step * 2  # e.g. 16.50 high → 17.50 when step is 0.5
    lo = round_step(low, step, "floor")
    hi = round(round_step(high, step, "ceil") + extra, 4)
    strikes: list[float] = []
    x = lo
    # guard float drift
    while x <= hi + 1e-9:
        strikes.append(round(x, 4))
        x = round(x + step, 4)
    return strikes, lo, hi, step


def strike_token(strike: float) -> str:
    """14.5 → 01450 (strike × 100, 5 digits). Matches UUUUH212601450.U^H26."""
    return f"{int(round(strike * 100)):05d}"


def build_call_ric(
    root: str,
    expiry: date,
    strike: float,
    as_of: date | None = None,
    exchange: str = ".U",
) -> str:
    root = option_root(root)
    month = CALL_MONTH[expiry.month]
    yy = f"{expiry.year % 100:02d}"
    token = strike_token(strike)
    ric = f"{root}{month}{expiry.day}{yy}{token}{exchange}"
    today = as_of or date.today()
    if expiry < today:
        ric = f"{ric}^{month}{yy}"
    return ric


def plan_expiries(bar_dates: list[date], extra_weeks: int = 5) -> list[date]:
    hist = week_endings(bar_dates)
    if not bar_dates:
        return hist
    last = max(bar_dates)
    fwd = next_fridays(last, extra_weeks)
    seen: set[date] = set()
    out: list[date] = []
    for d in hist + fwd:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def verify_example() -> None:
    ric = build_call_ric("UUUU", date(2026, 8, 21), 14.5, as_of=date(2026, 9, 8))
    assert ric == "UUUUH212601450.U^H26", ric


if __name__ == "__main__":
    verify_example()
    print("ok", build_call_ric("UUUU", date(2026, 8, 21), 14.5, as_of=date(2026, 9, 8)))
