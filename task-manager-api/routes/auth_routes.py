from flask import Blueprint

from controllers import auth_controller

auth_bp = Blueprint('auth', __name__)

auth_bp.post('/login')(auth_controller.login)
