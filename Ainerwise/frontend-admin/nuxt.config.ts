export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  experimental: { appManifest: false },

  app: {
    head: {
      script: [
        {
          key: 'admin-theme-init',
          innerHTML: `(function(){try{if(location.pathname==='/login')return;var t=localStorage.getItem('admin-theme');if(t==='light')document.documentElement.classList.add('theme-light')}catch(e){}})();`,
          type: 'text/javascript',
        },
      ],
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
      portalMode: process.env.NUXT_PUBLIC_PORTAL_MODE || 'aislos',
      aislosAdminUrl: process.env.NUXT_PUBLIC_AISLOS_ADMIN_URL || 'http://localhost:4097',
      storeAdminUrl: process.env.NUXT_PUBLIC_STORE_ADMIN_URL || 'http://localhost:4095',
      marketingUrl: process.env.NUXT_PUBLIC_MARKETING_URL || 'http://localhost:4094',
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
