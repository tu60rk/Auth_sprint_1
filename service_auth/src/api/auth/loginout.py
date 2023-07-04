from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from src.db.postgres import get_session
from src.models.entity import User
from src.schemas.entity import ForgotPassword
from src.utils import constantUtil, cryptoUtil, jwtUtil

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/v1")

@router.post('/auth/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    email = form_data.username
    password = form_data.password

    user = await db.execute(select(User).where(User.email == email))
    user = user.scalar()

    if not user:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User not found')

    password_match = cryptoUtil.verify_password(password, user.password)

    if not password_match:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail='Invalid password')

    access_token_expires = jwtUtil.timedelta(minutes=constantUtil.ACCESS_TOKEN_EXPIRE_MINUTE)
    access_token = await jwtUtil.create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)

    refresh_token_expires = jwtUtil.timedelta(days=constantUtil.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = jwtUtil.create_refresh_token(data={"sub": form_data.username}, expires_delta=refresh_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user_info": {
            "email": user.email,
        }
    }


@router.post('/auth/refresh-token')
async def refresh_token(refresh_token: str = Query(..., alias='refresh_token')):
    decoded_token = jwtUtil.decode_token(refresh_token)

    if "sub" not in decoded_token:
        raise HTTPException(status_code=HTTPStatus.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = decoded_token["sub"]
    async with get_session() as db:
        user = await db.execute(select(User).where(User.email == email))
        user = user.scalar()

        if not user:
            raise HTTPException(status_code=HTTPStatus.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token_expires = jwtUtil.timedelta(minutes=constantUtil.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwtUtil.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/auth/forgot-password')
async def forgot_password(request: ForgotPassword, db: AsyncSession = Depends(get_session)):
    email = request.email

    user = await db.execute(select(User).where(User.email == email))
    user = user.scalar()

    if not user:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='User not found')

    return "forgot password"


@router.post('/auth/logout')
async def logout():
    return {"message": "Logged out successfully"}
