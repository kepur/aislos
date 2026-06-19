<template>
  <div v-if="loading" class="min-h-screen flex items-center justify-center">
    <div class="text-slate-400 text-sm">Loading product...</div>
  </div>

  <div v-else-if="!item" class="min-h-screen flex items-center justify-center text-slate-400">
    <div class="text-center">
      <p class="text-lg font-medium">Product not found</p>
      <NuxtLink to="/marketplace" class="text-indigo-600 hover:underline text-sm mt-2 block">Back to Marketplace</NuxtLink>
    </div>
  </div>

  <div v-else class="bg-slate-50 min-h-screen">
    <div class="bg-white border-b border-slate-200 px-6 py-3">
      <div class="mx-auto max-w-7xl flex items-center gap-2 text-sm text-slate-500">
        <NuxtLink to="/marketplace" class="hover:text-indigo-600">Marketplace</NuxtLink>
        <span>/</span>
        <NuxtLink :to="`/marketplace?category_id=${item.category_id}`" class="hover:text-indigo-600">{{ item.category_name }}</NuxtLink>
        <span>/</span>
        <span class="text-slate-800 font-medium truncate max-w-xs">{{ item.title }}</span>
      </div>
    </div>

    <div class="mx-auto max-w-7xl px-6 py-8">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <div>
          <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden aspect-square relative">
            <img v-if="item.images && item.images[activeImg]" :src="item.images[activeImg]" :alt="item.title" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-slate-100 flex items-center justify-center text-6xl">📦</div>
            <span v-if="item.is_sponsored" class="absolute left-4 top-4 rounded-full bg-amber-400 px-3 py-1 text-xs font-bold text-amber-950">Ad</span>
          </div>
          <div v-if="item.images && item.images.length > 1" class="flex gap-2 mt-3">
            <button
              v-for="(img, i) in item.images"
              :key="i"
              @click="activeImg = i"
              :class="['w-16 h-16 rounded-xl overflow-hidden border-2 transition-colors', activeImg === i ? 'border-indigo-500' : 'border-slate-200 hover:border-indigo-300']"
            >
              <img :src="img" class="w-full h-full object-cover" />
            </button>
          </div>
        </div>

        <div class="space-y-5">
          <div class="flex items-center gap-2 flex-wrap">
            <span :class="['text-xs font-bold px-3 py-1.5 rounded-full', item.market_mode === 'B2C' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700']">
              {{ item.market_mode }}
            </span>
            <span v-if="item.origin_country" class="text-xs bg-slate-100 text-slate-600 px-3 py-1.5 rounded-full">
              {{ item.origin_country }}
            </span>
            <span v-for="tag in (item.tags || []).slice(0, 3)" :key="tag" class="text-xs bg-indigo-50 text-indigo-600 px-2.5 py-1 rounded-full">
              {{ tag }}
            </span>
          </div>

          <h1 class="text-3xl font-bold text-slate-900 leading-tight">{{ item.title }}</h1>

          <div class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4">
            <div class="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center text-indigo-600 font-bold text-base">
              {{ item.company_name?.[0] ?? 'S' }}
            </div>
            <div class="min-w-0">
              <p class="text-sm font-semibold text-slate-800 truncate">{{ item.company_name ?? 'Verified Supplier' }}</p>
              <div class="flex items-center gap-3 text-xs text-slate-400">
                <span v-if="item.company_trust_score" class="text-amber-500">Trust {{ Math.round(item.company_trust_score) }}/100</span>
                <span class="text-green-600">Verified</span>
                <span>{{ item.order_count }} orders</span>
                <span>{{ item.view_count.toLocaleString() }} views</span>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-2xl border border-slate-200 p-5">
            <div class="flex items-baseline gap-2 mb-1">
              <span class="text-3xl font-bold text-slate-900">{{ formatPrice(item.price_minor, item.currency) }}</span>
              <span class="text-sm text-slate-400">/ {{ item.unit }}</span>
            </div>
            <p v-if="item.min_order_qty > 1" class="text-sm text-amber-600 font-medium">
              Minimum order: {{ item.min_order_qty }} {{ item.unit }}
            </p>
            <p class="text-sm text-slate-400 mt-1">
              Stock:
              <span :class="item.stock_qty > 0 ? 'text-green-600 font-medium' : 'text-red-500'">
                {{ item.stock_qty > 0 ? `${item.stock_qty.toLocaleString()} available` : 'Out of stock' }}
              </span>
            </p>
          </div>

          <div v-if="item.weight_kg" class="text-xs text-slate-400 flex items-center gap-1">
            <span>Weight: ~{{ item.weight_kg }}kg/unit</span>
            <span class="mx-1">·</span>
            <button type="button" class="text-indigo-600 hover:underline" @click="openRfq">Request shipping quote</button>
          </div>

          <div class="flex gap-3">
            <button
              v-if="canBuyNow"
              class="flex-1 bg-green-600 text-white font-semibold py-4 rounded-2xl hover:bg-green-700 transition-colors text-center text-sm disabled:opacity-50"
              :disabled="item.stock_qty <= 0"
              @click="openBuyNow"
            >
              Buy Now
            </button>
            <button
              v-if="canRequestQuote"
              class="flex-1 bg-indigo-600 text-white font-semibold py-4 rounded-2xl hover:bg-indigo-700 transition-colors text-center text-sm"
              @click="openRfq"
            >
              Request Quote
            </button>
            <button
              class="w-14 h-14 rounded-2xl border border-slate-200 flex items-center justify-center hover:bg-slate-50 text-slate-400 hover:text-red-500 transition-colors flex-shrink-0"
              title="Save to wishlist"
              @click="wishlist = !wishlist"
            >
              {{ wishlist ? '♥' : '♡' }}
            </button>
          </div>

          <div
            v-if="activePanel"
            ref="composerRef"
            class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <div class="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em]" :class="activePanel === 'buy' ? 'text-green-600' : 'text-indigo-600'">
                  {{ activePanel === 'buy' ? 'Direct Purchase' : 'Negotiated Quote' }}
                </p>
                <h3 class="mt-1 text-xl font-bold text-slate-900">
                  {{ activePanel === 'buy' ? 'Buy on this page' : 'Request quote on this page' }}
                </h3>
                <p class="mt-1 text-sm text-slate-500">
                  {{ activePanel === 'buy'
                    ? 'Keep the shopping flow inside the product page. You can cancel anytime and continue browsing.'
                    : 'Ask for a quote without leaving the product page. You can stop anytime and return to browsing.' }}
                </p>
              </div>
              <button type="button" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-500 transition hover:border-slate-300 hover:text-slate-800" @click="closePanel">
                Close
              </button>
            </div>

            <div v-if="activePanel === 'quote'" class="space-y-5 pt-5">
              <div class="rounded-2xl bg-indigo-50 p-4 flex gap-3">
                <div class="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center text-lg flex-shrink-0">📦</div>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-slate-900 truncate">{{ item?.title }}</p>
                  <p class="text-xs text-indigo-600">{{ item?.company_name }} · {{ formatPrice(item?.price_minor ?? 0, item?.currency ?? 'PHP') }}/{{ item?.unit }}</p>
                </div>
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1.5">Quantity ({{ item?.unit }}) <span class="text-red-500">*</span></label>
                <input v-model.number="rfq.qty" type="number" :min="item?.min_order_qty ?? 1" :placeholder="`Min ${item?.min_order_qty ?? 1}`" class="form-input" />
                <p v-if="item?.min_order_qty && item.min_order_qty > 1" class="text-xs text-amber-600 mt-1">MOQ: {{ item.min_order_qty }} {{ item.unit }}</p>
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Transaction Mode <span class="text-red-500">*</span></label>
                <div class="grid grid-cols-2 gap-3">
                  <button
                    v-for="mode in dealModes"
                    :key="mode.key"
                    type="button"
                    @click="rfq.deal_mode = mode.key"
                    :class="['rounded-2xl border-2 p-4 text-left transition-all', rfq.deal_mode === mode.key ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 bg-white hover:border-indigo-200']"
                  >
                    <div class="text-xl mb-2">{{ mode.icon }}</div>
                    <p class="text-sm font-semibold text-slate-900">{{ mode.label }}</p>
                    <p class="mt-1 text-xs text-slate-500">{{ mode.desc }}</p>
                  </button>
                </div>
              </div>

              <div v-if="rfq.deal_mode === 'ONLINE'" class="space-y-3">
                <label class="block text-sm font-semibold text-slate-700">Delivery Address <span class="text-red-500">*</span></label>
                <div v-if="addresses.length" class="grid gap-2">
                  <button
                    v-for="addr in addresses"
                    :key="addr.id"
                    type="button"
                    @click="rfq.address_id = addr.id"
                    :class="['w-full rounded-2xl border-2 p-3 text-left transition-all', rfq.address_id === addr.id ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-200']"
                  >
                    <p class="text-sm font-semibold text-slate-800">{{ addr.label }}</p>
                    <p class="text-xs text-slate-500">{{ addr.contact_name }} · {{ addr.city }} {{ addr.state_province || '' }}</p>
                  </button>
                </div>
                <input v-model="rfq.city" type="text" placeholder="Or type city / area..." class="form-input" />
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1.5">Additional Notes</label>
                <textarea v-model="rfq.notes" rows="3" placeholder="Specs, brand preference, delivery deadline..." class="form-textarea resize-none" />
              </div>

              <div class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">
                The supplier can still contact you in-site. If you do not want to continue, close this panel and keep browsing.
              </div>

              <div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                <button type="button" class="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50" @click="closePanel">
                  Not Now
                </button>
                <button type="button" :disabled="rfqLoading || !rfqValid" class="rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50" @click="submitRfq">
                  {{ rfqLoading ? 'Submitting...' : 'Submit Quote Request' }}
                </button>
              </div>
              <p v-if="rfqError" class="text-sm text-red-600">{{ rfqError }}</p>
            </div>

            <div v-else class="space-y-5 pt-5">
              <div class="rounded-2xl bg-green-50 p-4 flex gap-3">
                <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center text-lg flex-shrink-0">🛒</div>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-slate-900 truncate">{{ item?.title }}</p>
                  <p class="text-xs text-green-700 font-semibold">{{ formatPrice(item?.price_minor ?? 0, item?.currency ?? 'PHP') }} / {{ item?.unit }}</p>
                </div>
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1.5">Quantity <span class="text-red-500">*</span></label>
                <div class="flex items-center gap-3">
                  <button type="button" class="w-11 h-11 rounded-xl bg-slate-100 text-xl font-bold flex items-center justify-center" @click="buy.qty = Math.max(item?.min_order_qty ?? 1, buy.qty - 1)">−</button>
                  <input v-model.number="buy.qty" type="number" :min="item?.min_order_qty ?? 1" class="form-input flex-1 text-center font-bold" />
                  <button type="button" class="w-11 h-11 rounded-xl bg-slate-100 text-xl font-bold flex items-center justify-center" @click="buy.qty++">+</button>
                </div>
                <p class="text-sm text-green-700 font-semibold mt-2 text-center">
                  Total: {{ formatPrice((item?.price_minor ?? 0) * buy.qty, item?.currency ?? 'PHP') }}
                </p>
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Delivery Address <span class="text-red-500">*</span></label>
                <div v-if="addresses.length" class="grid gap-2">
                  <button
                    v-for="addr in addresses"
                    :key="addr.id"
                    type="button"
                    @click="buy.address_id = addr.id"
                    :class="['w-full rounded-2xl border-2 p-3 text-left transition-all', buy.address_id === addr.id ? 'border-green-500 bg-green-50' : 'border-slate-200 hover:border-green-200']"
                  >
                    <p class="text-sm font-semibold text-slate-800">{{ addr.label }}</p>
                    <p class="text-xs text-slate-500">{{ addr.contact_name }} · {{ addr.city }}</p>
                  </button>
                </div>
                <input v-model="buy.city" type="text" placeholder="Or type delivery city / area..." class="form-input mt-2" />
              </div>

              <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p class="text-sm font-semibold text-slate-700 mb-1">Payment</p>
                <p class="text-xs text-slate-500">Order starts as AWAITING_PAYMENT. Buyer can pay from wallet escrow on the order page.</p>
              </div>

              <div class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">
                You are still inside the product page. If you changed your mind, close this section and continue browsing normally.
              </div>

              <div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                <button type="button" class="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50" @click="closePanel">
                  Keep Browsing
                </button>
                <button type="button" :disabled="buyLoading || !buyValid" class="rounded-2xl bg-green-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-green-700 disabled:opacity-50" @click="submitBuyNow">
                  {{ buyLoading ? 'Processing...' : `Confirm Order · ${formatPrice((item?.price_minor ?? 0) * buy.qty, item?.currency ?? 'PHP')}` }}
                </button>
              </div>
              <p v-if="buyError" class="text-sm text-red-600">{{ buyError }}</p>
            </div>
          </div>

          <div class="rounded-2xl border border-indigo-100 bg-indigo-50 p-4 text-xs text-indigo-900">
            <p class="font-semibold">Buyer flow parity with mobile</p>
            <p class="mt-1 text-indigo-800">B2B creates a bound request linked to this catalog item and supplier. B2C creates a direct order and can be paid through escrow from the buyer wallet.</p>
          </div>
        </div>
      </div>

      <div class="mt-10 bg-white rounded-2xl border border-slate-200 p-8">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Product Description</h2>
        <p class="text-slate-600 leading-relaxed whitespace-pre-line">{{ item.description ?? 'No description provided.' }}</p>
      </div>

      <div v-if="relatedItems.length" class="mt-10">
        <h2 class="text-lg font-bold text-slate-800 mb-4">More from this Category</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <NuxtLink
            v-for="rel in relatedItems"
            :key="rel.id"
            :to="`/marketplace/${rel.id}`"
            class="bg-white rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all overflow-hidden group"
          >
            <div class="aspect-square overflow-hidden">
              <img v-if="rel.images?.[0]" :src="rel.images[0]" :alt="rel.title" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
              <div v-else class="w-full h-full bg-slate-100 flex items-center justify-center text-3xl">📦</div>
            </div>
            <div class="p-3">
              <p class="text-xs font-semibold text-slate-800 line-clamp-2">{{ rel.title }}</p>
              <p class="text-sm font-bold text-indigo-600 mt-1">{{ formatPrice(rel.price_minor, rel.currency) }}</p>
            </div>
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>

</template>

<script setup lang="ts">
import { demoMarketplaceItemById, demoMarketplaceItems } from "~/utils/demoData";

definePageMeta({ layout: 'default' })

const config = useRuntimeConfig()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const intentStore = useIntentStore()

interface Product {
  id: string
  title: string
  description: string | null
  price_minor: number
  currency: string
  unit: string
  stock_qty: number
  images: string[] | null
  tags: string[] | null
  market_mode: string
  min_order_qty: number
  weight_kg: number | null
  origin_country: string | null
  view_count: number
  order_count: number
  category_id: string
  category_name: string | null
  company_id: string
  company_name: string | null
  company_trust_score: number | null
  is_sponsored: boolean
}

interface Address {
  id: string
  label: string
  contact_name: string
  city: string
  state_province: string
  country_code: string
}

const item = ref<Product | null>(null)
const loading = ref(true)
const activeImg = ref(0)
const wishlist = ref(false)
const relatedItems = ref<Product[]>([])
const addresses = ref<Address[]>([])
const composerRef = ref<HTMLElement | null>(null)
const activePanel = ref<'buy' | 'quote' | null>(null)

const rfqLoading = ref(false)
const rfqError = ref('')
const rfq = reactive({ qty: 1, deal_mode: 'ONLINE', address_id: '', city: '', notes: '' })

const buyLoading = ref(false)
const buyError = ref('')
const buy = reactive({ qty: 1, address_id: '', city: '' })

const dealModes = [
  { key: 'ONLINE', icon: '🔒', label: 'Online (Escrow)', desc: 'Secure escrow, delivery tracking' },
  { key: 'OFFLINE', icon: '🤝', label: 'Offline (Direct)', desc: 'Direct deal, contact supplier' },
]

const canBuyNow = computed(() => item.value?.market_mode === 'B2C' || item.value?.market_mode === 'BOTH')
const canRequestQuote = computed(() => item.value?.market_mode === 'B2B' || item.value?.market_mode === 'BOTH')

const rfqValid = computed(() => {
  if (!rfq.qty || rfq.qty < (item.value?.min_order_qty ?? 1)) return false
  if (rfq.deal_mode === 'ONLINE' && !rfq.address_id && !rfq.city.trim()) return false
  return true
})

const buyValid = computed(() => {
  if (!buy.qty || buy.qty < (item.value?.min_order_qty ?? 1)) return false
  if (!buy.address_id && !buy.city.trim()) return false
  return true
})

onMounted(async () => {
  try {
    const id = route.params.id as string
    item.value = await $fetch<Product>(`${config.public.apiBase}/marketplace/items/${id}`)

    if (item.value?.category_id) {
      const feed = await $fetch<{ items: Product[] }>(`${config.public.apiBase}/marketplace/feed`, {
        params: { category_id: item.value.category_id, page_size: 5, sort: 'orders' }
      })
      relatedItems.value = (feed.items ?? []).filter(i => i.id !== item.value!.id).slice(0, 4)
    }
  } catch (e) {
    console.error('Product load error', e)
    const demoItem = demoMarketplaceItemById(id) as Product | null
    item.value = demoItem
    relatedItems.value = demoItem
      ? (demoMarketplaceItems as Product[]).filter(i => i.id !== demoItem.id && i.category_id === demoItem.category_id).slice(0, 4)
      : []
  } finally {
    loading.value = false
  }

  await loadAddresses()
  const action = route.query.action
  if (action === 'buy') await openPanel('buy')
  if (action === 'quote') await openPanel('quote')
})

function formatPrice(minor: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(minor / 100)
}

async function loadAddresses() {
  if (!authStore.accessToken) return
  try {
    const data = await $fetch<Address[]>(`${config.public.apiBase}/addresses`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    addresses.value = data ?? []
    if (data?.length) {
      rfq.address_id = data[0].id
      buy.address_id = data[0].id
    }
  } catch {
    addresses.value = []
  }
}

function requireBuyerLogin(action: 'buy' | 'quote') {
  if (authStore.isLoggedIn) return false
  router.push(`/login?return_url=${encodeURIComponent(`/marketplace/${route.params.id}?action=${action}`)}`)
  return true
}

async function syncActionQuery(action: 'buy' | 'quote' | null) {
  const query = { ...route.query }
  if (action) query.action = action
  else delete query.action
  await router.replace({ query })
}

async function openPanel(panel: 'buy' | 'quote') {
  if (requireBuyerLogin(panel)) return
  activePanel.value = panel
  await syncActionQuery(panel)
  await nextTick()
  composerRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function closePanel() {
  activePanel.value = null
  rfqError.value = ''
  buyError.value = ''
  await syncActionQuery(null)
}

async function openRfq() {
  rfq.qty = item.value?.min_order_qty ?? 1
  rfqError.value = ''
  await openPanel('quote')
}

async function openBuyNow() {
  buy.qty = item.value?.min_order_qty ?? 1
  buyError.value = ''
  await openPanel('buy')
}

async function submitRfq() {
  if (!item.value || rfqLoading.value) return
  rfqLoading.value = true
  rfqError.value = ''
  try {
    const expiresAt = new Date()
    expiresAt.setDate(expiresAt.getDate() + 7)
    const payload = {
      category_id: item.value.category_id,
      title: `Quote Request: ${item.value.title}`,
      qty: rfq.qty,
      unit: item.value.unit,
      currency: item.value.currency,
      notes: [
        `Supplier: ${item.value.company_name}`,
        `Item: ${item.value.title}`,
        `Unit Price: ${formatPrice(item.value.price_minor, item.value.currency)}/${item.value.unit}`,
        `Deal Mode: ${rfq.deal_mode}`,
        rfq.notes ? `Notes: ${rfq.notes}` : '',
      ].filter(Boolean).join('\n'),
      city: rfq.city || undefined,
      radius_km: 50,
      expires_at: expiresAt.toISOString(),
      attrs_jsonb: {
        source: 'marketplace_pc',
        catalog_item_id: item.value.id,
        supplier_company_id: item.value.company_id,
        deal_mode: rfq.deal_mode,
        delivery_address_id: rfq.address_id || undefined,
      },
    }
    const intent = await intentStore.createIntent(payload)
    await closePanel()
    router.push(`/buyer/requests/${intent.id}?posted=1`)
  } catch (e: any) {
    rfqError.value = e?.data?.detail || 'Failed to submit. Please try again.'
  } finally {
    rfqLoading.value = false
  }
}

async function submitBuyNow() {
  if (!item.value || buyLoading.value) return
  buyLoading.value = true
  buyError.value = ''
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/orders`, {
      method: 'POST',
      body: {
        catalog_item_id: item.value.id,
        qty: buy.qty,
        delivery_address_id: buy.address_id || undefined,
        delivery_city: buy.city || undefined,
        notes: `B2C Order: ${item.value.title}`,
      },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    await closePanel()
    router.push(`/buyer/orders/${data.id}`)
  } catch (e: any) {
    buyError.value = e?.data?.detail || 'Order failed. Please try again.'
  } finally {
    buyLoading.value = false
  }
}
</script>
