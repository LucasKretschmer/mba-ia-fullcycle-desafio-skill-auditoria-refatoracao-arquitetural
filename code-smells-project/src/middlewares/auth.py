import hmac
from functools import wraps

from flask import current_app, request

from src.utils.errors import ForbiddenError


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN")
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(recebido, esperado):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)
    return wrapper
