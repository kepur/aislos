from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.catalog import CatalogItem
from app.models.user import User, UserRole
from app.schemas.catalog import CatalogItemCreate, CatalogItemResponse, CatalogItemUpdate
from app.services.company_service import ensure_supplier_company, get_supplier_company

router = APIRouter(prefix="/supplier/catalog", tags=["Catalog"])


@router.post("/items", response_model=CatalogItemResponse, status_code=201)
async def create_item(
    req: CatalogItemCreate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    company = await ensure_supplier_company(user, db)
    item = CatalogItem(company_id=company.id, **req.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/items", response_model=list[CatalogItemResponse])
async def list_items(
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    company = await get_supplier_company(user, db)
    if not company:
        return []
    result = await db.execute(select(CatalogItem).where(CatalogItem.company_id == company.id))
    return result.scalars().all()


@router.get("/items/{item_id}", response_model=CatalogItemResponse)
async def get_item(
    item_id: str,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    company = await get_supplier_company(user, db)
    if not company:
        raise HTTPException(status_code=404, detail="Item not found")
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == item_id, CatalogItem.company_id == company.id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/items/{item_id}", response_model=CatalogItemResponse)
async def update_item(
    item_id: str,
    req: CatalogItemUpdate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    company = await get_supplier_company(user, db)
    if not company:
        raise HTTPException(status_code=404, detail="Item not found")
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == item_id, CatalogItem.company_id == company.id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: str,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    company = await get_supplier_company(user, db)
    if not company:
        raise HTTPException(status_code=404, detail="Item not found")
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == item_id, CatalogItem.company_id == company.id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()
