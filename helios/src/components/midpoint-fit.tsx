import { useMemo } from "react";
import type { OptionsCache } from "@/lib/lseg-types";
import { ordinaryLeastSquares } from "@/lib/ols";

type Point = { mid: number; trade: number; ric: string; time: string };

function collect(cache: OptionsCache): Point[] {
  const pts: Point[] = [];
  for (const c of Object.values(cache.contracts)) {
    for (const b of c.bars) {
      if (b.trade == null || b.bid == null || b.ask == null) continue;
      if (!(b.ask >= b.bid) || b.trade <= 0) continue;
      pts.push({
        mid: (b.bid + b.ask) / 2,
        trade: b.trade,
        ric: c.ric,
        time: b.time,
      });
    }
  }
  return pts;
}

export function MidpointFit({ cache }: { cache: OptionsCache | null }) {
  const pts = useMemo(() => (cache ? collect(cache) : []), [cache]);
  const fit = useMemo(
    () => ordinaryLeastSquares(pts.map((p) => p.mid), pts.map((p) => p.trade)),
    [pts],
  );

  const layout = { w: 640, h: 340, padL: 48, padR: 16, padT: 16, padB: 36 };
  const domain = useMemo(() => {
    if (pts.length === 0) return { min: 0, max: 1 };
    let min = Infinity;
    let max = -Infinity;
    for (const p of pts) {
      min = Math.min(min, p.mid, p.trade);
      max = Math.max(max, p.mid, p.trade);
    }
    const pad = (max - min) * 0.08 || 0.05;
    return { min: Math.max(0, min - pad), max: max + pad };
  }, [pts]);

  const xy = (v: number) => {
    const { padL, padR, padT, padB, w, h } = layout;
    const t = (v - domain.min) / (domain.max - domain.min || 1);
    return {
      x: padL + t * (w - padL - padR),
      y: padT + (1 - t) * (h - padT - padB),
    };
  };

  const line = fit
    ? {
        a: xy(fit.xMin),
        b: xy(fit.xMax),
        ya: fit.intercept + fit.slope * fit.xMin,
        yb: fit.intercept + fit.slope * fit.xMax,
      }
    : null;

  return (
    <section className="mt-5 rounded-lg border border-line bg-surface p-4 sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-xs tracking-widest text-accent uppercase">Microstructure check</p>
          <h3 className="text-lg font-semibold text-fg">Trade vs bid/ask midpoint</h3>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted">
            Every option bar that has a print and a two-sided quote. X is (bid+ask)/2, Y is TRDPRC_1.
            Last week we assumed trades sit on the mid; R² on the fit is the check.
          </p>
        </div>
        {fit ? (
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Mini k="n" v={fit.n.toLocaleString()} />
            <Mini k="slope" v={fit.slope.toFixed(3)} />
            <Mini k="intercept" v={fit.intercept.toFixed(3)} />
            <Mini k="R²" v={fit.r2.toFixed(3)} accent />
          </dl>
        ) : null}
      </div>

      {pts.length < 2 ? (
        <p className="mt-4 font-mono text-xs text-faint">
          Pull weeklies first. The scatter needs bars with TRDPRC_1, OPEN_BID, and OPEN_ASK all present.
        </p>
      ) : (
        <svg
          viewBox={`0 0 ${layout.w} ${layout.h}`}
          className="mt-4 h-80 w-full"
          role="img"
          aria-label="Trade price versus bid-ask midpoint"
        >
          <line
            x1={xy(domain.min).x}
            y1={xy(domain.min).y}
            x2={xy(domain.max).x}
            y2={xy(domain.max).y}
            stroke="var(--color-line)"
            strokeDasharray="4 4"
          />
          {pts.map((p, i) => {
            const c = xy(p.mid);
            const d = xy(p.trade);
            return (
              <circle
                key={`${p.ric}-${p.time}-${i}`}
                cx={c.x}
                cy={d.y}
                r="2.4"
                fill="var(--color-accent)"
                fillOpacity="0.7"
              />
            );
          })}
          {line ? (
            <line
              x1={line.a.x}
              y1={xy(line.ya).y}
              x2={line.b.x}
              y2={xy(line.yb).y}
              stroke="var(--color-ice)"
              strokeWidth="1.75"
            />
          ) : null}
          <text
            x={layout.w / 2}
            y={layout.h - 6}
            textAnchor="middle"
            fill="var(--color-faint)"
            fontSize="10"
            fontFamily="var(--font-mono)"
          >
            midpoint (bid+ask)/2
          </text>
          <text
            x={14}
            y={layout.h / 2}
            fill="var(--color-faint)"
            fontSize="10"
            fontFamily="var(--font-mono)"
            transform={`rotate(-90 14 ${layout.h / 2})`}
            textAnchor="middle"
          >
            trade
          </text>
        </svg>
      )}
      {fit ? (
        <p className="mt-2 font-mono text-xs text-muted">
          trade ≈ {fit.intercept.toFixed(3)} + {fit.slope.toFixed(3)} × mid · dashed line is y = x · ice
          line is OLS. R² near 1 means last week’s mid ≈ trade assumption holds on this tape.
        </p>
      ) : null}
    </section>
  );
}

function Mini({ k, v, accent }: { k: string; v: string; accent?: boolean }) {
  return (
    <div className="rounded-md border border-line bg-bg px-3 py-2">
      <dt className="font-mono text-xs text-faint">{k}</dt>
      <dd className={`font-mono text-sm ${accent ? "text-accent" : "text-fg"}`}>{v}</dd>
    </div>
  );
}
