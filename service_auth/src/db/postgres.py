from src.core.config import settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


# Создаём движок
# Настройки подключения к БД передаём из переменных окружения, которые заранее загружены в файл настроек
engine = create_async_engine(
    settings.dsl_database,
    echo=True,
    future=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
