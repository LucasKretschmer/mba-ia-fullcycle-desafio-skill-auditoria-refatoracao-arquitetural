import logging
import sqlite3

from flask import current_app, jsonify, request

from src.config.constants import VERSAO_API
from src.models import sistema_model
from src.utils.errors import ValidationError

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSAO_API,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": sistema_model.contar_registros(),
        "versao": VERSAO_API,
        "ambiente": current_app.config["AMBIENTE"],
    }), 200


def resetar_banco():
    sistema_model.resetar()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = request.get_json(silent=True)
    sql = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not sql:
        raise ValidationError("Query não informada")
    try:
        resultado = sistema_model.consultar_somente_leitura(sql)
    except sqlite3.Error:
        raise ValidationError("Query inválida ou não permitida (somente leitura)")
    if resultado is None:
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    return jsonify({"dados": resultado, "sucesso": True}), 200
