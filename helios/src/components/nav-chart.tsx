import { useMemo, useRef, useState, type PointerEvent } from "react";
import type { LedgerRow } from "@/lib/sample-book";

type Props = { rows: LedgerRow[] };

function fmt(n: number, digits = 0): string {
  return n.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function money(n: number): string {
  const sign = n < 0 ? "−" : "";
  return `${sign}$${fmt(Math.abs(n), 2)}`;
}

function svgCoords(svg: SVGSVGElement, clientX: number, clientY: number) {
  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  return pt.matrixTransform(ctm.inverse());
}

const L = { w: 720, h: 280, padL: 52, padR: 16, padT: 16, padB: 32 };

export function NavChart({ rows }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  const series = useMemo(() => {
    const nav = rows.map((r) => r.nav);
    const init = rows.map((r) => r.init);
    const maint = rows.map((r) => r.maint);
    const all = [...nav, ...init, ...maint];
    const min = Math.min(...all) * 0.92;
    const max = Math.max(...all) * 1.04;
    return { nav, init, maint, min, max };
  }, [rows]);

  const x = (i: number) =>
    L.padL + (i / Math.max(rows.length - 1, 1)) * (L.w - L.padL - L.padR);
  const y = (v: number) =>
    L.padT + ((series.max - v) / (series.max - series.min || 1)) * (L.h - L.padT - L.padB);
  const path = (vals: number[]) =>
    vals.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  function indexFromX(px: number): number {
    const t = (px - L.padL) / (L.w - L.padL - L.padR || 1);
    return Math.max(0, Math.min(rows.length - 1, Math.round(t * (rows.length - 1))));
  }

  function onMove(e: PointerEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg || rows.length === 0) return;
    const raw = svgCoords(svg, e.clientX, e.clientY);
    if (raw.x < L.padL || raw.x > L.w - L.padR || raw.y < L.padT || raw.y > L.h - L.padB) {
      setHover(null);
      return;
    }
    setHover(indexFromX(raw.x));
  }

  const row = hover != null ? rows[hover] : null;
  const tipLeft =
    hover == null ? 0 : Math.min(72, Math.max(8, (x(hover) / L.w) * 100 - 14));

  return (
    <div className="relative flex h-full min-h-64 flex-col">
      <div className="flex flex-wrap items-baseline justify-between gap-2 px-4 pt-4">
        <div>
          <p className="font-mono text-xs tracking-widest text-accent uppercase">NAV</p>
          <h3 className="font-mono text-lg text-fg">Growth of the sample book</h3>
        </div>
        <p className="font-mono text-xs text-faint">
          {row ? row.date : "NAV · initial · maintenance · hover a date"}
        </p>
      </div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${L.w} ${L.h}`}
        className="h-full w-full cursor-crosshair"
        role="img"
        aria-label="NAV, initial margin, and maintenance over time"
        onPointerMove={onMove}
        onPointerLeave={() => setHover(null)}
      >
        {[0, 0.5, 1].map((t) => {
          const v = series.min + (series.max - series.min) * t;
          const yy = y(v);
          return (
            <g key={t}>
              <line
                x1={L.padL}
                x2={L.w - L.padR}
                y1={yy}
                y2={yy}
                stroke="var(--color-line)"
              />
              <text
                x={L.padL - 8}
                y={yy + 3}
                textAnchor="end"
                fill="var(--color-faint)"
                fontSize="10"
                fontFamily="var(--font-mono)"
              >
                {fmt(v)}
              </text>
            </g>
          );
        })}
        <path d={path(series.init)} fill="none" stroke="var(--color-faint)" strokeWidth="1.25" strokeDasharray="4 4" />
        <path d={path(series.maint)} fill="none" stroke="var(--color-down)" strokeWidth="1.25" strokeDasharray="3 4" />
        <path d={path(series.nav)} fill="none" stroke="var(--color-accent)" strokeWidth="2" />
        {rows.map((r, i) => (
          <g key={r.date}>
            <circle cx={x(i)} cy={y(r.nav)} r={hover === i ? 4.5 : 3} fill="var(--color-accent)" />
            <circle cx={x(i)} cy={y(r.init)} r={hover === i ? 3.5 : 2} fill="var(--color-faint)" />
            <circle cx={x(i)} cy={y(r.maint)} r={hover === i ? 3.5 : 2} fill="var(--color-down)" />
          </g>
        ))}
        {hover != null && row ? (
          <line
            x1={x(hover)}
            x2={x(hover)}
            y1={L.padT}
            y2={L.h - L.padB}
            stroke="var(--color-ice)"
            strokeWidth="1"
            strokeDasharray="3 3"
          />
        ) : null}
        <rect
          x={L.padL}
          y={L.padT}
          width={L.w - L.padL - L.padR}
          height={L.h - L.padT - L.padB}
          fill="transparent"
        />
        <text x={L.padL} y={L.h - 8} fill="var(--color-faint)" fontSize="10" fontFamily="var(--font-mono)">
          {rows[0]?.date}
        </text>
        <text
          x={L.w - L.padR}
          y={L.h - 8}
          textAnchor="end"
          fill="var(--color-faint)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          {rows[rows.length - 1]?.date}
        </text>
      </svg>

      {row && hover != null ? (
        <div
          className="pointer-events-none absolute top-16 z-10 min-w-52 rounded-md border border-line bg-surface px-3 py-2"
          style={{ left: `${tipLeft}%` }}
        >
          <p className="font-mono text-xs text-accent">{row.date}</p>
          <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 font-mono text-xs tabular-nums">
            <dt className="text-faint">NAV</dt>
            <dd className="text-right text-accent">{money(row.nav)}</dd>
            <dt className="text-faint">Initial</dt>
            <dd className="text-right text-fg">{money(row.init)}</dd>
            <dt className="text-faint">Maintenance</dt>
            <dd className="text-right text-down">{money(row.maint)}</dd>
            <dt className="text-faint">Available</dt>
            <dd className="text-right text-fg">{money(row.available)}</dd>
            <dt className="text-faint">Excess</dt>
            <dd className="text-right text-fg">{money(row.excess)}</dd>
            <dt className="text-faint">Cash</dt>
            <dd className="text-right text-muted">{money(row.cash)}</dd>
          </dl>
        </div>
      ) : null}
    </div>
  );
}
