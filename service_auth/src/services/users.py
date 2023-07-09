import uuid 

from functools import lru_cache
from typing import List, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, insert, update, delete
from werkzeug.security import check_password_hash, generate_password_hash

from src.db.postgres import get_session
from src.schemas.entity import ShemaAccountHistory, Status, UserInDB
from src.models.entity import AccountHistory, User
from src.core.config import settings


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_account_history(
        self,
        user_id: uuid
    ) -> Optional[List[ShemaAccountHistory]]:

        account_history = await self.db.execute(
            select(AccountHistory)
            .where(AccountHistory.user_id == user_id)
            .order_by(AccountHistory.created_at.desc())
        )
        return [
            ShemaAccountHistory(
                user_agent=login.user_agent,
                created_at=login.created_at
            )
            for login in account_history.scalars()
        ]

    async def change_password(
        self,
        current_password: str,
        password: str,
        user_info: UserInDB
    ) -> Status:

        user = await self.db.execute(
            select(User)
            .where(User.email == user_info.email)
        )
        user = user.scalar()

        password_match = check_password_hash(
            pwhash=user.hash_password,
            password=settings.SAULT + user.email + current_password
        )

        if not password_match:
            return None

        user.hash_password = generate_password_hash(
            password=settings.SAULT + user.email + password
        )
        await self.db.commit()
        return Status(status='success')
        # add condition when user want to out of all his gadgets.


@lru_cache()
def user_service(
    db: AsyncSession = Depends(get_session),
) -> UserService:
    return UserService(
        db=db
    )
