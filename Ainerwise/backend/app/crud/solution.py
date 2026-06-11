from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.solution import Solution, SolutionPackage


class CRUDSolution(CRUDBase[Solution]):
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Solution | None:
        result = await db.execute(select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none()

    async def get_public(self, db: AsyncSession) -> list[Solution]:
        result = await db.execute(
            select(self.model)
            .where(self.model.public_visible == True)
            .order_by(self.model.sort_order)
        )
        return list(result.scalars().all())


crud_solution = CRUDSolution(Solution)
crud_solution_package = CRUDBase[SolutionPackage](SolutionPackage)
