"""Public catalog and object-storage privacy boundaries."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.product import Product
from app.models.solution import Solution
from app.models.user import User


async def _user_headers(role: str = "buyer") -> tuple[dict[str, str], uuid.UUID]:
    async with async_session_factory() as db:
        user = User(
            email=f"catalog-security-{uuid.uuid4().hex[:10]}@example.com",
            password_hash=hash_password("catalog-security-123"),
            full_name="Catalog Security",
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        return (
            {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"},
            user.id,
        )


def test_public_catalog_hides_unpublished_products_and_solutions():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            product = Product(
                name="Private draft product",
                slug=f"private-draft-{uuid.uuid4().hex}",
                source_type="official",
                currency="EUR",
                moq=1,
                service_available=False,
                status="draft",
            )
            solution = Solution(
                title="Private solution",
                slug=f"private-solution-{uuid.uuid4().hex}",
                public_visible=False,
                sort_order=0,
            )
            db.add_all([product, solution])
            await db.commit()
            product_id, product_slug = product.id, product.slug
            solution_id, solution_slug = solution.id, solution.slug

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            public_list = await client.get("/api/v1/products?include_all=true")
            assert public_list.status_code == 200, public_list.text
            assert product_id not in {uuid.UUID(row["id"]) for row in public_list.json()["items"]}

            for path in (
                f"/api/v1/products/{product_id}",
                f"/api/v1/products/{product_slug}",
                f"/api/v1/solutions/{solution_id}",
                f"/api/v1/solutions/{solution_slug}",
            ):
                response = await client.get(path)
                assert response.status_code == 404, (path, response.text)

            public_inquiry = await client.post(
                "/api/v1/inquiries/public",
                json={
                    "product_id": str(product_id),
                    "contact_email": "catalog-security@example.com",
                    "message": "I should not be able to inquire about a draft",
                },
            )
            assert public_inquiry.status_code == 404, public_inquiry.text

    asyncio.run(_run())


def test_file_download_signing_is_owner_scoped(monkeypatch):
    class FakeMinio:
        def presigned_get_object(self, bucket: str, object_name: str, expires):
            return f"https://storage.example/{bucket}/{object_name}"

    async def _run():
        await engine.dispose()
        owner_headers, owner_id = await _user_headers()
        other_headers, _ = await _user_headers()
        admin_headers, _ = await _user_headers("admin")
        monkeypatch.setattr(
            "app.api.v1.endpoints.files.get_minio_client", lambda: FakeMinio()
        )
        object_name = f"uploads/{owner_id}/{uuid.uuid4()}/evidence.jpg"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            owner = await client.get(
                "/api/v1/files/download-url",
                params={"object_name": object_name},
                headers=owner_headers,
            )
            assert owner.status_code == 200, owner.text

            denied = await client.get(
                "/api/v1/files/download-url",
                params={"object_name": object_name},
                headers=other_headers,
            )
            assert denied.status_code == 403, denied.text

            admin = await client.get(
                "/api/v1/files/download-url",
                params={"object_name": object_name},
                headers=admin_headers,
            )
            assert admin.status_code == 200, admin.text

    asyncio.run(_run())
