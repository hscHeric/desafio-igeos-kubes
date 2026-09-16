# Frontend consumidor

Interface **React com TypeScript** que exibe mensagens persistidas através do [backend consumidor](../consumer-api/README.md). Não acessa diretamente Kafka ou PostgreSQL.

## Instalação e desenvolvimento

Execute nesta pasta, com **Node.js 24** e npm. A versão usada está em [.nvmrc](.nvmrc); as dependências exatas estão em [package-lock.json](package-lock.json).

```sh
npm ci
npm run dev
```

Acesse `http://localhost:5174/consumer/`. O Vite escuta em `127.0.0.1:5174` e falha se a porta estiver ocupada. O backend e suas dependências também precisam estar disponíveis. O proxy de desenvolvimento encaminha `/api/consumer/` ao backend em `http://127.0.0.1:8002/`, removendo o prefixo.

O link para publicar em desenvolvimento aponta para `http://localhost:5173/producer/`. No build de produção, usa `/producer/` na mesma origem.

## Build e deploy

```sh
npm run typecheck
npm run build
```

O build verifica TypeScript e gera **`dist/`** com arquivos estáticos. O caminho base da interface e dos assets é **`/consumer/`**, definido em [vite.config.ts](vite.config.ts).

Para inspecionar localmente o build, `npm run preview` usa `http://localhost:4174/consumer/`. O Vite pode reutilizar seu proxy local nessa prévia; esse proxy não faz parte de `dist/`.

## Variáveis

Consulte [.env.example](.env.example) para as configurações.

| Variável | Default | Momento |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api/consumer` | Incorporada ao bundle no build |
| `API_PROXY_TARGET` | `http://127.0.0.1:8002` | Usada somente pelo proxy local Vite |

Alterar uma variável no ambiente que já serve `dist/` não modifica o bundle: uma mudança de `VITE_API_BASE_URL` exige novo build. O valor padrão corresponde à rota pública prevista no enunciado.

## Comportamento

Consulta `GET /messages` no backend consumidor e atualiza o histórico automaticamente. Exibe mensagens de erro quando a consulta falha.

Os cenários de verificação estão no [enunciado do desafio](../../README.md).
