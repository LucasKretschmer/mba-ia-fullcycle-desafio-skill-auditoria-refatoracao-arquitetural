import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Settings
from src.middlewares.error_handler import register_error_handlers
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.sistema_routes import sistema_bp
from src.views.usuario_routes import usuario_bp

logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)
    if not settings.SECRET_KEY_DEFINIDA:
        logger.warning("SECRET_KEY não definida; usando chave aleatória (apenas para desenvolvimento)")

    CORS(app, origins=settings.CORS_ORIGINS)
    database.init_app(app)
    register_error_handlers(app)

    for blueprint in (sistema_bp, produto_bp, usuario_bp, pedido_bp, relatorio_bp):
        app.register_blueprint(blueprint)
    return app


def run(app):
    config = app.config
    logger.info("Servidor iniciado em http://%s:%s", config["HOST"], config["PORT"])
    app.run(host=config["HOST"], port=config["PORT"], debug=config["DEBUG"])
