import { fileURLToPath } from 'node:url'

const localeRoutePrefixes = ['/en', '/cn', '/rs', '/pl']

function addLocaleAliases(pages: any[]) {
  for (const page of pages) {
    if (page.path) {
      const basePath = page.path === '/' ? '' : page.path
      const aliases = localeRoutePrefixes.map(prefix => `${prefix}${basePath}`)
      page.alias = Array.from(new Set([
        ...(Array.isArray(page.alias) ? page.alias : page.alias ? [page.alias] : []),
        ...aliases,
      ]))
    }
    if (page.children) addLocaleAliases(page.children)
  }
}

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  experimental: { appManifest: false },

  hooks: {
    'pages:extend'(pages) {
      addLocaleAliases(pages)
    },
  },

  alias: {
    '@ainerwise/shared-auth': fileURLToPath(new URL('../shared/auth/useSharedAuth.ts', import.meta.url)),
  },

  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/i18n',
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
      // AISLOS Market (standalone procurement product). Official site links out here.
      marketUrl: process.env.NUXT_PUBLIC_MARKET_URL || 'http://market.localhost',
      // Use self-owned footage only. Defaults point at generated/local assets
      // and safely fall back to the in-house 3D scene if absent.
      homeHeroVideoWebm: process.env.NUXT_PUBLIC_HOME_HERO_VIDEO_WEBM || '/videos/ainerwise-smart-building-hero.webm',
      homeHeroVideoMp4: process.env.NUXT_PUBLIC_HOME_HERO_VIDEO_MP4 || '',
    },
  },

  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },

  i18n: {
    bundle: {
      optimizeTranslationDirective: false,
    },
    locales: [
      { code: 'en', name: 'English', file: 'en.json' },
      { code: 'zh', name: '中文', file: 'zh.json' },
      { code: 'sr', name: 'Srpski', file: 'sr.json' },
      { code: 'pl', name: 'Polski', file: 'pl.json' },
    ],
    defaultLocale: 'en',
    fallbackLocale: 'en',
    lazy: true,
    langDir: '.',
    strategy: 'no_prefix',
    // Locale is owned by middleware/locale.global.ts, which derives it from
    // the URL prefix and keeps the cookies in sync. nuxt-i18n's own cookie
    // detection was a second writer: it flipped the locale back on client
    // hydration, leaving the interface in one language on a URL of another —
    // and the next click dragged the visitor to whichever side won.
    detectBrowserLanguage: false,
  },

  build: {
    transpile: ['naive-ui', '@css-render/vue3-ssr', '@juggle/resize-observer'],
  },

  vite: {
    build: {
      chunkSizeWarningLimit: 600,
    },
    optimizeDeps: {
      include: ['naive-ui', 'vueuc', 'date-fns-tz/formatInTimeZone'],
    },
  },
})
