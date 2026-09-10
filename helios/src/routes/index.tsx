import { createFileRoute, Link } from "@tanstack/react-router";
import { NavChart } from "@/components/nav-chart";
import {
  INIT_PCT,
  MAINT_PCT,
  SAMPLE_BLOTTER,
  SAMPLE_LAST,
  SAMPLE_LEDGER,
  SAMPLE_START_CASH,
  SAMPLE_UNDERLYING,
} from "@/lib/sample-book";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({ component: BlotterHome });

function money(n: number, digits = 2): string {
  const sign = n < 0 ? "−" : "";
  return `${sign}$${Math.abs(n).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

function BlotterHome() {
  const last = SAMPLE_LAST;
  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-5 px-4 py-6 sm:px-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-4">
        <div>
          <p className="font-mono text-xs tracking-[0.28em] text-accent uppercase">
            Sample book · not a live backtest
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-fg sm:text-4xl">
            Covered-call blotter
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">
            A filled-in example of the book you will keep: every fill you actually did (blotter),
            the running position (ledger), and the Reg T accounts that decide whether you can
            write the next ~5 DTE call. Replace these rows with your own tape after{" "}
            <Link to="/data" className="text-accent">
              Data
            </Link>
            .
          </p>
        </div>
        <span className="inline-flex h-11 items-center rounded-sm border border-accent-dim px-3 font-mono text-xs text-accent">
          SAMPLE · {SAMPLE_UNDERLYING} · start {money(SAMPLE_START_CASH, 0)}
        </span>
      </header>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Account k="Cash" v={money(last.cash)} hint="Settled dollars after fills" />
        <Account k="Stock LMV" v={money(last.lmv)} hint={`${last.shares} ${SAMPLE_UNDERLYING} @ ${last.stockPx.toFixed(2)}`} />
        <Account k="Short option" v={money(last.optMv)} hint={last.callLabel} down={last.optMv < 0} />
        <Account k="NAV / equity" v={money(last.nav)} hint="cash + LMV + option MV" accent />
        <Account
          k="Initial margin"
          v={money(last.init)}
          hint={`Reg T ${INIT_PCT * 100}% of LMV · covered call adds $0`}
        />
        <Account
          k="Maintenance"
          v={money(last.maint)}
          hint={`FINRA ${MAINT_PCT * 100}% of LMV`}
        />
        <Account
          k="Available funds"
          v={money(last.available)}
          hint="NAV − initial. Room for a new risk."
        />
        <Account
          k="Excess equity"
          v={money(last.excess)}
          hint="NAV − maintenance. Margin-call line."
        />
      </section>

      <section className="min-h-72 rounded-lg border border-line bg-surface">
        <NavChart rows={SAMPLE_LEDGER} />
      </section>

      <section className="rounded-lg border border-line bg-surface p-4 sm:p-5">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="font-mono text-xs tracking-widest text-accent uppercase">Blotter</p>
            <h2 className="text-lg font-semibold text-fg">Trades you actually made</h2>
          </div>
          <p className="max-w-lg text-sm text-muted">
            Buy 100 shares, write one call. Rolls are a buy-to-close plus a new sell. Expires print
            at 0. Working orders do not belong here.
          </p>
        </div>
        <div className="overflow-auto rounded-md border border-line">
          <table className="w-full min-w-[52rem] text-left text-xs">
            <thead className="bg-surface-2 font-mono text-xs text-faint">
              <tr>
                <th className="px-3 py-2">Time</th>
                <th className="px-3 py-2">Side</th>
                <th className="px-3 py-2">Qty</th>
                <th className="px-3 py-2">Instrument</th>
                <th className="px-3 py-2">Px</th>
                <th className="px-3 py-2">Cash Δ</th>
                <th className="px-3 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLE_BLOTTER.map((t) => {
                const dir = t.side === "BUY" || t.side === "BTC" ? -1 : 1;
                const delta = dir * t.qty * t.price * t.multiplier;
                return (
                  <tr key={t.id} className="border-t border-line">
                    <td className="px-3 py-1.5 font-mono text-muted whitespace-nowrap">{t.ts}</td>
                    <td
                      className={cn(
                        "px-3 py-1.5 font-mono",
                        t.side === "SELL" ? "text-accent" : t.side === "EXPIRE" ? "text-faint" : "text-down",
                      )}
                    >
                      {t.side}
                    </td>
                    <td className="px-3 py-1.5 font-mono tabular-nums text-fg">{t.qty}</td>
                    <td className="px-3 py-1.5 font-mono text-fg">{t.instrument}</td>
                    <td className="px-3 py-1.5 font-mono tabular-nums text-fg">{t.price.toFixed(2)}</td>
                    <td
                      className={cn(
                        "px-3 py-1.5 font-mono tabular-nums",
                        delta >= 0 ? "text-accent" : "text-down",
                      )}
                    >
                      {money(delta)}
                    </td>
                    <td className="px-3 py-1.5 text-muted">{t.notes}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg border border-line bg-surface p-4 sm:p-5">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="font-mono text-xs tracking-widest text-accent uppercase">Ledger</p>
            <h2 className="text-lg font-semibold text-fg">Position, cash, and margin over time</h2>
          </div>
          <p className="max-w-lg text-sm text-muted">
            Marks at week-ends. Short calls are a negative market value. Covered-call initial is
            50% of stock LMV; the short call does not add naked-option margin.
          </p>
        </div>
        <div className="overflow-auto rounded-md border border-line">
          <table className="w-full min-w-[64rem] text-left text-xs">
            <thead className="bg-surface-2 font-mono text-xs text-faint">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Cash</th>
                <th className="px-3 py-2">Shares</th>
                <th className="px-3 py-2">Short call</th>
                <th className="px-3 py-2">Spot</th>
                <th className="px-3 py-2">LMV</th>
                <th className="px-3 py-2">Opt MV</th>
                <th className="px-3 py-2">NAV</th>
                <th className="px-3 py-2">Initial</th>
                <th className="px-3 py-2">Maint</th>
                <th className="px-3 py-2">Available</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLE_LEDGER.map((r) => (
                <tr key={r.date} className="border-t border-line">
                  <td className="px-3 py-1.5 font-mono text-muted">{r.date}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-fg">{money(r.cash)}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-fg">{r.shares}</td>
                  <td className="px-3 py-1.5 font-mono text-accent">
                    {r.shortCalls ? `${r.shortCalls} ${r.callLabel}` : "flat"}
                  </td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-fg">{r.stockPx.toFixed(2)}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-fg">{money(r.lmv)}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-muted">{money(r.optMv)}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-accent">{money(r.nav)}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-muted">{money(r.init)}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-muted">{money(r.maint)}</td>
                  <td className="px-3 py-1.5 font-mono tabular-nums text-fg">{money(r.available)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function Account({
  k,
  v,
  hint,
  accent,
  down,
}: {
  k: string;
  v: string;
  hint: string;
  accent?: boolean;
  down?: boolean;
}) {
  return (
    <div className="rounded-lg border border-line bg-surface px-4 py-3">
      <p className="font-mono text-xs text-faint">{k}</p>
      <p
        className={cn(
          "mt-1 font-mono text-xl tabular-nums",
          accent ? "text-accent" : down ? "text-down" : "text-fg",
        )}
      >
        {v}
      </p>
      <p className="mt-1 text-xs leading-snug text-muted">{hint}</p>
    </div>
  );
}
