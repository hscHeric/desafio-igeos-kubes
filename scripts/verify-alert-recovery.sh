#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-http://localhost:8080}"
alerts_url="${base_url}/alerts/api/v2/alerts"

has_consumer_alert() {
  local expected="$1"
  local alerts
  if ! alerts="$(curl --fail --silent --show-error "$alerts_url")"; then
    return 1
  fi
  python3 -c '
import json
import sys

expected = sys.argv[1]
alerts = json.load(sys.stdin)
raise SystemExit(not any(item.get("labels", {}).get("alertname") == expected for item in alerts))
' "$expected" <<<"$alerts"
}

echo "Stopping consumer-api to trigger the availability alert"
docker compose stop consumer-api
trap 'docker compose start consumer-api >/dev/null' EXIT

for ((attempt = 1; attempt <= 45; attempt++)); do
  if has_consumer_alert ConsumerApiDown; then
    echo "ConsumerApiDown alert is firing"
    break
  fi
  sleep 2
  if (( attempt == 45 )); then
    echo "ConsumerApiDown alert did not fire within 90 seconds" >&2
    exit 1
  fi
done

docker compose start consumer-api >/dev/null
trap - EXIT

for ((attempt = 1; attempt <= 45; attempt++)); do
  if curl --fail --silent --show-error "${base_url}/api/consumer/health/ready" >/dev/null && ! has_consumer_alert ConsumerApiDown; then
    echo "ConsumerApiDown alert recovered"
    exit 0
  fi
  sleep 2
done

echo "ConsumerApiDown alert did not recover within 90 seconds" >&2
exit 1
