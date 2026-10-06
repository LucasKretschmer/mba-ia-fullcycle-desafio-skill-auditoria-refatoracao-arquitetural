from database import db
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError


def get_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories_with_task_count():
    stmt = (
        db.select(Category, db.func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
    )
    return db.session.execute(stmt).all()


def create_category(fields):
    category = Category(**fields)
    db.session.add(category)
    db.session.commit()
    return category


def update_category(category, fields):
    for name, value in fields.items():
        setattr(category, name, value)
    db.session.commit()
    return category


def delete_category(category):
    db.session.delete(category)
    db.session.commit()
