#!/usr/bin/env bash
# Apply the newest fintech535-*.patch from ~/Downloads onto this git repo,
# then delete every matching patch in Downloads.
#
# PyCharm: Run → Edit Configurations → Shell Script
#   Script path: apply-fintech-patch.sh
#   Working directory: $ProjectFileDir$  (the 535_fintech repo root)

set -euo pipefail

DOWNLOADS="${FINTECH_PATCH_DIR:-$HOME/Downloads}"
PATTERN="fintech535-*.patch"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Not a git repo. Open the 535_fintech project root in PyCharm and run from there."
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

mapfile -t PATCHES < <(compgen -G "$DOWNLOADS/$PATTERN" | sort || true)
if [[ ${#PATCHES[@]} -eq 0 ]]; then
  echo "No $PATTERN in $DOWNLOADS"
  exit 1
fi

LATEST="$(
  python3 - "$DOWNLOADS" <<'PY'
import re, sys
from pathlib import Path
d = Path(sys.argv[1])
files = list(d.glob("fintech535-*.patch"))
if not files:
    raise SystemExit(1)

def key(p: Path):
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

shopt -s nullglob
REMOVED=("$DOWNLOADS"/$PATTERN)
rm -f "${REMOVED[@]}"
echo
echo "Removed ${#REMOVED[@]} patch file(s) from $DOWNLOADS"
echo "Next: git push   (then tell Grok to sync)"
