#!/usr/bin/env bash
# Apply the newest fintech535-*.patch from ~/Downloads onto this git repo,
# then delete every matching patch in Downloads.
#
# PyCharm: Run → Edit Configurations → Shell Script
#   Script path: scripts/apply-fintech535patch.sh
#   Working directory: $ProjectFileDir$  (the 535_fintech repo root)
#
# macOS /bin/bash is 3.2 — keep this script free of mapfile/associative arrays.

set -euo pipefail

DOWNLOADS="${FINTECH_PATCH_DIR:-$HOME/Downloads}"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Not a git repo. Open the 535_fintech project root in PyCharm and run from there."
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

LATEST="$(
  FINTECH_PATCH_DIR="$DOWNLOADS" python3 - <<'PY'
import os, re, sys
from pathlib import Path

d = Path(os.environ.get("FINTECH_PATCH_DIR") or Path.home() / "Downloads")
files = list(d.glob("fintech535-*.patch"))
if not files:
    sys.stderr.write("No fintech535-*.patch in %s\n" % d)
    sys.exit(1)

def key(p):
    m = re.search(r"-(\d+)\.patch$", p.name)
    n = int(m.group(1)) if m else -1
    return (n, p.stat().st_mtime)

print(max(files, key=key))
PY
)"

echo "Repo:    $ROOT"
echo "Apply:   $LATEST"
echo "Commit:  $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"

if head -n 1 "$LATEST" | grep -q '^From '; then
  git am --3way --keep-cr "$LATEST"
else
  git apply --index --whitespace=nowarn "$LATEST"
  git commit -am "Apply $(basename "$LATEST")"
fi

echo
echo "Applied. Status:"
git status -sb

FINTECH_PATCH_DIR="$DOWNLOADS" python3 - <<'PY'
import os
from pathlib import Path
d = Path(os.environ["FINTECH_PATCH_DIR"])
gone = list(d.glob("fintech535-*.patch"))
for p in gone:
    p.unlink()
print("Removed %d patch file(s) from %s" % (len(gone), d))
PY

echo "Next: git push   (then tell Grok to sync)"
