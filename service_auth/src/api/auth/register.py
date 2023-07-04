import uuid
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from passlib.context import CryptContext
from sqlalchemy.sql import select
from src.schemas.entity import UserCreate, UserInDB
from src.utils import cryptoUtil

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_session
from src.models.entity import User

router = APIRouter(
    prefix="/api/v1"
)


@router.post('/auth/signup', response_model=UserInDB, status_code=HTTPStatus.CREATED)
async def create_user(user_create: UserCreate, db: AsyncSession = Depends(get_session)) -> UserInDB:
    user_dto = jsonable_encoder(user_create)
    user = User(**user_dto)

    existing_user = await db.execute(select(User).where(User.email == user.email))
    if existing_user.scalar():
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User already registered')

    user.password = cryptoUtil.hash_password(user.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
