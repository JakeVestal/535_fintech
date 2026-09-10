(function () {
  const B = window.HELIOS_BOOK;
  if (!B) {
    document.body.insertAdjacentHTML(
      "afterbegin",
      "<p style='padding:2rem;color:#ff6b8a;font-family:sans-serif'>Missing book.js</p>"
    );
    return;
  }

  const money = (n, d = 2) => {
    const s = n < 0 ? "−" : "";
    return s + "$" + Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
  };

  const last = B.ledger[B.ledger.length - 1];
  const badge = document.getElementById("badge");
  if (badge) badge.textContent = "SAMPLE · " + B.underlying + " · start " + money(B.startCash, 0);

  const cards = [
    ["Cash", money(last.cash), "Settled dollars after fills"],
    ["Stock LMV", money(last.lmv), last.shares + " " + B.underlying + " @ " + last.stockPx.toFixed(2)],
    ["Short option", money(last.optMv), last.callLabel, last.optMv < 0],
    ["NAV / equity", money(last.nav), "cash + LMV + option MV", false, true],
    ["Initial margin", money(last.init), "Reg T " + Math.round(B.initPct * 100) + "% of LMV · covered call adds $0"],
    ["Maintenance", money(last.maint), "FINRA " + Math.round(B.maintPct * 100) + "% of LMV"],
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
        <td class="mono">${Number(t.price).toFixed(2)}</td>
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
        <td class="mono">${Number(r.stockPx).toFixed(2)}</td>
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
  const wu = document.getElementById("writeup");
  if (wu) {
    wu.innerHTML = `
      <div class="pane-head"><div><p class="kicker">Rules</p><h2>${w.title || "Covered-call rules"}</h2></div></div>
      <div class="writeup">
        <div><h3>Fill</h3><p>${w.fill || ""}</p></div>
        <div><h3>Roll</h3><p>${w.roll || ""}</p></div>
        <div><h3>Pin / assignment</h3><p>${w.pin || ""}</p></div>
        <div><h3>Reg T</h3><p>${w.regT || ""}</p></div>
      </div>`;
  }

  drawBookChart("book-chart", B.ledger);

  function drawBookChart(id, rows) {
    const host = document.getElementById(id);
    if (!host || !rows.length) return;
    const meta = document.getElementById("chart-meta");
    const W = 720, H = 280, padL = 52, padR = 16, padT = 16, padB = 32;
    const nav = rows.map((r) => r.nav);
    const init = rows.map((r) => r.init);
    const maint = rows.map((r) => r.maint);
    const all = nav.concat(init, maint);
    const min = Math.min.apply(null, all) * 0.92;
    const max = Math.max.apply(null, all) * 1.04;
    const x = (i) => padL + (i / Math.max(rows.length - 1, 1)) * (W - padL - padR);
    const y = (v) => padT + ((max - v) / (max - min || 1)) * (H - padT - padB);
    const path = (vals) =>
      vals.map((v, i) => (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
    const grid = [0, 0.5, 1]
      .map((t) => {
        const v = min + (max - min) * t;
        const yy = y(v);
        return `<line x1="${padL}" x2="${W - padR}" y1="${yy}" y2="${yy}" stroke="#24313c"/>
          <text x="${padL - 8}" y="${yy + 3}" text-anchor="end" fill="#5e7673" font-size="10" font-family="IBM Plex Mono,monospace">${Math.round(v).toLocaleString()}</text>`;
      })
      .join("");
    const dots = rows
      .map((r, i) => `<g class="pt" data-i="${i}">
        <circle cx="${x(i)}" cy="${y(r.nav)}" r="3" fill="#2ee6d0"/>
        <circle cx="${x(i)}" cy="${y(r.init)}" r="2" fill="#5e7673"/>
        <circle cx="${x(i)}" cy="${y(r.maint)}" r="2" fill="#ff6b8a"/>
      </g>`)
      .join("");
    host.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="NAV, initial, maintenance">
      ${grid}
      <path d="${path(init)}" fill="none" stroke="#5e7673" stroke-width="1.25" stroke-dasharray="4 4"/>
      <path d="${path(maint)}" fill="none" stroke="#ff6b8a" stroke-width="1.25" stroke-dasharray="3 4"/>
      <path d="${path(nav)}" fill="none" stroke="#2ee6d0" stroke-width="2"/>
      ${dots}
      <line id="hair" x1="0" x2="0" y1="${padT}" y2="${H - padB}" stroke="#9ef6ea" stroke-dasharray="3 3" visibility="hidden"/>
      <text x="${padL}" y="${H - 8}" fill="#5e7673" font-size="10" font-family="IBM Plex Mono,monospace">${rows[0].date}</text>
      <text x="${W - padR}" y="${H - 8}" text-anchor="end" fill="#5e7673" font-size="10" font-family="IBM Plex Mono,monospace">${rows[rows.length - 1].date}</text>
    </svg><div class="tip"></div>`;

    const svg = host.querySelector("svg");
    const tip = host.querySelector(".tip");
    const hair = host.querySelector("#hair");

    function show(i, ev) {
      const r = rows[i];
      hair.setAttribute("x1", x(i));
      hair.setAttribute("x2", x(i));
      hair.setAttribute("visibility", "visible");
      if (meta) meta.textContent = r.date;
      tip.style.display = "block";
      const rect = host.getBoundingClientRect();
      tip.style.left = Math.min(rect.width - 180, Math.max(8, ev.clientX - rect.left + 12)) + "px";
      tip.style.top = Math.max(8, ev.clientY - rect.top - 8) + "px";
      tip.innerHTML = `<b>${r.date}</b>
        <dl>
          <dt>NAV</dt><dd class="accent">${money(r.nav)}</dd>
          <dt>Initial</dt><dd>${money(r.init)}</dd>
          <dt>Maintenance</dt><dd class="down">${money(r.maint)}</dd>
          <dt>Available</dt><dd>${money(r.available)}</dd>
          <dt>Excess</dt><dd>${money(r.excess)}</dd>
          <dt>Cash</dt><dd>${money(r.cash)}</dd>
        </dl>`;
    }
    function hide() {
      hair.setAttribute("visibility", "hidden");
      tip.style.display = "none";
      if (meta) meta.textContent = "NAV · initial · maintenance · hover a date";
    }
    svg.addEventListener("pointermove", (ev) => {
      const pt = svg.createSVGPoint();
      pt.x = ev.clientX;
      pt.y = ev.clientY;
      const ctm = svg.getScreenCTM();
      if (!ctm) return;
      const p = pt.matrixTransform(ctm.inverse());
      const t = (p.x - padL) / (W - padL - padR || 1);
      const i = Math.max(0, Math.min(rows.length - 1, Math.round(t * (rows.length - 1))));
      show(i, ev);
    });
    svg.addEventListener("pointerleave", hide);
  }
})();
