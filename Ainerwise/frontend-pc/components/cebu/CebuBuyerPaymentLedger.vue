<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('wallet.eyebrow') }}</p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('wallet.title') }}</h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-400">{{ $t('wallet.subtitle') }}</p>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="load()">{{ loading ? $t('common.loading') : $t('wallet.refresh') }}</button>
    </div>

    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div v-for="card in summary" :key="card.label" class="pc-card">
        <p class="text-sm text-slate-400">{{ card.label }}</p>
        <p class="mt-2 text-2xl font-bold text-white">{{ card.value }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ card.hint }}</p>
      </div>
    </div>

    <div class="pc-card">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 class="text-lg font-medium text-white">{{ $t('wallet.ledgerTitle') }}</h3>
        <select v-model="kindFilter" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
          <option value="">{{ $t('wallet.allTypes') }}</option>
          <option v-for="k in kinds" :key="k" :value="k">{{ k }}</option>
        </select>
      </div>

      <p v-if="error" class="mb-3 text-sm text-red-300">{{ error }}</p>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-2 pr-4 font-medium">{{ $t('wallet.colDate') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('wallet.colType') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('wallet.colOrder') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('wallet.colAmount') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('common.status') }}</th>
              <th class="py-2 font-medium">{{ $t('wallet.colRef') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filtered" :key="item.id" class="border-b border-white/5">
              <td class="py-3 pr-4 text-xs text-slate-500">{{ formatDate(item.created_at) }}</td>
              <td class="py-3 pr-4 text-white">{{ item.kind || item.type || '—' }}</td>
              <td class="py-3 pr-4">
                <NuxtLink v-if="item.order_id" :to="localized(`/market/buyer/orders/${item.order_id}`)" class="text-indigo-300 hover:text-indigo-200">{{ item.order_id.slice(0, 8) }}</NuxtLink>
                <span v-else class="text-slate-500">—</span>
              </td>
              <td :class="['py-3 pr-4 font-semibold', isOutflow(item) ? 'text-amber-300' : 'text-emerald-300']">
                {{ isOutflow(item) ? '-' : '+' }}{{ money(Math.abs(item.amount_minor || 0), item.currency) }}
              </td>
              <td class="py-3 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(item.status)]">{{ item.status || '—' }}</span></td>
              <td class="py-3 text-xs text-slate-500">{{ item.external_ref || '—' }}</td>
            </tr>
            <tr v-if="!loading && !filtered.length">
              <td colspan="6" class="py-8 text-center text-slate-500">{{ $t('wallet.empty') }}</td>
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
const { formatDate } = useLocaleFormat()
const { listPaymentLedger } = useCommerce()
const items = ref<any[]>([])
const error = ref('')
const loading = ref(false)
const kindFilter = ref('')

const kinds = computed(() => Array.from(new Set(items.value.map(i => i.kind || i.type).filter(Boolean))))
const filtered = computed(() => (kindFilter.value ? items.value.filter(i => (i.kind || i.type) === kindFilter.value) : items.value))

const summary = computed(() => {
  const currency = items.value[0]?.currency || 'EUR'
  const inflow = items.value.filter(i => !isOutflow(i)).reduce((s, i) => s + Math.abs(i.amount_minor || 0), 0)
  const outflow = items.value.filter(isOutflow).reduce((s, i) => s + Math.abs(i.amount_minor || 0), 0)
  const settled = items.value.filter(i => /paid|settled|complete|released/i.test(String(i.status || ''))).length
  return [
    { label: t('wallet.sumEntries'), value: items.value.length, hint: t('wallet.sumEntriesHint') },
    { label: t('wallet.sumInflow'), value: money(inflow, currency), hint: t('wallet.sumInflowHint') },
    { label: t('wallet.sumOutflow'), value: money(outflow, currency), hint: t('wallet.sumOutflowHint') },
    { label: t('wallet.sumSettled'), value: settled, hint: t('wallet.sumSettledHint', { n: items.value.length }) },
  ]
})

function isOutflow(item: any) {
  if (typeof item.amount_minor === 'number' && item.amount_minor < 0) return true
  return /payout|payment|charge|fee|debit|withdraw/i.test(String(item.kind || item.type || ''))
}

function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (/paid|settled|complete|released|success/.test(v)) return 'bg-emerald-500/15 text-emerald-300'
  if (/pending|processing|hold/.test(v)) return 'bg-amber-500/15 text-amber-300'
  if (/fail|refund|reversed|cancel/.test(v)) return 'bg-red-500/15 text-red-300'
  return 'bg-white/10 text-slate-300'
}

function money(minor: number, currency = 'EUR') {
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 2 }).format((minor || 0) / 100)
  } catch {
    return `${((minor || 0) / 100).toLocaleString()} ${currency}`
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listPaymentLedger()).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('wallet.loadFailed')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
