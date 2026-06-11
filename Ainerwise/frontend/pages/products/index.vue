<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('products.title') }}</h1>
        <p class="mt-3 text-slate-300">{{ $t('products.subtitle') }}</p>
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
          <div v-if="products.length" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
            <NuxtLink
              v-for="product in products"
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
                <div class="mt-2 flex items-center justify-between">
                  <span v-if="product.list_price" class="font-bold text-primary-400">&euro;{{ product.list_price }}</span>
                  <span v-else class="text-sm text-primary-400 font-medium">{{ $t('products.requestQuote') }}</span>
                  <span v-if="product.moq > 1" class="text-xs text-slate-500">MOQ: {{ product.moq }}</span>
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
const products = ref<any[]>([])
const categories = ref<any[]>([])
const search = ref('')
const selectedCategory = ref<string | null>(null)

onMounted(async () => {
  try {
    const [prodRes, catRes] = await Promise.all([
      apiFetch<any>('/products'),
      apiFetch<any>('/product-categories'),
    ])
    products.value = prodRes.items || prodRes || []
    categories.value = catRes.items || catRes || []
  } catch {}
})
</script>
