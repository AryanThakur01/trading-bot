# app/crud/user.py
from typing import Optional, List, Union
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import User
from app.db.crud.abstract import AbstractCRUD


class UserCRUD(AbstractCRUD[User]):
    async def get(self, session: AsyncSession, id: Union[int, str]) -> Optional[User]:
        return await session.get(User, id)

    async def get_all(self, session: AsyncSession) -> List[User]:
        result = await session.exec(select(User))
        return result.all()

    async def create(self, session: AsyncSession, obj_in: User) -> User:
        session.add(obj_in)
        await session.commit()
        await session.refresh(obj_in)
        return obj_in

    async def delete(self, session: AsyncSession, id: Union[int, str]) -> None:
        user = await session.get(User, id)
        if user:
            await session.delete(user)
            await session.commit()

    async def update(
        self, session: AsyncSession, id: Union[int, str], obj_in: User
    ) -> Optional[User]:
        user = await session.get(User, id)
        if not user:
            return None
        for key, value in obj_in.dict(exclude_unset=True).items():
            setattr(user, key, value)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
