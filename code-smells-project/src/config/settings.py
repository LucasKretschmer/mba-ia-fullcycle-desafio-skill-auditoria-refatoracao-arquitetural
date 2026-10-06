import os
import secrets


def _bool(valor, padrao=False):
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


def _lista(valor):
    return [item.strip() for item in valor.split(",") if item.strip()]


class Settings:
    SECRET_KEY_DEFINIDA = bool(os.environ.get("SECRET_KEY"))
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("DEBUG"))
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = _lista(os.environ.get("CORS_ORIGINS", "http://localhost:3000"))
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    SEED_ADMIN_SENHA = os.environ.get("SEED_ADMIN_SENHA", "")
    AMBIENTE = os.environ.get("APP_ENV", "desenvolvimento")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
