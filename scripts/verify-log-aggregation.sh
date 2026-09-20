#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
TEXT="log-evidence-$(date -u +%Y%m%dT%H%M%SZ)"

response="$(curl -fsS -X POST "${BASE_URL}/api/producer/messages" \
  -H 'Content-Type: application/json' \
  --data "{\"text\":\"${TEXT}\"}")"
message_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"${response}")"

echo "Mensagem publicada: ${message_id}"
echo "Aguardando os eventos published e persisted nos logs..."

for attempt in $(seq 1 15); do
  logs="$(docker compose logs --no-color --since 2m producer-api consumer-api 2>/dev/null || true)"
  if grep -q "event=published message_id=${message_id}" <<<"${logs}" && \
     grep -q "event=persisted message_id=${message_id}" <<<"${logs}"; then
    echo "event=published encontrado no producer-api"
    echo "event=persisted encontrado no consumer-api"
    echo
    echo "Evidência filtrada:"
    grep "message_id=${message_id}" <<<"${logs}"
    exit 0
  fi
  sleep 2
done

echo "Não foi possível encontrar os dois eventos para ${message_id}." >&2
echo "Consulte: docker compose logs --no-color producer-api consumer-api" >&2
exit 1
