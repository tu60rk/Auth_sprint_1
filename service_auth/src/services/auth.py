import json
import logging

from functools import lru_cache
from typing import Optional
from http import HTTPStatus
from fastapi import Depends, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import true, false
from redis.asyncio import Redis
from werkzeug.security import check_password_hash
from datetime import timedelta

from src.db.postgres import get_session, DbService
from src.db.db_redis import get_redis, RedisService
from src.schemas.entity import Status, UserInDB, Tokens
from src.models.entity import (
    Role, User, UserRoles, RefreshToken, AccountHistory
)
from src.core.config import settings
from core.oauth2 import AuthJWT
from .abstracts import AsyncAuthService

logging.config.fileConfig('./src/core/logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class AuthService(AsyncAuthService):
    def __init__(
        self,
        db_service: DbService,
        redis_service: RedisService,
        Authorize: AuthJWT
    ) -> None:
        self.redis_service = redis_service
        self.Authorize = Authorize
        self.db_service = db_service

    async def __create_tokens(
        self,
        subject: str,
        is_ex: bool = True,
        user_claims: dict = {},
    ) -> Tokens:

        logger.info(f"""Start to create tokens. Params:
        subject - {subject},
        is_ex - {is_ex},
        user_claims - {user_claims}
        """)
        params_for_access = {
            'subject': subject,
            'user_claims': user_claims
        }

        params_for_refresh = {
            'subject': subject,
        }

        if is_ex:
            params_for_access.update(
                {
                    "expires_time": timedelta(
                        minutes=settings.ACCESS_TOKEN_EXPIRES_IN
                    )
                }
            )

            params_for_refresh.update(
                {
                    "expires_time": timedelta(
                        days=settings.REFRESH_TOKEN_EXPIRES_IN
                    )
                }
            )

        access_token = await self.Authorize.create_access_token(
            **params_for_access
        )
        refresh_token = await self.Authorize.create_refresh_token(
            **params_for_access
        )
        logger.info(msg="Finish to create tokens")
        return Tokens(access_token=access_token, refresh_token=refresh_token)

    async def __create_roles(self) -> None:
        logger.info(msg="Start to create default roles. No params.")
        user_role = Role(
            name='user',
            description='user'
        )
        admin_role = Role(
            name='admin',
            description='admin'
        )

        await self.db_service.insert_data(user_role)
        await self.db_service.insert_data(admin_role)
        logger.info(msg="Finish to create default roles")

    async def __check_user_exist_active(
        self,
        by: str,
        data: str
    ) -> Optional[HTTPStatus]:
        logger.info(f"""Start to check user exist.
        Params: by - {by}, data - {data}""")
        where_list = []
        if by == 'email':
            where_list = [User.email, data]
        else:
            where_list = [User.id, data]
        existing_user = await self.db_service.simple_select(
            what_select=User,
            where_select=where_list
        )
        if len(existing_user) == 0:
            return HTTPStatus.CONFLICT
        if not existing_user[0].is_active:
            return HTTPStatus.BAD_REQUEST

        logger.info(msg="Finish to check user exist")
        return existing_user[0]

    async def create_user(self, user_info: UserInDB) -> Optional[UserInDB]:
            logger.info(f'Start to create user. Params: user_info - {user_info}')
        # try:
            user_dto = jsonable_encoder(user_info)
            user_dto['password'] = settings.SAULT + user_dto['email'] + user_dto['password']
            user = User(**user_dto)

            roles = await self.db_service.simple_select(
                what_select=Role.id,
                where_select=[Role.name, 'user']
            )

            if len(roles) == 0:
                await self.__create_roles()
                roles = await self.db_service.simple_select(
                    what_select=Role.id,
                    where_select=[Role.name, 'user']
                )

            existing_user = await self.db_service.simple_select(
                what_select=User,
                where_select=[User.email, user.email]
            )
            if len(existing_user) > 0:
                logger.info(msg="Couldn't create user because of email exist.")
                return HTTPStatus.CONFLICT

            user.verified = True
            await self.db_service.insert_data(data=user)
            await self.db_service.simple_insert(
                what_insert=UserRoles,
                values_insert={
                    'user_id': user.id,
                    'role_id': roles[0]
                }
            )
            logger.info(msg="Finish to create user")
            return user
        # except Exception as err:
        #     logger.error(msg=f"Couldn't create user. Error - {err}")
        #     return None

    async def login(
        self,
        user_agent: str,
        email: str,
        passwd: str,
        set_cookie: bool,
        response: Response
    ) -> Tokens:
        try:
            logger.info(f"""Start User login. Params:
            user_agent - {user_agent},
            email - {email},
            set_cookie - {set_cookie},
            response - {response}
            """)
            existing_user = await self.__check_user_exist_active(
                by='email',
                data=email
            )
            if existing_user in [HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST]:
                logger.info(msg="User didn't go a checking")
                return existing_user

            password_match = check_password_hash(
                pwhash=existing_user.hash_password,
                password=settings.SAULT + existing_user.email + passwd
            )

            if not password_match:
                logger.info(msg="Password didn't match")
                return HTTPStatus.UNAUTHORIZED

            user_roles = await self.db_service.get_user_roles(
                user_id=existing_user.id
            )

            # create access and refresh tokens
            tokens = await self.__create_tokens(
                subject=str(existing_user.id),
                is_ex=True,
                user_claims={
                    "roles": user_roles,
                    "email": existing_user.email
                }
            )

            # save access token
            await self.redis_service.add_token(
                user_id=str(existing_user.id),
                access_token=tokens.access_token,
                user_agent=user_agent
            )
            # save refresh token
            data_refresh_token = RefreshToken(
                user_id=existing_user.id,
                user_token=tokens.refresh_token,
                is_active=true(),
                user_agent=user_agent
            )
            await self.db_service.insert_data(data_refresh_token)
            # add data to account history
            data_header = AccountHistory(
                user_id=existing_user.id,
                user_agent=user_agent
            )
            await self.db_service.insert_data(data_header)
            # set cookie
            if set_cookie:
                response.set_cookie('access_token', tokens.access_token, settings.ACCESS_TOKEN_EXPIRES_IN, settings.ACCESS_TOKEN_EXPIRES_IN, '/', None, False, True, 'lax')
                response.set_cookie('refresh_token', tokens.refresh_token, settings.REFRESH_TOKEN_EXPIRES_IN, settings.REFRESH_TOKEN_EXPIRES_IN, '/', None, False, True, 'lax')
            logger.info(msg="Finish User login")
        except Exception as err:
            logger.error(msg=f"User can't login. Err - {err}")
            return None
        return tokens

    async def refresh(self, refresh_token: str, user_agent: str) -> Tokens:
        # check token
        try:
            logger.info(msg="Start to refresh tokens")
            await self.Authorize._verify_jwt_in_request(
                token=refresh_token,
                type_token='refresh',
                token_from='headers'
            )

            # check user
            data_token = await self.Authorize.get_raw_jwt(refresh_token)
            sub = data_token.get('sub')
            existing_user = await self.__check_user_exist_active(
                by='user',
                data=sub
            )
            if existing_user in [HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST]:
                return existing_user

            # create access and refresh tokens
            user_roles = await self.db_service.get_user_roles(
                user_id=existing_user.id
            )
            tokens = await self.__create_tokens(
                subject=str(existing_user.id),
                is_ex=True,
                user_claims={
                    "roles": user_roles,
                    "email": existing_user.email
                }
            )

            # add access token in redis
            await self.redis_service.add_token(
                user_id=str(existing_user.id),
                access_token=tokens.access_token,
                user_agent=user_agent
            )

            # change status for refresh token
            await self.db_service.simple_update(
                what_update=RefreshToken,
                where_update=[RefreshToken.user_token, refresh_token],
                values_update={'is_active': false()}
            )
            # save a refresh token
            data_refresh_token = RefreshToken(
                user_id=existing_user.id,
                user_token=tokens.refresh_token,
                is_active=True
            )
            await self.db_service.insert_data(data_refresh_token)
            logger.info(msg="Finish to refresh tokens")
        except Exception as err:
            logger.error(msg=f"Couldn't refresh tokens. Err - {err}")
            return None
        return tokens

    async def logout_all(self, user_id: str) -> Status:
        try:
            logger.info(f"Start to logout all. Params: user_id - {user_id}")
            await self.redis_service.delete(user_id)
            await self.db_service.simple_update(
                what_update=RefreshToken,
                where_update=[RefreshToken.user_id, user_id],
                values_update={'is_active': false()}
            )
            logger.info(msg="Finish to logout all")
        except Exception as err:
            logger.error(msg=f"Couldn't logout all. Err - {err}")
            return None
        return Status(status='success')

    async def logout_me(self, user_id: str, user_agent: str) -> Status:
        try:
            logger.info(f"""Start to logout me. Params:
            user_id - {user_id},
            user_agent - {user_agent}
            """)
            current_user_tokens = await self.redis_service.get(user_id)
            current_user_tokens.pop(user_agent)

            if len(current_user_tokens) == 0:
                await self.redis_service.delete(user_id)
            else:
                await self.redis_service.set(
                    name=user_id,
                    value=json.dumps(current_user_tokens),
                )

            await self.db_service.update_token(
                what_update=RefreshToken,
                where_update={
                    'user_id': user_id,
                    'user_agent': user_agent,
                    'is_active': true()
                },
                values_update={'is_active': false()}
            )
            logger.info(msg="Finish to logout me")
        except Exception as err:
            logger.error(msg=f"Couldn't logout me. Err - {err}")
            return None

        return Status(status='success')


@lru_cache()
def auth_service(
    db: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
    Authorize: AuthJWT = Depends()
) -> AuthService:
    return AuthService(
        db_service=DbService(db=db),
        redis_service=RedisService(redis=redis),
        Authorize=Authorize,
    )
