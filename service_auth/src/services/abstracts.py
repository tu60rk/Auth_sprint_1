import abc
import uuid

from fastapi import Response
from typing import Optional, List

from src.schemas.entity import UserInDB, Tokens, Status, Roles, ShemaAccountHistory


class AsyncAuthService(abc.ABC):

    @abc.abstractmethod
    async def create_user(self, user_info: UserInDB) -> Optional[UserInDB]:
        pass

    @abc.abstractmethod
    async def login(
        self,
        user_agent: str,
        email: str,
        passwd: str,
        set_cookie: bool,
        response: Response
    ) -> Tokens:
        pass

    @abc.abstractmethod
    async def refresh(self, refresh_token: str, user_agent: str) -> Tokens:
        pass

    @abc.abstractmethod
    async def logout_all(self, user_id: str) -> Status:
        pass

    @abc.abstractmethod
    async def logout_me(self, user_id: str, user_agent: str) -> Status:
        pass


class AsyncRolesService(abc.ABC):

    @abc.abstractmethod
    async def create_role(
        self,
        name: str,
        description: str
    ) -> Optional[Roles]:
        pass

    @abc.abstractmethod
    async def delete_role(self, name: str) -> Optional[Status]:
        pass

    @abc.abstractmethod
    async def change_role(
        self,
        name: str,
        new_description: str,
        new_name: str,
    ) -> Optional[Status]:
        pass

    @abc.abstractmethod
    async def get_roles(self) -> List[Roles]:
        pass

    @abc.abstractmethod
    async def set_role_to_user(
        self,
        email: str,
        role_name: str,
    ) -> Optional[Roles]:
        pass

    @abc.abstractmethod
    async def delete_role_to_user(
        self,
        email: str,
        role_name: str,
    ) -> Optional[Status]:
        pass


class AsyncUsersService(abc.ABC):

    @abc.abstractmethod
    async def get_account_history(
        self,
        user_id: uuid
    ) -> Optional[List[ShemaAccountHistory]]:
        pass

    @abc.abstractclassmethod
    async def change_password(
        self,
        current_password: str,
        password: str,
        user_info: UserInDB
    ) -> Status:
        pass

    @abc.abstractclassmethod
    async def change_email(
        self,
        current_password: str,
        new_email: str,
        user_info: UserInDB
    ) -> Status:
        pass