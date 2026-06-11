<template>
  <div class="px-4 py-4">
    <NuxtLink to="/products" class="inline-flex items-center gap-1 text-xs font-medium text-blue-500 mb-4">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
      </svg>
      {{ $t('common.back') }}
    </NuxtLink>

    <div v-if="product" class="space-y-4">
      <!-- Image -->
      <div class="bg-white rounded-2xl overflow-hidden border border-slate-100 shadow-sm">
        <div class="h-48 bg-slate-50 flex items-center justify-center">
          <img v-if="product.image_url" :src="product.image_url" :alt="product.name" class="w-full h-full object-cover" />
          <svg v-else class="w-16 h-16 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1">
            <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5a1.5 1.5 0 0 0 1.5-1.5V5.25a1.5 1.5 0 0 0-1.5-1.5H3.75a1.5 1.5 0 0 0-1.5 1.5v14.25c0 .828.672 1.5 1.5 1.5Z" />
          </svg>
        </div>
        <div class="p-4">
          <h1 class="text-lg font-bold text-slate-800">{{ product.name }}</h1>
          <p v-if="product.brand" class="text-sm text-slate-400 mt-1">{{ product.brand }}</p>
          <p class="text-sm text-slate-600 mt-3 leading-relaxed">{{ product.description }}</p>
          <div v-if="product.supply_tier" class="mt-4 rounded-xl border border-emerald-100 bg-emerald-50 p-3">
            <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-600">Supply chain</p>
            <p class="mt-1 text-xs text-slate-700">{{ product.supply_tier }}</p>
            <p class="mt-1 text-[11px] text-slate-500">China first-tier, project-grade ecosystem. Not low-cost generic hardware.</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Price & Lifecycle</h2>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div v-if="product.list_price" class="rounded-xl bg-slate-50 p-3">
            <p class="text-slate-400">Device ref.</p>
            <p class="mt-1 font-bold text-blue-600">€{{ product.list_price }}</p>
          </div>
          <div v-if="product.warranty_years" class="rounded-xl bg-slate-50 p-3">
            <p class="text-slate-400">Warranty</p>
            <p class="mt-1 font-bold text-slate-700">{{ product.warranty_years }} years</p>
          </div>
          <div v-if="product.service_term_years?.length" class="rounded-xl bg-slate-50 p-3 col-span-2">
            <p class="text-slate-400">Service terms</p>
            <p class="mt-1 font-bold text-slate-700">{{ product.service_term_years.join(' / ') }} years</p>
          </div>
        </div>
        <div v-if="product.lifecycle_pricing_json?.length" class="mt-3 space-y-2">
          <div v-for="term in product.lifecycle_pricing_json" :key="term.label" class="rounded-xl border border-slate-100 p-3">
            <div class="flex items-center justify-between gap-3">
              <span class="text-xs font-semibold text-slate-700">{{ term.label }}</span>
              <span v-if="term.annual_fee" class="text-xs font-bold text-emerald-600">€{{ term.annual_fee }}/yr</span>
            </div>
            <p v-if="term.note" class="mt-1 text-[11px] text-slate-400">{{ term.note }}</p>
          </div>
        </div>
        <p v-if="product.service_pricing_note" class="mt-3 rounded-xl bg-amber-50 p-3 text-[11px] leading-relaxed text-amber-700">
          {{ product.service_pricing_note }}
        </p>
      </div>

      <!-- Specs -->
      <div v-if="protocolsFor(product).length" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Protocols</h2>
        <div class="flex flex-wrap gap-2">
          <span v-for="p in protocolsFor(product)" :key="p" class="text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full font-medium">{{ p }}</span>
        </div>
      </div>

      <!-- Inquiry CTA -->
      <NuxtLink to="/submit-requirement"
        class="block w-full text-center text-sm font-semibold bg-blue-500 text-white py-3 rounded-xl shadow-md shadow-blue-500/20">
        Inquire About This Product
      </NuxtLink>
    </div>

    <div v-else class="text-center py-20 text-slate-400">
      <p class="text-sm">Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiFetch } = useApi()
const { demoProducts } = useDemoCatalog()
const product = ref<any>(demoProducts.find((item) => item.slug === route.params.slug) || null)

function protocolsFor(product: any) {
  if (Array.isArray(product?.protocols_json)) return product.protocols_json
  if (product?.specs_json?.protocol) return String(product.specs_json.protocol).split(',').map((item) => item.trim())
  return []
}

onMounted(async () => {
  try {
    const res = await apiFetch<any>(`/products/${route.params.slug}`)
    product.value = res
  } catch {}
  if (!product.value) {
    product.value = demoProducts.find((item) => item.slug === route.params.slug)
  }
})
</script>
