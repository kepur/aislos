<template>
  <div class="space-y-4 p-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-[10px] font-bold uppercase tracking-widest text-violet-600">Creative briefs</p>
        <h1 class="mt-1 text-xl font-bold text-slate-900">Copy and production briefs</h1>
      </div>
      <NuxtLink to="/marketing-mobile/briefs/new" class="rounded-xl bg-violet-600 px-3 py-2 text-xs font-semibold text-white">New</NuxtLink>
    </div>
    <select v-model="status" class="m-input" @change="load">
      <option value="">All statuses</option>
      <option value="draft">Draft</option>
      <option value="in_review">In review</option>
      <option value="approved">Approved</option>
      <option value="rejected">Rejected</option>
    </select>
    <NuxtLink v-for="brief in items" :key="brief.id" :to="`/marketing-mobile/briefs/${brief.id}`" class="m-card block">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold text-slate-800">{{ brief.title }}</p>
          <p class="mt-1 line-clamp-2 text-xs text-slate-400">{{ brief.objective || 'No objective entered' }}</p>
        </div>
        <span :class="['status-pill shrink-0', statusClass(brief.status)]">{{ brief.status }}</span>
      </div>
      <p class="mt-3 text-[10px] text-slate-400">v{{ brief.current_version?.version || 1 }} · {{ formatDate(brief.updated_at) }}</p>
    </NuxtLink>
    <p v-if="!loading && !items.length" class="m-card text-center text-sm text-slate-400">No briefs match this filter.</p>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import type { MarketingBrief } from '~/composables/useMarketingMobile'
definePageMeta({ middleware: 'auth', layout: 'marketing-mobile' })
const api = useMarketingMobile()
const items = ref<MarketingBrief[]>([])
const status = ref('')
const loading = ref(false)
const error = ref('')
const formatDate = (value: string) => new Date(value).toLocaleString()
const statusClass = (value: string) => value === 'approved' ? 'bg-emerald-50 text-emerald-600' : value === 'rejected' ? 'bg-red-50 text-red-600' : 'bg-violet-50 text-violet-600'
async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await api.listBriefs(status.value || undefined)).items
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

