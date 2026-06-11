from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.models.user import AccountType, User, UserRole, UserStatus
from app.services.notification_service import get_merged_notification_preferences


class FakeAsyncSession:
    def __init__(self):
        self.committed = False
        self.refreshed = []

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)


def make_user() -> User:
    return User(
        id=uuid4(),
        email="buyer@test.local",
        phone="09171234567",
        password_hash="hashed",
        role=UserRole.BUYER,
        status=UserStatus.ACTIVE,
        account_type=AccountType.BUSINESS,
        full_name="Buyer Demo",
        avatar_url=None,
        telegram_chat_id="buyer-chat-id",
        notification_preferences={
            "channels": {"email": True, "telegram": False},
            "events": {
                "new_message": True,
                "intent_match": True,
                "offer_received": True,
                "offer_awarded": True,
                "order_update": True,
                "delivery_update": True,
            },
        },
        totp_secret=None,
        two_fa_enabled=False,
        email_verified_at=None,
        phone_verified_at=None,
        last_login_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_get_merged_notification_preferences_keeps_defaults():
    prefs = get_merged_notification_preferences(
        {
            "channels": {"telegram": True},
            "events": {"new_message": False},
        }
    )

    assert prefs["channels"]["email"] is True
    assert prefs["channels"]["telegram"] is True
    assert prefs["events"]["new_message"] is False
    assert prefs["events"]["delivery_update"] is True


def test_notification_preferences_endpoints_support_get_and_patch():
    user = make_user()
    db = FakeAsyncSession()

    async def override_current_user():
        return user

    async def override_db():
        return db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            response = client.get("/users/me/notification-preferences")
            assert response.status_code == 200
            body = response.json()
            assert body["email"] == "buyer@test.local"
            assert body["telegram_connected"] is True
            assert body["channels"]["telegram"] is False

            patch_response = client.patch(
                "/users/me/notification-preferences",
                json={
                    "channels": {"telegram": True},
                    "events": {"new_message": False, "delivery_update": False},
                },
            )
            assert patch_response.status_code == 200
            patch_body = patch_response.json()
            assert patch_body["channels"]["email"] is True
            assert patch_body["channels"]["telegram"] is True
            assert patch_body["events"]["new_message"] is False
            assert patch_body["events"]["delivery_update"] is False
            assert user.notification_preferences["channels"]["telegram"] is True
            assert db.committed is True
            assert db.refreshed == [user]
    finally:
        app.dependency_overrides.clear()


def test_openapi_exposes_notification_preferences_route():
    with TestClient(app) as client:
        schema = client.get("/openapi.json")
        assert schema.status_code == 200
        paths = schema.json()["paths"]
        assert "/users/me/notification-preferences" in paths
        assert "get" in paths["/users/me/notification-preferences"]
        assert "patch" in paths["/users/me/notification-preferences"]