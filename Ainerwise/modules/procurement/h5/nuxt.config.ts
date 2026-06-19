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
    "/api/admin/shipping/**": { proxy: `${coreApiInternal}/api/v1/admin/cebu-trade/shipping/**` },
    "/api/admin/deposits": { proxy: `${coreApiInternal}/api/v1/admin/cebu-trade/deposits` },
    "/api/admin/payouts": { proxy: `${coreApiInternal}/api/v1/admin/cebu-trade/payouts` },
    "/api/admin/ad-campaigns/**": { proxy: `${coreApiInternal}/api/v1/cebu-compat/admin/ad-campaigns/**` },
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
