# Solução

## Como executar

Pré-requisitos: Docker Engine com Docker Compose e pelo menos 4 GB de memória livre para os containers. Crie a configuração local e inicie tudo:

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

## Verificações executadas

- `docker compose config --quiet`
- publicação retornando `202` no produtor;
- consumo da mesma mensagem e persistência no PostgreSQL;
- endpoints de prontidão dos dois backends.

Para testar mensagens pendentes, pare o consumidor, publique uma mensagem pelo produtor e inicie-o novamente:

```sh
docker compose stop consumer-api
# publique uma mensagem em /producer/
docker compose start consumer-api
```

A mensagem deve aparecer em `/consumer/` em até 30 segundos. Repita após `docker compose down` e `docker compose up -d` para confirmar a persistência. A retenção de sete dias cobre mensagens pendentes nesse intervalo.

## Notas

Tempo dedicado: aproximadamente 8 horas. A principal dificuldade foi a permissão inicial do volume Kafka. Usei Codex para revisar a configuração Docker/Compose e validei os comandos e o fluxo gerado.
