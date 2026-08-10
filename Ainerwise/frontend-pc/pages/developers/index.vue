<template>
  <div class="section-padding">
    <div class="container-main max-w-6xl">
      <div class="grid gap-10 lg:grid-cols-[1.1fr_.9fr] lg:items-center">
        <div>
          <p class="text-xs font-bold tracking-[0.25em] text-primary-400 uppercase">{{ $t('developersPortal.eyebrow') }}</p>
          <h1 class="mt-4 text-5xl font-bold text-white">{{ $t('developersPortal.title') }}</h1>
          <p class="mt-5 text-lg text-slate-400">
            {{ $t('developersPortal.subtitle') }}
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <NuxtLink to="/developers/listings" class="btn-primary">{{ $t('developersPortal.submitAgent') }}</NuxtLink>
            <NuxtLink to="/marketplace" class="btn-secondary">{{ $t('developersPortal.browseMarketplace') }}</NuxtLink>
          </div>
        </div>
        <div class="glass-panel p-6">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-white">{{ $t('developersPortal.manifestTitle', { version: manifest.manifest_version || '1.0' }) }}</h2>
            <span class="text-xs text-emerald-300">{{ $t('developersPortal.governed') }}</span>
          </div>
          <pre class="mt-5 overflow-x-auto rounded-lg bg-black/30 p-4 text-xs text-primary-200">{{ JSON.stringify(manifest.example || {}, null, 2) }}</pre>
        </div>
      </div>

      <div class="mt-16 grid gap-5 md:grid-cols-3">
        <article class="glass-panel p-5">
          <h2 class="font-semibold text-white">{{ $t('developersPortal.step1Title') }}</h2>
          <p class="mt-2 text-sm text-slate-400">{{ $t('developersPortal.step1Desc') }}</p>
        </article>
        <article class="glass-panel p-5">
          <h2 class="font-semibold text-white">{{ $t('developersPortal.step2Title') }}</h2>
          <p class="mt-2 text-sm text-slate-400">{{ $t('developersPortal.step2Desc') }}</p>
        </article>
        <article class="glass-panel p-5">
          <h2 class="font-semibold text-white">{{ $t('developersPortal.step3Title') }}</h2>
          <p class="mt-2 text-sm text-slate-400">{{ $t('developersPortal.step3Desc') }}</p>
        </article>
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
