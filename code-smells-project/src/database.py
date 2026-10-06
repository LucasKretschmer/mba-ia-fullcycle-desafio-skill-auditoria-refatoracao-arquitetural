import logging
import secrets
import sqlite3
from contextlib import contextmanager

from flask import current_app, g
from werkzeug.security import generate_password_hash

from src.config.constants import TIPO_ADMIN, TIPO_CLIENTE

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    descricao TEXT,
    preco REAL,
    estoque INTEGER,
    categoria TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    senha TEXT,
    tipo TEXT DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    status TEXT DEFAULT 'pendente',
    total REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER REFERENCES pedidos(id),
    produto_id INTEGER REFERENCES produtos(id),
    quantidade INTEGER,
    preco_unitario REAL
);
"""

PRODUTOS_INICIAIS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Contas de demonstração sem privilégio; a senha do admin vem do ambiente.
CLIENTES_DEMO = [
    ("João Silva", "joao@email.com", "123456"),
    ("Maria Santos", "maria@email.com", "senha123"),
]

PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def conectar(caminho):
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def get_db():
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transacao():
    db = get_db()
    if db.in_transaction:
        yield db
        return
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    db.commit()


def _senha_admin_seed(config):
    if config.get("SEED_ADMIN_SENHA"):
        return config["SEED_ADMIN_SENHA"]
    logger.warning("SEED_ADMIN_SENHA não definida; admin de exemplo criado com senha aleatória")
    return secrets.token_urlsafe(16)


def _seed(db, config):
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    db.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        PRODUTOS_INICIAIS,
    )
    usuarios = [("Admin", "admin@loja.com", _senha_admin_seed(config), TIPO_ADMIN)]
    usuarios += [(nome, email, senha, TIPO_CLIENTE) for nome, email, senha in CLIENTES_DEMO]
    db.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in usuarios],
    )


def _migrar_senhas_texto_puro(db):
    rows = db.execute("SELECT id, senha FROM usuarios").fetchall()
    pendentes = [
        (generate_password_hash(row["senha"]), row["id"])
        for row in rows
        if row["senha"] and not row["senha"].startswith(PREFIXOS_HASH)
    ]
    if pendentes:
        db.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", pendentes)
        logger.info("%s senha(s) em texto puro convertidas para hash", len(pendentes))


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        with transacao():
            _seed(db, app.config)
            _migrar_senhas_texto_puro(db)
