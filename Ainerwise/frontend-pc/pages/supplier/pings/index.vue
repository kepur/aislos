<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Opportunities</p>
        <h1 class="mt-1 text-2xl font-bold text-white">匹配采购需求</h1>
        <p class="mt-1 text-sm text-slate-400">系统按你的目录与区域匹配到的买家需求，越快报价越有优势。</p>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="load()">{{ loading ? '加载中…' : '刷新' }}</button>
    </div>

    <div class="pc-card flex flex-wrap items-center gap-3">
      <input v-model.trim="keyword" class="input-field max-w-xs" placeholder="搜索需求标题…" />
      <span class="text-sm text-slate-500">共 {{ filtered.length }} 条匹配</span>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <div class="grid gap-4">
      <div v-for="p in filtered" :key="p.id" class="pc-card flex flex-wrap items-start justify-between gap-4 transition hover:border-indigo-400/40">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <h2 class="truncate font-semibold text-white">{{ p.title || '采购需求' }}</h2>
            <span v-if="p.pre_funded || p.is_pre_funded" class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">已预付</span>
            <span v-if="p.already_offered" class="rounded-full bg-blue-500/15 px-2 py-0.5 text-xs text-blue-300">已报价</span>
          </div>
          <p class="mt-1 line-clamp-2 text-sm text-slate-400">{{ p.description || '无描述' }}</p>
          <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
            <span>预算：{{ budgetOf(p) }}</span>
            <span>·</span>
            <span>{{ matchCount(p) }} 个匹配挂牌</span>
            <span>·</span>
            <span>{{ p.created_at ? timeAgo(p.created_at) : (p.status || '') }}</span>
          </div>
        </div>
        <NuxtLink :to="`/supplier/offers/new?request_id=${requestId(p)}`" class="btn-primary shrink-0">{{ p.already_offered ? '更新报价' : '立即报价' }}</NuxtLink>
      </div>
      <p v-if="!loading && !filtered.length" class="pc-card py-12 text-center text-sm text-slate-400">暂无匹配需求。完善 <NuxtLink to="/supplier/catalog" class="text-indigo-300">产品目录</NuxtLink> 可获得更多匹配。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const { listSupplierPings } = useCommerce()
const items = ref<any[]>([])
const error = ref('')
const loading = ref(false)
const keyword = ref('')

const filtered = computed(() => {
  const kw = keyword.value.toLowerCase()
  if (!kw) return items.value
  return items.value.filter(p => String(p.title || '').toLowerCase().includes(kw))
})

function requestId(p: any) {
  return p.procurement_request_id || p.request_id || p.id
}
function matchCount(p: any) {
  return (p.matching_listing_ids || p.matching_listings || []).length || 0
}
function budgetOf(p: any) {
  const req = p.requirements_json || p.request?.requirements_json || {}
  const min = req.budget_min_minor, max = req.budget_max_minor, cur = req.currency || 'EUR'
  const f = (v: any) => (v == null ? null : new Intl.NumberFormat(undefined, { style: 'currency', currency: cur, maximumFractionDigits: 0 }).format(v / 100))
  if (min != null && max != null) return `${f(min)} - ${f(max)}`
  if (max != null) return `≤ ${f(max)}`
  return '开放'
}
function timeAgo(iso: string) {
  const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (m < 60) return `${m} 分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小时前`
  return `${Math.floor(h / 24)} 天前`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listSupplierPings()).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载匹配需求失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
