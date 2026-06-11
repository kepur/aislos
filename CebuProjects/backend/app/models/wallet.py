import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WalletStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class WalletTransactionType(str, enum.Enum):
    DEPOSIT_INTENT_CREATED = "DEPOSIT_INTENT_CREATED"
    DEPOSIT_TX_SUBMITTED = "DEPOSIT_TX_SUBMITTED"
    DEPOSIT_VERIFIED = "DEPOSIT_VERIFIED"
    DEPOSIT_REJECTED = "DEPOSIT_REJECTED"
    ESCROW_LOCK = "ESCROW_LOCK"
    ESCROW_RELEASE = "ESCROW_RELEASE"
    ESCROW_REFUND = "ESCROW_REFUND"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT"


class DepositStatus(str, enum.Enum):
    PENDING_TX = "PENDING_TX"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    currency: Mapped[str] = mapped_column(String(10), default="USDT", index=True)
    available_balance_minor: Mapped[int] = mapped_column(Integer, default=0)
    locked_balance_minor: Mapped[int] = mapped_column(Integer, default=0)
    total_deposited_minor: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[WalletStatus] = mapped_column(Enum(WalletStatus, name="wallet_status", create_type=False), default=WalletStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    tx_type: Mapped[WalletTransactionType] = mapped_column(Enum(WalletTransactionType, name="wallet_transaction_type", create_type=False), index=True)
    amount_delta_minor: Mapped[int] = mapped_column(Integer, default=0)
    available_balance_after_minor: Mapped[int] = mapped_column(Integer, default=0)
    locked_balance_after_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USDT")
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    note: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WalletDeposit(Base):
    __tablename__ = "wallet_deposits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="USDT")
    network: Mapped[str] = mapped_column(String(50), default="TRC20")
    provider: Mapped[str] = mapped_column(String(50), default="MANUAL_BANK")
    payment_method: Mapped[str] = mapped_column(String(50), default="PHP_MANUAL_BANK")
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    source_currency: Mapped[str | None] = mapped_column(String(10))
    target_currency: Mapped[str | None] = mapped_column(String(10))
    deposit_address: Mapped[str] = mapped_column(String(255))
    tx_hash: Mapped[str | None] = mapped_column(String(255), index=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[DepositStatus] = mapped_column(Enum(DepositStatus, name="deposit_status", create_type=False), default=DepositStatus.PENDING_TX, index=True)
    submitter_note: Mapped[str | None] = mapped_column(Text)
    admin_note: Mapped[str | None] = mapped_column(Text)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
