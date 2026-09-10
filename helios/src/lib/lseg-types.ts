export const BAR_SIZES = [
  { value: "1min", label: "1 min" },
  { value: "5min", label: "5 min" },
  { value: "10min", label: "10 min" },
  { value: "30min", label: "30 min" },
  { value: "hourly", label: "Hourly" },
  { value: "daily", label: "Daily" },
] as const;

export type BarSize = (typeof BAR_SIZES)[number]["value"];

export type EquityHit = {
  ric: string;
  title: string;
  ticker: string;
  exchange: string;
  issuer: string;
  assetType: string;
  currency: string;
};

export type OhlcBar = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type LsegErrorCode =
  | "workspace_unavailable"
  | "library_missing"
  | "bad_request"
  | "upstream";

export type LsegOk<T> = { ok: true } & T;
export type LsegErr = {
  ok: false;
  code: LsegErrorCode;
  message: string;
  detail?: string | null;
};

export type HealthResult = LsegOk<{ workspace: boolean; proxy: boolean }> | LsegErr;
export type SearchResult = LsegOk<{ query: string; hits: EquityHit[] }> | LsegErr;
export type HistoryResult =
  | LsegOk<{
      ric: string;
      interval: string;
      start: string;
      end: string;
      bars: OhlcBar[];
    }>
  | LsegErr;

export function isWorkspaceError(code: string | undefined): boolean {
  return code === "workspace_unavailable" || code === "library_missing";
}

export type OptionQuote = {
  time: string;
  trade: number | null;
  bid: number | null;
  ask: number | null;
};

export type OptionCandidate = {
  ric: string;
  strike: number;
  expiry: string;
  expired: boolean;
  key: string;
};

export type OptionContract = OptionCandidate & {
  barCount?: number;
  bars: OptionQuote[];
};

export type OptionMiss = {
  ric: string;
  strike: number;
  expiry: string;
  key: string;
  reason: string;
};

export type OptionsPlan = {
  underlying: string;
  root: string;
  high: number;
  low: number;
  strikeMin: number;
  strikeMax: number;
  strikeStep: number;
  expiries: string[];
  candidates: OptionCandidate[];
  candidateCount: number;
};

export type OptionsCache = {
  root: string;
  underlying?: string;
  high?: number;
  low?: number;
  strikeMin?: number;
  strikeMax?: number;
  strikeStep?: number;
  expiries?: string[];
  updatedAt?: string;
  contracts: Record<string, OptionContract>;
  misses: OptionMiss[];
};

export type OptionsPlanResult = LsegOk<OptionsPlan> | LsegErr;
export type OptionsFetchResult =
  | LsegOk<{
      root: string;
      underlying: string;
      path?: string;
      added: OptionContract[];
      misses: OptionMiss[];
      addedCount: number;
      missCount: number;
      contractCount: number;
    }>
  | LsegErr;
export type OptionsCacheResult = LsegOk<{ root: string; cache: OptionsCache }> | LsegErr;

export function contractKey(expiry: string, strike: number): string {
  return `${expiry}|${strike.toFixed(2)}`;
}

export function lookupOption(
  cache: OptionsCache | null | undefined,
  expiry: string,
  strike: number,
): OptionContract | undefined {
  if (!cache) return undefined;
  return cache.contracts[contractKey(expiry, strike)];
}
