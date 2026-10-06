import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)

HTTP_ERROR_MESSAGES = {
    400: 'Dados inválidos',
    404: 'Recurso não encontrado',
    405: 'Método não permitido',
    415: 'Dados inválidos',
}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({'error': HTTP_ERROR_MESSAGES.get(error.code, error.description)}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
