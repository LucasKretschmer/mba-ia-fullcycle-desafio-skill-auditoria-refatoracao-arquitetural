import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"erro": error.description, "sucesso": False}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
