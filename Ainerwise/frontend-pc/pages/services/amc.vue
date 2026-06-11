<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="text-center max-w-3xl mx-auto">
        <p class="text-sm font-bold uppercase tracking-wider text-primary-400">{{ $t('amcp.kicker') }}</p>
        <h1 class="mt-3 text-3xl sm:text-4xl font-bold text-white">{{ $t('amcp.title') }}</h1>
        <p class="mt-4 text-slate-300">{{ $t('amcp.subtitle') }}</p>
      </div>

      <div class="mt-10 glass-panel p-5 border-emerald-500/30 text-center">
        <h2 class="font-semibold text-white">{{ $t('amcp.baselineTitle') }}</h2>
        <p class="mt-1 text-sm text-slate-300">{{ $t('amcp.baselineDesc') }}</p>
      </div>

      <div class="mt-10 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        <div v-for="tier in tiers" :key="tier.k" class="glass-panel p-5 border-primary-500/30 flex flex-col">
          <h3 class="text-lg font-bold text-white">{{ $t(`amcp.${tier.k}_name`) }}</h3>
          <p class="mt-1 text-xs text-slate-400">{{ $t(`amcp.${tier.k}_suit`) }}</p>
          <div class="mt-3 flex-1">
            <p class="text-xs font-semibold text-emerald-300">{{ $t('amcp.includesLabel') }}</p>
            <ul class="mt-1 space-y-1">
              <li v-for="i in $t(`amcp.${tier.k}_inc`).split('·')" :key="i" class="text-xs text-slate-300 flex gap-1.5"><span class="text-emerald-400">&#10003;</span>{{ i.trim() }}</li>
            </ul>
            <p class="mt-3 text-xs font-semibold text-red-300/80">{{ $t('amcp.excludesLabel') }}</p>
            <p class="text-xs text-slate-400">{{ $t(`amcp.${tier.k}_exc`) }}</p>
          </div>
          <NuxtLink to="/submit-requirement" class="mt-4 text-sm text-primary-400 font-medium hover:text-primary-300">{{ $t('amcp.requestTier') }} {{ $t(`amcp.${tier.k}_name`) }} &rarr;</NuxtLink>
        </div>
      </div>

      <div class="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass-panel p-6 border-white/10">
          <h2 class="text-lg font-semibold text-white">{{ $t('amcp.pricingTitle') }}</h2>
          <p class="mt-2 text-sm text-slate-300">{{ $t('amcp.pricingText') }}</p>
        </div>
        <div class="glass-panel p-6 border-white/10">
          <h2 class="text-lg font-semibold text-white">{{ $t('amcp.renewalTitle') }}</h2>
          <p class="mt-2 text-sm text-slate-300">{{ $t('amcp.renewalText') }}</p>
        </div>
      </div>

      <div class="mt-10 text-center">
        <NuxtLink to="/submit-requirement" class="btn-primary text-lg">{{ $t('rec.cta1') }}</NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const tiers = [{ k: 't1' }, { k: 't2' }, { k: 't3' }, { k: 't4' }]
</script>
