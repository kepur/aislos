from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.service import ServicePackage


class CRUDServicePackage(CRUDBase[ServicePackage]):
    async def get_public(self, db: AsyncSession) -> list[ServicePackage]:
        result = await db.execute(
            select(self.model)
            .where(self.model.public_visible == True)
            .order_by(self.model.sort_order)
        )
        return list(result.scalars().all())


crud_service_package = CRUDServicePackage(ServicePackage)
