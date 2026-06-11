---
name: ProcurePing
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f4'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#5b403d'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f0f1f1'
  outline: '#8f6f6c'
  outline-variant: '#e4beba'
  surface-tint: '#ba1a1f'
  primary: '#b6171d'
  on-primary: '#ffffff'
  primary-container: '#da3432'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb3ac'
  secondary: '#00677d'
  on-secondary: '#ffffff'
  secondary-container: '#8fe3ff'
  on-secondary-container: '#00667c'
  tertiary: '#615c41'
  on-tertiary: '#ffffff'
  tertiary-container: '#7a7558'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad6'
  primary-fixed-dim: '#ffb3ac'
  on-primary-fixed: '#410003'
  on-primary-fixed-variant: '#93000f'
  secondary-fixed: '#b4ebff'
  secondary-fixed-dim: '#7dd2ee'
  on-secondary-fixed: '#001f27'
  on-secondary-fixed-variant: '#004e5f'
  tertiary-fixed: '#ebe3c0'
  tertiary-fixed-dim: '#cec7a5'
  on-tertiary-fixed: '#1f1c06'
  on-tertiary-fixed-variant: '#4b472d'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
typography:
  display:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  h1:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  h3:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
  data-mono:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 40px
  xl: 64px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style
The design system is engineered for a high-stakes reverse marketplace where speed and security are paramount. The brand personality is **Professional, Secure, Global, and Efficient**. It targets enterprise procurement officers and global suppliers who require a tool that feels like a powerful financial instrument rather than a casual social platform.

The visual style is **Corporate / Modern**, leaning heavily into **Minimalism**. It prioritizes clarity through high-contrast elements and purposeful whitespace. By utilizing a "content-first" approach, the UI recedes to let critical data—such as bid amounts, lead times, and verification statuses—take center stage. The aesthetic avoids decorative flourishes, instead using structural alignment and subtle depth to convey a sense of institutional reliability.

## Colors
This design system employs a logic-driven palette designed for trust and functional signaling, featuring a clean white-base neutral set and a professional, high-contrast accent palette.

- **Primary (Vibrant Coral):** Reserved for primary actions, active navigation states, and branding. It represents the "Action" and "Urgency" inherent in a competitive bidding environment.
- **Secondary (Deep Teal):** Used for supporting information, secondary interactive elements, and professional contrast. This deep tone provides a stabilizing, corporate balance to the energetic coral.
- **Tertiary (Soft Cream):** Utilized for subtle background highlighting, "Pending" status containers, and low-priority UI sections.
- **Semantic Colors:** Emerald Green is strictly for "Escrow-Safe" and "Verified" indicators. Soft Cream/Tertiary handles "Pending" or "Expiring" states. Rose Red is reserved for "Disputes" and "Rejected Bids."
- **Neutrals:** The background (#FFFFFF) provides a clean, pure canvas. High-contrast Slate/Grey is used for body text to ensure WCAG AA compliance across all global regions.

## Typography
The design system utilizes **Inter** for its exceptional legibility in data-heavy environments and its comprehensive support for multi-language glyphs.

A strict hierarchy is maintained to ensure that bid numbers and status labels are immediately scannable. For currency and numeric data, the system activates tabular figures (`tnum`) to ensure columns of numbers align perfectly in data tables. Letter spacing is slightly tightened on larger headings for a more professional, "tight" editorial feel, while labels are tracked out for readability at small sizes.

## Layout & Spacing
The design system follows a **12-column fixed-grid model** for desktop, transitioning to a fluid layout for smaller viewports. 

- **The 8px Rhythm:** All spacing between elements (margins, padding) must be multiples of 8px (or 4px for tight components).
- **Margins:** Desktop views use 40px external page margins to create a sense of breathability and focus.
- **Data Density:** In data tables, vertical padding is reduced to 12px (sm) to maximize information density without sacrificing touch targets.
- **Internationalization Note:** Layouts must account for text expansion (up to 30% for German/French) and Right-to-Left (RTL) mirroring for Arabic. Ensure containers have flexible widths or robust overflow handling.

## Elevation & Depth
Depth in the design system is achieved through **Tonal Layers** and **Ambient Shadows**, avoiding heavy borders to maintain a modern SaaS aesthetic.

1.  **Level 0 (Floor):** The pure white background (#FFFFFF).
2.  **Level 1 (Card/Surface):** White surfaces with a subtle, 1px border (#F1F5F9) and no shadow. Used for standard dashboard tiles.
3.  **Level 2 (Active/Hover):** Soft, diffused shadow (0px 4px 12px rgba(0, 0, 0, 0.05)). Used to indicate interactable cards or focused states.
4.  **Level 3 (Overlays):** Modals and dropdowns use a high-precision shadow (0px 12px 32px rgba(0, 0, 0, 0.1)) to clearly separate them from the work surface.

Backdrop blurs (10px) are used sparingly for fixed headers to maintain context of the scroll position while ensuring text remains legible over content.

## Shapes
The design system uses a **Soft** shape language. This strikes a balance between the "rigid/sharp" look of traditional banking and the "overly-rounded" look of consumer apps.

- **Standard Radius:** 0.25rem (4px) for input fields, checkboxes, and small buttons.
- **Large Radius (rounded-lg):** 0.5rem (8px) for cards, data tables, and modal containers.
- **Pill Radius:** Used exclusively for status "Chips" (e.g., "Verified", "Open for Bids") to differentiate them from interactive buttons.

## Components
- **Buttons:** Primary buttons use the Vibrant Coral background with white text. Secondary buttons use a ghost style with a Deep Teal border and text.
- **Cards:** Information is organized into "White Cards" with 24px internal padding. Related data points are grouped with subtle dividers or Soft Cream backgrounds for pending items.
- **Data Tables:** Tables use a "borderless" internal look with only horizontal lines separating rows. Header cells use the `label-caps` typography style.
- **Trust Badges:** High-visibility "Verified Supplier" badges use the Emerald Green palette with a small shield icon. 
- **Map Components:** Professional grayscale base maps with Vibrant Coral pins and Deep Teal "active bid" clusters.
- **Global Header:** Must contain:
    - **Language Switcher:** Dropdown using ISO codes and localized names.
    - **Currency Switcher:** Toggles display values between USD, EUR, JPY, etc., applying the `data-mono` font to all price strings.
- **Input Fields:** 1px borders that transition to Vibrant Coral on focus. Errors must include both the Rose Red color and an icon for accessibility.