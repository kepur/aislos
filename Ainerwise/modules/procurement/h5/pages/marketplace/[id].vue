<template>
  <div v-if="loading" class="min-h-screen flex items-center justify-center bg-slate-50">
    <div class="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
  </div>

  <div v-else-if="!item" class="min-h-screen flex items-center justify-center bg-slate-50">
    <div class="text-center px-6">
      <div class="text-5xl mb-4">🔍</div>
      <p class="text-slate-700 font-semibold mb-1">Product not found</p>
      <NuxtLink to="/marketplace" class="text-indigo-600 text-sm">← Back to Marketplace</NuxtLink>
    </div>
  </div>

  <div v-else class="bg-slate-50 min-h-screen pb-32">
    <!-- Top Nav -->
    <header class="bg-white sticky top-0 z-30 flex items-center gap-3 px-4 py-3 border-b border-slate-100">
      <span class="flex-1 text-sm font-semibold text-slate-800 truncate">{{ item.title }}</span>
      <button @click="wishlist = !wishlist" class="w-8 h-8 flex items-center justify-center text-xl">
        {{ wishlist ? '❤️' : '🤍' }}
      </button>
      <NuxtLink to="/marketplace" class="w-8 h-8 flex items-center justify-center">
        <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </NuxtLink>
    </header>

    <!-- Image -->
    <div class="bg-white">
      <div class="relative aspect-square overflow-hidden">
        <img v-if="item.images?.[activeImg]" :src="item.images[activeImg]" :alt="item.title" class="w-full h-full object-cover" />
        <div v-else class="w-full h-full bg-slate-100 flex items-center justify-center text-7xl">📦</div>
        <div v-if="item.is_sponsored" class="absolute top-3 left-3">
          <span class="bg-amber-400 text-amber-900 text-[10px] font-bold px-2 py-0.5 rounded-full">Ad</span>
        </div>
      </div>
      <div v-if="item.images && item.images.length > 1" class="flex gap-2 px-4 py-3 overflow-x-auto scrollbar-hide">
        <button v-for="(img, i) in item.images" :key="i" @click="activeImg = i"
          :class="['flex-shrink-0 w-14 h-14 rounded-xl overflow-hidden border-2', activeImg === i ? 'border-indigo-500' : 'border-slate-200']">
          <img :src="img" class="w-full h-full object-cover" />
        </button>
      </div>
    </div>

    <!-- Info -->
    <div class="bg-white mt-2 px-4 py-4">
      <div class="flex items-center gap-2 flex-wrap mb-3">
        <span :class="['text-[11px] font-bold px-2.5 py-1 rounded-full', item.market_mode === 'B2C' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700']">{{ item.market_mode }}</span>
        <span v-if="item.origin_country" class="text-[11px] bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">🌍 {{ item.origin_country }}</span>
      </div>
      <h1 class="text-lg font-bold text-slate-900 leading-snug mb-3">{{ item.title }}</h1>
      <div class="flex items-baseline gap-1.5 mb-1">
        <span class="text-2xl font-extrabold text-slate-900">{{ formatPrice(item.price_minor, item.currency) }}</span>
        <span class="text-sm text-slate-400">/ {{ item.unit }}</span>
      </div>
      <div class="flex items-center gap-3 text-xs text-slate-500">
        <span v-if="item.min_order_qty > 1" class="text-amber-600 font-medium">MOQ: {{ item.min_order_qty }} {{ item.unit }}</span>
        <span :class="item.stock_qty > 0 ? 'text-green-600' : 'text-red-500'">
          {{ item.stock_qty > 0 ? `${item.stock_qty.toLocaleString()} in stock` : 'Out of stock' }}
        </span>
      </div>
    </div>

    <!-- Supplier -->
    <div class="bg-white mt-2 px-4 py-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center text-indigo-600 font-bold text-base flex-shrink-0">
          {{ item.company_name?.[0] ?? 'S' }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-slate-800 truncate">{{ item.company_name ?? 'Verified Supplier' }}</p>
          <div class="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
            <span v-if="item.company_trust_score" class="text-amber-500">★ {{ Math.round(item.company_trust_score) }}/100</span>
            <span class="text-green-600">✓ Verified</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Description -->
    <div class="bg-white mt-2 px-4 py-4">
      <h2 class="text-sm font-bold text-slate-800 mb-2">Product Description</h2>
      <p class="text-sm text-slate-600 leading-relaxed whitespace-pre-line">{{ item.description ?? 'No description provided.' }}</p>
    </div>

    <!-- Related -->
    <div v-if="relatedItems.length" class="mt-2 px-4">
      <h2 class="text-sm font-bold text-slate-800 mb-3">More from this Category</h2>
      <div class="grid grid-cols-2 gap-3">
        <NuxtLink v-for="rel in relatedItems" :key="rel.id" :to="`/marketplace/${rel.id}`"
          class="bg-white rounded-2xl overflow-hidden border border-slate-100 active:scale-95 transition-transform">
          <div class="aspect-square overflow-hidden">
            <img v-if="rel.images?.[0]" :src="rel.images[0]" :alt="rel.title" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-slate-50 flex items-center justify-center text-3xl">📦</div>
          </div>
          <div class="p-3">
            <p class="text-xs font-semibold text-slate-800 line-clamp-2">{{ rel.title }}</p>
            <p class="text-sm font-bold text-indigo-600 mt-1">{{ formatPrice(rel.price_minor, rel.currency) }}</p>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>

  <!-- Sticky CTA bar -->
  <div v-if="item" class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-4 py-3 pb-safe flex gap-2 z-40">
    <!-- Back button (thumb-friendly, bottom-left) -->
    <button @click="$router.back()"
      class="w-12 h-12 flex items-center justify-center rounded-2xl border border-slate-200 text-slate-500 active:bg-slate-50 flex-shrink-0">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
    <button v-if="item.market_mode === 'B2C' || item.market_mode === 'BOTH'"
      @click="openBuyNow"
      class="flex-1 bg-green-600 text-white font-semibold py-3.5 rounded-2xl text-sm active:bg-green-700">
      🛒 Buy Now
    </button>
    <button v-if="item.market_mode === 'B2B' || item.market_mode === 'BOTH'"
      @click="openRfq"
      class="flex-1 bg-indigo-600 text-white font-semibold py-3.5 rounded-2xl text-sm active:bg-indigo-700">
      📋 Request Quote
    </button>
  </div>

  <!-- ── B2B RFQ Bottom Sheet ── -->
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="showRfq" class="fixed inset-0 z-[200] flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/40" @click="showRfq = false" />
        <div class="relative bg-white rounded-t-3xl shadow-2xl max-h-[90vh] flex flex-col">
          <div class="flex justify-center pt-3 pb-1"><div class="w-10 h-1 bg-slate-200 rounded-full" /></div>
          <div class="px-5 pb-3 flex items-center justify-between border-b border-slate-100">
            <h3 class="text-base font-bold text-slate-900">📋 Request Quote</h3>
            <button @click="showRfq = false" class="text-slate-400 p-1">✕</button>
          </div>

          <div class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
            <!-- Item preview -->
            <div class="bg-indigo-50 rounded-xl p-3 flex gap-3">
              <div class="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center text-lg flex-shrink-0">📦</div>
              <div class="min-w-0">
                <p class="text-sm font-semibold text-slate-900 truncate">{{ item?.title }}</p>
                <p class="text-xs text-indigo-600">{{ item?.company_name }} · {{ formatPrice(item?.price_minor ?? 0, item?.currency ?? 'PHP') }}/{{ item?.unit }}</p>
              </div>
            </div>

            <!-- Qty -->
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1.5">Quantity ({{ item?.unit }})<span class="text-red-400">*</span></label>
              <input v-model.number="rfq.qty" type="number" :min="item?.min_order_qty ?? 1"
                :placeholder="`Min ${item?.min_order_qty ?? 1}`"
                class="w-full bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none" />
              <p v-if="item?.min_order_qty > 1" class="text-xs text-amber-600 mt-1">MOQ: {{ item?.min_order_qty }} {{ item?.unit }}</p>
            </div>

            <!-- Deal mode -->
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-2">Transaction Mode<span class="text-red-400">*</span></label>
              <div class="grid grid-cols-2 gap-2">
                <button v-for="m in dealModes" :key="m.key" @click="rfq.deal_mode = m.key"
                  :class="['p-3 rounded-xl border-2 text-left transition-all', rfq.deal_mode === m.key ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 bg-white']">
                  <div class="text-lg mb-1">{{ m.icon }}</div>
                  <p class="text-xs font-semibold text-slate-800">{{ m.label }}</p>
                  <p class="text-[10px] text-slate-500 mt-0.5">{{ m.desc }}</p>
                </button>
              </div>
            </div>

            <!-- Delivery address (online only) -->
            <div v-if="rfq.deal_mode === 'ONLINE'" class="space-y-3">
              <label class="block text-xs font-semibold text-slate-700">Delivery Address<span class="text-red-400">*</span></label>
              <!-- Saved addresses -->
              <div v-if="addresses.length" class="space-y-2">
                <button v-for="addr in addresses" :key="addr.id" @click="rfq.address_id = addr.id"
                  :class="['w-full text-left p-3 rounded-xl border-2 transition-all', rfq.address_id === addr.id ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200']">
                  <p class="text-xs font-semibold text-slate-800">{{ addr.label }}</p>
                  <p class="text-[11px] text-slate-500">{{ addr.city }}, {{ addr.state_province }}</p>
                </button>
              </div>
              <!-- Manual city fallback -->
              <div>
                <input v-model="rfq.city" type="text" placeholder="Or type city / area..."
                  class="w-full bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none" />
              </div>
            </div>

            <!-- Notes -->
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1.5">Additional Notes (optional)</label>
              <textarea v-model="rfq.notes" rows="2" placeholder="Specs, brand preference, delivery deadline..."
                class="w-full bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none resize-none" />
            </div>
          </div>

          <div class="px-5 pb-safe pt-3 border-t border-slate-100">
            <p v-if="rfqError" class="text-xs text-red-600 mb-2">{{ rfqError }}</p>
            <button @click="submitRfq" :disabled="rfqLoading || !rfqValid"
              class="w-full bg-indigo-600 text-white font-semibold py-4 rounded-2xl text-sm disabled:opacity-50 active:scale-95 transition-transform">
              {{ rfqLoading ? 'Submitting...' : '🚀 Submit Quote Request' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- ── B2C Buy Now Bottom Sheet ── -->
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="showBuyNow" class="fixed inset-0 z-[200] flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/40" @click="showBuyNow = false" />
        <div class="relative bg-white rounded-t-3xl shadow-2xl max-h-[90vh] flex flex-col">
          <div class="flex justify-center pt-3 pb-1"><div class="w-10 h-1 bg-slate-200 rounded-full" /></div>
          <div class="px-5 pb-3 flex items-center justify-between border-b border-slate-100">
            <h3 class="text-base font-bold text-slate-900">🛒 Buy Now</h3>
            <button @click="showBuyNow = false" class="text-slate-400 p-1">✕</button>
          </div>

          <div class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
            <!-- Item preview -->
            <div class="bg-green-50 rounded-xl p-3 flex gap-3">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-lg flex-shrink-0">🛒</div>
              <div class="min-w-0">
                <p class="text-sm font-semibold text-slate-900 truncate">{{ item?.title }}</p>
                <p class="text-xs text-green-700 font-semibold">{{ formatPrice(item?.price_minor ?? 0, item?.currency ?? 'PHP') }} / {{ item?.unit }}</p>
              </div>
            </div>

            <!-- Qty -->
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1.5">Quantity<span class="text-red-400">*</span></label>
              <div class="flex items-center gap-3">
                <button @click="buy.qty = Math.max(item?.min_order_qty ?? 1, buy.qty - 1)"
                  class="w-10 h-10 rounded-xl bg-slate-100 text-xl font-bold flex items-center justify-center">−</button>
                <input v-model.number="buy.qty" type="number" :min="item?.min_order_qty ?? 1"
                  class="flex-1 text-center bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none font-bold" />
                <button @click="buy.qty++"
                  class="w-10 h-10 rounded-xl bg-slate-100 text-xl font-bold flex items-center justify-center">+</button>
              </div>
              <p class="text-xs text-green-700 font-semibold mt-2 text-center">
                Total: {{ formatPrice((item?.price_minor ?? 0) * buy.qty, item?.currency ?? 'PHP') }}
              </p>
            </div>

            <!-- Delivery address -->
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-2">Delivery Address<span class="text-red-400">*</span></label>
              <div v-if="addresses.length" class="space-y-2">
                <button v-for="addr in addresses" :key="addr.id" @click="buy.address_id = addr.id"
                  :class="['w-full text-left p-3 rounded-xl border-2 transition-all', buy.address_id === addr.id ? 'border-green-500 bg-green-50' : 'border-slate-200']">
                  <p class="text-xs font-semibold text-slate-800">{{ addr.label }}</p>
                  <p class="text-[11px] text-slate-500">{{ addr.contact_name }} · {{ addr.city }}</p>
                </button>
              </div>
              <input v-else v-model="buy.city" type="text" placeholder="Enter delivery city/area"
                class="w-full bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none mt-2" />
            </div>

            <!-- Payment -->
            <div class="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <p class="text-xs font-semibold text-slate-700 mb-1">💳 Payment</p>
              <p class="text-xs text-slate-500">Funds will be held in secure escrow and released when you confirm delivery.</p>
            </div>
          </div>

          <div class="px-5 pb-safe pt-3 border-t border-slate-100">
            <p v-if="buyError" class="text-xs text-red-600 mb-2">{{ buyError }}</p>
            <button @click="submitBuyNow" :disabled="buyLoading || !buyValid"
              class="w-full bg-green-600 text-white font-semibold py-4 rounded-2xl text-sm disabled:opacity-50 active:scale-95 transition-transform">
              {{ buyLoading ? 'Processing...' : `🛒 Confirm Order · ${formatPrice((item?.price_minor ?? 0) * buy.qty, item?.currency ?? 'PHP')}` }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
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
  id: string; title: string; description: string | null
  price_minor: number; currency: string; unit: string
  stock_qty: number; images: string[] | null; tags: string[] | null
  market_mode: string; min_order_qty: number; weight_kg: number | null
  origin_country: string | null; view_count: number; order_count: number
  category_id: string; category_name: string | null
  company_id: string; company_name: string | null
  company_trust_score: number | null; is_sponsored: boolean
}

interface Address {
  id: string; label: string; contact_name: string
  city: string; state_province: string; country_code: string
}

const item = ref<Product | null>(null)
const loading = ref(true)
const activeImg = ref(0)
const wishlist = ref(false)
const relatedItems = ref<Product[]>([])
const addresses = ref<Address[]>([])

// ── RFQ state ──
const showRfq = ref(false)
const rfqLoading = ref(false)
const rfqError = ref('')
const rfq = reactive({ qty: 1, deal_mode: 'ONLINE', address_id: '', city: '', notes: '' })

const dealModes = [
  { key: 'ONLINE', icon: '🔒', label: 'Online (Escrow)', desc: 'Secure escrow, delivery tracking' },
  { key: 'OFFLINE', icon: '🤝', label: 'Offline (Direct)', desc: 'Direct deal, contact supplier' },
]

const rfqValid = computed(() => {
  if (!rfq.qty || rfq.qty < (item.value?.min_order_qty ?? 1)) return false
  if (rfq.deal_mode === 'ONLINE' && !rfq.address_id && !rfq.city) return false
  return true
})

// ── Buy Now state ──
const showBuyNow = ref(false)
const buyLoading = ref(false)
const buyError = ref('')
const buy = reactive({ qty: 1, address_id: '', city: '' })

const buyValid = computed(() => {
  if (!buy.qty || buy.qty < (item.value?.min_order_qty ?? 1)) return false
  if (!buy.address_id && !buy.city) return false
  return true
})

function formatPrice(minor: number, currency: string): string {
  const amount = minor / 100
  if (amount >= 1000000) return `${(amount / 1000000).toFixed(1)}M ${currency}`
  if (amount >= 1000) return `${(amount / 1000).toFixed(1)}k ${currency}`
  return `${amount.toLocaleString()} ${currency}`
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
  } catch {}
}

function openRfq() {
  if (!authStore.isLoggedIn) {
    router.push(`/auth/login?return_url=${encodeURIComponent(route.fullPath)}`)
    return
  }
  rfq.qty = item.value?.min_order_qty ?? 1
  rfqError.value = ''
  showRfq.value = true
}

function openBuyNow() {
  if (!authStore.isLoggedIn) {
    router.push(`/auth/login?return_url=${encodeURIComponent(route.fullPath)}`)
    return
  }
  buy.qty = item.value?.min_order_qty ?? 1
  buyError.value = ''
  showBuyNow.value = true
}

async function submitRfq() {
  if (!item.value || rfqLoading.value) return
  rfqLoading.value = true
  rfqError.value = ''
  try {
    const expiresAt = new Date()
    expiresAt.setDate(expiresAt.getDate() + 7)
    const payload: any = {
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
        catalog_item_id: item.value.id,
        supplier_company_id: item.value.company_id,
        deal_mode: rfq.deal_mode,
        delivery_address_id: rfq.address_id || undefined,
      },
    }
    const intent = await intentStore.createIntent(payload)
    showRfq.value = false
    router.push(`/buyer/requests/${intent.id}?posted=1`)
  } catch (e: any) {
    rfqError.value = e?.data?.detail || 'Failed to submit. Please try again.'
  } finally { rfqLoading.value = false }
}

async function submitBuyNow() {
  if (!item.value || buyLoading.value) return
  buyLoading.value = true
  buyError.value = ''
  try {
    // Create order directly for B2C
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
    showBuyNow.value = false
    router.push(`/buyer/orders/${data.id}`)
  } catch (e: any) {
    buyError.value = e?.data?.detail || 'Order failed. Please try again.'
  } finally { buyLoading.value = false }
}

onMounted(async () => {
  const id = route.params.id as string
  try {
    item.value = await $fetch<Product>(`${config.public.apiBase}/marketplace/items/${id}`)
    if (item.value?.category_id) {
      const feed = await $fetch<{ items: Product[] }>(`${config.public.apiBase}/marketplace/feed`, {
        params: { category_id: item.value.category_id, page_size: 5, sort: 'orders' }
      })
      relatedItems.value = (feed.items ?? []).filter(i => i.id !== item.value!.id).slice(0, 4)
    }
  } catch {
    const demoItem = demoMarketplaceItemById(id) as Product | null
    item.value = demoItem
    relatedItems.value = demoItem
      ? (demoMarketplaceItems as Product[]).filter(i => i.id !== demoItem.id && i.category_id === demoItem.category_id).slice(0, 4)
      : []
  }
  finally { loading.value = false }
  await loadAddresses()
})
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.sheet-enter-active, .sheet-leave-active { transition: all 0.3s cubic-bezier(0.32,0.72,0,1); }
.sheet-enter-from, .sheet-leave-to { transform: translateY(100%); opacity: 0; }
.pb-safe { padding-bottom: env(safe-area-inset-bottom, 16px); }
</style>
