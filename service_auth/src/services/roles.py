from functools import lru_cache
from typing import List, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, insert, update, delete

from src.db.postgres import get_session
from src.schemas.entity import Roles, Status
from src.models.entity import Role, User, UserRoles


class RolesService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _check_role_by_name(self, name: str) -> bool:
        role_exist = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        if role_exist:
            return role_exist.scalar()
        return False

    async def _check_user_by_email(self, email: str) -> bool:
        existing_user = await self.db.execute(
                select(User).where(User.email == email)
        )
        if existing_user:
            return existing_user.scalar()
        return False

    async def create_role(
        self,
        name: str,
        description: str
    ) -> Optional[Roles]:
        role_exist = await self._check_role_by_name(name=name)
        if role_exist:
            return None

        await self.db.execute(insert(Role).values(
            name=name, description=description
        ))
        await self.db.commit()
        return Roles(name=name, description=description)

    async def change_role(
        self,
        name: str,
        new_description: str,
        new_name: str,
    ) -> Optional[Status]:

        role_exist = await self._check_role_by_name(name=name)
        if not role_exist:
            return None

        values = {"description": new_description}
        values.update({'name': new_name}) if new_name else ''
        await self.db.execute(
            update(Role).where(Role.name == name).values(**values)
        )
        await self.db.commit()
        return Status(status='success')

    async def get_roles(self) -> List[Roles]:
        datas = await self.db.execute(select(Role))
        datas = datas.scalars()
        return [
            Roles(name=data.name, description=data.description)
            for data in datas
        ]

    async def delete_role(self, name: str) -> Optional[Status]:
        role_exist = await self._check_role_by_name(name=name)
        if not role_exist:
            return None
        await self.db.execute(delete(Role).where(Role.name == name))
        await self.db.commit()
        return Status(status='success')

    async def set_role_to_user(
        self,
        email: str,
        role_name: str,
    ) -> Optional[Roles]:
        role_exist = await self._check_role_by_name(name=role_name)
        if not role_exist:
            return None
        existing_user = await self._check_user_by_email(email=email)
        if not existing_user:
            return None

        user_roles = await self.db.execute(
            select(UserRoles)
            .where(
                UserRoles.user_id == existing_user.id,
                UserRoles.role_id == role_exist.id
            )
        )

        if user_roles.scalar():
            return None

        data_insert = UserRoles(
            user_id=existing_user.id,
            role_id=role_exist.id
        )

        self.db.add(data_insert)
        await self.db.commit()
        await self.db.refresh(data_insert)
        user_roles = await self.db.execute(
            select(Role)
            .where(
                UserRoles.user_id == existing_user.id
            )
            .join(UserRoles)
        )
        return [Roles(name=role.name, description=role.description) for role in user_roles.scalars()]

    async def delete_role_to_user(
        self,
        email: str,
        role_name: str,
    ) -> Optional[Status]:
        role_exist = await self._check_role_by_name(name=role_name)
        if not role_exist:
            return None
        existing_user = await self._check_user_by_email(email=email)
        if not existing_user:
            return None

        await self.db.execute(
            delete(UserRoles)
            .where(
                UserRoles.user_id == existing_user.id,
                UserRoles.role_id == role_exist.id
            )
        )
        await self.db.commit()
        return Status(status='success')


@lru_cache()
def role_services(
    db: AsyncSession = Depends(get_session),
) -> RolesService:
    return RolesService(
        db=db
    )
