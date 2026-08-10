<template>
  <div class="space-y-16">
    <section class="mx-auto max-w-5xl py-12 text-center">
      <p class="text-xs font-bold uppercase tracking-[0.25em] text-indigo-400">AinerWise Cebu Procurement</p>
      <h1 class="mt-5 text-4xl font-bold text-white sm:text-6xl">Tell AI what you need. Compare real supplier offers.</h1>
      <p class="mx-auto mt-6 max-w-2xl text-slate-400">Browse the public marketplace or create one structured procurement request. AinerWise handles sourcing, comparison, ordering, delivery and after-sales through the shared AISLOS operating system.</p>
      <div class="mt-8 flex flex-wrap justify-center gap-3"><NuxtLink :to="localized('/market/post-request')" class="btn-primary">Post a request</NuxtLink><NuxtLink :to="localized('/market/marketplace')" class="btn-secondary">Browse marketplace</NuxtLink><NuxtLink :to="localized('/market/buyer/dashboard')" class="btn-secondary">Buyer workspace</NuxtLink></div>
    </section>
    <section class="grid gap-4 md:grid-cols-4"><div v-for="item in steps" :key="item.title" class="pc-card"><p class="text-xs font-bold text-indigo-400">{{ item.step }}</p><h2 class="mt-2 font-semibold text-white">{{ item.title }}</h2><p class="mt-2 text-sm text-slate-500">{{ item.body }}</p></div></section>
    <CebuPublicMarketplace />
  </div>
</template>
<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'default' })
const steps = [
  { step: '01', title: 'Describe the outcome', body: 'Products, projects, installation and service requirements are accepted.' },
  { step: '02', title: 'AI structures the request', body: 'Facts, missing information and commercial scope are made explicit.' },
  { step: '03', title: 'Compare verified offers', body: 'Supplier offers remain tied to the same commercial request.' },
  { step: '04', title: 'Order and deliver', body: 'Track payment, shipment, messages, disputes and completion.' },
]
</script>
