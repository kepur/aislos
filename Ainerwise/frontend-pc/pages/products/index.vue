<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('products.title') }}</h1>
        <p class="mt-3 text-slate-300">{{ $t('products.subtitle') }}</p>
        <p class="mt-3 max-w-3xl mx-auto text-sm text-slate-400">
          AinerWise focuses on China first-tier, project-grade supply chains such as Huawei Digital Power, Sungrow, LONGi,
          Xiaomi ecosystem, leading CCTV/access vendors, and verified OEM/ODM partners. These are solution-ready building
          blocks, not cheap commodity products.
        </p>
        <div class="mt-6 flex flex-wrap justify-center gap-3">
          <button
            v-for="surface in surfaceOptions"
            :key="surface.value"
            type="button"
            class="rounded-full border px-4 py-2 text-sm font-semibold transition"
            :class="selectedSurface === surface.value ? 'border-primary-400 bg-primary-500/15 text-primary-200' : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'"
            @click="selectedSurface = surface.value"
          >
            {{ surface.label }}
          </button>
          <a :href="marketUrl" class="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-200 hover:bg-emerald-500/15">
            AinerWise Market
          </a>
          <a :href="`${marketUrl}/secondhand`" class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-white/10">
            2Hands
          </a>
        </div>
      </div>

      <div class="flex flex-col lg:flex-row gap-8">
        <!-- Filters -->
        <aside class="w-full lg:w-64 flex-shrink-0">
          <div class="glass-panel p-4 space-y-4 sticky top-20 border-primary-500/30 shadow-[0_0_20px_rgba(14,165,233,0.1)]">
            <h3 class="font-semibold text-white">{{ $t('products.filter') }}</h3>
            <div>
              <input
                v-model="search"
                type="text"
                :placeholder="$t('common.search')"
                class="input-field"
              />
            </div>
            <div>
              <p class="text-sm font-medium text-slate-300 mb-2">{{ $t('products.allCategories') }}</p>
              <div class="space-y-1 max-h-60 overflow-y-auto">
                <button
                  v-for="cat in categories"
                  :key="cat.id"
                  @click="selectedCategory = selectedCategory === cat.id ? null : cat.id"
                  class="block w-full text-left text-sm px-2 py-1 rounded transition"
                  :class="selectedCategory === cat.id ? 'bg-primary-900/50 text-primary-400 font-medium border border-primary-500/30' : 'text-slate-400 hover:bg-white/5 hover:text-white'"
                >
                  {{ cat.name }}
                </button>
              </div>
            </div>
          </div>
        </aside>

        <!-- Product Grid -->
        <div class="flex-1">
          <div v-if="loading" class="glass-panel p-8 text-center text-sm text-slate-400">
            Loading products...
          </div>
          <div v-else-if="error" class="glass-panel border-red-400/30 p-8 text-center">
            <p class="font-semibold text-red-300">Products could not be loaded.</p>
            <p class="mt-2 text-sm text-red-200/70">{{ error }}</p>
            <button type="button" class="btn-primary mt-4" @click="loadProducts">Retry</button>
          </div>
          <div v-else-if="filteredProducts.length" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
            <NuxtLink
              v-for="product in filteredProducts"
              :key="product.id"
              :to="`/products/${product.slug}`"
              class="glass-panel overflow-hidden transition hover:border-primary-500/50 hover:shadow-[0_0_15px_rgba(14,165,233,0.2)]"
            >
              <div class="aspect-video bg-black/20 flex items-center justify-center border-b border-white/10">
                <img
                  v-if="firstProductImage(product)"
                  :src="firstProductImage(product)"
                  :alt="product.name"
                  class="w-full h-full object-cover"
                />
                <FeatureIcon v-else name="camera" size="lg" class="text-slate-500" />
              </div>
              <div class="p-4">
                <div class="flex items-center gap-2 mb-2">
                  <StatusBadge v-if="product.source_type === 'official'" status="verified" :label="$t('products.official')" />
                  <StatusBadge v-if="product.service_available" status="active" :label="$t('products.serviceAvailable')" />
                </div>
                <h3 class="font-semibold text-white">{{ product.name }}</h3>
                <p v-if="product.brand" class="text-sm text-slate-400">{{ product.brand }}</p>
                <p v-if="product.supply_tier" class="mt-2 text-xs text-emerald-300 line-clamp-2">{{ product.supply_tier }}</p>
                <div class="mt-3 flex items-center justify-between gap-3">
                  <span v-if="product.list_price" class="font-bold text-primary-400">&euro;{{ product.list_price }} ref.</span>
                  <span v-else class="text-sm text-primary-400 font-medium">{{ $t('products.requestQuote') }}</span>
                  <span v-if="product.moq > 1" class="text-xs text-slate-500">MOQ: {{ product.moq }}</span>
                </div>
                <div class="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                  <div v-if="product.warranty_years" class="border border-white/10 bg-white/5 px-2 py-1 text-slate-300">
                    Warranty {{ product.warranty_years }}y
                  </div>
                  <div v-if="product.service_term_years?.length" class="border border-white/10 bg-white/5 px-2 py-1 text-slate-300">
                    Support {{ product.service_term_years.join('/') }}y
                  </div>
                </div>
                <div v-if="product.lifecycle_pricing_json?.length" class="mt-2 space-y-1">
                  <div
                    v-for="term in product.lifecycle_pricing_json.slice(0, 2)"
                    :key="term.label"
                    class="flex items-center justify-between gap-2 text-[11px] text-slate-400"
                  >
                    <span>{{ term.years }}y maintenance</span>
                    <span v-if="term.annual_fee" class="text-slate-200">&euro;{{ term.annual_fee }}/yr</span>
                  </div>
                </div>
              </div>
            </NuxtLink>
          </div>
          <p v-else class="text-center text-slate-500 py-12">{{ $t('products.noProducts') }}</p>
        </div>
      </div>
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
const selectedCategory = ref<string | null>(null)
const selectedSurface = ref<'official' | 'market' | 'recycled'>('official')
const requestUrl = useRequestURL()
const publicConfig = useRuntimeConfig().public
const marketUrl = computed(() => String(publicConfig.marketUrl || 'http://market.localhost'))
const surfaceOptions = [
  { value: 'official', label: 'Official recommended' },
  { value: 'market', label: 'Market products' },
  { value: 'recycled', label: 'Enterprise recycled' },
] as const

const { data, pending: loading, error: loadError, refresh: refreshProducts } = await useAsyncData(
  'official-products-index',
  async () => {
    const [prodRes, catRes] = await Promise.all([
      apiFetch<any>(`/products?limit=100&surface=${selectedSurface.value}`),
      apiFetch<any>('/product-categories'),
    ])
    return {
      products: prodRes.items || prodRes || [],
      categories: catRes.items || catRes || [],
    }
  },
  { default: () => ({ products: [], categories: [] }), watch: [selectedSurface] },
)

const products = computed<any[]>(() => data.value?.products || [])
const categories = computed<any[]>(() => data.value?.categories || [])
const error = computed(() => loadError.value
  ? (loadError.value as any)?.data?.detail || (loadError.value as any)?.message || 'Please try again.'
  : '')

const filteredProducts = computed(() => {
  const term = search.value.trim().toLowerCase()
  return products.value.filter((product) => {
    const matchesCategory = !selectedCategory.value || product.category_id === selectedCategory.value
    const searchable = `${product.name || ''} ${product.brand || ''} ${product.description || ''}`.toLowerCase()
    const matchesSearch = !term || searchable.includes(term)
    return matchesCategory && matchesSearch
  })
})

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
