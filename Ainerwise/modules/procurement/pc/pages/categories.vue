<template>
  <div class="bg-slate-50 min-h-screen">
    <!-- Header -->
    <div class="bg-white border-b border-slate-200 py-10 px-6">
      <div class="mx-auto max-w-7xl">
        <h1 class="text-3xl font-bold text-slate-900">{{ appStore.t('categories.title') }}</h1>
        <p class="mt-2 text-slate-500">{{ appStore.t('categories.subtitle').replace('{count}', String(categories.length)) }}</p>
      </div>
    </div>

    <!-- Category Grid -->
    <div class="mx-auto max-w-7xl px-6 py-10">
      <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div v-for="i in 15" :key="i" class="bg-white rounded-2xl p-6 animate-pulse">
          <div class="w-10 h-10 bg-slate-200 rounded-xl mb-3"></div>
          <div class="h-4 bg-slate-200 rounded w-3/4"></div>
          <div class="h-3 bg-slate-100 rounded w-1/2 mt-2"></div>
        </div>
      </div>

      <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <NuxtLink
          v-for="cat in categories"
          :key="cat.id"
          :to="`/marketplace?category_id=${cat.id}&category_name=${encodeURIComponent(categoryDisplayName(cat))}`"
          class="group bg-white rounded-2xl border border-slate-200 p-6 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer"
        >
          <div class="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center mb-4 group-hover:bg-indigo-100 transition-colors">
            <span class="text-2xl">{{ getCategoryEmoji(cat.slug) }}</span>
          </div>
          <h3 class="text-sm font-semibold text-slate-900 leading-tight">{{ categoryDisplayName(cat) }}</h3>
          <p v-if="categorySecondaryName(cat)" class="text-xs text-slate-400 mt-0.5">{{ categorySecondaryName(cat) }}</p>
          <span class="mt-2 text-xs text-indigo-600 font-medium group-hover:underline">{{ appStore.t('categories.browse') }} →</span>
        </NuxtLink>
      </div>

      <!-- Empty state -->
      <div v-if="!loading && categories.length === 0" class="text-center py-20 text-slate-400">
        <p>{{ appStore.t('categories.empty') }}</p>
      </div>

      <!-- CTA -->
      <div class="mt-12 bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-2xl p-8 text-white text-center">
        <h2 class="text-2xl font-bold">{{ appStore.t('categories.ctaTitle') }}</h2>
        <p class="mt-2 opacity-80">{{ appStore.t('categories.ctaDesc') }}</p>
        <NuxtLink to="/post-request" class="mt-5 inline-block bg-white text-indigo-600 font-semibold px-6 py-3 rounded-xl hover:bg-slate-50 transition-colors">
          {{ appStore.t('action.postRequest') }}
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const config = useRuntimeConfig()
const appStore = useAppStore()

interface Category {
  id: string
  name: string
  name_zh: string | null
  name_tl: string | null
  slug: string
  level: number
  icon: string | null
  sort_order: number
  status: string
}

const categories = ref<Category[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await $fetch<Category[]>(`${config.public.apiBase}/categories`)
    categories.value = (data ?? []).filter(c => c.status === 'ACTIVE').sort((a, b) => a.sort_order - b.sort_order)
  } catch (e) {
    console.error('Failed to load categories', e)
  } finally {
    loading.value = false
  }
})

const EMOJI_MAP: Record<string, string> = {
  'construction-materials': '🏗️',
  'it-office-equipment': '💻',
  'automotive-parts': '🚗',
  'electronics-components': '⚡',
  'machinery-industrial': '⚙️',
  'raw-materials-chemicals': '🧪',
  'textiles-garments': '👕',
  'food-beverages': '🍜',
  'agriculture-farming': '🌾',
  'medical-healthcare': '🏥',
  'packaging-printing': '📦',
  'furniture-home': '🪑',
  'lighting-electrical': '💡',
  'plumbing-hvac': '🔧',
  'safety-security': '🛡️',
  'sports-outdoor': '⛺',
  'beauty-personal-care': '💄',
  'toys-baby-products': '🧸',
  'pet-supplies': '🐾',
  'jewelry-accessories': '💍',
  'energy-solar': '☀️',
  'marine-shipping': '⚓',
  'mining-minerals': '⛏️',
  'telecom-networking': '📡',
  'tools-hardware': '🔨',
}

function getCategoryEmoji(slug: string): string {
  return EMOJI_MAP[slug] ?? '📦'
}

function categoryDisplayName(cat: Category): string {
  if (appStore.language === 'ZH') return cat.name_zh || cat.name
  if (appStore.language === 'TL') return cat.name_tl || cat.name
  return cat.name
}

function categorySecondaryName(cat: Category): string {
  if (appStore.language === 'ZH') return cat.name
  if (appStore.language === 'TL' && cat.name_tl) return cat.name
  return ''
}
</script>
