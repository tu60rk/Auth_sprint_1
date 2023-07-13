import abc

from typing import Optional
from datetime import timedelta


class AsyncCacheService(abc.ABC):

    @abc.abstractmethod
    async def add_token(
        self,
        user_id: str,
        access_token: str,
        user_agent: str
    ) -> None:
        pass

    @abc.abstractmethod
    async def get(self, user_id: str) -> Optional[dict]:
        pass

    @abc.abstractmethod
    async def set(self, name: str, value: str, ex: timedelta = None) -> None:
        pass

    @abc.abstractmethod
    async def delete(self, user_id: str) -> None:
        pass


class AsyncDbService(abc.ABC):

    @abc.abstractmethod
    async def insert_data(self, data) -> None:
        pass

    @abc.abstractmethod
    async def simple_select(
        self,
        what_select,
        where_select: list = None,
        order_select=None,
        join_with=None,
    ):
        pass

    @abc.abstractmethod
    async def simple_update(
        self,
        what_update,
        values_update: dict,
        where_update: list = None,
    ):
        pass

    @abc.abstractmethod
    async def simple_insert(
        self,
        what_insert,
        values_insert: dict
    ):
        pass

    @abc.abstractmethod
    async def update_token(
        self,
        what_update,
        values_update: dict,
        where_update: dict = None,
    ):
        pass

    @abc.abstractmethod
    async def simple_delete(
        self,
        what_delete,
        where_delete: list = None
    ):
        pass

    @abc.abstractmethod
    async def get_user_roles(self, user_id) -> list:
        pass
