# Mobile H5 Frontend Requirements V1

Project placeholder: `{{APP_NAME}}`  
Domain placeholder: `{{APP_DOMAIN}}`  
Default language: English  
Primary target: Mobile H5 first, PWA-ready, future Capacitor Android/iOS wrapper ready.

---

## 1. Product Positioning

`{{APP_NAME}}` is a reverse e-commerce / buyer-request marketplace.

Traditional e-commerce flow:

```text
Supplier lists products → Buyer searches → Buyer purchases
```

`{{APP_NAME}}` core flow:

```text
Buyer posts what they need → Verified suppliers receive pings → Suppliers submit offers → Buyer compares offers → Buyer pays into escrow → Supplier delivers → Buyer confirms receipt → Platform releases funds
```

The mobile H5 experience must feel like a serious marketplace app, not a compressed desktop website.

The product should communicate three things immediately:

1. The buyer is in control.
2. Suppliers compete to give better offers.
3. Escrow protects both sides.

---

## 2. Mobile H5 Design Goal

The mobile H5 app must be:

- Eye-catching on the first screen
- Very clear for non-technical users
- Fast to understand in 5 seconds
- Built around “Post Request” rather than “Browse Products”
- Trustworthy enough for escrow/payment flows
- Easy for suppliers to respond quickly from a phone
- Ready to be packaged as a future mobile app using Capacitor

Recommended visual style:

```text
Modern mobile marketplace app
Premium SaaS trust layer
Shopee/Lazada mobile familiarity
Stripe-style escrow/payment confidence
Facebook Ads-like location targeting
Upwork-style offer comparison
```

Avoid old-fashioned UI, cluttered product grids, harsh orange/green colors, and desktop-like tables on mobile.

---

## 3. Mobile Design System

### 3.1 Color System

Use a clean enterprise marketplace palette:

```text
Primary: Deep Blue / Indigo
Accent Success: Green for escrow protected / delivery confirmed / payout released
Warning: Amber for pending, expiring, needs action
Danger: Red for disputes, failed verification, risk alerts
Neutral: Slate / Gray
Background: Soft light gray
Card background: White
```

### 3.2 Mobile UI Principles

- Large touch targets
- Sticky bottom action buttons
- Bottom tab navigation for buyer and supplier flows
- Step-by-step request posting wizard
- Cards instead of complex tables
- Clear escrow status badges
- Clear trust badges
- Clear price breakdowns
- Clean map and radius controls
- Fast access to messages and notifications
- Safe-area support for iPhone notch and Android gesture navigation

### 3.3 Typography

Use strong, modern hierarchy:

- Large bold hero heading on homepage
- Medium card titles
- Small but readable metadata
- Avoid dense paragraphs on mobile

---

## 4. Mobile Navigation Model

### 4.1 Public / Guest Navigation

Bottom or top simplified navigation:

```text
Home
Categories
How it works
Login
```

### 4.2 Buyer Bottom Tabs

```text
Home
Requests
Offers
Orders
Messages
```

Optional floating primary action:

```text
+ Post Request
```

### 4.3 Supplier Bottom Tabs

```text
Pings
Offers
Orders
Catalog
Messages
```

Optional floating action:

```text
+ Make Offer
```

### 4.4 Admin Mobile Access

Admin is PC-first. Mobile H5 should only include emergency operations:

```text
Dashboard
Disputes
Verifications
Risk Alerts
Transactions
```

---

## 5. Mobile Homepage Definition

The mobile homepage is the most important screen.

It must **not** be a traditional e-commerce waterfall homepage as the primary design.

The homepage should make users feel:

```text
“I can post what I need, and suppliers will come to me with offers.”
```

### 5.1 Homepage First Screen

The first screen should be visually strong and action-driven.

Recommended layout:

```text
Top Bar:
- {{APP_NAME}} logo placeholder
- Current location: Mandaue, Cebu
- Language / Currency selector
- Notification icon if logged in

Hero Area:
- Large headline:
  “Tell suppliers what you need.”
- Subheadline:
  “Post a request, compare verified offers, and pay safely with escrow.”

Main Action Card:
- Large input box:
  “What are you looking for?”
- Example placeholder:
  “500 bags of cement, iPhone 15 Pro Max, delivery to Mandaue…”
- Primary button:
  “Post Request”
- Secondary actions:
  “Upload Photo”
  “Browse Categories”

Location Strip:
- “Searching around Mandaue · 10 km radius”
- Change location button

Trust Strip:
- Escrow protected
- Verified suppliers
- Dispute support
```

### 5.2 Homepage Visual Direction

Use a high-conversion mobile app layout:

- Hero gradient background or premium clean illustration area
- Floating request input card
- Rounded cards
- Small animated trust indicators if supported
- Location chip and radius chip
- Strong primary CTA

The homepage should feel closer to:

```text
Airbnb search card + Lazada mobile familiarity + Stripe trust/payment confidence
```

Not like:

```text
Taobao/Shopee product waterfall first
```

### 5.3 Homepage Content Sections

After the first screen, show:

#### Section 1: Quick Categories

Horizontal scroll chips/cards:

```text
Construction
Auto
Marine
IT / Office
Electronics
Home
Fashion
Services
Custom Request
```

Each category card should include an icon, short label, and “Post request” behavior.

#### Section 2: Active Requests Near You

This can be a card feed, but it is a **request feed**, not a product waterfall.

Example cards:

```text
500 bags Holcim cement
Mandaue · 10 km radius
Budget PHP 240k–260k
12 suppliers pinged · 4 offers received
Escrow-ready
```

```text
Looking for used iPhone 15 Pro Max
Cebu City · 15 km radius
Budget PHP 35k–40k
Accepts alternatives
```

#### Section 3: How It Works

Simple 4-step mobile cards:

```text
1. Post Request
2. Receive Offers
3. Pay into Escrow
4. Confirm Delivery
```

#### Section 4: Escrow Protection Card

Explain in simple language:

```text
Your money is held safely until you confirm delivery.
If something goes wrong, open a dispute and submit evidence.
```

#### Section 5: Supplier CTA

```text
Are you a supplier?
Receive real buyer requests near your branch.
Become a Supplier
```

#### Section 6: Region Preview

Small map preview:

```text
Cebu
Mandaue
Lapu-Lapu
10 km radius
```

#### Section 7: App-like Install CTA

```text
Install {{APP_NAME}} for faster alerts and order tracking.
```

Use PWA installation placeholder.

---

## 6. Feed Strategy: Not Product Waterfall First

The mobile app can have feeds, but the primary feed should be based on marketplace intent.

### 6.1 Buyer Feed

Show:

- Active requests near the user
- Popular request categories
- Ideal list alerts
- Matching supplier offers
- Recently viewed categories
- Escrow education cards

### 6.2 Supplier Feed

Show:

- New buyer pings
- Pre-funded requests
- High-match requests
- Expiring pings
- Requests near supplier branches
- Orders needing action

### 6.3 Future Product Waterfall

Traditional product browsing can be included as Phase 2 only:

```text
Browse Products
Supplier Stores
Product Detail
Add to Ideal List
Request Better Offer
```

Do not make product waterfall the homepage’s main design in V1.

---

## 7. Mobile Page Inventory

The following screens should be covered in Mobile H5 V1.

---

## 8. Public / Guest Mobile Pages

### 8.1 Mobile Landing / Homepage

Purpose: Convert first-time users into posting a request or becoming a supplier.

Must include:

- Location-aware top bar
- Large request input
- Post Request CTA
- Upload Photo CTA
- Browse Categories CTA
- Escrow trust strip
- Active requests near user
- How it works
- Supplier CTA
- Language / currency selector

### 8.2 How It Works

Mobile explanation page.

Tabs:

```text
For Buyers
For Suppliers
Escrow Protection
Disputes
```

### 8.3 Categories

Mobile category browser.

- Search category
- Popular categories
- Industry groups
- Custom request option

### 8.4 Trust & Safety

Explain:

- Verified suppliers
- Escrow protection
- Dispute handling
- Audit logs
- Secure messaging
- Buyer privacy before award

### 8.5 Supplier Onboarding Landing

For suppliers:

- Receive buyer pings
- Submit offers
- Manage orders
- Get paid after delivery confirmation
- KYB required

### 8.6 Pricing / Fees

Explain:

- No platform commission placeholder
- Payment provider fees pass-through placeholder
- Ads/promotions optional
- Verification fast-track optional future add-on

### 8.7 Help Center / FAQ

Searchable FAQ mobile view.

---

## 9. Auth / Onboarding Mobile Pages

### 9.1 Login

- Email / phone login
- Password
- Forgot password
- Google login placeholder
- Language selector

### 9.2 Register Role Selection

Cards:

```text
I want to buy
I am a supplier
```

### 9.3 Buyer Registration

Fields:

- Full name
- Email
- Phone
- Password
- Country
- City
- Preferred currency

### 9.4 Supplier Registration

Fields:

- Company name
- Contact person
- Email
- Phone
- Country
- City
- Business category

### 9.5 Email / Phone Verification

OTP screen.

### 9.6 Forgot Password

Email/phone reset flow.

### 9.7 Supplier KYB Start

Explain required documents.

### 9.8 Supplier KYB Upload

Upload:

- Business registration
- Tax ID
- Owner ID
- Store/warehouse photo
- Bank / Payoneer payout info placeholder

### 9.9 Verification Status

States:

```text
Pending
Approved
Rejected
Need more documents
```

---

## 10. Buyer Mobile Pages

### 10.1 Buyer Home Dashboard

Logged-in buyer home.

Must show:

- Quick Post Request card
- Active requests
- Offers received
- Orders in progress
- Escrow status highlights
- Messages
- Ideal list alerts

### 10.2 Post Request - Category Selection

- Category search
- Popular categories
- Recent categories
- Custom request

### 10.3 Post Request - Text Input

Natural language request input.

Example:

```text
I need 500 bags of Holcim Portland cement delivered to Mandaue this weekend.
```

Show parsed fields after input.

### 10.4 Post Request - Structured Details

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
- Accept alternatives toggle
- Notes

### 10.5 Post Request - Image Upload

- Upload photo
- Take photo from camera
- Image preview
- Suggested category/specs
- Confirm/edit results

### 10.6 Post Request - Location & Radius

Core mobile page.

Must include:

- Map view
- Search location input
- Use current location
- Area chips: Cebu, Mandaue, Lapu-Lapu
- Radius selector: 1km, 3km, 5km, 10km, 25km, 50km, custom
- Circle overlay on map
- Supplier coverage estimate
- Delivery address field

### 10.7 Post Request - Payment / Escrow Setup

Payment placeholders:

- Visa / Mastercard
- Stripe Checkout
- USDT
- Manual bank transfer
- Wallet balance future

Escrow UI:

- Budget amount
- Deposit / full authorization
- Funds held until delivery confirmation
- Authorization pending / held status

### 10.8 Request Review & Publish

Show summary:

- Item specs
- Budget
- Location radius
- Payment method
- Escrow protection
- Visible to suppliers

CTA:

```text
Publish Request
```

### 10.9 Request Detail

Show:

- Status
- Time remaining
- Suppliers pinged
- Offers received
- Request details
- Attachments
- Edit/cancel actions

### 10.10 Live Offers

Mobile card-based offer comparison.

Each offer card:

- Supplier name
- Trust badge
- Unit price
- Delivery fee
- Total landed cost
- ETA
- Distance
- Rating
- Stock confidence
- Offer expiry
- View / Award button

Provide sorting/filter chips:

```text
Lowest total
Fastest ETA
Highest trust
Nearest
```

### 10.11 Offer Detail

- Supplier profile
- Offer breakdown
- Delivery plan
- Warranty
- Message supplier
- Award offer sticky CTA

### 10.12 Buyer Orders List

Status chips:

```text
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
- Delivery proof
- Messages
- Confirm receipt button
- Open dispute button

### 10.14 Confirm Delivery

Checklist:

- Correct item received
- Correct quantity
- Condition acceptable
- Release escrow funds

CTA:

```text
Confirm & Release Payment
```

### 10.15 Open Dispute

Fields:

- Reason
- Description
- Evidence upload
- Requested resolution
- Full refund / partial refund / replacement

### 10.16 Dispute Detail

- Timeline
- Buyer evidence
- Supplier response
- Admin decision
- Refund status

### 10.17 Ideal List / Watchlist

- Saved needs
- Target price
- Location range
- Notification preference
- Repost request option

### 10.18 Buyer Messages List

Threads grouped by request/order.

### 10.19 Buyer Message Thread

- Secure messaging
- Attachment upload
- Offer/order context card

### 10.20 Buyer Profile & Settings

- Profile
- Addresses
- Language
- Currency
- Region
- Payment methods
- Notification settings
- Security

---

## 11. Supplier Mobile Pages

### 11.1 Supplier Dashboard

Show:

- New pings
- Active offers
- Awarded orders
- Deliveries pending
- Payout status
- Response SLA
- Rating
- Dispute rate

### 11.2 Ping Inbox

Card list of buyer requests.

Each card:

- Category
- Request title
- Budget
- Distance
- Delivery window
- Pre-funded / escrow-ready badge
- Time left
- Make Offer CTA

### 11.3 Intent Detail for Supplier

Show:

- Buyer details masked before award
- Request specs
- Budget range
- Location radius
- Delivery window
- Attachments
- Price band placeholder
- Make Offer sticky CTA

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

Show total landed cost preview.

### 11.5 Supplier Offers List

Status chips:

```text
Submitted
Viewed
Awarded
Rejected
Expired
Withdrawn
```

### 11.6 Supplier Offer Detail

- Offer status
- Buyer request summary
- Edit/withdraw if allowed
- Message buyer

### 11.7 Supplier Orders List

- Awarded orders
- Delivery status
- Escrow captured badge
- Delivery deadline

### 11.8 Supplier Order Detail

- Order details
- Escrow captured status
- Buyer delivery address after award
- Delivery timeline
- Upload proof
- Message buyer

### 11.9 Delivery Proof Upload

Mobile-first capture flow:

- Take photo
- Upload from gallery
- Tracking number
- Delivery note
- GPS proof optional
- Mark dispatched / delivered

### 11.10 Catalog List

Mobile catalog cards:

- Item name
- Category
- Price
- Stock
- Branch
- Status
- Match count

### 11.11 Add / Edit Catalog Item

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

### 11.12 Bulk Import Placeholder

Mobile explanation screen. Actual CSV import is PC-preferred.

### 11.13 Branch Management

- Branch name
- Address
- Map pin
- Service radius
- Delivery methods
- Business hours

### 11.14 Alert Rules / Matching Triggers

Mobile rule cards:

- Category watch
- Brand/model watch
- Budget range
- Quantity range
- Location range
- Notification channels

### 11.15 Payout Settings

Placeholders:

- Bank account
- Payoneer
- USDT wallet
- Payout currency
- Verification status

### 11.16 Reviews & Trust

- Rating
- On-time delivery
- Dispute rate
- Response time
- Verification badges

### 11.17 Team Members

- Invite member
- Admin / Agent / Finance / Warehouse
- Role permissions summary

### 11.18 Supplier Settings

- Company profile
- KYB documents
- Notification channels
- Telegram connection
- Email settings
- Security

---

## 12. Admin Emergency Mobile Pages

Admin full console is PC-first, but mobile H5 should support urgent review.

### 12.1 Admin Mobile Dashboard

Show:

- Open disputes
- Verification queue
- Risk alerts
- Escrow held
- Failed payments

### 12.2 Verification Quick Review

- Company summary
- Documents
- Approve / reject / request more info

### 12.3 Dispute Quick Review

- Order timeline
- Evidence
- Buyer claim
- Supplier response
- Escrow status
- Request more evidence

### 12.4 Risk Alert Detail

- Risk type
- Related user/company/order
- Timeline
- Freeze / restrict / dismiss actions

### 12.5 Transaction Status View

- Authorization
- Captured
- Released
- Refunded
- Chargeback
- Disputed

---

## 13. Payment & Escrow Mobile UX

Payment providers are placeholders in V1 UI but must be represented clearly.

Support UI for:

```text
Visa / Mastercard card payment
Stripe checkout placeholder
Payoneer supplier payout placeholder
USDT payment placeholder
Manual bank transfer placeholder
Wallet balance future placeholder
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

Mobile escrow component should show:

- Amount
- Currency
- Current status
- Timeline
- Who needs to act next
- Safety explanation

---

## 14. Telegram / Email Notification UX

Mobile UI must include notification settings for both buyers and suppliers.

Channels:

```text
In-app notification
Telegram Bot
Email
SMS future
Push notification future
```

Supplier Telegram connection flow:

1. Open Telegram bot
2. Send verification code
3. Connection successful
4. Choose alert types

Notification types:

- New supplier ping
- New offer received
- Offer expiring
- Order awarded
- Payment/escrow status changed
- Delivery uploaded
- Confirm receipt reminder
- Dispute opened
- Admin decision

---

## 15. Internationalization Requirements

Default language: English.

Support 10 languages:

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

UI must include:

- Language switcher
- Currency switcher
- Region selector
- RTL-ready layout consideration for Arabic
- Text expansion-safe components

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

---

## 16. Location & Map Requirements

Location is a core feature.

Mobile UI must support:

- Current GPS location permission
- Country selector
- City selector
- Area selector
- Address search
- Map pin drag
- Radius slider
- Radius chips: 1km / 3km / 5km / 10km / 25km / 50km / custom
- Circle overlay on map
- Saved locations
- Supplier coverage estimate

Example locations:

```text
Cebu
Mandaue
Lapu-Lapu
Cebu City
```

The experience should feel similar to Facebook Ads location targeting.

---

## 17. PWA / Capacitor App-Ready Requirements

The mobile H5 frontend must be designed so it can later be packaged into Android/iOS using Capacitor.

Must support:

- PWA manifest
- Install app prompt placeholder
- Safe-area support
- Bottom navigation
- Camera/photo upload flows
- GPS permission screens
- Push notification permission placeholder
- Offline/error state
- App loading screen
- Deep-link ready routes
- Token storage strategy suitable for app wrapper

Do not design mobile as a compressed desktop layout.

---

## 18. Empty, Error, Loading States

Every important mobile page must include:

### Empty states

Examples:

```text
No offers yet
No active requests
No pings found
No orders yet
No disputes
No messages
```

### Loading states

- Skeleton cards
- Map loading
- Payment processing
- Upload progress

### Error states

- Payment failed
- Location permission denied
- Upload failed
- Network offline
- Verification rejected
- Escrow hold failed

---

## 19. Mobile Accessibility

Requirements:

- Large buttons
- High contrast status badges
- Clear labels
- Avoid tiny table columns
- Support screen reader labels
- Avoid color-only status indication
- Keep forms step-by-step

---

## 20. Stitch Prompt: Mobile H5 Full UI

Copy the prompt below into Google Stitch.

```text
Design a complete mobile H5 UI for a responsive reverse e-commerce marketplace called {{APP_NAME}}. Do not hardcode the brand name or domain. Use placeholders {{APP_NAME}} and {{APP_DOMAIN}}.

This is not a traditional e-commerce app. It is a buyer-request marketplace. Buyers post what they need, including product/service specs, quantity, budget, location, and search radius. Verified suppliers near the buyer receive real-time pings, submit offers, and compete. Buyers compare supplier offers, choose one, pay into escrow, receive delivery, confirm receipt, and then the platform releases funds to the supplier. If there is a problem, the buyer can open a dispute and submit evidence.

The mobile UI must feel like a polished native marketplace app, even though it is H5. It should be PWA-ready and future Capacitor Android/iOS wrapper ready. Use mobile-first responsive design, safe-area support, bottom navigation, sticky action buttons, camera/photo upload flows, GPS permission flows, and app-like loading/error states.

The homepage is extremely important. It must be eye-catching, modern, and directly connected to the core user need. Do not design the homepage as a traditional product waterfall. The primary homepage experience should be “Tell suppliers what you need.” Use a large hero area, a floating request input card, location chip, radius chip, quick actions, trust badges, and active request cards.

Homepage first screen requirements:
- Top bar with {{APP_NAME}} logo placeholder, current location such as “Mandaue, Cebu”, language/currency selector, and notification icon
- Large headline: “Tell suppliers what you need.”
- Subheadline: “Post a request, compare verified offers, and pay safely with escrow.”
- Large input card with placeholder: “What are you looking for?”
- Example text: “500 bags of cement, iPhone 15 Pro Max, delivery to Mandaue…”
- Primary CTA: “Post Request”
- Secondary actions: “Upload Photo” and “Browse Categories”
- Location strip: “Searching around Mandaue · 10 km radius” with Change button
- Trust strip: Escrow protected, Verified suppliers, Dispute support

Homepage below first screen:
- Horizontal quick category cards: Construction, Auto, Marine, IT/Office, Electronics, Home, Fashion, Services, Custom Request
- Active Requests Near You card feed, not product waterfall. Cards should show request title, location radius, budget, suppliers pinged, offers received, and escrow-ready badge
- How It Works: Post Request → Receive Offers → Pay into Escrow → Confirm Delivery
- Escrow Protection card explaining that money is held until buyer confirms delivery
- Supplier CTA: “Are you a supplier? Receive real buyer requests near your branch.”
- Region preview with Cebu, Mandaue, Lapu-Lapu and a map radius preview
- PWA install CTA placeholder

Use a modern premium visual style inspired by Airbnb search cards, Lazada/Shopee mobile familiarity, Stripe trust/payment UI, Facebook Ads location targeting, and Upwork proposal comparison. Avoid old-fashioned UI, cluttered product grids, and a homepage dominated by product waterfall.

Create mobile H5 screens for these areas:
1. Public homepage
2. How It Works
3. Categories
4. Trust & Safety
5. Supplier Onboarding Landing
6. Pricing / Fees
7. Help Center / FAQ
8. Login
9. Register Role Selection
10. Buyer Registration
11. Supplier Registration
12. Email / Phone Verification
13. Forgot Password
14. Supplier KYB Start
15. Supplier KYB Document Upload
16. Verification Status
17. Buyer Home Dashboard
18. Post Request - Category Selection
19. Post Request - Natural Language Text Input
20. Post Request - Structured Details
21. Post Request - Image Upload / Camera
22. Post Request - Location & Radius Map
23. Post Request - Payment / Escrow Setup
24. Request Review & Publish
25. Buyer Request Detail
26. Live Offers Card Comparison
27. Offer Detail
28. Buyer Orders List
29. Buyer Order Detail
30. Confirm Delivery / Release Payment
31. Open Dispute
32. Dispute Detail
33. Ideal List / Target Price Watchlist
34. Buyer Messages List
35. Buyer Message Thread
36. Buyer Profile & Settings
37. Supplier Dashboard
38. Supplier Ping Inbox
39. Buyer Intent Detail for Supplier
40. Make Offer
41. Supplier Offers List
42. Supplier Offer Detail
43. Supplier Orders List
44. Supplier Order Detail
45. Delivery Proof Upload
46. Supplier Catalog List
47. Add/Edit Catalog Item
48. Bulk Import Placeholder
49. Branch Management
50. Alert Rules / Matching Triggers
51. Payout Settings
52. Reviews & Trust Score
53. Team Members
54. Supplier Settings
55. Admin Mobile Dashboard
56. Verification Quick Review
57. Dispute Quick Review
58. Risk Alert Detail
59. Transaction Status View

Design payment and escrow placeholders for Visa/Mastercard, Stripe Checkout, Payoneer supplier payout, USDT payment, manual bank transfer, and future wallet balance. Show escrow states clearly: authorization pending, funds held, captured, released, refunded, chargeback, and disputed.

Design notification settings for in-app notifications, Telegram Bot, Email, future SMS, and future push notifications. Include Telegram connection flow for suppliers.

Default language is English. Include language switcher and design for 10 languages: English, Simplified Chinese, Spanish, French, German, Japanese, Korean, Portuguese, Arabic, and Filipino/Tagalog. Include currency switching for PHP, USD, EUR, CNY, JPY, KRW, GBP, AUD, SGD, and USDT. Consider RTL layout for Arabic.

Design map-based location targeting similar to Facebook Ads. Users can choose country, city, area, drag a map pin, and set a radius such as 1km, 3km, 5km, 10km, 25km, 50km, or custom. Include example regions Cebu, Mandaue, and Lapu-Lapu. Show a circle overlay on the map and a supplier coverage estimate.

Use the following design system:
- Primary color: deep blue or indigo
- Success: green for escrow protected, delivery confirmed, payout released
- Warning: amber for pending, expiring, or needs action
- Danger: red for disputes and risk alerts
- Neutral: slate/gray
- Background: soft light gray
- Rounded white cards
- Large touch-friendly buttons
- Sticky bottom CTAs
- Bottom tab navigation
- Clear icons
- Trust badges
- Escrow status badges
- Card-based offer comparison instead of dense tables

The result should look like a serious global mobile marketplace app that can later be packaged into Android/iOS using Capacitor.
```

---

## 21. Priority Pages for First Stitch Generation

If Stitch quality drops when generating too many screens, generate this first batch:

```text
1. Mobile Homepage
2. Login
3. Register Role Selection
4. Buyer Home Dashboard
5. Post Request - Text Input
6. Post Request - Structured Details
7. Post Request - Location & Radius Map
8. Post Request - Payment / Escrow Setup
9. Request Review & Publish
10. Buyer Request Detail
11. Live Offers Card Comparison
12. Offer Detail
13. Buyer Order Detail
14. Confirm Delivery
15. Open Dispute
16. Supplier Dashboard
17. Supplier Ping Inbox
18. Intent Detail for Supplier
19. Make Offer
20. Supplier Order Detail
21. Delivery Proof Upload
22. Admin Mobile Dashboard
23. Dispute Quick Review
24. Transaction Status View
```

---

## 22. Final Product Rule

The mobile H5 app should always guide the user toward this mental model:

```text
Post what you need.
Let verified suppliers compete.
Pay safely with escrow.
Release funds only after delivery.
```

This is the core product identity.
