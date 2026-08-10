<template>
  <aside class="ws-rail" :class="{ 'ws-rail--collapsed': collapsed }" :aria-label="$t('rail.label')">
    <!-- Primary action stays pinned at the top, the way the 4106 rail does it. -->
    <NuxtLink to="/market/post-request" class="ws-rail__cta" :title="collapsed ? $t('rail.newRequest') : undefined">
      <AppIcon name="i-heroicons-plus-circle" class="h-5 w-5 shrink-0" />
      <span v-if="!collapsed" class="truncate">{{ $t('rail.newRequest') }}</span>
    </NuxtLink>

    <nav class="ws-rail__scroll">
      <div v-for="group in groups" :key="group.key" class="ws-rail__group">
        <!-- Collapsible sections: nineteen destinations is a long scroll, so
             each group folds and the open set is remembered. -->
        <button
          v-if="!collapsed"
          type="button"
          class="ws-rail__group-btn"
          :aria-expanded="isOpen(group.key)"
          @click="toggleGroup(group.key)"
        >
          <span>{{ group.label }}</span>
          <AppIcon
            name="i-heroicons-chevron-down"
            class="ws-rail__caret h-3.5 w-3.5"
            :class="{ 'ws-rail__caret--open': isOpen(group.key) }"
          />
        </button>
        <div v-else class="ws-rail__group-rule"></div>

        <!-- grid-template-rows 0fr -> 1fr animates to content height, which
             plain max-height cannot do without guessing a value. -->
        <div class="ws-rail__body" :class="{ 'ws-rail__body--open': collapsed || isOpen(group.key) }">
          <div class="ws-rail__body-inner">
            <NuxtLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              class="ws-rail__item"
              active-class="ws-rail__item--on"
              :title="collapsed ? item.label : undefined"
            >
              <AppIcon :name="item.icon" class="h-5 w-5 shrink-0" />
              <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
            </NuxtLink>
          </div>
        </div>
      </div>
    </nav>

    <button
      type="button"
      class="ws-rail__toggle"
      :aria-expanded="!collapsed"
      :title="collapsed ? $t('rail.expand') : $t('rail.collapse')"
      @click="toggle"
    >
      <AppIcon
        :name="collapsed ? 'i-heroicons-chevron-double-right' : 'i-heroicons-chevron-double-left'"
        class="h-4 w-4 shrink-0"
      />
      <span v-if="!collapsed" class="truncate">{{ $t('rail.collapse') }}</span>
    </button>
  </aside>
</template>

<script setup lang="ts">
const props = defineProps<{ isBusiness?: boolean }>()

const { t } = useI18n()

// Remembered across navigations and reloads, so the rail stays how the user
// left it rather than re-expanding on every page.
const collapsed = useCookie<boolean>('aislos_rail_collapsed', {
  default: () => false,
  sameSite: 'lax',
  maxAge: 60 * 60 * 24 * 365,
})
function toggle() {
  collapsed.value = !collapsed.value
}

// Accordion: opening a section folds the others, so the rail never grows past
// one screen no matter how many destinations a section holds.
const openGroup = useCookie<string>('aislos_rail_group', {
  default: () => 'journey',
  sameSite: 'lax',
  maxAge: 60 * 60 * 24 * 365,
})
function isOpen(key: string) {
  return openGroup.value === key
}
function toggleGroup(key: string) {
  // Accordion with no empty state: clicking the open section keeps it open, so
  // the fixed-height card always has content instead of a blank panel.
  if (isOpen(key)) return
  openGroup.value = key
}

// Mirrors the journey order in the top bar, then the same work/account split
// the account menu uses — one vocabulary in both places.
const groups = computed(() => {
  const account = [
    { to: '/market/buyer/settings', icon: 'i-heroicons-cog-8-tooth', label: t('procurement.nav.settings') },
    { to: '/market/buyer/wallet', icon: 'i-heroicons-wallet', label: t('procurement.nav.wallet') },
    { to: '/market/buyer/notifications', icon: 'i-heroicons-bell-alert', label: t('procurement.nav.notifications') },
  ]
  if (props.isBusiness) {
    account.push(
      { to: '/market/buyer/company-profile', icon: 'i-heroicons-building-office', label: t('procurement.nav.companyProfile') },
      { to: '/market/buyer/team', icon: 'i-heroicons-users', label: t('procurement.nav.team') },
    )
  }
  return [
    {
      key: 'journey',
      label: t('rail.journey'),
      items: [
        { to: '/market/buyer/dashboard', icon: 'i-heroicons-home', label: t('procurement.nav.workspace') },
        { to: '/market/buyer/requests', icon: 'i-heroicons-clipboard-document-list', label: t('procurement.nav.requests') },
        { to: '/market/buyer/projects', icon: 'i-heroicons-cpu-chip', label: t('procurement.nav.projects') },
        { to: '/market/buyer/orders', icon: 'i-heroicons-shopping-cart', label: t('procurement.nav.orders') },
        { to: '/portal/projects', icon: 'i-heroicons-truck', label: t('procurement.nav.delivery') },
        { to: '/portal/site-visits', icon: 'i-heroicons-calendar-days', label: t('procurement.nav.siteVisits') },
        { to: '/portal/installations', icon: 'i-heroicons-wrench-screwdriver', label: t('procurement.nav.installations') },
        { to: '/portal/assets', icon: 'i-heroicons-cube', label: t('procurement.nav.assets') },
      ],
    },
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
</script>

<style scoped>
/* A floating card pinned to the edge, matching the account menu and the
   dashboard cards, rather than a full-height column welded to the viewport. */
.ws-rail {
  position: sticky;
  top: 5.5rem;
  display: none;
  height: 34rem;
  max-height: calc(100vh - 7.5rem);
  width: 15rem;
  flex: none;
  flex-direction: column;
  gap: 0.75rem;
  margin: 1rem 0 1rem 1rem;
  border: 1px solid var(--card-border);
  border-radius: 1.25rem;
  background: var(--card-bg);
  padding: 0.9rem 0.7rem 0.7rem;
  backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(2, 6, 23, 0.10), 0 2px 8px rgba(2, 6, 23, 0.04);
  transition: width 0.18s ease;
}
.dark .ws-rail {
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.04) inset;
}
@media (min-width: 1024px) {
  .ws-rail { display: flex; }
}
.ws-rail--collapsed { width: 4.5rem; }

.ws-rail__cta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  border-radius: 0.75rem;
  background: var(--accent);
  padding: 0.65rem 0.8rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--accent-contrast);
  transition: filter 0.16s ease;
}
.ws-rail__cta:hover { filter: brightness(1.08); }

.ws-rail__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-content: start;
  gap: 0.5rem;
  /* A thin scrollbar keeps the rail from jumping width when it overflows. */
  scrollbar-width: thin;
}

.ws-rail__body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.26s cubic-bezier(0.4, 0, 0.2, 1);
}
.ws-rail__body--open { grid-template-rows: 1fr; }
.ws-rail__body-inner {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
@media (prefers-reduced-motion: reduce) {
  .ws-rail__body { transition: none; }
}
.ws-rail__group { display: flex; flex-direction: column; gap: 0.15rem; }
.ws-rail__group-btn {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-radius: 0.5rem;
  padding: 0.3rem 0.7rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-faint);
  transition: color 0.14s ease, background 0.14s ease;
}
.ws-rail__group-btn:hover { background: var(--surface-soft); color: var(--text-muted); }
.ws-rail__caret { transition: transform 0.26s cubic-bezier(0.4, 0, 0.2, 1); }
.ws-rail__caret--open { transform: rotate(180deg); }
.ws-rail__group-rule {
  margin: 0.3rem 0.6rem;
  height: 1px;
  background: var(--hairline-soft);
}

.ws-rail__item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  border-radius: 0.7rem;
  padding: 0.55rem 0.7rem;
  font-size: 0.86rem;
  color: var(--text-muted);
  transition: background 0.14s ease, color 0.14s ease;
}
.ws-rail--collapsed .ws-rail__item,
.ws-rail--collapsed .ws-rail__cta,
.ws-rail--collapsed .ws-rail__toggle { justify-content: center; padding-inline: 0.5rem; }
.ws-rail__item:hover { background: var(--surface-soft); color: var(--page-text); }
.ws-rail__item--on {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.ws-rail__toggle {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  border-top: 1px solid var(--hairline-soft);
  padding: 0.7rem;
  font-size: 0.78rem;
  color: var(--text-faint);
  transition: color 0.14s ease;
}
.ws-rail__toggle:hover { color: var(--accent); }
</style>
