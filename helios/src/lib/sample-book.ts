/** Sample covered-call book — template numbers, not a live backtest. */

export type BlotterRow = {
  id: string;
  ts: string;
  side: "BUY" | "SELL" | "BTC" | "EXPIRE";
  qty: number;
  instrument: string;
  asset: "STK" | "CALL";
  strike: number | null;
  expiry: string | null;
  price: number;
  multiplier: number;
  notes: string;
};

export type LedgerRow = {
  date: string;
  cash: number;
  shares: number;
  shortCalls: number;
  callLabel: string;
  stockPx: number;
  optPx: number;
  lmv: number;
  optMv: number;
  nav: number;
  init: number;
  maint: number;
  available: number;
  excess: number;
};

export const SAMPLE_START_CASH = 5000;
export const SAMPLE_UNDERLYING = "UUUU";
export const INIT_PCT = 0.5;
export const MAINT_PCT = 0.25;

export const SAMPLE_BLOTTER: BlotterRow[] = [
  {
    id: "t1",
    ts: "2026-06-30 09:44",
    side: "BUY",
    qty: 100,
    instrument: "UUUU",
    asset: "STK",
    strike: null,
    expiry: null,
    price: 12.9,
    multiplier: 1,
    notes: "Open the long. One covered call = 100 shares.",
  },
  {
    id: "t2",
    ts: "2026-06-30 09:51",
    side: "SELL",
    qty: 1,
    instrument: "UUUU 7/3 13.5 C",
    asset: "CALL",
    strike: 13.5,
    expiry: "2026-07-03",
    price: 0.22,
    multiplier: 100,
    notes: "Write ~5 DTE, slightly OTM. Premium to cash.",
  },
  {
    id: "t3",
    ts: "2026-07-03 16:00",
    side: "EXPIRE",
    qty: 1,
    instrument: "UUUU 7/3 13.5 C",
    asset: "CALL",
    strike: 13.5,
    expiry: "2026-07-03",
    price: 0,
    multiplier: 100,
    notes: "Expires OTM. Short call off the sheet; keep the 0.22.",
  },
  {
    id: "t4",
    ts: "2026-07-06 09:40",
    side: "SELL",
    qty: 1,
    instrument: "UUUU 7/10 13.5 C",
    asset: "CALL",
    strike: 13.5,
    expiry: "2026-07-10",
    price: 0.19,
    multiplier: 100,
    notes: "Rewrite the next weekly.",
  },
  {
    id: "t5",
    ts: "2026-07-10 15:48",
    side: "BTC",
    qty: 1,
    instrument: "UUUU 7/10 13.5 C",
    asset: "CALL",
    strike: 13.5,
    expiry: "2026-07-10",
    price: 0.06,
    multiplier: 100,
    notes: "Buy to close before the print. Roll rather than pin.",
  },
  {
    id: "t6",
    ts: "2026-07-10 15:49",
    side: "SELL",
    qty: 1,
    instrument: "UUUU 7/17 14.0 C",
    asset: "CALL",
    strike: 14,
    expiry: "2026-07-17",
    price: 0.21,
    multiplier: 100,
    notes: "Roll out and up. New ~5 DTE.",
  },
  {
    id: "t7",
    ts: "2026-07-17 16:00",
    side: "EXPIRE",
    qty: 1,
    instrument: "UUUU 7/17 14.0 C",
    asset: "CALL",
    strike: 14,
    expiry: "2026-07-17",
    price: 0,
    multiplier: 100,
    notes: "OTM expire. Another week of premium kept.",
  },
  {
    id: "t8",
    ts: "2026-07-20 10:12",
    side: "SELL",
    qty: 1,
    instrument: "UUUU 7/24 14.0 C",
    asset: "CALL",
    strike: 14,
    expiry: "2026-07-24",
    price: 0.24,
    multiplier: 100,
    notes: "Rewrite 14s.",
  },
  {
    id: "t9",
    ts: "2026-07-24 14:05",
    side: "BTC",
    qty: 1,
    instrument: "UUUU 7/24 14.0 C",
    asset: "CALL",
    strike: 14,
    expiry: "2026-07-24",
    price: 0.48,
    multiplier: 100,
    notes: "Stock through the strike. Close to dodge assignment / pin.",
  },
  {
    id: "t10",
    ts: "2026-07-24 14:06",
    side: "SELL",
    qty: 1,
    instrument: "UUUU 7/31 15.0 C",
    asset: "CALL",
    strike: 15,
    expiry: "2026-07-31",
    price: 0.18,
    multiplier: 100,
    notes: "Roll up. Give the shares room.",
  },
  {
    id: "t11",
    ts: "2026-07-31 16:00",
    side: "EXPIRE",
    qty: 1,
    instrument: "UUUU 7/31 15.0 C",
    asset: "CALL",
    strike: 15,
    expiry: "2026-07-31",
    price: 0,
    multiplier: 100,
    notes: "OTM expire.",
  },
  {
    id: "t12",
    ts: "2026-08-03 09:55",
    side: "SELL",
    qty: 1,
    instrument: "UUUU 8/7 15.0 C",
    asset: "CALL",
    strike: 15,
    expiry: "2026-08-07",
    price: 0.27,
    multiplier: 100,
    notes: "Still long 100. Write the next weekly.",
  },
];

/** Marks used to value the book (sample path, not LSEG). */
const MARKS: { date: string; stock: number; opt: number; callLabel: string; short: number }[] = [
  { date: "2026-06-30", stock: 12.9, opt: 0.22, callLabel: "7/3 13.5C", short: -1 },
  { date: "2026-07-03", stock: 12.72, opt: 0, callLabel: "—", short: 0 },
  { date: "2026-07-06", stock: 13.05, opt: 0.19, callLabel: "7/10 13.5C", short: -1 },
  { date: "2026-07-10", stock: 13.28, opt: 0.21, callLabel: "7/17 14.0C", short: -1 },
  { date: "2026-07-17", stock: 13.41, opt: 0, callLabel: "—", short: 0 },
  { date: "2026-07-20", stock: 13.88, opt: 0.24, callLabel: "7/24 14.0C", short: -1 },
  { date: "2026-07-24", stock: 14.62, opt: 0.18, callLabel: "7/31 15.0C", short: -1 },
  { date: "2026-07-31", stock: 14.2, opt: 0, callLabel: "—", short: 0 },
  { date: "2026-08-03", stock: 14.55, opt: 0.27, callLabel: "8/7 15.0C", short: -1 },
  { date: "2026-08-07", stock: 14.71, opt: 0.11, callLabel: "8/7 15.0C", short: -1 },
];

function cashAfter(ts: string): number {
  let cash = SAMPLE_START_CASH;
  for (const t of SAMPLE_BLOTTER) {
    if (t.ts.slice(0, 10) > ts) break;
    const signed =
      t.side === "BUY" || t.side === "BTC" ? -1 : t.side === "SELL" || t.side === "EXPIRE" ? 1 : 0;
    cash += signed * t.qty * t.price * t.multiplier;
  }
  return cash;
}

export const SAMPLE_LEDGER: LedgerRow[] = MARKS.map((m) => {
  const cash = cashAfter(m.date);
  const shares = 100;
  const lmv = shares * m.stock;
  const optMv = m.short * m.opt * 100;
  const nav = cash + lmv + optMv;
  const init = INIT_PCT * lmv;
  const maint = MAINT_PCT * lmv;
  return {
    date: m.date,
    cash,
    shares,
    shortCalls: m.short,
    callLabel: m.callLabel,
    stockPx: m.stock,
    optPx: m.opt,
    lmv,
    optMv,
    nav,
    init,
    maint,
    available: nav - init,
    excess: nav - maint,
  };
});

export const SAMPLE_LAST = SAMPLE_LEDGER[SAMPLE_LEDGER.length - 1];
