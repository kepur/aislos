<template>
  <div class="space-y-16">
    <section class="mx-auto max-w-5xl py-12 text-center">
      <p class="text-xs font-bold uppercase tracking-[0.25em] text-indigo-400">AinerWise Cebu Procurement</p>
      <h1 class="mt-5 text-4xl font-bold text-white sm:text-6xl">{{ $t('mktP.heroTitle') }}</h1>
      <p class="mx-auto mt-6 max-w-2xl text-slate-400">{{ $t('mktP.heroSubtitle') }}</p>
      <div class="mt-8 flex flex-wrap justify-center gap-3"><NuxtLink :to="localized('/market/post-request')" class="btn-primary">{{ $t('mkt.postRequest') }}</NuxtLink><NuxtLink :to="localized('/market/marketplace')" class="btn-secondary">{{ $t('portal.ideal.browse') }}</NuxtLink><NuxtLink :to="localized('/market/buyer/dashboard')" class="btn-secondary">{{ $t('mktP.buyerWorkspace') }}</NuxtLink></div>
    </section>
    <section class="grid gap-4 md:grid-cols-4"><div v-for="item in steps" :key="item.title" class="pc-card"><p class="text-xs font-bold text-indigo-400">{{ item.step }}</p><h2 class="mt-2 font-semibold text-white">{{ $t(item.title) }}</h2><p class="mt-2 text-sm text-slate-500">{{ $t(item.body) }}</p></div></section>
    <CebuPublicMarketplace />
  </div>
</template>
<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'default' })
const steps = [
  { step: '01', title: 'mktP.s1t', body: 'mktP.s1b' },
  { step: '02', title: 'mktP.s2t', body: 'mktP.s2b' },
  { step: '03', title: 'mktP.s3t', body: 'mktP.s3b' },
  { step: '04', title: 'mktP.s4t', body: 'mktP.s4b' },
]
</script>
