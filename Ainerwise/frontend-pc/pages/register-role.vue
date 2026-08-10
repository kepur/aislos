<template>
  <section class="container-main section-padding space-y-8">
    <div class="mx-auto max-w-3xl text-center">
      <p class="pc-kicker">AinerWise Procurement</p>
      <h1 class="mt-3 text-4xl font-bold text-white">Choose how you work with us</h1>
      <p class="mt-3 text-slate-400">One account can gain more portal memberships later. Start with your primary role.</p>
    </div>
    <div class="mx-auto grid max-w-5xl gap-5 md:grid-cols-3">
      <NuxtLink :to="localized('/register-buyer')" class="pc-card block">
        <p class="pc-kicker">Buyer</p>
        <h2 class="mt-3 text-xl font-bold text-white">Source a solution</h2>
        <p class="mt-2 text-sm text-slate-400">Post requirements, compare offers, award orders and track delivery.</p>
      </NuxtLink>
      <NuxtLink :to="localized('/register-supplier')" class="pc-card block">
        <p class="pc-kicker">Supplier</p>
        <h2 class="mt-3 text-xl font-bold text-white">Sell products and services</h2>
        <p class="mt-2 text-sm text-slate-400">Receive matching RFQs, quote, fulfil orders and manage your catalog.</p>
      </NuxtLink>
      <div class="pc-card opacity-70">
        <p class="pc-kicker-muted">Platform staff</p>
        <h2 class="mt-3 text-xl font-bold text-white">Invite only</h2>
        <p class="mt-2 text-sm text-slate-400">Internal AISLOS workbenches require an administrator-issued membership.</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ middleware: 'guest' })
</script>
