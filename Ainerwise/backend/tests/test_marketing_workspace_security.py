"""Workspace isolation for Marketing operators and AinerN2D work items."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.marketing import (
    MarketingActivity,
    MarketingAsset,
    MarketingCampaign,
    MarketingContact,
    MarketingCreativeBrief,
    MarketingCreativeBriefVersion,
    MarketingMediaRequest,
)
from app.models.portal_access import Workspace
from app.models.user import User
from app.services.portal_access import sync_role_portal_access


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}


def test_marketing_operator_requires_exact_workspace():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Marketing A {suffix}", slug=f"marketing-a-{suffix}")
            workspace_b = Workspace(name=f"Marketing B {suffix}", slug=f"marketing-b-{suffix}")
            operator = User(
                email=f"marketing-scope-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="marketing_operator",
            )
            db.add_all([workspace_a, workspace_b, operator])
            await db.flush()
            await sync_role_portal_access(
                db,
                user_id=operator.id,
                role=operator.role,
                workspace_id=workspace_a.id,
            )
            campaign_a = MarketingCampaign(
                workspace_id=workspace_a.id,
                name="Workspace A campaign",
                channel="email",
                utm_campaign=f"a-{suffix}",
            )
            campaign_b = MarketingCampaign(
                workspace_id=workspace_b.id,
                name="Workspace B private campaign",
                channel="email",
                utm_campaign=f"b-{suffix}",
            )
            contact_a = MarketingContact(workspace_id=workspace_a.id, email=f"a-{suffix}@example.com")
            contact_b = MarketingContact(workspace_id=workspace_b.id, email=f"b-{suffix}@example.com")
            db.add_all([campaign_a, campaign_b, contact_a, contact_b])
            await db.flush()
            activity_a = MarketingActivity(
                workspace_id=workspace_a.id,
                campaign_id=campaign_a.id,
                contact_id=contact_a.id,
                activity_type="campaign_outreach",
                channel="email",
            )
            activity_b = MarketingActivity(
                workspace_id=workspace_b.id,
                campaign_id=campaign_b.id,
                contact_id=contact_b.id,
                activity_type="campaign_outreach",
                channel="email",
            )
            brief_a = MarketingCreativeBrief(workspace_id=workspace_a.id, title="Workspace A brief")
            brief_b = MarketingCreativeBrief(workspace_id=workspace_b.id, title="Workspace B private brief")
            asset_a = MarketingAsset(
                workspace_id=workspace_a.id,
                kind="image",
                lang="en",
                status="in_review",
            )
            asset_b = MarketingAsset(
                workspace_id=workspace_b.id,
                kind="image",
                lang="en",
                status="in_review",
            )
            db.add_all([activity_a, activity_b, brief_a, brief_b, asset_a, asset_b])
            await db.flush()
            version_b = MarketingCreativeBriefVersion(
                brief_id=brief_b.id,
                version=1,
                status="approved",
            )
            db.add(version_b)
            await db.flush()
            request_b = MarketingMediaRequest(
                workspace_id=workspace_b.id,
                brief_version_id=version_b.id,
                deliverable_key="private-b",
            )
            db.add(request_b)
            await db.commit()
            ids = {
                "workspace_a": str(workspace_a.id),
                "workspace_b": str(workspace_b.id),
                "campaign_a": str(campaign_a.id),
                "campaign_b": str(campaign_b.id),
                "contact_a": str(contact_a.id),
                "contact_b": str(contact_b.id),
                "activity_a": str(activity_a.id),
                "activity_b": str(activity_b.id),
                "brief_a": str(brief_a.id),
                "brief_b": str(brief_b.id),
                "asset_a": str(asset_a.id),
                "asset_b": str(asset_b.id),
                "version_b": str(version_b.id),
            }
            headers = _headers(operator)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for path, allowed_id, denied_id in (
                ("/api/v1/marketing/campaigns", ids["campaign_a"], ids["campaign_b"]),
                ("/api/v1/marketing/contacts", ids["contact_a"], ids["contact_b"]),
                ("/api/v1/marketing/activities", ids["activity_a"], ids["activity_b"]),
                ("/api/v1/admin/marketing/creative-briefs", ids["brief_a"], ids["brief_b"]),
                ("/api/v1/admin/marketing/assets", ids["asset_a"], ids["asset_b"]),
            ):
                response = await client.get(path, headers=headers)
                assert response.status_code == 200, (path, response.text)
                result_ids = {item["id"] for item in response.json()["items"]}
                assert allowed_id in result_ids
                assert denied_id not in result_ids

            denied_campaign = await client.get(
                f"/api/v1/marketing/campaigns/{ids['campaign_b']}", headers=headers
            )
            assert denied_campaign.status_code == 403, denied_campaign.text
            denied_brief = await client.get(
                f"/api/v1/admin/marketing/creative-briefs/{ids['brief_b']}", headers=headers
            )
            assert denied_brief.status_code == 403, denied_brief.text
            denied_media = await client.get(
                f"/api/v1/admin/marketing/creative-brief-versions/{ids['version_b']}/media-requests",
                headers=headers,
            )
            assert denied_media.status_code == 403, denied_media.text
            denied_asset = await client.post(
                f"/api/v1/admin/marketing/assets/{ids['asset_b']}/approve",
                headers=headers,
                json={},
            )
            assert denied_asset.status_code == 403, denied_asset.text
            forged = await client.post(
                "/api/v1/marketing/campaigns",
                headers=headers,
                json={
                    "workspace_id": ids["workspace_b"],
                    "name": "Forged campaign",
                    "channel": "email",
                    "utm_campaign": f"forged-{suffix}",
                },
            )
            assert forged.status_code == 403, forged.text
            mixed = await client.post(
                "/api/v1/marketing/activities",
                headers=headers,
                json={
                    "workspace_id": ids["workspace_a"],
                    "campaign_id": ids["campaign_a"],
                    "contact_id": ids["contact_b"],
                    "activity_type": "campaign_outreach",
                    "channel": "email",
                },
            )
            assert mixed.status_code == 409, mixed.text

    asyncio.run(_run())
