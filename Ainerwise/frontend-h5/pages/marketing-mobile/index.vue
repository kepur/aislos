<template>
  <div class="space-y-4 p-4">
    <div>
      <p class="text-[10px] font-bold uppercase tracking-[0.24em] text-violet-600">Marketing workspace</p>
      <h1 class="mt-1 text-xl font-bold text-slate-900">Briefs, review and publishing</h1>
      <p class="mt-1 text-xs text-slate-500">AISLOS exports approved briefs and imports generated media assets.</p>
    </div>

    <div v-if="loading" class="m-card text-center text-sm text-slate-400">Loading marketing workspace...</div>
    <template v-else-if="data">
      <div class="grid grid-cols-3 gap-2">
        <NuxtLink v-for="card in cards" :key="card.label" :to="card.to" class="m-card p-3 text-center">
          <p class="text-xl font-bold text-violet-600">{{ card.value }}</p>
          <p class="mt-1 text-[10px] text-slate-400">{{ card.label }}</p>
        </NuxtLink>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <NuxtLink to="/marketing-mobile/briefs/new" class="rounded-2xl bg-violet-600 px-4 py-4 text-center text-xs font-semibold text-white shadow-lg shadow-violet-500/20">Create creative brief</NuxtLink>
        <NuxtLink to="/marketing-mobile/review" class="m-card block text-center text-xs font-semibold text-violet-700">Open review queue</NuxtLink>
      </div>

      <div class="m-card">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-bold text-slate-800">Campaign performance</h2>
          <span class="text-[10px] text-slate-400">{{ data.campaigns?.length || 0 }} campaigns</span>
        </div>
        <div v-if="data.campaigns?.length" class="mt-3 space-y-3">
          <div v-for="campaign in data.campaigns.slice(0, 5)" :key="campaign.id" class="rounded-xl bg-violet-50 p-3">
            <div class="flex items-start justify-between gap-2">
              <div>
                <p class="text-xs font-semibold text-slate-800">{{ campaign.name }}</p>
                <p class="mt-1 text-[10px] uppercase tracking-wide text-violet-500">{{ campaign.channel }} · {{ campaign.status }}</p>
              </div>
              <span class="text-sm font-bold text-violet-700">{{ campaign.conversions }}</span>
            </div>
          </div>
        </div>
        <p v-else class="py-4 text-center text-xs text-slate-400">No campaigns yet.</p>
      </div>
    </template>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'marketing-mobile' })

const api = useMarketingMobile()
const data = ref<any>(null)
const loading = ref(true)
const error = ref('')
const cards = computed(() => [
  { label: 'Active', value: data.value?.counts?.active_campaigns ?? 0, to: '/marketing-mobile/schedule' },
  { label: 'Awaiting review', value: data.value?.counts?.pending_approval ?? 0, to: '/marketing-mobile/review' },
  { label: 'Due now', value: data.value?.counts?.due_follow_ups ?? 0, to: '/marketing-mobile/schedule' },
  { label: 'Contacts', value: data.value?.counts?.contacts ?? 0, to: '/marketing-mobile/schedule' },
  { label: 'Leads', value: data.value?.counts?.attributed_leads ?? 0, to: '/marketing-mobile/schedule' },
  { label: 'Inquiries', value: data.value?.counts?.attributed_inquiries ?? 0, to: '/marketing-mobile/schedule' },
])

onMounted(async () => {
  try {
    data.value = await api.dashboard()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Marketing dashboard is unavailable.'
  } finally {
    loading.value = false
  }
})
</script>

