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

from api.v1 import auth #, loginout
from core.config import settings
from core.logger import LOGGING
from db import postgres
from src.db.postgres import get_session
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    redis_url = f'redis://{settings.redis_host}:{settings.redis_port}'
    redis = aioredis.from_url(redis_url)
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')

    yield

    await redis.close()


app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.api_version,
    docs_url='/api/v1/openapi',
    openapi_url='/api/v1/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Подключаем роутер к серверу, указав префикс /v1/films
# Теги указываем для удобства навигации по документации
app.include_router(auth.router, prefix='/api/v1/auth')
# app.include_router(loginout.router, prefix='auth/v1/loginout')


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
