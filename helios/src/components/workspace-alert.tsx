import * as AlertDialog from "@radix-ui/react-alert-dialog";
import { MonitorOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { LsegErrorCode } from "@/lib/lseg-types";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  code?: LsegErrorCode | null;
  detail?: string | null;
};

export function WorkspaceAlert({ open, onOpenChange, code, detail }: Props) {
  const missingLib = code === "library_missing";
  return (
    <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className="fixed inset-0 z-50 bg-bg/80" />
        <AlertDialog.Content className="fixed top-1/2 left-1/2 z-50 w-[min(28rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-line bg-surface p-6 shadow-none">
          <div className="mb-4 flex size-11 items-center justify-center rounded-sm border border-line bg-surface-2 text-danger">
            <MonitorOff className="size-5" strokeWidth={1.75} />
          </div>
          <AlertDialog.Title className="font-sans text-lg font-semibold text-fg">
            {missingLib ? "Python LSEG library missing" : "Workspace is not running"}
          </AlertDialog.Title>
          <AlertDialog.Description asChild>
            <div className="mt-2 space-y-3 text-sm leading-relaxed text-muted">
              {missingLib ? (
                <p>
                  Search and fetch run through Python{" "}
                  <span className="font-mono text-accent">lseg-data</span>. Install it, then retry.
                </p>
              ) : (
                <>
                  <p>
                    Helios Tape opens a desktop session against LSEG Workspace and calls{" "}
                    <span className="font-mono text-accent">ld.discovery.search()</span> plus{" "}
                    <span className="font-mono text-accent">ld.get_history()</span>.
                  </p>
                  <p>
                    Start LSEG Workspace on this machine, stay signed in, then search again. This
                    hosted preview cannot see Workspace on your own computer — live pulls only work
                    where Workspace is actually open.
                  </p>
                </>
              )}
              {detail ? (
                <p className="font-mono text-xs break-words text-faint">{detail.slice(0, 280)}</p>
              ) : null}
            </div>
          </AlertDialog.Description>
          <div className="mt-6 flex justify-end">
            <AlertDialog.Action asChild>
              <Button type="button">Got it</Button>
            </AlertDialog.Action>
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
