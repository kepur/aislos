<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">{{ $t('admin.leads') }}</h1>
        <p class="text-sm text-slate-400 mt-1">{{ total }} total leads</p>
      </div>
    </div>

    <!-- FI.6.3 CRM filters + sort -->
    <div class="admin-card p-3 flex flex-wrap items-end gap-3">
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Solution Line</label>
        <select v-model="filters.solution_line" class="bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-slate-200">
          <option value="">All</option>
          <option v-for="l in solutionLines" :key="l" :value="l">{{ l }}</option>
        </select>
      </div>
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Min Recurring Score</label>
        <input v-model.number="filters.min_recurring_score" type="number" min="0" max="100" placeholder="0"
          class="w-24 bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-slate-200" />
      </div>
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Compliance Risk</label>
        <select v-model="filters.compliance_risk" class="bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-slate-200">
          <option value="">Any</option>
          <option value="high">high</option><option value="medium">medium</option><option value="low">low</option>
        </select>
      </div>
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">AMC Potential</label>
        <select v-model="filters.amc_potential" class="bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-slate-200">
          <option value="">Any</option>
          <option value="high">high</option><option value="medium">medium</option><option value="low">low</option>
        </select>
      </div>
      <label class="flex items-center gap-2 text-sm text-slate-300">
        <input v-model="filters.multi_site" type="checkbox" class="rounded" /> Multi-site
      </label>
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Sort</label>
        <select v-model="filters.sort" class="bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-slate-200">
          <option value="created_at">Newest</option>
          <option value="recurring_revenue_score">Recurring score</option>
          <option value="estimated_arr">Estimated ARR</option>
          <option value="estimated_ltv">Estimated LTV</option>
          <option value="lead_score">Lead score</option>
        </select>
      </div>
      <button @click="load" class="px-3 py-1.5 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">Apply</button>
    </div>

    <!-- Table -->
    <div class="admin-card p-0 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="admin-table w-full text-sm">
          <thead>
            <tr class="border-b border-white/5 bg-white/[0.02]">
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Contact</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Type</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Country</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Line</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">RR Score</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">ARR</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">{{ $t('common.status') }}</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in leads" :key="lead.id"
                class="border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-colors"
                @click="navigateTo(`leads/${lead.id}`)">
              <td class="px-4 py-3">
                <span class="text-slate-200 font-medium">{{ lead.contact_name || '-' }}</span>
                <span v-if="lead.contact_email" class="block text-xs text-slate-500">{{ lead.contact_email }}</span>
              </td>
              <td class="px-4 py-3 text-slate-400">{{ lead.project_type || '-' }}</td>
              <td class="px-4 py-3 text-slate-400">{{ lead.country || '-' }}</td>
              <td class="px-4 py-3 text-slate-400">{{ lead.solution_line || '-' }}</td>
              <td class="px-4 py-3">
                <span v-if="lead.recurring_revenue_score != null"
                  :class="['px-2 py-0.5 rounded-full text-xs font-semibold', scoreClass(lead.recurring_revenue_score)]">
                  {{ lead.recurring_revenue_score }}
                </span>
                <span v-else class="text-slate-600">-</span>
              </td>
              <td class="px-4 py-3 text-slate-400">{{ lead.estimated_arr ? '€' + Math.round(lead.estimated_arr).toLocaleString() : '-' }}</td>
              <td class="px-4 py-3"><StatusBadge :status="lead.status" /></td>
              <td class="px-4 py-3 text-slate-500 text-xs">{{ new Date(lead.created_at).toLocaleDateString() }}</td>
            </tr>
            <tr v-if="!leads.length">
              <td colspan="8" class="px-4 py-12 text-center text-slate-500">{{ $t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const leads = ref<any[]>([])
const total = ref(0)

const solutionLines = ['buildingbrain', 'energyguard', 'storageguard', 'aquaguard', 'kitchenguard', 'assetpulse', 'factorypulse', 'agribrain']

const filters = reactive({
  solution_line: '',
  min_recurring_score: null as number | null,
  compliance_risk: '',
  amc_potential: '',
  multi_site: false,
  sort: 'created_at',
})

function scoreClass(score: number) {
  if (score >= 70) return 'bg-emerald-500/15 text-emerald-400'
  if (score >= 40) return 'bg-amber-500/15 text-amber-400'
  return 'bg-slate-500/15 text-slate-400'
}

async function load() {
  const q = new URLSearchParams({ limit: '100', sort: filters.sort, order: 'desc' })
  if (filters.solution_line) q.set('solution_line', filters.solution_line)
  if (filters.min_recurring_score != null && filters.min_recurring_score !== ('' as any)) q.set('min_recurring_score', String(filters.min_recurring_score))
  if (filters.compliance_risk) q.set('compliance_risk', filters.compliance_risk)
  if (filters.amc_potential) q.set('amc_potential', filters.amc_potential)
  if (filters.multi_site) q.set('multi_site', 'true')
  try {
    const res = await apiFetch<any>(`/leads?${q.toString()}`)
    leads.value = res.items || res || []
    total.value = res.total ?? leads.value.length
  } catch {}
}

onMounted(load)
</script>
