import { Link, useRouterState } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

const LINKS = [
  { to: "/", label: "Blotter" },
  { to: "/data", label: "Data" },
] as const;

export function SiteNav() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <header className="border-b border-line bg-bg/95">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-baseline gap-2">
          <span className="font-mono text-xs tracking-[0.28em] text-accent uppercase">Helios</span>
          <span className="text-lg font-semibold text-fg">Tape</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-1">
          {LINKS.map((l) => {
            const active = pathname === l.to;
            return (
              <Link
                key={l.to}
                to={l.to}
                className={cn(
                  "inline-flex h-11 items-center rounded-sm px-2.5 font-mono text-xs tracking-wide uppercase sm:px-3",
                  active ? "border border-accent-dim text-accent" : "text-muted hover:text-fg",
                )}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
