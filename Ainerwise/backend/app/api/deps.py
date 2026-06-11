from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import UserRole
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_role(*roles: UserRole):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in [r.value if hasattr(r, 'value') else r for r in roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_checker


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN))]
# Internal staff: same admin surface for now; granular menus come with real hires.
StaffUser = Annotated[User, Depends(require_role(
    UserRole.SUPER_ADMIN, UserRole.ADMIN,
    UserRole.SALES_MANAGER, UserRole.PROJECT_MANAGER, UserRole.FINANCE,
))]
# Partner layout on frontend-h5: owners, workers and maintenance crews.
ServicePartnerUser = Annotated[User, Depends(require_role(
    UserRole.SERVICE_PARTNER, UserRole.PARTNER_WORKER, UserRole.MAINTENANCE_WORKER,
))]
CustomerUser = Annotated[User, Depends(require_role(UserRole.BUYER, UserRole.CUSTOMER_USER))]
DB = Annotated[AsyncSession, Depends(get_db)]
