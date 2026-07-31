from app.adapters.email import EmailAdapter
from app.backend import BackendClient
from app.config import settings


def test_email_json_normalizes_to_shared_contract():
    adapter = EmailAdapter(settings, BackendClient(settings))
    message = adapter.normalize(
        {
            "message_id": "<message-42@example.com>",
            "from": {"name": "Mila Jovanovic", "email": "Mila@Example.com"},
            "subject": "Hotel lock RFQ",
            "text": "Please quote 40 rooms.",
        }
    )

    assert message is not None
    assert message.external_thread_id == "mila@example.com"
    assert message.external_message_id == "<message-42@example.com>"
    assert message.contact_name == "Mila Jovanovic"
    assert message.content == "Hotel lock RFQ\n\nPlease quote 40 rooms."


def test_email_provider_form_normalizes_to_shared_contract():
    adapter = EmailAdapter(settings, BackendClient(settings))
    message = adapter.normalize(
        {
            "Message-Id": "<provider-message@example.com>",
            "sender": "Marko Petrovic <marko@example.com>",
            "subject": "Site visit",
            "body-plain": "Tuesday works.",
        }
    )

    assert message is not None
    assert message.external_thread_id == "marko@example.com"
    assert message.contact_name == "Marko Petrovic"
    assert message.content == "Site visit\n\nTuesday works."


def test_email_without_valid_sender_is_ignored():
    adapter = EmailAdapter(settings, BackendClient(settings))
    assert adapter.normalize({"subject": "No sender"}) is None
