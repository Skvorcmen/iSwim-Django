import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Пытаемся загрузить .env файл (безопасно)
env = environ.Env()
try:
    environ.Env.read_env(BASE_DIR / '.env')
except FileNotFoundError:
    pass  # В production переменные должны быть в окружении

SECRET_KEY = env('SECRET_KEY')  # Обязательно должна быть
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# ... остальной код settings.py
