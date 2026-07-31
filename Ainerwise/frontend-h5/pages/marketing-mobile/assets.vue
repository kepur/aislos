<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-violet-600">Imported media</p><h1 class="mt-1 text-xl font-bold text-slate-900">Asset library</h1></div>
    <select v-model="status" class="m-input" @change="load">
      <option value="">All statuses</option><option value="in_review">In review</option><option value="approved">Approved</option><option value="rejected">Rejected</option><option value="scheduled">Scheduled</option>
    </select>
    <div v-for="asset in assets" :key="asset.id" class="m-card">
      <div class="flex justify-between gap-3">
        <div><p class="text-sm font-semibold text-slate-800">{{ asset.title || `${asset.kind} asset` }}</p><p class="mt-1 text-[10px] text-slate-400">{{ asset.channel || 'no channel' }} · {{ asset.lang }}</p></div>
        <span class="status-pill bg-violet-50 text-violet-600">{{ asset.status }}</span>
      </div>
      <p v-if="asset.content" class="mt-3 line-clamp-4 whitespace-pre-line text-xs text-slate-500">{{ asset.content }}</p>
      <div v-if="asset.status === 'in_review'" class="mt-3 grid grid-cols-2 gap-2">
        <button class="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white" @click="approve(asset.id)">Approve</button>
        <button class="rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-600" @click="reject(asset.id)">Reject</button>
      </div>
      <button v-if="asset.status === 'approved'" class="mt-3 w-full rounded-xl bg-violet-600 px-3 py-2 text-xs font-semibold text-white" @click="schedule(asset)">Schedule publication</button>
    </div>
    <p v-if="!assets.length && !error" class="m-card text-center text-sm text-slate-400">No imported assets match this filter.</p>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import type { MarketingAsset } from '~/composables/useMarketingMobile'
definePageMeta({ middleware: 'auth', layout: 'marketing-mobile' })
const api = useMarketingMobile()
const assets = ref<MarketingAsset[]>([])
const status = ref('')
const error = ref('')
async function load() {
  try {
    assets.value = (await api.listAssets(status.value || undefined)).items.filter(item => !item.ai_generated)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
}
async function approve(id: string) {
  await api.approveAsset(id)
  await load()
}
async function reject(id: string) {
  const reason = window.prompt('Rejection reason (required)')
  if (!reason?.trim()) return
  await api.rejectAsset(id, reason.trim())
  await load()
}
async function schedule(asset: MarketingAsset) {
  const at = window.prompt('Publish at (ISO date/time)', new Date(Date.now() + 3600e3).toISOString())
  if (!at) return
  await api.scheduleAsset(asset.id, asset.channel || 'linkedin', at)
  await load()
}
onMounted(load)
</script>

