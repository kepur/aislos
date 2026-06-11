<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Advertising Campaigns</h1>
        <p class="text-slate-500 mt-1">Promote your products and increase your visibility in the marketplace.</p>
      </div>
      <UButton color="indigo" icon="i-heroicons-plus" to="/supplier/ads/create">Create Campaign</UButton>
    </div>

    <!-- Campaigns List -->
    <UCard>
      <div v-if="loading" class="space-y-4">
        <div v-for="i in 3" :key="i" class="h-16 bg-slate-100 rounded-xl animate-pulse" />
      </div>
      <div v-else-if="campaigns.length === 0" class="text-center py-12">
        <div class="text-5xl mb-4">📢</div>
        <h3 class="text-lg font-semibold text-slate-900 mb-1">No campaigns yet</h3>
        <p class="text-slate-500 text-sm mb-4">Start advertising your products to get more orders.</p>
        <UButton color="indigo" to="/supplier/ads/create">Create your first campaign</UButton>
      </div>
      <div v-else class="space-y-4">
        <div v-for="camp in campaigns" :key="camp.id" class="border border-slate-200 rounded-xl p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center text-xl">
              {{ camp.placement === 'SEARCH_TOP' ? '🔍' : camp.placement === 'CATEGORY_TOP' ? '🗂️' : '✨' }}
            </div>
            <div>
              <h3 class="font-bold text-slate-900 flex items-center gap-2">
                {{ camp.title }}
                <UBadge :color="statusColor(camp.status)" size="xs">{{ camp.status }}</UBadge>
              </h3>
              <div class="text-xs text-slate-500 mt-1 flex items-center gap-3">
                <span>💰 Budget: {{ formatPrice(camp.budget_minor, camp.currency) }}</span>
                <span>💸 Spent: {{ formatPrice(camp.spent_minor, camp.currency) }}</span>
                <span>🖱️ {{ camp.clicks }} Clicks</span>
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <UButton v-if="camp.status === 'DRAFT'" size="sm" color="indigo" variant="soft" @click="submitCampaign(camp)">Submit for Review</UButton>
            <UButton v-if="camp.status === 'ACTIVE'" size="sm" color="amber" variant="soft" @click="pauseCampaign(camp)">Pause</UButton>
            <UButton v-if="['PAUSED', 'ACTIVE', 'COMPLETED'].includes(camp.status)" size="sm" color="gray" variant="ghost" :to="`/supplier/ads/${camp.id}/metrics`">Metrics</UButton>
          </div>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'supplier', middleware: ['supplier'] })

const config = useRuntimeConfig()
const authStore = useAuthStore()
const toast = useToast()

const loading = ref(true)
const campaigns = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const data = await $fetch<any[]>(`${config.public.apiBase}/merchant/ad-campaigns`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    campaigns.value = data ?? []
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Failed to load campaigns', color: 'red' })
  } finally {
    loading.value = false
  }
}

function formatPrice(minor: number, currency: string) {
  return `${(minor / 100).toLocaleString()} ${currency}`
}

function statusColor(status: string) {
  const map: Record<string, string> = {
    DRAFT: 'gray',
    PENDING_REVIEW: 'yellow',
    ACTIVE: 'green',
    PAUSED: 'orange',
    REJECTED: 'red',
    COMPLETED: 'blue',
  }
  return map[status] || 'gray'
}

async function submitCampaign(camp: any) {
  try {
    await $fetch(`${config.public.apiBase}/merchant/ad-campaigns/${camp.id}/submit`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    toast.add({ title: 'Campaign submitted for review', color: 'green' })
    await load()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Failed to submit', color: 'red' })
  }
}

async function pauseCampaign(camp: any) {
  try {
    await $fetch(`${config.public.apiBase}/merchant/ad-campaigns/${camp.id}/pause`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    toast.add({ title: 'Campaign paused', color: 'green' })
    await load()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Failed to pause', color: 'red' })
  }
}

onMounted(() => load())
</script>
