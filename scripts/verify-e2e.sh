#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-http://localhost:8080}"
message="ci-message-$(date +%s)-${RANDOM}"

wait_for() {
  local url="$1"
  local attempts=60

  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if curl --fail --silent --show-error "$url" >/dev/null; then
      return 0
    fi
    sleep 2
  done

  echo "Timed out waiting for ${url}" >&2
  return 1
}

echo "Waiting for Nginx routes and API readiness"
wait_for "${base_url}/producer/"
wait_for "${base_url}/consumer/"
wait_for "${base_url}/api/producer/health/ready"
wait_for "${base_url}/api/consumer/health/ready"

echo "Publishing ${message}"
status="$(
  curl --silent --show-error --output /tmp/producer-response.json --write-out '%{http_code}' \
    --request POST "${base_url}/api/producer/messages" \
    --header 'Content-Type: application/json' \
    --data "{\"text\":\"${message}\"}"
)"

if [[ "$status" != "202" ]]; then
  echo "Expected producer to return 202; received ${status}" >&2
  cat /tmp/producer-response.json >&2
  exit 1
fi

echo "Waiting for the consumer to persist the message"
for ((attempt = 1; attempt <= 30; attempt++)); do
  history="$(curl --fail --silent --show-error "${base_url}/api/consumer/messages")"
  if python3 -c '
import json
import sys

message = sys.argv[1]
messages = json.load(sys.stdin)["messages"]
raise SystemExit(not any(item["text"] == message for item in messages))
' "$message" <<<"$history"; then
    echo "End-to-end flow verified"
    exit 0
  fi
  sleep 2
done

echo "Published message was not persisted within 60 seconds" >&2
exit 1
