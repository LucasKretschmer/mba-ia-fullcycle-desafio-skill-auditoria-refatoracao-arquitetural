from flask import Blueprint

from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)

produto_bp.add_url_rule("/produtos", "listar", produto_controller.listar, methods=["GET"])
produto_bp.add_url_rule("/produtos/busca", "buscar", produto_controller.buscar, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "detalhar", produto_controller.detalhar, methods=["GET"])
produto_bp.add_url_rule("/produtos", "criar", produto_controller.criar, methods=["POST"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "atualizar", produto_controller.atualizar, methods=["PUT"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "deletar", produto_controller.deletar, methods=["DELETE"])
