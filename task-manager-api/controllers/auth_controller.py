from flask import jsonify, request

from middlewares.auth import issue_token
from services import auth_service
from utils.validators import validate_login


def login():
    user = auth_service.authenticate(**validate_login(request.get_json(silent=True)))
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user),
    }), 200
