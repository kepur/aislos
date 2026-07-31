# ZL13 Shared Channel Gateway Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. The implementing Agent does not mark
this work `VERIFIED`; an independent verification Agent must replay real
provider webhooks and outbound delivery.

## Delivered

- Kept one physical `channel-gateway` middleware service and one shared
  `ChannelAdapter` contract.
- Added WhatsApp Business Cloud API outbound delivery and inbound
  normalization.
- Added Meta webhook subscription verification and mandatory HMAC signature
  verification for inbound WhatsApp messages.
- Added provider-neutral Email webhook normalization and SMTP outbound
  delivery.
- Added mandatory Email webhook secret verification.
- Extended outbound metadata so Email can use a subject and optional HTML
  while Telegram and WhatsApp keep the same contract.
- Reused the existing `channels.channel_accounts`, `channel_threads`,
  `channel_messages`, and `delivery_log` persistence and idempotency path.
- Added Admin integration configuration and test delivery for WhatsApp and
  Gateway-backed SMTP.
- Kept secrets masked in Admin responses and exposed them only through the
  service-token-protected internal adapter endpoint.
- Kept `CebuProjects` unchanged.

## Security Rules

- WhatsApp inbound delivery fails closed when the App Secret is missing or the
  `X-Hub-Signature-256` signature is invalid.
- Email inbound delivery fails closed when the webhook secret is missing or
  invalid.
- WhatsApp verify tokens, App Secret, access token, SMTP password, and Email
  webhook secret are masked from Admin reads.
- Gateway outbound delivery remains idempotent by caller-supplied message ID.
- The Gateway remains Docker-internal; nginx only exposes `/webhooks/{channel}`.

## Verification Evidence

```text
channel-gateway focused tests: 11 passed, 2 warnings
backend integration + shared middleware focused tests: 11 passed, 2 warnings
backend full suite: 385 passed, 3 warnings
frontend-admin production build: passed
channel-gateway container rebuild: passed; email/telegram/whatsapp registered
feature parity ledger: 5470 entries
runtime API coverage: 683 / 683
alembic current: 057 (head)
alembic check: No new upgrade operations detected
git diff --check: passed
CebuProjects working tree: unchanged
```

## Independent Verification Checklist

- [ ] Replay a signed Meta WhatsApp verification request and inbound text,
      media-caption, and interactive-reply message.
- [ ] Send a real WhatsApp outbound message and verify durable idempotency.
- [ ] Replay the selected production Email provider's signed webhook format.
- [ ] Send a real SMTP outbound message and verify subject, text, and HTML.
- [ ] Confirm invalid/missing signatures produce `401` or fail-closed `503`.
- [ ] Confirm secrets never appear in Admin/API/browser responses or logs.
- [ ] Confirm retry behavior with provider timeout and duplicate message IDs.
