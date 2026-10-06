from flask import jsonify, request

from src.models import pedido_model
from src.services import pedido_service
from src.utils.validators import validar_pedido, validar_status


def criar():
    usuario_id, itens = validar_pedido(request.get_json(silent=True))
    resultado = pedido_service.criar_pedido(usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_todos():
    return jsonify({"dados": pedido_model.listar(), "sucesso": True}), 200


def listar_por_usuario(usuario_id):
    return jsonify({"dados": pedido_model.listar(usuario_id), "sucesso": True}), 200


def atualizar_status(pedido_id):
    status = validar_status(request.get_json(silent=True))
    pedido_service.atualizar_status(pedido_id, status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
