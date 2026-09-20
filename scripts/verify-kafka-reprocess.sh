#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-http://localhost:8080}"
topic="${KAFKA_TOPIC:-messages}"
group="${KAFKA_GROUP_ID:-message-store}"
message="kafka-reprocess-$(date -u +%Y%m%dT%H%M%SZ)-${RANDOM}"

restart_consumer() {
  docker compose start consumer-api >/dev/null 2>&1 || true
}
trap restart_consumer EXIT

echo "Parando o consumidor para criar um evento pendente"
docker compose stop consumer-api >/dev/null

response="$(curl -fsS -X POST "${base_url}/api/producer/messages" \
  -H 'Content-Type: application/json' \
  --data "{\"text\":\"${message}\"}")"
message_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"${response}")"
echo "Mensagem pendente: ${message_id}"

docker compose start consumer-api >/dev/null

for attempt in $(seq 1 30); do
  history="$(curl -fsS "${base_url}/api/consumer/messages" 2>/dev/null || true)"
  if python3 -c '
import json, sys
message_id = sys.argv[1]
try:
    items = json.load(sys.stdin).get("messages", [])
except (json.JSONDecodeError, UnicodeDecodeError):
    raise SystemExit(1)
raise SystemExit(0 if any(item["id"] == message_id for item in items) else 1)
' "${message_id}" <<<"${history}"; then
    break
  fi
  [[ "$attempt" == 30 ]] && { echo "A mensagem não foi persistida." >&2; exit 1; }
  sleep 2
done

echo "Mensagem persistida antes da releitura"
docker compose stop consumer-api >/dev/null
echo "Resetando o grupo ${group} para o início do tópico ${topic}"
docker compose exec -T kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --group "${group}" \
  --topic "${topic}" \
  --reset-offsets --to-earliest --execute
docker compose start consumer-api >/dev/null
trap - EXIT

for attempt in $(seq 1 30); do
  logs="$(docker compose logs --no-color --since 5m consumer-api 2>/dev/null || true)"
  persisted_count="$(grep -c "event=persisted message_id=${message_id}" <<<"${logs}" || true)"
  if (( persisted_count >= 2 )); then
    history="$(curl -fsS "${base_url}/api/consumer/messages")"
    count="$(python3 -c '
import json, sys
message_id = sys.argv[1]
try:
    items = json.load(sys.stdin).get("messages", [])
except (json.JSONDecodeError, UnicodeDecodeError):
    raise SystemExit(1)
print(sum(item["id"] == message_id for item in items))
' "${message_id}" <<<"${history}")"
    if [[ "$count" == 1 ]]; then
      echo "Releitura confirmada: ${persisted_count} registros de log, 1 registro no PostgreSQL"
      grep "message_id=${message_id}" <<<"${logs}"
      exit 0
    fi
  fi
  [[ "$attempt" == 30 ]] && { echo "A releitura não foi confirmada." >&2; exit 1; }
  sleep 2
done
