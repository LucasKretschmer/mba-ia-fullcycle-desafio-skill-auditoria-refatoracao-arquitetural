from collections import Counter

from src.database import transacao
from src.models import pedido_model, produto_model, usuario_model
from src.services import notificacao_service
from src.utils.errors import NotFoundError, ValidationError


def criar_pedido(usuario_id, itens):
    with transacao() as db:
        if usuario_model.buscar_por_id(usuario_id) is None:
            raise ValidationError("Usuário não encontrado")

        produtos = produto_model.buscar_por_ids(item["produto_id"] for item in itens)
        quantidade_por_produto = Counter()
        total = 0
        itens_pedido = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
            quantidade_por_produto[produto["id"]] += item["quantidade"]
            if produto["estoque"] < quantidade_por_produto[produto["id"]]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"])
            total += produto["preco"] * item["quantidade"]
            itens_pedido.append({**item, "preco_unitario": produto["preco"]})

        pedido_id = pedido_model.inserir(db, usuario_id, total, itens_pedido)
        for produto_id, quantidade in quantidade_por_produto.items():
            produto_model.baixar_estoque(db, produto_id, quantidade)

    notificacao_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, status):
    if not pedido_model.existe(pedido_id):
        raise NotFoundError("Pedido não encontrado")
    pedido_model.atualizar_status(pedido_id, status)
    notificacao_service.status_alterado(pedido_id, status)
