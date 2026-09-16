# Backend produtor

API **Python e FastAPI** que recebe texto e publica mensagens no Kafka. Não acessa PostgreSQL.

## Instalação e preparação

Execute os comandos nesta pasta. Use Python 3.12 e [uv](https://docs.astral.sh/uv/) (lockfile gerado com uv 0.12.0).

```sh
uv sync --locked
```

Consulte [.env.example](.env.example) para as configurações. Para preparar o tópico:

```sh
uv run --locked python prepare.py
```

O Kafka deve estar acessível antes da preparação. `prepare.py` cria um tópico com uma partição e fator de replicação 1; se já existir, preserva-o e não altera sua configuração. O tópico precisa existir antes de iniciar a aplicação.

Dependências exatas estão em [uv.lock](uv.lock).

## Configuração

| Variável | Default | Uso |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Interface de escuta HTTP |
| `PORT` | `8001` | Porta de escuta HTTP |
| `KAFKA_BROKERS` | `localhost:9092` | Brokers separados por vírgula |
| `KAFKA_TOPIC` | `messages` | Tópico compartilhado com o consumidor |

As configurações são lidas na inicialização. Variáveis do processo têm prioridade sobre o `.env` da pasta de execução, seguidas dos defaults. Uma configuração inválida, como `PORT` não numérica, impede a inicialização. Chaves extras no `.env` são ignoradas.

## API HTTP

| Rota interna | Rota pública esperada | Função |
| --- | --- | --- |
| `POST /messages` | `/api/producer/messages` | Publicar uma mensagem |
| `GET /health/live` | `/api/producer/health/live` | Verificar se a API responde |
| `GET /health/ready` | `/api/producer/health/ready` | Verificar disponibilidade do Kafka e do tópico |

`POST /messages` recebe JSON no formato `{"text":"Olá, Kafka!"}` e retorna `202` com `id`, `text` e `createdAt` após a confirmação do Kafka. A gravação no banco ocorre depois.

Os endpoints também estão disponíveis em `/docs` e `/openapi.json` no backend.

Os cenários de verificação estão no [enunciado do desafio](../../README.md).
