from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import RiskLevel
from app.models.platform_setting import PlatformSetting
from app.models.user import AccountType, User, UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, SystemModeResponse, TokenResponse
from app.schemas.user import UserResponse
from app.services.audit_service import create_audit_log
from app.services.company_service import ensure_supplier_company

router = APIRouter(prefix="/auth", tags=["Auth"])


async def _get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else default


@router.get("/system-mode", response_model=SystemModeResponse)
async def system_mode(db: AsyncSession = Depends(get_db)):
    demo_mode = (await _get_setting(db, "DEMO_MODE", "false")).lower() == "true"
    reg_enabled = (await _get_setting(db, "REGISTRATION_ENABLED", "true")).lower() == "true"
    app_name = await _get_setting(db, "APP_NAME", "ProcurePing")
    raw_limit = await _get_setting(db, "INTENT_MAX_ATTACHMENTS", "10")
    try:
        intent_max_attachments = max(0, min(20, int(raw_limit)))
    except ValueError:
        intent_max_attachments = 10
    return SystemModeResponse(
        demo_mode=demo_mode,
        registration_enabled=reg_enabled,
        app_name=app_name,
        intent_max_attachments=intent_max_attachments,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    reg_enabled = (await _get_setting(db, "REGISTRATION_ENABLED", "true")).lower() == "true"
    if not reg_enabled:
        raise HTTPException(status_code=403, detail="Registration is currently disabled. Contact an administrator.")

    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in (UserRole.BUYER, UserRole.SUPPLIER_ADMIN):
        raise HTTPException(status_code=400, detail="Can only register as BUYER or SUPPLIER_ADMIN")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        phone=req.phone,
        role=req.role,
        account_type=req.account_type,
    )
    db.add(user)
    await db.flush()

    if req.role == UserRole.SUPPLIER_ADMIN:
        await ensure_supplier_company(user, db)

    await create_audit_log(db, action="USER_REGISTERED", entity_type="User", entity_id=user.id, actor_id=user.id, actor_role=user.role.value)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    is_demo_account = req.email.strip().lower().endswith("@demo.procureping")
    demo_mode = (await _get_setting(db, "DEMO_MODE", "false")).lower() == "true"
    if is_demo_account and not demo_mode:
        await create_audit_log(db, action="DEMO_LOGIN_BLOCKED", entity_type="User", risk_level=RiskLevel.MEDIUM)
        await db.commit()
        raise HTTPException(status_code=403, detail="Demo mode is currently disabled")

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if is_demo_account and req.password == "123" and user and user.status.value == "ACTIVE":
        return TokenResponse(
            access_token=create_access_token(str(user.id), {"role": user.role.value}),
            refresh_token=create_refresh_token(str(user.id)),
        )

    if not user or not verify_password(req.password, user.password_hash):
        await create_audit_log(db, action="USER_LOGIN_FAILED", entity_type="User", risk_level=RiskLevel.MEDIUM)
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status.value != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account is not active")

    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status.value != "ACTIVE":
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


class AccountTypeUpdate(BaseModel):
    account_type: AccountType


@router.patch("/me/account-type")
async def update_account_type(
    req: AccountTypeUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade account type. INDIVIDUAL → BUSINESS allowed; BUSINESS → INDIVIDUAL is not."""
    if user.account_type == AccountType.BUSINESS and req.account_type == AccountType.INDIVIDUAL:
        raise HTTPException(status_code=400, detail="Cannot downgrade from BUSINESS to INDIVIDUAL")
    old_type = user.account_type
    user.account_type = req.account_type
    await create_audit_log(
        db, action="ACCOUNT_TYPE_CHANGED", entity_type="User", entity_id=user.id,
        actor_id=user.id, actor_role=user.role.value,
        before_json={"account_type": old_type.value},
        after_json={"account_type": req.account_type.value},
    )
    await db.commit()
    return {"account_type": user.account_type.value}


@router.get("/me/account-context")
async def account_context(user: User = Depends(get_current_user)):
    """Return current user account type and feature flags."""
    is_individual = user.account_type == AccountType.INDIVIDUAL
    is_buyer = user.role == UserRole.BUYER
    is_supplier = user.role in (UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)
    return {
        "account_type": user.account_type.value,
        "role": user.role.value,
        "features": {
            "kyb": not is_individual,
            "company_profile": not is_individual,
            "team_management": not is_individual,
            "b2b_rfq": True,
            "b2c_buy_now": True,
            "multi_branch": not is_individual and is_supplier,
            "payout_settings": is_supplier,
        },
    }
