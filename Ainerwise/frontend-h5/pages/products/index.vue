<template>
  <div class="px-4 py-4">
    <h1 class="text-lg font-bold text-slate-800 mb-1">{{ $t('products.title') }}</h1>
    <p class="text-xs text-slate-400 mb-4">{{ $t('products.subtitle') }}</p>
    <div class="mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-3">
      <p class="text-[10px] font-bold uppercase tracking-wider text-blue-500">China Tier-1 Supply Chain</p>
      <p class="mt-1 text-xs leading-relaxed text-slate-600">
        Project-grade ecosystem examples: Huawei Digital Power, Sungrow, LONGi, Xiaomi ecosystem,
        leading CCTV/access vendors, and verified OEM/ODM partners.
      </p>
    </div>

    <!-- Search -->
    <div class="relative mb-4">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
      </svg>
      <input v-model="search" type="text" :placeholder="$t('products.searchPlaceholder')"
        class="w-full pl-9 pr-4 py-2.5 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300" />
    </div>

    <div v-if="loading" class="py-12 text-center text-sm text-slate-400">
      Loading products...
    </div>

    <div v-else-if="error" class="rounded-2xl border border-red-100 bg-red-50 p-4 text-center">
      <p class="text-sm font-semibold text-red-700">Products could not be loaded.</p>
      <p class="mt-1 text-xs text-red-500">{{ error }}</p>
      <button type="button" class="mt-3 rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white" @click="loadProducts">
        Retry
      </button>
    </div>

    <div v-else-if="filteredProducts.length" class="grid grid-cols-2 gap-3">
      <NuxtLink
        v-for="product in filteredProducts"
        :key="product.id || product.slug"
        :to="`/products/${product.slug || product.id}`"
        class="bg-white rounded-xl overflow-hidden border border-slate-100 shadow-sm active:shadow-none transition"
      >
        <div class="h-28 bg-slate-50 flex items-center justify-center">
          <img v-if="firstProductImage(product)" :src="firstProductImage(product)" :alt="product.name" class="w-full h-full object-cover" />
          <svg v-else class="w-10 h-10 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1">
            <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5a1.5 1.5 0 0 0 1.5-1.5V5.25a1.5 1.5 0 0 0-1.5-1.5H3.75a1.5 1.5 0 0 0-1.5 1.5v14.25c0 .828.672 1.5 1.5 1.5Z" />
          </svg>
        </div>
        <div class="p-3">
          <h3 class="text-xs font-semibold text-slate-800 line-clamp-2">{{ product.name }}</h3>
          <p v-if="product.brand" class="text-[10px] text-slate-400 mt-1">{{ product.brand }}</p>
          <p v-if="product.supply_tier" class="mt-1 text-[10px] text-emerald-600 line-clamp-2">{{ product.supply_tier }}</p>
          <div class="mt-2 flex items-center justify-between gap-2">
            <span v-if="product.list_price" class="text-[11px] font-bold text-blue-600">€{{ product.list_price }} ref.</span>
            <span v-else class="text-[11px] font-semibold text-blue-600">Project quote</span>
            <span v-if="product.warranty_years" class="text-[10px] text-slate-400">{{ product.warranty_years }}y warranty</span>
          </div>
          <div v-if="product.lifecycle_pricing_json?.length" class="mt-1 text-[10px] text-slate-500">
            {{ product.lifecycle_pricing_json[0].years }}y support
            <span v-if="product.lifecycle_pricing_json[0].annual_fee">€{{ product.lifecycle_pricing_json[0].annual_fee }}/yr</span>
          </div>
          <div v-if="product.protocols_json || product.specs_json?.protocol" class="mt-2 flex flex-wrap gap-1">
            <span v-for="p in protocolsFor(product).slice(0, 2)" :key="p" class="text-[9px] text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">{{ p }}</span>
          </div>
        </div>
      </NuxtLink>
    </div>

    <div v-else class="text-center py-12 text-slate-400">
      <p class="text-sm">{{ search ? 'No products match your search.' : 'No products are currently available.' }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  absoluteSeoUrl,
  firstProductImage,
  productItemListJsonLd,
} from '~/utils/productSeo'

const { apiFetch } = useApi()
const route = useRoute()
const search = ref('')
const requestUrl = useRequestURL()

const { data, pending: loading, error: loadError, refresh: refreshProducts } = await useAsyncData(
  'h5-official-products-index',
  async () => {
    const res = await apiFetch<any>('/products?limit=100')
    return { products: res.items || res || [] }
  },
  { default: () => ({ products: [] }) },
)

const products = computed<any[]>(() => data.value?.products || [])
const error = computed(() => loadError.value
  ? (loadError.value as any)?.data?.detail || (loadError.value as any)?.message || 'Please try again.'
  : '')

const filteredProducts = computed(() => {
  if (!search.value) return products.value
  const q = search.value.toLowerCase()
  return products.value.filter((p: any) =>
    p.name?.toLowerCase().includes(q) || p.brand?.toLowerCase().includes(q) || p.supply_tier?.toLowerCase().includes(q)
  )
})

function protocolsFor(product: any) {
  if (Array.isArray(product.protocols_json)) return product.protocols_json
  if (product.specs_json?.protocol) return String(product.specs_json.protocol).split(',').map((item) => item.trim())
  return []
}

async function loadProducts() {
  await refreshProducts()
}

const canonicalUrl = computed(() => absoluteSeoUrl(route.path, requestUrl.origin))

useHead(() => ({
  link: [{ key: 'canonical', rel: 'canonical', href: canonicalUrl.value }],
  script: [
    {
      type: 'application/ld+json',
      children: JSON.stringify(productItemListJsonLd(products.value, canonicalUrl.value, requestUrl.origin)),
    },
  ],
}))
</script>
