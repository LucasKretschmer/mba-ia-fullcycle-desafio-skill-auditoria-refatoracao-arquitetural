# Análise de Projeto — Heurísticas

Guia para a Fase 1. O objetivo é descobrir **o que** é o projeto antes de julgar **como** ele está escrito.

## 1. Linguagem

Detecte pelo manifesto primeiro e pela extensão dos arquivos depois.

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python |
| `package.json`, `*.js`, `*.mjs`, `*.cjs` | JavaScript (Node.js) |
| `tsconfig.json`, `*.ts` | TypeScript |
| `go.mod`, `*.go` | Go |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |
| `*.csproj`, `*.cs` | C# |

Se houver mais de uma, a linguagem principal é a que contém o entry point e a maior parte das linhas.

## 2. Framework e versão

Leia a versão no manifesto (`flask==3.1.1`, `"express": "^4.18.2"`). Confirme pelo código:

| Framework | Sinais no código |
|---|---|
| Flask | `from flask import Flask`, `Flask(__name__)`, `@app.route`, `Blueprint`, `app.add_url_rule` |
| FastAPI | `FastAPI()`, `@app.get`, `APIRouter` |
| Django | `settings.py`, `urls.py`, `INSTALLED_APPS`, `manage.py` |
| Express | `require('express')` / `import express`, `app.get(`, `express.Router()` |
| NestJS | `@Controller`, `@Module`, `@nestjs/core` |
| Fastify | `require('fastify')`, `fastify.register` |
| Spring | `@RestController`, `@SpringBootApplication` |
| Laravel | `artisan`, `routes/web.php`, `Illuminate\` |
| Gin / Echo | `gin.Default()`, `echo.New()` |

Liste também as dependências relevantes (CORS, ORM, validação, HTTP client, dotenv) e marque as que aparecem no manifesto mas não são usadas no código, porque isso também é finding (dependência morta).

## 3. Banco de dados e acesso a dados

| Sinal | Banco / estratégia |
|---|---|
| `sqlite3.connect`, `new sqlite3.Database`, `sqlite:///`, `:memory:` | SQLite (driver cru ou ORM) |
| `psycopg2`, `pg`, `postgresql://` | PostgreSQL |
| `pymysql`, `mysql2`, `mysql://` | MySQL |
| `mongoose`, `pymongo`, `mongodb://` | MongoDB |
| `SQLAlchemy`, `db.Model`, `flask_sqlalchemy` | ORM SQLAlchemy |
| `sequelize`, `typeorm`, `prisma`, `knex` | ORM / query builder Node |

Mapeie as tabelas a partir de `CREATE TABLE`, `__tablename__`, classes de model ou schemas. Anote onde o schema é criado (migration, script de seed, dentro do boot da aplicação?) e onde ficam os dados de seed.

## 4. Domínio

Deduza pelo vocabulário das tabelas, rotas e mensagens:

- `produtos`, `pedidos`, `carrinho`, `checkout`, `payments` → e-commerce
- `courses`, `enrollments`, `students` → LMS / cursos online
- `tasks`, `projects`, `categories`, `due_date`, `priority` → gestão de tarefas
- `accounts`, `transactions`, `balance` → financeiro

Descreva em uma linha: tipo de sistema + entidades principais + fluxos relevantes (ex.: "checkout com criação de usuário, matrícula e pagamento").

## 5. Arquitetura atual

Classifique em uma destas categorias e justifique:

| Classificação | Sinais |
|---|---|
| **Monolítica sem camadas** | Poucos arquivos; o mesmo arquivo cria conexão, define rotas e tem regra de negócio; SQL junto do handler HTTP |
| **God Class** | Uma classe/arquivo que concentra banco + rotas + regras (ex.: `AppManager`, `utils` com config e lógica) |
| **Camadas parciais** | Existem pastas `models/`, `routes/`, `services/`, mas rotas ainda acessam o ORM direto, têm validação e regra de negócio inline, e não há controllers nem config isolados |
| **MVC / Layered** | Rotas finas → controllers → services/models, config separada, error handler central |

Para cada arquivo, anote em uma palavra o papel que ele exerce hoje (rotas, dados, regras, config, utilitário, misto). "Misto" é um forte indício de violação de responsabilidade.

## 6. Inventário de endpoints

Procure todas as definições de rota:

- Flask: `@app.route`, `@bp.route`, `app.add_url_rule(path, endpoint, view_func, methods=[...])`
- Express: `app.get|post|put|patch|delete(`, `router.<method>(`
- FastAPI: `@app.<method>(`, `@router.<method>(`

Registre `METHOD path → arquivo:linha do handler`. Inclua rotas utilitárias (`/`, `/health`) e administrativas.

## 7. Contagem

- **Source files:** arquivos de código da aplicação (inclui seeds e scripts). Exclua dependências instaladas, `.claude/`, bancos e lockfiles.
- **Linhas:** `wc -l` sobre esses arquivos.

## 8. Como validar (usado na Fase 3)

Descubra como a aplicação sobe, nesta ordem: README do projeto → `scripts.start` do `package.json` → bloco `if __name__ == "__main__"` / `app.listen` → Dockerfile.

| Stack | Instalação | Boot | Porta padrão |
|---|---|---|---|
| Python/Flask | `pip install -r requirements.txt` (de preferência em venv) | `python app.py` ou `flask --app app run` | 5000 |
| Node/Express | `npm install` | `npm start` / `node <main>` | 3000 |

Boas práticas na validação:

- Suba o servidor em background, espere a porta responder (`curl` em loop curto) e só então rode os testes.
- Se a porta padrão estiver ocupada, use outra via variável de ambiente (após a refatoração a porta deve vir da config).
- Se o projeto exige seed antes do boot (ex.: `python seed.py`), rode-o.
- Para cada endpoint guarde `status code` + chaves do JSON de resposta. Para POST/PUT use payloads coerentes com a validação do próprio código (leia os handlers) ou com os exemplos do projeto (`api.http`, README).
- Ao final, mate o processo e remova o banco gerado no teste se ele não existia antes.
