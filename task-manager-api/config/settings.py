import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _list(value):
    return [item.strip() for item in value.split(',') if item.strip()]


class Settings:
    SECRET_KEY_GENERATED = not os.environ.get('SECRET_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get('DEBUG'))
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = _list(os.environ.get('CORS_ORIGINS', 'http://localhost:3000'))
    TOKEN_MAX_AGE = int(os.environ.get('TOKEN_MAX_AGE', '28800'))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
