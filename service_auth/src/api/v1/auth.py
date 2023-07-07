import json

from datetime import timedelta
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.sql import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import check_password_hash
from redis.asyncio import Redis

from src.db.postgres import get_session
from src.db.db_redis import get_redis
from src.models.entity import User, Role, AccountHistory, RefreshToken
from src.schemas.entity import UserCreate, UserInDB, LoginUserSchema
from core.oauth2 import AuthJWT
from core.config import settings
from src.utils.oauth2 import get_current_user


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
    redis: Redis = Depends(get_redis),
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

    # create access token
    access_token = Authorize.create_access_token(
        subject=str(existing_user.id),
        expires_time=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN),
        user_claims={
            "role_id" : str(existing_user.role_id),
            "email" : existing_user.email
        }
    )
    # save access token
    redis_user = await redis.get(str(existing_user.id))
    values = json.loads(redis_user) if redis_user else []
    values.append(access_token)
    
    await redis.set(
        name=str(existing_user.id),
        value=json.dumps(values),
        ex=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN)
    )

    # create refresh token
    refresh_token = Authorize.create_refresh_token(
        subject=str(existing_user.id), expires_time=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_IN))

    # save refresh token
    data_refresh_token = RefreshToken(
        user_id=existing_user.id,
        user_token=refresh_token,
        is_active=True
    )
    db.add(data_refresh_token)
    await db.commit()
    await db.refresh(data_refresh_token)
        
    # add data to account history
    data_header = AccountHistory(
        user_id=existing_user.id,
        user_agent=request.headers.get('user-agent')
    )
    db.add(data_header)
    await db.commit()
    await db.refresh(data_header)

    # set cookie
    if payload.set_cookie:
        response.set_cookie('access_token', access_token, settings.ACCESS_TOKEN_EXPIRES_IN, settings.ACCESS_TOKEN_EXPIRES_IN, '/', None, False, True, 'lax')
        response.set_cookie('refresh_token', refresh_token, settings.REFRESH_TOKEN_EXPIRES_IN, settings.REFRESH_TOKEN_EXPIRES_IN, '/', None, False, True, 'lax')

    return {
        "status": "success",
        "detail": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    }


@router.post('/refresh')
async def refresh(
    refresh_token: str,
    Authorize: AuthJWT = Depends(),
    db: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    # проверка токена
    Authorize._verify_jwt_in_request(
        token=refresh_token,
        type_token='refresh',
        token_from='headers'
    )

    data_token = Authorize.get_raw_jwt(refresh_token)
    current_user = data_token.get('sub')
    
    existing_user = await db.execute(select(User).where(User.id == current_user))
    existing_user = existing_user.scalar()
    if not existing_user:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User not found')
    
    if not existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    
    # create access token
    access_token = Authorize.create_access_token(
        subject=str(current_user),
        expires_time=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN),
        user_claims={
            "role_id" : str(existing_user.role_id),
            "email" : existing_user.email
        }
    )

    # save access token - это не совсем верно. Нужно пересмотреть логику. Нам нужно старый токен из этого списка удалить. Как вариант хранить user_agent как ключ, а его значение токен
    redis_user = await redis.get(str(existing_user.id))
    values = json.loads(redis_user) if redis_user else []
    values.append(access_token)
    
    await redis.set(
        name=str(existing_user.id),
        value=json.dumps(values),
        ex=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN)
    )

    # change status for refresh token
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_token == refresh_token)
        .values(is_active=False)
    )
    await db.commit()
    # create a refresh token
    new_refresh_token = Authorize.create_refresh_token(
        subject=str(existing_user.id), expires_time=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_IN))
    
    # save a refresh token
    data_refresh_token = RefreshToken(
        user_id=existing_user.id,
        user_token=new_refresh_token,
        is_active=True
    )
    db.add(data_refresh_token)
    await db.commit()
    await db.refresh(data_refresh_token)
    
    return {
        "status": "success",
        "detail": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    }

@router.get("/users/me", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user
