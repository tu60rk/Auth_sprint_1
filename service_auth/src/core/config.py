import os
from logging import config as logging_config
from pydantic import BaseSettings

from core.logger import LOGGING


class Settings(BaseSettings):
    # Название проекта. Используется в Swagger-документации
    project_name = os.getenv("PROJECT_NAME", "Simple API for Cinema")
    project_description = os.getenv("PROJECT_DESCRIPTION", "Info about creators")
    api_version = os.getenv("API_VERSION", "1.0.0")

    # Настройка приложения
    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", 8000))

    # Настройки Redis
    redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
    redis_port = int(os.getenv("REDIS_PORT", 6379))

    # Настройка для БД
    # postgres
    dsl_database = {
        'dbname': os.getenv("POSTGRES_DB", "auth_database"),
        'user': os.getenv("POSTGRES_USER", "auth"),
        'password': os.getenv("POSTGRES_PASSWORD", None),
        'host': os.getenv("POSTGRES_HOST", "postgres"),
        'port': int(os.getenv("POSTGRES_PORT", 5432)),
    }

    # Корень проекта
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Время хранения кэша в Redis
    redis_cache_expires = 60 * 5


settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
