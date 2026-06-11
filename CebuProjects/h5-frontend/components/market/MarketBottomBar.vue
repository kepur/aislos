<template>
  <nav class="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-slate-100 pb-safe">
    <div class="flex items-stretch h-14">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="flex-1 flex flex-col items-center justify-center gap-0.5 relative transition-all active:scale-90"
        :class="tab.active ? 'text-indigo-600' : 'text-slate-400'"
        @click="navigate(tab)"
      >
        <!-- Active indicator dot -->
        <span
          v-if="tab.active"
          class="absolute top-1.5 w-1 h-1 rounded-full bg-indigo-500"
        />

        <!-- Icon -->
        <div class="w-6 h-6 flex items-center justify-center">
          <svg v-if="tab.id === 'home'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <svg v-else-if="tab.id === 'market'" :fill="tab.active ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
          <svg v-else-if="tab.id === 'requests'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <svg v-else-if="tab.id === 'catalog'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <svg v-else-if="tab.id === 'wallet'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7H5a2 2 0 00-2 2v8a2 2 0 002 2h15a1 1 0 001-1V8a1 1 0 00-1-1z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 12h.01" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 7V5a2 2 0 012-2h8" />
          </svg>
          <svg v-else-if="tab.id === 'me'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <svg v-else-if="tab.id === 'login'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
          </svg>
        </div>

        <!-- Label -->
        <span class="text-[9px] font-semibold leading-none tracking-tight">{{ tab.label }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { t } = useI18n({ useScope: 'global' })

interface Tab {
  id: string
  label: string
  to: string
  active?: boolean
}

const tabs = computed<Tab[]>(() => {
  const isLoggedIn = authStore.isLoggedIn
  const isSupplier = authStore.isSupplier

  // Home destination
  const homeTab: Tab = {
    id: 'home',
    label: t('nav.home'),
    to: isLoggedIn ? (isSupplier ? '/supplier/dashboard' : '/buyer/home') : '/',
    active: false,
  }

  // Market tab (always active on this page)
  const marketTab: Tab = {
    id: 'market',
    label: t('nav.market'),
    to: '/marketplace',
    active: route.path === '/marketplace' || route.path.startsWith('/marketplace/'),
  }

  // Middle tab — role aware
  const middleTab: Tab = isSupplier
    ? { id: 'catalog', label: t('nav.catalog'), to: '/supplier/catalog', active: route.path.startsWith('/supplier/catalog') }
    : { id: 'requests', label: t('nav.requests'), to: isLoggedIn ? '/buyer/requests' : `/auth/login?return_url=${encodeURIComponent('/buyer/requests')}`, active: route.path.startsWith('/buyer/requests') }

  const walletTab: Tab = {
    id: 'wallet',
    label: t('nav.wallet'),
    to: isLoggedIn ? (isSupplier ? '/supplier/wallet' : '/buyer/wallet') : `/auth/login?return_url=${encodeURIComponent('/buyer/wallet')}`,
    active: route.path === '/buyer/wallet' || route.path === '/supplier/wallet',
  }

  // Account / Login
  const accountTab: Tab = isLoggedIn
    ? {
        id: 'me',
        label: t('nav.me'),
        to: isSupplier ? '/supplier/settings' : '/buyer/profile',
        active: false,
      }
    : { id: 'login', label: t('auth.sign_in'), to: `/auth/login?return_url=${encodeURIComponent(route.fullPath)}`, active: false }

  return [homeTab, marketTab, middleTab, walletTab, accountTab]
})

function navigate(tab: Tab) {
  router.push(tab.to)
}
</script>
