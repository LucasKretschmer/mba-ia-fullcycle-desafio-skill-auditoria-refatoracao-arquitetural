import logging

from services import user_service
from utils.errors import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)


def authenticate(email, password):
    user = user_service.find_by_email(email)
    if not user or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    logger.info('Login realizado: usuario_id=%s', user.id)
    return user
