<template>
  <div>
    <!-- Login page: no shell -->
    <router-view v-if="$route.meta.public" />

    <!-- Admin shell -->
    <div v-else class="flex h-screen bg-slate-100 overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-56 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
        <div class="px-5 py-4 border-b border-slate-100">
          <p class="font-bold text-slate-900 text-base">ProcurePing</p>
          <p class="text-xs text-primary-600 font-semibold -mt-0.5">{{ t('login.title') }}</p>
        </div>
        <nav class="flex-1 p-3 space-y-0.5 overflow-y-auto">
          <template v-for="item in nav" :key="item.to">
            <p v-if="item.section" class="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3 pt-4 pb-1">{{ item.section }}</p>
            <router-link
              :to="item.to"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-colors"
              :class="$route.path === item.to ? 'bg-primary-50 text-primary-700' : 'text-slate-600 hover:bg-slate-50'"
            >
              <span class="w-5 text-center text-sm">{{ item.icon }}</span>
              {{ item.label }}
            </router-link>
          </template>
        </nav>
        <div class="p-4 border-t border-slate-100">
          <p class="text-xs text-slate-500 truncate mb-2">{{ auth.user?.email }}</p>
          <button class="w-full text-xs text-red-500 font-medium py-1.5 px-3 rounded-lg border border-red-100 hover:bg-red-50" @click="logout">
            {{ t('common.signOut') }}
          </button>
        </div>
      </aside>

      <!-- Main content -->
      <main class="flex-1 overflow-y-auto">
        <!-- Top bar -->
        <header class="bg-white border-b border-slate-100 px-6 h-14 flex items-center justify-between sticky top-0 z-20">
          <h2 class="font-semibold text-slate-800">{{ currentTitle }}</h2>
          <div class="flex items-center gap-3">
            <!-- Language switcher -->
            <select class="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-slate-600" :value="locale" @change="switchLocale($event.target.value)">
              <option v-for="l in supportedLocales" :key="l.code" :value="l.code">{{ l.name }}</option>
            </select>
            <span class="badge badge-blue">{{ auth.user?.role }}</span>
          </div>
        </header>
        <div class="p-6">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { SUPPORTED_LOCALES, applyDirection } from '@/i18n'

const { t, locale } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const supportedLocales = SUPPORTED_LOCALES

function switchLocale(lang) {
  locale.value = lang
  localStorage.setItem('admin_locale', lang)
  applyDirection(lang)
}

const nav = computed(() => [
  { to: '/dashboard',     icon: '📊', label: t('nav.dashboard'),      section: '' },
  { to: '/users',         icon: '👥', label: t('nav.users'),          section: t('sections.people') },
  { to: '/staff',         icon: '🛡️', label: t('nav.staff'),          section: '' },
  { to: '/companies',     icon: '🏢', label: t('nav.companies'),      section: '' },
  { to: '/verification',  icon: '✅', label: t('nav.verification'),   section: '' },
  { to: '/kyc-media',     icon: '🔍', label: 'KYC Media',              section: '' },
  { to: '/marketplace',   icon: '🏪', label: 'Marketplace',            section: t('sections.marketplace') },
  { to: '/ad-campaigns',  icon: '📣', label: 'Ad Campaigns',          section: '' },
  { to: '/intents',       icon: '📋', label: t('nav.intents'),        section: '' },
  { to: '/orders',        icon: '📦', label: t('nav.orders'),         section: '' },
  { to: '/disputes',      icon: '⚠️',  label: t('nav.disputes'),      section: '' },
  { to: '/escrow',        icon: '🔒', label: t('nav.escrow'),         section: t('sections.finance') },
  { to: '/payments',      icon: '💳', label: t('nav.payments'),       section: '' },
  { to: '/shipping',      icon: '🚚', label: t('nav.shipping'),       section: '' },
  { to: '/regions',       icon: '🗺️', label: t('nav.regions'),         section: '' },
  { to: '/risk',          icon: '🚨', label: t('nav.risk'),           section: t('sections.operations') },
  { to: '/trust',         icon: '⭐', label: t('nav.trust'),           section: '' },
  { to: '/notifications', icon: '🔔', label: t('nav.notifications'),  section: '' },
  { to: '/integrations',  icon: '🔌', label: t('nav.integrations'),   section: '' },
  { to: '/backups',        icon: '💾', label: 'Backups',               section: '' },
  { to: '/settings',      icon: '⚙️',  label: t('nav.settings'),      section: t('sections.system') },
  { to: '/audit',         icon: '📋', label: t('nav.audit'),          section: '' },
])

const titleMap = {
  '/dashboard': 'nav.dashboard',
  '/users': 'users.title',
  '/staff': 'staff.title',
  '/companies': 'companies.title',
  '/verification': 'verification.title',
  '/kyc-media': 'verification.title',
  '/backups': 'Backups',
  '/intents': 'intents.title',
  '/orders': 'orders.title',
  '/disputes': 'disputes.title',
  '/escrow': 'escrow.title',
  '/payments': 'payments.title',
  '/shipping': 'shipping.title',
  '/regions': 'regions.title',
  '/risk': 'risk.title',
  '/trust': 'trust.title',
  '/notifications': 'notifications.title',
  '/integrations': 'integrations.title',
  '/settings': 'settings.title',
  '/audit': 'audit.title',
  '/marketplace': 'nav.marketplace',
  '/ad-campaigns': 'nav.adCampaigns',
}
const currentTitle = computed(() => {
  const key = titleMap[route.path]
  if (!key) return t('nav.dashboard')
  // If the key doesn't contain a dot it's a raw label, not an i18n key
  return key.includes('.') ? t(key) : key
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
