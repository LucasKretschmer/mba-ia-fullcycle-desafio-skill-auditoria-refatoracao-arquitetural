import logging

from flask import jsonify, request

from src.models import usuario_model
from src.utils.errors import AppError, NotFoundError, ValidationError
from src.utils.validators import validar_login, validar_usuario

logger = logging.getLogger(__name__)


def listar():
    return jsonify({"dados": usuario_model.listar(), "sucesso": True}), 200


def detalhar(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar():
    dados = validar_usuario(request.get_json(silent=True))
    if usuario_model.email_cadastrado(dados["email"]):
        raise ValidationError("Email já cadastrado")
    novo_id = usuario_model.criar(dados["nome"], dados["email"], dados["senha"])
    logger.info("Usuário criado com id=%s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    email, senha = validar_login(request.get_json(silent=True))
    usuario = usuario_model.autenticar(email, senha)
    if usuario is None:
        logger.info("Falha de login")
        raise AppError("Email ou senha inválidos", 401)
    logger.info("Login bem-sucedido para usuario_id=%s", usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
