

# ProcurePing / Sanaoll Enterprise Admin Console Requirements

Version: v1.0  
Target: PC Web Admin Console  
Frontend: Enterprise desktop-first admin UI  
Backend: FastAPI monolith API  
Default language: English  
I18n ready: 10 languages  
Branding: use `{{APP_NAME}}` and `{{APP_DOMAIN}}`, do not hardcode the final site name

---

## 1. Product Positioning

This document defines the enterprise-grade backend operation console for a reverse e-commerce / buyer-request marketplace.

The platform flow is:

```text
Buyer posts purchase intent
→ verified suppliers receive pings
→ suppliers submit offers
→ buyer awards offer
→ buyer pays into escrow
→ supplier fulfills order
→ buyer confirms delivery
→ funds are released
→ disputes, refunds, audits and risk actions are handled by platform operations
```

The Admin Console is not a simple CRUD backend. It is the control center for:

- marketplace operations
- supplier verification
- buyer intent supervision
- offer and order monitoring
- escrow and payment tracking
- dispute resolution
- fraud and risk control
- notification management
- audit logs
- category/schema configuration
- region/currency/language management
- platform staff permission management

The UI must be PC-first, enterprise-grade, data-dense, and suitable for daily operations by platform staff.

---

## 2. Design Goals

### 2.1 Primary Goals

- Give platform staff full visibility into users, companies, requests, offers, orders, escrow, disputes and risk events.
- Provide safe manual intervention tools with mandatory audit logging.
- Support fraud prevention and scam investigation.
- Support buyer/supplier trust, KYB/KYC review and risk scoring.
- Make dispute handling structured, evidence-based and traceable.
- Support global marketplace configuration: countries, regions, languages, currencies and payment providers.
- Prepare for future payment integrations: Visa/Mastercard, Stripe, Payoneer, USDT and manual bank transfer.

### 2.2 Non-Goals for V1

- No complex microservice dashboard.
- No Kafka/RabbitMQ dependency required in admin V1.
- No real accounting ledger UI beyond escrow/payment event tracking unless backend supports it.
- No advanced AI fraud detection required in V1; only rule-based risk flags and manual review.
- No full BI warehouse required in V1.

---

## 3. Admin Roles and Permissions

The admin system must support RBAC.

### 3.1 Roles

#### Super Admin

Full access to all modules, staff management, platform settings and sensitive payment actions.

#### Operations Manager

Can manage users, companies, intents, offers, orders, disputes, notifications and categories. Cannot change payment provider credentials or create super admins.

#### Verification Officer

Can review KYC/KYB documents, approve/reject suppliers, add risk notes and request more documents.

#### Dispute Agent

Can view orders, escrow status, dispute evidence and issue recommended decisions. Final refund/release actions may require Operations Manager or Super Admin approval.

#### Finance Officer

Can view escrow transactions, payouts, refunds, chargebacks and payment provider events. Can mark manual bank/USDT payments as verified if permission is granted.

#### Risk Analyst

Can view audit logs, risk flags, suspicious activity, user/device/IP history and recommend account restrictions.

#### Support Agent

Can view users, requests, orders and messages. Can add support notes but cannot modify escrow or verification decisions.

#### Auditor Read-Only

Read-only access to audit logs, reports, transaction history and dispute history.

### 3.2 Permission Matrix

Each admin action must check permission by module and action:

```text
users.read
users.update_status
companies.read
companies.verify
companies.reject
intents.read
intents.moderate
offers.read
offers.moderate
orders.read
orders.update_status
escrow.read
escrow.release
escrow.refund
escrow.manual_verify
disputes.read
disputes.resolve
audit.read
risk.read
risk.apply_action
notifications.manage
categories.manage
settings.manage
staff.manage
```

---

## 4. Admin Console Navigation Structure

The PC admin UI must use a left sidebar with grouped modules.

```text
Overview
├── Admin Dashboard
├── Live Operations
├── Analytics Snapshot

Marketplace
├── Buyer Intents
├── Supplier Offers
├── Orders
├── Messages Monitor

Verification & Trust
├── Supplier Verification Queue
├── Buyer KYC Queue
├── Company Profiles
├── Trust Scores

Payments & Escrow
├── Escrow Transactions
├── Payment Events
├── Payouts
├── Refunds
├── Chargebacks
├── Manual Bank / USDT Verification

Disputes & Support
├── Dispute Center
├── Evidence Review
├── Support Tickets
├── Resolution Templates

Risk & Audit
├── Risk Flags
├── Fraud Review Queue
├── Audit Logs
├── Login / Device Logs
├── Admin Action Logs

Configuration
├── Categories
├── Attribute Schema Builder
├── Regions & Geo Rules
├── Currencies & FX
├── Languages & i18n
├── Notification Templates
├── Payment Providers
├── Escrow Rules
├── Dispute SLA Rules

Growth & Monetization
├── Ads & Promotions
├── Sponsored Placements
├── Supplier Analytics Add-ons

System
├── Staff Users
├── Roles & Permissions
├── Platform Settings
├── API Keys / Webhooks
├── System Health
```

---

## 5. Global Admin UI Requirements

### 5.1 Layout

- Desktop-first design.
- Left sidebar navigation.
- Top bar with search, notifications, admin profile, language selector and environment badge.
- Main content area with cards, tables, filters and action panels.
- Use responsive design but optimize for 1440px desktop width.
- Support tablet fallback, but admin is not mobile-first.

### 5.2 Visual Style

Use a modern enterprise SaaS style inspired by:

- Stripe Dashboard
- Shopify Admin
- Retool
- Linear
- Notion Enterprise Admin
- AWS Console for dense configuration screens

Recommended visual rules:

- Neutral gray background.
- White cards.
- Deep blue/indigo primary actions.
- Green for safe/verified/released.
- Amber for pending/review/warning.
- Red for risk/dispute/refund/frozen.
- Compact but readable tables.
- Clear status badges.
- Timeline components for order, escrow and dispute flows.

### 5.3 Global Search

Admin global search must support:

```text
User ID
Email
Phone
Company name
Intent ID
Offer ID
Order ID
Escrow transaction ID
Payment provider reference
Dispute ID
Audit action ID
```

### 5.4 Global Filters

Most list pages must support:

```text
Date range
Country
Region / city
Category
Status
Risk level
Verification level
Currency
Payment provider
Assigned staff
```

### 5.5 Bulk Actions

Where safe, support bulk actions:

- assign to staff
- export CSV
- add internal note
- change queue status
- send notification

High-risk actions must not be bulk-enabled unless explicitly allowed.

---

## 6. Dashboard Pages

## 6.1 Admin Dashboard

Purpose: executive snapshot of marketplace health.

Widgets:

```text
Active buyer intents
Offers submitted today
Orders in progress
Escrow held amount
Released payout amount
Refunded amount
Open disputes
High-risk alerts
Verification queue size
Average time-to-first-offer
Average supplier response time
Dispute rate
On-time delivery percentage
```

Charts:

- daily intent count
- offer volume
- order GMV
- escrow held/released/refunded
- dispute trend
- supplier verification approvals

Tables:

- latest high-risk orders
- newest disputes
- urgent verification cases
- failed payment events

Actions:

- View live operations
- Open dispute queue
- Open risk queue
- Open verification queue

---

## 6.2 Live Operations Page

Purpose: real-time marketplace activity monitoring.

Show:

- active intents by age
- offers per intent
- pings sent
- supplier response status
- orders waiting for delivery
- orders waiting for buyer confirmation
- deliveries overdue
- disputes newly opened

UI should include:

- real-time activity feed
- map heatmap by region
- status cards
- operational SLA warnings

---

## 6.3 Analytics Snapshot

Purpose: simple operational analytics without a full BI system.

Metrics:

```text
Time-to-first-offer
Offers per intent
Award rate
Order completion rate
Dispute rate
Refund rate
Supplier response SLA
Buyer repeat rate
Top categories
Top regions
Escrow volume
```

Support CSV export.

---

## 7. User and Account Management

## 7.1 User Management Page

List all users.

Columns:

```text
User ID
Name
Email
Phone
Role
Country
City
Status
Verification level
Created date
Last login
Risk level
```

Filters:

```text
Role
Status
Verification level
Country
Risk level
Date range
```

Actions:

- view profile
- suspend user
- reactivate user
- force logout
- reset 2FA
- add admin note
- view audit logs
- view related orders/disputes

High-risk actions require confirmation modal and reason.

---

## 7.2 User Detail Page

Sections:

```text
Profile summary
Contact information
Verification status
Security status
Linked companies
Buyer intents
Offers if supplier agent
Orders
Messages summary
Disputes
Payment methods, masked
Risk flags
Internal notes
Audit timeline
```

Sensitive PII must be masked by default. Admins need permission to reveal.

---

## 7.3 Account Status Actions

Supported statuses:

```text
ACTIVE
PENDING_VERIFICATION
RESTRICTED
SUSPENDED
BANNED
DELETED_REQUESTED
```

Every status change must write audit log.

Required fields:

```text
reason_code
reason_text
effective_until optional
notify_user true/false
```

---

## 8. Company and Supplier Verification

## 8.1 Supplier Verification Queue

Purpose: review KYB/KYC documents.

Columns:

```text
Company ID
Company name
Country
Business type
Submitted date
Verification status
Risk level
Assigned reviewer
Document count
```

Statuses:

```text
NOT_STARTED
SUBMITTED
IN_REVIEW
NEEDS_MORE_INFO
APPROVED_BASIC
APPROVED_BUSINESS
REJECTED
SUSPENDED
```

Actions:

- assign reviewer
- open review
- approve
- reject
- request more documents
- add risk note

---

## 8.2 Verification Review Detail

Layout:

Left side:

- company profile
- owner profile
- business address
- categories requested
- payout account summary
- risk score

Right side:

- document viewer
- checklist
- reviewer notes
- decision panel

Checklist items:

```text
Business registration document
Tax ID / company number
Owner / representative ID
Proof of address
Bank account / Payoneer account
USDT wallet, if provided
Storefront / warehouse photo, optional
Category license, if required
```

Decision options:

```text
Approve Basic
Approve Business
Request More Info
Reject
Escalate to Risk
```

Every decision must require:

```text
decision reason
internal note
optional user-facing note
```

---

## 8.3 Company Profile Admin View

Sections:

```text
Company identity
Branches
Users / agents
Categories
Catalog items
Verification history
Trust score
Orders
Disputes
Payout settings
Risk flags
Audit logs
```

Actions:

- update verification level
- restrict categories
- suspend company
- add branch restriction
- add internal note

---

## 9. Buyer Intent Management

## 9.1 Buyer Intents List

Columns:

```text
Intent ID
Buyer
Category
Title / summary
Budget min/max
Currency
Location
Radius
Status
Offers count
Created at
Expires at
Risk level
```

Statuses:

```text
DRAFT
ACTIVE
EXPIRED
CANCELED
AWARDED
UNDER_REVIEW
REMOVED
```

Filters:

```text
Status
Category
Country/region/city
Budget range
Currency
Offer count
Risk level
Created date
```

Actions:

- view intent
- moderate content
- pause intent
- cancel intent
- mark as suspicious
- view matching suppliers
- resend supplier pings

---

## 9.2 Buyer Intent Detail

Sections:

```text
Intent summary
Structured attributes
Buyer info, masked if required
Location map and radius
Budget and currency
Payment/preauth status
Attachments
Matching suppliers
Ping history
Offers received
Messages
Audit timeline
Risk flags
```

Admin actions:

- edit moderation status
- request buyer clarification
- remove attachment
- force expire intent
- escalate to risk

---

## 10. Offer Management

## 10.1 Supplier Offers List

Columns:

```text
Offer ID
Intent ID
Supplier company
Category
Unit price
Delivery fee
Total landed cost
Currency
ETA
Stock confidence
Status
Expires at
Risk flags
```

Statuses:

```text
SUBMITTED
VIEWED
WITHDRAWN
EXPIRED
AWARDED
REJECTED
REMOVED
```

Actions:

- view offer
- remove fraudulent offer
- flag price outlier
- contact supplier
- view related order

---

## 10.2 Offer Detail

Sections:

```text
Offer price breakdown
Supplier info
Trust badge
ETA and delivery plan
Warranty
Stock confidence
Attachments
Buyer intent summary
Price-band comparison
Messages
Audit timeline
Risk flags
```

Risk indicators:

- price below P10
- price above P90
- new supplier high-value offer
- repeated canceled orders
- mismatch with catalog price

---

## 11. Order Management

## 11.1 Orders List

Columns:

```text
Order ID
Buyer
Supplier
Category
Total amount
Currency
Escrow status
Order status
Delivery status
Dispute status
Created date
Risk level
```

Order statuses:

```text
CREATED
AWAITING_PAYMENT
ESCROW_FUNDED
IN_PROGRESS
READY_FOR_PICKUP
DISPATCHED
DELIVERED
ACCEPTED
COMPLETED
DISPUTED
CANCELED
REFUNDED
```

Actions:

- view order
- add internal note
- open dispute
- escalate risk
- view payment events
- view delivery proofs

---

## 11.2 Order Detail

This is one of the most important admin pages.

Sections:

```text
Order summary
Buyer and supplier cards
Intent and offer snapshots
Escrow timeline
Payment events
Delivery milestones
Proof attachments
Messages
Dispute panel, if any
Risk flags
Internal notes
Audit timeline
```

Admin actions:

```text
Mark under review
Request more evidence
Pause auto-release
Approve release, permission required
Issue refund, permission required
Partial refund, permission required
Escalate to risk
```

High-risk money actions must require:

```text
2-step confirmation
reason code
internal note
permission check
optional second approval for large amount
```

---

## 12. Payments and Escrow Management

## 12.1 Escrow Transactions Page

Purpose: view all escrow states.

Columns:

```text
Escrow ID
Order ID
Buyer
Supplier
Provider
Auth amount
Captured amount
Released amount
Refunded amount
Currency
Status
Created date
Updated date
Risk level
```

Escrow statuses:

```text
AUTH_PENDING
AUTH_HELD
AUTH_FAILED
CAPTURED
RELEASE_PENDING
RELEASED
PARTIALLY_RELEASED
REFUND_PENDING
REFUNDED
PARTIALLY_REFUNDED
CHARGEBACK
DISPUTED
MANUAL_REVIEW
```

Providers to display:

```text
Visa / Mastercard card
Stripe
Payoneer payout
USDT
Manual bank transfer
Wallet balance, future
```

---

## 12.2 Escrow Detail Page

Sections:

```text
Escrow summary
Order summary
Provider references
Authorization history
Capture history
Release history
Refund history
Chargeback history
Webhook events
Manual admin actions
Audit timeline
```

Actions:

- retry provider sync
- mark manual bank payment verified
- mark USDT transaction verified
- hold release
- release funds
- issue refund
- add finance note

Money actions must be permission protected and audited.

---

## 12.3 Payment Events Page

List raw payment provider events.

Columns:

```text
Event ID
Provider
Provider event ID
Event type
Related order
Related escrow
Amount
Currency
Status
Received at
Processed at
Error message
```

Event types:

```text
payment_intent.created
payment_authorized
payment_captured
payment_failed
refund_created
refund_succeeded
chargeback_opened
chargeback_lost
payout_created
payout_paid
manual_bank_verified
usdt_tx_detected
usdt_tx_confirmed
```

---

## 12.4 Manual Bank / USDT Verification

Purpose: support payment methods before full automation.

For manual bank transfer:

```text
Buyer upload receipt
Admin verifies bank statement reference
Admin marks as verified or rejected
Escrow status changes to AUTH_HELD or CAPTURED depending on flow
```

For USDT:

```text
Buyer submits transaction hash
Admin checks chain/network/address/amount
Admin marks transaction verified or rejected
```

UI fields:

```text
Payment method
Expected amount
Received amount
Currency/token
Network, for USDT
Wallet address
Transaction hash
Receipt image
Verification status
Reviewer
Review note
```

---

## 12.5 Payouts Page

Columns:

```text
Payout ID
Supplier
Order ID
Amount
Currency
Provider
Destination
Status
Scheduled date
Paid date
Risk hold
```

Payout statuses:

```text
PENDING
ON_HOLD
SCHEDULED
PROCESSING
PAID
FAILED
CANCELED
```

Support Payoneer placeholder, bank transfer and USDT payout placeholder.

---

## 13. Dispute Center

## 13.1 Dispute List

Columns:

```text
Dispute ID
Order ID
Buyer
Supplier
Reason
Requested resolution
Amount at risk
Status
SLA deadline
Assigned agent
Risk level
Created date
```

Statuses:

```text
OPENED
WAITING_BUYER_EVIDENCE
WAITING_SUPPLIER_EVIDENCE
UNDER_REVIEW
ESCALATED
RESOLVED_REFUND
RESOLVED_PARTIAL_REFUND
RESOLVED_RELEASE
CLOSED
```

Filters:

```text
Status
Reason
SLA breached
Assigned agent
Risk level
Category
Region
Amount range
```

---

## 13.2 Dispute Detail

This page must be designed very carefully.

Layout:

### Left Column: Case Summary

```text
Dispute ID
Order ID
Buyer
Supplier
Amount at risk
Escrow status
Order status
Reason
Requested resolution
SLA timer
Assigned agent
```

### Center: Evidence Timeline

Timeline includes:

```text
Order created
Escrow funded
Supplier dispatched
Delivery proof uploaded
Buyer opened dispute
Buyer evidence submitted
Supplier response submitted
Admin notes
Decision made
Refund/release executed
```

Each timeline item can have:

```text
text note
photo/video/file attachment
actor
timestamp
visibility: internal/public
```

### Right Column: Decision Panel

Decision options:

```text
Request more evidence from buyer
Request more evidence from supplier
Full refund to buyer
Partial refund
Release funds to supplier
Replacement required
Escalate to senior review
Close as invalid
```

Every decision must require:

```text
reason code
decision note
public message
internal note
refund amount, if applicable
release amount, if applicable
```

High-value disputes require second approval.

---

## 13.3 Dispute Resolution Templates

Admin can manage templates for common outcomes:

```text
Item not received
Wrong item
Damaged goods
Quantity mismatch
Late delivery
Counterfeit suspicion
Buyer no response
Supplier no response
```

Each template includes:

- public message
- required evidence checklist
- recommended resolution
- SLA

---

## 14. Risk and Fraud Management

## 14.1 Risk Flags Page

Columns:

```text
Risk ID
Entity type
Entity ID
Risk type
Risk level
Status
Assigned analyst
Created at
Last updated
```

Risk levels:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Risk statuses:

```text
OPEN
IN_REVIEW
MITIGATED
FALSE_POSITIVE
ACTION_TAKEN
CLOSED
```

Risk types:

```text
SUSPICIOUS_PRICE_LOW
SUSPICIOUS_PRICE_HIGH
NEW_SUPPLIER_HIGH_VALUE_ORDER
HIGH_DISPUTE_RATE
REPEATED_CANCELLATION
FAILED_LOGIN_SPIKE
DEVICE_MULTI_ACCOUNT
POSSIBLE_COUNTERFEIT
PAYMENT_MISMATCH
USDT_UNCONFIRMED
MANUAL_BANK_RECEIPT_SUSPICIOUS
OFF_PLATFORM_DEAL_ATTEMPT
```

---

## 14.2 Fraud Review Detail

Sections:

```text
Risk summary
Related user/company/order/intent
Timeline
Device/IP history
Payment history
Dispute history
Message excerpts, if permission allows
Evidence attachments
Recommended action
Analyst notes
Audit logs
```

Actions:

```text
Mark false positive
Add warning
Restrict user
Suspend company
Hold payout
Require re-verification
Escalate to senior review
```

---

## 14.3 Login and Device Logs

Track:

```text
user_id
login time
IP address
country/city approximation
device/browser
success/failure
2FA status
risk score
```

Admins can filter by user, IP, country, failed attempts and date.

---

## 15. Audit Log System

Audit log is mandatory and must be immutable from the admin UI.

## 15.1 Audit Logs Page

Columns:

```text
Audit ID
Timestamp
Actor
Actor role
Action
Entity type
Entity ID
Risk level
IP address
User agent
```

Filters:

```text
Actor
Role
Action
Entity type
Entity ID
Date range
Risk level
IP address
```

## 15.2 Audit Detail

Show:

```text
Actor details
Action details
Entity link
Before JSON
After JSON
Request metadata
IP address
User agent
Correlation ID
Reason code
Admin note
```

Important audited actions:

```text
user.login_failed
user.status_changed
company.verification_approved
company.verification_rejected
intent.created
intent.moderated
offer.submitted
offer.removed
order.created
order.status_changed
escrow.auth_held
escrow.captured
escrow.release_requested
escrow.released
escrow.refund_requested
escrow.refunded
payment.manual_verified
dispute.opened
dispute.evidence_added
dispute.resolved
risk.flag_created
risk.action_taken
admin.role_changed
settings.updated
```

---

## 16. Messaging and Support Monitoring

## 16.1 Messages Monitor

Admin can inspect messages only with proper permission and for support/risk reasons.

List filters:

```text
Intent ID
Order ID
User
Company
Date range
Flagged only
Contains attachment
```

Actions:

- view thread
- flag off-platform transaction attempt
- hide abusive message
- add support note

---

## 16.2 Support Tickets

Support ticket statuses:

```text
OPEN
PENDING_USER
PENDING_INTERNAL
RESOLVED
CLOSED
```

Ticket categories:

```text
Account
Verification
Payment
Order
Delivery
Dispute
Technical issue
Fraud report
```

---

## 17. Category and Attribute Schema Management

## 17.1 Category Management

Fields:

```text
Category name
Slug
Parent category
Icon
Status
Supported countries
Requires verification level
Risk level
```

Actions:

- create category
- edit category
- enable/disable category
- reorder category

---

## 17.2 Attribute Schema Builder

This is used for dynamic buyer request forms and supplier catalog specs.

Field types:

```text
text
number
select
multi_select
boolean
date
unit_value
range
file
image
```

Each attribute supports:

```text
field key
label
help text
required true/false
validation rules
unit options
allowed values
default value
visible to buyer true/false
visible to supplier true/false
searchable true/false
match weight
```

Example Construction Cement schema:

```json
{
  "brand": "Holcim",
  "type": "Portland",
  "bag_weight_kg": 40,
  "freshness_required": true
}
```

---

## 18. Region, Location and Radius Management

Admin must manage global regions for location-based matching.

Pages:

```text
Countries
Cities
Districts / Areas
Service zones
Radius rules
Delivery fee presets
```

Required examples:

```text
Philippines
Cebu
Mandaue
Lapu-Lapu
Cebu City
```

Features:

- map view
- polygon or radius zones
- default currency per region
- timezone
- supported payment methods
- supported languages
- delivery fee rules

---

## 19. Currency, FX and Internationalization

## 19.1 Currency Settings

Support:

```text
PHP
USD
EUR
CNY
JPY
KRW
GBP
AUD
SGD
USDT
```

Fields:

```text
currency code
symbol
decimal precision
active true/false
payment enabled true/false
payout enabled true/false
```

## 19.2 Language Settings

Default language: English.

Supported language placeholders:

```text
English
Simplified Chinese
Spanish
French
German
Japanese
Korean
Portuguese
Arabic
Filipino / Tagalog
```

Admin can manage translation keys or export/import JSON translation files.

---

## 20. Notification Management

## 20.1 Notification Templates

Channels:

```text
Email
Telegram Bot
In-app notification
WebSocket real-time event
SMS, future
Mobile push, future
```

Templates:

```text
New supplier ping
Offer submitted
Offer expiring
Offer awarded
Payment authorized
Escrow captured
Supplier dispatched
Delivery confirmed
Funds released
Dispute opened
Evidence requested
Dispute resolved
Verification approved
Verification rejected
Risk action taken
```

Each template supports:

```text
language
subject/title
body
variables
preview
send test
active true/false
```

Variables example:

```text
{{buyer_name}}
{{supplier_name}}
{{intent_id}}
{{order_id}}
{{amount}}
{{currency}}
{{category}}
{{location}}
{{deadline}}
```

---

## 20.2 Telegram Integration Settings

Admin can configure:

```text
Telegram bot token, masked
Webhook URL
Default notification rules
Supplier opt-in status
Test message sending
Error logs
```

Do not show full bot token after saving.

---

## 20.3 Email Integration Settings

Admin can configure:

```text
SMTP or provider API key, masked
From name
From email
Reply-to email
Template branding
Test email
Delivery logs
```

---

## 21. Ads and Promotions Management

The platform may have zero commission and monetize via ads/promotions.

Admin pages:

```text
Sponsored supplier profiles
Sponsored categories
Promoted offers
Inbox announcements
Ad placements
Campaign reports
```

Important rule:

Sponsored content must be clearly labeled and must not silently manipulate organic ranking.

Fields:

```text
campaign name
supplier/company
placement
country/region
category
date range
budget
status
creative assets
label text: Sponsored
```

---

## 22. Platform Settings

Settings page includes:

```text
Platform name placeholder {{APP_NAME}}
Domain placeholder {{APP_DOMAIN}}
Default language
Default country
Default currency
Supported regions
Escrow rules
Dispute SLA
Supplier response SLA
Payment providers
Notification providers
Risk thresholds
Maintenance mode
Terms links
Privacy links
```

Do not hardcode sanaoll.com into UI. Use environment configuration.

---

## 23. Payment Provider Settings

Payment providers to reserve:

```text
Visa / Mastercard card payment
Stripe
Payoneer payout
USDT payment
Manual bank transfer
Wallet balance, future
```

Provider config fields:

```text
provider name
mode: test/live
active true/false
supported countries
supported currencies
fee display mode
API key masked
webhook secret masked
callback URL
last webhook status
```

---

## 24. Staff Users and Roles

## 24.1 Staff Users Page

Columns:

```text
Staff ID
Name
Email
Role
Status
Last login
2FA enabled
Created date
```

Actions:

- invite staff
- disable staff
- reset 2FA
- change role
- view admin action logs

## 24.2 Roles & Permissions Page

Admin can view permission matrix.

V1 can be simple:

- predefined roles
- editable permissions only by Super Admin
- every change audited

---

## 25. API and Backend Requirements

Backend should be FastAPI monolith.

Recommended modules:

```text
app/auth
app/users
app/companies
app/verification
app/categories
app/intents
app/offers
app/orders
app/escrow
app/payments
app/disputes
app/risk
app/audit
app/notifications
app/admin
app/settings
```

Recommended infrastructure for V1:

```text
FastAPI
PostgreSQL
SQLAlchemy or SQLModel
Alembic migrations
Redis optional only if already available
S3/MinIO for documents and proof uploads
SMTP or email provider
Telegram Bot API
```

Avoid unnecessary middleware in V1:

- no Kafka required
- no RabbitMQ required
- no Elasticsearch required unless later needed
- use PostgreSQL full-text and JSONB first

---

## 26. Admin API Surface

Suggested endpoints:

```text
GET /admin/dashboard
GET /admin/live-ops
GET /admin/users
GET /admin/users/{id}
POST /admin/users/{id}/status

GET /admin/companies
GET /admin/companies/{id}
GET /admin/verification/queue
POST /admin/verification/{company_id}/approve
POST /admin/verification/{company_id}/reject
POST /admin/verification/{company_id}/request-more-info

GET /admin/intents
GET /admin/intents/{id}
POST /admin/intents/{id}/moderate

GET /admin/offers
GET /admin/offers/{id}
POST /admin/offers/{id}/remove

GET /admin/orders
GET /admin/orders/{id}
POST /admin/orders/{id}/hold

GET /admin/escrow
GET /admin/escrow/{id}
POST /admin/escrow/{id}/release
POST /admin/escrow/{id}/refund
POST /admin/escrow/{id}/manual-verify

GET /admin/payment-events
GET /admin/payouts

GET /admin/disputes
GET /admin/disputes/{id}
POST /admin/disputes/{id}/request-evidence
POST /admin/disputes/{id}/resolve

GET /admin/risk-flags
GET /admin/risk-flags/{id}
POST /admin/risk-flags/{id}/action

GET /admin/audit-logs
GET /admin/audit-logs/{id}

GET /admin/categories
POST /admin/categories
PUT /admin/categories/{id}

GET /admin/schemas
POST /admin/schemas
PUT /admin/schemas/{id}

GET /admin/notification-templates
PUT /admin/notification-templates/{id}
POST /admin/notifications/test

GET /admin/settings
PUT /admin/settings

GET /admin/staff
POST /admin/staff/invite
PUT /admin/staff/{id}/role
```

---

## 27. Database Tables Required for Admin V1

Core tables:

```text
users
companies
company_documents
company_verification_reviews
branches
categories
attribute_schemas
catalog_items
buyer_intents
intent_attachments
supplier_alert_rules
offers
orders
escrow_transactions
payment_events
payouts
deliveries
delivery_proofs
messages
disputes
dispute_evidence
reviews
notifications
notification_templates
risk_flags
audit_logs
admin_notes
staff_users
roles
role_permissions
platform_settings
regions
currencies
languages
ads_campaigns
```

---

## 28. Audit Log Data Model

Audit log table should contain:

```text
id
actor_id
actor_type: user/admin/system
actor_role
action
entity_type
entity_id
before_json
after_json
reason_code
reason_text
ip_address
user_agent
correlation_id
risk_level
created_at
```

Audit logs should not be editable from UI.

---

## 29. Admin Notes Data Model

Internal admin notes can be attached to:

```text
User
Company
Intent
Offer
Order
Escrow
Dispute
Risk Flag
```

Fields:

```text
id
entity_type
entity_id
author_admin_id
visibility: internal_only / risk_team / finance_team
note
created_at
updated_at
```

---

## 30. Security Requirements

- JWT authentication with refresh tokens.
- Admin accounts require 2FA.
- Permission check for every admin API.
- Sensitive payment actions require step-up confirmation.
- Staff action logging is mandatory.
- PII is masked by default.
- File download uses signed URLs.
- Rate-limit login and sensitive actions.
- Block inactive/suspended admin accounts.
- Optional IP allowlist for Super Admin.

---

## 31. Compliance and Privacy

Admin must support:

```text
PII masking
Data export request tracking
Delete/deactivate request tracking
Consent logs, future
KYC/KYB document retention policy
Audit log retention policy
```

GDPR/PDPA ready design.

---

## 32. Empty States and Error States

Every admin page must have:

- empty state
- loading state
- API error state
- permission denied state
- high-risk confirmation modal
- success toast
- failure toast

Examples:

```text
No disputes found.
No verification cases assigned to you.
You do not have permission to release funds.
This action requires Super Admin approval.
Payment provider sync failed. Please retry or contact finance.
```

---

## 33. Enterprise UX Details

Required components:

```text
Status badge
Risk badge
Trust badge
Escrow status badge
Timeline
Evidence gallery
Document viewer
JSON diff viewer
Audit detail drawer
Admin note drawer
Advanced filter panel
CSV export button
Permission-aware action menu
Confirmation modal
```

Table features:

```text
column sorting
column visibility
sticky header
pagination
saved filters
CSV export
row detail drawer
```

---

## 34. Stitch / UI Design Prompt for Admin PC

Use this prompt for UI generation:

```text
Design a desktop-first enterprise admin console for {{APP_NAME}}, a reverse e-commerce marketplace where buyers post purchase requests, verified suppliers submit offers, buyers pay into escrow, suppliers fulfill orders, and funds are released only after delivery confirmation.

The admin console is used by platform operations, verification officers, finance officers, dispute agents, risk analysts, support agents, auditors, and super admins.

Create a modern enterprise SaaS UI similar to Stripe Dashboard, Shopify Admin, Retool, Linear, and AWS Console. Use a left sidebar, top search bar, dense data tables, filters, status badges, risk badges, timelines, evidence viewers, audit log panels, and permission-aware action menus.

The admin console must include these modules:
1. Dashboard and live operations
2. User management
3. Supplier company verification and KYB document review
4. Buyer intent management
5. Supplier offer management
6. Order management
7. Escrow and payment transactions
8. Manual bank and USDT payment verification
9. Payoneer payout placeholder
10. Dispute center with evidence timeline and decision panel
11. Risk flags and fraud review queue
12. Audit logs with before/after JSON diff
13. Login and device logs
14. Category management
15. Attribute schema builder
16. Region and map/radius rules
17. Currency and language settings
18. Notification templates for Email, Telegram, in-app and future push
19. Ads and promotions management
20. Staff users, roles and permissions
21. Platform settings and payment provider settings

The UI must support default English and be prepared for 10 languages: English, Simplified Chinese, Spanish, French, German, Japanese, Korean, Portuguese, Arabic, and Filipino/Tagalog.

The UI must support currencies: PHP, USD, EUR, CNY, JPY, KRW, GBP, AUD, SGD, and USDT.

Payment provider placeholders must include Visa/Mastercard card payment, Stripe, Payoneer payouts, USDT, manual bank transfer, and future wallet balance.

Design the admin interface as a serious financial and operational control center, not a simple e-commerce dashboard. Emphasize trust, auditability, fraud prevention, escrow safety, dispute resolution, and global marketplace operations.
```

---

## 35. MVP Priority

### Must-have Admin V1

```text
Admin login + RBAC
Dashboard
User management
Company verification queue
Buyer intent management
Offer management
Order management
Escrow transaction viewer
Manual payment verification
Dispute center
Risk flags
Audit logs
Category management
Attribute schema builder
Notification templates
Platform settings
Staff users
```

### Should-have V1.1

```text
Pricing intelligence
Ads management
Advanced analytics
Login/device logs
CSV saved filters
Region polygon management
Translation key management
```

### Later Phase

```text
ML fraud scoring
Advanced BI dashboard
Automated payout reconciliation
Multi-approval workflow engine
Full accounting ledger
External CRM/helpdesk integration
```

---

## 36. Acceptance Criteria

Admin V1 is accepted when:

- Staff can log in and access pages based on role.
- Super Admin can invite staff and assign roles.
- Ops can view users, companies, intents, offers and orders.
- Verification Officer can approve/reject supplier KYB cases.
- Finance can view escrow/payment events and verify manual bank/USDT payments.
- Dispute Agent can review evidence and resolve disputes with audited decisions.
- Risk Analyst can view and act on risk flags.
- Audit Logs capture every sensitive action.
- Admin can configure categories and attribute schemas.
- Admin can configure notification templates for Email and Telegram.
- Payment provider placeholders exist for Visa/Mastercard, Stripe, Payoneer and USDT.
- Platform settings use placeholders `{{APP_NAME}}` and `{{APP_DOMAIN}}` instead of hardcoded branding.
- All high-risk actions require confirmation and reason notes.
- UI is desktop-first, enterprise-grade, responsive enough for tablet, and not designed as a consumer mobile interface.