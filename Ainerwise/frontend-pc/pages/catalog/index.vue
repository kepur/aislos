<template>
  <section class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
    <header class="flex flex-wrap items-end justify-between gap-6">
      <div class="max-w-2xl">
        <p class="text-xs font-bold uppercase tracking-[0.2em] ws-accent">{{ $t('catalog.eyebrow') }}</p>
        <h1 class="mt-2 text-3xl font-bold ws-title lg:text-4xl">{{ $t('catalog.title') }}</h1>
        <p class="mt-3 text-sm leading-6 ws-muted">{{ $t('catalog.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <input
          v-model.trim="keyword"
          class="input-field !w-64"
          :placeholder="$t('catalog.searchPlaceholder')"
          @keyup.enter="reload"
        />
        <button class="btn-primary !py-2.5 !px-5 text-sm" @click="reload">{{ $t('catalog.search') }}</button>
      </div>
    </header>

    <!-- Source tabs. This is the whole point of the page: one catalogue, the
         source is a filter rather than a separate menu entry. -->
    <div class="mt-8 flex flex-wrap items-center gap-2 border-b ws-hairline pb-4">
      <button
        v-for="tab in sourceTabs"
        :key="tab.key"
        type="button"
        class="ws-chip !px-4 !py-2 !text-sm"
        :class="{ 'ws-chip-active': activeSource === tab.key }"
        @click="selectSource(tab.key)"
      >
        {{ tab.label }}
        <span class="ml-1.5 opacity-60">{{ tab.count }}</span>
      </button>

      <span class="mx-2 hidden h-5 w-px shrink-0 sm:block" :style="{ background: 'var(--card-border)' }"></span>

      <button
        v-for="mode in modeTabs"
        :key="mode.key"
        type="button"
        class="ws-chip !px-4 !py-2 !text-sm"
        :class="{ 'ws-chip-active': activeMode === mode.key }"
        @click="selectMode(mode.key)"
      >{{ mode.label }}</button>

      <select v-model="sort" class="input-field ml-auto !w-auto !py-2 text-sm" @change="reload">
        <option value="newest">{{ $t('catalog.sortNewest') }}</option>
        <option value="price_asc">{{ $t('catalog.sortPriceAsc') }}</option>
        <option value="price_desc">{{ $t('catalog.sortPriceDesc') }}</option>
      </select>
    </div>

    <p v-if="error" class="mt-6 pc-card text-sm text-red-400">{{ error }}</p>

    <div v-if="loading" class="mt-10 text-center text-sm ws-muted">{{ $t('catalog.loading') }}</div>

    <div v-else-if="items.length" class="mt-8 grid grid-cols-2 gap-5 md:grid-cols-3 xl:grid-cols-4">
      <NuxtLink
        v-for="item in items"
        :key="item.id"
        :to="item.detail_path"
        class="pc-card group flex flex-col gap-3 !p-0 overflow-hidden transition hover:border-[color:var(--accent)]"
      >
        <div class="flex aspect-[4/3] items-center justify-center overflow-hidden ws-soft text-3xl">
          <img
            v-if="item.image"
            :src="item.image"
            :alt="item.title"
            class="h-full w-full object-cover transition-transform duration-200 group-hover:scale-105"
          />
          <span v-else>📦</span>
        </div>
        <div class="flex flex-1 flex-col gap-2 p-4 pt-0">
          <div class="flex flex-wrap items-center gap-1.5">
            <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', sourceTone(item.source)]">
              {{ $t(`catalog.source.${item.source}`) }}
            </span>
            <span
              v-if="item.market_mode"
              class="rounded-full px-2 py-0.5 text-[10px] font-semibold ws-soft ws-muted"
            >{{ item.market_mode }}</span>
          </div>
          <p class="line-clamp-2 text-sm font-semibold leading-snug ws-title">{{ item.title }}</p>
          <p v-if="item.vendor_name || item.brand" class="truncate text-xs ws-faint">
            {{ item.vendor_name || item.brand }}
          </p>
          <div class="mt-auto flex items-baseline gap-1.5 pt-1">
            <span class="text-base font-bold ws-accent">{{ formatPrice(item) }}</span>
            <span v-if="item.price_is_reference && item.price_minor != null" class="text-[10px] ws-faint">
              {{ $t('catalog.reference') }}
            </span>
          </div>
        </div>
      </NuxtLink>
    </div>

    <div v-else class="mt-16 text-center">
      <p class="text-4xl">🔍</p>
      <p class="mt-3 text-sm ws-muted">{{ $t('catalog.empty') }}</p>
    </div>

    <div v-if="totalPages > 1" class="mt-10 flex items-center justify-center gap-2">
      <button class="ws-chip !px-4 !py-2" :disabled="page <= 1" @click="goPage(page - 1)">
        {{ $t('catalog.prev') }}
      </button>
      <span class="px-3 text-sm ws-muted">{{ page }} / {{ totalPages }}</span>
      <button class="ws-chip !px-4 !py-2" :disabled="page >= totalPages" @click="goPage(page + 1)">
        {{ $t('catalog.next') }}
      </button>
    </div>
  </section>
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
  detail_path: string
}

const { t } = useI18n()
const { apiFetch } = useApi()
const route = useRoute()
const router = useRouter()

const items = ref<CatalogItem[]>([])
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

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const sourceTabs = computed(() => [
  { key: 'all', label: t('catalog.source.all'), count: sumFacets.value },
  { key: 'official', label: t('catalog.source.official'), count: facets.value.official ?? 0 },
  { key: 'supplier', label: t('catalog.source.supplier'), count: facets.value.supplier ?? 0 },
  { key: 'secondhand', label: t('catalog.source.secondhand'), count: facets.value.secondhand ?? 0 },
])
const sumFacets = computed(() =>
  Object.values(facets.value).reduce((sum, n) => sum + Number(n || 0), 0),
)

const modeTabs = computed(() => [
  { key: 'all', label: t('catalog.modeAll') },
  { key: 'B2B', label: 'B2B' },
  { key: 'B2C', label: 'B2C' },
])

function sourceTone(source: string) {
  return {
    official: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
    supplier: 'bg-blue-500/15 text-blue-600 dark:text-blue-300',
    secondhand: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
  }[source] || 'ws-soft ws-muted'
}

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

function syncQuery() {
  router.replace({
    query: {
      ...(activeSource.value !== 'all' ? { source: activeSource.value } : {}),
      ...(activeMode.value !== 'all' ? { market_mode: activeMode.value } : {}),
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
function selectSource(key: string) {
  activeSource.value = key
  reload()
}
function selectMode(key: string) {
  activeMode.value = key
  reload()
}
function goPage(next: number) {
  page.value = next
  syncQuery()
  load()
  if (import.meta.client) window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(load)
</script>
