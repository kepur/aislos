import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentType(str, enum.Enum):
    BUSINESS_REGISTRATION = "BUSINESS_REGISTRATION"
    TAX_ID = "TAX_ID"
    OWNER_ID = "OWNER_ID"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    USDT_WALLET = "USDT_WALLET"
    WAREHOUSE_PHOTO = "WAREHOUSE_PHOTO"
    CATEGORY_LICENSE = "CATEGORY_LICENSE"
    OTHER = "OTHER"


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class CompanyDocument(Base):
    __tablename__ = "company_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, name="document_type", create_type=False))
    file_url: Mapped[str] = mapped_column(String(512))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus, name="document_status", create_type=False), default=DocumentStatus.PENDING)
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
