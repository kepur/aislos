import autoprefixer from "autoprefixer";
import tailwindcss from "tailwindcss";

const coreApiInternal = process.env.NUXT_CORE_API_INTERNAL || "http://localhost:8000";

const tailwindTheme = {
  extend: {
    colors: {
      primary: {
        50: "#eef2ff",
        100: "#e0e7ff",
        200: "#c7d2fe",
        300: "#a5b4fc",
        400: "#818cf8",
        500: "#6366f1",
        600: "#4f46e5",
        700: "#4338ca",
        800: "#3730a3",
        900: "#312e81",
        950: "#1e1b4b",
      },
      success: "#16a34a",
      warning: "#d97706",
      danger: "#dc2626",
    },
    spacing: {
      "safe-bottom": "var(--safe-area-bottom)",
    },
    fontFamily: {
      sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
    },
    borderRadius: {
      "2xl": "1rem",
      "3xl": "1.5rem",
    },
    boxShadow: {
      card: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
      "card-hover": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
      bottom: "0 -2px 8px 0 rgb(0 0 0 / 0.08)",
    },
  },
};

export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: false },
  experimental: { appManifest: false },

  routeRules: {
    "/api/auth/system-mode": { proxy: `${coreApiInternal}/api/v1/cebu-compat/system-mode` },
    "/api/auth/**": { proxy: `${coreApiInternal}/api/v1/auth/**` },
    "/api/users/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/users/**` },
    "/api/addresses/**": { proxy: `${coreApiInternal}/api/v1/cebu-trade/addresses/**` },
    "/api/shipping/**": { proxy: `${coreApiInternal}/api/v1/cebu-trade/shipping/**` },
    "/api/ads/**": { proxy: `${coreApiInternal}/api/v1/cebu-trade/ads/**` },
    "/api/payouts/**": { proxy: `${coreApiInternal}/api/v1/cebu-trade/payouts/**` },
    "/api/wallets/me": { proxy: `${coreApiInternal}/api/v1/cebu-compat/wallets/me` },
    "/api/wallets/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/wallets/**` },
    "/api/admin/shipping/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/shipping/**` },
    "/api/admin/deposits": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/deposits` },
    "/api/admin/deposits/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/deposits/**` },
    "/api/admin/payouts": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/payouts` },
    "/api/admin/payouts/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/payouts/**` },
    "/api/admin/escrow": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/escrow` },
    "/api/admin/escrow/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/escrow/**` },
    "/api/admin/payment-events": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/payment-events` },
    "/api/admin/payment-events/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/payment-events/**` },
    "/api/admin/settlement-events": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/settlement-events` },
    "/api/admin/settlement-events/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/settlement-events/**` },
    "/api/admin/payment-region-configs": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/payment-region-configs` },
    "/api/admin/payment-region-configs/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/payment-region-configs/**` },
    "/api/admin/regions": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/regions` },
    "/api/admin/regions/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/regions/**` },
    "/api/admin/trust": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/trust` },
    "/api/admin/trust/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/trust/**` },
    "/api/admin/backups/config": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/backups/config` },
    "/api/admin/ai": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/ai` },
    "/api/admin/ai/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/ai/**` },
    "/api/admin/maps": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/maps` },
    "/api/admin/maps/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/maps/**` },
    "/api/admin/dashboard": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/dashboard` },
    "/api/admin/marketplace": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/marketplace` },
    "/api/admin/marketplace/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/marketplace/**` },
    "/api/admin/ad-campaigns": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/ad-campaigns` },
    "/api/admin/ad-campaigns/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/ad-campaigns/**` },
    "/api/admin/intents": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/intents` },
    "/api/admin/intents/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/intents/**` },
    "/api/admin/offers": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/offers` },
    "/api/admin/offers/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/offers/**` },
    "/api/admin/disputes": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/disputes` },
    "/api/admin/disputes/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/disputes/**` },
    "/api/admin/risk-flags": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/risk-flags` },
    "/api/admin/risk-flags/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/risk-flags/**` },
    "/api/admin/verification": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/verification` },
    "/api/admin/verification/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/verification/**` },
    "/api/admin/kyc-media": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/kyc-media` },
    "/api/admin/kyc-media/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/kyc-media/**` },
    "/api/admin/orders": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/orders` },
    "/api/admin/orders/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/orders/**` },
    "/api/admin/users": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/users` },
    "/api/admin/users/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/users/**` },
    "/api/admin/staff": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/staff` },
    "/api/admin/staff/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/staff/**` },
    "/api/admin/companies": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/companies` },
    "/api/admin/companies/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/companies/**` },
    "/api/admin/settings": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/settings` },
    "/api/admin/settings/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/settings/**` },
    "/api/admin/audit-logs": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/audit-logs` },
    "/api/admin/audit-logs/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/audit-logs/**` },
    "/api/admin/notification-templates": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/notification-templates` },
    "/api/admin/notification-templates/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/notification-templates/**` },
    "/api/admin/notifications": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/notifications` },
    "/api/admin/notifications/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/notifications/**` },
    "/api/admin/backups": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/backups` },
    "/api/admin/backups/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/backups/**` },
    "/api/admin/**": { proxy: `${coreApiInternal}/api/v1/admin/cebu/**` },
    "/api/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/**` },
  },

  modules: [
    "@pinia/nuxt",
    "@vueuse/nuxt",
  ],

  css: ["vant/lib/index.css", "~/assets/css/main.css"],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "/api",
      appName: process.env.NUXT_PUBLIC_APP_NAME || "AinerWise Procurement",
      appDomain: process.env.NUXT_PUBLIC_APP_DOMAIN || "procurement-h5.localhost",
    },
  },

  vite: {
    plugins: [],
    css: {
      postcss: {
        plugins: [
          tailwindcss({
            config: "./tailwind.config.cjs",
            theme: tailwindTheme,
          }),
          autoprefixer(),
        ],
      },
    },
    optimizeDeps: {
      include: ["vant"],
    },
  },

  build: {
    transpile: ["vant"],
  },

  typescript: {
    strict: true,
  },
});
