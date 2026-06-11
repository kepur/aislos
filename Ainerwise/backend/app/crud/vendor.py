from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import Company


class CRUDVendor(CRUDBase[Company]):
    async def get_vendors(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 20
    ) -> tuple[list[Company], int]:
        filters = [self.model.type == "vendor"]
        return await self.get_multi(db, skip=skip, limit=limit, filters=filters)


crud_vendor = CRUDVendor(Company)
