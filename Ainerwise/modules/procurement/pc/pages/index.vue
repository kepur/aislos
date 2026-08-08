<template>
  <div>
    <!-- Hero Section -->
    <section class="bg-indigo-900 text-white py-20 lg:py-32 relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-b from-indigo-900/50 to-indigo-900"></div>

      <div class="container mx-auto px-4 relative z-10 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <h1 class="text-4xl lg:text-6xl font-bold tracking-tight mb-6 leading-tight">
            Shop first. <br />
            <span class="text-indigo-300">Use AI when the product path is not enough.</span>
          </h1>
          <p class="text-lg lg:text-xl text-indigo-100 mb-8 max-w-2xl leading-relaxed">
            AinerWise Market is the shopping front for official products, market listings, enterprise recycled stock and supplier quotes. Browse products first; turn complex needs into RFQ when shopping is not enough.
          </p>
          <div class="flex flex-col sm:flex-row gap-4">
            <UButton size="xl" color="white" variant="solid" :to="localizedPath('/marketplace')" class="justify-center px-8 text-indigo-900 font-semibold shadow-lg hover:shadow-xl transition-shadow">
              Browse Market
            </UButton>
            <UButton size="xl" color="indigo" variant="outline" class="justify-center px-8 border-indigo-400 text-white hover:bg-indigo-800" :to="localizedPath('/post-request')">
              AI / RFQ Request
            </UButton>
          </div>

          <div class="mt-10 flex items-center space-x-6 text-sm text-indigo-200">
            <div class="flex items-center"><UIcon name="i-heroicons-shopping-bag" class="w-5 h-5 mr-2 text-green-400" /> Products first</div>
            <div class="flex items-center"><UIcon name="i-heroicons-sparkles" class="w-5 h-5 mr-2 text-blue-400" /> AI RFQ when needed</div>
            <div class="hidden lg:flex items-center"><UIcon name="i-heroicons-arrow-path-rounded-square" class="w-5 h-5 mr-2 text-amber-300" /> New + reused stock</div>
          </div>
        </div>

        <!-- Quick Request Panel -->
        <div class="bg-white rounded-2xl shadow-2xl p-6 lg:p-8 text-slate-900 max-w-md mx-auto w-full">
          <h3 class="text-2xl font-semibold mb-6">What are you looking for?</h3>
          <form @submit.prevent="handleHeroSearch" class="hero-quick-search space-y-4">
            <!-- Category -->
            <div class="space-y-1">
              <label class="block text-sm font-medium text-slate-700">Category</label>
              <select v-model="heroForm.category"
                class="w-full rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 appearance-none">
                <option value="">Select category</option>
                <option v-for="cat in categoryOptions" :key="cat.value" :value="cat.value">
                  {{ cat.name }}{{ cat.item_count ? ` (${cat.item_count})` : '' }}
                </option>
              </select>
            </div>

            <!-- Budget row -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">Min Budget ({{ appStore.currency }})</label>
                <div class="relative">
                  <span class="pointer-events-none absolute left-3 top-1/2 z-10 flex -translate-y-1/2 items-center text-sm text-slate-400">{{ budgetCurrencySymbol }}</span>
                  <input v-model="heroForm.budgetMin" type="number" placeholder="0" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white py-3 pl-8 pr-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
              </div>
              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">Max Budget ({{ appStore.currency }})</label>
                <div class="relative">
                  <span class="pointer-events-none absolute left-3 top-1/2 z-10 flex -translate-y-1/2 items-center text-sm text-slate-400">{{ budgetCurrencySymbol }}</span>
                  <input v-model="heroForm.budgetMax" type="number" placeholder="Max" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white py-3 pl-8 pr-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
              </div>
            </div>

            <!-- Country -->
            <div class="space-y-1">
              <label class="block text-sm font-medium text-slate-700">Delivery Country</label>
              <select
                v-model="heroForm.country"
                class="w-full rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 appearance-none"
              >
                <option v-for="region in regionOptions" :key="region.code" :value="region.code">
                  {{ region.label }} ({{ region.code }})
                </option>
              </select>
              <p class="text-xs text-slate-500">
                Budget uses {{ budgetCurrencyLabel }}. Local country rules are managed by Admin.
              </p>
            </div>

            <!-- Delivery Location -->
            <div class="space-y-1">
              <div class="flex items-center justify-between gap-3">
                <label class="block text-sm font-medium text-slate-700">Delivery Location</label>
                <button
                  type="button"
                  class="inline-flex items-center gap-1 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="locationStatus === 'loading'"
                  @click="detectBrowserLocation"
                >
                  <UIcon name="i-heroicons-map-pin" class="h-4 w-4" />
                  {{ locationStatus === 'loading' ? 'Detecting...' : 'Use current location' }}
                </button>
              </div>
              <div class="relative">
                <span class="pointer-events-none absolute left-3 top-1/2 z-10 flex -translate-y-1/2 items-center">
                  <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </span>
                <input v-model="heroForm.location" type="text" placeholder="Enter city or area"
                  class="w-full rounded-lg border border-slate-200 bg-white py-3 pl-10 pr-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
              </div>
              <p v-if="locationMessage" class="text-xs" :class="locationStatus === 'error' ? 'text-amber-600' : 'text-slate-500'">
                {{ locationMessage }}
              </p>
            </div>

            <!-- Search Radius -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="block text-sm font-medium text-slate-700">Search Radius</label>
                <span class="text-sm font-semibold text-indigo-600">{{ heroForm.radius }} km</span>
              </div>
              <input v-model="heroForm.radius" type="range" min="1" max="200" step="1"
                class="range-input w-full h-2 rounded-full bg-slate-200 appearance-none cursor-pointer accent-indigo-600" />
              <div class="flex justify-between text-xs text-slate-400">
                <span>1 km</span>
                <span>200 km</span>
              </div>
            </div>

            <UButton type="submit" color="indigo" block size="xl" class="mt-6 text-white shadow-md">
              Find Suppliers
            </UButton>
          </form>
        </div>
      </div>
    </section>

    <!-- Market preview -->
    <section class="py-16 bg-white">
      <div class="container mx-auto px-4">
        <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-8">
          <div>
            <p class="text-sm font-bold uppercase tracking-[0.18em] text-indigo-600">AinerWise Market</p>
            <h2 class="mt-2 text-3xl font-bold text-slate-900">Browse products before posting a request</h2>
            <p class="mt-2 text-slate-600 max-w-2xl">Official products, supplier market listings and recycled inventory share the same Core data. Product condition is a filter, not a separate second-hand portal.</p>
          </div>
          <div class="flex flex-wrap gap-3">
            <UButton :to="localizedPath('/marketplace')" color="indigo" size="lg">Open Marketplace</UButton>
            <UButton :to="localizedPath('/post-request')" color="gray" variant="outline" size="lg">Post AI Request</UButton>
          </div>
        </div>

        <div v-if="marketPreviewLoading" class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="idx in 4" :key="idx" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div class="aspect-[4/3] animate-pulse rounded-xl bg-slate-200"></div>
            <div class="mt-4 h-4 w-3/4 animate-pulse rounded bg-slate-200"></div>
            <div class="mt-2 h-3 w-1/2 animate-pulse rounded bg-slate-100"></div>
          </div>
        </div>
        <div v-else-if="marketPreviewError" class="rounded-2xl border border-red-100 bg-red-50 p-6 text-center text-red-700">
          <p class="font-semibold">Marketplace preview could not load.</p>
          <p class="mt-1 text-sm">{{ marketPreviewError }}</p>
          <button class="mt-4 rounded-xl bg-red-600 px-5 py-2 text-sm font-semibold text-white" @click="loadMarketPreview">Retry</button>
        </div>
        <div v-else-if="featuredProducts.length" class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <NuxtLink
            v-for="item in featuredProducts"
            :key="item.id"
            :to="localizedPath(`/marketplace/${item.id}`)"
            class="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-lg"
          >
            <div class="aspect-[4/3] overflow-hidden bg-slate-100">
              <img
                v-if="item.images && item.images[0]"
                :src="item.images[0]"
                :alt="item.title"
                class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <MarketItemVisual v-else :title="item.title" :category-name="item.category_name" />
            </div>
            <div class="p-4">
              <div class="mb-2 flex flex-wrap items-center gap-1.5">
                <span v-if="item.is_official" class="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700">Official</span>
                <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600">{{ item.market_mode }}</span>
                <span v-if="item.condition_label" class="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700">{{ item.condition_label }}</span>
              </div>
              <h3 class="line-clamp-2 text-sm font-bold leading-snug text-slate-900 group-hover:text-indigo-700">{{ item.title }}</h3>
              <p class="mt-2 text-base font-extrabold text-slate-950">{{ formatPrice(item.price_minor, item.currency) }}</p>
            </div>
          </NuxtLink>
        </div>
        <div v-else class="rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center text-slate-500">
          No marketplace products are published yet.
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="py-20 bg-white">
      <div class="container mx-auto px-4">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-slate-900 mb-4">How AISLOS Market Works</h2>
          <p class="text-lg text-slate-600 max-w-2xl mx-auto">The secure reverse marketplace that saves you time and protects your money.</p>
        </div>

        <div class="grid md:grid-cols-5 gap-8 relative">
          <div class="hidden md:block absolute top-1/2 left-0 w-full h-0.5 bg-indigo-100 -translate-y-1/2 z-0"></div>

          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-pencil-square" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">1. Post Request</h4>
            <p class="text-sm text-slate-600">Describe what you need, set budget & location.</p>
          </div>

          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-envelope-open" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">2. Receive Offers</h4>
            <p class="text-sm text-slate-600">Verified suppliers ping you with exact quotes.</p>
          </div>

          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-scale" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">3. Compare & Select</h4>
            <p class="text-sm text-slate-600">Compare by price, distance, and supplier rating.</p>
          </div>

          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-clipboard-document-check" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">4. Award &amp; Order</h4>
            <p class="text-sm text-slate-600">Award an offer — a milestone payment plan is recorded.</p>
          </div>

          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-green-100 text-green-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-check-badge" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">5. Deliver &amp; Confirm</h4>
            <p class="text-sm text-slate-600">Confirm each milestone as work is delivered — items become tracked assets.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Categories -->
    <section class="py-20 bg-slate-50">
      <div class="container mx-auto px-4">
        <div class="flex justify-between items-end mb-10">
          <div>
            <h2 class="text-3xl font-bold text-slate-900 mb-2">Popular Categories</h2>
            <p class="text-slate-600">Find exactly what you need from specialized suppliers.</p>
          </div>
          <UButton :to="localizedPath('/marketplace')" variant="ghost" color="indigo" trailing-icon="i-heroicons-arrow-right">View all in Market</UButton>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <NuxtLink
            v-for="cat in homepageCategories"
            :key="cat.value"
            :to="categoryMarketplacePath(cat)"
            class="bg-white rounded-xl p-6 border border-slate-200 hover:border-indigo-300 hover:shadow-lg transition-all cursor-pointer group"
          >
            <div class="w-12 h-12 bg-slate-100 rounded-lg mb-4 flex items-center justify-center group-hover:bg-indigo-50 group-hover:text-indigo-600 text-slate-500 transition-colors">
              <UIcon name="i-heroicons-cube" class="w-6 h-6" />
            </div>
            <h4 class="font-semibold text-slate-900">{{ cat.name }}</h4>
            <p v-if="cat.item_count" class="mt-2 text-xs text-slate-400">{{ cat.item_count }} products</p>
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { currencyMeta, currencyOptionLabel } from '~/utils/currencyPolicy'
import { inferLocationFromCoords, inferLocationFromTimezone, type LocationGuess } from '~/utils/geoPolicy'

// Landing Page
const router = useRouter()
const config = useRuntimeConfig()
const appStore = useAppStore()

type QuickCategory = {
  id?: string
  name: string
  value: string
  item_count?: number
}

type FeedItem = {
  id: string
  title: string
  price_minor: number
  currency: string
  images: string[] | null
  market_mode: string
  category_name: string | null
  is_official?: boolean
  condition_label?: string | null
}

const fallbackCategories: QuickCategory[] = [
  'KNX & Building Automation',
  'Energy Storage & Batteries',
  'CCTV',
  'Access Control',
  'Smart Panels',
  'Service Packages',
  'Enterprise Recycled',
  'Custom Requests',
].map((name) => ({ name, value: `name:${name}` }))

const loadedCategories = ref<QuickCategory[]>([])
const featuredProducts = ref<FeedItem[]>([])
const marketPreviewLoading = ref(false)
const marketPreviewError = ref('')
const locationStatus = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const locationMessage = ref('')

const heroForm = reactive({
  category: '',
  budgetMin: '',
  budgetMax: '',
  location: '',
  country: 'RS',
  radius: 25,
  latitude: null as number | null,
  longitude: null as number | null,
})

const categoryOptions = computed(() => loadedCategories.value.length ? loadedCategories.value : fallbackCategories)
const homepageCategories = computed(() => categoryOptions.value.slice(0, 8))
const budgetCurrencySymbol = computed(() => currencyMeta(appStore.currency).symbol || appStore.currency)
const budgetCurrencyLabel = computed(() => currencyOptionLabel(appStore.currency))
const regionOptions = computed(() => appStore.regionOptions.map((region) => ({
  code: String(region.code || '').toUpperCase().slice(0, 2),
  label: region.label || region.code,
})))
const selectedCategory = computed(() => categoryOptions.value.find((cat) => cat.value === heroForm.category) || null)
const selectedRegion = computed(() => regionOptions.value.find((region) => region.code === heroForm.country) || null)

watch(regionOptions, (options) => {
  if (!options.length) return
  if (!options.some((region) => region.code === heroForm.country)) {
    heroForm.country = options[0].code
  }
}, { immediate: true })

watch(() => appStore.regionCountry, (country) => {
  const normalized = String(country || '').toUpperCase().slice(0, 2)
  if (normalized && normalized !== heroForm.country) heroForm.country = normalized
}, { immediate: true })

watch(() => heroForm.country, async (country) => {
  const normalized = String(country || '').toUpperCase().slice(0, 2)
  if (normalized && normalized !== appStore.regionCountry) {
    await appStore.setRegionCountry(normalized)
  }
})

onMounted(async () => {
  await Promise.all([loadCategoryOptions(), loadMarketPreview()])
  applyTimezoneDefault()
})

async function loadCategoryOptions() {
  try {
    const filters = await $fetch<any>(`${config.public.apiBase}/marketplace/filters`)
    const categories = Array.isArray(filters?.categories) ? filters.categories : []
    loadedCategories.value = categories
      .map((cat: any) => ({
        id: cat.id ? String(cat.id) : '',
        name: String(cat.name || cat.slug || '').trim(),
        value: cat.id ? String(cat.id) : `name:${String(cat.name || cat.slug || '').trim()}`,
        item_count: Number(cat.item_count || 0),
      }))
      .filter((cat: QuickCategory) => cat.name && cat.value)
  } catch {
    loadedCategories.value = []
  }
}

async function loadMarketPreview() {
  marketPreviewLoading.value = true
  marketPreviewError.value = ''
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/marketplace/feed`, {
      params: {
        page: 1,
        page_size: 8,
        sort: 'rank',
      },
    })
    featuredProducts.value = Array.isArray(data?.items) ? data.items.slice(0, 8) : []
  } catch (e: any) {
    featuredProducts.value = []
    marketPreviewError.value = e?.data?.detail || e?.message || 'Marketplace feed request failed.'
  } finally {
    marketPreviewLoading.value = false
  }
}

function applyTimezoneDefault() {
  if (!import.meta.client) return
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone
  const guess = inferLocationFromTimezone(timeZone, regionOptions.value)
  if (guess) {
    applyLocationGuess(guess, false)
  }
}

async function detectBrowserLocation() {
  if (!import.meta.client || !navigator.geolocation) {
    locationStatus.value = 'error'
    locationMessage.value = 'Browser location is not available. Please choose country and city manually.'
    return
  }

  locationStatus.value = 'loading'
  locationMessage.value = ''
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const latitude = position.coords.latitude
      const longitude = position.coords.longitude
      heroForm.latitude = latitude
      heroForm.longitude = longitude
      const guess = inferLocationFromCoords(latitude, longitude, regionOptions.value)
      if (guess) {
        applyLocationGuess(guess, true)
        locationStatus.value = 'success'
        locationMessage.value = `Detected ${guess.city || guess.countryName}. You can still edit the city before searching.`
        return
      }

      const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone
      const timeZoneGuess = inferLocationFromTimezone(timeZone, regionOptions.value)
      if (timeZoneGuess) {
        applyLocationGuess(timeZoneGuess, false)
        locationStatus.value = 'success'
        locationMessage.value = `Location permission worked, but country was inferred from your browser timezone. Please confirm the city.`
        return
      }

      locationStatus.value = 'error'
      locationMessage.value = 'Your coordinates are outside the currently open countries. Please select an operating country manually.'
    },
    () => {
      locationStatus.value = 'error'
      locationMessage.value = 'Location permission was denied or timed out. Manual country and city selection still works.'
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
  )
}

function applyLocationGuess(guess: LocationGuess, overwriteCity: boolean) {
  if (guess.countryCode) heroForm.country = guess.countryCode
  if (guess.city && (overwriteCity || !heroForm.location.trim())) {
    heroForm.location = guess.city
  }
}

function localizedPath(path: string) {
  return appStore.localizedPath(path)
}

function handleHeroSearch() {
  const q = new URLSearchParams()
  if (selectedCategory.value?.id) q.set('category_id', selectedCategory.value.id)
  if (selectedCategory.value?.name) q.set('category_name', selectedCategory.value.name)
  if (selectedCategory.value?.name && !selectedCategory.value?.id) q.set('keyword', selectedCategory.value.name)
  if (heroForm.budgetMin) q.set('budget_min_minor', String(Math.round(Number(heroForm.budgetMin) * 100)))
  if (heroForm.budgetMax) q.set('budget_max_minor', String(Math.round(Number(heroForm.budgetMax) * 100)))
  if (heroForm.budgetMin || heroForm.budgetMax) q.set('budget_currency', appStore.currency)
  if (heroForm.country) {
    q.set('country', heroForm.country)
    q.set('delivery_country', heroForm.country)
    if (selectedRegion.value?.label) q.set('delivery_country_name', selectedRegion.value.label)
  }
  if (heroForm.location.trim()) {
    q.set('city', heroForm.location.trim())
    q.set('delivery_city', heroForm.location.trim())
  }
  if (heroForm.radius !== 25) q.set('radius_km', String(heroForm.radius))
  if (heroForm.latitude != null && heroForm.longitude != null) {
    q.set('lat', String(heroForm.latitude))
    q.set('lng', String(heroForm.longitude))
  }

  const target = q.toString() ? `/marketplace?${q.toString()}` : '/marketplace'
  router.push(appStore.localizedPath(target))
}

function categoryMarketplacePath(cat: QuickCategory) {
  const q = new URLSearchParams()
  if (cat.id) q.set('category_id', cat.id)
  if (cat.name) q.set('category_name', cat.name)
  if (!cat.id && cat.name) q.set('keyword', cat.name)
  const suffix = q.toString()
  return appStore.localizedPath(suffix ? `/marketplace?${suffix}` : '/marketplace')
}

function formatPrice(minor: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format((Number(minor) || 0) / 100)
}
</script>

<style scoped>
.hero-quick-search .range-input {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
}

.hero-quick-search .range-input::-webkit-slider-runnable-track {
  height: 0.5rem;
  border-radius: 999px;
  background: #cbd5e1;
}

.hero-quick-search .range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 1rem;
  height: 1rem;
  margin-top: -0.25rem;
  border-radius: 999px;
  border: 2px solid #ffffff;
  background: #4f46e5;
  box-shadow: 0 1px 4px rgb(15 23 42 / 0.28);
}

.hero-quick-search .range-input::-moz-range-track {
  height: 0.5rem;
  border-radius: 999px;
  background: #cbd5e1;
}

.hero-quick-search .range-input::-moz-range-thumb {
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  border: 2px solid #ffffff;
  background: #4f46e5;
  box-shadow: 0 1px 4px rgb(15 23 42 / 0.28);
}
</style>
