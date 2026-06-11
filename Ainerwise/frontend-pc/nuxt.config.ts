export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  experimental: { appManifest: false },

  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/i18n',
    '@pinia/nuxt',
    '@vueuse/nuxt',
  ],

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
      portalMode: process.env.NUXT_PUBLIC_PORTAL_MODE || 'aislos',
      /** Hostname + gateway inject portal policy; never send portal_key from the browser. */
      procurementEnabled: process.env.NUXT_PUBLIC_PROCUREMENT_ENABLED !== 'false',
      aislosUrl: process.env.NUXT_PUBLIC_AISLOS_URL || 'http://localhost:4099',
      storeUrl: process.env.NUXT_PUBLIC_STORE_URL || 'http://localhost:4096',
      developerUrl: process.env.NUXT_PUBLIC_DEVELOPER_URL || 'http://localhost:4092',
      customerUrl: process.env.NUXT_PUBLIC_CUSTOMER_URL || 'http://localhost:4098',
      adminUrl: process.env.NUXT_PUBLIC_ADMIN_URL || 'http://localhost:4097',
      storeAdminUrl: process.env.NUXT_PUBLIC_STORE_ADMIN_URL || 'http://localhost:4095',
      agentUrl: process.env.NUXT_PUBLIC_AGENT_URL || 'http://localhost:4093',
    },
  },

  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },

  i18n: {
    locales: [
      { code: 'en', name: 'English', file: 'en.json' },
      { code: 'zh', name: '中文', file: 'zh.json' },
      { code: 'sr', name: 'Srpski', file: 'sr.json' },
    ],
    defaultLocale: 'en',
    lazy: true,
    langDir: '.',
    strategy: 'no_prefix',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_locale',
      alwaysRedirect: false,
      fallbackLocale: 'en',
    },
  },

  build: {
    transpile: ['naive-ui', '@css-render/vue3-ssr', '@juggle/resize-observer'],
  },

  vite: {
    optimizeDeps: {
      include: ['naive-ui', 'vueuc', 'date-fns-tz/formatInTimeZone'],
    },
    plugins: [
      {
        name: 'fix-pinia-should-hydrate',
        enforce: 'pre' as const,
        transform(code: string, id: string) {
          if (id.includes('pinia') && id.endsWith('.mjs') && code.includes('obj.hasOwnProperty')) {
            return code.replace(
              /!isPlainObject\(obj\) \|\| !obj\.hasOwnProperty\(skipHydrateSymbol\)/g,
              '!isPlainObject(obj) || !Object.prototype.hasOwnProperty.call(obj, skipHydrateSymbol)'
            )
          }
        },
      },
    ],
  },
})
