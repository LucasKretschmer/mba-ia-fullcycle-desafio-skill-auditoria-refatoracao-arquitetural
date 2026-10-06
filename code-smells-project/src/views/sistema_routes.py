from flask import Blueprint

from src.controllers import sistema_controller
from src.middlewares.auth import admin_required

sistema_bp = Blueprint("sistema", __name__)

sistema_bp.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
sistema_bp.add_url_rule("/health", "health", sistema_controller.health, methods=["GET"])
sistema_bp.add_url_rule(
    "/admin/reset-db", "resetar_banco", admin_required(sistema_controller.resetar_banco), methods=["POST"]
)
sistema_bp.add_url_rule(
    "/admin/query", "executar_query", admin_required(sistema_controller.executar_query), methods=["POST"]
)
