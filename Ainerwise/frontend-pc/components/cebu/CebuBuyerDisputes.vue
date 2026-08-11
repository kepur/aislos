<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('disputes.eyebrow') }}</p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('disputes.title') }}</h1>
      </div>
      <NuxtLink :to="localized('/market/buyer/disputes/new')" class="btn-primary">{{ $t('disputes.new') }}</NuxtLink>
    </div>

    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div v-for="card in summary" :key="card.label" class="pc-card">
        <p class="text-sm text-slate-400">{{ card.label }}</p>
        <p class="mt-2 text-2xl font-bold text-white">{{ card.value }}</p>
      </div>
    </div>

    <div class="pc-card">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model.trim="keyword" class="input-field max-w-xs" :placeholder="$t('disputes.searchPh')" />
        <select v-model="statusFilter" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
          <option value="">{{ $t('disputes.allStatus') }}</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
        </select>
      </div>

      <p v-if="error" class="mb-3 text-sm text-red-300">{{ error }}</p>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[820px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-2 pr-4 font-medium">{{ $t('disputes.colId') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('disputes.colOrder') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('disputes.colReason') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('disputes.colDesc') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('common.status') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('disputes.colCreated') }}</th>
              <th class="py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in filtered" :key="d.id" class="border-b border-white/5">
              <td class="py-3 pr-4 font-mono text-xs text-slate-400">{{ d.id.slice(0, 8) }}</td>
              <td class="py-3 pr-4">
                <NuxtLink v-if="orderId(d)" :to="localized(`/market/buyer/orders/${orderId(d)}`)" class="text-indigo-300 hover:text-indigo-200">{{ orderId(d).slice(0, 8) }}</NuxtLink>
                <span v-else class="text-slate-500">—</span>
              </td>
              <td class="py-3 pr-4 text-white">{{ d.reason_code || '—' }}</td>
              <td class="py-3 pr-4 max-w-[280px] truncate text-slate-300">{{ d.description || '—' }}</td>
              <td class="py-3 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(d.status)]">{{ statusLabel(d.status) }}</span></td>
              <td class="py-3 pr-4 text-xs text-slate-500">{{ d.created_at ? new Date(d.created_at).toLocaleDateString() : '—' }}</td>
              <td class="py-3"><NuxtLink v-if="orderId(d)" :to="localized(`/market/buyer/orders/${orderId(d)}`)" class="text-xs text-indigo-300 hover:text-indigo-200">{{ $t('disputes.viewOrder') }}</NuxtLink></td>
            </tr>
            <tr v-if="!loading && !filtered.length">
              <td colspan="7" class="py-8 text-center text-slate-500">{{ $t('disputes.empty') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const { listDisputes } = useCommerce()
const items = ref<any[]>([])
const error = ref('')
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')
const statuses = ['open', 'under_review', 'resolved', 'closed']

const filtered = computed(() => {
  const kw = keyword.value.toLowerCase()
  return items.value.filter((d) => {
    if (statusFilter.value && String(d.status || '').toLowerCase() !== statusFilter.value) return false
    if (kw && !`${orderId(d)} ${d.reason_code || ''} ${d.description || ''}`.toLowerCase().includes(kw)) return false
    return true
  })
})

const summary = computed(() => [
  { label: t('disputes.sumAll'), value: items.value.length },
  { label: t('disputes.sumOpen'), value: items.value.filter(d => String(d.status).toLowerCase() === 'open').length },
  { label: t('disputes.sumReview'), value: items.value.filter(d => String(d.status).toLowerCase() === 'under_review').length },
  { label: t('disputes.sumResolved'), value: items.value.filter(d => /resolved|closed/i.test(String(d.status))).length },
])

function orderId(d: any) {
  return d.commerce_order_id || d.order_id || ''
}

function statusLabel(s?: string) {
  const key = { open: 'statusOpen', under_review: 'statusReview', resolved: 'statusResolved', closed: 'statusClosed' }[String(s || '').toLowerCase()]
  return key ? t(`disputes.${key}`) : (s || '—')
}

function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (/resolved|closed/.test(v)) return 'bg-emerald-500/15 text-emerald-300'
  if (/review/.test(v)) return 'bg-blue-500/15 text-blue-300'
  if (/open/.test(v)) return 'bg-amber-500/15 text-amber-300'
  return 'bg-white/10 text-slate-300'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listDisputes()).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('disputes.loadFailed')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
