import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, CurrentUser, DB
from app.core.permissions import ALL_ROLES, UserRole
from app.crud.user import crud_company, crud_user
from app.schemas.user import CompanyCreate, CompanyRead, CompanyUpdate, UserRead, UserUpdate
from app.services.audit import append_audit_event
from app.services.portal_access import suspend_user_portal_access, sync_role_portal_access

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


@router.patch("/users/me", response_model=UserRead)
async def update_current_user(data: UserUpdate, db: DB, user: CurrentUser):
    return await crud_user.update(db, db_obj=user, obj_in=data.model_dump(exclude_unset=True))


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
    allowed_roles = {item.value for item in ALL_ROLES}
    if role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Unknown user role")
    user = await crud_user.get(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=409, detail="Admin cannot change own role")
    if (
        user.role == UserRole.SUPER_ADMIN.value or role == UserRole.SUPER_ADMIN.value
    ) and admin.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="Only a super admin can manage super admin roles")

    previous_role = user.role
    user.role = role
    await sync_role_portal_access(
        db,
        user_id=user.id,
        role=user.role,
        company_id=user.company_id,
    )
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        action="identity.user_role_changed",
        entity_type="user",
        entity_id=user.id,
        before={"role": previous_role},
        after={"role": user.role},
        source="admin.users",
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{id}/active", response_model=UserRead)
async def toggle_user_active(id: uuid.UUID, db: DB, admin: AdminUser, is_active: bool = Query(...)):
    user = await crud_user.get(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id and not is_active:
        raise HTTPException(status_code=409, detail="Admin cannot deactivate own account")
    if user.role == UserRole.SUPER_ADMIN.value and admin.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="Only a super admin can manage super admin accounts")

    previous_value = user.is_active
    user.is_active = is_active
    if is_active:
        await sync_role_portal_access(
            db,
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
        )
    else:
        await suspend_user_portal_access(db, user_id=user.id)
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        action="identity.user_active_changed",
        entity_type="user",
        entity_id=user.id,
        before={"is_active": previous_value},
        after={"is_active": user.is_active},
        source="admin.users",
    )
    await db.commit()
    await db.refresh(user)
    return user


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
