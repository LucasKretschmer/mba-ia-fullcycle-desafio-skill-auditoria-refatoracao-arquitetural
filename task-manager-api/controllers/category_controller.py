from flask import jsonify, request

from services import category_service
from utils.validators import validate_category_create, validate_category_update


def list_categories():
    rows = category_service.list_categories_with_task_count()
    return jsonify([{**category.to_dict(), 'task_count': task_count} for category, task_count in rows]), 200


def create_category():
    fields = validate_category_create(request.get_json(silent=True))
    category = category_service.create_category(fields)
    return jsonify(category.to_dict()), 201


def update_category(category_id):
    category = category_service.get_category(category_id)
    fields = validate_category_update(request.get_json(silent=True))
    category_service.update_category(category, fields)
    return jsonify(category.to_dict()), 200


def delete_category(category_id):
    category_service.delete_category(category_service.get_category(category_id))
    return jsonify({'message': 'Categoria deletada'}), 200
