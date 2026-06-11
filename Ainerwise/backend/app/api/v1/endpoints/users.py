import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.user import crud_company, crud_user
from app.schemas.user import CompanyCreate, CompanyRead, CompanyUpdate, UserRead, UserUpdate

router = APIRouter(tags=["users"])


# ── Users ────────────────────────────────────────────────────────
@router.get("/users")
async def list_users(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = None,
):
    filters = []
    if role:
        from app.models.user import User

        filters.append(User.role == role)
    items, total = await crud_user.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [UserRead.model_validate(i) for i in items], "total": total}


@router.get("/users/{id}", response_model=UserRead)
async def get_user(id: uuid.UUID, db: DB, admin: AdminUser):
    user = await crud_user.get(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{id}", response_model=UserRead)
async def update_user_admin(id: uuid.UUID, data: UserUpdate, db: DB, admin: AdminUser):
    user = await crud_user.get(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud_user.update(db, db_obj=user, obj_in=data.model_dump(exclude_unset=True))


@router.patch("/users/{id}/role", response_model=UserRead)
async def update_user_role(id: uuid.UUID, db: DB, admin: AdminUser, role: str = Query(...)):
    user = await crud_user.get(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud_user.update(db, db_obj=user, obj_in={"role": role})


@router.patch("/users/{id}/active", response_model=UserRead)
async def toggle_user_active(id: uuid.UUID, db: DB, admin: AdminUser, is_active: bool = Query(...)):
    user = await crud_user.get(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud_user.update(db, db_obj=user, obj_in={"is_active": is_active})


# ── Companies ────────────────────────────────────────────────────
@router.get("/companies")
async def list_companies(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: str | None = None,
):
    filters = []
    if type:
        from app.models.user import Company

        filters.append(Company.type == type)
    items, total = await crud_company.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [CompanyRead.model_validate(i) for i in items], "total": total}


@router.get("/companies/{id}", response_model=CompanyRead)
async def get_company(id: uuid.UUID, db: DB, admin: AdminUser):
    company = await crud_company.get(db, id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/companies", response_model=CompanyRead, status_code=201)
async def create_company(data: CompanyCreate, db: DB, admin: AdminUser):
    return await crud_company.create(db, obj_in=data.model_dump())


@router.put("/companies/{id}", response_model=CompanyRead)
async def update_company(id: uuid.UUID, data: CompanyUpdate, db: DB, admin: AdminUser):
    company = await crud_company.get(db, id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return await crud_company.update(db, db_obj=company, obj_in=data.model_dump(exclude_unset=True))
