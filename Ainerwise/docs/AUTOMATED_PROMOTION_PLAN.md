# AinerWise Automated Promotion Plan

## Business Goal

The platform should not behave like a generic bulk-email tool. Its job is to turn local presence, events, referrals, content, and website traffic into qualified B2B conversations while preserving trust and consent.

The promotion loop is:

```text
Campaign / event / showroom / referral
  -> attributed landing page or QR link
  -> requirement or product inquiry
  -> AI qualification and lead score
  -> automatic follow-up draft
  -> human approval
  -> consultation / site survey / proposal
  -> project / maintenance / referral
```

## Phase 1: Attribution And Review Queue

Implemented in the platform:

- Campaign records with reusable UTM campaign links
- First-touch attribution stored in browser session storage
- Attribution fields on leads and product inquiries
- Local prospect/contact records with consent status
- Automatic follow-up drafts for every new lead and inquiry
- Campaign draft generation only for explicitly opted-in contacts
- Daily draft preparation for active campaigns through Celery beat
- Admin marketing dashboard, conversion counts, and approval queue

The system deliberately creates `pending_approval` drafts rather than sending automatically. This protects brand quality and reduces GDPR/ePrivacy risk.

## Phase 2: Content Engine

Add an AI content workflow with admin approval:

- One approved case study becomes Serbian, English, and Chinese variants
- Generate LinkedIn post, Instagram caption, email, landing-page section, and event invitation
- Attach every content item to a campaign and solution line
- Publish only after human review
- Record URL, publish date, reach, clicks, and conversions

Recommended content ratio:

- 40% local case studies and before/after results
- 25% educational smart-building and energy content
- 20% partner/vendor demonstrations
- 10% showroom events
- 5% direct offers

## Phase 3: Local Network Automation

Use the prospect CRM for architects, electricians, installers, property managers, hotels, restaurants, and real-estate partners:

- Import or add contacts after meetings and events
- Tag by segment, city, relationship strength, and solution interest
- Generate a personalized next action after every interaction
- Remind the founder to call, invite, visit, or send a relevant case study
- Never run promotional sequences for `unknown`, `inquiry_only`, or `unsubscribed` consent states

## Phase 4: Showroom Growth Loop

Every physical event gets a campaign:

- QR code links to `/submit-requirement?utm_source=showroom&utm_medium=qr&utm_campaign=...`
- Event registrations become prospects with explicit consent choice
- Visitors receive a reviewed follow-up within one business day
- High-score visitors are routed to consultation or site survey
- Event conversion is measured through lead, quote, project, and lifecycle revenue

## Phase 5: Channel Integrations

Connect channels only after attribution and review workflows are stable:

- SMTP or transactional email provider for approved operational follow-ups
- Telegram for internal alerts
- WhatsApp Business for opted-in conversations
- Meta/Google/LinkedIn APIs for campaign statistics and approved publishing
- Calendar booking for consultations and showroom visits

## Metrics That Matter

Do not optimize for likes alone. Track:

- Qualified leads per campaign
- Time from inquiry to first human response
- Consultation and site-survey booking rate
- Quote and project conversion rate
- Gross profit and estimated LTV by source
- Partner/referral revenue
- Showroom event cost per qualified opportunity
