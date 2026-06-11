"""User address book management."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.address import Address, AddressStatus
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=list[AddressResponse])
async def list_addresses(
    address_type: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Address).where(Address.user_id == user.id, Address.status == AddressStatus.ACTIVE)
    if address_type:
        q = q.where(Address.address_type == address_type)
    q = q.order_by(Address.is_default.desc(), Address.created_at.desc())
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.post("", response_model=AddressResponse, status_code=201)
async def create_address(
    body: AddressCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # If setting as default, unset other defaults of same type
    if body.is_default:
        await db.execute(
            update(Address)
            .where(Address.user_id == user.id, Address.address_type == body.address_type, Address.is_default == True)
            .values(is_default=False)
        )

    addr = Address(user_id=user.id, **body.model_dump())
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


@router.patch("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    body: AddressUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    addr = (await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user.id, Address.status == AddressStatus.ACTIVE)
    )).scalars().first()
    if not addr:
        raise HTTPException(404, "Address not found")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(addr, k, v)
    await db.commit()
    await db.refresh(addr)
    return addr


@router.delete("/{address_id}", status_code=204)
async def delete_address(
    address_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    addr = (await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user.id)
    )).scalars().first()
    if not addr:
        raise HTTPException(404, "Address not found")
    addr.status = AddressStatus.DELETED
    addr.is_default = False
    await db.commit()


@router.post("/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    address_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    addr = (await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user.id, Address.status == AddressStatus.ACTIVE)
    )).scalars().first()
    if not addr:
        raise HTTPException(404, "Address not found")

    # Unset other defaults of same type
    await db.execute(
        update(Address)
        .where(Address.user_id == user.id, Address.address_type == addr.address_type, Address.is_default == True)
        .values(is_default=False)
    )
    addr.is_default = True
    await db.commit()
    await db.refresh(addr)
    return addr
