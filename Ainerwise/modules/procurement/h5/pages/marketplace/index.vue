<template>
  <div class="bg-slate-50 min-h-screen pb-32">
    <!-- Top bar -->
    <header class="bg-white sticky top-0 z-30 border-b border-slate-100 px-4 py-3">
      <div class="flex items-center gap-2">
        <div class="flex-1 relative">
          <input
            v-model="keyword"
            type="text"
            :placeholder="activeCategoryName || t('market.search_placeholder')"
            class="w-full bg-slate-100 rounded-full px-4 py-2 text-sm outline-none"
            @keyup.enter="loadFeed(true)"
          />
        </div>
        <button @click="showFilter = !showFilter" class="w-8 h-8 flex items-center justify-center">
          <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
          </svg>
        </button>
      </div>

      <!-- Delivery policy row -->
      <div class="mt-2 grid grid-cols-[minmax(105px,36%)_1fr] gap-2">
        <select
          v-model="deliveryCountry"
          class="min-w-0 rounded-xl bg-slate-100 px-3 py-3 text-sm font-semibold text-slate-700 outline-none"
          @change="handleDeliveryCountryChange"
        >
          <option value="">{{ t('market.all_countries') }}</option>
          <option v-for="region in appStore.regionOptions" :key="region.code" :value="region.code">
            {{ region.label }}
          </option>
        </select>
        <input
          v-model="deliveryCity"
          type="text"
          :placeholder="t('market.city_or_area')"
          class="min-w-0 rounded-xl bg-slate-100 px-4 py-3 text-sm outline-none placeholder:text-slate-400"
          @keyup.enter="loadFeed(true)"
          @blur="loadFeed(true)"
        />
      </div>

      <!-- Product surface chips: one AinerWise Market, multiple product sources. -->
      <div class="flex items-center gap-2 mt-2 overflow-x-auto scrollbar-hide pb-1">
        <button
          v-for="surface in productSurfaceOptions"
          :key="surface.value"
          @click="setSurface(surface.value)"
          :class="['flex-shrink-0 text-xs px-3 py-1.5 rounded-full font-bold transition-colors', activeSurface === surface.value ? surface.activeClass : 'bg-slate-100 text-slate-600']"
        >{{ surface.label }}</button>
        <NuxtLink
          :to="localizedPath('/secondhand/sell')"
          class="flex-shrink-0 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700"
        >{{ t('secondhand.sell') }}</NuxtLink>
      </div>

      <!-- Secondary filters -->
      <div class="flex items-center gap-2 mt-2 overflow-x-auto scrollbar-hide pb-1">
        <button
          v-for="m in ['All', 'B2B', 'B2C']"
          :key="m"
          @click="marketMode = m === 'All' ? '' : m; loadFeed(true)"
          :class="['flex-shrink-0 text-xs px-3 py-1.5 rounded-full font-medium transition-colors', (m === 'All' && !marketMode) || marketMode === m ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600']"
        >{{ m }}</button>
        <button
          v-for="s in sortOptions"
          :key="s.value"
          @click="sort = s.value; loadFeed(true)"
          :class="['flex-shrink-0 text-xs px-3 py-1.5 rounded-full font-medium transition-colors', sort === s.value ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600']"
        >{{ s.label }}</button>
      </div>

      <div v-if="searchContextChips.length" class="mt-2 flex items-center gap-2 overflow-x-auto scrollbar-hide pb-1">
        <span
          v-for="chip in searchContextChips"
          :key="chip"
          class="flex-shrink-0 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-[11px] font-semibold text-indigo-700"
        >
          {{ chip }}
        </span>
        <button class="flex-shrink-0 rounded-full bg-slate-100 px-3 py-1.5 text-[11px] font-semibold text-slate-500" @click="clearSearchContext">
          Clear
        </button>
      </div>
    </header>

    <!-- Filter drawer -->
    <Transition name="slide-down">
      <div v-if="showFilter" class="bg-white border-b border-slate-200 px-4 py-3 space-y-3">
        <!-- Categories -->
        <div>
          <p class="text-xs font-semibold text-slate-500 mb-2">{{ t('market.categories') }}</p>
          <div class="flex flex-wrap gap-2">
            <button
              @click="setCategoryFilter(null); showFilter = false"
              :class="['text-xs px-3 py-1.5 rounded-full border transition-colors', !categoryId ? 'border-indigo-400 text-indigo-600 bg-indigo-50' : 'border-slate-200 text-slate-600']"
            >{{ t('market.all') }}</button>
            <button
              v-for="cat in filterCategories.slice(0, 12)"
              :key="cat.id"
              @click="setCategoryFilter(cat.id, cat.name); showFilter = false"
              :class="['text-xs px-3 py-1.5 rounded-full border transition-colors', categoryId === cat.id ? 'border-indigo-400 text-indigo-600 bg-indigo-50' : 'border-slate-200 text-slate-600']"
            >{{ cat.name }}</button>
          </div>
        </div>
        <!-- Seller Type -->
        <div>
          <p class="text-xs font-semibold text-slate-500 mb-2">{{ t('market.seller_type') }}</p>
          <div class="flex gap-2">
            <button
              v-for="type in sellerTypeOptions"
              :key="type.val"
              @click="merchantType = type.val; loadFeed(true)"
              :class="['text-xs px-3 py-1.5 rounded-full border transition-colors', merchantType === type.val ? 'border-indigo-400 text-indigo-600 bg-indigo-50' : 'border-slate-200 text-slate-600']"
            >{{ type.label }}</button>
          </div>
        </div>
        <!-- Verified Only -->
        <label class="flex items-center gap-2 text-xs text-slate-600">
          <input type="checkbox" v-model="verifiedOnly" @change="loadFeed(true)" class="rounded" />
          {{ t('market.verified_only') }}
        </label>

        <div class="space-y-2 rounded-2xl bg-slate-50 p-3">
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold text-slate-500">Budget</p>
            <span class="text-[11px] font-semibold text-slate-500">{{ budgetCurrency || appStore.currency }}</span>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <input
              v-model="budgetMinInput"
              type="number"
              min="0"
              placeholder="Min"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none"
            />
            <input
              v-model="budgetMaxInput"
              type="number"
              min="0"
              placeholder="Max"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none"
            />
          </div>
          <button class="w-full rounded-xl bg-indigo-600 py-2 text-xs font-semibold text-white" @click="applyBudgetFilter">
            Apply budget
          </button>
        </div>
      </div>
    </Transition>

    <!-- Stats bar -->
    <div class="px-4 py-2 text-xs text-slate-400 flex items-center gap-2">
      <span v-if="!loading">{{ total }} {{ t('market.products') }}</span>
      <span v-else>{{ t('market.loading') }}</span>
      <span v-if="activeCategoryName"> in {{ activeCategoryName }}</span>
      <span v-if="deliveryCountry || deliveryCity" class="ml-auto flex items-center gap-1 text-indigo-500 font-medium">
        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/></svg>
        {{ deliveryCity || countryName(deliveryCountry) }}
      </span>
    </div>

    <!-- Items list (waterfall-style 2 columns) -->
    <div class="px-3">
      <!-- Loading skeleton -->
      <div v-if="loading && items.length === 0" class="grid grid-cols-2 gap-3">
        <div v-for="i in 6" :key="i" class="bg-white rounded-2xl overflow-hidden animate-pulse">
          <div class="aspect-square bg-slate-100"></div>
          <div class="p-3 space-y-2">
            <div class="h-3 bg-slate-200 rounded w-3/4"></div>
            <div class="h-3 bg-slate-100 rounded w-1/2"></div>
          </div>
        </div>
      </div>

      <div v-else-if="feedError" class="rounded-2xl border border-red-100 bg-red-50 p-4 text-center text-red-700">
        <p class="text-sm font-semibold">{{ t('market.could_not_load') }}</p>
        <p class="mt-1 text-xs">{{ feedError }}</p>
        <button class="mt-3 rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white" @click="loadFeed(true)">{{ t('common.retry') }}</button>
      </div>

      <!-- Empty -->
      <div v-else-if="!loading && items.length === 0" class="text-center py-20">
        <div class="text-5xl mb-3">🔍</div>
        <p class="text-slate-500 text-sm">{{ t('market.no_products') }}</p>
        <NuxtLink :to="localizedPath('/buyer/post-request')" class="mt-3 inline-block text-indigo-600 text-sm font-medium">
          {{ t('market.post_request_instead') }} →
        </NuxtLink>
        <NuxtLink
          :to="localizedPath('/secondhand/sell')"
          class="ml-3 mt-3 inline-block text-emerald-600 text-sm font-medium"
        >
          {{ t('secondhand.sell') }} →
        </NuxtLink>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-2 gap-3">
        <div
          v-for="item in items"
          :key="item.id"
          class="bg-white rounded-2xl overflow-hidden border border-slate-100 active:scale-95 transition-transform cursor-pointer"
          role="button"
          tabindex="0"
          @click="openItem(item)"
          @keyup.enter="openItem(item)"
        >
          <!-- Sponsored -->
          <div v-if="item.is_sponsored" class="px-2 pt-1.5">
            <span class="text-[9px] bg-amber-50 text-amber-500 border border-amber-100 rounded-full px-1.5 py-0.5 font-medium">{{ t('market.ad') }}</span>
          </div>

          <!-- Image -->
          <div class="aspect-square">
            <img
              v-if="item.images && item.images[0]"
              :src="item.images[0]"
              :alt="item.title"
              class="w-full h-full object-cover"
            />
            <MarketItemVisual v-else :title="item.title" :category-name="item.category_name" />
          </div>

          <!-- Info -->
          <div class="p-3">
            <div class="flex items-center gap-1 mb-1">
              <span :class="marketModeBadgeClass(item)">
                {{ item.market_mode }}
              </span>
              <span :class="surfaceBadgeClass(item)">
                {{ itemSurfaceLabel(item) }}
              </span>
            </div>
            <h3 class="text-xs font-semibold text-slate-900 leading-tight line-clamp-2">{{ item.title }}</h3>
            <p class="text-[10px] text-slate-400 mt-0.5 truncate">{{ item.company_name }}</p>
            <div class="mt-2">
              <span class="text-sm font-bold text-slate-900">{{ formatPrice(item.price_minor, item.currency) }}</span>
              <span class="text-[10px] text-slate-400 ml-0.5">/{{ item.unit }}</span>
            </div>
            <button
              @click.stop="handleCta(item)"
              :class="ctaButtonClass(item)"
            >
              {{ itemCtaLabel(item) }}
            </button>
          </div>
        </div>
      </div>

      <!-- Load more -->
      <div v-if="hasNext" class="py-6 text-center">
        <button @click="loadMore" :disabled="loading" class="text-indigo-600 text-sm font-medium disabled:opacity-50">
          {{ loading ? t('market.loading') : t('market.load_more') }}
        </button>
      </div>
    </div>

    <!-- Bottom navigation bar -->
    <MarketBottomBar />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatMoneyMinor } from '~/utils/currencyPolicy'
import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

definePageMeta({ layout: 'default' })

const config = useRuntimeConfig()
const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const appStore = useAppStore()

interface FeedItem {
  id: string
  title: string
  price_minor: number
  currency: string
  unit: string
  images: string[] | null
  market_mode: string
  min_order_qty: number
  origin_country: string | null
  order_count: number
  category_name: string | null
  company_name: string | null
  company_trust_score: number | null
  is_sponsored: boolean
  is_official?: boolean
  surface?: string
  listing_origin?: string
  item_condition?: string
  warranty_left_months?: number | null
}

interface FilterCat { id: string; name: string; item_count: number }

const items = ref<FeedItem[]>([])
const total = ref(0)
const hasNext = ref(false)
const loading = ref(false)
const feedError = ref('')
const page = ref(1)
const showFilter = ref(false)

const categoryId = ref<string | null>((route.query.category_id as string) || null)
const activeCategoryName = ref<string>((route.query.category_name as string) || '')
const marketMode = ref<string>((route.query.market_mode as string) || '')
const listingOrigin = ref<string>((route.query.listing_origin as string) || '')
const activeSurface = ref<string>(normalizeSurface((route.query.surface as string) || surfaceFromListingOrigin(listingOrigin.value) || 'all'))
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
const budgetMinInput = ref<string>(budgetMinMinor.value ? String(Math.round(Number(budgetMinMinor.value) / 100)) : '')
const budgetMaxInput = ref<string>(budgetMaxMinor.value ? String(Math.round(Number(budgetMaxMinor.value) / 100)) : '')
const merchantType = ref('')
const verifiedOnly = ref(false)
const filterCategories = ref<FilterCat[]>([])
const filterOriginCountries = ref<string[]>([])

const sortOptions = computed(() => [
  { value: 'rank', label: t('market.sort_best') },
  { value: 'newest', label: t('market.sort_new') },
  { value: 'orders', label: t('market.sort_popular') },
  { value: 'price_asc', label: t('market.sort_price_asc') },
  { value: 'price_desc', label: t('market.sort_price_desc') },
])

const sellerTypeOptions = computed(() => [
  { label: t('market.all'), val: '' },
  { label: t('market.individual'), val: 'INDIVIDUAL' },
  { label: t('market.business'), val: 'BUSINESS' },
])

const productSurfaceOptions = computed(() => [
  { value: 'all', label: t('market.surface_all') || t('common.all'), activeClass: 'bg-indigo-600 text-white' },
  { value: 'official', label: t('market.surface_official') || 'Official', activeClass: 'bg-blue-600 text-white' },
  { value: 'market', label: t('market.surface_market') || t('nav.market'), activeClass: 'bg-indigo-600 text-white' },
  { value: 'enterprise_recycled', label: t('market.surface_recycled'), activeClass: 'bg-emerald-600 text-white' },
  { value: 'personal_secondhand', label: t('market.surface_secondhand'), activeClass: 'bg-amber-600 text-white' },
])

onMounted(async () => {
  await appStore.fetchMarketLocalizationConfig()
  await appStore.fetchPaymentRegionConfig(appStore.regionCountry || 'RS')
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

const searchContextChips = computed(() => {
  const chips: string[] = []
  if (activeCategoryName.value) chips.push(`Category: ${activeCategoryName.value}`)
  if (activeSurface.value !== 'all') {
    chips.push(productSurfaceOptions.value.find((item) => item.value === activeSurface.value)?.label || activeSurface.value)
  }
  if (deliveryCountry.value) chips.push(`Country: ${deliveryCountryName.value || countryName(deliveryCountry.value)}`)
  if (deliveryCity.value) chips.push(`City: ${deliveryCity.value}`)
  if (radiusKm.value) chips.push(`Radius: ${radiusKm.value} km`)
  if (budgetMinMinor.value || budgetMaxMinor.value) {
    chips.push(`Budget: ${formatBudgetRange()}`)
  }
  if (latitude.value && longitude.value) chips.push('Location detected')
  return chips
})

async function loadFeed(reset = false) {
  if (reset) { page.value = 1; items.value = [] }
  loading.value = true
  feedError.value = ''
  try {
    const params: Record<string, any> = { page: page.value, page_size: 20, sort: sort.value }
    if (categoryId.value) params.category_id = categoryId.value
    if (marketMode.value) params.market_mode = marketMode.value
    if (activeSurface.value && activeSurface.value !== 'all') params.surface = activeSurface.value
    if (listingOrigin.value && listingOrigin.value !== 'all') params.listing_origin = listingOrigin.value
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
    if (reset) items.value = data.items
    else items.value.push(...data.items)
    total.value = data.total
    hasNext.value = data.has_next
  } catch (e) {
    console.error(e)
    if (reset) items.value = []
    feedError.value = (e as any)?.data?.detail ?? (e as any)?.message ?? 'Marketplace feed request failed.'
    total.value = items.value.length
    hasNext.value = false
  }
  finally { loading.value = false }
}

function setCategoryFilter(id: string | null, name?: string) {
  categoryId.value = id
  activeCategoryName.value = name || ''
  loadFeed(true)
}

function setSurface(value: string) {
  activeSurface.value = normalizeSurface(value)
  listingOrigin.value = ''
  if (activeSurface.value === 'personal_secondhand') marketMode.value = ''
  loadFeed(true)
}

async function loadMore() { page.value++; await loadFeed(false) }

function formatPrice(minor: number, currency: string): string {
  return formatMoneyMinor(minor, currency)
}

function formatBudgetRange() {
  const currency = budgetCurrency.value || appStore.currency
  const min = budgetMinMinor.value ? formatMoneyMinor(Number(budgetMinMinor.value), currency) : '0'
  const max = budgetMaxMinor.value ? formatMoneyMinor(Number(budgetMaxMinor.value), currency) : 'Max'
  return `${min} - ${max}`
}

async function handleDeliveryCountryChange() {
  deliveryCountryName.value = ''
  if (deliveryCountry.value) await appStore.setRegionCountry(deliveryCountry.value)
  loadFeed(true)
}

function applyBudgetFilter() {
  budgetMinMinor.value = budgetMinInput.value ? String(Math.round(Number(budgetMinInput.value) * 100)) : ''
  budgetMaxMinor.value = budgetMaxInput.value ? String(Math.round(Number(budgetMaxInput.value) * 100)) : ''
  budgetCurrency.value = appStore.currency
  loadFeed(true)
  showFilter.value = false
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
  listingOrigin.value = ''
  activeSurface.value = 'all'
  budgetMinInput.value = ''
  budgetMaxInput.value = ''
  latitude.value = ''
  longitude.value = ''
  router.replace(localizedPath('/marketplace'))
  loadFeed(true)
}

function countryName(countryCode: string) {
  const normalized = String(countryCode || '').toUpperCase().slice(0, 2)
  return appStore.regionOptions.find((region) => region.code === normalized)?.label || normalized
}

function localizedPath(path: string) {
  const prefix = getLocalePrefixFromPath(route.path) || (import.meta.client ? localStorage.getItem('h5_locale_prefix') || '' : '')
  return prefix ? withLocalePrefix(path, prefix) : path
}

function handleCta(item: FeedItem) {
  if (isSecondhandItem(item)) {
    openItem(item)
    return
  }
  const authStore = useAuthStore()
  if (!authStore.isLoggedIn) {
    router.push(localizedPath(`/auth/login?return_url=${encodeURIComponent(route.fullPath)}`))
    return
  }
  // Always go to item detail — RFQ/Buy Now bottom sheet is on the detail page
  router.push(localizedPath(`/marketplace/${item.id}`))
}

function openItem(item: FeedItem) {
  router.push(localizedPath(isSecondhandItem(item) ? `/secondhand/${item.id}` : `/marketplace/${item.id}`))
}

function surfaceFromListingOrigin(value: string) {
  const normalized = String(value || '').trim().toLowerCase()
  if (normalized === 'personal_secondhand') return 'personal_secondhand'
  if (normalized === 'enterprise_recycled' || normalized === 'enterprise_refurbished') return 'enterprise_recycled'
  if (normalized === 'new') return 'market'
  return ''
}

function normalizeSurface(value: string) {
  const normalized = String(value || '').trim().toLowerCase()
  if (['official', 'market', 'enterprise_recycled', 'personal_secondhand'].includes(normalized)) return normalized
  if (['secondhand', '2hands', 'used'].includes(normalized)) return 'personal_secondhand'
  if (['recycled', 'enterprise_refurbished'].includes(normalized)) return 'enterprise_recycled'
  return 'all'
}

function isSecondhandItem(item: FeedItem) {
  return ['personal_secondhand', 'enterprise_recycled', 'enterprise_refurbished'].includes(String(item.listing_origin || '').toLowerCase())
}

function itemSurfaceLabel(item: FeedItem) {
  const origin = String(item.listing_origin || 'new').toLowerCase()
  if (origin === 'personal_secondhand') return t('market.surface_secondhand')
  if (origin === 'enterprise_recycled' || origin === 'enterprise_refurbished') return t('market.surface_recycled')
  if ((item as any).is_official) return t('market.surface_official') || 'Official'
  return t('market.surface_new')
}

function surfaceBadgeClass(item: FeedItem) {
  const origin = String(item.listing_origin || 'new').toLowerCase()
  if (origin === 'personal_secondhand') return 'rounded-full bg-amber-50 px-1.5 py-0.5 text-[9px] font-semibold text-amber-700'
  if (origin === 'enterprise_recycled' || origin === 'enterprise_refurbished') return 'rounded-full bg-emerald-50 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-600'
  if ((item as any).is_official) return 'rounded-full bg-blue-50 px-1.5 py-0.5 text-[9px] font-semibold text-blue-600'
  return 'rounded-full bg-slate-50 px-1.5 py-0.5 text-[9px] font-semibold text-slate-500'
}

function marketModeBadgeClass(item: FeedItem) {
  if (item.market_mode === 'B2C') return 'text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-green-50 text-green-600'
  if (item.market_mode === 'C2C') return 'text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-700'
  return 'text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600'
}

function itemCtaLabel(item: FeedItem) {
  if (isSecondhandItem(item)) return t('common.view')
  return item.market_mode === 'B2C' ? t('market.buy_now') : t('market.quote')
}

function ctaButtonClass(item: FeedItem) {
  if (isSecondhandItem(item)) return 'w-full mt-2 py-1.5 rounded-xl text-[11px] font-semibold transition-colors bg-amber-600 text-white'
  return ['w-full mt-2 py-1.5 rounded-xl text-[11px] font-semibold transition-colors', item.market_mode === 'B2C' ? 'bg-green-600 text-white' : 'bg-indigo-600 text-white']
}
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
