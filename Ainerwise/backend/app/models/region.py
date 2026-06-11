from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class Region(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "regions"

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), default="EUR")
    language_codes_json: Mapped[list | None] = mapped_column(JSONB)
    tax_rules_json: Mapped[dict | None] = mapped_column(JSONB)
    timezone: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
