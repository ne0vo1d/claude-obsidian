#!/usr/bin/env bash
# test_hot_staleness.sh — unit tests for scripts/check-hot-staleness.sh.
#
# Hermetic: creates a throwaway git repo + vault under mktemp, no network.
# Covers:
#   - stale hot.md (updated: far behind last commit) → HOT_CACHE_STALE warning
#   - fresh hot.md (updated: at/after last commit)   → silence
#   - --max-days override widens/narrows the window
#   - missing hot.md / no git repo / unparseable date → silence, exit 0
#
# Usage: bash tests/test_hot_staleness.sh

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK_SH="$ROOT/scripts/check-hot-staleness.sh"

PASS=0
FAIL=0

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "OK   $label"
    PASS=$((PASS + 1))
  else
    echo "FAIL $label: expected '$expected', got '$actual'"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  if printf '%s' "$haystack" | grep -q "$needle"; then
    echo "OK   $label"
    PASS=$((PASS + 1))
  else
    echo "FAIL $label: '$needle' not found in output: '$haystack'"
    FAIL=$((FAIL + 1))
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

make_vault() {
  # $1 = hot.md `updated:` value (empty = omit field entirely)
  local updated="$1" dir="$TMP/vault-$RANDOM"
  mkdir -p "$dir/wiki"
  (
    cd "$dir"
    git init -q
    git config user.email test@example.com
    git config user.name test
    if [ -n "$updated" ]; then
      printf -- '---\ntype: meta\nupdated: %s\n---\n# Hot\n' "$updated" > wiki/hot.md
    else
      printf -- '---\ntype: meta\n---\n# Hot\n' > wiki/hot.md
    fi
    git add -A
    git commit -qm "seed"
  )
  echo "$dir"
}

# 1. Stale: hot.md dated 30 days before the commit (which is "now").
OLD_DATE=$(python3 -c "from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)-timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S'))")
V=$(make_vault "$OLD_DATE")
OUT=$(cd "$V" && bash "$CHECK_SH")
RC=$?
assert_eq "stale exit code" 0 "$RC"
assert_contains "stale warning emitted" "HOT_CACHE_STALE" "$OUT"

# 2. Fresh: hot.md dated now → silence.
NOW_DATE=$(python3 -c "from datetime import datetime,timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'))")
V=$(make_vault "$NOW_DATE")
OUT=$(cd "$V" && bash "$CHECK_SH")
assert_eq "fresh is silent" "" "$OUT"

# 3. --max-days override: 30-day drift is fine under a 60-day window…
V=$(make_vault "$OLD_DATE")
OUT=$(cd "$V" && bash "$CHECK_SH" --max-days 60)
assert_eq "wide window silent" "" "$OUT"
# …and a 1-day window flags a 3-day drift.
THREE_DAYS=$(python3 -c "from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)-timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%S'))")
V=$(make_vault "$THREE_DAYS")
OUT=$(cd "$V" && bash "$CHECK_SH" --max-days 1)
assert_contains "narrow window flags" "HOT_CACHE_STALE" "$OUT"

# 4. Degradation paths: all silent, all exit 0.
V=$(make_vault "$OLD_DATE"); rm "$V/wiki/hot.md"
OUT=$(cd "$V" && bash "$CHECK_SH"); RC=$?
assert_eq "missing hot.md silent" "" "$OUT"
assert_eq "missing hot.md exit 0" 0 "$RC"

NOGIT="$TMP/nogit"; mkdir -p "$NOGIT/wiki"
printf -- '---\nupdated: %s\n---\n' "$OLD_DATE" > "$NOGIT/wiki/hot.md"
OUT=$(cd "$NOGIT" && bash "$CHECK_SH"); RC=$?
assert_eq "no git repo silent" "" "$OUT"
assert_eq "no git repo exit 0" 0 "$RC"

V=$(make_vault "not-a-date")
OUT=$(cd "$V" && bash "$CHECK_SH"); RC=$?
assert_eq "unparseable date silent" "" "$OUT"
assert_eq "unparseable date exit 0" 0 "$RC"

V=$(make_vault "")
OUT=$(cd "$V" && bash "$CHECK_SH"); RC=$?
assert_eq "missing updated field silent" "" "$OUT"
assert_eq "missing updated field exit 0" 0 "$RC"

echo ""
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && echo "ALL PASS test_hot_staleness.sh" || exit 1
