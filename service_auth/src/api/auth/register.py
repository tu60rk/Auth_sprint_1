from http import HTTPStatus
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache
from typing_extensions import Annotated
from typing import List

from src.schemas.entity import UserCreate, UserInDB

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_session
from src.models.entity import User
from fastapi.encoders import jsonable_encoder

router = APIRouter()




@router.post('/signup', response_model=UserInDB, status_code=HTTPStatus.CREATED)
async def create_user(user_create: UserCreate, db: AsyncSession = Depends(get_session)) -> UserInDB:
    user_dto = jsonable_encoder(user_create)
    user = User(**user_dto)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user