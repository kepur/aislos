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
              v-for="link in isSupplier ? supplierNav : cebuNav"
              :key="link.to"
              :to="link.to"
              class="rounded-md px-2 py-1 hover:text-indigo-200 hover:bg-white/5"
              active-class="!text-indigo-300 bg-indigo-500/10"
            >
              {{ link.label }}
            </NuxtLink>
          </nav>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <PortalSwitcher />
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

const { logout } = useAuth()
const { t } = useI18n()
const route = useRoute()
const policy = useState<PortalPolicy | null>('procurement-portal-policy', () => null)
const { brand, portalKey } = useProcurementBrand(policy)
const isCebu = computed(() => route.path === '/market' || route.path.startsWith('/market/') || portalKey.value === 'cebu')
const isSupplier = computed(() => route.path === '/supplier' || route.path.startsWith('/supplier/'))

const brandLabel = computed(() =>
  isCebu.value ? t('procurement.brands.cebu') : t('procurement.brands.aislos'),
)

const cebuNav = [
  { to: '/market/buyer/dashboard', label: '工作台' },
  { to: '/market/buyer/projects', label: '项目' },
  { to: '/market/buyer/requests', label: '采购需求' },
  { to: '/market/buyer/orders', label: '订单' },
  { to: '/market/buyer/messages', label: '消息' },
  { to: '/market/buyer/wallet', label: '支付账本' },
  { to: '/market/buyer/disputes', label: '争议' },
  { to: '/market/buyer/settings', label: '设置' },
]
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
