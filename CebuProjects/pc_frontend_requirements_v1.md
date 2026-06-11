# PC Frontend Requirements v1 — Reverse Marketplace / ProcurePing-style Platform

> Working brand placeholder: `{{APP_NAME}}`  
> Working domain placeholder: `{{APP_DOMAIN}}`  
> Do not hardcode `sanaoll.com` in UI text, routes, or configuration. Use environment/config variables.

---

## 1. Product Positioning

This is not a traditional e-commerce storefront.

The platform is a **buyer-request reverse marketplace**:

1. Buyers post what they want to buy.
2. The system matches the request to verified suppliers.
3. Suppliers receive pings and submit offers.
4. Buyers compare offers by total landed cost, delivery time, trust, and warranty.
5. Buyer pays into escrow.
6. Supplier fulfills the order.
7. Buyer confirms receipt.
8. Platform releases payout to supplier.
9. Disputes, refunds, audit logs, and fraud controls are handled by the platform.

The PC frontend must look and feel like an enterprise-grade marketplace system, not a simple demo or old-style classified listing website.

---

## 2. Target Platforms

PC frontend must support:

- Desktop web browser
- Large laptop screens
- Tablet landscape layout
- Responsive fallback for smaller screens
- Future shared components with mobile H5
- Future PWA support
- Future Capacitor wrapper compatibility for mobile app packaging

Admin and Supplier experiences are PC-first. Buyer experience should also work well on PC but may be simpler than the mobile/H5 buyer journey.

---

## 3. Recommended Frontend Stack

Recommended stack:

```text
Vue 3 / Nuxt 3
TypeScript
Tailwind CSS
Naive UI / Nuxt UI / shadcn-vue style components
Pinia
Vue I18n
Axios or Fetch API client
Map SDK abstraction layer
PWA-ready configuration
```

Alternative stack if the team prefers React:

```text
Next.js
TypeScript
Tailwind CSS
shadcn/ui
Zustand / Redux Toolkit
next-intl
PWA-ready configuration
```

For this requirement document, assume a Vue 3 / Nuxt 3 implementation unless otherwise specified.

---

## 4. Global UI Style

The UI should follow a modern enterprise SaaS marketplace style.

Reference style direction:

- Stripe Dashboard
- Shopify Admin
- Lazada Seller Center
- Shopee Seller Center
- Upwork proposal comparison
- Alibaba RFQ
- Facebook Ads location targeting
- Airbnb search filters

Visual guidelines:

```text
Primary color: deep blue / indigo
Success color: green for escrow-safe, verified, delivered, released
Warning color: amber for expiring, pending, review needed
Danger color: red for disputes, failed payment, fraud, rejected
Neutral: slate / gray
Background: light gray dashboard background
Cards: rounded, clean, subtle shadow
Tables: enterprise-grade, filterable, sortable
Forms: step-by-step, structured, validation-friendly
```

Avoid old demo UI, heavy orange/green, cluttered forms, and outdated table styles.

---

## 5. Global Layout Requirements

### 5.1 Public Website Layout

Public pages use:

- Top navigation
- Hero section
- CTA buttons
- Category previews
- Trust/safety sections
- Footer with language, currency, region, legal, and help links

### 5.2 Buyer/Supplier App Layout

Buyer and Supplier logged-in PC pages use:

- Left sidebar navigation
- Top header with search, notifications, language, currency, region, profile menu
- Main content area
- Right-side contextual panel where useful
- Breadcrumbs for detail pages
- Sticky action bar for critical actions such as publish request, award offer, submit offer, confirm delivery

### 5.3 Admin Console Layout

Admin uses:

- Dense sidebar navigation
- Global search
- Environment/status indicator
- Staff role indicator
- Audit-aware action modals
- Tables with advanced filters
- Data summary cards
- Timeline panels

---

## 6. Global Features

### 6.1 Internationalization

Default language: English.

Must support language switcher and i18n-ready UI for:

```text
English
en-US
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

Requirements:

- All text must use translation keys.
- No hardcoded UI copy inside components.
- Support RTL-ready layout for Arabic where possible.
- Date/time formatting must follow selected locale.
- Numbers and currencies must use locale-aware formatting.

### 6.2 Currency Support

Currency switcher must be available globally.

Supported currencies:

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

Monetary UI should show:

- Unit price
- Quantity
- Delivery fee
- Service/payment fee placeholder
- Total landed cost
- Escrow held amount
- Captured amount
- Released amount
- Refunded amount

### 6.3 Region and Location Support

The frontend must support global region switching and map-based local targeting.

Examples:

```text
Philippines → Cebu → Mandaue
Philippines → Cebu → Lapu-Lapu
Philippines → Metro Manila → Makati
United States → Georgia → Gainesville
```

Location UI must support:

- Country selector
- City selector
- Area/district selector
- Search address input
- Use current location button
- Map pin selector
- Radius selector: 1km, 3km, 5km, 10km, 25km, 50km, custom
- Radius circle overlay on map
- Estimated supplier count in selected radius
- Saved locations

The location targeting UX should be similar to Facebook Ads radius targeting.

### 6.4 Notification Channels

Frontend must expose notification preferences for:

```text
Email
Telegram Bot
In-app notification
WebSocket/live notification
SMS placeholder
Push notification placeholder
```

Telegram UI requirements:

- Connect Telegram bot
- Show bot username or connection status
- Copy pairing code
- Test notification button
- Select notification categories
- Quiet hours

Email UI requirements:

- Verify email
- Select email notification types
- Test email button

### 6.5 Payment and Escrow UI

Payment integration may be implemented later, but frontend must already show payment and escrow states.

Supported payment placeholders:

```text
Visa / Mastercard card payment
Stripe checkout
Payoneer supplier payout
USDT payment
Manual bank transfer
Wallet balance, future
```

Escrow states:

```text
AUTH_PENDING
AUTH_HELD
CAPTURED
RELEASED
REFUNDED
CHARGEBACK
DISPUTED
```

The UI must clearly explain:

- Buyer pays into escrow.
- Supplier does not receive funds until delivery is confirmed.
- Disputed orders freeze automatic payout.
- Refund and partial refund are handled by platform/admin decision.

---

## 7. Homepage Definition

The homepage must not be a traditional e-commerce product waterfall as the primary experience.

The product is a buyer-request marketplace, so the homepage must prioritize:

```text
Post Request
Describe what you need
Upload photo to identify item
Choose category
Set budget
Set location radius
Receive supplier offers
Escrow-protected checkout
```

### PC Homepage Structure

1. Top navigation
   - Logo placeholder `{{APP_NAME}}`
   - How it works
   - Categories
   - For Suppliers
   - Trust & Safety
   - Login
   - Post Request CTA

2. Hero section
   - Headline: “Post what you need. Verified suppliers compete with offers.”
   - Subtitle explaining request → offers → escrow → delivery → release payout.
   - CTA buttons: Post a Request, Become a Supplier.

3. Quick request panel
   - What are you looking for?
   - Category dropdown
   - Budget range
   - Location selector
   - Radius selector
   - Post Request button

4. Popular categories
   - Construction
   - Marine
   - Auto
   - IT / Office
   - Electronics
   - Home
   - Services
   - Custom Requests

5. Active request preview cards
   - These are not product cards.
   - They represent buyer intents, e.g. “500 bags Holcim cement needed in Mandaue, 10km radius, PHP 240k–260k budget.”

6. How it works
   - Buyer posts request
   - Suppliers submit offers
   - Buyer compares offers
   - Escrow checkout
   - Delivery and confirmation
   - Payout released

7. Trust and safety section
   - Verified suppliers
   - Escrow protection
   - Dispute center
   - Audit logs
   - Secure messaging

8. Regional map preview
   - Example: Cebu / Mandaue / Lapu-Lapu
   - Show radius targeting UI preview

9. Supplier CTA
   - “Receive real buyer pings. Submit offers. Get paid after confirmed delivery.”

10. Footer
   - Language switcher
   - Currency switcher
   - Region switcher
   - Terms
   - Privacy
   - Help Center

Traditional product browsing can be displayed as a small Phase 2 entry point only, not as the primary homepage experience.

---

## 8. Public Website Pages

### 8.1 Landing Page

Purpose: explain the platform and drive buyers to post a request.

Key sections:

- Hero
- Quick request panel
- How it works
- Popular categories
- Active requests preview
- Escrow protection
- Supplier CTA
- Trust & Safety
- Footer

### 8.2 How It Works

Separate explanation for:

- Buyers
- Suppliers
- Escrow protection
- Dispute resolution
- No commission / transparent fees / ads-supported model

### 8.3 Supplier Onboarding Page

Key sections:

- Why join
- Receive buyer pings
- Submit offers
- Manage orders
- Upload proof of delivery
- Get payout after buyer confirmation
- KYB verification
- CTA to register supplier account

### 8.4 Categories Page

Show category cards and supported attributes.

Starter categories:

```text
Construction
Marine
Auto
IT / Office
Electronics
Home
Fashion
Services
Custom Requests
```

### 8.5 Trust & Safety Page

Explain:

- Escrow
- Verified suppliers
- KYC/KYB
- Buyer privacy before award
- Dispute handling
- Audit logs
- Risk flags
- Secure messaging

### 8.6 Pricing / Fees Page

Explain:

- No commission if business model requires it
- Payment provider fees pass-through placeholder
- Sponsored placements clearly labeled
- Optional supplier add-ons placeholder

### 8.7 Help Center / FAQ

Include buyer, supplier, payment, escrow, dispute, verification, and Telegram notification FAQs.

---

## 9. Authentication and Onboarding Pages

### 9.1 Login

Features:

- Email login
- Phone login placeholder
- Password
- Remember me
- Forgot password
- Language/currency selector

### 9.2 Register Role Selection

Role cards:

- I am a Buyer
- I am a Supplier
- Platform Staff, invite only

### 9.3 Buyer Registration

Fields:

- Name
- Email
- Phone
- Password
- Country
- City
- Preferred currency
- Terms acceptance

### 9.4 Supplier Registration

Fields:

- Company name
- Contact person
- Email
- Phone
- Country
- City
- Business type
- Primary categories
- Terms acceptance

### 9.5 Email / Phone Verification

- OTP input
- Resend code
- Change email/phone

### 9.6 Forgot Password

- Email/phone input
- Reset link/code

### 9.7 KYC / KYB Start

Show required documents and progress.

### 9.8 Supplier KYB Upload

Documents:

- Business registration document
- Tax ID
- Owner ID
- Store/warehouse photos
- Bank account or Payoneer placeholder
- USDT wallet placeholder, optional

### 9.9 Verification Status

Statuses:

- Not started
- Pending review
- Approved
- Rejected
- Need more documents

---

## 10. Buyer Portal Pages

### 10.1 Buyer Dashboard

Widgets:

- Active requests
- Offers received
- Orders in progress
- Escrow held
- Disputes
- Recent messages
- Ideal list alerts
- Recommended categories

### 10.2 Post Request — Category Selection

Features:

- Search category
- Popular categories
- Recently used categories
- Custom request

### 10.3 Post Request — Structured Item Details

Fields:

- Title
- Category
- Brand
- Model
- Condition
- Quantity
- Unit
- Budget min
- Budget max
- Currency
- Photos / attachments
- Notes
- Accept alternatives toggle

Dynamic attributes should render based on category schema.

### 10.4 Post Request — Natural Language Input

User can type a freeform request.

Example:

```text
I need 500 bags of Holcim Portland cement delivered to Mandaue this weekend.
```

UI should show parsed fields for user confirmation.

### 10.5 Post Request — Image Upload Search

Features:

- Upload image
- Drag and drop
- Suggested categories
- Suggested attributes
- User confirmation

### 10.6 Post Request — Location and Radius

Features:

- Map view
- Location search
- Current location
- Pin selector
- Radius slider
- City/area selector
- Delivery address
- Supplier coverage estimate

### 10.7 Post Request — Payment / Escrow Setup

Features:

- Budget summary
- Deposit or full authorization option
- Visa/Mastercard card placeholder
- Stripe placeholder
- USDT placeholder
- Manual bank transfer placeholder
- Escrow explanation

### 10.8 Request Review and Publish

Show final summary:

- Request details
- Budget
- Location radius
- Delivery window
- Payment authorization status
- Supplier visibility
- Publish button

### 10.9 Buyer Request Detail

Show:

- Request status
- Offer countdown
- Number of suppliers pinged
- Offers received
- Request timeline
- Messages
- Edit/cancel request

### 10.10 Live Offers Matrix

This is a critical page.

Table columns:

- Supplier
- Trust badge
- Unit price
- Quantity available
- Delivery fee
- Total landed cost
- ETA
- Warranty
- Stock confidence
- Distance
- Rating
- Offer expiry
- Actions

Default sort:

1. Total landed cost
2. ETA
3. Supplier trust

### 10.11 Offer Detail

Show:

- Supplier profile
- Offer price breakdown
- Delivery plan
- Warranty
- Notes
- Photos
- Terms
- Chat supplier
- Award offer

### 10.12 Buyer Orders List

Statuses:

```text
Awaiting payment
Escrow funded
Preparing
Dispatched
Delivered
Accepted
Disputed
Completed
Refunded
```

### 10.13 Buyer Order Detail

Show:

- Order timeline
- Escrow timeline
- Supplier info
- Delivery proofs
- Messages
- Accept delivery button
- Open dispute button

### 10.14 Confirm Delivery

Checklist:

- Received correct item
- Quantity correct
- Item condition acceptable
- Upload optional photos
- Release funds button

### 10.15 Open Dispute

Fields:

- Reason
- Description
- Evidence upload
- Requested resolution
- Full refund / partial refund / replacement

### 10.16 Dispute Detail

Show:

- Dispute status
- Timeline
- Buyer evidence
- Supplier response
- Admin decision
- Refund/release status

### 10.17 Ideal List / Watchlist

Features:

- Saved requests
- Target price
- Target location
- Radius
- Notify when matched
- Auto repost placeholder

### 10.18 Buyer Messages

- Thread list
- Related request/order
- Unread count

### 10.19 Buyer Message Thread

- Chat
- Attachments
- Offer/order context panel
- System messages

### 10.20 Buyer Profile and Settings

Settings:

- Profile
- Addresses
- Language
- Currency
- Region
- Notification preferences
- Payment methods
- Security

---

## 11. Supplier Portal Pages

### 11.1 Supplier Dashboard

Widgets:

- New pings
- Active offers
- Awarded orders
- Pending deliveries
- Payout status
- Response SLA
- Rating
- Dispute rate

### 11.2 Ping Inbox

List buyer requests matched to supplier.

Columns/cards:

- Category
- Request summary
- Budget
- Quantity
- Distance
- Delivery window
- Time left
- Pre-funded badge
- Match score
- Make Offer button

### 11.3 Buyer Intent Detail for Supplier

Show:

- Buyer privacy masked before award
- Specs
- Budget range
- Location radius
- Delivery window
- Attachments
- Price band if available
- Make offer button

### 11.4 Make Offer

Fields:

- Unit price
- Quantity available
- Delivery fee
- ETA
- Warranty
- Stock confidence
- Offer expiry
- Good / Better / Best tier
- Notes
- Total landed cost preview

### 11.5 Supplier Offers List

Statuses:

```text
Submitted
Viewed
Awarded
Rejected
Expired
Withdrawn
```

### 11.6 Supplier Offer Detail

Show:

- Offer content
- Request context
- Buyer interaction status
- Edit/withdraw if allowed
- Expiry timer

### 11.7 Supplier Orders List

Columns:

- Order ID
- Buyer/request summary
- Amount
- Escrow status
- Delivery deadline
- Order status
- Actions

### 11.8 Supplier Order Detail

Show:

- Order info
- Escrow captured badge
- Buyer delivery location after award
- Delivery deadline
- Timeline
- Upload proof
- Message buyer
- Request payout placeholder

### 11.9 Delivery Proof Upload

Fields:

- Photos
- Tracking number
- Delivery note
- GPS location optional
- Mark as dispatched
- Mark as delivered

### 11.10 Supplier Catalog List

Columns:

- Item name
- Category
- Price
- Stock
- Branch
- Status
- Tags
- Match count

### 11.11 Add/Edit Catalog Item

Fields:

- Images
- Title
- Category
- Attributes
- Brand
- Model
- UPC
- MPN
- Price
- Stock
- Branch
- Tags
- Status

### 11.12 Bulk Catalog Import

Features:

- Upload CSV
- Mapping preview
- Validation errors
- Import result

### 11.13 Branch Management

Fields:

- Branch name
- Address
- Map pin
- Service radius
- Delivery methods
- Business hours

### 11.14 Alert Rules / Matching Triggers

Fields:

- Watch category
- Watch brand
- Watch model
- Budget range
- Quantity range
- Location radius
- Notify via email
- Notify via Telegram
- Auto-offer placeholder

### 11.15 Payout Settings

Fields:

- Bank account
- Payoneer placeholder
- USDT wallet placeholder
- Payout currency
- Verification status

### 11.16 Reviews and Trust Score

Show:

- Rating
- On-time delivery
- Dispute rate
- Response speed
- Verification badges

### 11.17 Team Members and Roles

Roles:

- Supplier Admin
- Supplier Agent
- Finance
- Warehouse

Features:

- Invite user
- Remove user
- Role permissions

### 11.18 Supplier Settings

Sections:

- Company profile
- KYB documents
- Notification channels
- Telegram bot connection
- Email settings
- Security

---

## 12. Admin Operations Console Pages

### 12.1 Admin Dashboard

Widgets:

- GMV
- Active intents
- Offers submitted
- Orders in progress
- Escrow held
- Released amount
- Refunded amount
- Disputes
- Verification queue
- Risk alerts

### 12.2 User Management

Features:

- Search/filter users
- View buyer/supplier/admin users
- Status management
- Role management
- Risk indicators

### 12.3 Company Verification Queue

Show:

- Company docs
- Tax ID
- Owner ID
- Bank / Payoneer info
- KYB checklist
- Approve / reject
- Risk notes

### 12.4 Buyer Intent Management

Columns:

- Intent ID
- Buyer
- Category
- Budget
- Location
- Status
- Offers count
- Risk flags

### 12.5 Offer Management

Columns:

- Offer ID
- Supplier
- Intent
- Price
- ETA
- Status
- Risk flags

### 12.6 Order Management

Columns:

- Order ID
- Buyer
- Supplier
- Amount
- Escrow status
- Order status
- Dispute status

### 12.7 Escrow / Payment Transactions

Show:

- Authorization
- Captured
- Released
- Refunded
- Chargeback
- Disputed
- Provider: Visa card / Stripe / Payoneer / USDT / manual bank transfer

### 12.8 Dispute Center

Must show:

- Case list
- Evidence timeline
- Buyer claim
- Supplier response
- Order timeline
- Escrow status
- Decision panel

Admin decisions:

- Full refund
- Partial refund
- Release to supplier
- Request more evidence
- Escalate

### 12.9 Audit Logs

Columns:

- Actor
- Actor role
- Action
- Entity type
- Entity ID
- Before/after change
- IP address
- Device/user agent
- Timestamp
- Risk level

### 12.10 Risk Flags

Risk types:

- Suspicious price
- New supplier high-value order
- Too many disputes
- Possible counterfeit
- Multiple failed logins
- Repeated cancellation
- Unusual payout change

### 12.11 Category Management

Features:

- Create category
- Edit category
- Parent/child category
- Status
- Icon

### 12.12 Attribute Schema Builder

Fields:

- Field name
- Type
- Required
- Unit
- Allowed values
- Validation rule
- Help text

### 12.13 Pricing Intelligence

Show:

- P10
- P50
- P90
- Region
- Category
- SKU attributes
- Outlier offers

### 12.14 Notification Templates

Templates for:

- Supplier ping
- Expiring offer reminder
- Award notice
- Delivery acceptance
- Dispute opened
- Verification approved/rejected

Channels:

- Email
- Telegram
- In-app
- Push placeholder

### 12.15 Ads and Promotions Management

Future monetization placeholders:

- Sponsored supplier profile
- Promoted category
- Inbox announcement
- Clearly labeled sponsored placement

### 12.16 Platform Settings

Settings:

- Platform name
- Domain
- Supported languages
- Supported currencies
- Payment providers
- Escrow rules
- Dispute SLA
- Region settings

### 12.17 Staff Roles and Permissions

Roles:

- Platform Ops
- Auditor read-only
- Dispute Manager
- Verification Officer
- Finance Admin
- Super Admin

---

## 13. Component Requirements

Reusable components:

```text
AppShell
PublicHeader
DashboardSidebar
TopBar
LanguageSwitcher
CurrencySwitcher
RegionSwitcher
NotificationBell
UserMenu
DataTable
FilterBar
StatusBadge
TrustBadge
EscrowStatusBadge
RiskFlagBadge
OfferMatrixTable
PriceBreakdownCard
Timeline
EvidenceUploader
MapRadiusSelector
LocationPicker
PaymentMethodSelector
TelegramConnectCard
EmailPreferenceCard
AuditLogViewer
DisputeDecisionPanel
```

---

## 14. State and API Integration Requirements

Frontend should be API-client driven.

Suggested API modules:

```text
api/auth.ts
api/users.ts
api/companies.ts
api/categories.ts
api/intents.ts
api/offers.ts
api/orders.ts
api/escrow.ts
api/deliveries.ts
api/disputes.ts
api/messages.ts
api/notifications.ts
api/audit.ts
api/admin.ts
```

State stores:

```text
stores/auth
stores/i18n
stores/region
stores/currency
stores/notifications
stores/buyer
stores/supplier
stores/admin
```

---

## 15. PWA and Future App Wrapper Readiness

Even though this document is for PC frontend, the shared frontend should be ready for future H5/PWA/Capacitor packaging.

Requirements:

- PWA manifest placeholder
- App icons placeholder
- Service worker placeholder
- Offline/error states
- API timeout/retry handling
- Safe-area CSS tokens for future mobile shell
- Touch-friendly shared components
- Camera/photo upload components should be reusable for H5/mobile
- GPS permission flow should be reusable for H5/mobile
- Push notification permission placeholder

---

## 16. Error, Empty, and Loading States

Every major page must include:

- Loading skeleton
- Empty state
- Error state
- Permission denied state
- Network error state
- Unauthorized/session expired state
- Form validation errors
- Confirmation modals for destructive actions

Critical actions must require confirmation:

- Publish request
- Award offer
- Cancel request
- Withdraw offer
- Confirm delivery
- Open dispute
- Release/refund escrow by admin
- Approve/reject KYB
- Suspend user/company

---

## 17. Security and Compliance UI Requirements

Frontend must show or support:

- Login session expiry
- 2FA placeholder
- KYC/KYB status
- Secure document upload
- Signed URL image/document preview
- PII masking before award
- Audit-aware admin action modals
- Staff permission-based menus
- Read-only auditor mode

---

## 18. Suggested Route Map

Public:

```text
/
/how-it-works
/categories
/suppliers
/trust-safety
/pricing
/help
```

Auth:

```text
/login
/register
/register/buyer
/register/supplier
/verify
/forgot-password
/onboarding/kyb
/onboarding/status
```

Buyer:

```text
/buyer/dashboard
/buyer/requests/new/category
/buyer/requests/new/details
/buyer/requests/new/natural-language
/buyer/requests/new/image
/buyer/requests/new/location
/buyer/requests/new/payment
/buyer/requests/new/review
/buyer/requests/:id
/buyer/requests/:id/offers
/buyer/offers/:id
/buyer/orders
/buyer/orders/:id
/buyer/orders/:id/confirm-delivery
/buyer/orders/:id/dispute
/buyer/disputes/:id
/buyer/watchlist
/buyer/messages
/buyer/messages/:threadId
/buyer/settings
```

Supplier:

```text
/supplier/dashboard
/supplier/pings
/supplier/pings/:id
/supplier/pings/:id/make-offer
/supplier/offers
/supplier/offers/:id
/supplier/orders
/supplier/orders/:id
/supplier/orders/:id/delivery-proof
/supplier/catalog
/supplier/catalog/new
/supplier/catalog/:id/edit
/supplier/catalog/import
/supplier/branches
/supplier/alerts
/supplier/payouts
/supplier/reviews
/supplier/team
/supplier/settings
```

Admin:

```text
/admin/dashboard
/admin/users
/admin/companies/verification
/admin/intents
/admin/offers
/admin/orders
/admin/escrow
/admin/disputes
/admin/disputes/:id
/admin/audit-logs
/admin/risk-flags
/admin/categories
/admin/attribute-schemas
/admin/pricing-intelligence
/admin/notifications/templates
/admin/ads
/admin/settings
/admin/staff
```

---

## 19. MVP Page Priority

### Priority 1 — Must Design First

```text
Landing Page
Login
Register
Buyer Dashboard
Post Request Flow
Location Radius Selector
Payment / Escrow Setup
Request Detail
Live Offers Matrix
Offer Detail
Buyer Order Detail
Supplier Dashboard
Ping Inbox
Make Offer
Supplier Order Detail
Catalog List
Admin Dashboard
Verification Queue
Dispute Center
Audit Logs
```

### Priority 2

```text
Ideal List
Messages
Supplier Branches
Alert Rules
Payout Settings
Risk Flags
Pricing Intelligence
Notification Templates
Settings
Language/Currency/Region settings
```

### Priority 3

```text
Ads/Promotions
Advanced pricing intelligence
Auto-offer rules
Full staff permission builder
Product catalog browsing Phase 2
```

---

## 20. Acceptance Criteria

The PC frontend is acceptable when:

1. It clearly communicates that the product is a buyer-request reverse marketplace.
2. Homepage prioritizes “Post Request,” not product waterfall browsing.
3. Buyer can complete the request posting flow from category to escrow setup.
4. Supplier can receive pings and submit offers.
5. Buyer can compare offers in a matrix and award one.
6. Order detail shows escrow and delivery timeline.
7. Dispute center exists for buyer and admin.
8. Admin console supports verification, disputes, escrow, audit logs, and risk flags.
9. Telegram and Email notification settings are visible.
10. Visa/Stripe/Payoneer/USDT placeholders are visible in payment/payout UI.
11. Language, currency, and region selectors are globally available.
12. Map radius targeting supports Cebu/Mandaue-style local radius selection.
13. UI is responsive and enterprise-grade.
14. Components are reusable for future H5/PWA/Capacitor packaging.
15. The UI does not hardcode `sanaoll.com`; it uses `{{APP_NAME}}` and `{{APP_DOMAIN}}` placeholders.

---

## 21. Single Prompt for UI Generation Tools

Use the following prompt for Stitch or similar UI generators:

```text
Design a PC web frontend for a modern enterprise-grade reverse e-commerce marketplace called {{APP_NAME}}. Do not hardcode the domain or brand; use {{APP_NAME}} and {{APP_DOMAIN}} placeholders.

The platform is not a traditional online store. It is a buyer-request marketplace: buyers post what they want to buy, including category, specs, quantity, budget, delivery location, and radius. Verified suppliers receive real-time pings, submit offers, and compete. Buyers compare offers by total landed cost, ETA, supplier trust, warranty, and distance. Buyers pay into escrow. Suppliers fulfill the order. Buyers confirm delivery. The platform releases payout to suppliers. If there is a problem, buyers open disputes and platform admins review evidence.

Create a clean, premium, enterprise SaaS style similar to Stripe Dashboard, Shopify Admin, Lazada Seller Center, Shopee Seller Center, Upwork proposal comparison, Alibaba RFQ, and Facebook Ads location targeting. Use cards, dashboards, tables, filters, trust badges, escrow status indicators, offer comparison matrices, and map-based radius selection.

The homepage must not be a traditional product waterfall as the primary experience. The homepage should prioritize Post Request, Describe what you need, category shortcuts, budget range, location radius, escrow protection, and active buyer request preview cards. Product catalog browsing can be shown only as a Phase 2 entry point.

Create these PC web areas: Public marketing site, Auth and onboarding, Buyer Portal, Supplier Portal, and Admin Operations Console.

Include public pages: Landing Page, How It Works, Categories, Supplier Onboarding, Trust & Safety, Pricing/Fees, Help Center.

Include buyer pages: Buyer Dashboard, Post Request Category Selection, Structured Item Details, Natural Language Request, Image Upload Search, Location and Radius Selection, Escrow Payment Setup, Request Review and Publish, Buyer Request Detail, Live Offers Matrix, Offer Detail, Buyer Orders List, Buyer Order Detail, Confirm Delivery, Open Dispute, Dispute Detail, Ideal List, Messages, Profile and Settings.

Include supplier pages: Supplier Dashboard, Ping Inbox, Buyer Intent Detail, Make Offer, Supplier Offers List, Supplier Offer Detail, Supplier Orders List, Supplier Order Detail, Delivery Proof Upload, Catalog List, Add/Edit Catalog Item, Bulk Import, Branch Management, Alert Rules, Payout Settings, Reviews and Trust Score, Team Members, Supplier Settings, Telegram and Email Notification Settings.

Include admin pages: Admin Dashboard, User Management, Company Verification Queue, Buyer Intent Management, Offer Management, Order Management, Escrow and Payment Transactions, Dispute Center, Audit Logs, Risk Flags, Category Management, Attribute Schema Builder, Pricing Intelligence, Notification Templates, Ads and Promotions, Platform Settings, Staff Roles and Permissions.

Default language is English. Include global language switcher and make the design ready for 10 languages: English, Simplified Chinese, Spanish, French, German, Japanese, Korean, Portuguese, Arabic, and Filipino/Tagalog. Include currency switching for PHP, USD, EUR, CNY, JPY, KRW, GBP, AUD, SGD, and USDT.

Include location targeting similar to Facebook Ads: country, city, area, map pin, and radius selector. Example areas include Cebu, Mandaue, and Lapu-Lapu. Users can set a search or delivery radius such as 1km, 3km, 5km, 10km, 25km, 50km, or custom. Show a map with a circular radius overlay and estimated supplier coverage.

Payment and escrow UI must support placeholders for Visa/Mastercard, Stripe checkout, Payoneer supplier payouts, USDT payment, manual bank transfer, and wallet balance. Show escrow states: authorization pending, funds held, captured, released, refunded, chargeback, and disputed.

Use a professional design system: deep blue or indigo primary, green for escrow safe and verified states, amber for warnings, red for danger/disputes, slate/gray neutrals, light gray dashboard background, rounded cards, clean tables, responsive navigation, sidebar dashboards, and clear action buttons.

Avoid old-fashioned demo UI, cluttered tables, and heavy orange/green colors. Make it look like a serious global procurement marketplace.
```
