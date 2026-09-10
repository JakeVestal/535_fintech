import type {
  HealthResult,
  HistoryResult,
  OptionsCacheResult,
  OptionsFetchResult,
  OptionsPlanResult,
  SearchResult,
} from "./lseg-types";

async function callLseg<T>(payload: Record<string, unknown>, timeoutMs: number): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch("/api/lseg", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    return (await res.json()) as T;
  } catch (error) {
    const aborted =
      error instanceof Error &&
      (error.name === "AbortError" || /aborted|econnreset/i.test(error.message));
    return {
      ok: false,
      code: aborted ? "upstream" : "upstream",
      message: aborted
        ? "Request timed out. Try hourly bars or a shorter window."
        : error instanceof Error
          ? error.message
          : String(error),
    } as T;
  } finally {
    clearTimeout(timer);
  }
}

export async function probeWorkspace() {
  return await callLseg<HealthResult>({ op: "health" }, 8000);
}

export async function searchEquities({ data }: { data: { query: string } }) {
  return await callLseg<SearchResult>({ op: "search", query: data.query }, 30000);
}

export async function fetchHistory({
  data,
}: {
  data: { ric: string; start: string; end: string; interval: string };
}) {
  return await callLseg<HistoryResult>(
    { op: "history", ric: data.ric, start: data.start, end: data.end, interval: data.interval },
    180000,
  );
}

export async function planOptions({
  data,
}: {
  data: { ric: string; bars: unknown[]; extraWeeks?: number };
}) {
  return await callLseg<OptionsPlanResult>(
    { op: "options_plan", ric: data.ric, bars: data.bars, extraWeeks: data.extraWeeks ?? 5 },
    20000,
  );
}

export async function fetchOptionsBatch({
  data,
}: {
  data: Record<string, unknown>;
}) {
  return await callLseg<OptionsFetchResult>({ op: "options_fetch", ...data }, 180000);
}

export async function loadOptionsCache({ data }: { data: { ric: string } }) {
  return await callLseg<OptionsCacheResult>({ op: "options_cache", ric: data.ric }, 10000);
}
