"""Helios site: FastAPI backend for VRP, term structure, and gamma proxy.

Run from the helios_site directory:
    uvicorn app:app --reload --port 8000
"""

from datetime import datetime, timedelta
from typing import Any
import math

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Helios")

# ---------------------------------------------------------------------------
# LSEG helpers
# ---------------------------------------------------------------------------

def _open_lseg():
    import lseg.data as ld
    try:
        cfg = ld.get_config()
        cfg.set_param("http.request-timeout", 120)
    except Exception:
        pass
    ld.open_session()
    return ld


def _vix_and_realized(ld) -> dict[str, Any]:
    out: dict[str, Any] = {"vix": None, "realized": None, "vrp": None, "notes": []}

    for ric in (".VIX", "/.VIX"):
        try:
            df = ld.get_data(universe=ric, fields=["TRDPRC_1"])
            if df is not None and not df.empty and "TRDPRC_1" in df.columns:
                out["vix"] = float(df["TRDPRC_1"].iloc[0])
                out["notes"].append(f"VIX from {ric}")
                break
        except Exception as e:
            out["notes"].append(f"VIX {ric}: {type(e).__name__}")

    hist = None
    for ric in (".SPX", "/.SPX"):
        try:
            hist = ld.get_history(universe=ric, fields=["TRDPRC_1"], interval="1D", count=45)
            if hist is not None and not hist.empty:
                out["notes"].append(f"SPX history from {ric}")
                break
        except Exception as e:
            out["notes"].append(f"SPX {ric}: {type(e).__name__}")

    if hist is not None and not hist.empty and "TRDPRC_1" in hist.columns:
        rets = hist["TRDPRC_1"].pct_change().dropna()
        if len(rets) >= 20:
            out["realized"] = float(rets.std() * math.sqrt(252) * 100)

    if out["vix"] is not None and out["realized"] is not None:
        out["vrp"] = out["vix"] - out["realized"]

    return out


def _surfaces(ld) -> dict[str, Any]:
    """ATM term structure and 25Δ RR for .SPX and QQQ.O via IPA ETI surfaces."""
    from lseg.data.delivery import endpoint_request
    import pandas as pd

    SURFACES_URL = "https://api.refinitiv.com/data/quantitative-analytics-curves-and-surfaces/v1/surfaces"
    instruments = [(".SPX", "spx"), ("QQQ.O", "qqq")]
    tenors = ["1W", "2W", "1M", "2M", "3M", "6M"]

    def request_axis(y_axis: str, tag_suffix: str = ""):
        universe = []
        for ric, tag in instruments:
            universe.append({
                "surfaceTag": f"{tag}{tag_suffix}",
                "underlyingType": "Eti",
                "underlyingDefinition": {"instrumentCode": f"{ric}@RIC"},
                "surfaceParameters": {
                    "inputVolatilityType": "Quoted",
                    "timeStamp": "Default",
                    "priceSide": "Mid",
                    "volatilityModel": "SSVI",
                    "xAxis": "Tenor",
                    "yAxis": y_axis,
                },
                "surfaceLayout": {"format": "Matrix"},
            })
        req = endpoint_request.Definition(
            url=SURFACES_URL,
            method=endpoint_request.RequestMethod.POST,
            body_parameters={"universe": universe, "outputs": ["Data"]},
        )
        resp = req.get_data()
        if resp is None or not hasattr(resp, "data") or resp.data.raw is None:
            return {}
        raw = resp.data.raw.get("data", [])
        return {item.get("surfaceTag"): item for item in raw}

    def parse_atm(surfaces: dict) -> dict[str, list]:
        result = {}
        for ric, tag in instruments:
            item = surfaces.get(tag)
            if not item or "surface" not in item:
                result[tag] = ["—"] * len(tenors)
                continue
            try:
                sdf = pd.DataFrame(item["surface"])
                moneyness = [str(x) for x in sdf.iloc[0, 1:].tolist()]
                tenors_returned = [str(x) for x in sdf.iloc[1:, 0].tolist()]
                cols = []
                for m in moneyness:
                    try:
                        cols.append(abs(float(m) - 100.0))
                    except Exception:
                        cols.append(999)
                atm_idx = cols.index(min(cols)) if cols else 0
                vals = []
                for t in tenors:
                    if t in tenors_returned:
                        row = tenors_returned.index(t)
                        val = sdf.iloc[row + 1, atm_idx + 1]
                        vals.append(f"{float(val):.2f}" if val is not None else "—")
                    else:
                        vals.append("—")
                result[tag] = vals
            except Exception:
                result[tag] = ["—"] * len(tenors)
        return result

    def parse_rr(surfaces: dict) -> dict[str, list]:
        result = {}
        for ric, tag in instruments:
            item = surfaces.get(f"{tag}_rr")
            if not item or "surface" not in item:
                result[tag] = ["—"] * len(tenors)
                continue
            try:
                sdf = pd.DataFrame(item["surface"])
                deltas = [str(x) for x in sdf.iloc[0, 1:].tolist()]
                tenors_returned = [str(x) for x in sdf.iloc[1:, 0].tolist()]

                def nearest(target):
                    best, best_d = None, 999
                    for i, d in enumerate(deltas):
                        try:
                            dist = abs(float(d) - target)
                            if dist < best_d:
                                best_d, best = dist, i
                        except Exception:
                            pass
                    return best

                i25 = nearest(25)
                i75 = nearest(75)
                if i25 is None or i75 is None:
                    result[tag] = ["—"] * len(tenors)
                    continue
                vals = []
                for t in tenors:
                    if t in tenors_returned:
                        row = tenors_returned.index(t)
                        v25 = sdf.iloc[row + 1, i25 + 1]
                        v75 = sdf.iloc[row + 1, i75 + 1]
                        try:
                            vals.append(f"{float(v25) - float(v75):+.2f}")
                        except Exception:
                            vals.append("—")
                    else:
                        vals.append("—")
                result[tag] = vals
            except Exception:
                result[tag] = ["—"] * len(tenors)
        return result

    atm_surfaces = request_axis("Moneyness")
    rr_surfaces = request_axis("Delta", "_rr")

    atm = parse_atm(atm_surfaces)
    rr = parse_rr(rr_surfaces)

    premium = []
    for s, q in zip(atm.get("spx", ["—"] * 6), atm.get("qqq", ["—"] * 6)):
        try:
            premium.append(f"{float(q) - float(s):+.2f}")
        except Exception:
            premium.append("—")

    return {
        "tenors": tenors,
        "spx_atm": atm.get("spx", ["—"] * 6),
        "qqq_atm": atm.get("qqq", ["—"] * 6),
        "premium": premium,
        "spx_rr25": rr.get("spx", ["—"] * 6),
        "qqq_rr25": rr.get("qqq", ["—"] * 6),
    }


def _gamma(ld) -> dict[str, Any]:
    """SPX option chain OI clusters and simple gamma proxy."""
    from lseg.data.discovery import Chain
    import pandas as pd

    out: dict[str, Any] = {
        "spot": None,
        "gamma_flip": None,
        "put_call_oi": None,
        "put_call_vol": None,
        "top_oi": [],
        "gamma_chart": [],
        "notes": [],
    }

    spot_df = ld.get_data(universe=".SPX", fields=["TRDPRC_1"])
    if spot_df is None or spot_df.empty or "TRDPRC_1" not in spot_df.columns:
        out["notes"].append("Could not retrieve .SPX spot")
        return out
    spot = float(spot_df["TRDPRC_1"].iloc[0])
    out["spot"] = spot

    rics = []
    chain_used = None
    for name in ("0#SPXW*.U", "0#SPX*.U", "0#/SPX*.U", "0#/SPXW*.U"):
        try:
            chain = Chain(name=name)
            rics = list(chain.constituents)[:600]
            if rics:
                chain_used = name
                out["notes"].append(f"Chain {name}: {len(rics)} RICs")
                break
        except Exception as e:
            out["notes"].append(f"Chain {name}: {type(e).__name__}")

    if not rics:
        out["notes"].append("No option chain constituents")
        return out

    fields = ["STRIKE_PRC", "EXPIR_DATE", "PUT_CALL", "OPINT_1", "ACVOL_1", "TR.IMPLIEDVOLATILITY"]
    df = ld.get_data(universe=rics, fields=fields)
    if df is None or df.empty:
        out["notes"].append("get_data returned empty")
        return out

    df = df.dropna(subset=["STRIKE_PRC"])
    df["STRIKE_PRC"] = pd.to_numeric(df["STRIKE_PRC"], errors="coerce")
    df = df.dropna(subset=["STRIKE_PRC"])
    lo, hi = spot * 0.88, spot * 1.12
    df = df[(df["STRIKE_PRC"] >= lo) & (df["STRIKE_PRC"] <= hi)]

    if "EXPIR_DATE" in df.columns:
        df["EXPIR_DATE"] = pd.to_datetime(df["EXPIR_DATE"], errors="coerce")
        cutoff = datetime.now() + timedelta(days=45)
        df = df[df["EXPIR_DATE"] <= cutoff]

    if df.empty:
        out["notes"].append("No near-term near-spot options after filter")
        return out

    df["OPINT_1"] = pd.to_numeric(df["OPINT_1"], errors="coerce").fillna(0)
    df["ACVOL_1"] = pd.to_numeric(df["ACVOL_1"], errors="coerce").fillna(0)
    if "TR.IMPLIEDVOLATILITY" in df.columns:
        df["IV"] = pd.to_numeric(df["TR.IMPLIEDVOLATILITY"], errors="coerce").fillna(0.20)
    else:
        df["IV"] = 0.20

    def bs_gamma(S, K, iv, T=21 / 365, r=0.04):
        if iv <= 0 or T <= 0 or S <= 0:
            return 0.0
        try:
            d1 = (math.log(S / K) + (r + 0.5 * iv * iv) * T) / (iv * math.sqrt(T))
            pdf = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
            return pdf / (S * iv * math.sqrt(T))
        except Exception:
            return 0.0

    rows = []
    for _, row in df.iterrows():
        K = float(row["STRIKE_PRC"])
        oi = float(row["OPINT_1"])
        vol = float(row["ACVOL_1"])
        iv = float(row["IV"]) if row["IV"] > 0 else 0.20
        g = bs_gamma(spot, K, iv)
        cp = str(row.get("PUT_CALL", ""))
        sign = 1.0 if cp.upper().startswith("C") else -1.0
        rows.append({
            "strike": K,
            "oi": oi,
            "vol": vol,
            "call_put": cp,
            "expiry": str(row.get("EXPIR_DATE", ""))[:10],
            "gamma": g * oi * 100 * sign,
            "dist": (K - spot) / spot * 100,
        })

    if not rows:
        out["notes"].append("No usable rows")
        return out

    top = sorted(rows, key=lambda r: r["oi"], reverse=True)[:12]
    out["top_oi"] = [
        {
            "Strike": f"{r['strike']:.0f}",
            "Dist %": f"{r['dist']:+.1f}",
            "OI": f"{r['oi']:,.0f}",
            "Vol": f"{r['vol']:,.0f}",
            "C/P": r["call_put"],
            "Expiry": r["expiry"],
        }
        for r in top
    ]

    by_strike: dict[float, float] = {}
    for r in rows:
        by_strike.setdefault(r["strike"], 0.0)
        by_strike[r["strike"]] += r["gamma"]
    gamma_list = sorted(
        [{"strike": k, "gamma": v} for k, v in by_strike.items()],
        key=lambda x: x["strike"],
    )
    out["gamma_chart"] = gamma_list

    cum = 0.0
    flip = None
    for i, g in enumerate(gamma_list):
        prev = cum
        cum += g["gamma"]
        if prev * cum <= 0 and abs(prev) + abs(cum) > 0:
            if abs(g["gamma"]) > 0 and i > 0:
                prev_strike = gamma_list[i - 1]["strike"]
                frac = abs(prev) / (abs(prev) + abs(g["gamma"]))
                flip = prev_strike + (g["strike"] - prev_strike) * frac
            else:
                flip = g["strike"]
            break
    out["gamma_flip"] = flip

    put_oi = sum(r["oi"] for r in rows if str(r["call_put"]).upper().startswith("P"))
    call_oi = sum(r["oi"] for r in rows if str(r["call_put"]).upper().startswith("C"))
    put_vol = sum(r["vol"] for r in rows if str(r["call_put"]).upper().startswith("P"))
    call_vol = sum(r["vol"] for r in rows if str(r["call_put"]).upper().startswith("C"))
    out["put_call_oi"] = (put_oi / call_oi) if call_oi else None
    out["put_call_vol"] = (put_vol / call_vol) if call_vol else None
    out["notes"].append(f"Loaded {len(rows)} contracts from {chain_used}")

    return out


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/api/refresh")
def refresh():
    """VRP + term structure. Surfaces failure does not block VRP."""
    try:
        ld = _open_lseg()
    except Exception as e:
        return {"ok": False, "status": f"Session error: {type(e).__name__}: {e}"}

    result: dict[str, Any] = {"ok": True, "status": "OK", "updated": datetime.now().strftime("%Y-%m-%d %H:%M")}

    try:
        result["vrp"] = _vix_and_realized(ld)
    except Exception as e:
        result["vrp"] = {"error": f"{type(e).__name__}: {e}"}
        result["status"] = f"VRP error: {e}"

    try:
        result["surfaces"] = _surfaces(ld)
    except Exception as e:
        result["surfaces"] = {"error": f"{type(e).__name__}: {e}"}
        result["status"] = f"Surfaces: {type(e).__name__}: {e}. VRP still returned."

    return result


@app.post("/api/refresh-gamma")
def refresh_gamma():
    try:
        ld = _open_lseg()
    except Exception as e:
        return {"ok": False, "status": f"Session error: {type(e).__name__}: {e}"}

    try:
        data = _gamma(ld)
        return {"ok": True, "status": "OK", "updated": datetime.now().strftime("%Y-%m-%d %H:%M"), "gamma": data}
    except Exception as e:
        return {"ok": False, "status": f"LSEG error: {type(e).__name__}: {e}"}


app.mount("/static", StaticFiles(directory="static"), name="static")
