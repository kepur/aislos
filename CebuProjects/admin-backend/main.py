import os
import sys

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.core.deps import get_current_user  # noqa: E402
from app.core.security import create_access_token, create_refresh_token, verify_password  # noqa: E402
from app.models.user import ADMIN_ROLES, User  # noqa: E402
from app.routers import admin, admin_trust, maps, payments, wallets  # noqa: E402
from app.schemas.auth import LoginRequest, TokenResponse  # noqa: E402
from app.schemas.user import UserResponse  # noqa: E402


app = FastAPI(
    title=f"{settings.APP_NAME} Admin API",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_router = APIRouter(prefix="/auth", tags=["Admin Auth"])
users_router = APIRouter(prefix="/users", tags=["Admin Users"])


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@auth_router.post("/login", response_model=TokenResponse)
async def admin_login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.status.value != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account is not active")
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")

    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@auth_router.get("/me", response_model=UserResponse)
async def admin_auth_me(user: User = Depends(get_current_admin_user)):
    return user


@users_router.get("/me", response_model=UserResponse)
async def admin_users_me(user: User = Depends(get_current_admin_user)):
    return user


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin.router)
app.include_router(admin_trust.router)
app.include_router(payments.router)
app.include_router(wallets.router)
app.include_router(maps.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "admin-backend"}
