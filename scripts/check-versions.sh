#!/bin/sh
# Verify plugin.json and both marketplace.json files agree on the version.
ROOT=$(cd "$(dirname "$0")/.." && pwd)

get() {
  python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."):
    d = d[int(k)] if k.isdigit() else d[k]
print(d)
' "$ROOT/$1" "$2"
}

canon_file=plugin/.claude-plugin/plugin.json
canon=$(get "$canon_file" version) || { echo "error: cannot read version from $canon_file" >&2; exit 2; }
status=0

check() {
  v=$(get "$1" "$2") || { echo "error: cannot read $2 in $1" >&2; status=1; return; }
  echo "$1 [$2] = $v"
  if [ "$v" != "$canon" ]; then
    echo "MISMATCH: $1 [$2] is $v but $canon_file [version] is $canon" >&2
    status=1
  fi
}

echo "$canon_file [version] = $canon"
check .claude-plugin/marketplace.json plugins.0.version
check plugin/.claude-plugin/marketplace.json metadata.version
check plugin/.claude-plugin/marketplace.json plugins.0.version
exit $status
