import { useMemo, useState } from "react";
import type { OptionContract, OptionsCache } from "@/lib/lseg-types";
import { contractKey } from "@/lib/lseg-types";
import { cn } from "@/lib/utils";

type Props = {
  cache: OptionsCache;
  stockHigh?: number | null;
  stockLow?: number | null;
};

type Last = {
  trade: number | null;
  bid: number | null;
  ask: number | null;
  mid: number | null;
  time: string;
};

function lastOf(c: OptionContract | undefined): Last | null {
  if (!c || c.bars.length === 0) return null;
  const b = c.bars[c.bars.length - 1];
  const mid =
    b.bid != null && b.ask != null ? (b.bid + b.ask) / 2 : b.trade ?? b.bid ?? b.ask;
  return { trade: b.trade, bid: b.bid, ask: b.ask, mid: mid ?? null, time: b.time };
}

function shortExpiry(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso.slice(5);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function fmt(n: number | null | undefined, digits = 2): string {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function OptionsSummary({ cache, stockHigh, stockLow }: Props) {
  const contracts = Object.values(cache.contracts);
  const missKeys = new Set(cache.misses.map((m) => m.key));

  const expiries = useMemo(() => {
    const set = new Set<string>(cache.expiries ?? []);
    for (const c of contracts) set.add(c.expiry);
    for (const m of cache.misses) set.add(m.expiry);
    return [...set].sort();
  }, [cache.expiries, cache.misses, contracts]);

  const strikes = useMemo(() => {
    const set = new Set<number>();
    if (cache.strikeMin != null && cache.strikeMax != null && (cache.strikeStep ?? 0) > 0) {
      let guard = 0;
      for (let k = cache.strikeMin; k <= cache.strikeMax + 1e-9 && guard < 80; k = round2(k + cache.strikeStep!)) {
        set.add(round2(k));
        guard += 1;
      }
    }
    for (const c of contracts) set.add(round2(c.strike));
    for (const m of cache.misses) set.add(round2(m.strike));
    return [...set].sort((a, b) => b - a);
  }, [cache.misses, cache.strikeMax, cache.strikeMin, cache.strikeStep, contracts]);

  const maxMid = useMemo(() => {
    let m = 0;
    for (const c of contracts) {
      const last = lastOf(c);
      if (last?.mid != null) m = Math.max(m, last.mid);
    }
    return m || 1;
  }, [contracts]);

  const [picked, setPicked] = useState<string | null>(null);

  const quotedExpiries = new Set(contracts.map((c) => c.expiry)).size;
  const quotedStrikes = new Set(contracts.map((c) => c.strike)).size;
  const tried = contracts.length + cache.misses.length;
  const fill = tried ? Math.round((100 * contracts.length) / tried) : 0;
  const barDays = contracts.reduce((n, c) => n + c.bars.length, 0);

  const pickedContract = picked ? cache.contracts[picked] : undefined;
  const pickedLast = lastOf(pickedContract);

  if (contracts.length === 0 && cache.misses.length === 0) return null;

  return (
    <div className="mt-5 flex flex-col gap-4">
      <div>
        <p className="font-mono text-xs tracking-widest text-accent uppercase">Fetch summary</p>
        <h3 className="text-base font-semibold text-fg">
          {cache.root} call grid · {contracts.length} quoted
        </h3>
      </div>

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Stat label="Quoted" value={String(contracts.length)} accent />
        <Stat label="Empty RICs" value={String(cache.misses.length)} />
        <Stat label="Fill" value={`${fill}%`} />
        <Stat label="Expiries live" value={`${quotedExpiries}/${expiries.length || "—"}`} />
        <Stat label="Strikes live" value={`${quotedStrikes}/${strikes.length || "—"}`} />
        <Stat label="Daily rows" value={barDays.toLocaleString()} />
      </dl>

      {stockLow != null && stockHigh != null ? (
        <p className="font-mono text-xs text-muted">
          Underlying range {fmt(stockLow)}–{fmt(stockHigh)} · strike band{" "}
          {fmt(cache.strikeMin)}–{fmt(cache.strikeMax)} · cells are last mid (bid/ask) or last
          trade. Empty cells were tried and returned no history.
        </p>
      ) : null}

      <div className="overflow-auto rounded-md border border-line">
        <table className="w-max min-w-full border-collapse text-center">
          <thead>
            <tr className="bg-surface-2">
              <th className="sticky left-0 z-10 bg-surface-2 px-2 py-2 text-left font-mono text-xs text-faint">
                Strike
              </th>
              {expiries.map((e) => (
                <th key={e} className="px-1.5 py-2 font-mono text-xs whitespace-nowrap text-faint">
                  {shortExpiry(e)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {strikes.map((k) => {
              const nearSpot =
                stockHigh != null &&
                stockLow != null &&
                k >= stockLow &&
                k <= stockHigh;
              return (
                <tr key={k}>
                  <th
                    className={cn(
                      "sticky left-0 z-10 bg-surface px-2 py-1 text-left font-mono text-xs tabular-nums",
                      nearSpot ? "text-accent" : "text-muted",
                    )}
                  >
                    {k.toFixed(2)}
                  </th>
                  {expiries.map((e) => {
                    const key = contractKey(e, k);
                    const rec = cache.contracts[key];
                    const last = lastOf(rec);
                    const miss = !rec && missKeys.has(key);
                    const active = picked === key;
                    const mid = last?.mid ?? null;
                    const pct = mid == null ? 0 : Math.min(1, mid / maxMid);
                    return (
                      <td key={key} className="p-0.5">
                        <button
                          type="button"
                          disabled={!rec && !miss}
                          onClick={() => setPicked(key)}
                          title={
                            rec
                              ? `${rec.ric} · mid ${fmt(mid)}`
                              : miss
                                ? "No history"
                                : "Not queried"
                          }
                          className={cn(
                            "flex h-9 min-w-14 items-center justify-center rounded-xs border px-1 font-mono text-xs tabular-nums",
                            rec
                              ? "border-accent-dim text-fg"
                              : miss
                                ? "border-line text-faint"
                                : "border-transparent text-faint",
                            active && "border-accent text-accent",
                          )}
                          style={
                            rec
                              ? {
                                  backgroundColor: `color-mix(in srgb, var(--color-accent) ${Math.round(12 + pct * 38)}%, var(--color-bg))`,
                                }
                              : undefined
                          }
                        >
                          {rec ? fmt(mid, mid != null && mid < 1 ? 3 : 2) : miss ? "·" : ""}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap gap-4 font-mono text-xs text-faint">
        <span className="inline-flex items-center gap-2">
          <span className="size-2.5 rounded-xs border border-accent-dim bg-accent/40" />
          quoted (darker = richer last mid)
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="size-2.5 rounded-xs border border-line bg-surface" />
          constructed, no tape
        </span>
        <span className="text-accent">cyan strike = inside stock high/low</span>
      </div>

      {pickedContract ? (
        <div className="rounded-md border border-line bg-bg px-3 py-3">
          <p className="font-mono text-xs text-accent">{pickedContract.ric}</p>
          <p className="mt-1 text-sm text-fg">
            {pickedContract.expiry} · {pickedContract.strike.toFixed(2)} call
            {pickedContract.expired ? " · expired RIC" : ""}
          </p>
          <dl className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5">
            <Mini k="Bars" v={String(pickedContract.bars.length)} />
            <Mini k="Last" v={pickedLast ? pickedLast.time.slice(0, 10) : "—"} />
            <Mini k="Trade" v={fmt(pickedLast?.trade)} />
            <Mini k="Bid" v={fmt(pickedLast?.bid)} />
            <Mini k="Ask" v={fmt(pickedLast?.ask)} />
          </dl>
        </div>
      ) : null}

      {contracts.length > 0 ? (
        <details className="rounded-md border border-line">
          <summary className="cursor-pointer px-3 py-2 font-mono text-xs text-muted">
            Quoted contract list ({contracts.length})
          </summary>
          <div className="overflow-auto border-t border-line">
            <table className="w-full min-w-[36rem] text-left text-xs">
              <thead className="bg-surface-2 font-mono text-xs text-faint">
                <tr>
                  <th className="px-3 py-2">Expiry</th>
                  <th className="px-3 py-2">Strike</th>
                  <th className="px-3 py-2">RIC</th>
                  <th className="px-3 py-2">Bars</th>
                  <th className="px-3 py-2">Last trade / bid / ask</th>
                </tr>
              </thead>
              <tbody>
                {contracts
                  .slice()
                  .sort((a, b) => a.expiry.localeCompare(b.expiry) || a.strike - b.strike)
                  .map((c) => {
                    const last = lastOf(c);
                    return (
                      <tr key={c.key} className="border-t border-line">
                        <td className="px-3 py-1.5 font-mono text-fg">{c.expiry}</td>
                        <td className="px-3 py-1.5 font-mono tabular-nums text-fg">
                          {c.strike.toFixed(2)}
                        </td>
                        <td className="px-3 py-1.5 font-mono text-accent">{c.ric}</td>
                        <td className="px-3 py-1.5 font-mono tabular-nums text-muted">
                          {c.bars.length}
                        </td>
                        <td className="px-3 py-1.5 font-mono tabular-nums text-muted">
                          {last
                            ? `${fmt(last.trade)} / ${fmt(last.bid)} / ${fmt(last.ask)}`
                            : "—"}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </div>
  );
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-md border border-line bg-bg px-3 py-2">
      <dt className="font-mono text-xs text-faint">{label}</dt>
      <dd className={cn("mt-0.5 font-mono text-sm", accent ? "text-accent" : "text-fg")}>{value}</dd>
    </div>
  );
}

function Mini({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="font-mono text-xs text-faint">{k}</dt>
      <dd className="font-mono text-sm text-fg">{v}</dd>
    </div>
  );
}
