from collections import Counter
from datetime import timedelta

from config.constants import (
    FINAL_STATUSES, HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_DONE,
    TASK_STATUSES,
)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services import user_service
from utils.helpers import calculate_percentage, utcnow


def _count(model, *conditions):
    return db.session.scalar(db.select(db.func.count()).select_from(model).where(*conditions))


def _count_grouped(column):
    return dict(db.session.execute(db.select(column, db.func.count()).group_by(column)).all())


def count_by_status():
    counts = _count_grouped(Task.status)
    return {status: counts.get(status, 0) for status in TASK_STATUSES}


def _overdue_tasks(now):
    stmt = (
        db.select(Task)
        .where(Task.due_date.is_not(None), Task.due_date < now, Task.status.not_in(FINAL_STATUSES))
        .order_by(Task.id)
    )
    return db.session.execute(stmt).scalars().all()


def _user_productivity():
    done_count = db.func.coalesce(db.func.sum(db.case((Task.status == STATUS_DONE, 1), else_=0)), 0)
    stmt = (
        db.select(User.id, User.name, db.func.count(Task.id), done_count)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    return [
        {
            'user_id': user_id,
            'user_name': name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        }
        for user_id, name, total, completed in db.session.execute(stmt).all()
    ]


def task_stats():
    by_status = count_by_status()
    total = _count(Task)
    return {
        'total': total,
        **by_status,
        'overdue': len(_overdue_tasks(utcnow())),
        'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
    }


def summary():
    now = utcnow()
    by_priority = _count_grouped(Task.priority)
    overdue = _overdue_tasks(now)
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': _count(Task),
            'total_users': _count(User),
            'total_categories': _count(Category),
        },
        'tasks_by_status': count_by_status(),
        'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': _count(Task, Task.created_at >= since),
            'tasks_completed_last_7_days': _count(Task, Task.status == STATUS_DONE, Task.updated_at >= since),
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user_id):
    user = user_service.get_user(user_id)
    tasks = user.tasks
    now = utcnow()
    by_status = Counter(task.status for task in tasks)

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': len(tasks),
            **{status: by_status.get(status, 0) for status in TASK_STATUSES},
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(by_status.get(STATUS_DONE, 0), len(tasks)),
        },
    }
