# Backend consumidor

Serviço **Python e FastAPI** que consome mensagens do Kafka, persiste no PostgreSQL e oferece uma API de histórico. A interface consumidora consulta o banco através desta API.

## Instalação e preparação

Execute nesta pasta, com Python 3.12 e [uv](https://docs.astral.sh/uv/) (lockfile gerado com uv 0.12.0):

```sh
uv sync --locked
```

Consulte [.env.example](.env.example) para as configurações. Para preparar a tabela e o índice, com PostgreSQL acessível e o banco já criado:

```sh
uv run --locked python prepare.py
```

`prepare.py` executa [schema.sql](schema.sql), criando tabela e índice se ainda não existirem; não apaga registros nem cria o banco/usuário. O banco, o usuário e o tópico Kafka precisam existir antes de iniciar a aplicação. O script de preparação do tópico está documentado no [backend produtor](../producer-api/README.md).

Cada processo FastAPI também inicia um consumidor Kafka. As dependências exatas estão em [uv.lock](uv.lock).

## Configuração

| Variável | Default | Uso |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Interface HTTP |
| `PORT` | `8002` | Porta HTTP |
| `KAFKA_BROKERS` | `localhost:9092` | Brokers separados por vírgula |
| `KAFKA_TOPIC` | `messages` | Mesmo tópico do produtor |
| `KAFKA_GROUP_ID` | `message-store` | Grupo consumidor ao qual os offsets são associados |
| `DATABASE_URL` | Sem default; obrigatória | URI PostgreSQL com banco e credenciais |

As configurações são lidas na inicialização. Variáveis do processo têm prioridade sobre o `.env` da pasta de execução, seguidas dos defaults. `DATABASE_URL` ausente ou vazia e `PORT` não numérica são rejeitadas na inicialização. Chaves extras no `.env` são ignoradas.

## API HTTP

| Rota interna | Rota pública esperada | Função |
| --- | --- | --- |
| `GET /messages` | `/api/consumer/messages` | Consultar até 100 mensagens recentes |
| `GET /health/live` | `/api/consumer/health/live` | Verificar se a API responde |
| `GET /health/ready` | `/api/consumer/health/ready` | Verificar disponibilidade das dependências e do consumidor |

`GET /messages` retorna `{"messages":[...]}`, com os campos `id`, `text`, `createdAt` e `processedAt` em cada mensagem. Os endpoints também estão disponíveis em `/docs` e `/openapi.json` no backend.

## Persistência e recuperação

As mensagens são armazenadas no PostgreSQL. Reprocessar uma mensagem com o mesmo identificador não duplica o registro.

Uma falha de processamento pode interromper o consumo enquanto a API continua respondendo. Nesse caso, `/health/ready` retorna `503`; após corrigir a causa, é necessário reiniciar o consumidor.

Os cenários de verificação estão no [enunciado do desafio](../../README.md).
