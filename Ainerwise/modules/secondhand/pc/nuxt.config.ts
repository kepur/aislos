const coreApiInternal = process.env.NUXT_CORE_API_INTERNAL || "http://backend:8000";

export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  devtools: { enabled: false },

  modules: ["@pinia/nuxt", "@nuxt/ui"],

  css: ["~/assets/css/main.css"],

  // Icons must resolve offline — the public iconify fallback hangs the UI
  // when the network is slow or blocked.
  icon: {
    localApiEndpoint: "/_nuxt_icon",
    fallbackToApi: false,
    clientBundle: { scan: true },
  },

  routeRules: {
    "/api/auth/**": { proxy: `${coreApiInternal}/api/v1/auth/**` },
    "/api/secondhand/**": { proxy: `${coreApiInternal}/api/v1/secondhand/**` },
    "/api/uploads": { proxy: `${coreApiInternal}/api/v1/cebu-compat/uploads` },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "/api",
      appName: process.env.NUXT_PUBLIC_APP_NAME || "2Hands",
      appDomain: process.env.NUXT_PUBLIC_APP_DOMAIN || "2hands.localhost",
      aislosSiteUrl: process.env.NUXT_PUBLIC_AISLOS_SITE_URL || "http://localhost:4099",
      defaultCurrency: process.env.NUXT_PUBLIC_DEFAULT_CURRENCY || "EUR",
      defaultCountry: process.env.NUXT_PUBLIC_DEFAULT_COUNTRY || "RS",
    },
  },

  app: {
    head: {
      title: "2Hands — buy and sell second-hand locally",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content:
            "Buy and sell quality second-hand gear locally. Graded condition, verified serials, collect in person.",
        },
      ],
    },
  },
});
