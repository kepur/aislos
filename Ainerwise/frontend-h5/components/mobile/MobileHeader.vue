<template>
  <header class="mobile-header">
    <NuxtLink :key="`${activePortalKey}:${homePath}`" :to="homePath" class="flex min-w-0 flex-1 items-center gap-2">
      <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600">
        <span class="text-white font-black text-xs">A</span>
      </div>
      <span class="truncate text-base font-bold text-slate-800">{{ portalName }}</span>
    </NuxtLink>

    <div class="flex items-center gap-2">
      <PortalSwitcher />
      <LanguageSwitcher class="h5-lang" />
      <NuxtLink
        v-if="!isLoggedIn"
        to="/login"
        class="text-xs font-semibold text-white bg-blue-500 px-3 py-1.5 rounded-full hover:bg-blue-600 transition"
      >
        {{ $t('auth.login') }}
      </NuxtLink>
      <NuxtLink
        v-else
        to="/profile"
        class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center"
      >
        <span class="text-xs font-bold text-white">{{ userInitial }}</span>
      </NuxtLink>
    </div>
  </header>
</template>

<script setup lang="ts">
const { user, isLoggedIn } = useAuth()
const { portal } = usePortalMode()
const { manifest } = usePortalManifest()
const activePortalKey = computed(() => manifest.value?.portal_key || portal.shortName)
const headerNames: Record<string, string> = {
  consumer_h5: 'AinerWise',
  customer_h5: 'AinerWise',
  customer: 'AinerWise',
  cebu_buyer_h5: 'Market',
  cebu_buyer: 'Market',
  supplier_h5: 'Supplier',
  supplier: 'Supplier',
  partner_company_h5: 'Partner',
  partner_company: 'Partner',
  marketing_h5: 'Marketing',
  field_worker_h5: 'Field',
  crew_lead_h5: 'Crew',
  kiosk_h5: 'Kiosk',
}
const portalName = computed(() => {
  const key = activePortalKey.value
  if (headerNames[key]) return headerNames[key]
  const raw = manifest.value?.display_name || portal.shortName || 'AinerWise'
  return raw
    .replace(/\s+(Consumer Mobile|Workspace H5|Buyer H5|PWA)$/i, '')
    .replace(/^Customer\s+/i, '')
})
const homePath = computed(() => manifest.value?.home_route || portal.home)

const userInitial = computed(() => {
  const name = user.value?.full_name || user.value?.email || 'U'
  return name.charAt(0).toUpperCase()
})
</script>

<style scoped>
.mobile-header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

:deep(.h5-lang select) {
  background: rgba(241,245,249,0.8) !important;
  border-color: rgba(203,213,225,0.5) !important;
  color: #475569 !important;
  font-size: 11px !important;
  padding: 2px 6px !important;
  border-radius: 6px !important;
}
:deep(.h5-lang select option) {
  background: white !important;
  color: #1e293b !important;
}
</style>
