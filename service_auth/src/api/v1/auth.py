from datetime import timedelta
from typing import Annotated
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Response, Header, Request
from sqlalchemy.sql import select
from src.schemas.entity import UserCreate, UserInDB, LoginUserSchema

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_session
from src.models.entity import User, Role, AccountHistory, RefreshToken
from werkzeug.security import check_password_hash
from core.oauth2 import AuthJWT
from core.config import settings


router = APIRouter()


@router.post('/register', response_model=UserInDB, status_code=HTTPStatus.CREATED)
async def create_user(user_create: UserCreate, db: AsyncSession = Depends(get_session)) -> UserInDB:
    user_dto = jsonable_encoder(user_create)
    user_dto['password'] = settings.SAULT + user_dto['email'] + user_dto['password']
    user = User(**user_dto)

    existing_user = await db.execute(select(User).where(User.email == user.email))
    if existing_user.scalar():
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User already registered')

    existing_user = await db.execute(select(Role).where(Role.name == 'user'))
    user.role_id = existing_user.scalar().id
    user.verified = True

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post('/login', status_code=HTTPStatus.ACCEPTED)
async def login(
    payload: LoginUserSchema,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_session),
    Authorize: AuthJWT = Depends(),
):

    existing_user = await db.execute(select(User).where(User.email == payload.email))
    if not existing_user:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User not found')
    
    existing_user = existing_user.scalar()
    password_match = check_password_hash(
        pwhash=existing_user.hash_password,
        password=settings.SAULT + existing_user.email + payload.password
    )

    if not password_match:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail='Invalid password')

    access_token = Authorize.create_access_token(
        subject=str(existing_user.id),
        expires_time=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN),
        user_claims={
        }
    )

    refresh_token = Authorize.create_refresh_token(
        subject=str(existing_user.id), expires_time=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_IN))

    # save refresh token пока не работает
    data_refresh_token = RefreshToken(
        user_id=existing_user.id,
        user_token=refresh_token,
        is_active=True
    )
    db.add(data_refresh_token)
    await db.commit()
    await db.refresh(data_refresh_token)

    # save access token


    # add data to account history
    data_header = AccountHistory(
        user_id=existing_user.id,
        user_agent=request.headers.get('user-agent')
    )

    db.add(data_header)
    await db.commit()
    await db.refresh(data_header)

    if payload.set_cookie:
        response.set_cookie('access_token', access_token, settings.ACCESS_TOKEN_EXPIRES_IN, settings.ACCESS_TOKEN_EXPIRES_IN, '/', None, False, True, 'lax')
        response.set_cookie('refresh_token', refresh_token, settings.REFRESH_TOKEN_EXPIRES_IN, settings.REFRESH_TOKEN_EXPIRES_IN, '/', None, False, True, 'lax')

    return {
        "status": "success",
        "detail": {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
        }
    }
