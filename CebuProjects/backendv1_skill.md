# Backend V1 Skill — ProcurePing Backend MVP

> Target stack: **FastAPI + PostgreSQL + SQLAlchemy + Alembic + JWT Auth + Local/S3-compatible file storage**  
> Principle: Keep V1 simple. Avoid unnecessary middleware. Do not introduce Kafka, RabbitMQ, Elasticsearch, Kubernetes, microservices, or complex payment rails in V1 unless explicitly requested later.

---

## 0. Product Summary

ProcurePing is a reverse-commerce / procurement marketplace.

Traditional e-commerce flow:

```text
Seller lists products → Buyer searches → Buyer buys
```

ProcurePing V1 flow:

```text
Buyer posts a purchase intent/request → Matching suppliers receive pings → Suppliers submit offers → Buyer selects an offer → Order is created → Buyer pays into escrow simulation → Supplier delivers → Buyer confirms receipt → Platform releases payout simulation
```

V1 must support:

- Buyer accounts
- Supplier accounts
- Admin/Ops accounts
- Product/category management
- Buyer purchase requests, called **Intents**
- Supplier offers
- Order lifecycle
- Escrow-style state machine, simulated first
- Telegram and email notifications
- Basic messaging
- Delivery proof upload
- Dispute handling
- Full audit logs for sensitive actions
- Admin console APIs

V1 does **not** need real payment gateway integration yet. However, the data model and order states must be designed so PayMongo/Xendit/Stripe can be added later without rewriting the backend.

---

## 1. Engineering Rules

### 1.1 Required Stack

Use:

```text
FastAPI
PostgreSQL
SQLAlchemy 2.x
Alembic
Pydantic v2
JWT access/refresh tokens
Passlib/bcrypt or argon2 for password hashing
Python email library or SMTP provider wrapper
Telegram Bot API via HTTP requests
Uvicorn/Gunicorn
```

Optional but allowed:

```text
Redis only for rate limiting or token blacklist if truly needed
MinIO/S3 only if file storage is required beyond local development
```

Do not use in V1 unless explicitly approved:

```text
Kafka
RabbitMQ
Celery
Elasticsearch
OpenSearch
Microservices
Kubernetes-specific logic
Complex event sourcing
Real escrow PSP integration
AI/NLP matching
```

### 1.2 Architecture Style

Use a modular monolith.

Suggested structure:

```text
backend/
  app/
    main.py
    core/
      config.py
      security.py
      database.py
      deps.py
      audit.py
      notifications.py
    models/
      user.py
      company.py
      category.py
      catalog.py
      intent.py
      offer.py
      order.py
      escrow.py
      delivery.py
      dispute.py
      message.py
      notification.py
      audit_log.py
    schemas/
      auth.py
      user.py
      company.py
      category.py
      catalog.py
      intent.py
      offer.py
      order.py
      escrow.py
      delivery.py
      dispute.py
      message.py
      notification.py
      audit_log.py
    services/
      auth_service.py
      matching_service.py
      notification_service.py
      escrow_service.py
      order_service.py
      dispute_service.py
      audit_service.py
    routers/
      auth.py
      users.py
      companies.py
      categories.py
      catalog.py
      intents.py
      offers.py
      orders.py
      deliveries.py
      disputes.py
      messages.py
      notifications.py
      admin.py
    migrations/
  alembic.ini
  requirements.txt
  .env.example
  README.md
```

---

## 2. User Roles

Implement RBAC using a `role` field on users.

Roles:

```text
BUYER
SUPPLIER_ADMIN
SUPPLIER_AGENT
ADMIN
AUDITOR
```

Permissions:

| Role | Permissions |
|---|---|
| BUYER | Create intents, view own intents, view offers on own intents, award offer, manage own orders, open disputes, send messages |
| SUPPLIER_ADMIN | Manage company, branches, catalog, supplier users, offers, orders, notification settings |
| SUPPLIER_AGENT | View matching intents, submit offers, manage assigned orders, send messages |
| ADMIN | Full operational control, verification, dispute resolution, manual state changes |
| AUDITOR | Read-only access to reports, audit logs, orders, disputes |

Important:

- Never allow suppliers to see buyer private contact details before an order is awarded.
- Never allow buyers to modify offers.
- Never allow normal users to modify escrow/payment states directly.
- All admin state changes must create audit logs.

---

## 3. Core Data Models

Use UUID primary keys unless the project standard prefers big integers.

### 3.1 User

Fields:

```text
id
email
phone
password_hash
role
status: ACTIVE | PENDING | SUSPENDED | DELETED
full_name
avatar_url
telegram_chat_id nullable
email_verified_at nullable
phone_verified_at nullable
created_at
updated_at
```

### 3.2 Company

Supplier business profile.

Fields:

```text
id
owner_user_id
name
tax_id nullable
country
city nullable
address nullable
verification_level: UNVERIFIED | BASIC | BUSINESS | TRUSTED
status: PENDING | ACTIVE | RESTRICTED | SUSPENDED
kyb_notes nullable
created_at
updated_at
```

### 3.3 Branch

Supplier physical branch or service location.

Fields:

```text
id
company_id
name
country
city
address
lat nullable
lng nullable
radius_km default 30
delivery_methods: JSON array
status: ACTIVE | INACTIVE
created_at
updated_at
```

### 3.4 Category

Fields:

```text
id
parent_id nullable
name
slug
schema_json: JSONB
status: ACTIVE | INACTIVE
created_at
updated_at
```

`schema_json` defines dynamic attributes for the category.

Example:

```json
{
  "required": ["brand", "model"],
  "fields": [
    {"key": "brand", "type": "string", "label": "Brand"},
    {"key": "model", "type": "string", "label": "Model"},
    {"key": "condition", "type": "enum", "options": ["new", "used", "refurbished"]}
  ]
}
```

### 3.5 CatalogItem

Supplier-listed item or service.

Fields:

```text
id
company_id
branch_id nullable
category_id
title
description
attrs_jsonb
price_minor
currency
stock_qty
unit
images: JSON array
tags: text array
status: DRAFT | ACTIVE | INACTIVE | OUT_OF_STOCK
created_at
updated_at
```

### 3.6 Intent

Buyer purchase request.

Fields:

```text
id
buyer_id
category_id
title
attrs_jsonb
qty
unit
budget_min_minor
budget_max_minor
currency
country
city nullable
lat nullable
lng nullable
radius_km default 30
delivery_window_start nullable
delivery_window_end nullable
notes nullable
attachments: JSON array
status: DRAFT | ACTIVE | AWARDED | EXPIRED | CANCELED
expires_at nullable
created_at
updated_at
```

### 3.7 Offer

Supplier response to buyer intent.

Fields:

```text
id
intent_id
company_id
branch_id nullable
catalog_item_id nullable
supplier_user_id
unit_price_minor
qty_available
delivery_fee_minor default 0
total_price_minor
currency
eta_date nullable
warranty nullable
tier: GOOD | BETTER | BEST | CUSTOM
stock_confidence: FIRM | BACKORDER | UNKNOWN
message nullable
status: SUBMITTED | WITHDRAWN | EXPIRED | AWARDED | REJECTED
expires_at nullable
created_at
updated_at
```

### 3.8 Order

Created when a buyer awards an offer.

Fields:

```text
id
offer_id
intent_id
buyer_id
company_id
branch_id nullable
total_amount_minor
currency
status: CREATED | AWAITING_PAYMENT | PAID_IN_ESCROW | IN_PROGRESS | DELIVERED | ACCEPTED | PAYOUT_RELEASED | DISPUTED | CANCELED | REFUNDED
created_at
updated_at
```

### 3.9 EscrowTransaction

V1 is simulated but must behave like real escrow.

Fields:

```text
id
order_id
provider: SIMULATED | PAYMONGO | XENDIT | STRIPE
provider_reference nullable
auth_amount_minor
captured_amount_minor default 0
released_amount_minor default 0
refunded_amount_minor default 0
currency
status: AUTH_PENDING | AUTH_HELD | CAPTURED | RELEASED | REFUNDED | CHARGEBACK | FAILED
raw_event_json nullable
created_at
updated_at
```

### 3.10 Delivery

Fields:

```text
id
order_id
status: PENDING | READY_FOR_PICKUP | DISPATCHED | DELIVERED | ACCEPTED | FAILED
carrier nullable
tracking_number nullable
notes nullable
proofs: JSON array
actor_id
created_at
updated_at
```

### 3.11 Dispute

Fields:

```text
id
order_id
opened_by_user_id
reason
status: OPENED | WAITING_BUYER_EVIDENCE | WAITING_SUPPLIER_EVIDENCE | UNDER_REVIEW | RESOLVED_REFUND | RESOLVED_RELEASE | RESOLVED_PARTIAL_REFUND | ESCALATED | CANCELED
evidence_json: JSON array
admin_notes nullable
resolution nullable
refund_amount_minor nullable
created_at
updated_at
```

### 3.12 Message

Fields:

```text
id
thread_type: INTENT | ORDER | DISPUTE
thread_id
sender_id
body
attachments: JSON array
created_at
```

### 3.13 Notification

Fields:

```text
id
user_id
channel: IN_APP | EMAIL | TELEGRAM
notification_type
subject nullable
body
status: PENDING | SENT | FAILED | READ
provider_response nullable
created_at
sent_at nullable
read_at nullable
```

### 3.14 AuditLog

Mandatory for sensitive operations.

Fields:

```text
id
actor_id nullable
actor_role nullable
action
entity_type
entity_id
before_json nullable
after_json nullable
ip_address nullable
user_agent nullable
risk_level: LOW | MEDIUM | HIGH | CRITICAL
created_at
```

Audit these actions at minimum:

```text
USER_REGISTERED
USER_LOGIN_FAILED
COMPANY_VERIFICATION_CHANGED
INTENT_CREATED
INTENT_CANCELED
OFFER_SUBMITTED
OFFER_AWARDED
ORDER_CREATED
ORDER_STATUS_CHANGED
ESCROW_STATUS_CHANGED
DELIVERY_PROOF_UPLOADED
ORDER_ACCEPTED
DISPUTE_OPENED
DISPUTE_RESOLVED
ADMIN_MANUAL_ACTION
USER_SUSPENDED
COMPANY_SUSPENDED
```

---

## 4. State Machines

### 4.1 Intent

```text
DRAFT → ACTIVE → AWARDED
DRAFT → CANCELED
ACTIVE → EXPIRED
ACTIVE → CANCELED
```

Rules:

- Only buyer can create/cancel own intent.
- Intent becomes `AWARDED` only after an offer is awarded.
- No new offers can be submitted after `AWARDED`, `EXPIRED`, or `CANCELED`.

### 4.2 Offer

```text
SUBMITTED → AWARDED
SUBMITTED → REJECTED
SUBMITTED → WITHDRAWN
SUBMITTED → EXPIRED
```

Rules:

- Supplier can withdraw own offer before awarded.
- Buyer can award only one offer in V1.
- When one offer is awarded, other offers for the same intent become `REJECTED`.

### 4.3 Order

```text
CREATED
→ AWAITING_PAYMENT
→ PAID_IN_ESCROW
→ IN_PROGRESS
→ DELIVERED
→ ACCEPTED
→ PAYOUT_RELEASED
```

Exception paths:

```text
PAID_IN_ESCROW → DISPUTED
IN_PROGRESS → DISPUTED
DELIVERED → DISPUTED
DISPUTED → REFUNDED
DISPUTED → PAYOUT_RELEASED
DISPUTED → ACCEPTED
```

### 4.4 Escrow

```text
AUTH_PENDING → AUTH_HELD → CAPTURED → RELEASED
CAPTURED → REFUNDED
CAPTURED → CHARGEBACK
AUTH_PENDING → FAILED
```

For V1 simulated payment:

- Awarding an offer can create an escrow record with `CAPTURED` or `AUTH_HELD` depending on endpoint.
- Admin test endpoint may simulate payment success/failure.
- Buyer acceptance triggers simulated release.
- Dispute pauses release.

---

## 5. Main User Flows

### 5.1 Buyer Creates Intent

Endpoint:

```http
POST /intents
```

Request:

```json
{
  "category_id": "uuid",
  "title": "Need 500 bags Holcim cement",
  "attrs": {"brand": "Holcim", "type": "Portland", "bag_weight_kg": 40},
  "qty": 500,
  "unit": "bag",
  "budget_min_minor": 24000000,
  "budget_max_minor": 26000000,
  "currency": "PHP",
  "city": "Cebu",
  "lat": 10.3157,
  "lng": 123.8854,
  "radius_km": 30,
  "delivery_window_start": "2026-06-01T08:00:00Z",
  "delivery_window_end": "2026-06-02T18:00:00Z",
  "notes": "Need factory fresh, no clumped bags."
}
```

Backend actions:

1. Validate buyer role.
2. Validate category exists.
3. Validate required category attributes.
4. Create `Intent` as `ACTIVE`.
5. Create audit log `INTENT_CREATED`.
6. Run simple matching service.
7. Create notifications for matched suppliers.
8. Send email/Telegram where configured.

### 5.2 Supplier Receives Ping

Matching V1:

Supplier is eligible if:

```text
company.status = ACTIVE
company.verification_level in BASIC/BUSINESS/TRUSTED
catalog item category matches intent category
catalog item status = ACTIVE
branch radius includes buyer location, if location data exists
```

Score:

```text
category match: 40
attribute overlap: 0-30
geo proximity: 0-20
supplier trust: 0-10
```

Notify suppliers with score >= 50.

No ML in V1.

### 5.3 Supplier Submits Offer

Endpoint:

```http
POST /intents/{intent_id}/offers
```

Request:

```json
{
  "catalog_item_id": "uuid",
  "unit_price_minor": 49500,
  "qty_available": 500,
  "delivery_fee_minor": 500000,
  "currency": "PHP",
  "eta_date": "2026-06-01",
  "warranty": "Replacement for damaged bags on delivery",
  "tier": "GOOD",
  "stock_confidence": "FIRM",
  "message": "Can deliver tomorrow morning.",
  "expires_at": "2026-05-31T10:00:00Z"
}
```

Backend actions:

1. Validate supplier role.
2. Validate supplier company is active and verified.
3. Validate intent is active.
4. Calculate total price:

```text
total_price = unit_price * qty_available + delivery_fee
```

5. Create `Offer`.
6. Create audit log `OFFER_SUBMITTED`.
7. Notify buyer by in-app/email/Telegram if enabled.

### 5.4 Buyer Awards Offer

Endpoint:

```http
POST /offers/{offer_id}/award
```

Backend actions:

1. Validate buyer owns the intent.
2. Validate offer is submitted and not expired.
3. Create order.
4. Set selected offer to `AWARDED`.
5. Set other offers for same intent to `REJECTED`.
6. Set intent to `AWARDED`.
7. Create simulated escrow transaction.
8. Set order status to `PAID_IN_ESCROW` or `AWAITING_PAYMENT` depending config.
9. Create audit logs:

```text
OFFER_AWARDED
ORDER_CREATED
ESCROW_STATUS_CHANGED
```

10. Notify supplier.

### 5.5 Supplier Updates Delivery

Endpoint:

```http
POST /orders/{order_id}/delivery
```

Statuses:

```text
READY_FOR_PICKUP
DISPATCHED
DELIVERED
```

Supplier may upload proof images or documents.

Backend actions:

1. Validate supplier owns order.
2. Create delivery record.
3. Update order status.
4. Create audit log.
5. Notify buyer.

### 5.6 Buyer Accepts Delivery

Endpoint:

```http
POST /orders/{order_id}/accept
```

Backend actions:

1. Validate buyer owns order.
2. Validate order status is `DELIVERED`.
3. Set order status to `ACCEPTED`.
4. Set escrow status to `RELEASED`.
5. Set order status to `PAYOUT_RELEASED`.
6. Create audit logs.
7. Notify supplier.

### 5.7 Buyer Opens Dispute

Endpoint:

```http
POST /orders/{order_id}/dispute
```

Request:

```json
{
  "reason": "Item not delivered as described",
  "evidence": [
    {"type": "image", "url": "..."},
    {"type": "text", "body": "Received damaged bags."}
  ]
}
```

Backend actions:

1. Validate buyer owns order or supplier is party to order.
2. Set order status to `DISPUTED`.
3. Create dispute record.
4. Pause escrow release.
5. Create audit log `DISPUTE_OPENED`.
6. Notify admin and other party.

### 5.8 Admin Resolves Dispute

Endpoint:

```http
POST /admin/disputes/{dispute_id}/resolve
```

Request:

```json
{
  "decision": "PARTIAL_REFUND",
  "refund_amount_minor": 500000,
  "resolution": "Partial refund due to damaged quantity. Remaining amount released to supplier."
}
```

Allowed decisions:

```text
FULL_REFUND
PARTIAL_REFUND
RELEASE_TO_SUPPLIER
REQUEST_MORE_EVIDENCE
ESCALATE
```

Backend actions:

1. Validate admin role.
2. Update dispute.
3. Update order.
4. Update escrow simulated amounts.
5. Create high-risk audit log.
6. Notify buyer and supplier.

---

## 6. API Endpoints

### 6.1 Auth

```http
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
```

### 6.2 Users

```http
GET    /users/me
PATCH  /users/me
PATCH  /users/me/telegram
```

### 6.3 Companies / Suppliers

```http
POST   /companies
GET    /companies/me
PATCH  /companies/me
POST   /companies/me/branches
GET    /companies/me/branches
PATCH  /companies/me/branches/{branch_id}
```

### 6.4 Categories

```http
GET    /categories
POST   /admin/categories
PATCH  /admin/categories/{category_id}
GET    /categories/{category_id}/schema
```

### 6.5 Catalog

```http
POST   /supplier/catalog/items
GET    /supplier/catalog/items
GET    /supplier/catalog/items/{item_id}
PATCH  /supplier/catalog/items/{item_id}
DELETE /supplier/catalog/items/{item_id}
```

### 6.6 Intents

```http
POST   /intents
GET    /intents/my
GET    /intents/{intent_id}
PATCH  /intents/{intent_id}
POST   /intents/{intent_id}/cancel
GET    /supplier/intents/matching
```

### 6.7 Offers

```http
POST   /intents/{intent_id}/offers
GET    /intents/{intent_id}/offers
GET    /supplier/offers
POST   /offers/{offer_id}/withdraw
POST   /offers/{offer_id}/award
```

### 6.8 Orders

```http
GET    /orders/my
GET    /orders/{order_id}
POST   /orders/{order_id}/accept
POST   /admin/orders/{order_id}/status
```

### 6.9 Delivery

```http
POST   /orders/{order_id}/delivery
GET    /orders/{order_id}/delivery
```

### 6.10 Disputes

```http
POST   /orders/{order_id}/dispute
GET    /disputes/my
GET    /disputes/{dispute_id}
POST   /disputes/{dispute_id}/evidence
POST   /admin/disputes/{dispute_id}/resolve
```

### 6.11 Messages

```http
POST   /threads/{thread_type}/{thread_id}/messages
GET    /threads/{thread_type}/{thread_id}/messages
```

### 6.12 Notifications

```http
GET    /notifications/my
POST   /notifications/{notification_id}/read
POST   /admin/notifications/test-email
POST   /admin/notifications/test-telegram
```

### 6.13 Admin

```http
GET    /admin/dashboard
GET    /admin/users
PATCH  /admin/users/{user_id}/status
GET    /admin/companies
PATCH  /admin/companies/{company_id}/verification
PATCH  /admin/companies/{company_id}/status
GET    /admin/intents
GET    /admin/offers
GET    /admin/orders
GET    /admin/disputes
GET    /admin/audit-logs
```

---

## 7. Notification Requirements

### 7.1 Supported Channels

V1 must support:

```text
IN_APP
EMAIL
TELEGRAM
```

### 7.2 Telegram API

Use Telegram Bot API.

Environment variables:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_ENABLED=true
```

User must be able to bind Telegram chat ID manually in V1:

```http
PATCH /users/me/telegram
```

Request:

```json
{"telegram_chat_id": "123456789"}
```

Telegram sending function:

```text
POST https://api.telegram.org/bot{TOKEN}/sendMessage
```

Do not block business flow if Telegram fails. Save notification status as `FAILED` and continue.

### 7.3 Email

Use SMTP for V1.

Environment variables:

```env
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
EMAIL_ENABLED=true
```

Do not block business flow if email fails. Save notification status as `FAILED` and continue.

### 7.4 Notification Templates

Implement simple string templates.

Required templates:

```text
NEW_INTENT_FOR_SUPPLIER
NEW_OFFER_FOR_BUYER
OFFER_AWARDED_SUPPLIER
ORDER_CREATED_BUYER
DELIVERY_UPDATED_BUYER
ORDER_ACCEPTED_SUPPLIER
DISPUTE_OPENED_ADMIN
DISPUTE_UPDATED_PARTIES
```

---

## 8. Audit Requirements

### 8.1 General Rule

Every sensitive business action must create an audit log.

Audit logging must never fail the main business action unless database transaction fails.

### 8.2 Risk Levels

Use:

```text
LOW: normal create/update actions
MEDIUM: order state changes, offer award
HIGH: escrow/payment/dispute/company verification
CRITICAL: refunds, admin override, suspension, chargeback
```

### 8.3 Admin Audit View

Endpoint:

```http
GET /admin/audit-logs
```

Filters:

```text
actor_id
entity_type
entity_id
action
risk_level
created_at_from
created_at_to
```

---

## 9. Security Requirements

### 9.1 Authentication

- JWT access token with short TTL.
- Refresh token with longer TTL.
- Hash passwords securely.
- Never store plaintext password.
- Login failure should create audit log after repeated failures.

### 9.2 Authorization

- Use dependency functions for role checks.
- Check resource ownership on every endpoint.
- Admin and auditor endpoints must be protected.

### 9.3 Privacy

Before order award:

- Supplier cannot see buyer phone/email.
- Buyer cannot see supplier banking details.

After order award:

- Show only required contact and delivery information.

### 9.4 File Uploads

V1 can use local filesystem in development.

Rules:

- Validate file size.
- Validate MIME type.
- Store generated filename, not original filename only.
- Return file URL/path.
- Later replace with S3/MinIO adapter.

Allowed upload types:

```text
image/jpeg
image/png
image/webp
application/pdf
```

---

## 10. Admin Dashboard Requirements

Admin dashboard endpoint:

```http
GET /admin/dashboard
```

Return:

```json
{
  "users_total": 1200,
  "buyers_total": 800,
  "suppliers_total": 300,
  "active_intents": 45,
  "offers_today": 120,
  "orders_today": 12,
  "orders_in_escrow": 8,
  "open_disputes": 3,
  "pending_company_verifications": 5
}
```

Admin must be able to:

```text
View users
Suspend users
View companies
Approve/reject company verification
View intents
View offers
View orders
View escrow simulation state
View disputes
Resolve disputes
View audit logs
Send test email/Telegram notification
```

---

## 11. MVP Matching Logic

Keep V1 simple.

When an intent is created:

1. Find active catalog items in same category.
2. Filter by active company and verified supplier.
3. If both intent and branch have coordinates, filter by branch radius.
4. Calculate attribute overlap score.
5. Notify top suppliers.

Example scoring:

```python
score = 0
if category_match:
    score += 40
score += min(attribute_overlap_count * 10, 30)
if within_radius:
    score += 20
if company.verification_level == "TRUSTED":
    score += 10
elif company.verification_level == "BUSINESS":
    score += 7
elif company.verification_level == "BASIC":
    score += 5
```

Notify if:

```text
score >= 50
```

Limit notifications:

```text
max 50 suppliers per intent in V1
```

---

## 12. Payment/Escrow Simulation

V1 should not integrate real payment by default.

Implement a clean abstraction:

```python
class EscrowProvider:
    def authorize(...): ...
    def capture(...): ...
    def release(...): ...
    def refund(...): ...
```

Implement:

```text
SimulatedEscrowProvider
```

Later implementations:

```text
PayMongoEscrowProvider
XenditEscrowProvider
StripeEscrowProvider
```

Simulated behavior:

- On award offer: create escrow transaction.
- If `ESCROW_AUTO_CAPTURE=true`, set escrow to `CAPTURED` and order to `PAID_IN_ESCROW`.
- On buyer accept: set escrow to `RELEASED`.
- On dispute: do not release.
- On admin refund: set escrow to `REFUNDED` or partially refunded.

Environment:

```env
ESCROW_PROVIDER=SIMULATED
ESCROW_AUTO_CAPTURE=true
```

---

## 13. Environment Variables

`.env.example` must include:

```env
APP_NAME=ProcurePing Backend
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/procureping
JWT_SECRET=change-me
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

CORS_ORIGINS=http://localhost:3000,http://localhost:5173

UPLOAD_STORAGE=local
UPLOAD_DIR=./uploads
PUBLIC_FILE_BASE_URL=http://localhost:8000/uploads

EMAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=no-reply@procureping.local

TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=

ESCROW_PROVIDER=SIMULATED
ESCROW_AUTO_CAPTURE=true
```

---

## 14. Acceptance Criteria

### 14.1 Backend Boot

- Backend starts with `uvicorn app.main:app --reload`.
- `/health` returns `200 OK`.
- OpenAPI docs available at `/docs`.
- Alembic migrations run successfully.

### 14.2 Auth

- User can register as buyer.
- User can register as supplier admin.
- User can login.
- JWT protected endpoints reject unauthenticated requests.
- Role-protected endpoints reject wrong role.

### 14.3 Buyer Intent

- Buyer can create an intent.
- Buyer can list own intents.
- Intent creation creates audit log.
- Intent creation triggers supplier matching.
- Matched suppliers receive in-app notifications.
- Email/Telegram send attempts are recorded if enabled.

### 14.4 Supplier Offer

- Supplier can create catalog item.
- Supplier can see matching intents.
- Supplier can submit offer.
- Buyer can see offers for own intent.
- Offer submission creates audit log and notification.

### 14.5 Order and Escrow

- Buyer can award an offer.
- Order is created.
- Other offers are rejected.
- Simulated escrow is created.
- Buyer can accept delivered order.
- Escrow status becomes released.
- Audit logs are created.

### 14.6 Delivery

- Supplier can update delivery status.
- Supplier can upload proof.
- Buyer can see delivery updates.

### 14.7 Dispute

- Buyer can open dispute.
- Order becomes disputed.
- Escrow is not released while disputed.
- Admin can resolve dispute.
- Resolution creates high-risk or critical audit log.

### 14.8 Admin

- Admin can view dashboard.
- Admin can view users, companies, intents, offers, orders, disputes, audit logs.
- Admin can approve/suspend companies.
- Auditor can read audit logs but cannot modify anything.

---

## 15. Suggested Implementation Order

Implement in this order:

```text
1. Project setup, config, DB, health check
2. User model, auth, JWT, RBAC
3. Company and branch models
4. Category and schema model
5. Catalog item model
6. Intent model and buyer endpoints
7. Matching service V1
8. Notification model + in-app notifications
9. Email and Telegram senders
10. Offer model and supplier endpoints
11. Award offer → order creation
12. Simulated escrow provider
13. Delivery updates and proof upload
14. Dispute module
15. Audit log service integration
16. Admin dashboard and admin APIs
17. Tests and seed data
```

---

## 16. Seed Data

Create seed script with:

```text
Admin user
Buyer test user
Supplier admin test user
Supplier company
Supplier branch in Cebu
Categories: Construction, IT/Office, Auto
Example category schema for Cement and Laptop
Example catalog items
```

---

## 17. Testing Requirements

Minimum tests:

```text
Auth register/login
RBAC access control
Buyer creates intent
Supplier matching returns expected supplier
Supplier submits offer
Buyer awards offer
Escrow simulated capture/release
Supplier updates delivery
Buyer opens dispute
Admin resolves dispute
Audit logs created for key actions
```

Use pytest.

---

## 18. Non-Goals for Backend V1

Do not implement these in V1:

```text
Real payment gateway
Real logistics API
Mobile push notification
SMS
AI image recognition
AI natural language parsing
Advanced price-band intelligence
Full tax/VAT invoicing
Public marketplace browsing
Complex ad/promoted offer system
Multi-supplier split orders
Auto-award logic
Financing/lending
```

Design database and services so these can be added later.

---

## 19. Definition of Done

Backend V1 is complete when:

```text
A buyer can register and post an intent.
A verified supplier can receive the ping and submit an offer.
The buyer can award the offer.
An order and simulated escrow transaction are created.
The supplier can mark delivery and upload proof.
The buyer can accept delivery and trigger simulated payout release.
The buyer or supplier can open a dispute.
Admin can resolve the dispute.
All critical actions are audit logged.
Telegram and email notifications are supported and failure-safe.
The API is documented in FastAPI OpenAPI.
```
