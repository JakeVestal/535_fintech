(function () {
  const B = window.HELIOS_BOOK;
  if (!B) {
    document.body.innerHTML = "<p style='padding:2rem;color:#ff6b8a'>Missing book.js</p>";
    return;
  }

  const money = (n, d = 2) => {
    const s = n < 0 ? "−" : "";
    return s + "$" + Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
  };

  const last = B.ledger[B.ledger.length - 1];
  document.getElementById("badge").textContent =
    "SAMPLE · " + B.underlying + " · start " + money(B.startCash, 0);

  const cards = [
    ["Cash", money(last.cash), "Settled dollars after fills"],
    ["Stock LMV", money(last.lmv), last.shares + " " + B.underlying + " @ " + last.stockPx.toFixed(2)],
    ["Short option", money(last.optMv), last.callLabel, last.optMv < 0],
    ["NAV / equity", money(last.nav), "cash + LMV + option MV", false, true],
    ["Initial margin", money(last.init), "Reg T " + B.initPct * 100 + "% of LMV · covered call adds $0"],
    ["Maintenance", money(last.maint), "FINRA " + B.maintPct * 100 + "% of LMV"],
    ["Available funds", money(last.available), "NAV − initial. Room for a new risk."],
    ["Excess equity", money(last.excess), "NAV − maintenance. Margin-call line."],
  ];
  document.getElementById("accounts").innerHTML = cards
    .map(([k, v, h, down, acc]) => {
      const cls = acc ? "accent" : down ? "down" : "";
      return `<div class="card"><div class="lbl">${k}</div><div class="val ${cls}">${v}</div><div class="hint">${h}</div></div>`;
    })
    .join("");

  document.getElementById("blotter-body").innerHTML = B.blotter
    .map((t) => {
      const dir = t.side === "BUY" || t.side === "BTC" ? -1 : 1;
      const delta = dir * t.qty * t.price * t.multiplier;
      const sc = t.side === "SELL" ? "accent" : t.side === "EXPIRE" ? "" : "down";
      const dc = delta >= 0 ? "accent" : "down";
      return `<tr>
        <td class="mono" style="color:var(--muted);white-space:nowrap">${t.ts}</td>
        <td class="mono ${sc}">${t.side}</td>
        <td class="mono">${t.qty}</td>
        <td class="mono">${t.instrument}</td>
        <td class="mono">${t.price.toFixed(2)}</td>
        <td class="mono ${dc}">${money(delta)}</td>
        <td style="color:var(--muted)">${t.notes}</td>
      </tr>`;
    })
    .join("");

  document.getElementById("ledger-body").innerHTML = B.ledger
    .map((r) => {
      const call = r.shortCalls ? `${r.shortCalls} ${r.callLabel}` : "flat";
      return `<tr>
        <td class="mono" style="color:var(--muted)">${r.date}</td>
        <td class="mono">${money(r.cash)}</td>
        <td class="mono">${r.shares}</td>
        <td class="mono accent">${call}</td>
        <td class="mono">${r.stockPx.toFixed(2)}</td>
        <td class="mono">${money(r.lmv)}</td>
        <td class="mono" style="color:var(--muted)">${money(r.optMv)}</td>
        <td class="mono accent">${money(r.nav)}</td>
        <td class="mono" style="color:var(--muted)">${money(r.init)}</td>
        <td class="mono" style="color:var(--muted)">${money(r.maint)}</td>
        <td class="mono">${money(r.available)}</td>
      </tr>`;
    })
    .join("");

  const w = B.writeup || {};
  document.getElementById("writeup").innerHTML = `
    <h2>${w.title || "Rules"}</h2>
    <div class="writeup">
      <div><h3>Fill</h3><p>${w.fill || ""}</p></div>
      <div><h3>Roll</h3><p>${w.roll || ""}</p></div>
      <div><h3>Pin / assignment</h3><p>${w.pin || ""}</p></div>
      <div><h3>Reg T</h3><p>${w.regT || ""}</p></div>
    </div>`;

  drawChart("nav-chart", B.ledger, [
    { key: "nav", color: "#2ee6d0", label: "NAV" },
    { key: "available", color: "#9ef6ea", label: "Available" },
  ]);
  drawChart("mgn-chart", B.ledger, [
    { key: "init", color: "#2ee6d0", label: "Initial" },
    { key: "maint", color: "#ff6b8a", label: "Maint" },
    { key: "cash", color: "#8aa8a4", label: "Cash" },
  ]);

  function drawChart(id, rows, series) {
    const host = document.getElementById(id);
    const W = 800, H = 260, L = 52, R = 12, T = 16, Btm = 28;
    const ys = series.flatMap((s) => rows.map((r) => r[s.key]));
    const ymin = Math.min(0, ...ys);
    const ymax = Math.max(...ys);
    const x = (i) => L + (i * (W - L - R)) / Math.max(1, rows.length - 1);
    const y = (v) => T + ((ymax - v) * (H - T - Btm)) / (ymax - ymin || 1);
    const paths = series
      .map((s) => {
        const d = rows.map((r, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(r[s.key]).toFixed(1)}`).join(" ");
        return `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="1.8"/>`;
      })
      .join("");
    const labels = rows
      .map((r, i) =>
        i % Math.ceil(rows.length / 6) === 0
          ? `<text x="${x(i)}" y="${H - 8}" fill="#5e7673" font-size="10" font-family="ui-monospace,monospace" text-anchor="middle">${r.date.slice(5)}</text>`
          : ""
      )
      .join("");
    host.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${paths}${labels}</svg><div class="tip"></div>`;
    const svg = host.querySelector("svg");
    const tip = host.querySelector(".tip");
    svg.addEventListener("mousemove", (ev) => {
      const rect = svg.getBoundingClientRect();
      const i = Math.round(((ev.clientX - rect.left) / rect.width) * (rows.length - 1) * ((W - L - R) / W) + (L / W) * (rows.length - 1));
      const idx = Math.max(0, Math.min(rows.length - 1, Math.round(((ev.clientX - rect.left) / rect.width) * (rows.length - 1))));
      const r = rows[idx];
      tip.style.display = "block";
      tip.style.left = ev.offsetX + 12 + "px";
      tip.style.top = ev.offsetY + 8 + "px";
      tip.innerHTML =
        r.date +
        "<br>" +
        series.map((s) => s.label + " " + money(r[s.key])).join("<br>");
    });
    svg.addEventListener("mouseleave", () => {
      tip.style.display = "none";
    });
  }
})();
