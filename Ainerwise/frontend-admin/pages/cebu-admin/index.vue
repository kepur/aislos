<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">Cebu Administration</h1>
      <p class="admin-page-desc">Zero-loss operations dashboard backed by AinerWise Core</p>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-4 md:grid-cols-3">
      <article v-for="(value, key) in stats" :key="key" class="admin-panel p-5">
        <p class="text-xs uppercase tracking-wider text-slate-400">{{ String(key).replaceAll('_', ' ') }}</p>
        <p class="mt-2 text-3xl font-bold text-white">{{ value }}</p>
      </article>
    </div>
    <div class="grid gap-3 md:grid-cols-4">
      <NuxtLink v-for="link in links" :key="link.to" :to="link.to" class="admin-panel p-4 font-semibold text-cyan-300 hover:border-cyan-400/40">
        {{ link.label }}
      </NuxtLink>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const stats = ref<Record<string, number>>({})
const error = ref('')
const links = [
  { to: '/cebu-admin/migrations', label: 'Historical Migration' },
  { to: '/cebu-admin/users', label: 'Users & Staff' }, { to: '/cebu-admin/companies', label: 'Companies & KYC' },
  { to: '/cebu-admin/intents', label: 'Procurement Intents' }, { to: '/cebu-admin/offers', label: 'Offers' },
  { to: '/cebu-admin/orders', label: 'Orders' }, { to: '/cebu-admin/disputes', label: 'Disputes' },
  { to: '/cebu-admin/risk', label: 'Risk' }, { to: '/cebu-admin/trade', label: 'Trade Operations' },
  { to: '/cebu-admin/audit', label: 'Audit' },
]
onMounted(async () => {
  try { stats.value = (await apiFetch<any>('/admin/cebu/dashboard')).stats }
  catch (e: any) { error.value = e?.data?.detail || e?.message || 'Load failed' }
})
</script>
