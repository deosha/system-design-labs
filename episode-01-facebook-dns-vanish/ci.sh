#!/usr/bin/env bash
# CI for this lab: the broken behaviour must reproduce, the starter must fail
# the check, and the sample solution must pass it.
set -uo pipefail
cd "$(dirname "$0")"

fail() { echo "CI FAIL: $1"; exit 1; }

echo "== 1. withdraw: shop.example should vanish while both servers run"
out=$(python3 vanish.py withdraw) || fail "withdraw mode crashed"
echo "$out"
grep -q "NO ANSWER" <<<"$out" || fail "the outage did not reproduce"

echo "== 2. starter policy.py should FAIL the check"
python3 vanish.py check && fail "starter passed; the exercise is already solved"

echo "== 3. solution/policy.py should PASS the check"
tmp=$(mktemp -d)
cp vanish.py "$tmp/" && cp solution/policy.py "$tmp/policy.py"
(cd "$tmp" && python3 vanish.py check) || fail "solution did not pass"

echo "CI OK"
