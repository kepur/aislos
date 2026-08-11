<template>
  <div class="min-h-screen procurement-layout text-slate-100">
    <header class="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
      <div class="mx-auto flex min-h-[4.5rem] max-w-7xl items-center justify-between gap-3 px-4 py-2 sm:px-6 lg:px-8">
        <div class="flex items-center gap-3 min-w-0">
          <NuxtLink :to="localized(brand.homePath)" class="text-2xl font-bold text-white shrink-0">
            {{ brandLabel }}
          </NuxtLink>
          <span :class="['rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider shrink-0', brand.badge]">
            {{ $t('procurement.workspace') }}
          </span>
          <!-- Long-language labels (Serbian/Bosnian) overrun a single row and used
               to collide with the language + account controls. The bar now wraps
               to at most two lines and shrinks its type, and the right-hand
               controls are pinned (shrink-0) so they never get pushed. -->
          <nav v-if="isCebu || isSupplier" class="hidden md:flex min-w-0 flex-wrap items-center gap-x-0.5 gap-y-1 ml-4 text-[0.82rem] leading-none text-slate-300">
            <NuxtLink
              v-for="link in primaryNav"
              :key="link.to"
              :to="localized(link.to)"
              class="ws-ripple whitespace-nowrap rounded-md px-2 py-1.5 font-medium transition hover:text-white hover:bg-white/5"
              active-class="ws-nav-on"
              @click="ripple"
            >
              {{ link.label }}
            </NuxtLink>
          </nav>
        </div>
        <div class="flex shrink-0 items-center gap-3 text-sm">
          <LanguageSwitcher class="procurement-lang" />
          <!-- Account menu. The overflow destinations used to hang off a
               hover-triggered "more" item mid-bar, which opened by accident and
               closed the moment the pointer left. It is a click-opened menu on
               the avatar now, the place people already look for account items. -->
          <div ref="accountRef" class="relative">
            <button
              type="button"
              class="ws-avatar flex items-center gap-2 rounded-full py-1 pl-1 pr-2.5 transition"
              :class="{ 'ws-avatar-open': accountOpen }"
              :aria-expanded="accountOpen"
              aria-haspopup="menu"
              @click="accountOpen = !accountOpen"
            >
              <span class="ws-avatar-badge">{{ userInitial }}</span>
              <span class="hidden text-xs font-medium sm:inline">{{ accountLabel }}</span>
              <span class="text-[10px] opacity-60">▾</span>
            </button>

            <div
              v-if="accountOpen"
              class="ws-menu absolute right-0 top-full z-50 mt-2 w-[26rem] overflow-hidden rounded-2xl border p-2"
              role="menu"
            >
              <div class="flex items-center gap-3 rounded-xl px-3 py-2.5 ws-sunken">
                <span class="ws-avatar-badge !h-9 !w-9 !text-sm">{{ userInitial }}</span>
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold ws-title">{{ user?.full_name || accountLabel }}</p>
                  <p class="truncate text-xs ws-faint">{{ user?.email }}</p>
                </div>
              </div>

              <div v-for="group in menuGroups" :key="group.key" class="mt-2">
                <p class="px-3 pb-1 text-[10px] font-bold uppercase tracking-[0.14em] ws-faint">
                  {{ group.label }}
                </p>
                <div class="grid grid-cols-2 gap-0.5">
                  <NuxtLink
                    v-for="link in group.items"
                    :key="link.to"
                    :to="localized(link.to)"
                    class="ws-menu-item flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition"
                    active-class="ws-menu-item-active"
                    role="menuitem"
                    @click="accountOpen = false"
                  >
                    <AppIcon :name="link.icon" class="h-4 w-4 shrink-0 opacity-70" />
                    {{ link.label }}
                  </NuxtLink>
                </div>
              </div>

              <div class="mt-2 border-t ws-hairline pt-2">
                <p v-if="policy" class="px-3 pb-1.5 text-[11px] ws-faint">
                  {{ $t('procurement.mode') }}: {{ policy.default_procurement_mode }}
                </p>
                <button
                  type="button"
                  class="ws-menu-item flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition hover:!text-red-500"
                  role="menuitem"
                  @click="logout"
                >
                  <AppIcon name="i-heroicons-arrow-right-on-rectangle" class="h-4 w-4 shrink-0 opacity-70" />
                  {{ $t('nav.logout') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
    <div class="mx-auto flex w-full max-w-[100rem] gap-0">
      <WorkspaceRail v-if="isCebu" :is-business="isBusiness" />
      <main class="min-w-0 flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:pl-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PortalPolicy } from '~/composables/useProcurement'
import { stripLocalePrefix } from '~/utils/localeRoutes'

const { logout } = useAuth()
const { t } = useI18n()
const route = useRoute()
const { localized } = useLocalizedLink()
const policy = useState<PortalPolicy | null>('procurement-portal-policy', () => null)
const { brand, portalKey } = useProcurementBrand(policy)
// Routes are served under a locale prefix (/cn/market/...), so the raw path
// never matched these checks and the workspace nav silently disappeared.
const basePath = computed(() => stripLocalePrefix(route.path))
// /portal carries the second half of the same buyer journey, so it shows the
// same shell and nav rather than a workspace of its own.
const isCebu = computed(() =>
  basePath.value === '/market' ||
  basePath.value.startsWith('/market/') ||
  basePath.value === '/portal' ||
  basePath.value.startsWith('/portal/') ||
  portalKey.value === 'cebu',
)
const isSupplier = computed(() => basePath.value === '/supplier' || basePath.value.startsWith('/supplier/'))

const brandLabel = computed(() =>
  isCebu.value ? t('procurement.brands.cebu') : t('procurement.brands.aislos'),
)

const { user } = useAuth()
const { getAccountContext } = useCommerce()

function ripple(event: MouseEvent) {
  const el = event.currentTarget as HTMLElement | null
  if (!el) return
  const rect = el.getBoundingClientRect()
  el.style.setProperty('--rx', `${event.clientX - rect.left}px`)
  el.style.setProperty('--ry', `${event.clientY - rect.top}px`)
  el.classList.remove('is-rippling')
  // Force a reflow so removing and re-adding the class restarts the animation.
  void el.offsetWidth
  el.classList.add('is-rippling')
  window.setTimeout(() => el.classList.remove('is-rippling'), 520)
}
const accountContext = ref<{ account_type?: string } | null>(null)
// Company and team only mean something on a business account; a personal buyer
// seeing a "team" entry is just noise.
const isBusiness = computed(() => String(accountContext.value?.account_type || '').toUpperCase() === 'BUSINESS')
onMounted(async () => {
  try { accountContext.value = await getAccountContext() } catch { accountContext.value = null }
})
const accountOpen = ref(false)
const accountRef = ref<HTMLElement | null>(null)

const userInitial = computed(() =>
  (user.value?.full_name || user.value?.email || '?').charAt(0).toUpperCase(),
)
const accountLabel = computed(() => user.value?.full_name?.split(' ')[0] || t('procurement.nav.account'))

// A click-opened menu has to close on an outside click, or it traps the page.
function closeOnOutsideClick(event: MouseEvent) {
  if (!accountOpen.value) return
  if (accountRef.value && !accountRef.value.contains(event.target as Node)) accountOpen.value = false
}
onMounted(() => document.addEventListener('click', closeOnOutsideClick))
onBeforeUnmount(() => document.removeEventListener('click', closeOnOutsideClick))
watch(() => route.fullPath, () => { accountOpen.value = false })

// One buyer journey, in the order it actually happens: source and buy under
// /market/buyer, then delivery through after-sales under /portal. Those two
// route trees used to be separate workspaces with no link between them.
const cebuNav = computed(() => [
  { to: '/market/buyer/dashboard', label: t('procurement.nav.workspace') },
  { to: '/market/buyer/requests', label: t('procurement.nav.requests') },
  { to: '/market/buyer/projects', label: t('procurement.nav.projects') },
  { to: '/market/buyer/orders', label: t('procurement.nav.orders') },
  { to: '/portal/projects', label: t('procurement.nav.delivery') },
  { to: '/portal/site-visits', label: t('procurement.nav.siteVisits') },
  { to: '/portal/installations', label: t('procurement.nav.installations') },
  { to: '/portal/assets', label: t('procurement.nav.assets') },
  { to: '/portal/tickets', label: t('procurement.nav.afterSales') },
  { to: '/market/buyer/messages', label: t('procurement.nav.messages') },
  { to: '/market/buyer/wallet', label: t('procurement.nav.wallet') },
  { to: '/portal/approvals', label: t('procurement.nav.approvals') },
  { to: '/market/buyer/disputes', label: t('procurement.nav.disputes') },
  { to: '/market/buyer/ideal-list', label: t('procurement.nav.idealList') },
  { to: '/market/buyer/notifications', label: t('procurement.nav.notifications') },
  { to: '/market/buyer/company-profile', label: t('procurement.nav.companyProfile') },
  { to: '/market/buyer/team', label: t('procurement.nav.team') },
  { to: '/portal/insights', label: t('procurement.nav.insights') },
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

// Menu contents, grouped by what the entry is for rather than listed flat.
const menuGroups = computed(() => {
  if (isSupplier.value) {
    return [{ key: 'work', label: t('procurement.menu.work'), items: overflowNav.value }]
  }
  const account = [
    { to: '/market/buyer/settings', icon: 'i-heroicons-cog-8-tooth', label: t('procurement.nav.settings') },
    { to: '/market/buyer/wallet', icon: 'i-heroicons-wallet', label: t('procurement.nav.wallet') },
    { to: '/market/buyer/notifications', icon: 'i-heroicons-bell-alert', label: t('procurement.nav.notifications') },
  ]
  if (isBusiness.value) {
    account.push(
      { to: '/market/buyer/company-profile', icon: 'i-heroicons-building-office', label: t('procurement.nav.companyProfile') },
      { to: '/market/buyer/team', icon: 'i-heroicons-users', label: t('procurement.nav.team') },
    )
  }
  return [
    {
      key: 'work',
      label: t('procurement.menu.work'),
      items: [
        { to: '/market/buyer/messages', icon: 'i-heroicons-chat-bubble-left-right', label: t('procurement.nav.messages') },
        { to: '/portal/approvals', icon: 'i-heroicons-check-badge', label: t('procurement.nav.approvals') },
        { to: '/market/buyer/disputes', icon: 'i-heroicons-exclamation-triangle', label: t('procurement.nav.disputes') },
        { to: '/market/buyer/ideal-list', icon: 'i-heroicons-heart', label: t('procurement.nav.idealList') },
        { to: '/portal/tickets', icon: 'i-heroicons-lifebuoy', label: t('procurement.nav.afterSales') },
        { to: '/portal/insights', icon: 'i-heroicons-chart-bar', label: t('procurement.nav.insights') },
      ],
    },
    { key: 'account', label: t('procurement.menu.account'), items: account },
  ]
})

const NAV_BAR_SLOTS = 8
const activeNav = computed(() => (isSupplier.value ? supplierNav : cebuNav.value))
const primaryNav = computed(() => activeNav.value.slice(0, NAV_BAR_SLOTS))
const overflowNav = computed(() => activeNav.value.slice(NAV_BAR_SLOTS))

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
