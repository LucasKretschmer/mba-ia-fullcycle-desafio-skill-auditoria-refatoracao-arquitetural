import logging

from src.config.constants import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação (email/sms/push): pedido %s criado para usuario_id=%s", pedido_id, usuario_id)


def status_alterado(pedido_id, status):
    if status == STATUS_APROVADO:
        logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)
    elif status == STATUS_CANCELADO:
        logger.info("Notificação: pedido %s cancelado, devolver estoque", pedido_id)
