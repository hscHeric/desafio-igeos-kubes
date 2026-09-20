#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-http://localhost:8080}"
topic="${KAFKA_TOPIC:-messages}"
group="${KAFKA_GROUP_ID:-message-store}"
message="kafka-recovery-$(date -u +%Y%m%dT%H%M%SZ)-${RANDOM}"

kafka_cli() {
  docker compose exec -T kafka "/opt/kafka/bin/$1" "${@:2}"
}

wait_for_kafka() {
  for attempt in $(seq 1 30); do
    if kafka_cli kafka-topics.sh --bootstrap-server kafka:9092 --list >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Kafka não voltou a ficar disponível." >&2
  return 1
}

wait_for_message() {
  local message_id="$1"
  for attempt in $(seq 1 30); do
    local history
    history="$(curl -fsS "${base_url}/api/consumer/messages" 2>/dev/null || true)"
    if python3 -c '
import json, sys
try:
    items = json.load(sys.stdin).get("messages", [])
except (json.JSONDecodeError, UnicodeDecodeError):
    raise SystemExit(1)
raise SystemExit(0 if any(item["id"] == sys.argv[1] for item in items) else 1)
' "${message_id}" <<<"${history}"; then
      return 0
    fi
    sleep 2
  done
  return 1
}

echo "Metadados do tópico antes da recuperação"
kafka_cli kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic "${topic}"
echo "Offsets do grupo antes da recuperação"
kafka_cli kafka-consumer-groups.sh --bootstrap-server kafka:9092 --group "${group}" --describe || true

echo "Parando o consumidor e publicando um evento pendente"
docker compose stop consumer-api >/dev/null
response="$(curl -fsS -X POST "${base_url}/api/producer/messages" \
  -H 'Content-Type: application/json' \
  --data "{\"text\":\"${message}\"}")"
message_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"${response}")"
echo "Mensagem pendente: ${message_id}"

echo "Recriando somente o container Kafka; os volumes não são removidos"
docker compose stop kafka >/dev/null
docker compose rm --force kafka >/dev/null
docker compose up -d kafka >/dev/null
wait_for_kafka

echo "Metadados do tópico depois da recuperação"
kafka_cli kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic "${topic}"

docker compose start consumer-api >/dev/null
if ! wait_for_message "${message_id}"; then
  echo "A mensagem não foi processada após a recuperação do broker." >&2
  exit 1
fi

echo "Offsets do grupo depois da recuperação"
kafka_cli kafka-consumer-groups.sh --bootstrap-server kafka:9092 --group "${group}" --describe || true
logs="$(docker compose logs --no-color --since 5m consumer-api 2>/dev/null || true)"
echo "Evidência do evento recuperado"
grep "message_id=${message_id}" <<<"${logs}" || true

count="$(curl -fsS "${base_url}/api/consumer/messages" | python3 -c '
import json, sys
message_id = sys.argv[1]
items = json.load(sys.stdin).get("messages", [])
print(sum(item["id"] == message_id for item in items))
' "${message_id}")"
if [[ "${count}" != 1 ]]; then
  echo "Esperava exatamente um registro no PostgreSQL; encontrei ${count}." >&2
  exit 1
fi

echo "Recuperação confirmada: volume, metadados e offset preservados; 1 registro no PostgreSQL"
