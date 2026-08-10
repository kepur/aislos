<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Commerce</p>
        <h1 class="mt-1 text-2xl font-bold text-white">订单与交付</h1>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="load()">{{ loading ? '加载中…' : '刷新' }}</button>
    </div>

    <div class="pc-card">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input
          v-model.trim="keyword"
          class="input-field max-w-xs"
          placeholder="按订单号 / 供应商搜索…"
        />
        <select v-model="status" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60" @change="load()">
          <option value="">全部状态</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
        </select>
      </div>

      <p v-if="error" class="mb-3 text-sm text-red-300">{{ error }}</p>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-2 pr-4 font-medium">订单号</th>
              <th class="py-2 pr-4 font-medium">供应商</th>
              <th class="py-2 pr-4 font-medium">托管总额</th>
              <th class="py-2 pr-4 font-medium">状态</th>
              <th class="py-2 pr-4 font-medium">日期</th>
              <th class="py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in paged" :key="o.id" class="border-b border-white/5">
              <td class="py-3 pr-4 font-mono text-xs text-slate-400">#{{ o.id.slice(0, 8) }}</td>
              <td class="py-3 pr-4 text-white">{{ o.supplier_company_name || o.supplier_name || '—' }}</td>
              <td class="py-3 pr-4 font-semibold text-white">{{ formatMinor(totalMinor(o), o.currency) }}</td>
              <td class="py-3 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(o.status)]">{{ statusLabel(o.status) }}</span></td>
              <td class="py-3 pr-4 text-xs text-slate-500">{{ o.created_at ? new Date(o.created_at).toLocaleDateString() : '—' }}</td>
              <td class="py-3"><NuxtLink :to="localized(`/market/buyer/orders/${o.id}`)" class="text-xs text-indigo-300 hover:text-indigo-200">查看详情</NuxtLink></td>
            </tr>
            <tr v-if="!loading && !filtered.length">
              <td colspan="6" class="py-8 text-center text-slate-500">该状态下暂无订单</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-4 text-sm text-slate-500">共 {{ filtered.length }} 笔订单</p>
    </div>
      <WorkspacePagination v-model:page="page" :page-size="pageSize" :total="filtered.length" />

  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()

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
    String(o.supplier_company_name || o.supplier_name || '').toLowerCase().includes(kw),
  )
})

// Client-side paging: these lists already hold the full filtered set, so the
// pager slices it rather than adding a round trip per page.
const page = ref(1)
const pageSize = 20
const paged = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch(() => filtered.value.length, () => { page.value = 1 })


function totalMinor(o: any) {
  return o.total_minor ?? o.total_amount_minor ?? 0
}

function statusLabel(s?: string) {
  return {
    confirmed: '已确认',
    in_delivery: '配送中',
    delivered: '已送达',
    completed: '已完成',
    disputed: '争议中',
    cancelled: '已取消',
  }[String(s || '')] || s || '—'
}

function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (v.includes('complete') || v.includes('deliver') || v.includes('accept')) return 'bg-emerald-500/15 text-emerald-300'
  if (v.includes('dispute') || v.includes('cancel')) return 'bg-red-500/15 text-red-300'
  if (v.includes('progress') || v.includes('delivery') || v.includes('confirm')) return 'bg-blue-500/15 text-blue-300'
  return 'bg-white/10 text-slate-300'
}

function formatMinor(minor?: number, currency = 'EUR') {
  if (minor == null) return '—'
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(minor / 100)
  } catch {
    return `${(minor / 100).toLocaleString()} ${currency}`
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listOrders(status.value || undefined)).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载订单失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
