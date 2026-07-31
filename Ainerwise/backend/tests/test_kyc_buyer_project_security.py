"""Security boundary tests for KYC verification and Buyer Project modules."""
import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.user import Company, User


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _create_identity(*, role: str, with_company: bool = True) -> tuple[str, str, uuid.UUID | None]:
    suffix = uuid.uuid4().hex[:10]
    email = f"kycbp-{role}-{suffix}@example.com"
    password = "kyctest123"
    async with async_session_factory() as db:
        company_id = None
        if with_company:
            company = Company(
                name=f"KYC {role} {suffix}",
                type="supplier" if role == "vendor" else "buyer",
                verification_status="verified",
            )
            db.add(company)
            await db.flush()
            company_id = company.id
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name=f"KYC {role}",
                role=role,
                company_id=company_id,
                is_active=True,
            )
        )
        await db.commit()
    return email, password, company_id


async def _login(email: str, password: str) -> dict:
    async with _client() as client:
        response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# ── KYC: company-scoped document isolation ──────────────────────────


def test_kyc_documents_scoped_to_own_company():
    async def _run():
        await engine.dispose()
        vendor_a_email, password, _ = await _create_identity(role="vendor")
        vendor_b_email, _, _ = await _create_identity(role="vendor")
        vendor_a = await _login(vendor_a_email, password)
        vendor_b = await _login(vendor_b_email, password)

        async with _client() as client:
            doc = await client.post(
                "/api/v1/kyc/documents",
                headers=vendor_a,
                json={
                    "doc_type": "BUSINESS_REGISTRATION",
                    "file_url": "https://storage.example.com/doc1.pdf",
                },
            )
            assert doc.status_code == 201, doc.text

            vendor_b_docs = await client.get("/api/v1/kyc/documents", headers=vendor_b)
            assert vendor_b_docs.status_code == 200
            assert vendor_b_docs.json()["total"] == 0

    asyncio.run(_run())


def test_companyless_user_cannot_upload_kyc():
    async def _run():
        await engine.dispose()
        email, password, _ = await _create_identity(role="buyer", with_company=False)
        headers = await _login(email, password)

        async with _client() as client:
            resp = await client.post(
                "/api/v1/kyc/documents",
                headers=headers,
                json={
                    "doc_type": "TAX_ID",
                    "file_url": "https://storage.example.com/tax.pdf",
                },
            )
            assert resp.status_code == 403

    asyncio.run(_run())


def test_regular_user_cannot_access_admin_kyc():
    async def _run():
        await engine.dispose()
        buyer_email, password, _ = await _create_identity(role="buyer")
        buyer = await _login(buyer_email, password)
        fake_company = str(uuid.uuid4())

        async with _client() as client:
            resp = await client.get(
                f"/api/v1/admin/kyc/documents/{fake_company}", headers=buyer
            )
            assert resp.status_code == 403

            queue = await client.get("/api/v1/admin/kyc/verification/queue", headers=buyer)
            assert queue.status_code == 403

    asyncio.run(_run())


# ── Buyer Project: owner isolation ──────────────────────────────────


def test_buyer_project_scoped_to_owner():
    async def _run():
        await engine.dispose()
        buyer_a_email, password, _ = await _create_identity(role="buyer")
        buyer_b_email, _, _ = await _create_identity(role="buyer")
        buyer_a = await _login(buyer_a_email, password)
        buyer_b = await _login(buyer_b_email, password)

        async with _client() as client:
            project = await client.post(
                "/api/v1/buyer/projects",
                headers=buyer_a,
                json={"title": "Solar Installation Project"},
            )
            assert project.status_code == 201, project.text
            project_id = project.json()["id"]

            buyer_b_list = await client.get("/api/v1/buyer/projects", headers=buyer_b)
            assert buyer_b_list.status_code == 200
            buyer_b_ids = {p["id"] for p in buyer_b_list.json()["items"]}
            assert project_id not in buyer_b_ids

            stranger_detail = await client.get(
                f"/api/v1/buyer/projects/{project_id}", headers=buyer_b
            )
            assert stranger_detail.status_code == 404

            stranger_update = await client.patch(
                f"/api/v1/buyer/projects/{project_id}",
                headers=buyer_b,
                json={"title": "Stolen Project"},
            )
            assert stranger_update.status_code == 404

            stranger_msg = await client.post(
                f"/api/v1/buyer/projects/{project_id}/messages",
                headers=buyer_b,
                json={"content": "Injection attempt"},
            )
            assert stranger_msg.status_code == 404

    asyncio.run(_run())


def test_unauthenticated_cannot_access_buyer_projects():
    async def _run():
        await engine.dispose()
        async with _client() as client:
            for path in (
                "/api/v1/buyer/projects",
                "/api/v1/kyc/documents",
                "/api/v1/kyc/verification/status",
            ):
                resp = await client.get(path)
                assert resp.status_code == 401, f"{path} returned {resp.status_code}"

    asyncio.run(_run())
