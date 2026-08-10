<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Supplier</p>
        <h1 class="mt-1 text-2xl font-bold text-white">我的报价</h1>
      </div>
      <NuxtLink :to="localized('/supplier/offers/new')" class="btn-primary">+ 新报价</NuxtLink>
    </div>

    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div v-for="c in summary" :key="c.label" class="pc-card"><p class="text-sm text-slate-400">{{ c.label }}</p><p class="mt-1 text-2xl font-bold text-white">{{ c.value }}</p></div>
    </div>

    <div class="pc-card">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model.trim="keyword" class="input-field max-w-xs" placeholder="按需求 ID 搜索…" />
        <select v-model="statusFilter" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
          <option value="">全部状态</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
        </select>
      </div>

      <p v-if="error" class="mb-3 text-sm text-red-300">{{ error }}</p>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-2 pr-4 font-medium">报价金额</th>
              <th class="py-2 pr-4 font-medium">关联需求</th>
              <th class="py-2 pr-4 font-medium">状态</th>
              <th class="py-2 pr-4 font-medium">提交时间</th>
              <th class="py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in filtered" :key="o.id" class="border-b border-white/5">
              <td class="py-3 pr-4 font-semibold text-white">{{ money(o.total_price_minor ?? o.price_minor, o.currency) }}</td>
              <td class="py-3 pr-4 font-mono text-xs text-indigo-300">{{ String(o.procurement_request_id || '').slice(0, 8) || '—' }}</td>
              <td class="py-3 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(o.status)]">{{ statusLabel(o.status) }}</span></td>
              <td class="py-3 pr-4 text-xs text-slate-500">{{ o.created_at ? new Date(o.created_at).toLocaleDateString() : '—' }}</td>
              <td class="py-3 text-right">
                <button v-if="String(o.status).toLowerCase() === 'submitted'" class="text-xs text-red-300 hover:text-red-200" @click="withdraw(o.id)">撤回</button>
              </td>
            </tr>
            <tr v-if="!loading && !filtered.length">
              <td colspan="5" class="py-8 text-center text-slate-500">还没有报价，<NuxtLink :to="localized('/supplier/pings')" class="text-indigo-300">去匹配需求</NuxtLink></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const api = useCommerce()
const items = ref<any[]>([])
const error = ref('')
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')
const statuses = ['submitted', 'awarded', 'rejected', 'withdrawn']

const filtered = computed(() => {
  const kw = keyword.value.toLowerCase()
  return items.value.filter((o) => {
    if (statusFilter.value && String(o.status || '').toLowerCase() !== statusFilter.value) return false
    if (kw && !String(o.procurement_request_id || '').toLowerCase().includes(kw)) return false
    return true
  })
})
const summary = computed(() => [
  { label: '全部报价', value: items.value.length },
  { label: '待审', value: items.value.filter(o => String(o.status).toLowerCase() === 'submitted').length },
  { label: '已中标', value: items.value.filter(o => String(o.status).toLowerCase() === 'awarded').length },
  { label: '未中标', value: items.value.filter(o => /reject|withdraw/i.test(String(o.status))).length },
])

function statusLabel(s?: string) {
  return { submitted: '待审', awarded: '已中标', rejected: '未中标', withdrawn: '已撤回' }[String(s || '').toLowerCase()] || s || '—'
}
function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (/award/.test(v)) return 'bg-emerald-500/15 text-emerald-300'
  if (/submit/.test(v)) return 'bg-blue-500/15 text-blue-300'
  if (/reject|withdraw/.test(v)) return 'bg-white/10 text-slate-400'
  return 'bg-white/10 text-slate-300'
}
function money(v?: number, c = 'EUR') {
  if (v == null) return '—'
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(v / 100) } catch { return `${(v / 100).toLocaleString()} ${c}` }
}

async function load() {
  loading.value = true
  try { items.value = (await api.listSupplierOffers()).items || [] } catch (e: any) { error.value = e?.data?.detail || e?.message || '加载报价失败' } finally { loading.value = false }
}
async function withdraw(id: string) {
  try { await api.withdrawSupplierOffer(id); await load() } catch (e: any) { error.value = e?.data?.detail || e?.message || '撤回失败' }
}
onMounted(load)
</script>
