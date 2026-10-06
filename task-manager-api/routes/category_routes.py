from flask import Blueprint

from controllers import category_controller
from middlewares.auth import login_required

category_bp = Blueprint('categories', __name__)

category_bp.get('/categories')(category_controller.list_categories)
category_bp.post('/categories')(category_controller.create_category)
category_bp.put('/categories/<int:category_id>')(category_controller.update_category)
category_bp.delete('/categories/<int:category_id>')(login_required(category_controller.delete_category))
