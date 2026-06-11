<template>
  <div class="bg-slate-50 min-h-screen">
    <!-- Top filter bar -->
    <div class="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
      <div class="mx-auto max-w-7xl px-6 py-3 flex flex-wrap items-center gap-3">
        <!-- Breadcrumb / Title -->
        <div class="flex-1 min-w-0">
          <h1 class="text-lg font-bold text-slate-900 truncate">
            {{ activeCategoryName || 'Marketplace' }}
          </h1>
          <p v-if="!loading" class="text-xs text-slate-400">{{ total }} items</p>
        </div>

        <!-- Search -->
        <div class="flex items-center gap-2 flex-wrap">
          <input
            v-model="keyword"
            type="text"
            placeholder="Search products..."
            class="border border-slate-200 rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-300 w-48"
            @keyup.enter="loadFeed(true)"
          />

          <!-- Market Mode -->
          <select v-model="marketMode" @change="loadFeed(true)" class="border border-slate-200 rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-300">
            <option value="">All (B2B + B2C)</option>
            <option value="B2B">B2B Only</option>
            <option value="B2C">B2C Only</option>
          </select>

          <!-- Sort -->
          <select v-model="sort" @change="loadFeed(true)" class="border border-slate-200 rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-300">
            <option value="rank">Best Match</option>
            <option value="newest">Newest</option>
            <option value="orders">Most Orders</option>
            <option value="price_asc">Price ↑</option>
            <option value="price_desc">Price ↓</option>
          </select>

          <button @click="loadFeed(true)" class="bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors">
            Search
          </button>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-7xl px-6 py-6 flex gap-6">
      <!-- Sidebar filters -->
      <aside class="w-52 flex-shrink-0 hidden lg:block">
        <div class="bg-white rounded-2xl border border-slate-200 p-4 sticky top-20">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">Categories</h3>
          <div class="space-y-1">
            <button
              @click="setCategoryFilter(null)"
              :class="['w-full text-left text-sm px-3 py-2 rounded-lg transition-colors', !categoryId ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-50']"
            >
              All Categories
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
            <h3 class="text-sm font-semibold text-slate-700 mb-3">Origin Country</h3>
            <select v-model="originCountry" @change="loadFeed(true)" class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm">
              <option value="">All Countries</option>
              <option v-for="c in filterOriginCountries" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <!-- Seller Type -->
          <div class="mt-4 pt-4 border-t border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">Seller Type</h3>
            <select v-model="merchantType" @change="loadFeed(true)" class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm">
              <option value="">All Sellers</option>
              <option value="INDIVIDUAL">Individual / Freelancer</option>
              <option value="BUSINESS">Business / Company</option>
            </select>
          </div>

          <!-- Verified Only -->
          <div class="mt-3 flex items-center gap-2">
            <input id="verified-only" type="checkbox" v-model="verifiedOnly" @change="loadFeed(true)" class="rounded border-slate-300" />
            <label for="verified-only" class="text-sm text-slate-600 cursor-pointer">Verified businesses only</label>
          </div>
        </div>
      </aside>

      <!-- Feed Grid -->
      <main class="flex-1 min-w-0">
        <!-- Loading skeleton -->
        <div v-if="loading && items.length === 0" class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
          <div v-for="i in 8" :key="i" class="bg-white rounded-2xl border border-slate-200 p-4 animate-pulse">
            <div class="aspect-square bg-slate-100 rounded-xl mb-3"></div>
            <div class="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
            <div class="h-3 bg-slate-100 rounded w-1/2"></div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else-if="!loading && items.length === 0" class="text-center py-24 text-slate-400">
          <div class="text-5xl mb-4">🔍</div>
          <p class="text-lg font-medium">No products found</p>
          <p class="text-sm mt-1">Try adjusting your filters or <NuxtLink to="/post-request" class="text-indigo-600 hover:underline">post a request</NuxtLink></p>
        </div>

        <!-- Items grid -->
        <div v-else class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="item in items"
            :key="item.id"
            class="bg-white rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer group"
            @click="router.push(`/marketplace/${item.id}`)"
          >
            <!-- Sponsored badge -->
            <div v-if="item.is_sponsored" class="px-3 pt-2">
              <span class="text-[10px] bg-amber-50 text-amber-600 border border-amber-200 rounded-full px-2 py-0.5 font-medium">Sponsored</span>
            </div>

            <!-- Image -->
            <div class="aspect-square overflow-hidden" :class="item.is_sponsored ? 'rounded-t-none' : 'rounded-t-2xl'">
              <img
                v-if="item.images && item.images[0]"
                :src="item.images[0]"
                :alt="item.title"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div v-else class="w-full h-full bg-slate-100 flex items-center justify-center text-4xl">
                {{ getCategoryEmoji(item.category_name) }}
              </div>
            </div>

            <!-- Info -->
            <div class="p-4">
              <!-- Market mode badge -->
              <div class="flex items-center gap-1.5 mb-2">
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
                <span v-if="item.min_order_qty > 1" class="text-[10px] text-slate-400">MOQ: {{ item.min_order_qty }}</span>
                <span v-if="item.company_trust_score" class="text-[10px] text-amber-600">★ {{ Math.round(item.company_trust_score) }}</span>
                <span v-if="item.order_count > 0" class="text-[10px] text-slate-400 ml-auto">{{ item.order_count }} orders</span>
              </div>

              <!-- CTA button -->
              <button
                @click.stop="handleCta(item)"
                :class="['w-full mt-3 py-2 rounded-xl text-xs font-semibold transition-colors', item.market_mode === 'B2C' ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-indigo-600 text-white hover:bg-indigo-700']"
              >
                {{ item.market_mode === 'B2C' ? 'Buy Now' : 'Request Quote' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Load more -->
        <div v-if="hasNext" class="mt-8 text-center">
          <button
            @click="loadMore"
            :disabled="loading"
            class="bg-white border border-slate-200 text-slate-700 px-8 py-3 rounded-xl font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <span v-if="loading">Loading...</span>
            <span v-else>Load More</span>
          </button>
        </div>
      </main>
    </div>
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
const page = ref(1)

// Filters
const categoryId = ref<string | null>((route.query.category_id as string) || null)
const activeCategoryName = ref<string>((route.query.category_name as string) || '')
const marketMode = ref<string>('')
const keyword = ref<string>('')
const sort = ref<string>('rank')
const originCountry = ref<string>('')

const merchantType = ref<string>('')
const verifiedOnly = ref<boolean>(false)

// Filter options from API
const filterCategories = ref<FilterCat[]>([])
const filterOriginCountries = ref<string[]>([])

// Load filter options
onMounted(async () => {
  try {
    const f = await $fetch<any>(`${config.public.apiBase}/marketplace/filters`)
    filterCategories.value = f.categories ?? []
    filterOriginCountries.value = f.origin_countries ?? []
  } catch {}
  await loadFeed(true)
})

async function loadFeed(reset = false) {
  if (reset) {
    page.value = 1
    items.value = []
  }
  loading.value = true
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
    const filtered = demoMarketplaceItems.filter((item) => {
      if (categoryId.value && item.category_id !== categoryId.value) return false
      if (marketMode.value && item.market_mode !== marketMode.value) return false
      if (keyword.value.trim() && !item.title.toLowerCase().includes(keyword.value.trim().toLowerCase())) return false
      if (originCountry.value && item.origin_country !== originCountry.value) return false
      return true
    }) as FeedItem[]
    if (reset) {
      items.value = filtered
    } else {
      items.value.push(...filtered)
    }
    total.value = filtered.length
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

async function loadMore() {
  page.value++
  await loadFeed(false)
}

function formatPrice(minor: number, currency: string): string {
  const amount = minor / 100
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency || 'USD', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(amount)
}

function getCategoryEmoji(categoryName: string | null): string {
  if (!categoryName) return '📦'
  const lower = categoryName.toLowerCase()
  if (lower.includes('construct')) return '🏗️'
  if (lower.includes('it') || lower.includes('office')) return '💻'
  if (lower.includes('auto')) return '🚗'
  if (lower.includes('electron')) return '⚡'
  if (lower.includes('machin')) return '⚙️'
  if (lower.includes('chemical') || lower.includes('material')) return '🧪'
  if (lower.includes('textile') || lower.includes('garment')) return '👕'
  if (lower.includes('food') || lower.includes('bev')) return '🍜'
  if (lower.includes('agri')) return '🌾'
  if (lower.includes('medical') || lower.includes('health')) return '🏥'
  if (lower.includes('furniture')) return '🪑'
  if (lower.includes('energy') || lower.includes('solar')) return '☀️'
  if (lower.includes('tool') || lower.includes('hardware')) return '🔨'
  return '📦'
}

function handleCta(item: FeedItem) {
  const action = item.market_mode === 'B2C' ? 'buy' : 'quote'
  router.push(`/marketplace/${item.id}?action=${action}`)
}
</script>
