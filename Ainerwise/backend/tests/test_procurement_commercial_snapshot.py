"""C07: commercial snapshot hashing and immutability."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.models.procurement import CommercialSnapshot
from app.services.procurement_rfq import (
    CommercialSnapshotImmutableError,
    assert_snapshot_immutable,
    canonical_terms_payload,
    compute_terms_hash,
    validate_commercial_terms,
)


def _sample_terms() -> dict:
    expiry = datetime.now(timezone.utc) + timedelta(days=30)
    return {
        "currency": "USD",
        "exchange_rate_snapshot_json": {"base": "USD", "quote": "PHP", "rate": "56.5"},
        "tax_mode": "exclusive",
        "margin_rule_json": {"type": "percent", "value": "0.15"},
        "service_fee_json": {"platform_fee_percent": "0.05"},
        "warranty_rule_json": {"months": 12},
        "delivery_region_json": {"country": "PH", "city": "Cebu"},
        "quote_expiry": expiry,
        "payment_terms_json": {"net_days": 30},
    }


def test_validate_commercial_terms_rejects_missing_field():
    terms = _sample_terms()
    terms.pop("tax_mode")
    with pytest.raises(Exception, match="tax_mode"):
        validate_commercial_terms(terms)


def test_terms_hash_is_stable_and_recomputable():
    terms = _sample_terms()
    h1 = compute_terms_hash(terms)
    h2 = compute_terms_hash(canonical_terms_payload(terms))
    assert h1 == h2
    assert len(h1) == 64


def test_snapshot_update_blocked_at_application_layer():
    with pytest.raises(CommercialSnapshotImmutableError):
        assert_snapshot_immutable()


def test_snapshot_persists_hash():
    async def _run():
        await engine.dispose()
        from app.services.portal_policy import ensure_default_policies

        async with async_session_factory() as db:
            await ensure_default_policies(db)
            await db.commit()
        terms = _sample_terms()
        terms_hash = compute_terms_hash(terms)
        async with async_session_factory() as db:
            from app.models.portal_policy import PortalPolicy
            from app.models.procurement import (
                BoqVersion,
                ProcurementPackage,
                ProcurementProject,
            )
            from app.models.user import User
            from app.core.security import hash_password

            user = User(
                email=f"snap-{uuid.uuid4().hex[:8]}@test.local",
                password_hash=hash_password("x"),
                full_name="Snap",
                role="buyer",
                is_active=True,
            )
            db.add(user)
            await db.flush()

            policy = (
                await db.execute(
                    select(PortalPolicy).where(
                        PortalPolicy.portal_key == "aislos",
                        PortalPolicy.status == "active",
                    )
                )
            ).scalar_one()

            project = ProcurementProject(
                owner_user_id=user.id,
                portal_key="aislos",
                portal_policy_id=policy.id,
                policy_snapshot_json={"portal_key": "aislos"},
                project_type="villa_smart_home",
                title="snap test",
                status="packaged",
                created_by=user.id,
            )
            db.add(project)
            await db.flush()

            boq = BoqVersion(
                project_id=project.id,
                version=1,
                status="frozen",
            )
            db.add(boq)
            await db.flush()

            package = ProcurementPackage(
                project_id=project.id,
                boq_version_id=boq.id,
                title="Lighting",
                trade="lighting",
                commercial_type="equipment",
                procurement_mode="managed",
                status="ready",
                revision=1,
            )
            db.add(package)
            await db.flush()

            snap = CommercialSnapshot(
                portal_key="aislos",
                portal_policy_id=policy.id,
                procurement_project_id=project.id,
                boq_version_id=boq.id,
                package_id=package.id,
                package_revision=1,
                currency=terms["currency"],
                exchange_rate_snapshot_json=terms["exchange_rate_snapshot_json"],
                tax_mode=terms["tax_mode"],
                margin_rule_json=terms["margin_rule_json"],
                service_fee_json=terms["service_fee_json"],
                warranty_rule_json=terms["warranty_rule_json"],
                delivery_region_json=terms["delivery_region_json"],
                quote_expiry=terms["quote_expiry"],
                payment_terms_json=terms["payment_terms_json"],
                terms_hash=terms_hash,
                created_by=user.id,
            )
            db.add(snap)
            await db.commit()
            await db.refresh(snap)
            assert snap.terms_hash == compute_terms_hash(terms)

    asyncio.run(_run())
