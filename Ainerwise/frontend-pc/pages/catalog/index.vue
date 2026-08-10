<template>
  <div class="catalog-page">
    <!-- Header band. Carries the counts so the page states its own scope
         before any filter is touched. -->
    <header class="catalog-band">
      <div class="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-10 sm:px-6 lg:px-8">
        <div class="flex flex-wrap items-end justify-between gap-6">
          <div class="max-w-2xl">
            <p class="text-xs font-bold uppercase tracking-[0.22em] ws-accent">{{ $t('catalog.eyebrow') }}</p>
            <h1 class="mt-2 text-3xl font-bold ws-title lg:text-[2.6rem] lg:leading-[1.1]">{{ $t('catalog.title') }}</h1>
            <p class="mt-3 text-sm leading-6 ws-muted">{{ $t('catalog.subtitle') }}</p>
          </div>
          <div class="flex items-stretch gap-2">
            <div class="relative">
              <UIcon
                name="i-heroicons-magnifying-glass"
                class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 ws-faint"
              />
              <input
                v-model.trim="keyword"
                class="input-field !w-72 !pl-9"
                :placeholder="$t('catalog.searchPlaceholder')"
                @keyup.enter="reload"
              />
            </div>
            <button class="btn-primary !py-2.5 !px-5 text-sm" @click="reload">{{ $t('catalog.search') }}</button>
          </div>
        </div>

        <!-- Source segments, each carrying its own count. -->
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-for="tab in sourceTabs"
            :key="tab.key"
            type="button"
            class="catalog-seg"
            :class="{ 'catalog-seg--on': activeSource === tab.key }"
            @click="selectSource(tab.key)"
          >
            <UIcon :name="tab.icon" class="h-4 w-4" />
            {{ tab.label }}
            <span class="catalog-seg__count">{{ tab.count }}</span>
          </button>
        </div>
      </div>
    </header>

    <section class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="flex flex-col gap-8 lg:flex-row">
        <!-- Category rail -->
        <aside class="w-full shrink-0 lg:w-60">
          <div class="pc-card sticky top-24 !p-4">
            <h2 class="mb-3 px-1 text-xs font-bold uppercase tracking-[0.16em] ws-faint">
              {{ $t('catalog.categories') }}
            </h2>
            <div class="max-h-[22rem] space-y-0.5 overflow-y-auto pr-1">
              <button
                type="button"
                class="catalog-cat"
                :class="{ 'catalog-cat--on': !activeCategory }"
                @click="selectCategory('')"
              >{{ $t('catalog.allCategories') }}</button>
              <button
                v-for="cat in categories"
                :key="cat.id"
                type="button"
                class="catalog-cat"
                :class="{ 'catalog-cat--on': activeCategory === cat.id }"
                @click="selectCategory(cat.id)"
              >{{ cat.name }}</button>
            </div>

            <div class="mt-4 space-y-3 border-t ws-hairline pt-4">
              <div>
                <p class="mb-1.5 px-1 text-xs font-bold uppercase tracking-[0.16em] ws-faint">
                  {{ $t('catalog.tradeMode') }}
                </p>
                <div class="flex flex-wrap gap-1.5">
                  <button
                    v-for="mode in modeTabs"
                    :key="mode.key"
                    type="button"
                    class="ws-chip !px-3 !py-1"
                    :class="{ 'ws-chip-active': activeMode === mode.key }"
                    @click="selectMode(mode.key)"
                  >{{ mode.label }}</button>
                </div>
              </div>

              <label class="flex cursor-pointer items-center gap-2 px-1 text-sm ws-muted">
                <input
                  v-model="verifiedOnly"
                  type="checkbox"
                  class="accent-[color:var(--accent)]"
                  @change="reload"
                />
                {{ $t('catalog.verifiedOnly') }}
              </label>
            </div>
          </div>
        </aside>

        <!-- Results -->
        <main class="min-w-0 flex-1">
          <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p class="text-sm ws-muted">
              {{ $t('catalog.resultCount', { total }) }}
              <span v-if="activeCategoryName" class="ws-title"> · {{ activeCategoryName }}</span>
            </p>
            <select v-model="sort" class="input-field !w-auto !py-2 text-sm" @change="reload">
              <option value="newest">{{ $t('catalog.sortNewest') }}</option>
              <option value="trust">{{ $t('catalog.sortTrust') }}</option>
              <option value="price_asc">{{ $t('catalog.sortPriceAsc') }}</option>
              <option value="price_desc">{{ $t('catalog.sortPriceDesc') }}</option>
            </select>
          </div>

          <p v-if="error" class="pc-card text-sm text-red-400">{{ error }}</p>

          <div v-if="loading" class="grid grid-cols-2 gap-5 md:grid-cols-3 xl:grid-cols-4">
            <div v-for="n in 8" :key="n" class="pc-card !p-0 overflow-hidden">
              <div class="aspect-[4/3] animate-pulse ws-soft"></div>
              <div class="space-y-2 p-4">
                <div class="h-3 w-3/4 animate-pulse rounded ws-soft"></div>
                <div class="h-3 w-1/2 animate-pulse rounded ws-soft"></div>
              </div>
            </div>
          </div>

          <div v-else-if="items.length" class="grid grid-cols-2 gap-5 md:grid-cols-3 xl:grid-cols-4">
            <article v-for="item in items" :key="item.id" class="catalog-card group">
              <NuxtLink :to="item.detail_path" class="block">
                <div class="catalog-card__media">
                  <img v-if="item.image" :src="item.image" :alt="item.title" />
                  <UIcon v-else name="i-heroicons-cube" class="h-10 w-10 ws-faint" />
                  <span :class="['catalog-badge', `catalog-badge--${item.source}`]">
                    {{ $t(`catalog.source.${item.source}`) }}
                  </span>
                </div>
                <div class="catalog-card__body">
                  <p class="catalog-card__title">{{ item.title }}</p>
                  <p class="catalog-card__meta">
                    <UIcon
                      v-if="item.verified"
                      name="i-heroicons-check-badge"
                      class="mr-0.5 inline h-3.5 w-3.5 align-[-2px] text-emerald-500"
                    />
                    {{ item.vendor_name || item.brand || $t('catalog.platformStock') }}
                    <span v-if="item.trust_score" class="ml-1 text-amber-500">★ {{ item.trust_score }}</span>
                  </p>
                </div>
              </NuxtLink>
              <div class="catalog-card__foot">
                <div class="min-w-0">
                  <span class="catalog-card__price">{{ formatPrice(item) }}</span>
                  <span v-if="item.price_is_reference && item.price_minor != null" class="ml-1 text-[10px] ws-faint">
                    {{ $t('catalog.reference') }}
                  </span>
                </div>
                <NuxtLink :to="ctaTarget(item)" class="catalog-cta">{{ ctaLabel(item) }}</NuxtLink>
              </div>
            </article>
          </div>

          <div v-else class="pc-card py-20 text-center">
            <UIcon name="i-heroicons-magnifying-glass" class="mx-auto h-10 w-10 ws-faint" />
            <p class="mt-3 text-sm ws-muted">{{ $t('catalog.empty') }}</p>
            <button class="ws-chip mt-4 !px-4 !py-2" @click="resetFilters">{{ $t('catalog.clearFilters') }}</button>
          </div>

          <WorkspacePagination v-model:page="page" :page-size="pageSize" :total="total" />
        </main>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
type CatalogItem = {
  id: string
  source: 'official' | 'supplier' | 'secondhand'
  title: string
  brand?: string | null
  vendor_name?: string | null
  price_minor?: number | null
  currency: string
  price_is_reference: boolean
  market_mode?: string | null
  image?: string | null
  verified?: boolean
  trust_score?: number | null
  detail_path: string
}

const { t } = useI18n()
const { apiFetch } = useApi()
const route = useRoute()
const router = useRouter()

const items = ref<CatalogItem[]>([])
const categories = ref<Array<{ id: string; name: string }>>([])
const facets = ref<Record<string, number>>({})
const total = ref(0)
const page = ref(Number(route.query.page) || 1)
const pageSize = 24
const loading = ref(true)
const error = ref('')
const keyword = ref(String(route.query.keyword || ''))
const sort = ref(String(route.query.sort || 'newest'))
const activeSource = ref(String(route.query.source || 'all'))
const activeMode = ref(String(route.query.market_mode || 'all'))
const activeCategory = ref(String(route.query.category_id || ''))
const verifiedOnly = ref(route.query.verified === '1')

const sumFacets = computed(() =>
  Object.values(facets.value).reduce((sum, n) => sum + Number(n || 0), 0),
)
const sourceTabs = computed(() => [
  { key: 'all', icon: 'i-heroicons-squares-2x2', label: t('catalog.source.all'), count: sumFacets.value },
  { key: 'official', icon: 'i-heroicons-shield-check', label: t('catalog.source.official'), count: facets.value.official ?? 0 },
  { key: 'supplier', icon: 'i-heroicons-building-storefront', label: t('catalog.source.supplier'), count: facets.value.supplier ?? 0 },
  { key: 'secondhand', icon: 'i-heroicons-arrow-path', label: t('catalog.source.secondhand'), count: facets.value.secondhand ?? 0 },
])
const modeTabs = computed(() => [
  { key: 'all', label: t('catalog.modeAll') },
  { key: 'B2B', label: 'B2B' },
  { key: 'B2C', label: 'B2C' },
])
const activeCategoryName = computed(
  () => categories.value.find(c => c.id === activeCategory.value)?.name || '',
)

function formatPrice(item: CatalogItem) {
  if (item.price_minor == null) return t('catalog.onRequest')
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: item.currency || 'EUR',
      maximumFractionDigits: 0,
    }).format(item.price_minor / 100)
  } catch {
    return `${(item.price_minor / 100).toLocaleString()} ${item.currency}`
  }
}

// B2C listings can be bought outright; everything else starts a quote.
function ctaLabel(item: CatalogItem) {
  if (item.source === 'official') return t('catalog.ctaEnquire')
  return item.market_mode === 'B2C' ? t('catalog.ctaBuy') : t('catalog.ctaQuote')
}
function ctaTarget(item: CatalogItem) {
  if (item.market_mode === 'B2C' && item.source !== 'official') return item.detail_path
  return `/market/post-request?listing=${item.id}`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({
      page: String(page.value),
      page_size: String(pageSize),
      sort: sort.value,
    })
    if (activeSource.value !== 'all') params.set('source', activeSource.value)
    if (activeMode.value !== 'all') params.set('market_mode', activeMode.value)
    if (activeCategory.value) params.set('category_id', activeCategory.value)
    if (verifiedOnly.value) params.set('verified_only', 'true')
    if (keyword.value) params.set('keyword', keyword.value)
    const data = await apiFetch<any>(`/catalog/unified?${params.toString()}`)
    items.value = data.items || []
    total.value = data.total || 0
    facets.value = data.facets?.source || {}
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('catalog.loadFailed')
    items.value = []
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const data = await apiFetch<any>('/catalog/categories')
    // Both trees in one rail; the feed matches an id against either side.
    categories.value = [...(data.supplier || []), ...(data.official || [])]
  } catch {
    categories.value = []
  }
}

function syncQuery() {
  router.replace({
    query: {
      ...(activeSource.value !== 'all' ? { source: activeSource.value } : {}),
      ...(activeMode.value !== 'all' ? { market_mode: activeMode.value } : {}),
      ...(activeCategory.value ? { category_id: activeCategory.value } : {}),
      ...(verifiedOnly.value ? { verified: '1' } : {}),
      ...(keyword.value ? { keyword: keyword.value } : {}),
      ...(sort.value !== 'newest' ? { sort: sort.value } : {}),
      ...(page.value > 1 ? { page: String(page.value) } : {}),
    },
  })
}

function reload() {
  page.value = 1
  syncQuery()
  load()
}
function selectSource(key: string) { activeSource.value = key; reload() }
function selectMode(key: string) { activeMode.value = key; reload() }
function selectCategory(id: string) { activeCategory.value = id; reload() }
function resetFilters() {
  activeSource.value = 'all'
  activeMode.value = 'all'
  activeCategory.value = ''
  verifiedOnly.value = false
  keyword.value = ''
  reload()
}

watch(page, () => { syncQuery(); load() })

onMounted(() => {
  loadCategories()
  load()
})
</script>

<style scoped>
.catalog-band {
  border-bottom: 1px solid var(--card-border);
  background: linear-gradient(180deg, var(--surface-sunken), transparent);
}

.catalog-seg {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  border: 1px solid var(--hairline-soft);
  background: var(--card-bg);
  padding: 0.5rem 0.9rem;
  font-size: 0.875rem;
  color: var(--text-muted);
  transition: all 0.16s ease;
}
.catalog-seg:hover { border-color: var(--accent); color: var(--accent); }
.catalog-seg--on {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--accent-contrast);
  font-weight: 600;
}
.catalog-seg__count {
  border-radius: 999px;
  background: var(--surface-soft);
  padding: 0 0.4rem;
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  color: var(--text-muted);
}
.catalog-seg--on .catalog-seg__count {
  background: rgba(255, 255, 255, 0.22);
  color: var(--accent-contrast);
}

.catalog-cat {
  display: block;
  width: 100%;
  border-radius: 0.6rem;
  padding: 0.5rem 0.7rem;
  text-align: left;
  font-size: 0.85rem;
  color: var(--text-muted);
  transition: all 0.14s ease;
}
.catalog-cat:hover { background: var(--surface-soft); color: var(--page-text); }
.catalog-cat--on {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.catalog-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}
.catalog-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(2, 6, 23, 0.1);
}
.catalog-card__media {
  position: relative;
  display: flex;
  aspect-ratio: 4 / 3;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--surface-soft);
}
.catalog-card__media img {
  height: 100%;
  width: 100%;
  object-fit: cover;
  transition: transform 0.25s ease;
}
.catalog-card:hover .catalog-card__media img { transform: scale(1.05); }

.catalog-badge {
  position: absolute;
  left: 0.6rem;
  top: 0.6rem;
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 700;
  backdrop-filter: blur(6px);
}
.catalog-badge--official { background: rgba(16, 185, 129, 0.16); color: #047857; }
.catalog-badge--supplier { background: rgba(59, 130, 246, 0.16); color: #1d4ed8; }
.catalog-badge--secondhand { background: rgba(245, 158, 11, 0.18); color: #b45309; }
:global(.dark) .catalog-badge--official { color: #6ee7b7; }
:global(.dark) .catalog-badge--supplier { color: #93c5fd; }
:global(.dark) .catalog-badge--secondhand { color: #fcd34d; }

.catalog-card__body { padding: 0.85rem 0.9rem 0.5rem; }
.catalog-card__title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--page-text);
}
.catalog-card__meta {
  margin-top: 0.3rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.75rem;
  color: var(--text-faint);
}
.catalog-card__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-top: 1px solid var(--hairline-soft);
  padding: 0.7rem 0.9rem;
}
.catalog-card__price {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--accent);
}
.catalog-cta {
  flex: none;
  border-radius: 999px;
  border: 1px solid var(--accent);
  padding: 0.3rem 0.7rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--accent);
  transition: all 0.16s ease;
}
.catalog-cta:hover { background: var(--accent); color: var(--accent-contrast); }
</style>
