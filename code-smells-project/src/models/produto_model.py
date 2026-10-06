from src.database import get_db, transacao

SELECT_PRODUTO = "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos"


def _para_dict(row):
    return dict(row) if row else None


def listar():
    return [_para_dict(row) for row in get_db().execute(SELECT_PRODUTO).fetchall()]


def buscar_por_id(produto_id):
    return _para_dict(get_db().execute(SELECT_PRODUTO + " WHERE id = ?", (produto_id,)).fetchone())


def buscar_por_ids(produto_ids):
    ids = list(set(produto_ids))
    marcadores = ", ".join("?" for _ in ids)
    rows = get_db().execute(SELECT_PRODUTO + f" WHERE id IN ({marcadores})", ids).fetchall()
    return {row["id"]: _para_dict(row) for row in rows}


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    query = SELECT_PRODUTO + " WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)
    return [_para_dict(row) for row in get_db().execute(query, params).fetchall()]


def criar(nome, descricao, preco, estoque, categoria):
    with transacao() as db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    with transacao() as db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def possui_pedidos(produto_id):
    row = get_db().execute("SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)).fetchone()
    return row is not None


def deletar(produto_id):
    with transacao() as db:
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(db, produto_id, quantidade):
    db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))
