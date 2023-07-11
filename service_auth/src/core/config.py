import os
from logging import config as logging_config
from pydantic import BaseSettings

from src.core.logger import LOGGING


class Settings(BaseSettings):
    # Название проекта. Используется в Swagger-документации
    project_name: str = os.getenv("PROJECT_NAME", "Simple API for AUTH")
    project_description: str = os.getenv("PROJECT_DESCRIPTION", "Api's for authorisation and managing by roles.")
    api_version: str = os.getenv("API_VERSION", "1.0.0")

    # Настройка приложения
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", 8000))

    # Настройки Redis
    redis_host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))

    db_name: str = os.getenv("POSTGRES_DB", "auth_database")
    db_user: str = os.getenv("POSTGRES_USER", "auth")
    db_password: str = os.getenv("POSTGRES_PASSWORD", None)
    db_host: str = os.getenv("POSTGRES_HOST", "postgres")
    db_port: int = int(os.getenv("POSTGRES_PORT", 5432))
    dsl_database: str = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?async_fallback=True"
    # Корень проекта
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    JWT_PUBLIC_KEY: str = os.getenv('JWT_PUBLIC_KEY', None)
    JWT_PRIVATE_KEY: str = os.getenv('JWT_PRIVATE_KEY', None)
    REFRESH_TOKEN_EXPIRES_IN: int = os.getenv('REFRESH_TOKEN_EXPIRES_IN', 15)
    ACCESS_TOKEN_EXPIRES_IN: int = os.getenv('ACCESS_TOKEN_EXPIRES_IN', 60)
    JWT_ALGORITHM: str = os.getenv('ALGORITHM', 'RS256')
    SAULT: str = os.getenv('SAULT', '')


settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
