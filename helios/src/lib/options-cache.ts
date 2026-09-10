import { create } from "zustand";
import type { OptionContract, OptionMiss, OptionsCache } from "./lseg-types";
import { contractKey, lookupOption } from "./lseg-types";

type OptionsStore = {
  cache: OptionsCache | null;
  progress: { done: number; total: number } | null;
  setCache: (cache: OptionsCache | null) => void;
  mergeFetch: (added: OptionContract[], misses: OptionMiss[], meta?: Partial<OptionsCache>) => void;
  setProgress: (progress: { done: number; total: number } | null) => void;
  get: (expiry: string, strike: number) => OptionContract | undefined;
};

export const useOptionsCache = create<OptionsStore>((set, get) => ({
  cache: null,
  progress: null,
  setCache: (cache) => set({ cache }),
  mergeFetch: (added, misses, meta) => {
    const prev = get().cache;
    const contracts = { ...(prev?.contracts ?? {}) };
    for (const rec of added) {
      contracts[rec.key || contractKey(rec.expiry, rec.strike)] = rec;
    }
    const missMap = new Map((prev?.misses ?? []).map((m) => [m.key, m]));
    for (const m of misses) missMap.set(m.key, m);
    for (const rec of added) missMap.delete(rec.key);
    set({
      cache: {
        root: meta?.root ?? prev?.root ?? "",
        underlying: meta?.underlying ?? prev?.underlying,
        high: meta?.high ?? prev?.high,
        low: meta?.low ?? prev?.low,
        strikeMin: meta?.strikeMin ?? prev?.strikeMin,
        strikeMax: meta?.strikeMax ?? prev?.strikeMax,
        strikeStep: meta?.strikeStep ?? prev?.strikeStep,
        expiries: meta?.expiries ?? prev?.expiries,
        updatedAt: new Date().toISOString(),
        contracts,
        misses: [...missMap.values()],
      },
    });
  },
  setProgress: (progress) => set({ progress }),
  get: (expiry, strike) => lookupOption(get().cache, expiry, strike),
}));

export { contractKey, lookupOption };
