# h5_ui_stitch_prompt.md

## Purpose

Use this document as a direct prompt for Google Stitch to design the **mobile H5 UI** for a reverse e-commerce / buyer-request marketplace.

The product is temporarily called `{{APP_NAME}}`. Do **not** hardcode `sanaoll.com` or any fixed domain in the UI. Use placeholders:

- `{{APP_NAME}}`
- `{{APP_DOMAIN}}`
- `{{SUPPORT_EMAIL}}`

Default language: **English**.

The UI must support internationalization for 10 languages:

- English
- Simplified Chinese
- Spanish
- French
- German
- Japanese
- Korean
- Portuguese
- Arabic
- Filipino / Tagalog

The UI must support currency switching:

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

---

# 1. Product Overview

Design a **mobile-first H5 web application** for `{{APP_NAME}}`, a reverse e-commerce marketplace.

This is not a traditional marketplace where sellers list products and buyers browse. Instead, buyers post what they want to buy, including category, specifications, budget, quantity, location, and delivery radius. Verified suppliers receive real-time pings, submit offers, and compete. Buyers compare offers, choose one, pay into escrow, receive the goods, confirm delivery, and only then does the platform release funds to the supplier.

If something goes wrong, the buyer can open a dispute. The platform can review evidence, pause payout, issue refunds, or release funds.

Core concept:

```text
Buyer posts request → Suppliers receive ping → Suppliers submit offers → Buyer compares offers → Buyer pays into escrow → Supplier delivers → Buyer confirms receipt → Platform releases payout
```

The mobile H5 UI should feel like a serious global marketplace with the simplicity of a consumer app and the trust of an enterprise escrow platform.

Reference style direction:

- Lazada / Shopee mobile marketplace clarity
- Stripe checkout trust and payment clarity
- Upwork proposal comparison logic
- Facebook Ads-style location radius targeting
- Airbnb-style location search and filtering
- Shopify-style clean account and order flows

Avoid old-fashioned demo UI. Avoid heavy orange/green colors. Use modern, clean, premium mobile interface patterns.

---

# 2. Visual Style

Create a modern mobile UI design system.

Recommended style:

- Mobile-first responsive H5
- Clean card-based layout
- Sticky bottom navigation for buyer and supplier portals
- Sticky action buttons on important flows
- Large tap targets
- Rounded cards
- Soft shadows
- Clear status badges
- Trust and safety indicators
- Minimal but information-rich product/request cards
- Enterprise-grade forms with progressive steps
- Mobile-friendly data comparison cards instead of wide desktop tables

Color direction:

- Primary: deep blue / indigo
- Success: green for escrow safe, confirmed, released, verified
- Warning: amber for pending, expiring, review needed
- Danger: red for dispute, rejected, risk flag, failed payment
- Neutral: slate / gray
- Background: very light gray or off-white

Typography:

- Clear mobile headings
- Strong hierarchy
- Avoid tiny text
- Use readable form labels
- Use short button copy

---

# 3. Global Mobile Navigation

Design mobile H5 navigation patterns for three main roles:

1. Buyer
2. Supplier
3. Admin / Platform Staff

## Buyer Bottom Navigation

Tabs:

- Home
- Post
- Offers
- Orders
- Account

## Supplier Bottom Navigation

Tabs:

- Dashboard
- Pings
- Offers
- Orders
- Account

## Admin Mobile Navigation

Admin is mainly desktop-first, but H5 should still provide mobile access for urgent actions.

Tabs:

- Dashboard
- Verifications
- Disputes
- Risk
- More

Use role-based navigation. A user who has both buyer and supplier access should be able to switch workspace.

---

# 4. Global Components

Create reusable mobile components:

## Request Card

Shows buyer request summary:

- Request title
- Category
- Quantity and unit
- Budget range
- Location and radius
- Time left
- Offer count
- Escrow/pre-funded badge
- Status badge

## Offer Card

Shows supplier offer summary:

- Supplier name
- Verified badge
- Trust score
- Unit price
- Delivery fee
- Total landed cost
- ETA
- Distance
- Warranty
- Stock confidence
- Offer expiry
- CTA: View / Award

## Escrow Status Card

Shows:

- Authorization pending
- Funds held
- Captured
- Released
- Refunded
- Chargeback
- Disputed

## Trust Badge

Shows:

- Verified business
- KYB approved
- On-time delivery percentage
- Dispute rate
- Rating
- Supplier tenure

## Location Radius Selector

Mobile map component:

- Search country / city / area
- Example areas: Cebu, Mandaue, Lapu-Lapu
- Use current location button
- Map pin
- Radius slider: 1km, 3km, 5km, 10km, 25km, 50km, Custom
- Circular radius overlay
- Supplier count estimate
- Delivery coverage estimate

## Payment Method Card

Payment options to show as placeholders:

- Visa / Mastercard
- Stripe Checkout
- Payoneer payout / supplier settlement
- USDT
- Manual bank transfer
- Wallet balance, future phase

## Status Timeline

Used in orders, delivery, disputes, and escrow:

- Created
- Payment authorized
- Offer awarded
- Preparing
- Dispatched
- Delivered
- Accepted
- Released
- Disputed
- Resolved

## Notification Preferences

Channels:

- In-app
- Email
- Telegram Bot
- SMS, future
- Mobile push, future

---

# 5. Public H5 Pages

## 5.1 Mobile Landing Page

Purpose: explain the marketplace quickly and convert users.

Sections:

- Hero headline: “Post what you need. Verified suppliers compete with offers.”
- Primary CTA: Post a Request
- Secondary CTA: Become a Supplier
- 3-step explainer:
  1. Post your request
  2. Compare supplier offers
  3. Pay safely with escrow
- Trust section:
  - Verified suppliers
  - Escrow protection
  - Dispute support
  - Secure messaging
- Popular categories carousel
- Language and currency switcher
- Footer links

Mobile UX:

- Sticky CTA at bottom
- Compact sections
- Horizontal category cards

## 5.2 How It Works

Separate tabs:

- For Buyers
- For Suppliers

Buyer flow:

- Post request
- Receive offers
- Compare total landed cost 
- Pay into escrow
- Confirm delivery

Supplier flow:

- Verify business
- Receive pings
- Submit offers
- Deliver order
- Receive payout

## 5.3 Trust & Safety

Explain:

- Escrow protection
- Verified suppliers
- KYB/KYC
- Audit logs
- Dispute center
- Secure messaging
- Buyer privacy before award

## 5.4 Supplier Onboarding Marketing Page

Sections:

- Receive real buyer requests
- Compete with offers
- Build trust score
- Get paid after delivery confirmation
- KYB required
- CTA: Start Supplier Verification

## 5.5 Category Browse Page

Even though the core flow is buyer request, show starter categories:

- Construction
- Marine
- Auto
- IT / Office
- Electronics
- Home
- Fashion
- Services
- Custom Requests

---

# 6. Authentication & Onboarding H5 Pages

## 6.1 Login

Fields:

- Email or phone
- Password
- Remember me
- Forgot password
- Login button
- Google login placeholder
- Register link
- Language switcher

## 6.2 Role Selection Register Page

Cards:

- I am a Buyer
- I am a Supplier

Each card explains benefits.

## 6.3 Buyer Registration

Fields:

- Full name
- Email
- Phone
- Password
- Country
- City
- Preferred currency

## 6.4 Supplier Registration

Fields:

- Company name
- Contact person
- Email
- Phone
- Country
- City
- Business type
- Main categories

## 6.5 Email / Phone Verification

OTP code UI.

## 6.6 Forgot Password

Email/phone input and reset flow.

## 6.7 KYC / KYB Intro

Explain required documents and review process.

## 6.8 Supplier KYB Upload

Mobile upload UI for:

- Business registration document
- Tax ID / business number
- Owner ID
- Store or warehouse photos
- Bank account placeholder
- Payoneer placeholder
- USDT wallet placeholder

## 6.9 Verification Status

States:

- Pending review
- Approved
- Rejected
- Need more documents

Show next steps and contact support.

---

# 7. Buyer H5 App Pages

## 7.1 Buyer Home / Dashboard

Widgets:

- Active requests
- Offers received
- Orders in progress
- Escrow held
- Disputes
- Ideal list alerts
- Recent messages

Primary CTA:

- Post a Request

Cards:

- Continue draft request
- New offers received
- Delivery awaiting confirmation

## 7.2 Post Request Step 1 — Category Selection

Mobile flow:

- Search category
- Popular categories
- Recent categories
- Custom request option

Use large selectable cards.

## 7.3 Post Request Step 2 — Item Details

Dynamic structured form.

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
- Accept alternatives toggle
- Notes
- Photos / attachments

Mobile UX:

- Progressive form sections
- Save draft
- Sticky Next button

## 7.4 Post Request — Natural Language Input

Text area:

“Describe what you need…”

Example:

“I need 500 bags of Holcim Portland cement delivered to Mandaue this weekend.”

After input, show parsed fields:

- Category
- Brand
- Quantity
- Budget
- Location
- Delivery window

User can edit parsed fields.

## 7.5 Post Request — Image Upload Search

UI:

- Upload photo
- Take photo from camera
- System suggested category
- Suggested attributes
- Buyer confirms or edits

## 7.6 Post Request Step 3 — Location & Radius

This is a critical mobile page.

Elements:

- Search location input
- Use current location
- Country selector
- City selector
- Area selector
- Example areas: Cebu, Mandaue, Lapu-Lapu
- Map preview
- Draggable pin
- Radius slider
- Radius chips: 1km, 3km, 5km, 10km, 25km, 50km, Custom
- Supplier coverage estimate
- Delivery methods

Show copy:

“Suppliers within this radius can receive your request.”

## 7.7 Post Request Step 4 — Delivery Window

Fields:

- Needed by date
- Time window
- Flexible date toggle
- Pickup / delivery / meet-up options

## 7.8 Post Request Step 5 — Escrow Payment Setup

Explain escrow in a simple card:

“Your money is held safely. The supplier gets paid only after you confirm delivery.”

Payment options:

- Visa / Mastercard
- Stripe Checkout placeholder
- USDT placeholder
- Manual bank transfer placeholder
- Wallet balance placeholder

Fields:

- Full budget authorization
- Deposit authorization
- Payment fee disclosure

Show escrow status preview:

- Authorization pending
- Funds held after publish

## 7.9 Request Review & Publish

Summary cards:

- Item details
- Quantity
- Budget
- Location radius
- Delivery window
- Payment method
- Escrow setup

CTA:

- Publish Request

Secondary:

- Save Draft

## 7.10 Request Published Success

Show:

- Request ID
- Suppliers pinged
- Estimated first offer time
- View live offers button

## 7.11 Buyer Request List

Tabs:

- Draft
- Active
- Awarded
- Expired
- Canceled

Request cards show:

- Offer count
- Time left
- Status
- Budget
- Location

## 7.12 Buyer Request Detail

Sections:

- Request summary
- Status
- Countdown
- Suppliers pinged
- Offers received
- Messages
- Attachments
- Edit/cancel request

Sticky bottom CTA:

- View Offers

## 7.13 Live Offers Mobile Comparison

Since H5 screen is narrow, do not use a desktop table. Use stacked comparison cards with sorting/filtering.

Controls:

- Sort by total landed cost
- Sort by ETA
- Sort by trust score
- Filter verified only
- Filter within budget
- Filter delivery date

Each offer card shows:

- Supplier name
- Trust badge
- Unit price
- Delivery fee
- Total landed cost
- ETA
- Distance
- Warranty
- Stock confidence
- Offer expiry
- CTA: View Details
- CTA: Award Offer

## 7.14 Offer Detail

Show:

- Supplier profile
- Verification badges
- Rating
- Price breakdown
- Delivery plan
- Warranty
- Offer terms
- Attachments/photos
- Chat supplier
- Award offer

## 7.15 Award Offer Confirmation

Before awarding, show:

- Selected supplier
- Total landed cost
- Escrow capture amount
- Delivery window
- Refund/dispute note
- Confirm award button

## 7.16 Buyer Orders List

Tabs:

- Awaiting payment
- Escrow funded
- Preparing
- Dispatched
- Delivered
- Accepted
- Disputed
- Completed
- Refunded

## 7.17 Buyer Order Detail

Sections:

- Order summary
- Escrow status card
- Delivery timeline
- Supplier info
- Delivery proof
- Messages
- Receipt / invoice placeholder

Sticky actions:

- Confirm Receipt
- Open Dispute

## 7.18 Confirm Receipt

Checklist:

- Correct item received
- Correct quantity
- Acceptable condition
- No dispute

CTA:

- Confirm Receipt & Release Funds

Warning text:

“After confirmation, the escrow payout will be released to the supplier.”

## 7.19 Open Dispute

Fields:

- Reason
- Description
- Upload evidence
- Requested resolution
  - Full refund
  - Partial refund
  - Replacement
  - Other

## 7.20 Buyer Dispute Detail

Show:

- Dispute status
- Evidence timeline
- Buyer claim
- Supplier response
- Admin decision
- Escrow hold status
- Refund status

## 7.21 Ideal List / Target Price Watchlist

Purpose: buyer saves desired items and target price.

Cards show:

- Item
- Target price
- Target location
- Radius
- Alert status
- Matched offers

Actions:

- Create new target
- Turn alert on/off
- Repost as request

## 7.22 Buyer Messages List

Show threads by request/order.

## 7.23 Buyer Message Thread

Features:

- Secure chat
- Attach images/files
- System notices
- Offer/order context card at top

## 7.24 Buyer Account

Sections:

- Profile
- Addresses
- Payment methods
- Language
- Currency
- Region
- Notifications
- Security
- Help
- Switch to Supplier workspace

## 7.25 Buyer Notification Settings

Channels:

- In-app
- Email
- Telegram Bot
- SMS, future
- Push, future

Events:

- New offerproof uploaded
- Dispute update
- Payment update

--- received
- Offer expiring
- Order status update
- Delivery 

# 8. Supplier H5 App Pages

## 8.1 Supplier Dashboard

Widgets:

- New pings
- Active offers
- Awarded orders
- Pending delivery
- Pending payout
- Response time
- Rating
- Dispute rate

Primary CTA:

- View New Pings

## 8.2 Supplier Ping Inbox

List of matched buyer requests.

Filters:

- Category
- Distance
- Budget
- Delivery date
- Pre-funded only
- Expiring soon

Ping card:

- Category
- Quantity
- Budget
- Location radius
- Time left
- Pre-funded badge
- Match score
- CTA: Make Offer

## 8.3 Buyer Intent Detail for Supplier

Buyer information should be masked before award.

Show:

- Request specs
- Budget range
- Quantity
- Delivery window
- Approximate location / radius
- Attachments
- Price band, if available
- Supplier eligibility status

CTA:

- Make Offer

## 8.4 Make Offer

Mobile form:

- Unit price
- Quantity available
- Delivery fee
- ETA
- Warranty
- Stock confidence
- Offer expiry
- Good / Better / Best tier
- Notes

Show sticky total preview:

- Unit price
- Delivery fee
- Total landed cost

CTA:

- Submit Offer

## 8.5 Offer Submitted Success

Show:

- Offer ID
- Expiry
- Request title
- View offer button

## 8.6 Supplier Offers List

Tabs:

- Submitted
- Viewed
- Awarded
- Rejected
- Expired
- Withdrawn

## 8.7 Supplier Offer Detail

Show:

- Offer summary
- Request context
- Buyer viewed status
- Expiry
- Edit offer, if allowed
- Withdraw offer

## 8.8 Supplier Orders List

Tabs:

- New awarded
- Preparing
- Dispatched
- Delivered
- Accepted
- Disputed
- Paid

## 8.9 Supplier Order Detail

Show:

- Order summary
- Escrow captured badge
- Buyer delivery address, visible after award
- Delivery deadline
- Timeline
- Messages
- Proof upload
- Payout status

Actions:

- Mark preparing
- Mark dispatched
- Upload proof
- Mark delivered

## 8.10 Delivery Proof Upload

Fields:

- Photos
- Tracking number
- Delivery note
- Optional GPS location
- Status update

CTA:

- Submit Delivery Proof

## 8.11 Supplier Catalog List

Mobile cards:

- Item name
- Category
- Price
- Stock
- Branch
- Status
- Tags
- Match count

Actions:

- Add item
- Edit item
- Set active/inactive

## 8.12 Add / Edit Catalog Item

Fields:

- Image
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

## 8.13 Bulk Import Mobile Helper

Since CSV import is hard on mobile, show a simplified upload helper:

- Upload CSV
- Download template
- Import status
- Validation errors

## 8.14 Branch Management

Fields:

- Branch name
- Address
- Map pin
- Service radius
- Delivery methods
- Business hours

## 8.15 Alert Rules / Matching Triggers

This replaces the old “Trigger” concept with a modern mobile UI.

Fields:

- Watch category
- Brand
- Model
- Attribute rules
- Budget range
- Quantity range
- Location radius
- Notification channels
- Quiet hours

Actions:

- Create alert rule
- Edit alert rule
- Pause alert rule

## 8.16 Supplier Payout Settings

Show payout methods:

- Bank transfer placeholder
- Payoneer placeholder
- USDT wallet placeholder

Fields:

- Payout currency
- Account verification status
- Settlement schedule

## 8.17 Supplier Trust & Reviews

Show:

- Average rating
- On-time delivery
- Dispute rate
- Response speed
- Verification badges
- Recent reviews

## 8.18 Supplier Team Members

Mobile list:

- Admin
- Agent
- Finance
- Warehouse

Actions:

- Invite member
- Change role
- Remove member

## 8.19 Supplier Settings

Sections:

- Company profile
- KYB documents
- Notification channels
- Telegram bot connection
- Email settings
- Security
- Language
- Currency
- Region

## 8.20 Telegram Connection Page

Purpose: connect Telegram API notifications.

Show:

- Telegram bot connect instructions
- Connect button
- Verification code
- Test notification button
- Events toggles

Events:

- New ping
- Offer awarded
- Order update
- Dispute opened
- Payout released

---

# 9. Admin / Ops H5 Pages

Admin mobile pages are for urgent actions. The full admin console is PC-first, but H5 should support essential workflows.

## 9.1 Admin Dashboard Mobile

Widgets:

- Active intents
- Orders in progress
- Escrow held
- Disputes open
- Verification pending
- Risk alerts

## 9.2 Verification Queue

Cards:

- Company name
- Country/city
- Submitted documents
- Risk notes
- Status

Actions:

- Approve
- Reject
- Request more documents

## 9.3 Verification Detail

Show:

- Company profile
- Documents
- Owner info
- Bank/Payoneer/USDT payout placeholders
- Audit timeline
- Admin notes

## 9.4 Dispute Center List

Filters:

- Open
- Waiting evidence
- Under review
- Escalated
- Resolved

Dispute cards:

- Order ID
- Buyer claim
- Supplier
- Escrow amount
- Deadline
- Risk level

## 9.5 Dispute Detail

Show:

- Order timeline
- Escrow status
- Buyer claim
- Supplier response
- Evidence images/files
- Chat history summary
- Admin decision panel

Actions:

- Request buyer evidence
- Request supplier evidence
- Full refund
- Partial refund
- Release to supplier
- Escalate

## 9.6 Escrow / Payment Transaction Detail

Show:

- Payment provider placeholder: Visa / Stripe / Payoneer / USDT / manual
- Authorization amount
- Captured amount
- Released amount
- Refunded amount
- Chargeback status
- Webhook event timeline placeholder

## 9.7 Risk Alerts

Risk cards:

- Suspicious pricing
- New supplier high-value order
- Too many disputes
- Possible counterfeit
- Repeated cancellation
- Multiple failed logins

## 9.8 Audit Log Mobile

Search and filter:

- Actor
- Role
- Action
- Entity type
- Date
- Risk level

Log card shows:

- Who
- Action
- Entity
- Timestamp
- IP/device
- Before/after diff link

## 9.9 Notification Template Quick Edit

Mobile simple template edit for:

- Email
- Telegram
- In-app

## 9.10 Platform Settings Mobile

Basic settings only:

- App name placeholder
- Supported languages
- Supported currencies
- Region availability
- Payment providers enabled
- Escrow rules summary

---

# 10. Payment & Escrow H5 Flows

Create mobile UI states for escrow and payment.

## 10.1 Payment Method Selection

Options:

- Visa / Mastercard
- Stripe Checkout
- USDT
- Manual bank transfer
- Wallet balance, future

## 10.2 Card Payment Placeholder

Fields:

- Card number
- Expiry
- CVC
- Billing country

Display as placeholder, not actual integration.

## 10.3 USDT Payment Placeholder

Show:

- Network selector placeholder
- Wallet address placeholder
- QR code placeholder
- Amount
- Expiry timer
- Payment pending state

## 10.4 Escrow Status Detail

Timeline:

- Authorization pending
- Funds held
- Offer awarded
- Captured
- Delivered
- Accepted
- Released

Exception states:

- Refunded
- Chargeback
- Disputed

## 10.5 Refund Status

Show:

- Refund amount
- Refund reason
- Method
- Estimated completion
- Timeline

---

# 11. Location & Map H5 Flow

Create a polished mobile location targeting flow similar to Facebook Ads.

Pages/components:

## 11.1 Select Region

- Country
- City
- Area
- Saved locations
- Recent locations

## 11.2 Map Radius Picker

- Full screen map
- Search bar at top
- Pin in center
- Radius circle overlay
- Bottom sheet for radius controls
- Supplier count estimate
- Confirm location button

## 11.3 Delivery Coverage Preview

Show:

- Selected area
- Radius
- Estimated suppliers
- Estimated delivery methods
- Estimated delivery fee range, if available

---

# 12. Internationalization H5 UI

Create mobile settings for:

- Language
- Currency
- Region
- Timezone
- Measurement units

Use English as default.

Language switcher should be visible on:

- Landing page
- Login
- Account settings

All UI copy should be written in English but designed to expand for longer translated text.

Arabic support must consider RTL layout compatibility.

---

# 13. Mobile Empty States

Design empty states for:

- No active requests
- No offers yet
- No orders
- No messages
- No pings
- No catalog items
- No disputes
- No notifications

Use helpful CTAs:

- Post your first request
- Add your first catalog item
- Create alert rule
- Connect Telegram notifications

---

# 14. Mobile Error & Safety States

Design states for:

- Payment failed
- Authorization failed
- Offer expired
- Request expired
- Supplier not verified
- Location permission denied
- Upload failed
- Dispute already opened
- Network offline
- Session expired

Use clear, calm language.

---

# 15. Mobile Notification Center

Notification types:

- New offer received
- Supplier ping received
- Offer expiring
- Offer awarded
- Payment authorized
- Escrow captured
- Delivery proof uploaded
- Buyer confirmed receipt
- Payout released
- Dispute opened
- Dispute resolved
- KYB approved/rejected

Each notification card should show:

- Icon
- Title
- Short message
- Timestamp
- Related entity
- Status color

---

# 16. H5 Page List Summary

Generate mobile H5 UI screens for at least the following pages:

## Public

1. Mobile Landing Page
2. How It Works
3. Trust & Safety
4. Supplier Onboarding Marketing Page
5. Category Browse Page

## Auth & Onboarding

6. Login
7. Register Role Selection
8. Buyer Registration
9. Supplier Registration
10. Email / Phone Verification
11. Forgot Password
12. KYC / KYB Intro
13. Supplier KYB Upload
14. Verification Status

## Buyer

15. Buyer Home / Dashboard
16. Post Request Category Selection
17. Post Request Item Details
18. Natural Language Request Input
19. Image Upload Search
20. Location & Radius Selector
21. Delivery Window
22. Escrow Payment Setup
23. Request Review & Publish
24. Request Published Success
25. Buyer Request List
26. Buyer Request Detail
27. Live Offers Mobile Comparison
28. Offer Detail
29. Award Offer Confirmation
30. Buyer Orders List
31. Buyer Order Detail
32. Confirm Receipt
33. Open Dispute
34. Buyer Dispute Detail
35. Ideal List / Target Price Watchlist
36. Buyer Messages List
37. Buyer Message Thread
38. Buyer Account
39. Buyer Notification Settings

## Supplier

40. Supplier Dashboard
41. Supplier Ping Inbox
42. Buyer Intent Detail for Supplier
43. Make Offer
44. Offer Submitted Success
45. Supplier Offers List
46. Supplier Offer Detail
47. Supplier Orders List
48. Supplier Order Detail
49. Delivery Proof Upload
50. Supplier Catalog List
51. Add / Edit Catalog Item
52. Bulk Import Mobile Helper
53. Branch Management
54. Alert Rules / Matching Triggers
55. Supplier Payout Settings
56. Supplier Trust & Reviews
57. Supplier Team Members
58. Supplier Settings
59. Telegram Connection Page

## Admin / Ops Mobile

60. Admin Dashboard Mobile
61. Verification Queue
62. Verification Detail
63. Dispute Center List
64. Dispute Detail
65. Escrow / Payment Transaction Detail
66. Risk Alerts
67. Audit Log Mobile
68. Notification Template Quick Edit
69. Platform Settings Mobile

## Payment / Escrow / Location

70. Payment Method Selection
71. Card Payment Placeholder
72. USDT Payment Placeholder
73. Escrow Status Detail
74. Refund Status
75. Select Region
76. Map Radius Picker
77. Delivery Coverage Preview
78. Language / Currency / Region Settings
79. Notification Center
80. Error / Empty State Examples

---

# 17. Final Stitch Instruction

Generate a complete mobile H5 UI design system and screen set for this product. Prioritize buyer and supplier flows first, then admin urgent-action flows. Use realistic sample data for Cebu, Mandaue, and Lapu-Lapu. Use English copy by default. Do not hardcode the final domain. Keep the UI clean, responsive, mobile-first, and enterprise-grade.

The final result should look like a serious global procurement marketplace with escrow protection, supplier verification, Telegram/email notifications, map radius targeting, and mobile-friendly offer comparison.
