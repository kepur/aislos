<template>
  <div>
    <div class="mb-6">
      <h1 class="admin-page-title">Agent Marketplace Review</h1>
      <p class="admin-page-desc">Approve purpose and risk before publication. Third-party Agents enter paused with all eight data grants denied.</p>
    </div>
    <div class="grid gap-4 lg:grid-cols-2">
      <article v-for="listing in listings" :key="listing.id" class="admin-panel p-5">
        <div class="flex items-start justify-between gap-4">
          <div><h2 class="font-semibold text-white">{{ listing.name }}</h2><p class="text-xs text-slate-400">{{ listing.slug }} · v{{ listing.version }}</p></div>
          <StatusBadge :status="listing.status" />
        </div>
        <p class="mt-4 text-sm text-slate-400">{{ listing.description || 'No description provided.' }}</p>
        <div class="mt-4 grid gap-3 text-xs sm:grid-cols-2">
          <div><p class="text-slate-500 uppercase tracking-wide">Workflows</p><p class="mt-1 text-slate-300">{{ listing.workflows.join(', ') || 'none' }}</p></div>
          <div><p class="text-slate-500 uppercase tracking-wide">Requested scopes</p><p class="mt-1 text-amber-200">{{ listing.requested_scopes.join(', ') || 'none' }}</p></div>
        </div>
        <p v-if="listing.review_notes" class="mt-4 rounded bg-white/5 p-3 text-xs text-slate-300">{{ listing.review_notes }}</p>
        <div v-if="listing.status === 'submitted'" class="mt-5 flex gap-2">
          <button class="rounded bg-emerald-500/20 px-3 py-2 text-xs font-medium text-emerald-300 hover:bg-emerald-500/30" @click="review(listing, 'approve')">Approve safely</button>
          <button class="rounded bg-red-500/20 px-3 py-2 text-xs font-medium text-red-300 hover:bg-red-500/30" @click="review(listing, 'reject')">Reject</button>
        </div>
      </article>
    </div>
    <p v-if="!listings.length" class="admin-panel p-8 text-center text-sm text-slate-400">No Marketplace listings yet.</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { apiFetch } = useApi()
const listings = ref<any[]>([])
async function load() {
  const res = await apiFetch<any>('/admin/marketplace/listings')
  listings.value = res.items || []
}
async function review(listing: any, action: 'approve' | 'reject') {
  const notes = window.prompt(`${action === 'approve' ? 'Approval' : 'Rejection'} notes`) || ''
  await apiFetch(`/admin/marketplace/listings/${listing.id}/${action}`, { method: 'POST', body: { notes } })
  await load()
}
onMounted(load)
</script>
