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
        <div class="mt-5 flex flex-wrap justify-center gap-2">
          <span
            v-for="partner in demoSupplyPartners"
            :key="partner.name"
            class="border border-primary-500/30 bg-primary-900/30 text-primary-200 px-3 py-1 text-xs"
          >
            {{ partner.name }}
          </span>
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
          <div v-if="filteredProducts.length" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
            <NuxtLink
              v-for="product in filteredProducts"
              :key="product.id"
              :to="`/products/${product.slug}`"
              class="glass-panel overflow-hidden transition hover:border-primary-500/50 hover:shadow-[0_0_15px_rgba(14,165,233,0.2)]"
            >
              <div class="aspect-video bg-black/20 flex items-center justify-center border-b border-white/10">
                <img
                  v-if="product.images_json?.[0]"
                  :src="product.images_json[0]"
                  :alt="product.name"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-slate-600 text-4xl">&#128247;</span>
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
const { apiFetch } = useApi()
const { demoCategories, demoProducts, demoSupplyPartners } = useDemoCatalog()
const products = ref<any[]>(demoProducts)
const categories = ref<any[]>(demoCategories)
const search = ref('')
const selectedCategory = ref<string | null>(null)

const filteredProducts = computed(() => {
  const term = search.value.trim().toLowerCase()
  return products.value.filter((product) => {
    const matchesCategory = !selectedCategory.value || product.category_id === selectedCategory.value
    const searchable = `${product.name || ''} ${product.brand || ''} ${product.description || ''}`.toLowerCase()
    const matchesSearch = !term || searchable.includes(term)
    return matchesCategory && matchesSearch
  })
})

onMounted(async () => {
  try {
    const [prodRes, catRes] = await Promise.all([
      apiFetch<any>('/products'),
      apiFetch<any>('/product-categories'),
    ])
    products.value = prodRes.items || prodRes || []
    categories.value = catRes.items || catRes || []
  } catch {}

  if (!products.value.length) {
    products.value = demoProducts
  }
  if (!categories.value.length) {
    categories.value = demoCategories
  }
})
</script>
