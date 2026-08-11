<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('sup.pingsEyebrow') }}</p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('sup.pingsTitle') }}</h1>
        <p class="mt-1 text-sm text-slate-400">{{ $t('sup.pingsSubtitle') }}</p>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="load()">{{ loading ? $t('common.loading') : $t('ui.refresh') }}</button>
    </div>

    <div class="pc-card flex flex-wrap items-center gap-3">
      <input v-model.trim="keyword" class="input-field max-w-xs" :placeholder="$t('reqList.searchPh')" />
      <span class="text-sm text-slate-500">{{ $t('sup.matchCount', { n: filtered.length }) }}</span>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <div class="grid gap-4">
      <div v-for="p in filtered" :key="p.id" class="pc-card flex flex-wrap items-start justify-between gap-4 transition hover:border-indigo-400/40">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <h2 class="truncate font-semibold text-white">{{ p.title || $t('supplier.reqFallback') }}</h2>
            <span v-if="p.pre_funded || p.is_pre_funded" class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">{{ $t('supplier.prefunded') }}</span>
            <span v-if="p.already_offered" class="rounded-full bg-blue-500/15 px-2 py-0.5 text-xs text-blue-300">{{ $t('sup.alreadyOffered') }}</span>
          </div>
          <p class="mt-1 line-clamp-2 text-sm text-slate-400">{{ p.description || $t('portal.procure.noDescription') }}</p>
          <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
            <span>{{ $t('supplier.budgetLabel', { v: budgetOf(p) }) }}</span>
            <span>·</span>
            <span>{{ $t('sup.matchListings', { n: matchCount(p) }) }}</span>
            <span>·</span>
            <span>{{ p.created_at ? timeAgo(p.created_at) : (p.status || '') }}</span>
          </div>
        </div>
        <NuxtLink :to="localized(`/supplier/offers/new?request_id=${requestId(p)}`)" class="btn-primary shrink-0">{{ p.already_offered ? $t('sup.updateQuote') : $t('supplier.quoteNow') }}</NuxtLink>
      </div>
      <p v-if="!loading && !filtered.length" class="pc-card py-12 text-center text-sm text-slate-400">{{ $t('sup.noPingsPre') }}<NuxtLink :to="localized('/supplier/catalog')" class="text-indigo-300">{{ $t('sup.catalogLink') }}</NuxtLink>{{ $t('sup.noPingsPost') }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
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
  return t('supplier.budgetOpen')
}
function timeAgo(iso: string) {
  const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (m < 60) return t('supplier.minAgo', { n: m })
  const h = Math.floor(m / 60)
  if (h < 24) return t('supplier.hourAgo', { n: h })
  return t('supplier.dayAgo', { n: Math.floor(h / 24) })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listSupplierPings()).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('sup.loadPingsFailed')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
