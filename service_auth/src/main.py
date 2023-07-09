import os
import sys


sys.path.append(os.path.join(sys.path[0], 'src'))

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from api.v1 import auth, roles, users
from core.config import settings
from core.logger import LOGGING
from db import db_redis
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    db_redis.redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port
    )
    yield
    await db_redis.redis.close()


app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.api_version,
    docs_url='/api/v1/openapi',
    openapi_url='/api/v1/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(auth.router, prefix='/api/v1/auth')
app.include_router(roles.router, prefix='/auth/v1/roles')
app.include_router(users.router, prefix='/auth/v1/users')

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
