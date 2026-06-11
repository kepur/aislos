from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class FounderProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "founder_profiles"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    bio_short: Mapped[str | None] = mapped_column(String(500))
    bio_long: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    skills_json: Mapped[list | None] = mapped_column(JSONB)
    certifications_json: Mapped[list | None] = mapped_column(JSONB)
    service_regions_json: Mapped[list | None] = mapped_column(JSONB)
    languages_json: Mapped[list | None] = mapped_column(JSONB)
    visible_on_site: Mapped[bool] = mapped_column(Boolean, default=True)
