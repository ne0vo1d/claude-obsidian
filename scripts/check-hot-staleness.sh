#!/usr/bin/env bash
# check-hot-staleness.sh — warn when wiki/hot.md has drifted behind the repo.
#
# The hot cache is the vault's session-to-session memory. When work continues
# (commits land) but hot.md's `updated:` timestamp doesn't move, every new
# session starts from a stale picture — the exact failure observed 2026-07-05,
# when hot.md sat 7 weeks / 5 minor versions behind HEAD.
#
# Compares the `updated:` frontmatter field of wiki/hot.md against the most
# recent git commit date. If the last commit is more than MAX_DAYS newer than
# hot.md, prints a HOT_CACHE_STALE warning for the session context.
#
# Usage:
#   bash scripts/check-hot-staleness.sh [--max-days N]   # default 7
#
# Designed for hooks: ALWAYS exits 0; silent unless stale; every failure
# path (no hot.md, no git, unparseable date) degrades to silence, never to
# a broken session start. Bash 3.2 compatible (macOS system bash).

set -u

MAX_DAYS=7
if [ "${1:-}" = "--max-days" ] && [ -n "${2:-}" ]; then
  MAX_DAYS="$2"
fi

HOT="wiki/hot.md"
[ -f "$HOT" ] || exit 0
command -v git >/dev/null 2>&1 || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

# Last commit epoch (any file — "the repo moved on"). The case guard keeps
# the "always silent on failure" contract even if git's output shape changes:
# non-numeric → silent exit rather than a shell arithmetic error below.
LAST_COMMIT_EPOCH=$(git log -1 --format=%ct 2>/dev/null) || exit 0
case "$LAST_COMMIT_EPOCH" in
  ''|*[!0-9]*) exit 0 ;;
esac

# hot.md `updated:` → epoch. python3 does the ISO parsing; any parse
# failure prints nothing and we exit silently.
HOT_EPOCH=$(python3 - "$HOT" <<'PY' 2>/dev/null
import re, sys
from datetime import datetime, timezone
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
m = re.search(r"^updated:\s*[\"']?([0-9T:\-\. ]+)", text, re.M)
if not m:
    sys.exit(1)
raw = m.group(1).strip()
for candidate in (raw, raw[:19], raw[:10]):
    try:
        dt = datetime.fromisoformat(candidate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        print(int(dt.timestamp()))
        sys.exit(0)
    except ValueError:
        continue
sys.exit(1)
PY
) || exit 0
[ -n "$HOT_EPOCH" ] || exit 0

DRIFT_SECS=$((LAST_COMMIT_EPOCH - HOT_EPOCH))
MAX_SECS=$((MAX_DAYS * 86400))

if [ "$DRIFT_SECS" -gt "$MAX_SECS" ]; then
  DRIFT_DAYS=$((DRIFT_SECS / 86400))
  echo "HOT_CACHE_STALE: wiki/hot.md was last updated ${DRIFT_DAYS} day(s) before the latest commit. Its 'recent context' is out of date — reconcile it against git log / CHANGELOG before trusting it, then rewrite hot.md."
fi

exit 0
