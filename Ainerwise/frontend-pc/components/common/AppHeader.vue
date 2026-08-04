<template>
  <header class="bg-slate-900/60 backdrop-blur-md border-b border-white/10 sticky top-0 z-50">
    <div class="container-main flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
      <NuxtLink :to="portal.home" class="flex items-center gap-2">
        <span class="text-xl font-bold text-primary-400 drop-shadow-[0_0_8px_rgba(14,165,233,0.5)]">{{ portal.name }}</span>
      </NuxtLink>

      <!-- Desktop Nav -->
      <nav class="hidden md:flex items-center gap-6">
        <template v-for="item in navItems" :key="item.label">
          <a v-if="item.external" :href="item.to" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ item.label }}</a>
          <NuxtLink v-else :to="item.to" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ item.label }}</NuxtLink>
        </template>
      </nav>

      <div class="flex items-center gap-3">
        <!-- Three themes now, so a colour swatch reads better than a
             sun/moon toggle: it shows which of the three is active. -->
        <div class="flex items-center gap-1 rounded-full border border-white/10 p-0.5">
          <button
            v-for="option in THEME_OPTIONS"
            :key="option.key"
            type="button"
            :aria-label="`Theme: ${option.key}`"
            :aria-pressed="theme === option.key"
            :title="option.key"
            class="h-6 w-6 rounded-full border-2 transition"
            :class="theme === option.key ? 'border-current scale-110' : 'border-transparent opacity-50 hover:opacity-100'"
            :style="{ backgroundColor: option.swatch }"
            @click="setTheme(option.key)"
          />
        </div>
        <LanguageSwitcher />
        <template v-if="isLoggedIn">
          <PortalSwitcher />
          <a :href="dashboardUrl" class="text-sm font-medium text-primary-400 hover:text-primary-300">
            {{ $t('nav.dashboard') }}
          </a>
          <button @click="logout" class="text-sm text-slate-400 hover:text-red-400">{{ $t('nav.logout') }}</button>
        </template>
        <template v-else>
          <NuxtLink to="/login" class="text-sm font-medium text-slate-300 hover:text-white">{{ $t('nav.login') }}</NuxtLink>
          <NuxtLink v-if="mode === 'aislos'" to="/submit-requirement" class="bg-primary-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-primary-500 transition shadow-[0_0_10px_rgba(14,165,233,0.3)]">{{ $t('nav.submitRequirement') }}</NuxtLink>
        </template>

        <!-- Mobile menu button -->
        <button @click="mobileMenuOpen = !mobileMenuOpen" class="md:hidden p-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile Nav -->
    <div v-if="mobileMenuOpen" class="md:hidden border-t border-white/10 bg-slate-900/95 backdrop-blur-md px-4 py-4 space-y-3">
      <template v-for="item in navItems" :key="item.label">
        <a v-if="item.external" :href="item.to" class="block text-sm text-slate-300" @click="mobileMenuOpen = false">{{ item.label }}</a>
        <NuxtLink v-else :to="item.to" class="block text-sm text-slate-300" @click="mobileMenuOpen = false">{{ item.label }}</NuxtLink>
      </template>
      <NuxtLink v-if="mode === 'aislos'" to="/submit-requirement" class="block text-sm font-medium text-primary-400" @click="mobileMenuOpen = false">{{ $t('nav.submitRequirement') }}</NuxtLink>
    </div>
  </header>
</template>

<script setup lang="ts">
import { prefixForLocale, withLocalePrefix } from '~/utils/localeRoutes'

const { theme, set: setTheme } = useTheme()
const { isLoggedIn, isAdmin, logout } = useAuth()
const { t, locale } = useI18n({ useScope: 'global' })
const { mode, portal: legacyPortal, urls } = usePortalMode()
const { manifest } = usePortalManifest()
const portal = computed(() => ({
  name: manifest.value?.portal_key === 'store' || mode === 'store'
    ? `AISLOS ${t('nav.products')}`
    : manifest.value?.display_name || legacyPortal.name,
  home: localPath(manifest.value?.home_route || legacyPortal.home),
}))
const mobileMenuOpen = ref(false)

function localPath(path: string) {
  const prefix = prefixForLocale(locale.value)
  return prefix ? withLocalePrefix(path, prefix) : path
}

function externalPath(baseUrl: string, path = '/') {
  const prefix = prefixForLocale(locale.value)
  const targetPath = prefix ? withLocalePrefix(path, prefix) : path
  try {
    return new URL(targetPath, baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`).toString()
  } catch {
    return `${baseUrl.replace(/\/$/, '')}${targetPath}`
  }
}

const navItems = computed(() => {
  if (mode === 'store') {
    return [
      { to: externalPath(urls.aislos, '/ai-building-brain'), label: t('nav.aiBrain'), external: true },
      { to: externalPath(urls.aislos, '/solutions'), label: t('nav.solutions'), external: true },
      { to: localPath('/products'), label: t('nav.products'), external: false },
      { to: externalPath(urls.developer, '/developers'), label: t('nav.developers'), external: true },
      { to: externalPath(urls.developer, '/marketplace'), label: t('nav.marketplace'), external: true },
      { to: externalPath(urls.market, '/marketplace'), label: t('nav.procurementMarket'), external: true },
    ]
  }
  if (mode === 'developer') {
    return [
      { to: externalPath(urls.aislos, '/ai-building-brain'), label: t('nav.aiBrain'), external: true },
      { to: externalPath(urls.aislos, '/solutions'), label: t('nav.solutions'), external: true },
      { to: externalPath(urls.store, '/products'), label: t('nav.products'), external: true },
      { to: localPath('/developers'), label: t('nav.developers'), external: false },
      { to: localPath('/marketplace'), label: t('nav.marketplace'), external: false },
      { to: externalPath(urls.market, '/marketplace'), label: t('nav.procurementMarket'), external: true },
    ]
  }
  return [
    { to: localPath('/ai-building-brain'), label: t('nav.aiBrain'), external: false },
    { to: localPath('/solutions'), label: t('nav.solutions'), external: false },
    { to: externalPath(urls.store, '/products'), label: t('nav.products'), external: true },
    { to: externalPath(urls.developer, '/developers'), label: t('nav.developers'), external: true },
    { to: externalPath(urls.developer, '/marketplace'), label: t('nav.marketplace'), external: true },
    { to: externalPath(urls.market, '/marketplace'), label: t('nav.procurementMarket'), external: true },
  ]
})

const dashboardUrl = computed(() => {
  if (isAdmin.value && mode === 'store') return urls.storeAdmin
  if (isAdmin.value && mode === 'developer') return urls.agent
  if (isAdmin.value) return urls.admin
  if (mode === 'store') return `${urls.store}/store/orders`
  if (mode === 'developer') return `${urls.developer}/developers/listings`
  return '/portal'
})
</script>
