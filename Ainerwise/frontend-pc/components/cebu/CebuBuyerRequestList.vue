<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Buyer</p>
        <h1 class="mt-1 text-2xl font-bold text-white">我的采购需求</h1>
      </div>
      <NuxtLink to="/market/post-request" class="btn-primary">+ 发布采购需求</NuxtLink>
    </div>

    <div class="pc-card">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model.trim="keyword" class="input-field max-w-xs" placeholder="搜索需求标题…" />
        <select v-model="statusFilter" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
          <option value="">全部状态</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
        </select>
      </div>

      <p v-if="error" class="mb-3 text-sm text-red-300">{{ error }}</p>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[820px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-2 pr-4 font-medium">ID</th>
              <th class="py-2 pr-4 font-medium">需求标题</th>
              <th class="py-2 pr-4 font-medium">预算</th>
              <th class="py-2 pr-4 font-medium">发布日期</th>
              <th class="py-2 pr-4 font-medium">状态</th>
              <th class="py-2 pr-4 font-medium">报价</th>
              <th class="py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in paged" :key="r.id" class="border-b border-white/5">
              <td class="py-3 pr-4 font-mono text-xs text-slate-400">{{ r.id.slice(0, 8) }}</td>
              <td class="py-3 pr-4 text-white">{{ r.title || '未命名需求' }}</td>
              <td class="py-3 pr-4 text-slate-300">{{ budgetLabel(r) }}</td>
              <td class="py-3 pr-4 text-xs text-slate-500">{{ r.created_at ? new Date(r.created_at).toLocaleDateString() : '—' }}</td>
              <td class="py-3 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(r.status)]">{{ statusLabel(r.status) }}</span></td>
              <td class="py-3 pr-4 font-medium text-indigo-300">{{ offerCount(r) }}</td>
              <td class="py-3">
                <div class="flex gap-3">
                  <NuxtLink :to="`/market/buyer/requests/${r.id}`" class="text-xs text-slate-300 hover:text-white">查看</NuxtLink>
                  <NuxtLink v-if="offerCount(r) > 0" :to="`/market/buyer/requests/${r.id}/offers`" class="text-xs text-indigo-300 hover:text-indigo-200">对比报价</NuxtLink>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filtered.length">
              <td colspan="7" class="py-8 text-center text-slate-500">还没有采购需求，<NuxtLink to="/market/post-request" class="text-indigo-300">去发布</NuxtLink></td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-4 text-sm text-slate-500">共 {{ filtered.length }} 条需求</p>
      <WorkspacePagination v-model:page="page" :page-size="pageSize" :total="filtered.length" />

    </div>
  </section>
</template>

<script setup lang="ts">

const { listProcurementRequests } = useCommerce()
const items = ref<any[]>([])
const error = ref('')
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')
const statuses = ['draft', 'published', 'closed', 'awarded', 'cancelled']

const filtered = computed(() => {
  const kw = keyword.value.toLowerCase()
  return items.value.filter((r) => {
    if (statusFilter.value && String(r.status || '').toLowerCase() !== statusFilter.value) return false
    if (kw && !String(r.title || '').toLowerCase().includes(kw)) return false
    return true
  })
})

// Client-side paging: these lists already hold the full filtered set, so the
// pager slices it rather than adding a round trip per page.
const page = ref(1)
const pageSize = 20
const paged = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch(() => filtered.value.length, () => { page.value = 1 })


function offerCount(r: any) {
  return r.offer_count ?? r.offers_count ?? r.offers ?? 0
}

function pickNumber(...values: any[]) {
  for (const v of values) {
    if (v === null || v === undefined || v === '') continue
    const n = Number(v)
    if (Number.isFinite(n)) return n
  }
  return null
}

function budgetLabel(r: any) {
  const req = r.requirements_json || {}
  const attrs = r.attrs_json || {}
  const min = pickNumber(req.budget_min_minor, attrs.budget_min_minor, r.budget_min_minor)
  const max = pickNumber(req.budget_max_minor, attrs.budget_max_minor, r.budget_max_minor)
  const currency = req.currency || attrs.currency || r.currency || 'EUR'
  if (min != null && max != null) return `${fmt(min, currency)} - ${fmt(max, currency)}`
  if (max != null) return `≤ ${fmt(max, currency)}`
  if (min != null) return `≥ ${fmt(min, currency)}`
  return 'Open'
}

function fmt(minor: number, currency = 'EUR') {
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(minor / 100)
  } catch {
    return `${(minor / 100).toLocaleString()} ${currency}`
  }
}

function statusLabel(s?: string) {
  return {
    draft: '草稿',
    published: '招标中',
    closed: '已关闭',
    awarded: '已授标',
    cancelled: '已取消',
  }[String(s || '').toLowerCase()] || s || '—'
}

function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (v.includes('award') || v.includes('complete')) return 'bg-emerald-500/15 text-emerald-300'
  if (v.includes('publish') || v.includes('receiv') || v.includes('open')) return 'bg-blue-500/15 text-blue-300'
  if (v.includes('draft') || v.includes('review')) return 'bg-amber-500/15 text-amber-300'
  if (v.includes('cancel') || v.includes('closed')) return 'bg-white/10 text-slate-400'
  return 'bg-white/10 text-slate-300'
}

onMounted(async () => {
  loading.value = true
  try {
    items.value = (await listProcurementRequests()).items.filter((item: any) => item.portal_key === 'cebu')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载需求失败'
  } finally {
    loading.value = false
  }
})
</script>
