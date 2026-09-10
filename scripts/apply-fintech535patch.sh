#!/usr/bin/env bash
# Apply the newest fintech535-*.patch from ~/Downloads onto this git repo,
# then delete every matching patch in Downloads.
#
# PyCharm: Run → Edit Configurations → Shell Script
#   Script path: scripts/apply-fintech535patch.sh
#   Working directory: $ProjectFileDir$  (the 535_fintech repo root)
#
# This patch stream is for a clone of github.com/JakeVestal/535_fintech.
# It adds files under helios/. Do not run it on the unzipped Grok app
# (src/ + python/ at the repo root, AGENTS.md, etc.).
#
# macOS /bin/bash is 3.2 — no mapfile.

set -euo pipefail

DOWNLOADS="${FINTECH_PATCH_DIR:-$HOME/Downloads}"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Not a git repo. Open the 535_fintech GitHub clone in PyCharm."
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [[ -f AGENTS.md && -f src/routes/data.tsx && ! -d helios && ! -d fintech535 ]]; then
  echo "This looks like the unzipped Helios zip (files at repo root), not the GitHub course clone."
  echo "Clone https://github.com/JakeVestal/535_fintech.git into a new folder and run the script there."
  exit 1
fi

if ! git diff --quiet --cached || ! git diff --quiet; then
  echo "Working tree is dirty — git am refuses to run."
  echo
  echo "This repo must be a CLEAN clone of JakeVestal/535_fintech (Reflex on main)."
  echo "Patches create helios/; they do not overlay src/ at the root."
  echo
  echo "Safe path:"
  echo "  cd ~/Desktop"
  echo "  git clone https://github.com/JakeVestal/535_fintech.git 535_fintech_git"
  echo "  # PyCharm: open 535_fintech_git, script = scripts/apply-fintech535patch.sh"
  echo
  echo "Do NOT git reset --hard unless you mean to throw away the zip overlay."
  echo
  git status -sb | head -n 40
  exit 1
fi

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
