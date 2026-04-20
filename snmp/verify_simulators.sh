#!/usr/bin/env bash
# From the agent container, SNMP-walk each lab device IP with community mocksnmp (same as NDM autodiscovery).
set -euo pipefail
AGENT="${1:-datadog-agent}"
IPS=(
  172.20.0.10
  172.20.0.11
  172.20.0.12
  172.20.0.13
  172.20.0.14
  172.20.0.15
  172.20.0.16
  172.20.0.17
  172.20.0.18
  172.20.0.19
  172.20.0.20
  172.20.0.21
)
if ! docker ps --format '{{.Names}}' | grep -qx "$AGENT"; then
  echo "Container '$AGENT' is not running. Start the stack: docker compose up -d" >&2
  exit 1
fi
ok=0
fail=0
for ip in "${IPS[@]}"; do
  if out=$(docker exec "$AGENT" agent snmp walk "$ip" -C mocksnmp -v 2c -t 3 1.3.6.1.2.1.1.1.0 2>&1); then
    if echo "$out" | grep -q 'STRING:'; then
      echo "OK  $ip  ${out//$'\n'/ }"
      ok=$((ok + 1))
    else
      echo "BAD $ip  (unexpected output)"
      echo "$out"
      fail=$((fail + 1))
    fi
  else
    echo "BAD $ip"
    echo "$out"
    fail=$((fail + 1))
  fi
done
echo "---"
echo "Passed: $ok / ${#IPS[@]}"
exit $((fail > 0 ? 1 : 0))
