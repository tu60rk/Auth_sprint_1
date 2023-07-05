from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.sql import select
from src.schemas.entity import UserCreate, UserInDB, LoginUserSchema

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_session
from src.models.entity import User
from werkzeug.security import check_password_hash
from core.oauth2 import AuthJWT
from core.config import settings
from datetime import timedelta
import uuid


router = APIRouter()


@router.post('/register', response_model=UserInDB, status_code=HTTPStatus.CREATED)
async def create_user(user_create: UserCreate, db: AsyncSession = Depends(get_session)) -> UserInDB:
    user_dto = jsonable_encoder(user_create)
    print(user_dto)
    user_dto['password'] = settings.SAULT + user_dto['email'] + user_dto['password']
    # добавим соли
    user = User(**user_dto)

    existing_user = await db.execute(select(User).where(User.email == user.email))
    if existing_user.scalar():
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User already registered')

    user.role_id = uuid.UUID('499be5e3-cceb-4e18-8dd6-4fbfaaa907b4')
    user.verified = True

    await db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post('/login')
async def login(
    payload: LoginUserSchema,
    response: Response,
    db: AsyncSession = Depends(get_session),
    Authorize: AuthJWT = Depends()
):  

    existing_user = await db.execute(select(User).where(User.email == payload.email))
    if not existing_user:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User not found')


    # email = form_data.username
    # password = form_data.password

    # user = await db.execute(select(User).where(User.email == email))
    # user = user.scalar()

    # if not user:
    #     raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User not found')

    # password_match = cryptoUtil.verify_password(password, user.password)
    password_match = check_password_hash(
        pwhash=existing_user.hash_password,
        password=payload.password
    )

    if not password_match:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail='Invalid password')

    access_token = Authorize.create_access_token(
        subject=str(existing_user.id),
        expires_time=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN),
        user_claims={
            'role_id': existing_user.role_id
        }
    )

    # Create refresh token
    refresh_token = Authorize.create_refresh_token(
        subject=str(existing_user.id), expires_time=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_IN))


    # access_token_expires = jwtUtil.timedelta(minutes=constantUtil.ACCESS_TOKEN_EXPIRE_MINUTE)
    # access_token = await jwtUtil.create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)

    # refresh_token_expires = jwtUtil.timedelta(days=constantUtil.REFRESH_TOKEN_EXPIRE_DAYS)
    # refresh_token = jwtUtil.create_refresh_token(data={"sub": form_data.username}, expires_delta=refresh_token_expires)

    return {
        "status": "success",
        "detail": {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
        }
    }
