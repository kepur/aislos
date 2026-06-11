<template>
  <div class="section-padding">
    <div class="container-main max-w-6xl">
      <div class="grid gap-10 lg:grid-cols-[1.1fr_.9fr] lg:items-center">
        <div>
          <p class="text-xs font-bold tracking-[0.25em] text-primary-400 uppercase">AISLOS Developer Portal</p>
          <h1 class="mt-4 text-5xl font-bold text-white">Build AI employees that enter real workflows safely.</h1>
          <p class="mt-5 text-lg text-slate-400">
            Publish Agent manifests, request the minimum scopes, pass human review, and reach solution companies through the Agent Marketplace.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <NuxtLink to="/developers/listings" class="btn-primary">Submit an Agent</NuxtLink>
            <NuxtLink to="/marketplace" class="btn-secondary">Browse Marketplace</NuxtLink>
          </div>
        </div>
        <div class="glass-panel p-6">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-white">Manifest v{{ manifest.manifest_version || '1.0' }}</h2>
            <span class="text-xs text-emerald-300">Governed by default</span>
          </div>
          <pre class="mt-5 overflow-x-auto rounded-lg bg-black/30 p-4 text-xs text-primary-200">{{ JSON.stringify(manifest.example || {}, null, 2) }}</pre>
        </div>
      </div>

      <div class="mt-16 grid gap-5 md:grid-cols-3">
        <article class="glass-panel p-5"><h2 class="font-semibold text-white">1. Submit</h2><p class="mt-2 text-sm text-slate-400">Describe workflows, pricing and requested scopes through a versioned manifest.</p></article>
        <article class="glass-panel p-5"><h2 class="font-semibold text-white">2. Human review</h2><p class="mt-2 text-sm text-slate-400">AISLOS reviews purpose and risk before any listing reaches customers.</p></article>
        <article class="glass-panel p-5"><h2 class="font-semibold text-white">3. Install safely</h2><p class="mt-2 text-sm text-slate-400">Third-party Agents start paused with all data grants denied.</p></article>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const manifest = ref<any>({})
onMounted(async () => {
  manifest.value = await apiFetch('/developer/sdk/manifest')
})
</script>
