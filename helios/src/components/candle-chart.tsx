import { useEffect, useMemo, useRef, useState, type MouseEvent, type PointerEvent } from "react";
import type { OhlcBar } from "@/lib/lseg-types";
import { cn } from "@/lib/utils";

type Props = {
  bars: OhlcBar[];
  ric?: string;
  interval?: string;
};

type Hover = { i: number };

type Zoom = {
  start: number;
  end: number;
  yMin: number;
  yMax: number;
};

type Drag = { x0: number; y0: number; x1: number; y1: number };

const MIN_DRAG = 10;

function fmtPrice(n: number): string {
  if (!Number.isFinite(n)) return "—";
  const abs = Math.abs(n);
  const digits = abs >= 1000 ? 2 : abs >= 10 ? 2 : 4;
  return n.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function fmtTime(raw: string): string {
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw.slice(0, 16);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function svgCoords(svg: SVGSVGElement, clientX: number, clientY: number) {
  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  const p = pt.matrixTransform(ctm.inverse());
  return { x: p.x, y: p.y };
}

export function CandleChart({ bars, ric, interval }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const dragRef = useRef<Drag | null>(null);
  const zoomRef = useRef<Zoom | null>(null);
  const [hover, setHover] = useState<Hover | null>(null);
  const [zoom, setZoom] = useState<Zoom | null>(null);
  const [drag, setDrag] = useState<Drag | null>(null);

  useEffect(() => {
    zoomRef.current = zoom;
  }, [zoom]);

  useEffect(() => {
    setZoom(null);
    zoomRef.current = null;
    dragRef.current = null;
    setDrag(null);
    setHover(null);
  }, [bars]);

  const viewStart = zoom?.start ?? 0;
  const viewEnd = zoom?.end ?? bars.length;
  const visible = useMemo(
    () => bars.slice(viewStart, viewEnd),
    [bars, viewStart, viewEnd],
  );

  const layout = useMemo(() => {
    const w = 860;
    const h = 420;
    const padL = 58;
    const padR = 16;
    const padT = 18;
    const volH = 56;
    const padB = 28;
    const plotB = h - padB - volH;
    const plotT = padT;
    const plotH = plotB - plotT;
    const plotW = w - padL - padR;
    if (visible.length === 0) {
      return {
        w,
        h,
        padL,
        padR,
        padT,
        padB,
        plotB,
        plotT,
        plotH,
        plotW,
        volH,
        min: 0,
        max: 1,
        maxVol: 1,
      };
    }
    let min = Infinity;
    let max = -Infinity;
    let maxVol = 1;
    for (const b of visible) {
      min = Math.min(min, b.low);
      max = Math.max(max, b.high);
      maxVol = Math.max(maxVol, b.volume || 0);
    }
    const pad = (max - min) * 0.06 || 1;
    if (zoom) {
      min = zoom.yMin;
      max = zoom.yMax;
      if (max <= min) max = min + 1;
    } else {
      min -= pad;
      max += pad;
    }
    return {
      w,
      h,
      padL,
      padR,
      padT,
      padB,
      plotB,
      plotT,
      plotH,
      plotW,
      volH,
      min,
      max,
      maxVol,
    };
  }, [visible, zoom]);

  const layoutRef = useRef(layout);
  layoutRef.current = layout;
  const visibleRef = useRef(visible);
  visibleRef.current = visible;
  const viewStartRef = useRef(viewStart);
  viewStartRef.current = viewStart;

  const y = (price: number) => {
    const { plotT, plotH, min, max } = layout;
    return plotT + ((max - price) / (max - min || 1)) * plotH;
  };

  const xAt = (i: number) => {
    const n = Math.max(visible.length, 1);
    const slot = layout.plotW / n;
    return layout.padL + slot * (i + 0.5);
  };

  function priceAt(py: number, L = layout) {
    return L.max - ((py - L.plotT) / (L.plotH || 1)) * (L.max - L.min);
  }

  function indexFromX(px: number, L = layout, n = visible.length) {
    const count = Math.max(n, 1);
    const t = (px - L.padL) / (L.plotW || 1);
    return Math.max(0, Math.min(count - 1, Math.floor(t * count)));
  }

  function clampPlot(x: number, yv: number, L = layout) {
    return {
      x: Math.max(L.padL, Math.min(L.w - L.padR, x)),
      y: Math.max(L.plotT, Math.min(L.plotB, yv)),
    };
  }

  const ticks = useMemo(() => {
    const { min, max } = layout;
    const steps = 4;
    return Array.from({ length: steps + 1 }, (_, i) => min + ((max - min) * i) / steps);
  }, [layout]);

  const hovered = hover ? visible[hover.i] : null;
  const n = visible.length;
  const slot = layout.plotW / Math.max(n, 1);
  const bodyW = Math.max(1.2, Math.min(14, slot * 0.62));

  function resetZoom() {
    dragRef.current = null;
    zoomRef.current = null;
    setDrag(null);
    setZoom(null);
    setHover(null);
  }

  function commitZoom(box: Drag) {
    const L = layoutRef.current;
    const vis = visibleRef.current;
    const x0 = Math.min(box.x0, box.x1);
    const x1 = Math.max(box.x0, box.x1);
    const y0 = Math.min(box.y0, box.y1);
    const y1 = Math.max(box.y0, box.y1);
    if (x1 - x0 < MIN_DRAG && y1 - y0 < MIN_DRAG) return;
    if (vis.length === 0) return;

    let i0 = indexFromX(x0, L, vis.length);
    let i1 = indexFromX(x1, L, vis.length);
    if (i1 < i0) [i0, i1] = [i1, i0];
    if (i1 === i0) i1 = Math.min(vis.length - 1, i0 + 1);

    const absStart = viewStartRef.current + i0;
    const absEnd = viewStartRef.current + i1 + 1;
    if (absEnd - absStart < 1) return;

    let yMin = priceAt(y1, L);
    let yMax = priceAt(y0, L);
    if (yMax < yMin) [yMin, yMax] = [yMax, yMin];
    if (yMax - yMin < (L.max - L.min) * 0.002) {
      let lo = Infinity;
      let hi = -Infinity;
      for (let i = i0; i <= i1; i++) {
        const b = vis[i];
        if (!b) continue;
        lo = Math.min(lo, b.low);
        hi = Math.max(hi, b.high);
      }
      const pad = ((hi - lo) || 1) * 0.06;
      yMin = lo - pad;
      yMax = hi + pad;
    }

    const next = { start: absStart, end: absEnd, yMin, yMax };
    zoomRef.current = next;
    setZoom(next);
    setHover(null);
  }

  function onPointerDown(e: PointerEvent<SVGSVGElement>) {
    if (e.button !== 0) return;
    if (e.detail >= 2) {
      e.preventDefault();
      resetZoom();
      return;
    }
    const svg = svgRef.current;
    if (!svg) return;
    const L = layoutRef.current;
    const raw = svgCoords(svg, e.clientX, e.clientY);
    const c = clampPlot(raw.x, raw.y, L);
    svg.setPointerCapture(e.pointerId);
    const next = { x0: c.x, y0: c.y, x1: c.x, y1: c.y };
    dragRef.current = next;
    setDrag(next);
    setHover(null);
  }

  function onPointerMove(e: PointerEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg) return;
    const L = layoutRef.current;
    const vis = visibleRef.current;
    const raw = svgCoords(svg, e.clientX, e.clientY);
    const current = dragRef.current;
    if (current) {
      const c = clampPlot(raw.x, raw.y, L);
      const next = { ...current, x1: c.x, y1: c.y };
      dragRef.current = next;
      setDrag(next);
      return;
    }
    if (
      raw.x >= L.padL &&
      raw.x <= L.w - L.padR &&
      raw.y >= L.plotT &&
      raw.y <= L.h - L.padB
    ) {
      setHover({ i: indexFromX(raw.x, L, vis.length) });
    } else {
      setHover(null);
    }
  }

  function onPointerUp(e: PointerEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (svg?.hasPointerCapture(e.pointerId)) svg.releasePointerCapture(e.pointerId);
    const current = dragRef.current;
    dragRef.current = null;
    setDrag(null);
    if (!current) return;
    commitZoom(current);
  }

  function onDoubleClick(e: MouseEvent<SVGSVGElement>) {
    e.preventDefault();
    resetZoom();
  }

  if (bars.length === 0) {
    return (
      <div className="flex h-full min-h-80 flex-col items-center justify-center gap-2 px-6 text-center">
        <p className="text-sm text-muted">No bars yet</p>
        <p className="max-w-sm text-xs leading-relaxed text-faint">
          Search an equity, pick a RIC, set the window, then fetch OHLC from Workspace.
        </p>
      </div>
    );
  }

  const rubber =
    drag == null
      ? null
      : {
          x: Math.min(drag.x0, drag.x1),
          y: Math.min(drag.y0, drag.y1),
          w: Math.abs(drag.x1 - drag.x0),
          h: Math.abs(drag.y1 - drag.y0),
        };

  return (
    <div className="relative flex h-full min-h-80 flex-col">
      <div className="flex flex-wrap items-baseline justify-between gap-2 px-4 pt-4">
        <div>
          <p className="font-mono text-xs tracking-widest text-accent uppercase">OHLC</p>
          <h2 className="font-mono text-lg text-fg">
            {ric ?? "—"}
            <span className="ml-2 text-xs text-muted">{interval}</span>
          </h2>
        </div>
        <div className="flex items-center gap-3">
          {hovered ? (
            <dl className="grid grid-cols-5 gap-3 font-mono text-xs tabular-nums">
              <Stat k="O" v={fmtPrice(hovered.open)} />
              <Stat k="H" v={fmtPrice(hovered.high)} />
              <Stat k="L" v={fmtPrice(hovered.low)} />
              <Stat
                k="C"
                v={fmtPrice(hovered.close)}
                up={hovered.close >= hovered.open}
              />
              <Stat k="V" v={Math.round(hovered.volume).toLocaleString()} />
            </dl>
          ) : (
            <p className="font-mono text-xs text-faint">
              {n.toLocaleString()} bars · drag to zoom · double-click reset
            </p>
          )}
          {zoom ? (
            <button
              type="button"
              onClick={resetZoom}
              className="h-8 rounded-sm border border-line px-2.5 font-mono text-[11px] text-accent hover:border-accent-dim"
            >
              Reset
            </button>
          ) : null}
        </div>
      </div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${layout.w} ${layout.h}`}
        className="h-full w-full cursor-crosshair touch-none select-none"
        role="img"
        aria-label={`Candlestick chart for ${ric ?? "selected equity"}`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={() => {
          dragRef.current = null;
          setDrag(null);
        }}
        onDoubleClick={onDoubleClick}
        onPointerLeave={() => {
          if (!dragRef.current) setHover(null);
        }}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line
              x1={layout.padL}
              x2={layout.w - layout.padR}
              y1={y(t)}
              y2={y(t)}
              stroke="var(--color-line)"
              strokeWidth="1"
            />
            <text
              x={layout.padL - 8}
              y={y(t) + 3}
              textAnchor="end"
              fill="var(--color-faint)"
              fontSize="10"
              fontFamily="var(--font-mono)"
            >
              {fmtPrice(t)}
            </text>
          </g>
        ))}
        {visible.map((b, i) => {
          const cx = xAt(i);
          const up = b.close >= b.open;
          const color = up ? "var(--color-up)" : "var(--color-down)";
          const top = y(Math.max(b.open, b.close));
          const bot = y(Math.min(b.open, b.close));
          const bodyH = Math.max(1, bot - top);
          const volH = ((b.volume || 0) / (layout.maxVol || 1)) * (layout.volH - 8);
          return (
            <g key={`${b.time}-${i}`} pointerEvents="none">
              <line
                x1={cx}
                x2={cx}
                y1={y(b.high)}
                y2={y(b.low)}
                stroke={color}
                strokeWidth="1.25"
              />
              <rect
                x={cx - bodyW / 2}
                y={top}
                width={bodyW}
                height={bodyH}
                fill={color}
              />
              <rect
                x={cx - bodyW / 2}
                y={layout.h - layout.padB - volH}
                width={bodyW}
                height={volH}
                fill={color}
                opacity="0.35"
              />
            </g>
          );
        })}
        {hover ? (
          <line
            x1={xAt(hover.i)}
            x2={xAt(hover.i)}
            y1={layout.plotT}
            y2={layout.h - layout.padB}
            stroke="var(--color-ice)"
            strokeDasharray="3 4"
            strokeWidth="1"
            pointerEvents="none"
          />
        ) : null}
        {rubber && rubber.w > 0 && rubber.h > 0 ? (
          <rect
            x={rubber.x}
            y={rubber.y}
            width={rubber.w}
            height={rubber.h}
            fill="var(--color-accent)"
            fillOpacity="0.12"
            stroke="var(--color-accent)"
            strokeWidth="1"
            pointerEvents="none"
          />
        ) : null}
        <text
          x={layout.padL}
          y={layout.h - 8}
          fill="var(--color-faint)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          {fmtTime(visible[0].time)}
        </text>
        <text
          x={layout.w - layout.padR}
          y={layout.h - 8}
          textAnchor="end"
          fill="var(--color-faint)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          {fmtTime(visible[visible.length - 1].time)}
        </text>
      </svg>
    </div>
  );
}

function Stat({ k, v, up }: { k: string; v: string; up?: boolean }) {
  return (
    <div>
      <dt className="text-faint">{k}</dt>
      <dd
        className={cn(
          "text-fg",
          up === true && "text-up",
          up === false && "text-down",
        )}
      >
        {v}
      </dd>
    </div>
  );
}
