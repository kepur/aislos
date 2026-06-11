export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  experimental: { appManifest: false },

  app: {
    head: {
      title: 'AinerWise',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1' },
        { name: 'theme-color', content: '#0f172a' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-title', content: 'AinerWise' },
      ],
      link: [{ rel: 'manifest', href: '/manifest.webmanifest' }],
    },
  },

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
      portalMode: process.env.NUXT_PUBLIC_PORTAL_MODE || 'customer',
      customerUrl: process.env.NUXT_PUBLIC_CUSTOMER_URL || 'http://localhost:4098',
      partnerUrl: process.env.NUXT_PUBLIC_PARTNER_URL || 'http://localhost:4091',
      kioskUrl: process.env.NUXT_PUBLIC_KIOSK_URL || 'http://localhost:4090',
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
