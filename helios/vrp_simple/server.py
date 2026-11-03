"""Simple VRP webpage. Serves HTML and pulls real LSEG data on /api/refresh."""
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import math
import traceback

app = FastAPI()

# In-memory log of LSEG interactions for the session
LOG = []

def log(direction, ric, detail):
    LOG.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "direction": direction,  # SENT or RECV
        "ric": ric,
        "detail": detail,
    })
    # keep last 50
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
  .card .hint { font-size: 0.75rem; color: var(--muted); }
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
  <div class="sub">Implied vs realized. Values appear only from LSEG.</div>
  <div class="cards">
    <div class="card"><div class="label">VIX</div><div class="value" id="vix">—</div><div class="hint">30d implied (LSEG)</div></div>
    <div class="card"><div class="label">Realized</div><div class="value" id="realized">—</div><div class="hint">Close-to-close (LSEG)</div></div>
    <div class="card"><div class="label">VRP</div><div class="value" id="vrp">—</div><div class="hint">Implied − realized</div></div>
    <div class="card"><div class="label">Updated</div><div class="value" id="updated">—</div><div class="hint">Session</div></div>
  </div>
  <button id="btn" onclick="refresh()">Refresh (LSEG)</button>
  <div class="status" id="status">Awaiting LSEG session.</div>

  <div class="log-section">
    <h2>LSEG Log</h2>
    <div class="log" id="log"><div class="entry">No requests yet.</div></div>
  </div>
</div>
<script>
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
  status.textContent = 'Opening LSEG session…';
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
    """Pull VIX and SPX realized vol via lseg-data. No fallbacks."""
    result = {"vix": "—", "realized": "—", "vrp": "—", "updated": "—", "status": "", "log": []}
    try:
        import lseg.data as ld
        try:
            cfg = ld.get_config()
            cfg.set_param("http.request-timeout", 60)
        except Exception:
            pass

        log("SENT", "session", "ld.open_session()")
        sess = ld.open_session()
        log("RECV", "session", f"type={type(sess).__name__}")

        # VIX
        vix_val = None
        for ric in (".VIX", "/.VIX"):
            log("SENT", ric, "get_data fields=['TRDPRC_1']")
            try:
                df = ld.get_data(universe=ric, fields=["TRDPRC_1"])
                cols = list(df.columns) if df is not None else None
                empty = df.empty if df is not None else None
                rows = len(df) if df is not None else 0
                log("RECV", ric, f"get_data cols={cols} empty={empty} rows={rows}")
                if df is not None and not df.empty:
                    for col in ("TRDPRC_1", "TRD_PRC_1", "CF_LAST", "BID", "ASK"):
                        if col in df.columns:
                            val = df[col].iloc[0]
                            if val is not None and str(val) not in ("", "nan", "None"):
                                vix_val = float(val)
                                result["vix"] = f"{vix_val:.2f}"
                                log("RECV", ric, f"used {col}={vix_val}")
                                break
                    if vix_val is not None:
                        break
            except Exception as e:
                log("ERR", ric, f"get_data {type(e).__name__}: {e}")

        # Realized from SPX
        realized_val = None
        for ric in (".SPX", "/.SPX"):
            log("SENT", ric, "get_history fields=['TRDPRC_1'] interval=1D count=45")
            try:
                hist = ld.get_history(universe=ric, fields=["TRDPRC_1"], interval="1D", count=45)
                cols = list(hist.columns) if hist is not None else None
                empty = hist.empty if hist is not None else None
                rows = len(hist) if hist is not None else 0
                log("RECV", ric, f"get_history cols={cols} empty={empty} rows={rows}")
                if hist is not None and not hist.empty:
                    price_col = None
                    for col in ("TRDPRC_1", "TRD_PRC_1", "CLOSE", "CF_CLOSE"):
                        if col in hist.columns:
                            price_col = col
                            break
                    if price_col:
                        rets = hist[price_col].pct_change().dropna()
                        log("RECV", ric, f"rets len={len(rets)} col={price_col}")
                        if len(rets) >= 20:
                            realized_val = float(rets.std() * math.sqrt(252) * 100)
                            result["realized"] = f"{realized_val:.2f}"
                            log("RECV", ric, f"realized={realized_val:.2f}")
                            break
            except Exception as e:
                log("ERR", ric, f"get_history {type(e).__name__}: {e}")

        if vix_val is not None and realized_val is not None:
            result["vrp"] = f"{vix_val - realized_val:+.2f}"

        result["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if vix_val is None and realized_val is None:
            result["status"] = "LSEG returned no usable data. See log."
        else:
            result["status"] = "LSEG pull complete."
    except Exception as e:
        result["status"] = f"LSEG error: {type(e).__name__}: {e}"
        result["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        log("ERR", "refresh", f"{type(e).__name__}: {e}\\n{traceback.format_exc()}")

    result["log"] = list(LOG)
    return JSONResponse(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
