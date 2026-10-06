# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (configurável por `HOST`/`PORT`). O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

As variáveis de ambiente suportadas estão em `.env.example`. Para usar os endpoints `/admin/*`, defina `ADMIN_TOKEN` e envie o mesmo valor no header `X-Admin-Token`. A senha do usuário `admin@loja.com` do seed vem de `SEED_ADMIN_SENHA`.

Bancos criados por versões anteriores continuam funcionando: no boot, senhas em texto puro são convertidas para hash.

## Estrutura

```
app.py              entry point (python app.py)
src/app.py          create_app(): composition root
src/config/         settings (ambiente) e constantes de domínio
src/database.py     conexão por requisição, schema, seed e transações
src/models/         acesso a dados por entidade
src/services/       pedido (transacional), relatório e notificações
src/controllers/    fluxo de cada requisição
src/views/          blueprints com as rotas
src/middlewares/    error handler central e autenticação admin
src/utils/          erros de domínio e validadores
```
