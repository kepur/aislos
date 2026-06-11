from app.adapters.telegram import TelegramAdapter
from app.backend import BackendClient
from app.config import settings


def test_telegram_update_normalizes_to_shared_contract():
    adapter = TelegramAdapter(settings, BackendClient(settings))
    message = adapter.normalize(
        {
            "update_id": 1,
            "message": {
                "message_id": 42,
                "from": {"first_name": "Mila", "last_name": "Jovanovic"},
                "chat": {"id": 1234, "type": "private"},
                "text": "Interested in the KNX RFQ",
            },
        }
    )

    assert message is not None
    assert message.external_thread_id == "1234"
    assert message.external_message_id == "42"
    assert message.contact_name == "Mila Jovanovic"
    assert message.content == "Interested in the KNX RFQ"


def test_telegram_non_message_update_is_ignored():
    adapter = TelegramAdapter(settings, BackendClient(settings))
    assert adapter.normalize({"update_id": 2, "callback_query": {}}) is None
