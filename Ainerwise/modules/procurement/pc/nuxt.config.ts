import autoprefixer from "autoprefixer";
import { fileURLToPath } from "node:url";

const tailwindColorsAlias = fileURLToPath(new URL("./tailwind-colors.mjs", import.meta.url));
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

  app: {
    pageTransition: false,
    layoutTransition: false
  },

  appConfig: {
    ui: {
      primary: "indigo",
      gray: "slate",
      colors: ["primary", "indigo", "slate", "green", "red", "yellow", "blue", "purple", "gray"],
    },
  },

  alias: {
    "#tailwind-config/theme/colors": tailwindColorsAlias,
  },

  devServer: {
    port: 4106,
  },

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
    "/api/admin/shipping/**": { proxy: `${coreApiInternal}/api/v1/admin/cebu-trade/shipping/**` },
    "/api/admin/deposits": { proxy: `${coreApiInternal}/api/v1/admin/cebu-trade/deposits` },
    "/api/admin/payouts": { proxy: `${coreApiInternal}/api/v1/admin/cebu-trade/payouts` },
    "/api/admin/ad-campaigns": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/ad-campaigns` },
    "/api/admin/ad-campaigns/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/ad-campaigns/**` },
    "/api/admin/disputes": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/disputes` },
    "/api/admin/disputes/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/disputes/**` },
    "/api/admin/risk-flags": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/risk-flags` },
    "/api/admin/risk-flags/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/risk-flags/**` },
    "/api/admin/verification": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/verification` },
    "/api/admin/verification/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/verification/**` },
    "/api/admin/kyc-media": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/kyc-media` },
    "/api/admin/kyc-media/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/kyc-media/**` },
    "/api/admin/**": { proxy: `${coreApiInternal}/api/v1/admin/cebu/**` },
    "/api/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/**` },
  },

  modules: [
    "@pinia/nuxt",
    "@nuxt/ui",
    "@vueuse/nuxt",
  ],

  ui: {
    disableGlobalStyles: true,
  },

  css: ["~/assets/css/compiled.css", "~/assets/css/nuxt-ui-fallback.css"],

  tailwindcss: {
    cssPath: false,
    configPath: "tailwind.config.cjs",
    config: {
      content: [
        "./app.vue",
        "./components/**/*.{vue,js,ts}",
        "./layouts/**/*.vue",
        "./pages/**/*.vue",
        "./plugins/**/*.{js,ts}",
        "./stores/**/*.{js,ts}",
        "./node_modules/@nuxt/ui/dist/runtime/**/*.{vue,js,mjs}",
      ],
      safelist: [
        "relative",
        "absolute",
        "inset-y-0",
        "start-0",
        "end-0",
        "flex",
        "items-center",
        "pointer-events-none",
        "ps-7",
        "ps-8",
        "ps-9",
        "ps-10",
        "ps-11",
        "ps-12",
        "pe-7",
        "pe-8",
        "pe-9",
        "pe-10",
        "pe-11",
        "pe-12",
        "px-2",
        "px-2.5",
        "px-3",
        "px-3.5",
        "h-4",
        "h-5",
        "h-6",
        "w-4",
        "w-5",
        "w-6",
        "form-input",
        "form-select",
        "form-checkbox",
      ],
      theme: tailwindTheme,
    },
    disableHMR: true,
    exposeConfig: false,
    viewer: false,
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "/api",
      appName: process.env.NUXT_PUBLIC_APP_NAME || "AinerWise Procurement",
      appDomain: process.env.NUXT_PUBLIC_APP_DOMAIN || "procurement.localhost",
    },
  },

  vite: {
    css: {
      postcss: {
        plugins: [autoprefixer()],
      },
    },
  },

  typescript: {
    strict: true,
  },
});
