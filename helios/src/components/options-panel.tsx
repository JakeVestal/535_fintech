import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { OptionsSummary } from "@/components/options-summary";
import { MidpointFit } from "@/components/midpoint-fit";
import { fetchOptionsBatch, planOptions } from "@/lib/lseg.functions";
import { useOptionsCache } from "@/lib/options-cache";
import type {
  BarSize,
  EquityHit,
  LsegErrorCode,
  OhlcBar,
  OptionsPlan,
} from "@/lib/lseg-types";
import { isWorkspaceError } from "@/lib/lseg-types";

const BATCH = 8;
const CONCURRENCY = 1;

type Props = {
  selected: EquityHit | null;
  bars: OhlcBar[];
  start: string;
  interval: BarSize;
  onWorkspaceError: (code: LsegErrorCode, detail?: string | null) => void;
};

export function OptionsPanel({ selected, bars, start, interval, onWorkspaceError }: Props) {
  const cache = useOptionsCache((s) => s.cache);
  const progress = useOptionsCache((s) => s.progress);
  const mergeFetch = useOptionsCache((s) => s.mergeFetch);
  const setProgress = useOptionsCache((s) => s.setProgress);
  const setCache = useOptionsCache((s) => s.setCache);
  const [plan, setPlan] = useState<OptionsPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("Fetch the underlying first, then pull weekly calls in the traded range.");

  const range = useMemo(() => {
    if (bars.length === 0) return null;
    let high = -Infinity;
    let low = Infinity;
    for (const b of bars) {
      high = Math.max(high, b.high);
      low = Math.min(low, b.low);
    }
    return { high, low };
  }, [bars]);

  const hasCache =
    !!cache && (Object.keys(cache.contracts).length > 0 || cache.misses.length > 0);

  async function onPull() {
    if (!selected || bars.length === 0) return;
    setBusy(true);
    setProgress({ done: 0, total: 0 });
    try {
      const planned = await planOptions({
        data: { ric: selected.ric, bars, extraWeeks: 5 },
      });
      if (!planned.ok) {
        setNote(planned.message);
        if (isWorkspaceError(planned.code)) onWorkspaceError(planned.code, planned.detail);
        return;
      }
      setPlan(planned);
      setCache({
        root: planned.root,
        underlying: planned.underlying,
        high: planned.high,
        low: planned.low,
        strikeMin: planned.strikeMin,
        strikeMax: planned.strikeMax,
        strikeStep: planned.strikeStep,
        expiries: planned.expiries,
        contracts: {},
        misses: [],
      });
      const lastExpiry = planned.expiries[planned.expiries.length - 1] ?? start;
      const total = planned.candidates.length;
      const chunks: (typeof planned.candidates)[] = [];
      for (let i = 0; i < planned.candidates.length; i += BATCH) {
        chunks.push(planned.candidates.slice(i, i + BATCH));
      }
      setProgress({ done: 0, total });
      setNote(`Trying ${total} call RICs in batches of ${BATCH} · ${interval}`);

      let done = 0;
      let stop = false;
      for (let i = 0; i < chunks.length && !stop; i += CONCURRENCY) {
        const wave = chunks.slice(i, i + CONCURRENCY);
        const results = await Promise.all(
          wave.map((slice) =>
            fetchOptionsBatch({
              data: {
                ric: selected.ric,
                root: planned.root,
                start,
                end: `${lastExpiry}T23:59:59`,
                interval,
                high: planned.high,
                low: planned.low,
                strikeMin: planned.strikeMin,
                strikeMax: planned.strikeMax,
                strikeStep: planned.strikeStep,
                expiries: planned.expiries,
                candidates: slice,
              },
            }),
          ),
        );
        for (let w = 0; w < results.length; w++) {
          const result = results[w];
          const slice = wave[w];
          if (!result.ok) {
            setNote(result.message);
            if (isWorkspaceError(result.code)) onWorkspaceError(result.code, result.detail);
            stop = true;
            break;
          }
          mergeFetch(result.added, result.misses, {
            root: planned.root,
            underlying: planned.underlying,
            high: planned.high,
            low: planned.low,
            strikeMin: planned.strikeMin,
            strikeMax: planned.strikeMax,
            strikeStep: planned.strikeStep,
            expiries: planned.expiries,
          });
          done += slice.length;
          setProgress({ done: Math.min(done, total), total });
          setNote(
            `${Math.min(done, total)}/${total} · ${result.contractCount} quoted on disk · ${result.missCount} empty this batch`,
          );
        }
      }
    } catch (err) {
      onWorkspaceError("workspace_unavailable", err instanceof Error ? err.message : String(err));
      setNote("Options pull failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-lg border border-line bg-surface p-4 sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-xs tracking-widest text-accent uppercase">
            Covered-call tape
          </p>
          <h2 className="text-lg font-semibold text-fg">Weekly calls in range</h2>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted">
            Last session of each week in the stock series, plus five Fridays past the last bar.
            Strikes from the traded low to a step above the high. Expired RICs get the{" "}
            <span className="font-mono text-accent">^MYY</span> suffix. Cache is keyed by expiry
            and strike for the surface next.
          </p>
        </div>
        <Button type="button" onClick={() => void onPull()} disabled={!selected || bars.length === 0 || busy}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : null}
          Pull weeklies
        </Button>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Stock low" value={range ? range.low.toFixed(2) : "—"} />
        <Stat label="Stock high" value={range ? range.high.toFixed(2) : "—"} />
        <Stat
          label="Strike band"
          value={
            plan
              ? `${plan.strikeMin.toFixed(2)}–${plan.strikeMax.toFixed(2)} × ${plan.strikeStep}`
              : "—"
          }
        />
        <Stat label="Expiries" value={plan ? String(plan.expiries.length) : "—"} />
      </dl>

      {progress ? (
        <div className="mt-4">
          <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
            <div
              className="h-full bg-accent transition-[width] duration-150"
              style={{ width: `${progress.total ? (100 * progress.done) / progress.total : 0}%` }}
            />
          </div>
          <p className="mt-2 font-mono text-xs text-faint">
            {progress.done}/{progress.total} RICs · {note}
          </p>
        </div>
      ) : (
        <p className="mt-4 font-mono text-xs text-faint">{note}</p>
      )}

      {hasCache && cache ? (
        <>
          <OptionsSummary cache={cache} stockHigh={range?.high} stockLow={range?.low} />
          <MidpointFit cache={cache} />
        </>
      ) : (
        <MidpointFit cache={cache} />
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-bg px-3 py-2">
      <dt className="font-mono text-xs text-faint">{label}</dt>
      <dd className="mt-0.5 font-mono text-sm text-fg">{value}</dd>
    </div>
  );
}
