import os
import sys
import logging
import time
import random
import string


sys.path.append(os.path.join(sys.path[0], 'src'))

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from api.v1 import auth, roles, users
from core.config import settings
from core.logger import LOGGING
from db import db_redis

logging.config.fileConfig('./src/core/logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

origins = [
    "http://localhost",
    "http://localhost:8080",
]


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    logger.info(f"headers= {request.headers}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response

app.include_router(auth.router, prefix='/api/v1/auth')
app.include_router(roles.router, prefix='/api/v1/roles')
app.include_router(users.router, prefix='/api/v1/users')

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
