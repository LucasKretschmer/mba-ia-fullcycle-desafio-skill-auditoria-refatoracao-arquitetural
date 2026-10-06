from flask import jsonify, request

from config.constants import PRIVILEGED_USER_FIELDS, ROLE_USER
from middlewares.auth import require_auth
from services import user_service
from utils.validators import validate_user_create, validate_user_update


def list_users():
    rows = user_service.list_users_with_task_count()
    return jsonify([{**user.to_dict(), 'task_count': task_count} for user, task_count in rows]), 200


def get_user(user_id):
    user = user_service.get_user(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in user.tasks]
    return jsonify(data), 200


def create_user():
    fields = validate_user_create(request.get_json(silent=True))
    if fields['role'] != ROLE_USER:
        require_auth(admin=True)
    user = user_service.create_user(fields)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = user_service.get_user(user_id)
    fields = validate_user_update(request.get_json(silent=True))
    if any(name in fields for name in PRIVILEGED_USER_FIELDS):
        require_auth(admin=True)
    user_service.update_user(user, fields)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user_service.delete_user(user_service.get_user(user_id))
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user = user_service.get_user(user_id)
    return jsonify([task.to_summary_dict() for task in user.tasks]), 200
