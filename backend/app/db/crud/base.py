# app/crud/base.py
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseCRUD(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, **filters) -> Optional[ModelType]:
        result = await session.exec(select(self.model).filter_by(**filters))
        return result.first()

    async def get_all(self, session: AsyncSession, **filters) -> List[ModelType]:
        result = await session.exec(select(self.model).filter_by(**filters))
        return result.all()

    async def create(
        self, session: AsyncSession, obj_data: Dict[str, Any]
    ) -> ModelType:
        obj = self.model(**obj_data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(
        self, session: AsyncSession, filters: Dict[str, Any], updates: Dict[str, Any]
    ) -> Optional[ModelType]:
        result = await session.exec(select(self.model).filter_by(**filters))
        obj = result.first()
        if not obj:
            return None
        for key, value in updates.items():
            setattr(obj, key, value)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, **filters) -> Optional[ModelType]:
        result = await session.exec(select(self.model).filter_by(**filters))
        obj = result.first()
        if obj:
            await session.delete(obj)
            await session.commit()
        return obj
