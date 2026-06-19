<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Reviews & Trust Score</h1>
        <p class="text-sm text-slate-500 mt-1">Buyer feedback after online and offline transactions.</p>
      </div>
      <UButton color="gray" variant="outline" icon="i-heroicons-arrow-path" :loading="loading" @click="loadReviews">Refresh</UButton>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <UCard class="text-center">
        <p class="text-slate-500 text-sm font-medium mb-2">Overall Rating</p>
        <div class="flex justify-center items-center text-4xl font-bold text-slate-900">
          {{ summary.average_overall_rating.toFixed(1) }}
          <UIcon name="i-heroicons-star-solid" class="w-8 h-8 text-amber-400 ml-2" />
        </div>
        <p class="text-xs text-slate-500 mt-2">Based on {{ summary.total_reviews }} reviews</p>
      </UCard>
      <UCard class="text-center">
        <p class="text-slate-500 text-sm font-medium mb-2">Product Quality</p>
        <p class="text-4xl font-bold text-green-600">{{ metric(summary.average_product_quality_rating) }}</p>
        <p class="text-xs text-slate-500 mt-2">Online + offline</p>
      </UCard>
      <UCard class="text-center">
        <p class="text-slate-500 text-sm font-medium mb-2">Logistics</p>
        <p class="text-4xl font-bold text-indigo-600">{{ metric(summary.average_logistics_rating) }}</p>
        <p class="text-xs text-slate-500 mt-2">Online transactions only</p>
      </UCard>
      <UCard class="text-center">
        <p class="text-slate-500 text-sm font-medium mb-2">Communication</p>
        <p class="text-4xl font-bold text-purple-600">{{ metric(summary.average_communication_rating) }}</p>
        <p class="text-xs text-slate-500 mt-2">{{ summary.online_reviews }} online · {{ summary.offline_reviews }} offline</p>
      </UCard>
    </div>

    <UCard>
      <template #header>
        <h3 class="text-lg font-medium text-slate-900">Recent Buyer Reviews</h3>
      </template>

      <div v-if="loading" class="py-10 text-center text-slate-400">Loading reviews...</div>
      <div v-else-if="!summary.reviews.length" class="py-12 text-center text-slate-400">
        <div class="text-4xl mb-2">⭐</div>
        <p class="text-sm">No buyer reviews yet.</p>
      </div>
      <div v-else class="space-y-6">
        <div v-for="review in summary.reviews" :key="review.id" class="pb-6 border-b border-slate-100 last:border-0 last:pb-0">
          <div class="flex justify-between items-start gap-4">
            <div class="flex items-center">
              <UAvatar :src="`https://i.pravatar.cc/150?u=${review.reviewer_id}`" />
              <div class="ml-3">
                <p class="font-medium text-slate-900">Buyer Review</p>
                <div class="flex items-center gap-2 mt-0.5">
                  <div class="flex text-amber-400">
                    <UIcon name="i-heroicons-star-solid" class="w-4 h-4" v-for="i in review.overall_rating" :key="i" />
                  </div>
                  <UBadge :color="review.transaction_channel === 'ONLINE' ? 'blue' : 'gray'" variant="soft" size="xs">
                    {{ review.transaction_channel }}
                  </UBadge>
                </div>
              </div>
            </div>
            <span class="text-xs text-slate-500">{{ new Date(review.created_at).toLocaleDateString() }}</span>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-3 gap-2 mt-4 text-xs">
            <div class="bg-slate-50 rounded-lg p-2">Product: <b>{{ review.product_quality_rating || '—' }}</b></div>
            <div class="bg-slate-50 rounded-lg p-2">Logistics: <b>{{ review.logistics_rating || 'N/A' }}</b></div>
            <div class="bg-slate-50 rounded-lg p-2">Communication: <b>{{ review.communication_rating || '—' }}</b></div>
          </div>
          <p v-if="review.comment" class="mt-3 text-slate-600 text-sm">{{ review.comment }}</p>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'supplier' })

const authStore = useAuthStore()
const config = useRuntimeConfig()
const loading = ref(false)

const summary = reactive({
  total_reviews: 0,
  average_overall_rating: 0,
  average_product_quality_rating: null as number | null,
  average_logistics_rating: null as number | null,
  average_communication_rating: null as number | null,
  online_reviews: 0,
  offline_reviews: 0,
  reviews: [] as any[],
})

function metric(value: number | null) {
  return value == null ? '—' : value.toFixed(1)
}

async function loadReviews() {
  loading.value = true
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/reviews/company/me`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    Object.assign(summary, data)
  } catch {
    Object.assign(summary, {
      total_reviews: 0,
      average_overall_rating: 0,
      average_product_quality_rating: null,
      average_logistics_rating: null,
      average_communication_rating: null,
      online_reviews: 0,
      offline_reviews: 0,
      reviews: [],
    })
  } finally {
    loading.value = false
  }
}

onMounted(() => loadReviews())
</script>
