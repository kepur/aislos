<template>
  <div class="bg-slate-50 min-h-screen">
    <section class="mx-auto max-w-7xl px-6 pt-4">
      <div class="relative">
        <a
          :href="activeHero.href"
          class="group relative block h-24 overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 shadow-lg shadow-slate-200/60 sm:h-28"
        >
          <img
            v-for="(slide, index) in marketHeroSlides"
            :key="slide.image"
            :src="slide.image"
            :alt="slide.title"
            :class="[
              'absolute inset-0 h-full w-full object-cover transition-all duration-700',
              activeHeroIndex === index ? 'scale-100 opacity-100' : 'scale-105 opacity-0'
            ]"
          />
        </a>
        <div class="absolute bottom-3 right-4 flex items-center gap-1.5">
          <button
            v-for="(_slide, index) in marketHeroSlides"
            :key="index"
            type="button"
            :aria-label="`${appStore.t('market.bannerGoTo')} ${index + 1}`"
            :class="[
              'h-2.5 w-2.5 rounded-full border border-white/70 transition-colors',
              activeHeroIndex === index ? 'bg-white' : 'bg-white/30 hover:bg-white/60'
            ]"
            @click.prevent="setHeroBanner(index)"
          />
        </div>
      </div>
    </section>

    <!-- Top filter bar -->
    <div class="mt-4 bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
      <div class="mx-auto max-w-7xl px-6 py-3 flex flex-wrap items-center gap-3">
        <!-- Breadcrumb / Title -->
        <div class="flex-shrink-0 min-w-0 max-w-[220px]">
          <h1 class="text-lg font-bold text-slate-900 truncate">
            {{ activeCategoryName || appStore.t('market.title') }}
          </h1>
          <p v-if="!loading" class="text-xs text-slate-400">{{ total }} {{ appStore.t('market.items') }}</p>
        </div>

        <!-- Search -->
        <div class="flex flex-1 items-center gap-2 flex-wrap justify-end">
          <div class="relative flex-1 min-w-[280px] max-w-3xl">
            <UIcon name="i-heroicons-magnifying-glass" class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              v-model="keyword"
              type="text"
              :placeholder="appStore.t('market.searchPlaceholder')"
              class="w-full border-2 border-slate-200 rounded-xl pl-11 pr-4 py-3 text-base outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-200"
              @keyup.enter="loadFeed(true)"
            />
          </div>

          <!-- Market Mode -->
          <select v-model="marketMode" @change="loadFeed(true)" class="border border-slate-200 rounded-xl px-3 py-3 text-sm outline-none focus:ring-2 focus:ring-indigo-300">
            <option value="">{{ appStore.t('market.allModes') }}</option>
            <option value="B2B">{{ appStore.t('market.b2bOnly') }}</option>
            <option value="B2C">{{ appStore.t('market.b2cOnly') }}</option>
          </select>

          <!-- Sort -->
          <select v-model="sort" @change="loadFeed(true)" class="border border-slate-200 rounded-xl px-3 py-3 text-sm outline-none focus:ring-2 focus:ring-indigo-300">
            <option value="rank">{{ appStore.t('market.bestMatch') }}</option>
            <option value="newest">{{ appStore.t('market.newest') }}</option>
            <option value="orders">{{ appStore.t('market.mostOrders') }}</option>
            <option value="price_asc">{{ appStore.t('market.priceAsc') }}</option>
            <option value="price_desc">{{ appStore.t('market.priceDesc') }}</option>
          </select>

          <button @click="loadFeed(true)" class="bg-indigo-600 text-white px-6 py-3 rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-colors">
            {{ appStore.t('action.search') }}
          </button>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-7xl px-6 py-6 flex gap-6">
      <!-- Sidebar filters -->
      <aside class="w-52 flex-shrink-0 hidden lg:block">
        <div class="bg-white rounded-2xl border border-slate-200 p-4 sticky top-20">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">{{ appStore.t('nav.categories') }}</h3>
          <div class="space-y-1">
            <button
              @click="setCategoryFilter(null)"
              :class="['w-full text-left text-sm px-3 py-2 rounded-lg transition-colors', !categoryId ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-50']"
            >
              {{ appStore.t('categories.title') }}
            </button>
            <button
              v-for="cat in filterCategories"
              :key="cat.id"
              @click="setCategoryFilter(cat.id, cat.name)"
              :class="['w-full text-left text-sm px-3 py-2 rounded-lg transition-colors flex items-center justify-between', categoryId === cat.id ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-50']"
            >
              <span>{{ cat.name }}</span>
              <span class="text-xs bg-slate-100 text-slate-500 rounded-full px-1.5">{{ cat.item_count }}</span>
            </button>
          </div>

          <div v-if="filterOriginCountries.length" class="mt-4 pt-4 border-t border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">{{ appStore.t('market.originCountry') }}</h3>
            <select v-model="originCountry" @change="loadFeed(true)" class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm">
              <option value="">{{ appStore.t('market.allCountries') }}</option>
              <option v-for="c in filterOriginCountries" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <div class="mt-4 pt-4 border-t border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">Delivery Country</h3>
            <select v-model="deliveryCountry" @change="loadFeed(true)" class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm">
              <option value="">All open countries</option>
              <option v-for="region in appStore.regionOptions" :key="region.code" :value="region.code">
                {{ region.label }}
              </option>
            </select>
          </div>

          <!-- Seller Type -->
          <div class="mt-4 pt-4 border-t border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">{{ appStore.t('market.sellerType') }}</h3>
            <select v-model="merchantType" @change="loadFeed(true)" class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm">
              <option value="">{{ appStore.t('market.allSellers') }}</option>
              <option value="INDIVIDUAL">{{ appStore.t('market.individual') }}</option>
              <option value="BUSINESS">{{ appStore.t('market.business') }}</option>
            </select>
          </div>

          <!-- Verified Only -->
          <div class="mt-3 flex items-center gap-2">
            <input id="verified-only" type="checkbox" v-model="verifiedOnly" @change="loadFeed(true)" class="rounded border-slate-300" />
            <label for="verified-only" class="text-sm text-slate-600 cursor-pointer">{{ appStore.t('market.verifiedOnly') }}</label>
          </div>
        </div>
      </aside>

      <!-- Feed Grid -->
      <main class="flex-1 min-w-0">
        <div v-if="searchContextChips.length" class="mb-5 rounded-2xl border border-indigo-100 bg-white p-4 shadow-sm">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-sm font-semibold text-slate-700">Active search</span>
            <span
              v-for="chip in searchContextChips"
              :key="chip"
              class="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700"
            >
              {{ chip }}
            </span>
            <button class="ml-auto text-xs font-semibold text-slate-500 hover:text-indigo-600" @click="clearSearchContext">
              Clear
            </button>
          </div>
          <p v-if="budgetCurrency" class="mt-2 text-xs text-slate-500">
            Budget is interpreted in {{ budgetCurrency }}. Product cards keep each supplier listing currency.
          </p>
        </div>

        <!-- Loading skeleton -->
        <div v-if="loading && items.length === 0" class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
          <div v-for="i in 8" :key="i" class="bg-white rounded-2xl border border-slate-200 p-4 animate-pulse">
            <div class="aspect-square bg-slate-100 rounded-xl mb-3"></div>
            <div class="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
            <div class="h-3 bg-slate-100 rounded w-1/2"></div>
          </div>
        </div>

        <div v-else-if="feedError" class="rounded-2xl border border-red-100 bg-red-50 p-6 text-center text-red-700">
          <p class="text-base font-semibold">{{ appStore.t('market.couldNotLoad') }}</p>
          <p class="mt-1 text-sm">{{ feedError }}</p>
          <button class="mt-4 rounded-xl bg-red-600 px-5 py-2 text-sm font-semibold text-white" @click="loadFeed(true)">{{ appStore.t('market.retry') }}</button>
        </div>

        <!-- Empty state -->
        <div v-else-if="!loading && items.length === 0" class="text-center py-24 text-slate-400">
          <div class="text-5xl mb-4">🔍</div>
          <p class="text-lg font-medium">{{ appStore.t('market.noProducts') }}</p>
          <p class="text-sm mt-1">{{ appStore.t('market.tryFilters') }} <NuxtLink :to="appStore.localizedPath('/post-request')" class="text-indigo-600 hover:underline">{{ appStore.t('market.postRequestInstead') }}</NuxtLink></p>
        </div>

        <template v-else>
          <!-- Recommended (official) strip -->
          <div v-if="recommendedItems.length" class="mb-6">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-lg">⭐</span>
              <h2 class="text-base font-bold text-slate-900">{{ appStore.t('market.recommended') }}</h2>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div
                v-for="item in recommendedItems"
                :key="`rec-${item.id}`"
                class="relative bg-gradient-to-br from-indigo-50 to-white rounded-2xl border border-indigo-200 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group overflow-hidden"
                @click="router.push(appStore.localizedPath(`/marketplace/${item.id}`))"
              >
                <span class="absolute left-3 top-3 z-10 inline-flex items-center gap-1 rounded-full bg-indigo-600 px-2 py-0.5 text-[10px] font-bold text-white shadow">
                  ✓ {{ appStore.t('market.official') }}
                </span>
                <div class="aspect-[4/3] overflow-hidden">
                  <img
                    v-if="item.images && item.images[0]"
                    :src="item.images[0]"
                    :alt="item.title"
                    class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <MarketItemVisual v-else :title="item.title" :category-name="item.category_name" />
                </div>
                <div class="p-3">
                  <h3 class="text-sm font-semibold text-slate-900 line-clamp-1 group-hover:text-indigo-600 transition-colors">{{ item.title }}</h3>
                  <div class="mt-1 flex items-center justify-between">
                    <span class="text-sm font-bold text-slate-900">{{ formatPrice(item.price_minor, item.currency) }}</span>
                    <span class="text-[10px] text-slate-400">{{ item.market_mode }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Items grid -->
          <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="item in items"
            :key="item.id"
            class="bg-white rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer group"
            @click="router.push(appStore.localizedPath(`/marketplace/${item.id}`))"
          >
            <!-- Sponsored badge -->
            <div v-if="item.is_sponsored" class="px-3 pt-2">
              <span class="text-[10px] bg-amber-50 text-amber-600 border border-amber-200 rounded-full px-2 py-0.5 font-medium">{{ appStore.t('market.sponsored') }}</span>
            </div>

            <!-- Image -->
            <div class="aspect-square overflow-hidden" :class="item.is_sponsored ? 'rounded-t-none' : 'rounded-t-2xl'">
              <img
                v-if="item.images && item.images[0]"
                :src="item.images[0]"
                :alt="item.title"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <MarketItemVisual v-else :title="item.title" :category-name="item.category_name" />
            </div>

            <!-- Info -->
            <div class="p-4">
              <!-- Market mode badge -->
              <div class="flex items-center gap-1.5 mb-2">
                <span v-if="item.is_official" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-600 text-white">✓ {{ appStore.t('market.official') }}</span>
                <span
                  :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full', item.market_mode === 'B2C' ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600']"
                >{{ item.market_mode }}</span>
                <span v-if="item.origin_country" class="text-[10px] text-slate-400">{{ item.origin_country }}</span>
              </div>

              <h3 class="text-sm font-semibold text-slate-900 leading-tight line-clamp-2 group-hover:text-indigo-600 transition-colors">
                {{ item.title }}
              </h3>
              <p class="text-xs text-slate-400 mt-1 truncate">{{ item.company_name }}</p>

              <!-- Price & Action -->
              <div class="mt-3 flex items-center justify-between">
                <div>
                  <span class="text-base font-bold text-slate-900">{{ formatPrice(item.price_minor, item.currency) }}</span>
                  <span class="text-xs text-slate-400 ml-1">/ {{ item.unit }}</span>
                </div>
              </div>

              <!-- Min order + trust -->
              <div class="mt-2 flex items-center gap-2">
                <span v-if="item.min_order_qty > 1" class="text-[10px] text-slate-400">{{ appStore.t('market.moq') }}: {{ item.min_order_qty }}</span>
                <span v-if="item.company_trust_score" class="text-[10px] text-amber-600">★ {{ Math.round(item.company_trust_score) }}</span>
                <span v-if="item.order_count > 0" class="text-[10px] text-slate-400 ml-auto">{{ item.order_count }} {{ appStore.t('market.orders') }}</span>
              </div>

              <!-- CTA button -->
              <button
                @click.stop="handleCta(item)"
                :class="['w-full mt-3 py-2 rounded-xl text-xs font-semibold transition-colors', item.market_mode === 'B2C' ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-indigo-600 text-white hover:bg-indigo-700']"
              >
                {{ item.market_mode === 'B2C' ? appStore.t('market.buyNow') : appStore.t('market.requestQuote') }}
              </button>
            </div>
          </div>
          </div>
        </template>

        <!-- Load more -->
        <div v-if="hasNext" class="mt-8 text-center">
          <button
            @click="loadMore"
            :disabled="loading"
            class="bg-white border border-slate-200 text-slate-700 px-8 py-3 rounded-xl font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <span v-if="loading">{{ appStore.t('market.loading') }}</span>
            <span v-else>{{ appStore.t('market.loadMore') }}</span>
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">

definePageMeta({ layout: 'default' })

const config = useRuntimeConfig()
const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const activeHeroIndex = ref(0)
let heroTimer: ReturnType<typeof setInterval> | null = null

interface FeedItem {
  id: string
  title: string
  description: string | null
  price_minor: number
  currency: string
  unit: string
  stock_qty: number
  images: string[] | null
  tags: string[] | null
  market_mode: 'B2B' | 'B2C' | 'BOTH'
  min_order_qty: number
  origin_country: string | null
  view_count: number
  order_count: number
  category_id: string
  category_name: string | null
  company_id: string
  company_name: string | null
  company_trust_score: number | null
  is_sponsored: boolean
  ad_placement: string | null
  rank_score: number | null
}

interface FilterCat { id: string; name: string; name_zh?: string; icon?: string; item_count: number }

const items = ref<FeedItem[]>([])
const total = ref(0)
const hasNext = ref(false)
const loading = ref(false)
const feedError = ref('')
const page = ref(1)

// Filters
const categoryId = ref<string | null>((route.query.category_id as string) || null)
const activeCategoryName = ref<string>((route.query.category_name as string) || '')
const marketMode = ref<string>((route.query.market_mode as string) || '')
const keyword = ref<string>((route.query.keyword as string) || '')
const sort = ref<string>((route.query.sort as string) || 'rank')
const originCountry = ref<string>((route.query.origin_country as string) || '')
const deliveryCountry = ref<string>(
  ((route.query.delivery_country as string) || (route.query.country as string) || '').toUpperCase().slice(0, 2)
)
const deliveryCountryName = ref<string>((route.query.delivery_country_name as string) || '')
const deliveryCity = ref<string>((route.query.delivery_city as string) || (route.query.city as string) || (route.query.location as string) || '')
const radiusKm = ref<string>((route.query.radius_km as string) || (route.query.radius as string) || '')
const budgetMinMinor = ref<string>((route.query.budget_min_minor as string) || (route.query.budget_min as string) || '')
const budgetMaxMinor = ref<string>((route.query.budget_max_minor as string) || (route.query.budget_max as string) || '')
const budgetCurrency = ref<string>((route.query.budget_currency as string) || '')
const latitude = ref<string>((route.query.lat as string) || '')
const longitude = ref<string>((route.query.lng as string) || '')

const merchantType = ref<string>('')
const verifiedOnly = ref<boolean>(false)

// Curated strip: official listings, only on the unfiltered feed.
const recommendedItems = computed(() =>
  keyword.value || categoryId.value ? [] : items.value.filter((item: any) => item.is_official).slice(0, 4)
)

// Filter options from API
const filterCategories = ref<FilterCat[]>([])
const filterOriginCountries = ref<string[]>([])
const searchContextChips = computed(() => {
  const chips: string[] = []
  if (activeCategoryName.value) chips.push(`Category: ${activeCategoryName.value}`)
  if (deliveryCountry.value) chips.push(`Country: ${deliveryCountryName.value || countryName(deliveryCountry.value)}`)
  if (deliveryCity.value) chips.push(`City: ${deliveryCity.value}`)
  if (radiusKm.value) chips.push(`Radius: ${radiusKm.value} km`)
  if (budgetMinMinor.value || budgetMaxMinor.value) {
    const min = budgetMinMinor.value ? Number(budgetMinMinor.value) / 100 : null
    const max = budgetMaxMinor.value ? Number(budgetMaxMinor.value) / 100 : null
    chips.push(`Budget: ${min == null ? '0' : formatNumber(min)} - ${max == null ? 'Max' : formatNumber(max)} ${budgetCurrency.value || appStore.currency}`)
  }
  if (latitude.value && longitude.value) chips.push('Location detected')
  return chips
})

const marketHeroSlides = computed(() => [
  {
    image: '/market-banners/ai-knx-smart-building.svg',
    title: appStore.t('market.banner1Title'),
    href: officialSitePath('/ai-building-brain'),
  },
  {
    image: '/market-banners/villa-smart-home.svg',
    title: appStore.t('market.banner2Title'),
    href: officialSitePath('/solutions'),
  },
  {
    image: '/market-banners/hotel-ai-upgrade.svg',
    title: appStore.t('market.banner3Title'),
    href: officialSitePath('/submit-requirement?category=hotel'),
  },
])
const activeHero = computed(() => marketHeroSlides.value[activeHeroIndex.value] || marketHeroSlides.value[0])
function officialSitePath(path: string) {
  const prefix = appStore.routeLocalePrefix || appStore.prefixForLanguage(appStore.language) || 'en'
  const cleanBase = String(config.public.aislosSiteUrl || 'http://localhost:4099').replace(/\/+$/, '')
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${cleanBase}/${prefix}${normalizedPath === '/' ? '' : normalizedPath}`
}

// Load filter options
onMounted(async () => {
  heroTimer = setInterval(() => {
    activeHeroIndex.value = (activeHeroIndex.value + 1) % marketHeroSlides.value.length
  }, 5200)
  try {
    const f = await $fetch<any>(`${config.public.apiBase}/marketplace/filters`)
    filterCategories.value = f.categories ?? []
    filterOriginCountries.value = f.origin_countries ?? []
    if (categoryId.value && !activeCategoryName.value) {
      activeCategoryName.value = filterCategories.value.find((cat) => cat.id === categoryId.value)?.name || ''
    }
  } catch {}
  await loadFeed(true)
})

onBeforeUnmount(() => {
  if (heroTimer) clearInterval(heroTimer)
})

async function loadFeed(reset = false) {
  if (reset) {
    page.value = 1
    items.value = []
  }
  loading.value = true
  feedError.value = ''
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: 20,
      sort: sort.value,
    }
    if (categoryId.value) params.category_id = categoryId.value
    if (marketMode.value) params.market_mode = marketMode.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (originCountry.value) params.origin_country = originCountry.value
    if (deliveryCountry.value) params.country = deliveryCountry.value
    if (deliveryCity.value) params.city = deliveryCity.value
    if (radiusKm.value) params.radius_km = radiusKm.value
    if (budgetMinMinor.value) params.budget_min_minor = budgetMinMinor.value
    if (budgetMaxMinor.value) params.budget_max_minor = budgetMaxMinor.value
    if (budgetCurrency.value) params.budget_currency = budgetCurrency.value
    if (latitude.value && longitude.value) {
      params.lat = latitude.value
      params.lng = longitude.value
    }
    if (merchantType.value) params.account_type = merchantType.value
    if (verifiedOnly.value) params.verified_only = true

    const data = await $fetch<any>(`${config.public.apiBase}/marketplace/feed`, { params })
    if (reset) {
      items.value = data.items
    } else {
      items.value.push(...data.items)
    }
    total.value = data.total
    hasNext.value = data.has_next
  } catch (e) {
    console.error('Feed error', e)
    if (reset) items.value = []
    feedError.value = (e as any)?.data?.detail ?? (e as any)?.message ?? 'Marketplace feed request failed.'
    total.value = items.value.length
    hasNext.value = false
  } finally {
    loading.value = false
  }
}

function setCategoryFilter(id: string | null, name?: string) {
  categoryId.value = id
  activeCategoryName.value = name || ''
  loadFeed(true)
}

function clearSearchContext() {
  categoryId.value = null
  activeCategoryName.value = ''
  keyword.value = ''
  originCountry.value = ''
  deliveryCountry.value = ''
  deliveryCountryName.value = ''
  deliveryCity.value = ''
  radiusKm.value = ''
  budgetMinMinor.value = ''
  budgetMaxMinor.value = ''
  budgetCurrency.value = ''
  latitude.value = ''
  longitude.value = ''
  router.replace(appStore.localizedPath('/marketplace'))
  loadFeed(true)
}

function setHeroBanner(index: number) {
  activeHeroIndex.value = index
}

async function loadMore() {
  page.value++
  await loadFeed(false)
}

function formatPrice(minor: number, currency: string): string {
  const amount = minor / 100
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency || 'USD', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(amount)
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
}

function countryName(countryCode: string) {
  const normalized = String(countryCode || '').toUpperCase().slice(0, 2)
  return appStore.regionOptions.find((region) => region.code === normalized)?.label || normalized
}

function handleCta(item: FeedItem) {
  const action = item.market_mode === 'B2C' ? 'buy' : 'quote'
  router.push(appStore.localizedPath(`/marketplace/${item.id}?action=${action}`))
}
</script>
