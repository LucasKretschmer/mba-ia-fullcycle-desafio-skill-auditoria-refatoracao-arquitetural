from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import TIPO_CLIENTE
from src.database import get_db, transacao

SELECT_USUARIO = "SELECT id, nome, email, tipo, criado_em FROM usuarios"


def _para_dict(row):
    return dict(row) if row else None


def listar():
    return [_para_dict(row) for row in get_db().execute(SELECT_USUARIO).fetchall()]


def buscar_por_id(usuario_id):
    return _para_dict(get_db().execute(SELECT_USUARIO + " WHERE id = ?", (usuario_id,)).fetchone())


def email_cadastrado(email):
    return get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def criar(nome, email, senha, tipo=TIPO_CLIENTE):
    with transacao() as db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def autenticar(email, senha):
    row = get_db().execute(
        "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    if row is None or not check_password_hash(row["senha"], senha):
        return None
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
