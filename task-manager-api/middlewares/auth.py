from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from services import user_service
from utils.errors import ForbiddenError, UnauthorizedError

TOKEN_SALT = 'auth-token'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def issue_token(user):
    return _serializer().dumps({'user_id': user.id})


def _user_from_request():
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme.lower() != 'bearer' or not token:
        return None
    try:
        payload = _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE'])
    except BadSignature:
        return None
    return user_service.find_active_user(payload.get('user_id'))


def require_auth(admin=False):
    user = _user_from_request()
    if not user:
        raise UnauthorizedError('Token inválido ou ausente')
    if admin and not user.is_admin():
        raise ForbiddenError('Acesso negado')
    g.current_user = user
    return user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        require_auth()
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        require_auth(admin=True)
        return view(*args, **kwargs)
    return wrapper
