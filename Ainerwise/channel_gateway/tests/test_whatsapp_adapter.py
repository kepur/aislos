from app.adapters.whatsapp import WhatsAppAdapter
from app.backend import BackendClient
from app.config import settings


def test_whatsapp_text_normalizes_to_shared_contract():
    adapter = WhatsAppAdapter(settings, BackendClient(settings))
    message = adapter.normalize(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "contacts": [{"profile": {"name": "Ana"}, "wa_id": "381601234567"}],
                                "messages": [
                                    {
                                        "from": "381601234567",
                                        "id": "wamid.42",
                                        "type": "text",
                                        "text": {"body": "Need a solar quote"},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }
    )

    assert message is not None
    assert message.external_thread_id == "381601234567"
    assert message.external_message_id == "wamid.42"
    assert message.contact_name == "Ana"
    assert message.content == "Need a solar quote"


def test_whatsapp_delivery_status_is_ignored():
    adapter = WhatsAppAdapter(settings, BackendClient(settings))
    assert adapter.normalize({"entry": [{"changes": [{"value": {"statuses": [{"id": "42"}]}}]}]}) is None
