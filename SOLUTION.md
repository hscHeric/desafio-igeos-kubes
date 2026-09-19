# Solução

## Como executar

Pré-requisitos: Docker Engine com Docker Compose. Crie a configuração local e inicie tudo:

```sh
cp .env.example .env
docker compose up --build -d
```

O ponto de entrada é `http://localhost:8080` por padrão:

- `http://localhost:8080/producer/`
- `http://localhost:8080/consumer/`
- `http://localhost:8080/api/producer/health/ready`
- `http://localhost:8080/api/consumer/health/ready`

Somente a porta do Nginx é publicada. Kafka, PostgreSQL, APIs e frontends usam a rede interna do Compose.

## Configuração local

Copie `.env.example` para `.env` e ajuste somente se necessário:

| Variável | Função |
| --- | --- |
| `HTTP_PORT` | Porta HTTP publicada pelo Nginx |
| `KAFKA_TOPIC` | Tópico compartilhado entre produtor e consumidor |
| `KAFKA_GROUP_ID` | Grupo do consumidor Kafka |
| `KAFKA_CLUSTER_ID` | Identificador persistente do cluster KRaft |
| `KAFKA_LOG_RETENTION_MS` | Retenção dos eventos Kafka |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Banco e credenciais locais do PostgreSQL |

## Decisões

Kafka usa KRaft com um broker e volume `kafka-data`; a retenção é de sete dias. PostgreSQL usa o volume `postgres-data`. O serviço `kafka-volume-init` prepara a permissão do volume para o usuário não privilegiado da imagem oficial. `kafka-init` cria o tópico e `postgres-init` prepara tabela e índice. Ambos são idempotentes.

Healthchecks e `depends_on` evitam iniciar serviços dependentes antes de Kafka, PostgreSQL, tópico e tabela estarem prontos. As APIs também repetem a conexão durante sua inicialização.

## Operação e diagnóstico

```sh
docker compose ps
docker compose logs -f kafka consumer-api
docker compose down
docker compose up -d
```

`docker compose down` preserva os volumes e as mensagens. Para apagar todos os dados intencionalmente:

```sh
docker compose down -v
```

## Ambiente de verificação

| Item | Valor |
| --- | --- |
| Sistema operacional | Fedora Linux 44 |
| Arquitetura | `x86_64` |
| CPU | 8 processadores lógicos |
| Memória RAM | 5,5 GiB |
| Disco disponível | 440 GiB |
| Docker Engine | `29.8.1` |
| Docker Compose | `v5.5.1` |

## Validação

A configuração do Compose foi validada:

```text
$ docker compose config --quiet
# saída vazia; código de saída 0

$ docker compose config --services
kafka-volume-init
consumer-web
kafka
kafka-init
producer-api
producer-web
postgres
postgres-init
consumer-api
nginx
```

Inicie os serviços e confira as duas interfaces e APIs pelo Nginx:

```sh
docker compose up --build -d
docker compose ps
curl -I http://localhost:8080/producer/
curl -I http://localhost:8080/consumer/
curl -i http://localhost:8080/api/producer/health/ready
curl -i http://localhost:8080/api/consumer/health/ready
```

Publique uma mensagem e confirme seu processamento:

```sh
curl -i -X POST http://localhost:8080/api/producer/messages \
  -H 'Content-Type: application/json' \
  --data '{"text":"evidencia-fluxo-completo"}'
sleep 10
curl -s http://localhost:8080/api/consumer/messages
```

Confirme o processamento de uma mensagem publicada com o consumidor parado:

```sh
docker compose stop consumer-api
curl -i -X POST http://localhost:8080/api/producer/messages \
  -H 'Content-Type: application/json' \
  --data '{"text":"evidencia-consumidor-parado"}'
docker compose start consumer-api
sleep 10
curl -s http://localhost:8080/api/consumer/messages
```

Recrie o ambiente sem apagar volumes e confirme que o histórico continua disponível:

```sh
docker compose down
docker compose up -d
sleep 10
curl -s http://localhost:8080/api/consumer/messages
```

A publicação deve retornar `202`; cada texto deve aparecer em `/consumer/` e em `/api/consumer/messages` em até 30 segundos. Para verificar Kafka recriado com uma mensagem pendente, execute a sequência do consumidor parado, seguida de `docker compose down` e `docker compose up -d`, sem remover os volumes. O histórico deve conter a mensagem após a retomada.

## Integração contínua

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) executa em pushes para `main`, pull requests e manualmente pelo GitHub Actions. Ele valida o Compose, constrói e inicia os serviços e executa [`scripts/verify-e2e.sh`](scripts/verify-e2e.sh), que confirma as rotas do Nginx, publica uma mensagem e verifica sua persistência pela API consumidora. Em caso de falha, o job publica o estado e os logs de todos os containers.

## Backup e restauração do PostgreSQL

Volumes preservam os dados entre recriações, mas não são um backup recuperável. [`scripts/backup-postgres.sh`](scripts/backup-postgres.sh) cria um dump PostgreSQL em formato customizado no diretório `backups/`, que não é versionado. Para restaurá-lo em um banco separado, sem alterar o banco da aplicação:

```sh
backup_file="$(bash scripts/backup-postgres.sh)"
RESTORE_DB=messages_restore bash scripts/restore-postgres-backup.sh "$backup_file"
```

O segundo comando recria apenas `messages_restore`, restaura o dump e imprime a quantidade de mensagens recuperadas. Para demonstrar a recuperação, compare esse total com a consulta da aplicação em `/api/consumer/messages` ou execute:

```sh
bash scripts/verify-backup-restore.sh
```

Esse script compara a quantidade de mensagens do banco principal com a restaurada em `ci_messages_restore`. O workflow de CI também executa essa verificação após o fluxo ponta a ponta. O backup fica no disco local e não inclui agendamento, criptografia ou cópia externa; esses controles devem ser definidos conforme a política do ambiente onde ele for armazenado.

## Notas

Tempo dedicado: aproximadamente 8 horas. A principal dificuldade foi a permissão inicial do volume Kafka. Usei Codex para revisar a configuração Docker/Compose e validei os comandos e o fluxo gerado.
