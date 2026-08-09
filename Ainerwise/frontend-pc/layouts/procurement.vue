<template>
  <div class="min-h-screen procurement-layout text-slate-100">
    <header class="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
      <div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div class="flex items-center gap-3 min-w-0">
          <NuxtLink :to="brand.homePath" class="text-sm font-semibold text-white shrink-0">
            {{ brandLabel }}
          </NuxtLink>
          <span :class="['rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider shrink-0', brand.badge]">
            {{ $t('procurement.workspace') }}
          </span>
          <nav v-if="isCebu || isSupplier" class="hidden md:flex items-center gap-1 ml-2 text-xs text-slate-400">
            <NuxtLink
              v-for="link in primaryNav"
              :key="link.to"
              :to="link.to"
              class="rounded-md px-2 py-1 hover:text-indigo-200 hover:bg-white/5"
              active-class="!text-indigo-300 bg-indigo-500/10"
            >
              {{ link.label }}
            </NuxtLink>
            <!-- The buyer workspace has more destinations than fit the bar; the
                 overflow ones live behind this menu instead of being dropped. -->
            <div v-if="overflowNav.length" class="relative" @mouseleave="moreOpen = false">
              <button
                type="button"
                class="rounded-md px-2 py-1 hover:text-indigo-200 hover:bg-white/5"
                :class="{ '!text-indigo-300 bg-indigo-500/10': moreOpen || isOverflowActive }"
                @mouseenter="moreOpen = true"
                @click="moreOpen = !moreOpen"
              >
                {{ t('procurement.nav.more') }} ▾
              </button>
              <div
                v-if="moreOpen"
                class="absolute right-0 top-full z-50 mt-1 min-w-[160px] overflow-hidden rounded-xl border border-white/10 bg-slate-950/95 py-1 shadow-xl backdrop-blur-md"
              >
                <NuxtLink
                  v-for="link in overflowNav"
                  :key="link.to"
                  :to="link.to"
                  class="block px-3 py-2 text-xs text-slate-300 hover:bg-white/5 hover:text-indigo-200"
                  active-class="!text-indigo-300 bg-indigo-500/10"
                  @click="moreOpen = false"
                >
                  {{ link.label }}
                </NuxtLink>
              </div>
            </div>
          </nav>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <span v-if="policy" class="hidden sm:inline text-slate-400">
            {{ $t('procurement.mode') }}: {{ policy.default_procurement_mode }}
          </span>
          <LanguageSwitcher class="procurement-lang" />
          <button type="button" class="text-slate-400 hover:text-red-400" @click="logout">
            {{ $t('nav.logout') }}
          </button>
        </div>
      </div>
    </header>
    <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import type { PortalPolicy } from '~/composables/useProcurement'
import { stripLocalePrefix } from '~/utils/localeRoutes'

const { logout } = useAuth()
const { t } = useI18n()
const route = useRoute()
const policy = useState<PortalPolicy | null>('procurement-portal-policy', () => null)
const { brand, portalKey } = useProcurementBrand(policy)
// Routes are served under a locale prefix (/cn/market/...), so the raw path
// never matched these checks and the workspace nav silently disappeared.
const basePath = computed(() => stripLocalePrefix(route.path))
const isCebu = computed(() => basePath.value === '/market' || basePath.value.startsWith('/market/') || portalKey.value === 'cebu')
const isSupplier = computed(() => basePath.value === '/supplier' || basePath.value.startsWith('/supplier/'))

const brandLabel = computed(() =>
  isCebu.value ? t('procurement.brands.cebu') : t('procurement.brands.aislos'),
)

const moreOpen = ref(false)

// Buyer destinations, brought in line with the 4106 workspace. The first eight
// stay in the bar; the rest move into the overflow menu.
const cebuNav = computed(() => [
  { to: '/market/buyer/dashboard', label: t('procurement.nav.workspace') },
  { to: '/market/buyer/projects', label: t('procurement.nav.projects') },
  { to: '/market/buyer/requests', label: t('procurement.nav.requests') },
  { to: '/market/buyer/orders', label: t('procurement.nav.orders') },
  { to: '/market/buyer/messages', label: t('procurement.nav.messages') },
  { to: '/market/buyer/wallet', label: t('procurement.nav.wallet') },
  { to: '/market/buyer/disputes', label: t('procurement.nav.disputes') },
  { to: '/market/buyer/ideal-list', label: t('procurement.nav.idealList') },
  { to: '/market/buyer/notifications', label: t('procurement.nav.notifications') },
  { to: '/market/buyer/company-profile', label: t('procurement.nav.companyProfile') },
  { to: '/market/buyer/team', label: t('procurement.nav.team') },
  { to: '/market/buyer/settings', label: t('procurement.nav.settings') },
])
const supplierNav = [
  { to: '/supplier/dashboard', label: '工作台' },
  { to: '/supplier/pings', label: '匹配需求' },
  { to: '/supplier/catalog', label: '目录' },
  { to: '/supplier/offers', label: '报价' },
  { to: '/supplier/orders', label: '订单' },
  { to: '/supplier/messages', label: '消息' },
  { to: '/supplier/ads', label: '广告' },
  { to: '/supplier/payouts', label: '结算' },
  { to: '/supplier/team', label: '团队' },
  { to: '/supplier/settings', label: '设置' },
]

const NAV_BAR_SLOTS = 8
const activeNav = computed(() => (isSupplier.value ? supplierNav : cebuNav.value))
const primaryNav = computed(() => activeNav.value.slice(0, NAV_BAR_SLOTS))
const overflowNav = computed(() => activeNav.value.slice(NAV_BAR_SLOTS))
const isOverflowActive = computed(() =>
  overflowNav.value.some(link => basePath.value === link.to || basePath.value.startsWith(`${link.to}/`)),
)
</script>

<style scoped>
.procurement-layout {
  background: transparent;
}
:deep(.procurement-lang select) {
  background: rgba(15, 23, 42, 0.8) !important;
  border-color: rgba(148, 163, 184, 0.3) !important;
  color: #e2e8f0 !important;
}
</style>
