<template>
  <div class="bg-slate-50 min-h-screen pb-32">
    <!-- Top bar -->
    <header class="bg-white sticky top-0 z-30 border-b border-slate-100 px-4 py-3">
      <div class="flex items-center gap-2">
        <div class="flex-1 relative">
          <input
            v-model="keyword"
            type="text"
            :placeholder="activeCategoryName || 'Search products...'"
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

      <!-- Location picker row -->
      <div class="mt-2">
        <CommonLocationPicker
          v-model="userLocation"
          placeholder="Near me (all locations)"
          @update:modelValue="loadFeed(true)"
        />
      </div>

      <!-- Filter chips -->
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
    </header>

    <!-- Filter drawer -->
    <Transition name="slide-down">
      <div v-if="showFilter" class="bg-white border-b border-slate-200 px-4 py-3 space-y-3">
        <!-- Categories -->
        <div>
          <p class="text-xs font-semibold text-slate-500 mb-2">Categories</p>
          <div class="flex flex-wrap gap-2">
            <button
              @click="setCategoryFilter(null); showFilter = false"
              :class="['text-xs px-3 py-1.5 rounded-full border transition-colors', !categoryId ? 'border-indigo-400 text-indigo-600 bg-indigo-50' : 'border-slate-200 text-slate-600']"
            >All</button>
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
          <p class="text-xs font-semibold text-slate-500 mb-2">Seller Type</p>
          <div class="flex gap-2">
            <button
              v-for="t in [{label:'All', val:''},{label:'Individual', val:'INDIVIDUAL'},{label:'Business', val:'BUSINESS'}]"
              :key="t.val"
              @click="merchantType = t.val; loadFeed(true)"
              :class="['text-xs px-3 py-1.5 rounded-full border transition-colors', merchantType === t.val ? 'border-indigo-400 text-indigo-600 bg-indigo-50' : 'border-slate-200 text-slate-600']"
            >{{ t.label }}</button>
          </div>
        </div>
        <!-- Verified Only -->
        <label class="flex items-center gap-2 text-xs text-slate-600">
          <input type="checkbox" v-model="verifiedOnly" @change="loadFeed(true)" class="rounded" />
          Verified businesses only
        </label>
      </div>
    </Transition>

    <!-- Stats bar -->
    <div class="px-4 py-2 text-xs text-slate-400 flex items-center gap-2">
      <span v-if="!loading">{{ total }} products</span>
      <span v-else>Loading...</span>
      <span v-if="activeCategoryName"> in {{ activeCategoryName }}</span>
      <span v-if="userLocation" class="ml-auto flex items-center gap-1 text-indigo-500 font-medium">
        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/></svg>
        Near {{ userLocation.label.split(',')[0] }}
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

      <!-- Empty -->
      <div v-else-if="!loading && items.length === 0" class="text-center py-20">
        <div class="text-5xl mb-3">🔍</div>
        <p class="text-slate-500 text-sm">No products found</p>
        <NuxtLink to="/buyer/post-request" class="mt-3 inline-block text-indigo-600 text-sm font-medium">
          Post a request instead →
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
            <span class="text-[9px] bg-amber-50 text-amber-500 border border-amber-100 rounded-full px-1.5 py-0.5 font-medium">Ad</span>
          </div>

          <!-- Image -->
          <div class="aspect-square">
            <img
              v-if="item.images && item.images[0]"
              :src="item.images[0]"
              :alt="item.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full bg-slate-50 flex items-center justify-center text-3xl">
              📦
            </div>
          </div>

          <!-- Info -->
          <div class="p-3">
            <div class="flex items-center gap-1 mb-1">
              <span :class="['text-[9px] font-semibold px-1.5 py-0.5 rounded-full', item.market_mode === 'B2C' ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600']">
                {{ item.market_mode }}
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
              :class="['w-full mt-2 py-1.5 rounded-xl text-[11px] font-semibold transition-colors', item.market_mode === 'B2C' ? 'bg-green-600 text-white' : 'bg-indigo-600 text-white']"
            >
              {{ item.market_mode === 'B2C' ? 'Buy Now' : 'Quote' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Load more -->
      <div v-if="hasNext" class="py-6 text-center">
        <button @click="loadMore" :disabled="loading" class="text-indigo-600 text-sm font-medium disabled:opacity-50">
          {{ loading ? 'Loading...' : 'Load more' }}
        </button>
      </div>
    </div>

    <!-- Bottom navigation bar -->
    <MarketBottomBar />
  </div>
</template>

<script setup lang="ts">
import { demoMarketplaceItems } from "~/utils/demoData";

definePageMeta({ layout: 'default' })

const config = useRuntimeConfig()
const route = useRoute()
const router = useRouter()

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
}

interface FilterCat { id: string; name: string; item_count: number }

const items = ref<FeedItem[]>([])
const total = ref(0)
const hasNext = ref(false)
const loading = ref(false)
const page = ref(1)
const showFilter = ref(false)

const categoryId = ref<string | null>((route.query.category_id as string) || null)
const activeCategoryName = ref<string>((route.query.category_name as string) || '')
const marketMode = ref('')
const keyword = ref('')
const sort = ref('rank')
const merchantType = ref('')
const verifiedOnly = ref(false)
const filterCategories = ref<FilterCat[]>([])
const userLocation = ref<{ lat: number; lng: number; label: string; regionId?: string } | null>(null)

const sortOptions = [
  { value: 'rank', label: 'Best' },
  { value: 'newest', label: 'New' },
  { value: 'orders', label: 'Popular' },
  { value: 'price_asc', label: 'Price ↑' },
  { value: 'price_desc', label: 'Price ↓' },
]

onMounted(async () => {
  try {
    const f = await $fetch<any>(`${config.public.apiBase}/marketplace/filters`)
    filterCategories.value = f.categories ?? []
  } catch {}
  await loadFeed(true)
})

async function loadFeed(reset = false) {
  if (reset) { page.value = 1; items.value = [] }
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: 20, sort: sort.value }
    if (categoryId.value) params.category_id = categoryId.value
    if (marketMode.value) params.market_mode = marketMode.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (merchantType.value) params.account_type = merchantType.value
    if (verifiedOnly.value) params.verified_only = true
    if (userLocation.value) {
      params.lat = userLocation.value.lat
      params.lng = userLocation.value.lng
      if (userLocation.value.regionId) params.region_id = userLocation.value.regionId
    }

    const data = await $fetch<any>(`${config.public.apiBase}/marketplace/feed`, { params })
    if (reset) items.value = data.items
    else items.value.push(...data.items)
    total.value = data.total
    hasNext.value = data.has_next
  } catch (e) {
    console.error(e)
    const filtered = demoMarketplaceItems.filter((item) => {
      if (categoryId.value && item.category_id !== categoryId.value) return false
      if (marketMode.value && item.market_mode !== marketMode.value) return false
      if (keyword.value.trim() && !item.title.toLowerCase().includes(keyword.value.trim().toLowerCase())) return false
      return true
    })
    if (reset) items.value = filtered
    else items.value.push(...filtered)
    total.value = filtered.length
    hasNext.value = false
  }
  finally { loading.value = false }
}

function setCategoryFilter(id: string | null, name?: string) {
  categoryId.value = id
  activeCategoryName.value = name || ''
  loadFeed(true)
}

async function loadMore() { page.value++; await loadFeed(false) }

function formatPrice(minor: number, currency: string): string {
  const amount = minor / 100
  if (amount >= 1000) return `${(amount / 1000).toFixed(1)}k ${currency}`
  return `${amount.toLocaleString()} ${currency}`
}

function handleCta(item: FeedItem) {
  const authStore = useAuthStore()
  if (!authStore.isLoggedIn) {
    router.push(`/auth/login?return_url=${encodeURIComponent(route.fullPath)}`)
    return
  }
  // Always go to item detail — RFQ/Buy Now bottom sheet is on the detail page
  router.push(`/marketplace/${item.id}`)
}

function openItem(item: FeedItem) {
  router.push(`/marketplace/${item.id}`)
}
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
