# ProcurePing / {{APP_NAME}} — PC Web UI Prompt for Google Stitch

> Use this document directly in Google Stitch.  
> Default product name placeholder: `{{APP_NAME}}`  
> Default domain placeholder: `{{APP_DOMAIN}}`  
> Do **not** hardcode `sanaoll.com` in the UI. The website can temporarily be named Sanaoll, but all UI text should use configurable placeholders.

---

## 1. Product Context

Design a modern, enterprise-grade **PC web application** for a reverse e-commerce / buyer-request marketplace called `{{APP_NAME}}`.

This is **not a traditional online store** where sellers list products and buyers browse. This platform reverses the flow:

1. Buyers post what they want to buy.
2. Buyers define category, specs, quantity, budget, delivery location, radius, and preferred delivery time.
3. Verified suppliers receive real-time pings.
4. Suppliers submit offers.
5. Buyers compare offers side by side.
6. Buyer selects an offer.
7. Buyer pays into escrow.
8. Supplier delivers the goods.
9. Buyer confirms receipt.
10. Platform releases funds to supplier.
11. If there is a problem, buyer opens a dispute and platform reviews evidence.

The UI should feel like a serious global procurement and marketplace platform, combining the best parts of:

- Stripe Dashboard
- Shopify Admin
- Lazada Seller Center
- Shopee Seller Center
- Upwork proposal comparison
- Alibaba RFQ
- Facebook Ads location targeting
- Airbnb-style search filters

---

## 2. Design Style

Create a **desktop-first PC web UI** with responsive behavior for tablet and large mobile, but the main target is PC browser.

Style requirements:

- Modern enterprise SaaS
- Clean dashboard layout
- Premium B2B marketplace feel
- Card-based information architecture
- Data tables with filters, sorting, bulk actions, and row actions
- Clear trust badges and escrow state indicators
- Professional map/radius selector
- Clean offer comparison matrix
- Strong admin operations console
- Avoid old orange/green demo UI
- Avoid outdated 2010-style dashboards
- Use whitespace, modern typography, and clear hierarchy

Color system:

- Primary: deep blue / indigo
- Secondary: slate / gray
- Success: green for verified, escrow safe, released, delivered
- Warning: amber for pending, expiring, review needed
- Danger: red for dispute, rejected, suspicious, failed
- Info: cyan or sky blue for notifications and system tips
- Background: light gray dashboard background
- Cards: white with subtle border and soft shadow

Navigation:

- Public site: top navigation
- Buyer portal: left sidebar + top header
- Supplier portal: left sidebar + top header
- Admin console: dense left sidebar + top header
- Header should include language switcher, currency switcher, region selector, notification bell, messages, profile menu

---

## 3. Global Requirements

### 3.1 Internationalization

Default language: **English**.

The UI must be designed for internationalization and support a language switcher for at least these 10 languages:

1. English
2. Simplified Chinese
3. Spanish
4. French
5. German
6. Japanese
7. Korean
8. Portuguese
9. Arabic
10. Filipino / Tagalog

The layout should be compatible with longer translated strings. Include placeholder language selector in the header and settings pages.

### 3.2 Currency Support

Include currency switcher and currency-aware UI.

Supported currencies:

- PHP
- USD
- EUR
- CNY
- JPY
- KRW
- GBP
- AUD
- SGD
- USDT

Amounts should appear in structured forms such as:

- Budget min / max
- Unit price
- Delivery fee
- Total landed cost
- Escrow held amount
- Captured amount
- Released amount
- Refunded amount
- Supplier payout amount

### 3.3 Region and Location Targeting

Include a map-based location/radius selector similar to Facebook Ads location targeting.

The user can:

- Select country
- Select city
- Select area or district, for example Cebu, Mandaue, Lapu-Lapu
- Search location by address
- Use current location
- Place or move a map pin
- Select radius: 1km, 3km, 5km, 10km, 25km, 50km, or custom
- See circular radius overlay on the map
- See estimated suppliers inside the selected radius
- Save location presets

This location/radius selector should appear in buyer request creation, supplier branch settings, supplier alert rules, and admin region settings.

### 3.4 Payment and Escrow UI

Payment integration is not required in the design, but the UI must include placeholders for:

- Visa / Mastercard card payment
- Stripe checkout
- Payoneer supplier payout
- USDT payment
- Manual bank transfer
- Future wallet balance

Escrow states to show visually:

- Authorization pending
- Funds held
- Captured
- Released
- Refunded
- Chargeback
- Disputed

Important: The UI should explain that buyer funds are held safely and released only after buyer confirmation or platform dispute decision.

### 3.5 Trust and Anti-Fraud

The UI must include trust and safety components:

- Verified supplier badge
- KYB verified badge
- Response speed
- On-time delivery percentage
- Dispute rate
- Rating
- Risk flags
- Audit log timeline
- Dispute evidence panel
- Escrow protection badge
- Price outlier warning
- Suspicious supplier warning

---

## 4. Main PC Web Areas

Create a complete PC web UI covering these areas:

1. Public marketing website
2. Authentication and onboarding
3. Buyer portal
4. Supplier portal
5. Admin operations console
6. Payment and escrow flows
7. Dispute and audit flows
8. Settings and notification management

---

# 5. Public Website Pages

## Page 1 — Landing Page

Purpose: Explain the platform in one screen and convert users to post a request or become a supplier.

Content:

- Hero title: “Post what you need. Verified suppliers compete with offers.”
- Subtitle: “A safer reverse marketplace with escrow protection, supplier verification, and side-by-side offer comparison.”
- Primary CTA: “Post a Request”
- Secondary CTA: “Become a Supplier”
- How it works: Post Request → Receive Offers → Pay into Escrow → Confirm Delivery → Release Funds
- Category preview cards
- Escrow protection section
- Verified supplier section
- Global marketplace section
- Testimonials / trust metrics
- Footer with language, currency, region selectors

## Page 2 — How It Works

Content sections:

- For Buyers
- For Suppliers
- Escrow Protection
- Dispute Resolution
- No hidden commission model
- FAQ accordion

## Page 3 — Supplier Onboarding Marketing Page

Content:

- Receive real buyer pings
- Quote only on requests that match your inventory and delivery radius
- Manage offers, orders, proof of delivery, payouts
- KYB verification explanation
- CTA: “Start Supplier Verification”

## Page 4 — Categories Page

Show category cards:

- Construction
- Marine
- Auto
- IT / Office
- Electronics
- Home
- Fashion
- Services
- Custom Requests

Each category card should show example attributes and sample requests.

## Page 5 — Trust & Safety Page

Content:

- Escrow protection
- Verified suppliers
- Buyer privacy before award
- Audit logs
- Dispute center
- Anti-fraud monitoring
- Secure messaging

## Page 6 — Pricing / Fees Page

Content:

- Platform does not need to show commission by default
- Payment provider fees are transparently shown
- Optional ads/promotions for suppliers
- Optional premium supplier tools

## Page 7 — Help Center / FAQ

Create a searchable help center layout with categories:

- Buyer questions
- Supplier questions
- Escrow and payment
- Delivery and proof
- Disputes
- Account verification

---

# 6. Authentication and Onboarding Pages

## Page 8 — Login

Fields:

- Email or phone
- Password
- Remember me
- Forgot password
- Login button
- Google login placeholder
- Language selector

## Page 9 — Register Role Selection

Cards:

- I am a Buyer
- I am a Supplier
- Platform Staff, invite only

## Page 10 — Buyer Registration

Fields:

- Full name
- Email
- Phone
- Password
- Country
- City
- Preferred currency
- Terms checkbox

## Page 11 — Supplier Registration

Fields:

- Company name
- Contact person
- Email
- Phone
- Country
- Business type
- Primary categories
- Password
- Terms checkbox

## Page 12 — Email / Phone Verification

Design OTP verification page.

## Page 13 — Forgot Password

Email/phone reset flow.

## Page 14 — Supplier KYB Start

Explain required documents:

- Business registration
- Tax ID
- Owner or representative ID
- Store or warehouse photos
- Bank / Payoneer / payout account

## Page 15 — Supplier KYB Upload

Upload interface with document cards, status indicators, and progress checklist.

## Page 16 — Verification Status

States:

- Pending review
- Approved
- Rejected
- Need more documents

---

# 7. Buyer Portal PC Pages

## Page 17 — Buyer Dashboard

Layout:

- Sidebar navigation
- Top header with language, currency, region, notifications, messages, profile
- KPI cards:
  - Active requests
  - Offers received
  - Orders in progress
  - Escrow funds held
  - Disputes
- Active request table
- Recent offers panel
- Recent messages panel
- Recommended categories

## Page 18 — Post Request: Category Selection

UI:

- Search category input
- Popular category grid
- Recently used categories
- Custom request option
- Category attribute preview

## Page 19 — Post Request: Structured Item Details

Dynamic form based on category.

Fields:

- Request title
- Category
- Brand
- Model
- Condition
- Quantity
- Unit
- Budget min
- Budget max
- Currency
- Required attributes
- Optional attributes
- Photos / attachments
- Description
- Accept alternatives toggle

## Page 20 — Post Request: Natural Language Input

UI:

- Large text input
- Example prompt: “I need 500 bags of Holcim Portland cement delivered to Mandaue this weekend.”
- Parsed attributes preview panel
- Confidence badges
- Edit parsed fields button

## Page 21 — Post Request: Image Upload Search

UI:

- Upload image area
- Image preview
- Suggested category
- Suggested brand/model/specs
- Confidence indicators
- Confirm and continue

## Page 22 — Post Request: Location and Radius

Important page.

UI:

- Map panel
- Location search input
- Country/city/area selectors
- Current location button
- Radius slider and preset buttons
- Circular radius overlay
- Estimated suppliers in radius
- Delivery address form
- Saved locations
- Delivery methods selector

Example locations to show:

- Cebu
- Mandaue
- Lapu-Lapu

## Page 23 — Post Request: Payment and Escrow Setup

UI:

- Budget summary
- Deposit / full authorization selector
- Payment method cards:
  - Visa / Mastercard
  - Stripe checkout
  - USDT
  - Manual bank transfer
- Escrow explanation card
- Fee transparency card
- Authorization amount preview

## Page 24 — Request Review and Publish

UI:

- Request summary
- Specs summary
- Budget and currency
- Location radius map summary
- Delivery window
- Payment authorization status
- Supplier visibility setting
- Publish button

## Page 25 — Buyer Request Detail

UI:

- Request title and status
- Offer countdown
- Number of suppliers pinged
- Offers received
- Budget range
- Location radius
- Specs
- Attachments
- Messages tab
- Offers tab
- Activity timeline
- Edit/cancel request buttons

## Page 26 — Live Offers Matrix

Very important page.

Design a side-by-side comparison table with columns:

- Supplier
- Trust badge
- Rating
- Distance
- Unit price
- Delivery fee
- Total landed cost
- ETA
- Stock confidence
- Warranty
- Offer expiry
- Risk flag
- Action: View / Award

Default sorting:

- Total landed cost
- ETA
- Supplier trust

Include filters:

- Price range
- ETA
- Distance
- Verified only
- Stock confidence
- Payment method

## Page 27 — Offer Detail

UI:

- Supplier profile card
- Verification badges
- Offer price breakdown
- Delivery fee
- Total landed cost
- ETA
- Warranty
- Stock confidence
- Photos / documents
- Terms and notes
- Chat supplier
- Award offer button

## Page 28 — Buyer Orders List

Table columns:

- Order ID
- Supplier
- Item/request
- Total amount
- Escrow status
- Delivery status
- Updated time
- Action

Statuses:

- Awaiting payment
- Escrow funded
- Preparing
- Dispatched
- Delivered
- Accepted
- Disputed
- Completed
- Refunded

## Page 29 — Buyer Order Detail

UI:

- Order header
- Escrow timeline
- Delivery timeline
- Supplier info
- Request and offer summary
- Delivery proofs
- Messages
- Accept delivery button
- Open dispute button

## Page 30 — Confirm Delivery

UI:

- Checklist:
  - Correct item received?
  - Correct quantity?
  - Acceptable condition?
  - Delivery proof matches?
- Warning: confirming delivery releases escrow funds
- Confirm and release funds button

## Page 31 — Open Dispute

Fields:

- Reason
- Description
- Requested resolution
- Upload evidence
- Order summary
- Escrow status

Resolution options:

- Full refund
- Partial refund
- Replacement
- Supplier correction

## Page 32 — Dispute Detail

UI:

- Dispute status
- Evidence timeline
- Buyer claim
- Supplier response
- Admin decision
- Refund/release status
- Message thread

## Page 33 — Ideal List / Target Price Watchlist

UI:

- Saved desired items
- Target price
- Target location
- Radius
- Notify when matched
- Auto repost option
- Matching supplier count

## Page 34 — Buyer Messages

Thread list with filters by request/order/dispute.

## Page 35 — Buyer Message Thread

Chat UI with order/request context panel.

## Page 36 — Buyer Profile and Settings

Sections:

- Profile
- Addresses
- Saved locations
- Language
- Currency
- Region
- Notifications
- Payment methods
- Security

---

# 8. Supplier Portal PC Pages

## Page 37 — Supplier Dashboard

KPI cards:

- New pings
- Active offers
- Awarded orders
- Pending deliveries
- Payout amount
- Response SLA
- Rating
- Dispute rate

Panels:

- New matched requests
- Orders requiring action
- Recent messages
- Payout status

## Page 38 — Ping Inbox

Table/list of matched buyer requests.

Columns:

- Intent ID
- Category
- Request summary
- Budget
- Quantity
- Distance
- Delivery window
- Pre-funded badge
- Time left
- Action: Make Offer

Filters:

- Category
- Distance
- Budget
- Delivery date
- Pre-funded only
- New only

## Page 39 — Buyer Intent Detail for Supplier

UI:

- Buyer identity masked before award
- Request specs
- Budget range
- Quantity
- Delivery window
- Location radius, not exact address before award
- Attachments
- Price band indicator
- Risk tips
- Make offer button

## Page 40 — Make Offer

Fields:

- Unit price
- Quantity available
- Delivery fee
- ETA
- Warranty
- Stock confidence
- Offer expiry
- Tier: Good / Better / Best
- Notes
- Attachments

Preview:

- Total landed cost
- Buyer budget match
- Delivery distance
- Offer competitiveness score

## Page 41 — Supplier Offers List

Table columns:

- Offer ID
- Intent
- Buyer request
- Unit price
- Delivery fee
- Total
- Status
- Expiry
- Viewed by buyer
- Action

Statuses:

- Submitted
- Viewed
- Awarded
- Rejected
- Expired
- Withdrawn

## Page 42 — Supplier Offer Detail

UI:

- Offer summary
- Request context
- Buyer messages
- Edit/withdraw offer options if allowed
- Activity timeline

## Page 43 — Supplier Orders List

Table columns:

- Order ID
- Buyer request
- Total amount
- Escrow status
- Delivery status
- Deadline
- Payout status
- Action

## Page 44 — Supplier Order Detail

UI:

- Order summary
- Escrow captured badge
- Delivery deadline
- Buyer delivery address shown after award
- Delivery milestones
- Upload proof
- Message buyer
- Request payout / view payout status

## Page 45 — Delivery Proof Upload

Fields:

- Tracking number
- Courier
- Upload photos
- Upload delivery note
- Optional GPS proof
- Mark dispatched
- Mark delivered

## Page 46 — Supplier Catalog List

Table columns:

- Item image
- Item name
- Category
- Price
- Stock
- Branch
- Status
- Tags
- Match count
- Action

## Page 47 — Add/Edit Catalog Item

Fields:

- Images
- Title
- Category
- Dynamic attributes
- Brand
- Model
- UPC
- MPN
- Price
- Stock
- Branch
- Tags
- Status
- Description

## Page 48 — Bulk Catalog Import

UI:

- Upload CSV
- Template download button
- Field mapping preview
- Validation errors
- Import result summary

## Page 49 — Branch Management

UI:

- Branch list
- Add/edit branch drawer
- Branch name
- Address
- Map pin
- Service radius
- Delivery methods
- Business hours
- Branch status

## Page 50 — Alert Rules / Matching Triggers

Modern replacement for old “trigger tags”.

Fields:

- Watch category
- Watch brand
- Watch model
- Watch custom attributes
- Budget range
- Quantity range
- Location radius
- Notification channels: email, Telegram, dashboard, push placeholder
- Quiet hours
- Rate limit
- Auto-offer placeholder

## Page 51 — Supplier Payout Settings

UI:

- Bank account placeholder
- Payoneer placeholder
- USDT wallet placeholder
- Payout currency
- Verification status
- Payout schedule
- Payout history shortcut

## Page 52 — Supplier Reviews and Trust

UI:

- Rating average
- Review list
- On-time delivery percentage
- Dispute rate
- Response speed
- Verification badges
- Trust level progress

## Page 53 — Supplier Team Members

UI:

- User list
- Invite user
- Roles:
  - Supplier Admin
  - Supplier Agent
  - Finance
  - Warehouse
- Permissions matrix

## Page 54 — Supplier Settings

Sections:

- Company profile
- KYB documents
- Branch settings
- Notification channels
- Telegram bot connection
- Email settings
- Security
- Language/currency/region

---

# 9. Admin Operations Console PC Pages

## Page 55 — Admin Dashboard

KPI cards:

- GMV
- Active intents
- Offers submitted
- Orders in progress
- Escrow held
- Released amount
- Refunded amount
- Open disputes
- Verification queue
- Risk alerts

Charts:

- Intent volume by category
- Offers per intent
- Order completion rate
- Dispute rate
- Region heatmap placeholder

## Page 56 — User Management

Table:

- User
- Role
- Email/phone
- Country
- Status
- Created at
- Last login
- Risk flags
- Actions

## Page 57 — Company Verification Queue

UI:

- Company list
- Document viewer
- Tax ID
- Owner ID
- Store/warehouse photos
- Bank / Payoneer info
- Risk notes
- Approve / reject / request more documents

## Page 58 — Buyer Intent Management

Table:

- Intent ID
- Buyer
- Category
- Budget
- Currency
- Location
- Radius
- Offers count
- Status
- Risk flags
- Created at

## Page 59 — Offer Management

Table:

- Offer ID
- Supplier
- Intent
- Unit price
- Delivery fee
- Total
- ETA
- Status
- Risk flag
- Created at

## Page 60 — Order Management

Table:

- Order ID
- Buyer
- Supplier
- Total amount
- Escrow status
- Delivery status
- Dispute status
- Updated at
- Action

## Page 61 — Escrow and Payment Transactions

UI:

- Transaction table
- Provider filter: Visa, Stripe, Payoneer, USDT, bank transfer
- Status filter
- Order link
- Timeline panel
- Amount breakdown

States:

- Authorization pending
- Funds held
- Captured
- Released
- Refunded
- Chargeback
- Disputed

## Page 62 — Dispute Center

Very important admin page.

UI:

- Dispute case queue
- Evidence timeline
- Buyer claim
- Supplier response
- Order timeline
- Escrow status
- Chat/messages
- Admin internal notes
- Decision panel

Decision actions:

- Full refund
- Partial refund
- Release to supplier
- Request more evidence
- Escalate

## Page 63 — Audit Logs

Table:

- Timestamp
- Actor
- Actor role
- Action
- Entity type
- Entity ID
- Before / after changes
- IP address
- Device / user agent
- Risk level

Include filters by user, action, entity, date range, and risk level.

## Page 64 — Risk Flags

UI:

- Risk alert queue
- Suspicious price
- New supplier high-value order
- Repeated disputes
- Possible counterfeit
- Failed login attempts
- Cancellation abuse
- Velocity warning
- Resolve / escalate actions

## Page 65 — Category Management

UI:

- Category tree
- Add/edit category
- Status
- Icon
- Parent category
- Attribute schema link

## Page 66 — Attribute Schema Builder

Dynamic category form builder.

Fields:

- Field name
- Type
- Required
- Unit
- Allowed values
- Validation rule
- Display order
- Buyer visible
- Supplier visible

## Page 67 — Pricing Intelligence

UI:

- Category/SKU selector
- Region selector
- Currency selector
- P10 / P50 / P90 price band
- Outlier offer list
- Price history chart
- Risk tooltip for too-low or too-high quotes

## Page 68 — Notification Templates

Manage templates for:

- Email
- Telegram
- In-app notification
- SMS placeholder

Template examples:

- Supplier ping
- Offer submitted
- Offer expiring
- Award notice
- Delivery acceptance
- Dispute opened
- Payout released

## Page 69 — Ads and Promotions Management

Future monetization page.

UI:

- Sponsored supplier profiles
- Sponsored categories
- Promoted offers with clear label
- Inbox announcements
- Campaign status
- CTR / eCPM placeholder

## Page 70 — Platform Settings

Sections:

- Platform name `{{APP_NAME}}`
- Domain `{{APP_DOMAIN}}`
- Supported languages
- Supported currencies
- Payment providers
- Escrow rules
- Dispute SLA
- Region settings
- Notification settings
- Security settings

## Page 71 — Staff Roles and Permissions

UI:

- Staff list
- Invite staff
- Role templates:
  - Platform Ops
  - Auditor read-only
  - Dispute Manager
  - Verification Manager
  - Finance Manager
  - Super Admin
- Permissions matrix

---

# 10. Common Components to Design

Please create reusable components for:

1. App header
2. Sidebar navigation
3. Language switcher
4. Currency switcher
5. Region selector
6. Notification bell
7. Message icon
8. Profile menu
9. Trust badge
10. Escrow status badge
11. Risk flag badge
12. Supplier rating card
13. Offer comparison table
14. Payment method cards
15. Escrow timeline
16. Delivery timeline
17. Dispute timeline
18. Audit log drawer
19. Map radius selector
20. File upload component
21. Dynamic attribute form
22. Data table with filters
23. Empty state
24. Loading state
25. Error state
26. Confirmation modal
27. Bulk action toolbar
28. Chat panel
29. Evidence upload panel
30. Price-band ribbon

---

# 11. Important UX Rules

- Replace “Start Search” with “Post Request”.
- Always show “Total Landed Cost”, not only item price.
- In buyer offer comparison, default sort should be total landed cost, then ETA, then supplier trust.
- Before buyer awards an offer, supplier should not see exact buyer private details.
- Buyer should clearly see escrow protection before paying.
- Supplier should clearly see whether request is pre-funded.
- Admin should have full audit visibility.
- Dispute pages must show evidence timeline clearly.
- Payment pages must show provider placeholders without requiring real integration.
- Sponsored or promoted content must be clearly labeled.
- Do not let ads visually mix with organic ranking.
- All pages must support long translated text.
- All monetary values must show currency.
- All location-based pages must support radius targeting.

---

# 12. First Batch Priority Pages

If generating all pages is too large, prioritize these 25 PC pages first:

1. Landing Page
2. Login
3. Register Role Selection
4. Supplier KYB Upload
5. Buyer Dashboard
6. Post Request: Structured Item Details
7. Post Request: Location and Radius
8. Post Request: Payment and Escrow Setup
9. Request Review and Publish
10. Buyer Request Detail
11. Live Offers Matrix
12. Offer Detail
13. Buyer Order Detail
14. Open Dispute
15. Supplier Dashboard
16. Ping Inbox
17. Buyer Intent Detail for Supplier
18. Make Offer
19. Supplier Order Detail
20. Supplier Catalog List
21. Alert Rules / Matching Triggers
22. Admin Dashboard
23. Company Verification Queue
24. Dispute Center
25. Audit Logs

---

# 13. Final Design Direction

The final UI should look like a real enterprise-grade marketplace platform ready for global use. It should not look like a simple prototype.

The design must communicate:

- Buyer power
- Supplier competition
- Safe escrow
- Verified trust
- Transparent pricing
- Location-aware matching
- Global language and currency support
- Strong admin operations
- Fraud prevention and auditability