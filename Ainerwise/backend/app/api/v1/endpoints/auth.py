import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.core.config import settings
from app.core.permissions import PUBLIC_REGISTRATION_ROLES, UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import Company, PasswordResetToken, User
from app.models.service import ServicePartner
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.demo_mode import is_demo_mode_enabled, is_demo_restricted_email
from app.services.email import send_email
from app.services.portal_access import sync_role_portal_access
from app.services.rate_limit import enforce_public_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, request: Request, db: DB):
    await enforce_public_rate_limit(
        request, bucket="auth-register", limit=10, subject_suffix=data.email
    )
    if data.role not in PUBLIC_REGISTRATION_ROLES:
        raise HTTPException(status_code=403, detail="This role requires an administrator invitation")
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    company = None
    if data.company_name:
        company_type = data.company_type or (
            "vendor" if data.role.value == "vendor" else
            "developer" if data.role.value == "developer" else
            "service_partner" if data.role.value == "service_partner" else
            "buyer"
        )
        company = Company(name=data.company_name, type=company_type)
        db.add(company)
        await db.flush()

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=data.role.value,
        language=data.language,
        country=data.country,
        company_id=company.id if company else None,
    )
    db.add(user)
    await db.flush()
    if data.role == UserRole.SERVICE_PARTNER:
        db.add(
            ServicePartner(
                company_id=company.id if company else None,
                user_id=user.id,
                partner_type="general",
                country=data.country,
                languages_json=[data.language],
                availability_status="available",
                verification_status="pending",
            )
        )
    await sync_role_portal_access(
        db,
        user_id=user.id,
        role=user.role,
        company_id=user.company_id,
    )
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: DB):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        await enforce_public_rate_limit(
            request,
            bucket="auth-login-failed-ip",
            limit=60,
            window_seconds=900,
        )
        await enforce_public_rate_limit(
            request,
            bucket="auth-login-failed-account",
            limit=10,
            window_seconds=900,
            subject_suffix=data.email,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if is_demo_restricted_email(data.email) and not await is_demo_mode_enabled(db):
        raise HTTPException(
            status_code=403,
            detail="Demo mode is disabled. Enable it in Admin → Settings.",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.last_login_at = datetime.now(timezone.utc)
    await sync_role_portal_access(
        db,
        user_id=user.id,
        role=user.role,
        company_id=user.company_id,
    )
    await db.commit()

    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: DB):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(str(user.id), user.role)
    new_refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    return current_user


def _account_context_payload(user: User, company: Company | None) -> dict:
    company_contact = company.contact_info if company and isinstance(company.contact_info, dict) else {}
    account_type = company_contact.get("account_type") or ("BUSINESS" if company else "INDIVIDUAL")
    portals = ["customer"]
    if user.role == "vendor":
        portals.append("supplier")
    if user.role in ("admin", "super_admin", "finance"):
        portals.extend(["admin", "supplier", "buyer"])
    if user.role in ("buyer", "customer_user") and "buyer" not in portals:
        portals.append("buyer")
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_id": user.company_id,
        },
        "account_type": account_type,
        "is_company_account": company is not None,
        "company": {
            "id": company.id,
            "name": company.name,
            "type": company.type,
            "verification_status": company.verification_status,
            "country": company.country,
            "city": company.city,
        } if company else None,
        "available_portals": portals,
        "default_portal": "supplier" if user.role == "vendor" else "buyer" if user.role in ("buyer", "customer_user") else "admin",
    }


@router.get("/me/account-context")
async def get_account_context(current_user: CurrentUser, db: DB):
    company = await db.get(Company, current_user.company_id) if current_user.company_id else None
    return _account_context_payload(current_user, company)


@router.get("/me/account-type")
async def get_account_type(current_user: CurrentUser, db: DB):
    company = await db.get(Company, current_user.company_id) if current_user.company_id else None
    payload = _account_context_payload(current_user, company)
    return {
        "account_type": payload["account_type"],
        "role": current_user.role,
        "company_id": current_user.company_id,
        "is_company_account": payload["is_company_account"],
    }


@router.patch("/me/account-type")
async def update_account_type(data: dict, current_user: CurrentUser, db: DB):
    account_type = str(data.get("account_type") or "BUSINESS").upper()
    if account_type not in {"INDIVIDUAL", "BUSINESS"}:
        raise HTTPException(status_code=422, detail="account_type must be INDIVIDUAL or BUSINESS")
    company = await db.get(Company, current_user.company_id) if current_user.company_id else None
    if company is None:
        company = Company(
            name=f"{current_user.full_name or current_user.email} Supplier",
            type="vendor",
            country=current_user.country,
            contact_info={"email": current_user.email, "account_type": account_type},
        )
        db.add(company)
        await db.flush()
        current_user.company_id = company.id
    contact_info = dict(company.contact_info or {})
    contact_info["account_type"] = account_type
    company.contact_info = contact_info
    company.type = "vendor"
    if current_user.role in ("buyer", "customer_user"):
        current_user.role = "vendor"
    await sync_role_portal_access(
        db,
        user_id=current_user.id,
        role=current_user.role,
        company_id=current_user.company_id,
    )
    await db.commit()
    await db.refresh(current_user)
    await db.refresh(company)
    return _account_context_payload(current_user, company)


@router.put("/change-password")
async def change_password(data: ChangePasswordRequest, current_user: CurrentUser, db: DB):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/request-password-reset")
async def request_password_reset(data: PasswordResetRequest, request: Request, db: DB):
    """Create a short-lived one-time token without revealing account existence."""
    await enforce_public_rate_limit(
        request, bucket="auth-password-reset", limit=5, subject_suffix=data.email
    )
    generic_response = {
        "message": "If an active account exists for that email, a password reset link has been sent."
    }
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return generic_response

    now = datetime.now(timezone.utc)
    outstanding = list(
        (
            await db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                )
            )
        ).scalars()
    )
    for reset in outstanding:
        reset.used_at = now

    raw_token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=now + timedelta(minutes=30),
        )
    )
    await db.commit()

    reset_url = f"{settings.PASSWORD_RESET_BASE_URL}?{urlencode({'token': raw_token})}"
    await send_email(
        db,
        to=user.email,
        subject="Reset your AinerWise password",
        body=(
            "A password reset was requested for your AinerWise account.\n\n"
            f"Use this one-time link within 30 minutes:\n{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        ),
    )
    return generic_response


@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm, db: DB):
    now = datetime.now(timezone.utc)
    token_hash = hashlib.sha256(data.token.encode("utf-8")).hexdigest()
    reset = (
        await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    ).scalar_one_or_none()
    if reset is None or reset.used_at is not None or reset.expires_at <= now:
        raise HTTPException(status_code=400, detail="Password reset token is invalid or expired")

    user = await db.get(User, reset.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Password reset token is invalid or expired")

    outstanding = list(
        (
            await db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                )
            )
        ).scalars()
    )
    for item in outstanding:
        item.used_at = now
    user.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"message": "Password reset successfully"}
