import logging

from flask import jsonify, request

from src.models import produto_model
from src.utils.errors import ConflictError, NotFoundError
from src.utils.validators import converter_preco, validar_produto

logger = logging.getLogger(__name__)


def _produto_ou_404(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto


def listar():
    return jsonify({"dados": produto_model.listar(), "sucesso": True}), 200


def detalhar(produto_id):
    return jsonify({"dados": _produto_ou_404(produto_id), "sucesso": True}), 200


def buscar():
    resultados = produto_model.buscar(
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=converter_preco(request.args.get("preco_min"), "preco_min"),
        preco_max=converter_preco(request.args.get("preco_max"), "preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar():
    dados = validar_produto(request.get_json(silent=True))
    novo_id = produto_model.criar(**dados)
    logger.info("Produto criado com id=%s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(produto_id):
    _produto_ou_404(produto_id)
    dados = validar_produto(request.get_json(silent=True))
    produto_model.atualizar(produto_id, **dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(produto_id):
    _produto_ou_404(produto_id)
    if produto_model.possui_pedidos(produto_id):
        raise ConflictError("Produto possui pedidos e não pode ser removido")
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
