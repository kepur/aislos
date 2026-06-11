"""SP04: map Cebu legacy identities to Core users without sharing JWT secrets."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legacy_bridge import LegacyIdentityMapping


async def upsert_identity_mapping(
    db: AsyncSession,
    *,
    portal_key: str,
    legacy_system: str,
    legacy_user_id: str,
    legacy_company_id: str | None = None,
    core_user_id: uuid.UUID | None = None,
    core_company_id: uuid.UUID | None = None,
    metadata_json: dict | None = None,
) -> LegacyIdentityMapping:
    if not legacy_user_id:
        raise ValueError("legacy_user_id is required")
    result = await db.execute(
        select(LegacyIdentityMapping).where(
            LegacyIdentityMapping.portal_key == portal_key,
            LegacyIdentityMapping.legacy_system == legacy_system,
            LegacyIdentityMapping.legacy_user_id == legacy_user_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = LegacyIdentityMapping(
            portal_key=portal_key,
            legacy_system=legacy_system,
            legacy_user_id=legacy_user_id,
        )
        db.add(row)
    row.legacy_company_id = legacy_company_id
    row.core_user_id = core_user_id
    row.core_company_id = core_company_id
    row.metadata_json = metadata_json
    await db.flush()
    return row


async def resolve_core_user_id(
    db: AsyncSession,
    *,
    portal_key: str,
    legacy_system: str,
    legacy_user_id: str,
) -> uuid.UUID | None:
    result = await db.execute(
        select(LegacyIdentityMapping.core_user_id).where(
            LegacyIdentityMapping.portal_key == portal_key,
            LegacyIdentityMapping.legacy_system == legacy_system,
            LegacyIdentityMapping.legacy_user_id == legacy_user_id,
        )
    )
    return result.scalar_one_or_none()
