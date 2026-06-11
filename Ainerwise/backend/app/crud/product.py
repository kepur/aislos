import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.product import Product, ProductCategory


class CRUDProduct(CRUDBase[Product]):
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Product | None:
        result = await db.execute(select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none()

    async def get_public(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        category_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        filters = [self.model.status == "approved"]
        if category_id:
            filters.append(self.model.category_id == category_id)
        if search:
            filters.append(self.model.name.ilike(f"%{search}%"))
        return await self.get_multi(db, skip=skip, limit=limit, filters=filters)


class CRUDProductCategory(CRUDBase[ProductCategory]):
    async def get_by_slug(self, db: AsyncSession, slug: str) -> ProductCategory | None:
        result = await db.execute(select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none()

    async def get_tree(self, db: AsyncSession) -> list[ProductCategory]:
        result = await db.execute(select(self.model).order_by(self.model.sort_order))
        return list(result.scalars().all())


crud_product = CRUDProduct(Product)
crud_product_category = CRUDProductCategory(ProductCategory)
