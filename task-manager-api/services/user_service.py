import logging

from database import db
from models.task import Task
from models.user import User
from utils.errors import ConflictError, NotFoundError
from utils.validators import is_int

logger = logging.getLogger(__name__)


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def find_active_user(user_id):
    user = db.session.get(User, user_id) if is_int(user_id) else None
    return user if user and user.active else None


def find_by_email(email):
    return db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()


def list_users_with_task_count():
    stmt = (
        db.select(User, db.func.count(Task.id))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    return db.session.execute(stmt).all()


def _ensure_email_available(email, user_id=None):
    existing = find_by_email(email)
    if existing and existing.id != user_id:
        raise ConflictError('Email já cadastrado')


def create_user(fields):
    _ensure_email_available(fields['email'])
    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    db.session.add(user)
    db.session.commit()
    logger.info('Usuário criado: %s', user.id)
    return user


def update_user(user, fields):
    if 'email' in fields:
        _ensure_email_available(fields['email'], user.id)
    for name, value in fields.items():
        if name == 'password':
            user.set_password(value)
        else:
            setattr(user, name, value)
    db.session.commit()
    return user


def delete_user(user):
    user_id = user.id
    db.session.delete(user)
    db.session.commit()
    logger.info('Usuário deletado: %s', user_id)
