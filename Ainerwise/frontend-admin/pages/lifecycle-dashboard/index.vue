<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">{{ t('lc.ctTitle') }}</h1>
      <p class="admin-page-desc">{{ t('lc.ctDesc') }}</p>
    </div>

    <!-- ARR + headline stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl border p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wider">{{ t('lc.arrPipeline') }}</p>
        <p class="text-2xl font-bold text-gray-900 mt-1">{{ money(data.arr?.pipeline) }}</p>
      </div>
      <div class="bg-white rounded-xl border p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wider">{{ t('lc.arrContracted') }}</p>
        <p class="text-2xl font-bold text-emerald-600 mt-1">{{ money(data.arr?.contracted) }}</p>
      </div>
      <div class="bg-white rounded-xl border p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wider">{{ t('lc.highLtvLeads') }}</p>
        <p class="text-2xl font-bold text-gray-900 mt-1">{{ data.high_ltv_leads ?? 0 }}</p>
      </div>
      <div class="bg-white rounded-xl border p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wider">{{ t('lc.openTickets') }}</p>
        <p class="text-2xl font-bold text-gray-900 mt-1">{{ data.open_tickets ?? 0 }}</p>
      </div>
    </div>

    <!-- Due-date alerts -->
    <div>
      <h2 class="admin-section-title mb-3">{{ t('lc.dueAlerts') }}</h2>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div v-for="(count, key) in data.alerts || {}" :key="key"
          class="bg-white rounded-xl border p-4 text-center"
          :class="count > 0 ? 'border-amber-300' : ''">
          <p class="text-2xl font-bold" :class="count > 0 ? 'text-amber-600' : 'text-gray-300'">{{ count }}</p>
          <p class="text-[11px] text-gray-500 mt-1 capitalize">{{ String(key).replace(/_/g, ' ') }}</p>
        </div>
      </div>
    </div>

    <!-- Margin ranking -->
    <div>
      <h2 class="admin-section-title mb-3">{{ t('lc.marginRanking') }}</h2>
      <div class="bg-white rounded-xl border overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500">
            <tr>
              <th class="text-left font-medium px-4 py-2.5">{{ t('lc.solutionLine') }}</th>
              <th class="text-right font-medium px-4 py-2.5">{{ t('lc.contract') }}</th>
              <th class="text-right font-medium px-4 py-2.5">{{ t('lc.grossProfit') }}</th>
              <th class="text-right font-medium px-4 py-2.5">{{ t('lc.margin') }}</th>
              <th class="text-right font-medium px-4 py-2.5">{{ t('lc.ltv3') }}</th>
              <th class="text-right font-medium px-4 py-2.5">{{ t('lc.ltv5') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="row in data.margin_ranking || []" :key="row.id" class="hover:bg-gray-50">
              <td class="px-4 py-2.5 text-gray-700">{{ row.solution_line || '—' }}</td>
              <td class="px-4 py-2.5 text-right">{{ money(row.contract_total) }}</td>
              <td class="px-4 py-2.5 text-right">{{ money(row.gross_profit) }}</td>
              <td class="px-4 py-2.5 text-right font-semibold">{{ row.gross_margin_percent?.toFixed(1) }}%</td>
              <td class="px-4 py-2.5 text-right">{{ money(row.ltv_3_year) }}</td>
              <td class="px-4 py-2.5 text-right">{{ money(row.ltv_5_year) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!(data.margin_ranking || []).length" class="p-8 text-center text-gray-500">{{ t('lc.pfEmpty') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const { t } = useI18n({ useScope: 'global' })
const data = ref<any>({})
const money = (v: any) => (v == null ? '€0' : `€${Number(v).toLocaleString()}`)

onMounted(async () => {
  try {
    data.value = await apiFetch<any>('/admin/lifecycle-dashboard')
  } catch {
    data.value = {}
  }
})
</script>
