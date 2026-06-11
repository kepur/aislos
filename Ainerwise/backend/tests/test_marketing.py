"""Marketing attribution and review-first automation tests."""
from datetime import timedelta

from app.main import app
from app.models.lead import Lead
from app.schemas.inquiry import InquiryCreate
from app.schemas.lead import LeadCreate
from app.tasks.celery_app import celery_app
from app.services.marketing_automation import build_lead_follow_up_draft, follow_up_delay


def test_marketing_routes_registered():
    paths = {route.path for route in app.routes}
    for path in (
        "/api/v1/marketing/dashboard",
        "/api/v1/marketing/campaigns",
        "/api/v1/marketing/campaigns/{id}/prepare",
        "/api/v1/marketing/contacts",
        "/api/v1/marketing/activities",
    ):
        assert path in paths, path


def test_public_intake_schemas_accept_attribution():
    values = {
        "source_channel": "campaign",
        "utm_source": "showroom",
        "utm_medium": "qr",
        "utm_campaign": "open-day-june",
        "landing_page": "/submit-requirement?utm_campaign=open-day-june",
    }
    lead = LeadCreate(**values)
    inquiry = InquiryCreate(**values)
    assert lead.utm_campaign == inquiry.utm_campaign == "open-day-june"


def test_follow_up_delay_prioritizes_hot_leads():
    assert follow_up_delay(80) == timedelta(minutes=15)
    assert follow_up_delay(50) == timedelta(hours=4)
    assert follow_up_delay(10) == timedelta(hours=24)
    assert follow_up_delay(10, phase1_requested=True) == timedelta(minutes=15)


def test_follow_up_draft_is_preliminary_and_localized():
    lead = Lead(contact_name="Mila", project_type="Smart Hotel", language="sr")
    draft = build_lead_follow_up_draft(lead)
    assert "Mila" in draft["content"]
    assert "preliminarni" in draft["content"].lower()


def test_active_campaign_drafts_are_scheduled_daily():
    task = celery_app.conf.beat_schedule["prepare-active-marketing-campaigns"]
    assert task["task"] == "prepare_active_marketing_campaigns"
    celery_app.loader.import_default_modules()
    assert "prepare_active_marketing_campaigns" in celery_app.tasks
