from typing import TypeVar, Generic,Type
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class BaseService(Generic[T]):
    def __init__(self,model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def _get(self, id: UUID) -> T | None:
        return await self.session.get(self.model,id)

    async def _add(self,entity: T) -> T:
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    
    async def _update(self,entity:T) -> T:
        return await self._add(entity)
    
    async def _delete(self,entity: T):
        await self.session.delete(entity)
        await self.session.commit()