import logging

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.errors import NotFoundError
from utils.helpers import utcnow
from utils.validators import is_int

logger = logging.getLogger(__name__)


def _find(model, ident):
    return db.session.get(model, ident) if is_int(ident) else None


def _ensure_references(user_id, category_id):
    if user_id and not _find(User, user_id):
        raise NotFoundError('Usuário não encontrado')
    if category_id and not _find(Category, category_id):
        raise NotFoundError('Categoria não encontrada')


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def list_tasks():
    stmt = (
        db.select(Task)
        .options(db.joinedload(Task.user), db.joinedload(Task.category))
        .order_by(Task.id)
    )
    return db.session.execute(stmt).scalars().all()


def search_tasks(query='', status='', priority=None, user_id=None):
    stmt = db.select(Task)
    if query:
        stmt = stmt.where(db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%')))
    if status:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if user_id is not None:
        stmt = stmt.where(Task.user_id == user_id)
    return db.session.execute(stmt.order_by(Task.id)).scalars().all()


def create_task(fields):
    _ensure_references(fields.get('user_id'), fields.get('category_id'))
    task = Task(**fields)
    db.session.add(task)
    db.session.commit()
    logger.info('Task criada: %s', task.id)
    return task


def update_task(task, fields):
    _ensure_references(fields.get('user_id'), fields.get('category_id'))
    for name, value in fields.items():
        setattr(task, name, value)
    task.updated_at = utcnow()
    db.session.commit()
    logger.info('Task atualizada: %s', task.id)
    return task


def delete_task(task):
    task_id = task.id
    db.session.delete(task)
    db.session.commit()
    logger.info('Task deletada: %s', task_id)
