import re
from datetime import datetime

from config.constants import (
    COLOR_REGEX, DATE_FORMAT, DEFAULT_COLOR, DEFAULT_PRIORITY, EMAIL_REGEX, PASSWORD_MIN_LENGTH,
    PRIORITY_MAX, PRIORITY_MIN, ROLE_USER, ROLES, STATUS_PENDING, TASK_STATUSES,
    TITLE_MAX_LENGTH, TITLE_MIN_LENGTH,
)
from utils.errors import ValidationError


def require_json(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError('Dados inválidos')
    return data


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _priority(priority):
    if not is_int(priority) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return priority


def _due_date(value, message):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(message)


def _tags(tags):
    if tags is None or isinstance(tags, str):
        return tags
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return ','.join(tags)
    raise ValidationError('Tags inválidas')


def validate_task_create(data):
    require_json(data)
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')

    fields = {
        'title': _title(data['title']),
        'description': data.get('description', ''),
        'status': _status(data.get('status', STATUS_PENDING)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': data.get('user_id'),
        'category_id': data.get('category_id'),
    }
    if data.get('due_date'):
        fields['due_date'] = _due_date(data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
    if data.get('tags'):
        fields['tags'] = _tags(data['tags'])
    return fields


def validate_task_update(data):
    require_json(data)
    fields = {}
    if 'title' in data:
        fields['title'] = _title(data['title'])
    if 'description' in data:
        fields['description'] = data['description']
    if 'status' in data:
        fields['status'] = _status(data['status'])
    if 'priority' in data:
        fields['priority'] = _priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = data['user_id']
    if 'category_id' in data:
        fields['category_id'] = data['category_id']
    if 'due_date' in data:
        fields['due_date'] = _due_date(data['due_date'], 'Formato de data inválido') if data['due_date'] else None
    if 'tags' in data:
        fields['tags'] = _tags(data['tags'])
    return fields


def parse_search_filters(args):
    filters = {'query': args.get('q', ''), 'status': args.get('status', '')}
    for name in ('priority', 'user_id'):
        value = args.get(name, '')
        if value and not value.lstrip('-').isdigit():
            raise ValidationError(f'Parâmetro {name} inválido')
        filters[name] = int(value) if value else None
    return filters


def _email(email):
    if not isinstance(email, str) or not re.match(EMAIL_REGEX, email):
        raise ValidationError('Email inválido')
    return email


def _role(role):
    if role not in ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_user_create(data):
    require_json(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    _email(email)
    if not isinstance(password, str) or len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {PASSWORD_MIN_LENGTH} caracteres')
    return {'name': name, 'email': email, 'password': password, 'role': _role(data.get('role', ROLE_USER))}


def validate_user_update(data):
    require_json(data)
    fields = {}
    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name']:
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'email' in data:
        fields['email'] = _email(data['email'])
    if 'password' in data:
        if not isinstance(data['password'], str) or len(data['password']) < PASSWORD_MIN_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = data['password']
    if 'role' in data:
        fields['role'] = _role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        fields['active'] = data['active']
    return fields


def validate_login(data):
    require_json(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return {'email': email, 'password': password}


def _color(color):
    if not isinstance(color, str) or not re.match(COLOR_REGEX, color):
        raise ValidationError('Cor inválida')
    return color


def validate_category_create(data):
    require_json(data)
    if not data.get('name'):
        raise ValidationError('Nome é obrigatório')
    return {
        'name': data['name'],
        'description': data.get('description', ''),
        'color': _color(data.get('color', DEFAULT_COLOR)),
    }


def validate_category_update(data):
    require_json(data, allow_empty=True)
    fields = {key: data[key] for key in ('name', 'description', 'color') if key in data}
    if 'name' in fields and not fields['name']:
        raise ValidationError('Nome é obrigatório')
    if 'color' in fields:
        _color(fields['color'])
    return fields
