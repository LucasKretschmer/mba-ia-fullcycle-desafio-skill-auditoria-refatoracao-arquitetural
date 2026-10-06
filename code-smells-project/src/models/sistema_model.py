import sqlite3
from pathlib import Path

from flask import current_app

from src.database import get_db, transacao


def contar_registros():
    row = get_db().execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    ).fetchone()
    return dict(row)


def resetar():
    with transacao() as db:
        db.execute("DELETE FROM itens_pedido")
        db.execute("DELETE FROM pedidos")
        db.execute("DELETE FROM produtos")
        db.execute("DELETE FROM usuarios")


def consultar_somente_leitura(sql):
    uri = Path(current_app.config["DATABASE_PATH"]).resolve().as_uri() + "?mode=ro"
    conexao = sqlite3.connect(uri, uri=True)
    conexao.row_factory = sqlite3.Row
    try:
        cursor = conexao.execute(sql)
        if cursor.description is None:
            return None
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conexao.close()
