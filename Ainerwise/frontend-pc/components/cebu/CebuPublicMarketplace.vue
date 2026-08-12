<template>
  <section class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">AinerWise Market</p>
        <h1 class="mt-2 text-3xl font-bold text-white">{{ $t('mkt.title') }}</h1>
        <p class="mt-2 text-sm text-slate-400">{{ $t('mkt.subtitle') }}</p>
      </div>
      <NuxtLink :to="localized('/market/post-request')" class="btn-primary">{{ $t('mkt.postRequest') }}</NuxtLink>
    </div>

    <!-- Sticky filter bar -->
    <div class="pc-card sticky top-16 z-20 flex flex-wrap items-center gap-3">
      <div class="min-w-0 flex-1">
        <p class="truncate text-sm font-semibold text-white">{{ activeCategoryName || $t('mkt.allItems') }}</p>
        <p class="text-xs text-slate-500">{{ loading ? $t('common.loading') : $t('mkt.countItems', { n: items.length }) }}</p>
      </div>
      <input v-model.trim="filters.q" class="input-field w-44" :placeholder="$t('mkt.searchPh')" @keyup.enter="load" />
      <select v-model="marketMode" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
        <option value="">{{ $t('mkt.modeAll') }}</option>
        <option value="B2B">{{ $t('mkt.modeB2B') }}</option>
        <option value="B2C">{{ $t('mkt.modeB2C') }}</option>
      </select>
      <select v-model="sort" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
        <option value="newest">{{ $t('mkt.sortNewest') }}</option>
        <option value="price_asc">{{ $t('mkt.sortPriceAsc') }}</option>
        <option value="price_desc">{{ $t('mkt.sortPriceDesc') }}</option>
        <option value="title">{{ $t('mkt.sortTitle') }}</option>
      </select>
      <button class="btn-primary" @click="load">{{ $t('common.search') }}</button>
    </div>

    <div class="flex gap-6">
      <!-- Sidebar -->
      <aside class="hidden w-56 shrink-0 lg:block">
        <div class="pc-card sticky top-40">
          <h3 class="mb-3 text-sm font-semibold text-slate-200">{{ $t('mkt.categories') }}</h3>
          <div class="space-y-1">
            <button
              :class="['w-full rounded-lg px-3 py-2 text-left text-sm transition', !filters.category_schema_id ? 'bg-indigo-500/15 font-medium text-indigo-200' : 'text-slate-400 hover:bg-white/5']"
              @click="setCategory('', '')"
            >{{ $t('mkt.allCats') }}</button>
            <button
              v-for="c in categories"
              :key="c.id"
              :class="['flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition', filters.category_schema_id === c.id ? 'bg-indigo-500/15 font-medium text-indigo-200' : 'text-slate-400 hover:bg-white/5']"
              @click="setCategory(c.id, categoryLabel(c))"
            >
              <span class="truncate">{{ categoryLabel(c) }}</span>
              <span v-if="c.item_count != null" class="ml-2 rounded-full bg-white/10 px-1.5 text-xs text-slate-500">{{ c.item_count }}</span>
            </button>
          </div>
          <p v-if="categoryError" class="mt-3 text-xs text-amber-300">
            {{ categoryError }}
            <button class="ml-1 underline" @click="loadCategories">{{ $t('common.retry') }}</button>
          </p>
          <label class="mt-4 flex items-center gap-2 border-t border-white/10 pt-4 text-sm text-slate-300">
            <input v-model="verifiedOnly" type="checkbox" class="accent-indigo-400" />
            {{ $t('mkt.verifiedOnly') }}
          </label>
        </div>
      </aside>

      <!-- Grid -->
      <main class="min-w-0 flex-1">
        <p v-if="error" class="pc-card border-red-500/30 text-sm text-red-300">{{ error }}</p>

        <div v-if="loading && !items.length" class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
          <div v-for="i in 8" :key="i" class="pc-card animate-pulse">
            <div class="aspect-square rounded-xl bg-white/5"></div>
            <div class="mt-3 h-4 w-3/4 rounded bg-white/10"></div>
            <div class="mt-2 h-3 w-1/2 rounded bg-white/5"></div>
          </div>
        </div>

        <div v-else-if="!visibleItems.length" class="pc-card py-16 text-center text-slate-400">
          <div class="text-4xl">🔍</div>
          <p class="mt-3 text-lg font-medium text-slate-300">{{ $t('mkt.noMatch') }}</p>
          <p class="mt-1 text-sm">{{ $t('mkt.adjustFilters') }}<NuxtLink :to="localized('/market/post-request')" class="text-indigo-300 hover:underline">{{ $t('mkt.postDirectly') }}</NuxtLink></p>
        </div>

        <div v-else class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
          <NuxtLink
            v-for="item in visibleItems"
            :key="item.id"
            :to="localized(`/market/marketplace/${item.id}`)"
            class="pc-card group !p-0 overflow-hidden transition hover:-translate-y-0.5 hover:border-indigo-400/40"
          >
            <div class="flex aspect-square items-center justify-center bg-white/5 text-5xl transition group-hover:scale-105">
              {{ categoryEmoji(item) }}
            </div>
            <div class="p-4">
              <div class="mb-2 flex items-center gap-1.5">
                <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', marketModeOf(item) === 'B2C' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-blue-500/15 text-blue-300']">{{ marketModeOf(item) }}</span>
                <span v-if="originOf(item)" class="text-[10px] text-slate-500">{{ originOf(item) }}</span>
              </div>
              <h3 class="line-clamp-2 text-sm font-semibold leading-tight text-white group-hover:text-indigo-200">{{ item.title }}</h3>
              <p class="mt-1 truncate text-xs text-slate-500">{{ supplierOf(item) }}</p>
              <div class="mt-3 flex items-end justify-between">
                <span class="text-base font-bold text-white">{{ money(item.price_minor, item.currency) }}</span>
                <span v-if="trustOf(item)" class="text-[10px] text-amber-300">★ {{ trustOf(item) }}</span>
              </div>
              <span class="mt-3 block rounded-xl bg-indigo-600 py-2 text-center text-xs font-semibold text-white transition group-hover:bg-indigo-500">
                {{ marketModeOf(item) === 'B2C' ? $t('mkt.buyNow') : $t('mkt.requestQuote') }}
              </span>
            </div>
          </NuxtLink>
        </div>

        <div v-if="visibleItems.length < sortedItems.length" class="mt-8 text-center">
          <button class="btn-secondary" @click="limit += 12">{{ $t('mkt.loadMore') }}</button>
        </div>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const { categoryLabel } = useCategoryLabel()
const { listPublicCategories, listPublicListings } = useCommerce()
const categories = ref<any[]>([])
const items = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const categoryError = ref('')
const filters = reactive({ q: '', category_schema_id: '' })
const activeCategoryName = ref('')
const marketMode = ref('')
const sort = ref('newest')
const verifiedOnly = ref(false)
const limit = ref(12)

const filteredItems = computed(() =>
  items.value.filter((it) => {
    if (marketMode.value && marketModeOf(it) !== marketMode.value) return false
    if (verifiedOnly.value && !isVerified(it)) return false
    return true
  }),
)

const sortedItems = computed(() => {
  const rows = [...filteredItems.value]
  if (sort.value === 'price_asc') rows.sort((a, b) => (a.price_minor ?? Infinity) - (b.price_minor ?? Infinity))
  else if (sort.value === 'price_desc') rows.sort((a, b) => (b.price_minor ?? -1) - (a.price_minor ?? -1))
  else if (sort.value === 'title') rows.sort((a, b) => String(a.title).localeCompare(String(b.title)))
  else rows.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
  return rows
})
const visibleItems = computed(() => sortedItems.value.slice(0, limit.value))

function attrs(it: any) {
  return it?.attributes_json && typeof it.attributes_json === 'object' ? it.attributes_json : {}
}
function marketModeOf(it: any) {
  return it.market_mode || attrs(it).market_mode || 'B2B'
}
function supplierOf(it: any) {
  return it.company_name || it.supplier_name || attrs(it).supplier_name || t('mkt.verifiedSupplier')
}
function originOf(it: any) {
  return it.origin_country || attrs(it).origin_country || ''
}
function trustOf(it: any) {
  const t = it.company_trust_score ?? attrs(it).trust_score
  return t ? Math.round(Number(t)) : ''
}
function isVerified(it: any) {
  return it.is_verified ?? attrs(it).verified ?? true
}
function categoryEmoji(it: any) {
  const name = String(it.category_name || attrs(it).category || it.title || '').toLowerCase()
  const map: [string, string][] = [
    ['construct', '🏗️'], ['knx', '🏠'], ['smart', '🏠'], ['security', '🛡️'], ['solar', '☀️'], ['energy', '⚡'],
    ['it', '💻'], ['office', '💻'], ['electron', '⚡'], ['machin', '⚙️'], ['material', '🧪'],
    ['light', '💡'], ['hvac', '❄️'], ['tool', '🔨'], ['furniture', '🪑'], ['medical', '🏥'],
  ]
  for (const [k, e] of map) if (name.includes(k)) return e
  return '📦'
}

function money(value?: number, currency = 'EUR') {
  return value == null ? t('mkt.inquire') : new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(value / 100)
}

function setCategory(id: string, name: string) {
  filters.category_schema_id = id
  activeCategoryName.value = name
  limit.value = 12
  load()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listPublicListings({ q: filters.q || undefined, category_schema_id: filters.category_schema_id || undefined })).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('mkt.loadFailed')
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  categoryError.value = ''
  try {
    categories.value = (await listPublicCategories()).items || []
  } catch (e: any) {
    categories.value = []
    categoryError.value = e?.data?.detail || e?.message || t('mkt.catLoadFailed')
  }
}

onMounted(async () => {
  await loadCategories()
  await load()
})
</script>
