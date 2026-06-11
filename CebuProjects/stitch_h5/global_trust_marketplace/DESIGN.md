---
name: Global Trust Marketplace
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#454652'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#757684'
  outline-variant: '#c5c5d4'
  surface-tint: '#4355b9'
  primary: '#24389c'
  on-primary: '#ffffff'
  primary-container: '#3f51b5'
  on-primary-container: '#cacfff'
  inverse-primary: '#bac3ff'
  secondary: '#4d5a9c'
  on-secondary: '#ffffff'
  secondary-container: '#abb7ff'
  on-secondary-container: '#394687'
  tertiary: '#6c3400'
  on-tertiary: '#ffffff'
  tertiary-container: '#8f4700'
  on-tertiary-container: '#ffc7a2'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dee0ff'
  primary-fixed-dim: '#bac3ff'
  on-primary-fixed: '#00105c'
  on-primary-fixed-variant: '#293ca0'
  secondary-fixed: '#dee1ff'
  secondary-fixed-dim: '#b9c3ff'
  on-secondary-fixed: '#021355'
  on-secondary-fixed-variant: '#354282'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb784'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  h1:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  margin-mobile: 16px
  gutter-mobile: 12px
---

## Brand & Style

The design system is anchored in a **Corporate Modern** aesthetic that balances the authority of a global financial institution with the frictionless utility of a premier consumer application. It is designed to evoke immediate trust, reliability, and professional transparency, specifically catering to users engaged in high-value reverse e-commerce transactions.

The visual narrative focuses on clarity and structural integrity. By utilizing a "Soft Minimalism" approach, the system reduces cognitive load through generous whitespace and a strict card-based container logic. This ensures that complex marketplace data—such as escrow statuses, bidding histories, and dispute resolutions—remains legible and approachable on mobile devices.

## Colors

The palette is strategically weighted to emphasize security and system status.

- **Primary (Indigo):** Used for critical path actions, brand moments, and active states. It signals professional intent and stability.
- **Semantic Palette:** Success Green, Warning Amber, and Danger Red are reserved strictly for transactional statuses (e.g., "Escrow Released," "Payment Pending," "Dispute Opened"). These should always be paired with high-contrast text to ensure accessibility.
- **Neutrals:** A Slate/Gray scale is used for secondary information and borders to maintain a clean, "uncluttered" interface.
- **Background:** An off-white (#F8F9FA) provides a subtle contrast against white surface cards, enhancing the perceived depth of the layout.

## Typography

The typography system utilizes **Inter** to achieve a systematic, utilitarian feel. The hierarchy is "top-heavy," using bold weights for headlines to provide clear landmarks during fast scrolling. 

To maintain premium readability:
- **No text smaller than 12px** is permitted.
- **Body-lg (16px)** is the standard for user-generated content and descriptions.
- **Labels** use medium and semi-bold weights to differentiate from body text without requiring larger sizes.
- **Line Heights** are generous (1.5x for body) to ensure legibility in dense transactional lists.

## Layout & Spacing

This design system employs a **fluid grid** optimized for mobile viewports (H5). The standard layout uses a 16px outer margin to provide breathing room on small screens.

- **Grid:** A 4-column fluid layout for mobile. 
- **Rhythm:** An 8pt spacing system governs all vertical margins.
- **Safe Areas:** Sticky bottom elements must account for mobile browser chrome and notch safe areas, using a minimum of 24px padding at the base.
- **Touch Targets:** All interactive elements maintain a minimum hit area of 44x44px.

## Elevation & Depth

Visual hierarchy is established through **Ambient Shadows** and tonal layering. This creates a clear physical metaphor of "sheets" of information resting on a foundation.

- **Level 0 (Background):** Flat #F8F9FA.
- **Level 1 (Cards):** White surface with a soft, diffused shadow (Offset: 0, 4px; Blur: 12px; Color: rgba(0,0,0,0.05)).
- **Level 2 (Sticky Elements/Modals):** White surface with a more pronounced shadow to indicate it sits above the main content (Offset: 0, -4px; Blur: 20px; Color: rgba(0,0,0,0.08)).
- **Interaction:** Buttons utilize a slight inner shadow or darken by 5% on tap to provide tactile feedback.

## Shapes

The shape language is consistently **Rounded**, reflecting a modern and approachable consumer feel while maintaining enough structure for a "serious" marketplace.

- **Cards & Primary Containers:** 16px corner radius.
- **Buttons & Input Fields:** 12px corner radius.
- **Status Badges & Chips:** Fully pill-shaped (999px) to contrast against the more rectangular cards and buttons.
- **Visual Consistency:** Ensure that nested elements (like an image inside a card) have a slightly smaller radius (12px) than their parent (16px) to maintain geometric harmony.

## Components

### Buttons & Inputs
- **Primary Action:** 56px height, Indigo background, white semi-bold text. Sticky to the bottom of the viewport on transaction pages.
- **Input Fields:** 52px height, 1px Slate-200 border. Labels are always visible above the field (never just placeholders) to maintain context during entry.

### Cards & Status
- **Transaction Cards:** 16px padding, white background. Include a top-right **Status Badge** using semantic colors (Success/Warning/Danger) with 10% opacity backgrounds and 100% opacity text.
- **Trust Indicators:** Small, locked-width components featuring an icon (e.g., a shield) and "Verified" or "Escrow Protected" text in Success Green.

### Navigation
- **Sticky Bottom Tabs:** 64px height, blurred background (backdrop-filter: blur(10px)) or solid white. Icons use a 2pt stroke weight for clarity.
- **Progress Steppers:** Used for multi-step "reverse bidding" or "shipping" flows to reduce anxiety and show clear progress toward completion.

### Lists
- **Marketplace Rows:** Use 16px vertical padding with a thin 1px separator (#F1F5F9). Each row should have a clear "Chevron-right" accessory to indicate tapability.