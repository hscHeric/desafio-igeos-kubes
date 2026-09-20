#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-http://localhost:8080}"
total="${LOAD_REQUESTS:-40}"
workers="${LOAD_WORKERS:-4}"

echo "Uso dos containers antes da carga"
docker compose stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'

echo "Executando ${total} publicações com ${workers} workers"
python3 scripts/load-test.py "${base_url}" "${total}" "${workers}"

sleep 5
echo "Uso dos containers depois da carga"
docker compose stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'
