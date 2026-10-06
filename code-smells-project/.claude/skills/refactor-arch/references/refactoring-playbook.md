# Playbook de Refatoração

Transformações concretas usadas na Fase 3. Cada uma indica quais anti-patterns resolve. Os exemplos estão em Python (Flask) e JavaScript (Express); para outra stack, aplique a mesma ideia com a sintaxe dela.

| ID | Transformação | Resolve |
|---|---|---|
| T1 | Extrair configuração para módulo + variáveis de ambiente | AP01, AP11 |
| T2 | Queries parametrizadas | AP02 |
| T3 | Quebrar God Class em Model / Controller / View por domínio | AP03 |
| T4 | Error handler centralizado + erros de domínio | AP14 |
| T5 | Hash de senha seguro + serialização sem dados sensíveis | AP05, AP06 |
| T6 | Mover regra de negócio do controller para model/service | AP07, AP15 |
| T7 | Injeção de dependência e composition root | AP08, AP09 |
| T8 | Eliminar N+1 com JOIN / eager loading / agregação | AP12 |
| T9 | Transação + async/await no lugar de callbacks | AP10, AP17 |
| T10 | Camada de validação reutilizável | AP13, AP15 |
| T11 | Substituir APIs deprecated | AP16 |
| T12 | Constantes, nomes claros e limpeza de código morto | AP18, AP19, AP20, AP22 |
| T13 | Proteger endpoints sensíveis | AP04 |
| T14 | Logging estruturado sem dados sensíveis | AP06, AP21 |

---

## T1 — Extrair configuração para módulo + variáveis de ambiente

**Antes (Python)**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
...
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois (Python)** `src/config/settings.py`
```python
import os
import secrets


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("DEBUG"))
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
```
```python
# src/app.py
def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)
    ...
    return app
```

**Antes (Node)**
```js
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000
};
```

**Depois (Node)** `src/config/settings.js`
```js
const settings = {
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
};

module.exports = settings;
```

Sempre criar `.env.example` com as chaves (sem valores reais). Se o projeto já tem `python-dotenv`/`dotenv` como dependência, carregue o `.env` no settings.

---

## T2 — Queries parametrizadas

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```

**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

query = "SELECT * FROM produtos WHERE 1=1"
params = []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(query, params)
```

**Node (sqlite3 / pg)**
```js
// antes
db.get(`SELECT * FROM users WHERE email = '${email}'`);
// depois
db.get('SELECT * FROM users WHERE email = ?', [email]);
```

Nunca interpole nomes de coluna/tabela vindos do usuário; se precisar ordenar dinamicamente, use uma whitelist.

---

## T3 — Quebrar God Class em Model / Controller / View por domínio

**Antes** (um arquivo com conexão, rotas e regra)
```js
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    initDb() { /* CREATE TABLE ... INSERT seed ... */ }
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => { /* 50 linhas de SQL + regra */ });
        app.get('/api/admin/financial-report', (req, res) => { /* ... */ });
    }
}
```

**Depois**
```js
// src/database/connection.js  → abre conexão, cria schema, seed
// src/models/courseModel.js
function createCourseModel(db) {
    return {
        findActiveById: (id) => db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]),
        findAll: () => db.all('SELECT * FROM courses'),
    };
}
module.exports = { createCourseModel };

// src/controllers/checkoutController.js
function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const input = validateCheckout(req.body);
            const result = await checkoutService.checkout(input);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
        },
    };
}

// src/views/routes.js
function buildRoutes({ checkoutController, reportController }) {
    const router = express.Router();
    router.post('/checkout', asyncHandler(checkoutController.checkout));
    router.get('/admin/financial-report', asyncHandler(reportController.financialReport));
    return router;
}
```

Python segue o mesmo corte: `models.py` gigante → `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`; `controllers.py` → um controller por domínio; `app.add_url_rule(...)` → `views/<dominio>_routes.py` com Blueprint.

```python
# src/views/produto_routes.py
from flask import Blueprint
from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)
produto_bp.get("/produtos")(produto_controller.listar)
produto_bp.get("/produtos/busca")(produto_controller.buscar)
produto_bp.get("/produtos/<int:produto_id>")(produto_controller.detalhar)
produto_bp.post("/produtos")(produto_controller.criar)
```

---

## T4 — Error handler centralizado + erros de domínio

**Antes** (repetido em todo handler)
```python
def buscar_produto(id):
    try:
        produto = models.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Depois**
```python
# src/utils/errors.py
class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    status_code = 400
```
```python
# src/middlewares/error_handler.py
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException
from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"erro": error.description, "sucesso": False}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
```
```python
# controller
def detalhar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200
```

**Express**
```js
// src/middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
    const status = err.statusCode || 500;
    if (status >= 500) console.error(err);
    res.status(status).send(status >= 500 ? 'Erro interno' : err.message);
}

// wrapper para não repetir try/catch em cada rota async
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// app.js — registrado depois das rotas
app.use('/api', routes);
app.use(errorHandler);
```

Mantenha o formato de erro que o cliente já conhece (texto puro, `erro`, `error`...).

---

## T5 — Hash de senha seguro + serialização sem dados sensíveis

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```

**Depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)

def to_dict(self):
    return {"id": self.id, "email": self.email, "role": self.role}
```

Login com SQL cru: buscar por e-mail e comparar o hash no código, nunca `WHERE senha = ?`.
```python
row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
if row and check_password_hash(row["senha"], senha):
    ...
```

**Node (sem dependência extra)**
```js
// antes
function badCrypto(pwd) { /* base64 repetido */ }

// depois
const crypto = require('crypto');

function hashPassword(password) {
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.scryptSync(password, salt, 64).toString('hex');
    return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
    const [salt, hash] = stored.split(':');
    const candidate = crypto.scryptSync(password, salt, 64);
    return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```

Seeds também passam pelo hash. Se já existe banco com senhas antigas, documente a necessidade de recriar/migrar.

---

## T6 — Mover regra de negócio do controller para model/service

**Antes**
```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    for t in tasks:
        task_data = {...}
        if t.due_date:
            if t.due_date < datetime.utcnow():
                if t.status != 'done' and t.status != 'cancelled':
                    task_data['overdue'] = True
        ...
```

**Depois**
```python
# models/task.py
def is_overdue(self):
    return bool(
        self.due_date
        and self.due_date < utcnow()
        and self.status not in (STATUS_DONE, STATUS_CANCELLED)
    )

def to_dict(self, include_relations=False):
    data = {..., "overdue": self.is_overdue()}
    ...

# controllers/task_controller.py
def list_tasks():
    tasks = task_service.list_with_relations()
    return [t.to_dict(include_relations=True) for t in tasks]
```

Efeitos colaterais (notificação, e-mail) saem do controller para um service:
```python
# antes (controller)
print("ENVIANDO EMAIL: Pedido " + str(pedido_id) + " criado")
print("ENVIANDO SMS: Seu pedido foi recebido!")

# depois
pedido = pedido_service.criar(usuario_id, itens)   # service chama notification_service.pedido_criado(pedido)
```

Cálculos de domínio (desconto por faixa, total do pedido, status do pagamento) vão para o model ou service com nome expressivo:
```python
def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0
```

---

## T7 — Injeção de dependência e composition root

**Antes**
```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
```

**Depois (Flask: conexão por requisição em `g`)**
```python
# src/database.py
import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_schema(get_db())
```

**Depois (Node: dependências criadas no app.js e passadas adiante)**
```js
// src/app.js — composition root
const db = await createDatabase(settings.dbPath);
const cache = new Map();
const models = createModels(db);
const checkoutService = createCheckoutService({ db, models, cache, settings });
const checkoutController = createCheckoutController({ checkoutService });
app.use('/api', buildRoutes({ checkoutController, ... }));
```

Nenhum módulo de negócio cria a própria conexão ou guarda estado em variável global de módulo.

---

## T8 — Eliminar N+1 com JOIN / eager loading / agregação

**Antes**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois (SQL cru)**
```python
rows = db.execute(
    """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(pr.nome, 'Desconhecido') AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE (? IS NULL OR p.usuario_id = ?)
    ORDER BY p.id
    """,
    (usuario_id, usuario_id),
).fetchall()
# agrupar em Python por p.id
```

**Depois (SQLAlchemy)**
```python
from sqlalchemy.orm import joinedload

tasks = db.session.execute(
    db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
).scalars().all()
```

**Contagens separadas → um GROUP BY**
```python
# antes: 4 queries COUNT(*) WHERE status = ...
rows = db.session.execute(
    db.select(Task.status, db.func.count()).group_by(Task.status)
).all()
por_status = {status: total for status, total in rows}
```

---

## T9 — Transação + async/await no lugar de callbacks

**Antes**
```js
db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
    let enrId = this.lastID;
    self.db.run("INSERT INTO payments ...", [enrId, price, status], function (err) {
        self.db.run("INSERT INTO audit_logs ...", [...], (err) => {
            res.status(200).json({ msg: "Sucesso", enrollment_id: enrId });
        });
    });
});
```

**Depois**
```js
// src/database/connection.js — wrapper Promise sobre sqlite3
function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

async function transaction(work) {
    await run('BEGIN');
    try {
        const result = await work();
        await run('COMMIT');
        return result;
    } catch (err) {
        await run('ROLLBACK');
        throw err;
    }
}

// src/services/checkoutService.js
const enrollmentId = await db.transaction(async () => {
    const { lastID } = await enrollments.create(userId, courseId);
    await payments.create(lastID, course.price, PAYMENT_STATUS.PAID);
    await auditLogs.register(`Checkout curso ${courseId} por ${userId}`);
    return lastID;
});
```

**Python (sqlite3)**
```python
with db:  # commit no sucesso, rollback em exceção
    cur = db.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)", (...))
    db.executemany("INSERT INTO itens_pedido (...) VALUES (?, ?, ?, ?)", itens)
    db.executemany("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", baixas)
```

Exclusão de pai com filhos: apagar/tratar dependentes na mesma transação (ou `ON DELETE CASCADE`).
```js
await db.transaction(async () => {
    await db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
    await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
    await db.run('DELETE FROM users WHERE id = ?', [id]);
});
```

---

## T10 — Camada de validação reutilizável

**Antes** (copiado em criar e atualizar)
```python
if "nome" not in dados:
    return jsonify({"erro": "Nome é obrigatório"}), 400
if "preco" not in dados:
    return jsonify({"erro": "Preço é obrigatório"}), 400
if preco < 0:
    return jsonify({"erro": "Preço não pode ser negativo"}), 400
```

**Depois**
```python
# src/utils/validators.py
def require_json(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def validar_produto(dados):
    require_json(dados)
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")
    if not isinstance(dados["preco"], (int, float)) or dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    ...
    return {...}
```
```python
# controller
def criar():
    dados = validar_produto(request.get_json(silent=True))
    produto_id = produto_model.criar(**dados)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201
```

Mantenha as mesmas mensagens de erro já usadas pela API. Valide **tipo** antes de comparar (`int("abc")` não pode virar 500).

---

## T11 — Substituir APIs deprecated

**SQLAlchemy legacy Query.get**
```python
# antes
task = Task.query.get(task_id)
# depois
task = db.session.get(Task, task_id)
```

**datetime.utcnow (deprecated no Python 3.12)**
```python
# antes
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if self.due_date < datetime.utcnow(): ...

# depois — helper único, mantém datetime "naive" em UTC para compatibilidade com o SQLite
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow)
```

**Node**
```js
new Buffer(pwd)                 // → Buffer.from(pwd)
app.use(bodyParser.json())      // → app.use(express.json())
res.send(404, 'x')              // → res.status(404).send('x')
```

---

## T12 — Constantes, nomes claros e limpeza de código morto

**Antes**
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05

if status not in ['pending', 'in_progress', 'done', 'cancelled']: ...

def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
```
```js
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
```

**Depois**
```python
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")

def is_admin(self):
    return self.role == ROLE_ADMIN
```
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
```

O contrato externo (`usr`, `eml`...) é mantido; só os nomes internos mudam. Remova imports sem uso (`import os, sys, json`), exports nunca lidos e funções utilitárias que ninguém chama (ou passe a usá-las se fizerem sentido).

---

## T13 — Proteger endpoints sensíveis

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])
```

**Depois** — exigir credencial vinda da config; sem credencial configurada o endpoint fica desabilitado.
```python
# src/middlewares/auth.py
import hmac
from functools import wraps
from flask import current_app, request
from src.utils.errors import AppError


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided, expected):
            raise AppError("Acesso negado", 403)
        return view(*args, **kwargs)
    return wrapper
```
```js
// src/middlewares/auth.js
function adminOnly(settings) {
    return (req, res, next) => {
        if (!settings.adminToken || req.get('X-Admin-Token') !== settings.adminToken) {
            return res.status(403).send('Acesso negado');
        }
        next();
    };
}
```

Endpoint que executa SQL arbitrário: além de proteger, restrinja a `SELECT` (somente leitura) ou remova se não for necessário. Registre como "mudança intencional de comportamento". Tokens falsos (`'fake-jwt-token-' + id`) viram token assinado (`itsdangerous`, `jsonwebtoken`) ou ficam documentados como pendência se exigir mudança de contrato.

---

## T14 — Logging estruturado sem dados sensíveis

**Antes**
```python
print("Login bem-sucedido: " + email)
print("ERRO: " + str(e))
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

**Depois**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Login bem-sucedido para usuario_id=%s", usuario["id"])
logger.exception("Falha ao criar pedido")
```
```js
const last4 = cardNumber.slice(-4);
logger.info(`Processando pagamento com cartão final ${last4}`);
```

Configure o logging uma vez no entry point (`logging.basicConfig(level=...)`). Nunca logue senha, número completo de cartão, chave de API ou token.
