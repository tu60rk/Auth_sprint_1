import os
import sys


sys.path.append(os.path.join(sys.path[0], 'src'))

from contextlib import asynccontextmanager

import uvicorn
# from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from src.api.auth import register, loginout
from src.core.config import settings
from src.core.logger import LOGGING
from src.db import postgres
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    # postgres_url = f'http://{settings.postgres_host}:{settings.postgres_port}'
    redis_url = f'redis://{settings.redis_host}:{settings.redis_port}'

    # load services
    # elastic.es = AsyncElasticsearch(hosts=[es_url])
    from src.models.entity import User
    from src.db.postgres import create_database

    await create_database()
    redis = aioredis.from_url(redis_url)
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')

    yield

    # close services and release the resources
    # await elastic.elastic.close()
    await redis.close()


app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.api_version,
    docs_url='/auth/openapi',
    openapi_url='/auth/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Подключаем роутер к серверу, указав префикс /v1/films
# Теги указываем для удобства навигации по документации
app.include_router(register.router, prefix='')
app.include_router(loginout.router, prefix='')


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
