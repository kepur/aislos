import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AccountType(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"


class UserRole(str, enum.Enum):
    # Marketplace roles
    BUYER = "BUYER"
    SUPPLIER_ADMIN = "SUPPLIER_ADMIN"
    SUPPLIER_AGENT = "SUPPLIER_AGENT"
    # Platform admin roles
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
    OPS_MANAGER = "OPS_MANAGER"
    VERIFICATION_OFFICER = "VERIFICATION_OFFICER"
    DISPUTE_AGENT = "DISPUTE_AGENT"
    FINANCE_OFFICER = "FINANCE_OFFICER"
    RISK_ANALYST = "RISK_ANALYST"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    AUDITOR = "AUDITOR"


# All roles that have platform admin access
ADMIN_ROLES = {
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
    UserRole.OPS_MANAGER,
    UserRole.VERIFICATION_OFFICER,
    UserRole.DISPUTE_AGENT,
    UserRole.FINANCE_OFFICER,
    UserRole.RISK_ANALYST,
    UserRole.SUPPORT_AGENT,
    UserRole.AUDITOR,
}


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    DELETED = "DELETED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", create_type=False), default=UserRole.BUYER)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus, name="user_status", create_type=False), default=UserStatus.ACTIVE)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type", create_type=False), default=AccountType.INDIVIDUAL)
    full_name: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100))
    notification_preferences: Mapped[dict | None] = mapped_column(JSON, default=dict)
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    two_fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

