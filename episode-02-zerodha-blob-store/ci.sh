#!/usr/bin/env bash
# CI for this lab: the starter must fail the check, the sample solution must pass,
# and async acknowledgement must lose writes on kill -9.
set -uo pipefail
cd "$(dirname "$0")"
fail() { echo "CI FAIL: $1"; exit 1; }

echo "== 1. starter config.py should FAIL the check"
python3 lab.py check && fail "starter passed; the exercise is already solved"

echo "== 2. solution/config.py should PASS the check"
tmp=$(mktemp -d)
cp blobstore.py lab.py "$tmp/" && cp solution/config.py "$tmp/config.py"
(cd "$tmp" && python3 lab.py check) || fail "solution did not pass"

echo "== 3. async acknowledgement should lose writes on kill -9"
sed 's/^ASYNC_ACK = False/ASYNC_ACK = True/' config.py > "$tmp/config.py"
out=$(cd "$tmp" && python3 lab.py crash) || fail "crash mode failed"
echo "$out"
lost=$(sed -n 's/.*lost after kill -9: \([0-9,]*\).*/\1/p' <<<"$out" | tr -d ,)
[ "${lost:-0}" -gt 0 ] || fail "async mode lost nothing; the demo didn't reproduce"

echo "CI OK"
