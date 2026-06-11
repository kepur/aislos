import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AddressType(str, enum.Enum):
    SHIPPING_FROM = "SHIPPING_FROM"    # Supplier origin address
    DELIVERY_TO = "DELIVERY_TO"        # Buyer delivery address
    WAREHOUSE = "WAREHOUSE"            # Supplier warehouse
    BILLING = "BILLING"                # Billing address


class AddressStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    address_type: Mapped[AddressType] = mapped_column(Enum(AddressType, name="address_type", create_type=False))
    label: Mapped[str] = mapped_column(String(100))  # "Home", "Office", "Main Warehouse"
    contact_name: Mapped[str] = mapped_column(String(255))
    contact_phone: Mapped[str] = mapped_column(String(50))
    country_code: Mapped[str] = mapped_column(String(5), index=True)  # ISO 3166-1 alpha-2
    country_name: Mapped[str] = mapped_column(String(100))
    state_province: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    address_line1: Mapped[str] = mapped_column(Text)
    address_line2: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    google_place_id: Mapped[str | None] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[AddressStatus] = mapped_column(Enum(AddressStatus, name="address_status", create_type=False), default=AddressStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
