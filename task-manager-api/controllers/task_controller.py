from flask import jsonify, request

from services import report_service, task_service
from utils.validators import parse_search_filters, validate_task_create, validate_task_update


def list_tasks():
    tasks = task_service.list_tasks()
    return jsonify([task.to_dict(include_overdue=True, include_relations=True) for task in tasks]), 200


def get_task(task_id):
    task = task_service.get_task(task_id)
    return jsonify(task.to_dict(include_overdue=True)), 200


def create_task():
    fields = validate_task_create(request.get_json(silent=True))
    task = task_service.create_task(fields)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = task_service.get_task(task_id)
    fields = validate_task_update(request.get_json(silent=True))
    task_service.update_task(task, fields)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task_service.delete_task(task_service.get_task(task_id))
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    tasks = task_service.search_tasks(**parse_search_filters(request.args))
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(report_service.task_stats()), 200
