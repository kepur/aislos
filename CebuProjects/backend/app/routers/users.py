from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    TelegramUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.notification_service import get_merged_notification_preferences

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(req: UserUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.post("/me/password")
async def change_password(req: PasswordChange, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    user.password_hash = hash_password(req.new_password)
    await db.commit()
    return {"ok": True}


@router.patch("/me/telegram", response_model=UserResponse)
async def update_telegram(req: TelegramUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.telegram_chat_id = req.telegram_chat_id
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me/notification-preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(user: User = Depends(get_current_user)):
    prefs = get_merged_notification_preferences(user.notification_preferences)
    return NotificationPreferencesResponse(
        **prefs,
        email=user.email,
        telegram_chat_id=user.telegram_chat_id,
        telegram_connected=bool(user.telegram_chat_id),
    )


@router.patch("/me/notification-preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    req: NotificationPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prefs = get_merged_notification_preferences(user.notification_preferences)
    payload = req.model_dump(exclude_unset=True, exclude_none=True)
    for section, values in payload.items():
        prefs.setdefault(section, {})
        prefs[section].update(values)
    user.notification_preferences = prefs
    await db.commit()
    await db.refresh(user)
    return NotificationPreferencesResponse(
        **prefs,
        email=user.email,
        telegram_chat_id=user.telegram_chat_id,
        telegram_connected=bool(user.telegram_chat_id),
    )
