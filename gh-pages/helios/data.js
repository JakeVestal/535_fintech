(function () {
  const hosted =
    location.hostname.endsWith("github.io") ||
    (location.protocol === "https:" && location.hostname !== "localhost");

  if (hosted) {
    document.getElementById("gate").hidden = false;
    document.getElementById("lab").hidden = true;
    return;
  }

  const API = (location.hostname === "127.0.0.1" || location.hostname === "localhost")
    ? "/api/lseg"
    : "http://127.0.0.1:8765/api/lseg";

  const $ = (id) => document.getElementById(id);
  const status = (t) => { $("status").textContent = t; };
  let lastPayload = null;

  const today = new Date();
  const start = new Date(today.getTime() - 10 * 7 * 24 * 3600 * 1000);
  const iso = (d) => d.toISOString().slice(0, 10);
  $("end").value = iso(today);
  $("start").value = iso(start);
  $("q").value = "UUUU";

  async function rpc(body) {
    const res = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const json = await res.json();
    if (!json || json.ok === false) {
      const err = new Error((json && json.message) || res.statusText || "request failed");
      err.code = json && json.code;
      throw err;
    }
    return json;
  }

  async function ping() {
    try {
      const h = await rpc({ op: "health" });
      $("health").textContent = h.workspace ? "Workspace up" : "Workspace not running";
      $("health").classList.toggle("down", !h.workspace);
    } catch (e) {
      $("health").textContent = "no local server";
      $("health").classList.add("down");
      status("Start python3 helios/python/local_server.py  (this page talks to 127.0.0.1:8765).");
    }
  }

  $("search").addEventListener("click", async () => {
    try {
      status("Searching…");
      const out = await rpc({ op: "search", query: $("q").value });
      const hits = out.hits || [];
      $("ric").innerHTML = hits
        .map((h) => `<option value="${h.ric}">${h.ric} — ${h.title || h.ticker || ""}</option>`)
        .join("");
      status(hits.length ? hits.length + " hits" : "No matches");
    } catch (e) {
      status(e.message);
    }
  });

  $("fetch").addEventListener("click", async () => {
    const ric = $("ric").value;
    if (!ric) {
      status("Search and pick a RIC first.");
      return;
    }
    try {
      status("Fetching " + ric + "…");
      const out = await rpc({
        op: "history",
        ric,
        start: $("start").value,
        end: $("end").value,
        interval: $("interval").value,
      });
      lastPayload = out;
      $("dl").disabled = !(out.bars && out.bars.length);
      draw(out.bars || []);
      status((out.bars || []).length + " bars · " + ric);
    } catch (e) {
      status(e.message);
    }
  });

  $("dl").addEventListener("click", () => {
    if (!lastPayload) return;
    const blob = new Blob([JSON.stringify(lastPayload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = (lastPayload.ric || "bars") + ".json";
    a.click();
  });

  function draw(bars) {
    const host = $("candles");
    if (!bars.length) {
      host.innerHTML = "<p class='lede'>No bars.</p>";
      return;
    }
    const W = 900, H = 320, L = 56, R = 8, T = 12, B = 28;
    const lo = Math.min(...bars.map((b) => b.low));
    const hi = Math.max(...bars.map((b) => b.high));
    const x = (i) => L + ((i + 0.5) * (W - L - R)) / bars.length;
    const y = (v) => T + ((hi - v) * (H - T - B)) / (hi - lo || 1);
    const w = Math.max(1, (W - L - R) / bars.length - 1);
    const sticks = bars
      .map((b, i) => {
        const up = b.close >= b.open;
        const color = up ? "#2ee6d0" : "#ff6b8a";
        const bodyTop = y(Math.max(b.open, b.close));
        const bodyBot = y(Math.min(b.open, b.close));
        const bh = Math.max(1, bodyBot - bodyTop);
        return `<line x1="${x(i)}" x2="${x(i)}" y1="${y(b.high)}" y2="${y(b.low)}" stroke="${color}" stroke-width="1"/>
          <rect x="${x(i) - w / 2}" y="${bodyTop}" width="${w}" height="${bh}" fill="${color}"/>`;
      })
      .join("");
    host.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${sticks}
      <text x="8" y="14" fill="#5e7673" font-size="10" font-family="ui-monospace,monospace">${hi.toFixed(2)}</text>
      <text x="8" y="${H - 18}" fill="#5e7673" font-size="10" font-family="ui-monospace,monospace">${lo.toFixed(2)}</text>
    </svg>`;
  }

  ping();
})();
