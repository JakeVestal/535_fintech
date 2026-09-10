import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-11 w-full rounded-sm border border-line bg-surface-2 px-3 text-sm text-fg placeholder:text-faint",
        "transition-colors duration-150 focus-visible:border-accent focus-visible:outline-none",
        className,
      )}
      {...props}
    />
  );
}
