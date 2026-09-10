import { createFileRoute } from "@tanstack/react-router";
import { Loader2, Search, Wifi, WifiOff } from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import { CandleChart } from "@/components/candle-chart";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { WorkspaceAlert } from "@/components/workspace-alert";
import { OptionsPanel } from "@/components/options-panel";
import { fetchHistory, loadOptionsCache, searchEquities } from "@/lib/lseg.functions";
import { useOptionsCache } from "@/lib/options-cache";
import { BAR_SIZES, type BarSize, type EquityHit, type HistoryResult, type LsegErrorCode, type OhlcBar, isWorkspaceError } from "@/lib/lseg-types";
import { cn, isoDate, weeksAgo } from "@/lib/utils";

export const Route = createFileRoute("/data")({
  component: DataPage,
  errorComponent: function DataError({ error }) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-16">
        <p className="font-mono text-xs tracking-widest text-accent uppercase">Data</p>
        <h1 className="mt-2 text-2xl font-semibold text-fg">This route did not load</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          Stop npm run dev, confirm src/routes/data.tsx is on disk, then start it again. Vite will
          not attach a new route until restart.
        </p>
        <pre className="mt-4 overflow-auto rounded-md border border-line bg-surface p-3 font-mono text-xs text-faint">
          {error instanceof Error ? error.message : String(error)}
        </pre>
      </main>
    );
  },
});

function DataPage() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<EquityHit[]>([]);
  const [selected, setSelected] = useState<EquityHit | null>(null);
  const [start, setStart] = useState(() => isoDate(weeksAgo(10)));
  const [end, setEnd] = useState(() => isoDate(new Date()));
  const [interval, setInterval] = useState<BarSize>("hourly");
  const [bars, setBars] = useState<OhlcBar[]>([]);
  const [searching, setSearching] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [alertOpen, setAlertOpen] = useState(false);
  const [alertCode, setAlertCode] = useState<LsegErrorCode | null>(null);
  const [alertDetail, setAlertDetail] = useState<string | null>(null);
  const [status, setStatus] = useState("Idle — search when Workspace is up");
  const [chartMeta, setChartMeta] = useState<{ ric: string; interval: string } | null>(null);
  const setCache = useOptionsCache((s) => s.setCache);

  function raiseAlert(code: LsegErrorCode, detail?: string | null) {
    setAlertCode(code);
    setAlertDetail(detail ?? null);
    setAlertOpen(true);
    setConnected(false);
  }

  async function onSearch(e?: FormEvent) {
    e?.preventDefault();
    const q = query.trim();
    if (!q) return;
    setSearching(true);
    setStatus(`Searching “${q}”`);
    try {
      const result = await searchEquities({ data: { query: q } });
      if (!result.ok) {
        setHits([]);
        setStatus(result.message);
        if (isWorkspaceError(result.code)) raiseAlert(result.code, result.detail);
        return;
      }
      setHits(result.hits);
      setSelected((prev) => result.hits.find((h) => h.ric === prev?.ric) ?? result.hits[0] ?? null);
      setStatus(
        result.hits.length
          ? `${result.hits.length} matching quotes`
          : "No equity quotes matched",
      );
      setConnected(true);
    } catch (err) {
      raiseAlert("workspace_unavailable", err instanceof Error ? err.message : String(err));
      setStatus("Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function onFetch() {
    if (!selected) return;
    setFetching(true);
    setStatus(`Fetching ${selected.ric} ${interval}`);
    try {
      const result: HistoryResult = await fetchHistory({
        data: { ric: selected.ric, start, end, interval },
      });
      if (!result.ok) {
        setStatus(result.message);
        if (isWorkspaceError(result.code)) raiseAlert(result.code, result.detail);
        return;
      }
      setBars(result.bars);
      setChartMeta({ ric: result.ric, interval: result.interval });
      try {
        const cached = await loadOptionsCache({ data: { ric: selected.ric } });
        if (cached.ok && cached.cache?.contracts) setCache(cached.cache);
      } catch {
        /* disk cache is optional */
      }
      setStatus(
        result.bars.length
          ? `${result.bars.length} ${result.interval} bars for ${result.ric}`
          : `No OHLC rows returned for ${result.ric}`,
      );
      setConnected(true);
    } catch (err) {
      const aborted =
        err instanceof Error && (err.name === "AbortError" || /aborted|econnreset/i.test(err.message));
      if (aborted) {
        setStatus("Fetch interrupted — retry. Workspace was still opening a session.");
        return;
      }
      raiseAlert("workspace_unavailable", err instanceof Error ? err.message : String(err));
      setStatus("Fetch failed");
    } finally {
      setFetching(false);
    }
  }

  const selectedLabel = useMemo(() => selected?.ric ?? "None", [selected]);

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-5 px-4 py-6 sm:px-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-4">
        <div>
          <p className="font-mono text-[11px] tracking-[0.28em] text-accent uppercase">
            LSEG desktop · discovery + history
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-fg sm:text-4xl">
            Helios Tape
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "inline-flex h-11 items-center gap-2 rounded-sm border px-3 font-mono text-xs",
              connected
                ? "border-accent-dim text-accent"
                : "border-line text-muted",
            )}
          >
            {connected ? <Wifi className="size-3.5" /> : <WifiOff className="size-3.5" />}
            {connected ? "Workspace" : "No session"}
          </span>
        </div>
      </header>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <div className="flex flex-col gap-4 rounded-lg border border-line bg-surface p-4 sm:p-5">
          <form onSubmit={onSearch} className="flex flex-col gap-2">
            <Label htmlFor="equity-search">Equity search</Label>
            <div className="flex gap-2">
              <Input
                id="equity-search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="AAPL, Tesla, LSEG…"
                autoComplete="off"
              />
              <Button type="submit" disabled={searching || !query.trim()} aria-label="Search">
                {searching ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
              </Button>
            </div>
          </form>

          <div className="flex min-h-48 flex-col">
            <Label>Matching quotes</Label>
            <div
              role="listbox"
              aria-label="Matching equities"
              className="mt-2 max-h-64 overflow-auto rounded-md border border-line bg-bg"
            >
              {hits.length === 0 ? (
                <p className="px-3 py-8 text-center text-sm text-faint">
                  Results from <span className="font-mono text-muted">ld.discovery.search()</span>{" "}
                  appear here.
                </p>
              ) : (
                hits.map((hit) => {
                  const active = selected?.ric === hit.ric;
                  return (
                    <button
                      key={hit.ric}
                      type="button"
                      role="option"
                      aria-selected={active}
                      onClick={() => setSelected(hit)}
                      className={cn(
                        "flex w-full flex-col gap-0.5 border-b border-line px-3 py-2.5 text-left last:border-b-0",
                        active ? "bg-surface-2" : "hover:bg-surface-2/70",
                      )}
                    >
                      <span className="flex items-baseline justify-between gap-2">
                        <span className={cn("font-mono text-sm", active ? "text-accent" : "text-fg")}>
                          {hit.ric}
                        </span>
                        <span className="font-mono text-[11px] text-faint">
                          {hit.exchange || hit.currency}
                        </span>
                      </span>
                      <span className="line-clamp-2 text-xs leading-snug text-muted">{hit.title}</span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="start-date">Start</Label>
              <Input
                id="start-date"
                type="date"
                value={start}
                max={end}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="end-date">End</Label>
              <Input
                id="end-date"
                type="date"
                value={end}
                min={start}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="bar-size">Bar size</Label>
            <select
              id="bar-size"
              value={interval}
              onChange={(e) => setInterval(e.target.value as BarSize)}
              className="h-11 w-full rounded-sm border border-line bg-surface-2 px-3 text-sm text-fg focus-visible:border-accent focus-visible:outline-none"
            >
              {BAR_SIZES.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <Button type="button" onClick={() => void onFetch()} disabled={!selected || fetching}>
            {fetching ? <Loader2 className="size-4 animate-spin" /> : null}
            Fetch {selectedLabel}
          </Button>
          <p className="font-mono text-[11px] leading-relaxed text-faint">{status}</p>
        </div>

        <div className="min-h-[28rem] rounded-lg border border-line bg-surface">
          <CandleChart bars={bars} ric={chartMeta?.ric} interval={chartMeta?.interval} />
        </div>
      </section>

      <OptionsPanel
        selected={selected}
        bars={bars}
        start={start}
        interval={(chartMeta?.interval as BarSize | undefined) ?? interval}
        onWorkspaceError={raiseAlert}
      />

      <WorkspaceAlert
        open={alertOpen}
        onOpenChange={setAlertOpen}
        code={alertCode}
        detail={alertDetail}
      />
    </main>
  );
}
