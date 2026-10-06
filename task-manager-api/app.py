import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.auth_routes import auth_bp
from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)
    if settings.SECRET_KEY_GENERATED:
        logger.warning('SECRET_KEY não definida: usando chave temporária, válida só para desenvolvimento')

    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)
    register_error_handlers(app)

    for blueprint in (health_bp, task_bp, user_bp, auth_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    create_app().run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
