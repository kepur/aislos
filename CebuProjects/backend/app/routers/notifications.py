from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.user import User, UserRole
from app.schemas.notification import NotificationResponse
from app.services.notification_service import create_notification

router = APIRouter(tags=["Notifications"])


@router.get("/notifications/my", response_model=list[NotificationResponse])
async def list_my_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100)
    )
    return result.scalars().all()


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(notification_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.status = NotificationStatus.READ
    n.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(n)
    return n


@router.post("/notifications/read-all")
async def mark_all_read(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    )
    for n in result.scalars().all():
        n.status = NotificationStatus.READ
        n.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.post("/admin/notifications/test-email")
async def test_email(user: User = Depends(require_roles(UserRole.ADMIN)), db: AsyncSession = Depends(get_db)):
    n = await create_notification(db, user_id=user.id, channel=NotificationChannel.EMAIL, notification_type="TEST", subject="Test Email", body="This is a test email from ProcurePing.")
    await db.commit()
    return {"status": n.status.value}


@router.post("/admin/notifications/test-telegram")
async def test_telegram(user: User = Depends(require_roles(UserRole.ADMIN)), db: AsyncSession = Depends(get_db)):
    n = await create_notification(db, user_id=user.id, channel=NotificationChannel.TELEGRAM, notification_type="TEST", body="This is a test Telegram message from ProcurePing.")
    await db.commit()
    return {"status": n.status.value}
