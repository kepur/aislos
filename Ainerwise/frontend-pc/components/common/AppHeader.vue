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
        <LanguageSwitcher />
        <template v-if="isLoggedIn">
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
const { isLoggedIn, isAdmin, logout } = useAuth()
const { t } = useI18n({ useScope: 'global' })
const { mode, portal, urls } = usePortalMode()
const mobileMenuOpen = ref(false)

const navItems = computed(() => {
  if (mode === 'store') {
    return [
      { to: '/store', label: t('nav.store'), external: false },
      { to: '/products', label: 'Products', external: false },
      { to: urls.aislos, label: 'AISLOS', external: true },
    ]
  }
  if (mode === 'developer') {
    return [
      { to: '/developers', label: t('nav.developers'), external: false },
      { to: '/marketplace', label: t('nav.marketplace'), external: false },
      { to: urls.aislos, label: 'AISLOS', external: true },
    ]
  }
  return [
    { to: '/solutions', label: t('nav.solutions'), external: false },
    { to: '/ai-building-brain-demo', label: t('nav.aiBrain'), external: false },
    { to: urls.store, label: t('nav.store'), external: true },
    { to: urls.developer, label: t('nav.developers'), external: true },
  ]
})

const dashboardUrl = computed(() => {
  if (isAdmin.value && mode === 'store') return urls.storeAdmin
  if (isAdmin.value && mode === 'developer') return urls.agent
  if (isAdmin.value) return urls.admin
  if (mode === 'store') return `${urls.store}/store/orders`
  if (mode === 'developer') return `${urls.developer}/developers/listings`
  return urls.customer
})
</script>
