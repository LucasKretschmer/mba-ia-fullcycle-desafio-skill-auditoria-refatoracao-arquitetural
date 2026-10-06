from flask import Blueprint

from src.controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__)

usuario_bp.add_url_rule("/usuarios", "listar", usuario_controller.listar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios/<int:usuario_id>", "detalhar", usuario_controller.detalhar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios", "criar", usuario_controller.criar, methods=["POST"])
usuario_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])
