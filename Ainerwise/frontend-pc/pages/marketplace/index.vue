<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between mb-10">
        <div>
          <p class="text-xs font-bold tracking-[0.25em] text-primary-400 uppercase">{{ $t('agentMarketplace.eyebrow') }}</p>
          <h1 class="mt-3 text-4xl font-bold text-white">{{ $t('agentMarketplace.title') }}</h1>
          <p class="mt-3 max-w-3xl text-slate-400">
            {{ $t('agentMarketplace.subtitle') }}
          </p>
        </div>
        <NuxtLink to="/developers" class="btn-secondary text-center">{{ $t('agentMarketplace.buildCta') }}</NuxtLink>
      </div>

      <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="listing in listings" :key="listing.id" class="glass-panel marketplace-card p-5">
          <div class="flex items-start justify-between gap-3">
            <div>
              <h2 class="text-lg font-semibold text-white">{{ listing.name }}</h2>
              <p class="text-xs text-primary-300">{{ listing.role_title || $t('agentMarketplace.aiEmployee') }}</p>
            </div>
            <span class="rounded-full border border-emerald-400/30 px-2 py-1 text-[10px] text-emerald-300">{{ $t('agentMarketplace.reviewed') }}</span>
          </div>
          <p class="mt-4 line-clamp-3 text-sm text-slate-400">{{ listing.description || $t('agentMarketplace.fallbackDesc') }}</p>
          <div class="mt-4 flex flex-wrap gap-1">
            <span v-for="workflow in listing.workflows" :key="workflow" class="rounded bg-white/5 px-2 py-1 text-[10px] font-mono text-slate-400">{{ workflow }}</span>
          </div>
          <div class="mt-5 flex items-center justify-between">
            <span class="font-semibold text-white">{{ priceLabel(listing) }}</span>
            <button class="btn-primary !px-4 !py-2 text-sm" @click="install(listing)">{{ $t('agentMarketplace.install') }}</button>
          </div>
        </article>
      </div>

      <div v-if="isLoggedIn" class="mt-12">
        <h2 class="text-xl font-semibold text-white">{{ $t('agentMarketplace.myAgents') }}</h2>
        <div class="mt-4 grid gap-3 md:grid-cols-2">
          <div v-for="item in installations" :key="item.id" class="glass-panel marketplace-card flex items-center justify-between gap-4 p-4">
            <div>
              <p class="font-medium text-white">{{ item.name }}</p>
              <p class="text-xs text-slate-400">{{
                $t('agentMarketplace.installMeta', { status: item.status, workspace: item.workspace_id })
              }}</p>
            </div>
            <button v-if="item.status === 'installed'" class="text-xs text-red-300" @click="uninstall(item)">{{ $t('agentMarketplace.uninstall') }}</button>
          </div>
        </div>
      </div>
      <p v-if="message" class="mt-6 text-sm text-emerald-300">{{ message }}</p>
      <p v-if="error" class="mt-6 text-sm text-red-300">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { apiFetch } = useApi()
const { isLoggedIn } = useAuth()
const { activeWorkspaceId, loadAccess } = usePortalManifest()
const listings = ref<any[]>([])
const installations = ref<any[]>([])
const message = ref('')
const error = ref('')

function priceLabel(listing: any) {
  if (listing.price_monthly == null) return t('agentMarketplace.included')
  return t('agentMarketplace.perMonth', { price: listing.price_monthly, currency: listing.currency })
}

async function loadInstallations() {
  if (!isLoggedIn.value) return
  if (!activeWorkspaceId.value) {
    error.value = t('agentMarketplace.selectWorkspace')
    installations.value = []
    return
  }
  const res = await apiFetch<any>(`/marketplace/installations/my?workspace_id=${activeWorkspaceId.value}`)
  installations.value = res.items || []
}
async function install(listing: any) {
  if (!isLoggedIn.value) return navigateTo('/login?redirect=/marketplace')
  if (!activeWorkspaceId.value) {
    error.value = t('agentMarketplace.selectWorkspaceInstall')
    return
  }
  try {
    await apiFetch(`/marketplace/listings/${listing.id}/install`, {
      method: 'POST',
      body: { workspace_id: activeWorkspaceId.value },
    })
    message.value = t('agentMarketplace.installedOk', { name: listing.name })
    await loadInstallations()
  } catch (e: any) {
    error.value = e?.data?.detail || t('agentMarketplace.installFailed')
  }
}
async function uninstall(item: any) {
  await apiFetch(`/marketplace/installations/${item.id}/uninstall`, { method: 'POST' })
  await loadInstallations()
}
onMounted(async () => {
  const res = await apiFetch<any>('/marketplace/listings')
  listings.value = res.items || []
  if (isLoggedIn.value) await loadAccess()
  await loadInstallations()
})
</script>

<style scoped>
.marketplace-card {
  min-height: 100%;
  background:
    linear-gradient(165deg, #ffffff 0%, #f3f7f4 55%, #eef3f0 100%) !important;
  border: 1px solid #d5ddd8 !important;
  box-shadow: 0 1px 2px rgba(13, 27, 22, 0.04), 0 8px 22px rgba(13, 27, 22, 0.05) !important;
}
.marketplace-card:hover {
  border-color: #b9c8c0 !important;
  box-shadow: 0 2px 6px rgba(13, 27, 22, 0.06), 0 12px 28px rgba(13, 27, 22, 0.08) !important;
}
:global(html.light) .marketplace-card {
  background:
    linear-gradient(165deg, #ffffff 0%, #f5f7fb 55%, #eef2f7 100%) !important;
  border-color: rgba(15, 23, 42, 0.12) !important;
}
:global(.dark) .marketplace-card,
:global(html:not(.light):not(.theme-knx)) .marketplace-card {
  background:
    linear-gradient(165deg, rgba(30, 41, 59, 0.92) 0%, rgba(15, 23, 42, 0.88) 100%) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25) !important;
}
</style>
