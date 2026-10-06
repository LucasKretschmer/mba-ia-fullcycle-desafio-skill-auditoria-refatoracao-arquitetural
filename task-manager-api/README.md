# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: ajuste SECRET_KEY, PORT, DATABASE_URL...
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (porta configurável via `PORT`). O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias. Bancos criados antes da troca do hash de senha precisam ser recriados com o seed.

## Estrutura

`routes/` (blueprints) → `controllers/` (request/response) → `services/` (regras) → `models/` (SQLAlchemy). Configuração em `config/`, autenticação e tratamento de erros em `middlewares/`, validação em `utils/validators.py`.

## Autenticação

`POST /login` devolve um `token` assinado. Envie `Authorization: Bearer <token>` para:

- `DELETE /tasks/<id>` e `DELETE /categories/<id>`: qualquer usuário autenticado;
- `DELETE /users/<id>`, criar usuário com `role` diferente de `user` e alterar `role`/`active` em `PUT /users/<id>`: somente `admin`.
