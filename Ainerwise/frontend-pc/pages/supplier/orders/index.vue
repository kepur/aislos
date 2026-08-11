<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('orders.eyebrow') }}</p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('orders.title') }}</h1>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="load()">{{ loading ? $t('common.loading') : $t('ui.refresh') }}</button>
    </div>

    <div class="pc-card">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model.trim="keyword" class="input-field max-w-xs" :placeholder="$t('sup.searchOrderBuyer')" />
        <select v-model="status" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60" @change="load()">
          <option value="">{{ $t('ui.allStatus') }}</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
        </select>
      </div>

      <p v-if="error" class="mb-3 text-sm text-red-300">{{ error }}</p>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-2 pr-4 font-medium">{{ $t('orders.colOrder') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('sup.colBuyer') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('sup.colAmount') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('common.status') }}</th>
              <th class="py-2 pr-4 font-medium">{{ $t('orders.colDate') }}</th>
              <th class="py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in filtered" :key="o.id" class="border-b border-white/5">
              <td class="py-3 pr-4 font-mono text-xs text-slate-400">#{{ o.id.slice(0, 8) }}</td>
              <td class="py-3 pr-4 text-white">{{ o.buyer_company_name || o.buyer_name || '—' }}</td>
              <td class="py-3 pr-4 font-semibold text-white">{{ money(o.total_minor ?? o.total_amount_minor, o.currency) }}</td>
              <td class="py-3 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(o.status)]">{{ statusLabel(o.status) }}</span></td>
              <td class="py-3 pr-4 text-xs text-slate-500">{{ formatDay(o.created_at) }}</td>
              <td class="py-3"><NuxtLink :to="localized(`/supplier/orders/${o.id}`)" class="text-xs text-indigo-300 hover:text-indigo-200">{{ $t('sup.manageDelivery') }}</NuxtLink></td>
            </tr>
            <tr v-if="!loading && !filtered.length">
              <td colspan="6" class="py-8 text-center text-slate-500">{{ $t('orders.empty') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-4 text-sm text-slate-500">{{ $t('orders.count', { n: filtered.length }) }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const { formatDay } = useLocaleFormat()
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const { listOrders } = useCommerce()
const items = ref<any[]>([])
const error = ref('')
const loading = ref(false)
const status = ref('')
const keyword = ref('')
const statuses = ['confirmed', 'in_delivery', 'delivered', 'completed', 'disputed', 'cancelled']

const filtered = computed(() => {
  const kw = keyword.value.toLowerCase()
  if (!kw) return items.value
  return items.value.filter(o =>
    String(o.id).toLowerCase().includes(kw) ||
    String(o.buyer_company_name || o.buyer_name || '').toLowerCase().includes(kw),
  )
})

function statusLabel(s?: string) {
  const known = ['confirmed', 'in_delivery', 'delivered', 'completed', 'disputed', 'cancelled']
  const key = String(s || '')
  return known.includes(key) ? t(`orderStatus.${key}`) : (s || '—')
}
function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (/complete|deliver|accept/.test(v)) return 'bg-emerald-500/15 text-emerald-300'
  if (/dispute|cancel/.test(v)) return 'bg-red-500/15 text-red-300'
  if (/progress|delivery|confirm/.test(v)) return 'bg-blue-500/15 text-blue-300'
  return 'bg-white/10 text-slate-300'
}
function money(minor?: number, currency = 'EUR') {
  if (minor == null) return '—'
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(minor / 100) } catch { return `${(minor / 100).toLocaleString()} ${currency}` }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listOrders(status.value || undefined)).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('orders.loadFailed')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
