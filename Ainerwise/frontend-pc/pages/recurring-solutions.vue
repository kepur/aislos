<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="text-center max-w-3xl mx-auto">
        <p class="text-sm font-bold uppercase tracking-wider text-primary-400">{{ $t('rec.kicker') }}</p>
        <h1 class="mt-3 text-3xl sm:text-4xl font-bold text-white">{{ $t('rec.title') }}</h1>
        <p class="mt-4 text-slate-300">{{ $t('rec.subtitle') }}</p>
      </div>

      <div class="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div v-for="b in why" :key="b.t" class="glass-panel p-6 border-white/10">
          <h2 class="text-lg font-semibold text-white">{{ $t(b.t) }}</h2>
          <p class="mt-2 text-sm text-slate-300">{{ $t(b.x) }}</p>
        </div>
      </div>

      <div class="mt-12">
        <h2 class="text-2xl font-bold text-white text-center mb-8">{{ $t('rec.carriersTitle') }}</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div v-for="c in carriers" :key="c" class="glass-panel p-4 text-center border-emerald-500/30">
            <span class="text-sm font-medium text-emerald-200">{{ $t(c) }}</span>
          </div>
        </div>
      </div>

      <div class="mt-12 glass-panel border-amber-500/30 bg-amber-400/5 p-5 text-center">
        <p class="text-sm text-amber-200/90 max-w-3xl mx-auto">{{ $t('mtx.guardrail') }}</p>
      </div>

      <div class="mt-12 text-center flex flex-col sm:flex-row gap-4 justify-center">
        <NuxtLink to="/submit-requirement" class="btn-primary text-lg shadow-[0_0_15px_rgba(14,165,233,0.3)]">{{ $t('rec.cta1') }}</NuxtLink>
        <NuxtLink to="/services/amc" class="glass-panel text-white px-6 py-3 font-semibold hover:bg-white/10 transition">{{ $t('rec.cta2') }} &rarr;</NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const why = [
  { t: 'rec.why1_t', x: 'rec.why1_x' },
  { t: 'rec.why2_t', x: 'rec.why2_x' },
  { t: 'rec.why3_t', x: 'rec.why3_x' },
  { t: 'rec.why4_t', x: 'rec.why4_x' },
]
const carriers = ['rec.car1', 'rec.car2', 'rec.car3', 'rec.car4', 'rec.car5', 'rec.car6', 'rec.car7', 'rec.car8']
</script>
