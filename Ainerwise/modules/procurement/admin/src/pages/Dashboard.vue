<template>
  <div class="space-y-6">
    <!-- Stat cards -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
      <div v-for="s in stats" :key="s.label" class="card p-5">
        <p class="text-xs text-slate-500 font-medium mb-1">{{ s.label }}</p>
        <p class="text-2xl font-extrabold" :class="s.color || 'text-slate-900'">{{ s.value }}</p>
      </div>
    </div>

    <div class="grid lg:grid-cols-2 gap-6">
      <!-- Recent audit -->
      <div class="card overflow-hidden">
        <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 class="font-semibold text-slate-900">{{ t('dashboard.recentAudit') }}</h3>
          <router-link to="/audit" class="text-xs text-primary-600 font-medium hover:underline">{{ t('common.view') }} →</router-link>
        </div>
        <div class="divide-y divide-slate-50">
          <div v-for="log in recentLogs" :key="log.id" class="px-5 py-3 flex items-start gap-3">
            <span class="text-sm mt-0.5 flex-shrink-0">{{ riskIcon(log.risk_level) }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-800 truncate">{{ log.action.replace(/_/g, ' ') }}</p>
              <p class="text-xs text-slate-400">{{ log.entity_type }} · {{ fmtRelative(log.created_at) }}</p>
            </div>
          </div>
          <div v-if="!recentLogs.length" class="px-5 py-8 text-center text-slate-400 text-sm">{{ t('common.noData') }}</div>
        </div>
      </div>

      <!-- Quick links -->
      <div class="card overflow-hidden">
        <div class="px-5 py-4 border-b border-slate-100">
          <h3 class="font-semibold text-slate-900">{{ t('dashboard.quickActions') }}</h3>
        </div>
        <div class="p-4 grid grid-cols-2 gap-3">
          <router-link v-for="a in quickActions" :key="a.to" :to="a.to"
            class="flex flex-col items-center gap-2 p-4 rounded-xl border border-slate-100 hover:border-primary-300 hover:bg-primary-50 transition-colors cursor-pointer"
          >
            <span class="text-2xl">{{ a.icon }}</span>
            <span class="text-xs font-medium text-slate-700">{{ a.label }}</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, fmtRelative, fmtPrice } from '@/utils/api'

const { t } = useI18n()
const dash = ref({})
const recentLogs = ref([])

const stats = computed(() => [
  { label: t('dashboard.totalUsers'),   value: dash.value.users_total ?? 0 },
  { label: t('users.role') + ': Buyer', value: dash.value.buyers_total ?? 0 },
  { label: t('users.role') + ': Supplier', value: dash.value.suppliers_total ?? 0 },
  { label: t('intents.title'),          value: dash.value.active_intents ?? 0 },
  { label: t('dashboard.escrowHeld'),   value: dash.value.orders_in_escrow ?? 0, color: 'text-amber-600' },
  { label: t('dashboard.openDisputes'), value: dash.value.open_disputes ?? 0, color: dash.value.open_disputes ? 'text-red-600' : 'text-slate-900' },
  { label: t('verification.title'),     value: dash.value.pending_company_verifications ?? 0, color: dash.value.pending_company_verifications ? 'text-amber-600' : 'text-slate-900' },
  { label: t('dashboard.escrowHeld'),   value: fmtPrice(dash.value.escrow_held_minor ?? 0) },
])

const quickActions = computed(() => [
  { to: '/users',     icon: '👥', label: t('nav.users') },
  { to: '/disputes',  icon: '⚠️',  label: t('nav.disputes') },
  { to: '/companies', icon: '🏢', label: t('nav.companies') },
  { to: '/settings',  icon: '⚙️',  label: t('nav.settings') },
])

function riskIcon(level) {
  return { CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '⚪' }[level] || '⚪'
}

onMounted(async () => {
  const [d, logs] = await Promise.all([
    api.get('/admin/dashboard').then(r => r.data),
    api.get('/admin/audit-logs?limit=10').then(r => r.data),
  ])
  dash.value = d
  recentLogs.value = logs
})
</script>
