"""Supplier company helpers."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, CompanyStatus, VerificationLevel
from app.models.user import User


async def get_supplier_company(user: User, db: AsyncSession) -> Company | None:
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    return result.scalar_one_or_none()


async def ensure_supplier_company(user: User, db: AsyncSession, *, commit: bool = False) -> Company:
    """Return the supplier's company, creating a pending profile if missing."""
    company = await get_supplier_company(user, db)
    if company:
        return company

    company = Company(
        owner_user_id=user.id,
        name=(user.full_name or user.email.split("@")[0]).strip() or "My Company",
        country="PH",
        verification_level=VerificationLevel.UNVERIFIED,
        status=CompanyStatus.PENDING,
    )
    db.add(company)
    await db.flush()
    if commit:
        await db.commit()
        await db.refresh(company)
    return company
