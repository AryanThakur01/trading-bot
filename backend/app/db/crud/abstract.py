# app/crud/abstract.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Union
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class AbstractCRUD(ABC, Generic[ModelType]):
    @abstractmethod
    async def get(
        self, session: AsyncSession, id: Union[int, str]
    ) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> List[ModelType]:
        pass

    @abstractmethod
    async def create(self, session: AsyncSession, obj_in: ModelType) -> ModelType:
        pass

    @abstractmethod
    async def delete(self, session: AsyncSession, id: Union[int, str]) -> None:
        pass
