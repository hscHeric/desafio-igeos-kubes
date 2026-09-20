# Evidências de verificação

Execute os comandos a partir da raiz do repositório. As saídas são gravadas nesta pasta.

## 1. Primeira inicialização

Execute antes dos testes de preservação, pois remove os volumes locais:

```bash
mkdir -p evidence
docker compose down -v --remove-orphans
docker compose up --build -d 2>&1 | tee evidence/01-first-startup.txt
docker compose ps -a | tee -a evidence/01-first-startup.txt
```

## 2. Rotas do Nginx

```bash
{
  echo "PRODUCER"
  curl -I http://localhost:8080/producer/
  echo "CONSUMER"
  curl -I http://localhost:8080/consumer/
  echo "PRODUCER API"
  curl -i http://localhost:8080/api/producer/health/ready
  echo "CONSUMER API"
  curl -i http://localhost:8080/api/consumer/health/ready
} 2>&1 | tee evidence/02-nginx-routes.txt
```

## 3. Publicação e consulta

```bash
response="$(curl -sS -X POST http://localhost:8080/api/producer/messages \
  -H 'Content-Type: application/json' \
  -d '{"text":"evidencia-publicacao-consulta"}')"
echo "$response" | tee evidence/03-publish-response.txt
sleep 10
curl -sS http://localhost:8080/api/consumer/messages \
  | tee evidence/03-consumer-history.json
```

Confirme o status `202`, o campo `id` e a presença do texto no histórico.

## 4. Consumidor parado

```bash
docker compose stop consumer-api
curl -sS -X POST http://localhost:8080/api/producer/messages \
  -H 'Content-Type: application/json' \
  -d '{"text":"evidencia-consumidor-parado"}' \
  | tee evidence/04-pending-message.json
docker compose start consumer-api
sleep 15
curl -sS http://localhost:8080/api/consumer/messages \
  | tee evidence/04-after-consumer-restart.json
```

## 5. Preservação após `down/up`

```bash
curl -sS -X POST http://localhost:8080/api/producer/messages \
  -H 'Content-Type: application/json' \
  -d '{"text":"evidencia-preservacao-volume"}' \
  | tee evidence/05-before-recreation.json
sleep 10
docker compose down 2>&1 | tee evidence/05-down.txt
docker compose up -d 2>&1 | tee evidence/05-up.txt
sleep 15
curl -sS http://localhost:8080/api/consumer/messages \
  | tee evidence/05-after-recreation.json
```

Não use `docker compose down -v` neste teste.

## 6. Diagnóstico

```bash
docker compose ps -a | tee evidence/06-diagnostic-ps.txt
docker compose logs --no-color --tail=100 \
  producer-api consumer-api kafka postgres nginx loki promtail \
  | tee evidence/06-diagnostic-logs.txt
```

## 7. Backup, alertas e métricas

```bash
bash scripts/verify-backup-restore.sh \
  2>&1 | tee evidence/07-backup-restore.txt

bash scripts/verify-alert-recovery.sh \
  2>&1 | tee evidence/08-alert-recovery.txt

curl -sS --get \
  --data-urlencode 'query=producer_messages_published_total' \
  http://localhost:8080/prometheus/api/v1/query \
  | tee evidence/09-metric-published.json

curl -sS --get \
  --data-urlencode 'query=consumer_messages_persisted_total' \
  http://localhost:8080/prometheus/api/v1/query \
  | tee evidence/09-metric-persisted.json
```

## 8. Agregação de logs

```bash
bash scripts/verify-log-aggregation.sh \
  2>&1 | tee evidence/10-log-aggregation.txt
```

## 9. Retenção e reprocessamento Kafka

```bash
bash scripts/verify-kafka-reprocess.sh \
  2>&1 | tee evidence/kafka-reprocess-2026-09-20.txt
```

## 10. Recuperação avançada Kafka

```bash
bash scripts/verify-kafka-recovery-advanced.sh \
  2>&1 | tee evidence/kafka-recovery-advanced-2026-09-20.txt
```

## 11. Recursos e desempenho

```bash
LOAD_REQUESTS=40 LOAD_WORKERS=4 \
  bash scripts/verify-load.sh \
  2>&1 | tee evidence/load-test-2026-09-20.txt
```
