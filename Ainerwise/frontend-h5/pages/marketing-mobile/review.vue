<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-violet-600">Human approval gate</p><h1 class="mt-1 text-xl font-bold text-slate-900">Review queue</h1></div>
    <div class="m-card">
      <h2 class="text-sm font-bold text-slate-800">Creative briefs</h2>
      <NuxtLink v-for="brief in briefs" :key="brief.id" :to="`/marketing-mobile/briefs/${brief.id}`" class="mt-3 block rounded-xl bg-violet-50 p-3">
        <p class="text-xs font-semibold text-slate-800">{{ brief.title }}</p>
        <p class="mt-1 line-clamp-2 text-[11px] text-slate-500">{{ brief.current_version?.copy_json?.headline || brief.objective }}</p>
      </NuxtLink>
      <p v-if="!briefs.length" class="py-3 text-center text-xs text-slate-400">No briefs awaiting review.</p>
    </div>
    <div class="m-card">
      <h2 class="text-sm font-bold text-slate-800">Imported media assets</h2>
      <div v-for="asset in assets" :key="asset.id" class="mt-3 rounded-xl bg-slate-50 p-3">
        <p class="text-xs font-semibold text-slate-800">{{ asset.title || `${asset.kind} asset` }}</p>
        <p class="mt-1 text-[10px] text-slate-400">{{ asset.channel || 'no channel' }} · {{ asset.lang }}</p>
        <p v-if="asset.content" class="mt-2 line-clamp-3 text-xs text-slate-500">{{ asset.content }}</p>
        <div class="mt-3 grid grid-cols-2 gap-2">
          <button class="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white" @click="approve(asset.id)">Approve</button>
          <button class="rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-600" @click="reject(asset.id)">Reject</button>
        </div>
      </div>
      <p v-if="!assets.length" class="py-3 text-center text-xs text-slate-400">No imported assets awaiting review.</p>
    </div>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import type { MarketingBrief, MarketingAsset } from '~/composables/useMarketingMobile'
definePageMeta({ middleware: 'auth', layout: 'marketing-mobile' })
const api = useMarketingMobile()
const briefs = ref<MarketingBrief[]>([])
const assets = ref<MarketingAsset[]>([])
const error = ref('')
async function load() {
  try {
    const [briefData, assetData] = await Promise.all([api.listBriefs('in_review'), api.listAssets('in_review')])
    briefs.value = briefData.items
    assets.value = assetData.items.filter(item => !item.ai_generated)
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
onMounted(load)
</script>

