# Frontend produtor

Interface **React com TypeScript** para publicar mensagens. A comunicação é HTTP com o [backend produtor](../producer-api/README.md); não acessa diretamente Kafka ou PostgreSQL.

## Instalação e desenvolvimento

Execute nesta pasta, com **Node.js 24** e npm. A versão usada está em [.nvmrc](.nvmrc); as dependências exatas estão em [package-lock.json](package-lock.json).

```sh
npm ci
npm run dev
```

Acesse `http://localhost:5173/producer/`. O Vite escuta em `127.0.0.1:5173` e falha se a porta estiver ocupada. Inicie também o backend e suas dependências seguindo seu README. O proxy de desenvolvimento encaminha `/api/producer/` ao backend em `http://127.0.0.1:8001/`, removendo o prefixo.

O link para o histórico em desenvolvimento aponta para `http://localhost:5174/consumer/`, onde a outra aplicação deve estar rodando. No build de produção, usa `/consumer/` na mesma origem.

## Build e deploy

```sh
npm run typecheck
npm run build
```

O build verifica TypeScript e gera **`dist/`** com arquivos estáticos. O caminho base da interface e dos assets é **`/producer/`**, definido em [vite.config.ts](vite.config.ts).

Para inspecionar localmente o build, `npm run preview` usa `http://localhost:4173/producer/`. O Vite pode reutilizar seu proxy local nessa prévia; esse proxy não faz parte de `dist/`.

## Variáveis

Consulte [.env.example](.env.example) para as configurações.

| Variável | Default | Momento |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api/producer` | Incorporada ao JavaScript durante o build |
| `API_PROXY_TARGET` | `http://127.0.0.1:8001` | Destino do proxy Vite local; não entra no bundle |

Alterar uma variável no ambiente que já serve `dist/` não muda o JavaScript: uma mudança de `VITE_API_BASE_URL` exige novo build. O valor padrão corresponde à rota pública prevista no enunciado.

## Comportamento

Envia mensagens ao backend produtor por `POST /messages` e exibe o resultado da publicação.

Os cenários de verificação estão no [enunciado do desafio](../../README.md).
