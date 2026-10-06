# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=troque-me npm start
```

A aplicação sobe em `http://localhost:3000` (ou na porta de `PORT`). Por padrão o banco SQLite é em memória e carrega seeds automaticamente no boot.

Variáveis de ambiente (veja `.env.example`):

- `PORT`: porta HTTP (padrão `3000`).
- `DB_PATH`: arquivo do SQLite (padrão `:memory:`).
- `ADMIN_TOKEN`: token exigido no header `X-Admin-Token` em `GET /api/admin/financial-report` e `DELETE /api/users/:id`. Sem ele essas rotas respondem 403.

## Estrutura

```
src/
├── app.js           composition root + listen
├── config/          settings (env) e constantes
├── database/        conexão SQLite com Promise, transação, schema e seed
├── models/          acesso a dados por entidade
├── services/        checkout e relatório financeiro
├── controllers/     fluxo de cada requisição
├── views/           rotas Express
├── middlewares/     auth admin e tratamento de erro
└── utils/           validação, erros, logger, hash de senha
```

Exemplos de requisições estão em `api.http`.
