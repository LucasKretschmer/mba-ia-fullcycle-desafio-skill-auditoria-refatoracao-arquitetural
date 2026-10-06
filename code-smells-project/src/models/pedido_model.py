from src.config.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from src.database import get_db, transacao


def listar(usuario_id=None):
    rows = get_db().execute(
        """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.produto_id, i.quantidade, i.preco_unitario,
               COALESCE(pr.nome, 'Desconhecido') AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
        WHERE (? IS NULL OR p.usuario_id = ?)
        ORDER BY p.id, i.id
        """,
        (usuario_id, usuario_id),
    ).fetchall()

    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def existe(pedido_id):
    return get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def inserir(db, usuario_id, total, itens):
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, STATUS_PENDENTE, total),
    )
    pedido_id = cursor.lastrowid
    db.executemany(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        [(pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]) for item in itens],
    )
    return pedido_id


def atualizar_status(pedido_id, status):
    with transacao() as db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def resumo_vendas():
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(row)
