<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between mb-10">
        <div>
          <p class="text-xs font-bold tracking-[0.25em] text-primary-400 uppercase">AISLOS Agent Marketplace</p>
          <h1 class="mt-3 text-4xl font-bold text-white">Install governed AI employees.</h1>
          <p class="mt-3 max-w-3xl text-slate-400">
            Every Agent is reviewed before publication. Installation never grants access to company data; permissions remain explicit and auditable.
          </p>
        </div>
        <NuxtLink to="/developers" class="btn-secondary text-center">Build an Agent</NuxtLink>
      </div>

      <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="listing in listings" :key="listing.id" class="glass-panel p-5">
          <div class="flex items-start justify-between gap-3">
            <div>
              <h2 class="text-lg font-semibold text-white">{{ listing.name }}</h2>
              <p class="text-xs text-primary-300">{{ listing.role_title || 'AI employee' }}</p>
            </div>
            <span class="rounded-full border border-emerald-400/30 px-2 py-1 text-[10px] text-emerald-300">Reviewed</span>
          </div>
          <p class="mt-4 line-clamp-3 text-sm text-slate-400">{{ listing.description || 'Governed AISLOS Agent capability.' }}</p>
          <div class="mt-4 flex flex-wrap gap-1">
            <span v-for="workflow in listing.workflows" :key="workflow" class="rounded bg-white/5 px-2 py-1 text-[10px] font-mono text-slate-400">{{ workflow }}</span>
          </div>
          <div class="mt-5 flex items-center justify-between">
            <span class="font-semibold text-white">{{ listing.price_monthly == null ? 'Included' : `${listing.price_monthly} ${listing.currency}/mo` }}</span>
            <button class="btn-primary !px-4 !py-2 text-sm" @click="install(listing)">Install</button>
          </div>
        </article>
      </div>

      <div v-if="isLoggedIn" class="mt-12">
        <h2 class="text-xl font-semibold text-white">My installed Agents</h2>
        <div class="mt-4 grid gap-3 md:grid-cols-2">
          <div v-for="item in installations" :key="item.id" class="glass-panel flex items-center justify-between gap-4 p-4">
            <div>
              <p class="font-medium text-white">{{ item.name }}</p>
              <p class="text-xs text-slate-400">{{ item.status }} · permissions remain separately governed</p>
            </div>
            <button v-if="item.status === 'installed'" class="text-xs text-red-300" @click="uninstall(item)">Uninstall</button>
          </div>
        </div>
      </div>
      <p v-if="message" class="mt-6 text-sm text-emerald-300">{{ message }}</p>
      <p v-if="error" class="mt-6 text-sm text-red-300">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const { isLoggedIn } = useAuth()
const listings = ref<any[]>([])
const installations = ref<any[]>([])
const message = ref('')
const error = ref('')
async function loadInstallations() {
  if (!isLoggedIn.value) return
  const res = await apiFetch<any>('/marketplace/installations/my')
  installations.value = res.items || []
}
async function install(listing: any) {
  if (!isLoggedIn.value) return navigateTo('/login?redirect=/marketplace')
  try {
    await apiFetch(`/marketplace/listings/${listing.id}/install`, { method: 'POST', body: {} })
    message.value = `${listing.name} installed. No data permission was granted automatically.`
    await loadInstallations()
  } catch (e: any) {
    error.value = e?.data?.detail || 'Installation failed'
  }
}
async function uninstall(item: any) {
  await apiFetch(`/marketplace/installations/${item.id}/uninstall`, { method: 'POST' })
  await loadInstallations()
}
onMounted(async () => {
  const res = await apiFetch<any>('/marketplace/listings')
  listings.value = res.items || []
  await loadInstallations()
})
</script>
