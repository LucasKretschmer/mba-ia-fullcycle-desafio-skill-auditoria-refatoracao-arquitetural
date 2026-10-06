# Catálogo de Anti-patterns

Usado na Fase 2. Cada item tem um ID, a severidade padrão, os sinais de detecção (textuais e estruturais) e a transformação do playbook que resolve.

## Escala de severidade

- **CRITICAL:** falha grave de arquitetura ou segurança que impede o funcionamento correto, expõe dados sensíveis (credenciais hardcoded, SQL Injection) ou viola completamente a separação de responsabilidades (God Class com banco, regras e roteamento no mesmo arquivo).
- **HIGH:** violação forte de MVC/SOLID que dificulta muito manutenção e testes (regra de negócio pesada em controller/rota, acoplamento sem injeção de dependência, estado global mutável).
- **MEDIUM:** padronização, duplicação, performance moderada (N+1, middleware mal usado, validação ausente, API deprecated).
- **LOW:** legibilidade, nomes ruins, magic numbers, imports sem uso.

A severidade pode **subir** um nível quando o contexto agrava (ex.: dado sensível exposto em endpoint público) e **descer** quando o impacto é contido (ex.: segredo apenas em script de seed local). Justifique sempre que fugir do padrão.

## Resumo

| ID | Anti-pattern | Severidade | Playbook |
|---|---|---|---|
| AP01 | Credenciais / segredos hardcoded | CRITICAL | T1 |
| AP02 | SQL Injection (query montada com string) | CRITICAL | T2 |
| AP03 | God Class / God File | CRITICAL | T3 |
| AP04 | Endpoint sensível sem autenticação/autorização | CRITICAL | T13 |
| AP05 | Armazenamento inseguro de senha | CRITICAL | T5 |
| AP06 | Exposição de dados sensíveis (resposta ou log) | CRITICAL | T5, T14 |
| AP07 | Regra de negócio no controller/rota (Fat Controller) | HIGH | T6 |
| AP08 | Acoplamento forte sem injeção de dependência | HIGH | T7 |
| AP09 | Estado global mutável | HIGH | T7 |
| AP10 | Operação multi-etapa sem transação / callback hell | HIGH | T9 |
| AP11 | Configuração insegura de execução (debug, CORS aberto) | HIGH | T1 |
| AP12 | Queries N+1 | MEDIUM | T8 |
| AP13 | Validação ausente, fraca ou duplicada | MEDIUM | T10 |
| AP14 | Error handling inconsistente / vazamento de exceção | MEDIUM | T4 |
| AP15 | Código duplicado (serialização, regras repetidas) | MEDIUM | T6, T10 |
| AP16 | Uso de APIs deprecated | MEDIUM | T11 |
| AP17 | Integridade referencial ignorada (registros órfãos) | MEDIUM | T9 |
| AP18 | Magic numbers / strings | LOW | T12 |
| AP19 | Nomes ruins / pouco descritivos | LOW | T12 |
| AP20 | Imports, variáveis e código mortos | LOW | T12 |
| AP21 | `print` / `console.log` no lugar de logger | LOW | T14 |
| AP22 | Condicionais verbosas (`if x: return True else: return False`) | LOW | T12 |

---

## CRITICAL

### AP01 — Credenciais / segredos hardcoded
**Sinais de detecção**
- Atribuição literal a chaves sensíveis: `SECRET_KEY = "..."`, `password = '...'`, `apiKey`, `paymentGatewayKey`, `dbPass`, `token`, `pk_live_`, `sk_live_`.
- `grep -niE "(secret|passw|pass|pwd|key|token)\s*[:=]\s*['\"]"`.
- Objeto/dicionário `config` literal no código em vez de leitura de `os.environ` / `process.env`.
- Segredo devolvido em endpoint (ex.: `/health` retornando `secret_key`) → também AP06.

**Impacto:** qualquer pessoa com acesso ao repositório (ou à resposta HTTP) obtém as credenciais; impossível ter valores diferentes por ambiente.

### AP02 — SQL Injection
**Sinais de detecção**
- SQL montado por concatenação ou interpolação: `"... WHERE id = " + str(id)`, `f"SELECT ... {var}"`, `` `SELECT ... ${var}` ``, `"... '" + nome + "'"`, `%` formatting em SQL.
- `LIKE '%" + termo + "%'`.
- `cursor.execute(query)` onde `query` foi construída dinamicamente com input do usuário.
- Endpoint que recebe SQL do cliente e executa (`/admin/query`) → também AP04.

**Não é finding:** placeholders (`?`, `%s`, `:nome`, `$1`) com parâmetros separados, ORM com filtros (`filter_by`, `.like(f'%{q}%')` do SQLAlchemy é parametrizado).

### AP03 — God Class / God File
**Sinais de detecção**
- Um arquivo/classe que faz 3+ destas coisas: abre conexão/define schema, define rotas, contém regra de negócio, formata resposta, guarda config.
- Classe "Manager"/"Helper"/"Utils" com métodos de domínios diferentes (usuários, pagamentos, relatórios).
- Arquivo de models com funções de 3+ domínios e 300+ linhas.
- Métodos com 50+ linhas ou callbacks aninhados em 4+ níveis.

**Impacto:** impossível testar em isolamento; qualquer mudança afeta tudo.

### AP04 — Endpoint sensível sem autenticação/autorização
**Sinais de detecção**
- Rotas `/admin/*`, `reset`, `query`, `delete`, relatórios financeiros sem nenhum decorator/middleware de auth.
- Endpoint que executa SQL arbitrário ou apaga a base.
- "Token" falso ou previsível (`'fake-jwt-token-' + id`), login que não gera credencial verificável.
- `DELETE /users/:id` acessível a qualquer um.

### AP05 — Armazenamento inseguro de senha
**Sinais de detecção**
- Senha gravada em texto puro (`INSERT ... senha` com o valor recebido; seed com `'admin123'`).
- Hash fraco ou inadequado: `md5`, `sha1`, `sha256` sem salt, base64, funções caseiras (`badCrypto`).
- Comparação de senha dentro da query SQL (`WHERE email = ? AND senha = ?`).

**Correto:** `werkzeug.security.generate_password_hash`, `bcrypt`, `argon2`, `crypto.scrypt` com salt.

### AP06 — Exposição de dados sensíveis
**Sinais de detecção**
- Serialização que inclui `senha`/`password`/`hash` (`to_dict` com `'password'`, `SELECT *` de usuários devolvido direto).
- Log de dado sensível: número de cartão, senha, chave de API em `print`/`console.log`.
- Endpoint de health/debug devolvendo config, path do banco, `secret_key`.
- Mensagens de erro com `str(e)` ou stack trace para o cliente (combina com AP14).

---

## HIGH

### AP07 — Regra de negócio no controller/rota (Fat Controller)
**Sinais de detecção**
- Handler HTTP com cálculo de domínio (descontos, total de pedido, status de pagamento, "está atrasada?"), loops de agregação, várias queries.
- Handler com 40+ linhas.
- Efeitos colaterais de negócio (enviar e-mail/SMS, notificar) escritos inline no handler.
- Rotas acessando o ORM/driver diretamente (`Model.query...`, `db.session...`, `db.run(...)`) sem passar por model/service.

### AP08 — Acoplamento forte sem injeção de dependência
**Sinais de detecção**
- Funções de dados chamando `get_db()` global em toda função; classes instanciando dependências no construtor (`new sqlite3.Database(...)` dentro da classe de negócio).
- Módulos importando o objeto `app` ou a conexão concreta de outro módulo.
- Impossível trocar banco ou mockar sem monkeypatch.

### AP09 — Estado global mutável
**Sinais de detecção**
- `global` em Python, variáveis `let` de módulo alteradas em funções (`globalCache[key] = ...`, `totalRevenue`).
- Conexão única compartilhada entre threads (`check_same_thread=False` com conexão global).
- Listas em memória usadas como "banco" (`self.notifications = []` em serviço singleton).

### AP10 — Operação multi-etapa sem transação / callback hell
**Sinais de detecção**
- Sequência INSERT/UPDATE de várias tabelas sem `BEGIN/COMMIT/ROLLBACK` (pedido + itens + estoque; matrícula + pagamento).
- Retorno no meio do fluxo deixando escrita parcial.
- Callbacks aninhados 3+ níveis (`db.get(..., () => db.run(..., () => db.run(...)))`), erros de callback ignorados (`(err) => {}` sem checar `err`).
- Contadores manuais para saber quando callbacks paralelos acabaram.

### AP11 — Configuração insegura de execução
**Sinais de detecção**
- `debug=True`, `DEBUG = True` fixo, `app.run(host='0.0.0.0', debug=True)` (debugger interativo exposto).
- `CORS(app)` / `cors()` sem restrição de origem em API com dados sensíveis.
- Porta, path do banco e ambiente fixos no código.

---

## MEDIUM

### AP12 — Queries N+1
**Sinais de detecção**
- Query dentro de `for`/`forEach` sobre o resultado de outra query (`for pedido in pedidos: execute("SELECT ... WHERE pedido_id = ...")`).
- `Model.query.get(x.fk_id)` dentro de loop em vez de relationship/join.
- `len(user.tasks)` em loop com lazy loading.
- Várias queries `COUNT(*)` separadas que poderiam ser um `GROUP BY`.

### AP13 — Validação ausente, fraca ou duplicada
**Sinais de detecção**
- `request.get_json()` / `req.body` usado sem checar tipo, campos obrigatórios ou formato.
- Comparações numéricas sobre valor não convertido (`priority < 1` quando pode vir string → TypeError 500).
- Mesmo bloco de validação copiado em criar e atualizar.
- Regex de e-mail duplicada; listas de valores válidos repetidas em vários arquivos.
- Validação existe em helper/model mas não é usada pelas rotas.

### AP14 — Error handling inconsistente / vazamento de exceção
**Sinais de detecção**
- `try/except Exception as e: return {"erro": str(e)}, 500` repetido em cada handler.
- `except:` sem tipo (bare except) engolindo erros.
- Respostas de erro com formatos diferentes (`res.send("texto")` vs JSON; `erro` vs `error`).
- Ausência de `@app.errorhandler` / middleware `(err, req, res, next)`.

### AP15 — Código duplicado
**Sinais de detecção**
- Mesmo dicionário de serialização montado manualmente em 3+ lugares em vez de `to_dict()`.
- Mesma regra (ex.: "tarefa atrasada", cálculo de estatística) reimplementada em vários handlers enquanto já existe método no model.
- Funções quase idênticas que diferem só por um filtro (`get_pedidos_usuario` vs `get_todos_pedidos`).

### AP16 — Uso de APIs deprecated
Verifique sempre. Sinais conhecidos por stack:

| Stack | Deprecated | Equivalente moderno |
|---|---|---|
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` (legacy Query API) | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `Model.query.filter_by(...).all()` em código novo | `db.session.execute(db.select(Model).filter_by(...)).scalars().all()` |
| Python 3.12+ | `datetime.utcnow()` / `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` |
| Flask 2.3+/3.x | `@app.before_first_request` (removido), `flask.json.JSONEncoder`, `app.json_encoder` | inicialização na factory, `app.json` provider |
| Flask 3.1 | `flask.__version__` | `importlib.metadata.version("flask")` |
| Node.js | `new Buffer(x)` / `Buffer(x)` | `Buffer.from(x)` |
| Node.js | `crypto.createCipher` | `crypto.createCipheriv` |
| Node.js | `url.parse()` | `new URL()` |
| Express 4 | `body-parser` separado | `express.json()` |
| Express 4→5 | `res.send(status)`, `res.json(obj, status)`, `app.del()`, `req.param()` | `res.status(code).send()`, `app.delete()`, `req.params`/`req.query` |
| Node sqlite3 | API só de callback | wrapper com Promise / `async/await` (ou `better-sqlite3`) |
| Marshmallow 3.x | `fields.Field(default=...)`, `missing=` | `dump_default=` / `load_default=` |

Também conta: dependência com versão bem desatualizada fixada no manifesto quando o código usa API que mudou.

### AP17 — Integridade referencial ignorada
**Sinais de detecção**
- `DELETE` de entidade pai sem tratar filhos (matrículas, pagamentos, tarefas ficam órfãs) e sem `FOREIGN KEY ... ON DELETE`.
- Mensagem de resposta admitindo inconsistência ("ficaram sujos no banco").
- Tabelas sem chave estrangeira declarada entre entidades relacionadas.

---

## LOW

### AP18 — Magic numbers / strings
**Sinais:** limites de desconto (`10000`, `0.1`), faixas de prioridade (`1..5`), listas de status/categorias literais espalhadas, `10000` iterações, strings de status (`'PAID'`, `'pendente'`) repetidas.

### AP19 — Nomes ruins
**Sinais:** variáveis de uma letra fora de loops curtos (`u`, `e`, `p`, `cc`, `cid`), campos de API abreviados (`usr`, `eml`, `pwd`), nomes enganosos (`badCrypto`, `AppManager`, `utils` que guarda config), parâmetro `id` sombreando builtin.

### AP20 — Código morto
**Sinais:** imports não usados (`import os, sys, json`), variáveis exportadas e nunca lidas, funções utilitárias nunca chamadas, dependência no manifesto sem uso.

### AP21 — `print` / `console.log` como log
**Sinais:** `print(` / `console.log(` em código de aplicação para registrar eventos ou erros; mensagens simulando envio de e-mail/SMS.

### AP22 — Condicionais verbosas
**Sinais:** `if cond: return True else: return False`; ifs aninhados que podem virar uma expressão booleana; `type(x) == list` em vez de `isinstance`.
