"""Simple VRP webpage. Serves HTML and pulls real IBKR data on /api/refresh."""
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import math
import traceback

app = FastAPI()

# In-memory log of IBKR interactions for the session
LOG = []

def log(direction, symbol, detail):
    LOG.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "direction": direction,  # SENT or RECV or ERR
        "ric": symbol,
        "detail": detail,
    })
    if len(LOG) > 50:
        LOG.pop(0)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Helios — Variance Risk Premium</title>
<style>
  :root {
    --bg: #070b10;
    --surface: #101820;
    --fg: #e8f6f3;
    --muted: #8aa8a4;
    --accent: #2ee6d0;
    --line: #24313c;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--fg);
    font-family: 'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
  }
  .wrap {
    max-width: 1100px;
    margin: 0 auto;
    padding: 1.5rem;
  }
  .kicker {
    font-size: 0.7rem;
    letter-spacing: 0.28em;
    color: var(--accent);
    font-family: 'IBM Plex Mono', monospace;
  }
  h1 { margin: 0.25rem 0 0.5rem; font-size: 2rem; }
  .sub { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }
  .cards { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1.5rem; }
  .card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1rem;
    min-width: 140px;
    flex: 1;
  }
  .card .label { font-size: 0.75rem; color: var(--muted); font-family: 'IBM Plex Mono', monospace; }
  .card .value { font-size: 1.75rem; font-weight: 600; font-family: 'IBM Plex Mono', monospace; margin: 0.25rem 0; }
  .card .hint { font-size: 0.7rem; color: var(--muted); line-height: 1.3; margin-top: 0.25rem; }
  button {
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 0.5rem;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
  }
  button:disabled { opacity: 0.6; cursor: wait; }
  .status { margin-top: 1rem; font-size: 0.8rem; color: var(--muted); min-height: 1.2em; }
  .log-section { margin-top: 2rem; }
  .log-section h2 { font-size: 1.1rem; margin-bottom: 0.5rem; }
  .log {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 0.75rem;
    max-height: 320px;
    overflow-y: auto;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    line-height: 1.4;
  }
  .log .entry { margin-bottom: 0.4rem; }
  .log .sent { color: var(--accent); }
  .log .recv { color: #e8f6f3; }
  .log .err { color: #ff6b8a; }
</style>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
<div class="wrap">
  <div class="kicker">HELIOS</div>
  <h1>Variance Risk Premium</h1>
  <div class="sub">Implied vs realized. Values appear only from IBKR TWS (paper).</div>
  <div class="cards">
    <div class="card">
      <div class="label">VIX</div>
      <div class="value" id="vix">—</div>
      <div class="hint" id="hint-vix">30d implied (IBKR)</div>
    </div>
    <div class="card">
      <div class="label">Realized</div>
      <div class="value" id="realized">—</div>
      <div class="hint" id="hint-realized">Close-to-close (IBKR)</div>
    </div>
    <div class="card">
      <div class="label">VRP</div>
      <div class="value" id="vrp">—</div>
      <div class="hint" id="hint-vrp">Implied − realized</div>
    </div>
    <div class="card">
      <div class="label">Updated</div>
      <div class="value" id="updated">—</div>
      <div class="hint" id="hint-updated">Session</div>
    </div>
  </div>
  <button id="btn" onclick="refresh()">Refresh (IBKR)</button>
  <div class="status" id="status">Awaiting IBKR TWS (paper, port 7497).</div>

  <div class="log-section">
    <h2>IBKR Log</h2>
    <div class="log" id="log"><div class="entry">No requests yet.</div></div>
  </div>
</div>
<script>
// EDIT THESE to change the text under each card
const DESCRIPTIONS = {
  vix: "30-day implied volatility of the S&P 500. What the market is pricing for near-term moves.",
  realized: "Trailing close-to-close volatility of the S&P 500 over the last ~30 sessions. What actually happened.",
  vrp: "Implied minus realized. Positive means options are expensive relative to recent moves; negative means they are cheap.",
  updated: "Time of the last successful IBKR pull."
};

function applyDescriptions() {
  document.getElementById("hint-vix").textContent = DESCRIPTIONS.vix;
  document.getElementById("hint-realized").textContent = DESCRIPTIONS.realized;
  document.getElementById("hint-vrp").textContent = DESCRIPTIONS.vrp;
  document.getElementById("hint-updated").textContent = DESCRIPTIONS.updated;
}
applyDescriptions();

function renderLog(entries) {
  const el = document.getElementById('log');
  if (!entries || !entries.length) {
    el.innerHTML = '<div class="entry">No requests yet.</div>';
    return;
  }
  el.innerHTML = entries.map(e => {
    const cls = e.direction === 'SENT' ? 'sent' : (e.direction === 'ERR' ? 'err' : 'recv');
    return `<div class="entry ${cls}">[${e.time}] ${e.direction} ${e.ric || ''} — ${e.detail}</div>`;
  }).join('');
  el.scrollTop = el.scrollHeight;
}

async function refresh() {
  const btn = document.getElementById('btn');
  const status = document.getElementById('status');
  btn.disabled = true;
  status.textContent = 'Connecting to TWS…';
  try {
    const r = await fetch('/api/refresh', { method: 'POST' });
    const data = await r.json();
    document.getElementById('vix').textContent = data.vix || '—';
    document.getElementById('realized').textContent = data.realized || '—';
    document.getElementById('vrp').textContent = data.vrp || '—';
    document.getElementById('updated').textContent = data.updated || '—';
    status.textContent = data.status || 'Done.';
    renderLog(data.log || []);
  } catch (e) {
    status.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML

@app.post("/api/refresh")
def refresh():
    """Pull VIX and SPX realized vol via IBKR TWS paper. No fallbacks."""
    result = {"vix": "—", "realized": "—", "vrp": "—", "updated": "—", "status": "", "log": []}
    ib = None
    try:
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        from ib_insync import IB, Index

        HOST = "127.0.0.1"
        PORT = 7497  # TWS paper
        CLIENT_ID = 1

        ib = IB()
        log("SENT", "tws", f"connect {HOST}:{PORT} clientId={CLIENT_ID}")
        ib.connect(HOST, PORT, clientId=CLIENT_ID, timeout=10)
        log("RECV", "tws", f"connected={ib.isConnected()}")

        # VIX index
        vix_contract = Index("VIX", "CBOE", "USD")
        log("SENT", "VIX", "qualifyContracts Index VIX CBOE")
        qualified = ib.qualifyContracts(vix_contract)
        if not qualified:
            log("ERR", "VIX", "qualifyContracts returned empty")
        else:
            log("RECV", "VIX", f"qualified {qualified[0].symbol} conId={qualified[0].conId}")
            bars = ib.reqHistoricalData(
                vix_contract,
                endDateTime="",
                durationStr="1 D",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
            log("RECV", "VIX", f"hist bars={len(bars) if bars else 0}")
            if bars:
                vix_val = float(bars[-1].close)
                result["vix"] = f"{vix_val:.2f}"
                log("RECV", "VIX", f"close={vix_val}")

        # SPX realized
        spx_contract = Index("SPX", "CBOE", "USD")
        log("SENT", "SPX", "qualifyContracts Index SPX CBOE")
        qualified_spx = ib.qualifyContracts(spx_contract)
        if not qualified_spx:
            log("ERR", "SPX", "qualifyContracts returned empty")
        else:
            log("RECV", "SPX", f"qualified {qualified_spx[0].symbol} conId={qualified_spx[0].conId}")
            bars_spx = ib.reqHistoricalData(
                spx_contract,
                endDateTime="",
                durationStr="45 D",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
            log("RECV", "SPX", f"hist bars={len(bars_spx) if bars_spx else 0}")
            if bars_spx and len(bars_spx) >= 21:
                closes = [b.close for b in bars_spx]
                rets = []
                for i in range(1, len(closes)):
                    if closes[i-1] and closes[i]:
                        rets.append(closes[i] / closes[i-1] - 1)
                if len(rets) >= 20:
                    mean = sum(rets) / len(rets)
                    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
                    realized = math.sqrt(var) * math.sqrt(252) * 100
                    result["realized"] = f"{realized:.2f}"
                    log("RECV", "SPX", f"realized={realized:.2f} n={len(rets)}")

        if result["vix"] != "—" and result["realized"] != "—":
            result["vrp"] = f"{float(result['vix']) - float(result['realized']):+.2f}"

        result["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if result["vix"] == "—" and result["realized"] == "—":
            result["status"] = "IBKR returned no usable data. See log."
        else:
            result["status"] = "IBKR pull complete."
    except Exception as e:
        result["status"] = f"IBKR error: {type(e).__name__}: {e}"
        result["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        log("ERR", "refresh", f"{type(e).__name__}: {e}\\n{traceback.format_exc()}")
    finally:
        if ib is not None:
            try:
                ib.disconnect()
                log("RECV", "tws", "disconnected")
            except Exception:
                pass

    result["log"] = list(LOG)
    return JSONResponse(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
