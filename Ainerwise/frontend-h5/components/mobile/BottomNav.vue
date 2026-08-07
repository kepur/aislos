<template>
  <nav class="bottom-nav safe-bottom">
    <NuxtLink
      v-for="tab in tabs"
      :key="`${activePortalKey}:${tab.to}`"
      :to="tab.to"
      :class="['bottom-nav-item', { 'is-center': tab.center }]"
      :active-class="tab.center ? '' : 'active'"
    >
      <div v-if="tab.center" class="center-btn" :class="{ 'active': isActive(tab.to) }">
        <component :is="tab.icon || IconProducts" class="h-6 w-6" />
      </div>
      <template v-else>
        <component :is="tab.icon" class="w-5 h-5" />
        <span class="text-[10px] mt-0.5">{{ tab.label }}</span>
      </template>
      <span v-if="tab.center" class="mt-1 text-[10px]">{{ tab.centerLabel || tab.label }}</span>
    </NuxtLink>
  </nav>
</template>

<script setup lang="ts">
import { h } from 'vue'

const route = useRoute()
const { t } = useI18n({ useScope: 'global' })
const { mode } = usePortalMode()
const { manifest } = usePortalManifest()
const publicConfig = useRuntimeConfig().public
const activePortalKey = computed(() => manifest.value?.portal_key || (mode === 'partner' ? 'partner_company' : mode))
const marketH5Url = computed(() => String(publicConfig.marketH5Url || 'http://localhost:4107'))

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

// Icon components as render functions
const IconHome = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'm2.25 12 8.954-8.955a1.126 1.126 0 0 1 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25' })
])

const IconSolutions = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z' })
])

const IconProjects = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z' })
])

const IconProducts = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 10.104A2.25 2.25 0 0 1 18.637 21H5.363a2.25 2.25 0 0 1-2.232-2.389L4.394 8.507A2.25 2.25 0 0 1 6.626 6.5h10.748a2.25 2.25 0 0 1 2.232 2.007Z' })
])

const IconSecondhand = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M16.5 9.75h1.875A2.625 2.625 0 0 1 21 12.375v0A2.625 2.625 0 0 1 18.375 15H7.5m0 0 3-3m-3 3 3 3M7.5 14.25H5.625A2.625 2.625 0 0 1 3 11.625v0A2.625 2.625 0 0 1 5.625 9H16.5m0 0-3-3m3 3-3 3' })
])

const IconProfile = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z' })
])

const IconDashboard = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z' })
])

const IconCalendar = () => h('svg', { class: 'w-5 h-5', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M6.75 3v2.25M17.25 3v2.25M3.75 8.25h16.5M5.25 4.5h13.5A1.5 1.5 0 0 1 20.25 6v13.5H3.75V6a1.5 1.5 0 0 1 1.5-1.5Z' })
])

const tabs = computed(() => {
  if (['field_worker', 'field_worker_h5'].includes(activePortalKey.value)) {
    return [
      { to: '/field/today', label: 'Today', icon: IconDashboard },
      { to: '/profile', label: t('nav.profile'), icon: IconProfile },
    ]
  }
  if (activePortalKey.value === 'crew_lead_h5') {
    return [
      { to: '/crew', label: 'Overview', icon: IconDashboard },
      { to: '/crew/tasks', label: 'Crew tasks', icon: IconProjects },
      { to: '/crew/members', label: 'Members', icon: IconProfile },
    ]
  }
  if (['supplier', 'supplier_h5'].includes(activePortalKey.value)) {
    return [
      { to: '/supplier', label: 'Supplier', icon: IconDashboard },
      { to: '/supplier/pings', label: 'Pings', icon: IconSolutions },
      { to: '/supplier/catalog', label: 'Catalog', center: true },
      { to: '/supplier/offers', label: 'Offers', icon: IconProjects },
      { to: '/supplier/orders', label: 'Orders', icon: IconProjects },
    ]
  }
  if (['partner_company', 'partner_company_h5'].includes(activePortalKey.value)) {
    return [
      { to: '/partner', label: t('partner.work'), icon: IconDashboard },
      { to: '/partner/rfqs', label: t('partner.requests'), icon: IconProjects },
      { to: '/partner/work-packages', label: 'Delivery', icon: IconSolutions },
      { to: '/partner/crews', label: 'Crews', icon: IconProfile },
      { to: '/partner/calendar', label: t('partner.calendar'), icon: IconCalendar },
    ]
  }
  if (['cebu_buyer', 'cebu_buyer_h5'].includes(activePortalKey.value)) {
    return [
      { to: '/marketplace', label: t('nav.market'), icon: IconProducts },
      { to: '/secondhand', label: '2Hands', icon: IconSecondhand },
      { to: '/buyer/post-request', label: t('nav.submitRequirement'), centerLabel: 'Post', center: true },
      { to: '/buyer/orders', label: 'Orders', icon: IconSolutions },
      { to: '/buyer', label: 'Me', icon: IconProfile },
    ]
  }
  if (activePortalKey.value === 'marketing_h5') {
    return [
      { to: '/marketing-mobile', label: 'Overview', icon: IconDashboard },
      { to: '/marketing-mobile/briefs', label: 'Briefs', icon: IconProjects },
      { to: '/marketing-mobile/review', label: 'Review', icon: IconSolutions },
      { to: '/marketing-mobile/assets', label: 'Assets', icon: IconProfile },
      { to: '/marketing-mobile/schedule', label: 'Schedule', icon: IconCalendar },
    ]
  }
  if (['customer', 'customer_h5'].includes(activePortalKey.value)) {
    return [
      { to: '/dashboard', label: 'Overview', icon: IconDashboard },
      { to: '/projects', label: 'Projects', icon: IconProjects },
      { to: '/products', label: t('nav.products'), centerLabel: t('nav.products'), center: true, icon: IconProducts },
      { to: '/customer/installations', label: 'Install', icon: IconCalendar },
      { to: '/customer/assets', label: 'Assets', icon: IconProfile },
    ]
  }
  return [
    { to: '/', label: t('nav.home'), icon: IconHome },
    { to: '/solutions', label: t('nav.solutions'), icon: IconSolutions },
    { to: '/products', label: t('nav.products'), centerLabel: t('nav.products'), center: true, icon: IconProducts },
    { to: marketH5Url.value, label: t('nav.market'), icon: IconProducts },
    { to: '/profile', label: t('nav.profile'), icon: IconProfile },
  ]
})
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 56px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.04);
}

.bottom-nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
  text-decoration: none;
  transition: color 0.2s;
  -webkit-tap-highlight-color: transparent;
  position: relative;
}

.bottom-nav-item.active {
  color: #3b82f6;
}

.bottom-nav-item.is-center {
  color: #3b82f6;
}

.center-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-top: -18px;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35);
  transition: transform 0.2s, box-shadow 0.2s;
}

.center-btn.active {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.5);
}

.bottom-nav-item.is-center:active .center-btn {
  transform: scale(0.95);
}
</style>
