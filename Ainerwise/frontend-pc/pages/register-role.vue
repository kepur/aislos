<template>
  <section class="container-main section-padding space-y-8">
    <div class="mx-auto max-w-3xl text-center">
      <p class="pc-kicker">AinerWise Procurement</p>
      <h1 class="mt-3 text-4xl font-bold text-white">{{ $t('authP.chooseHow') }}</h1>
      <p class="mt-3 text-slate-400">{{ $t('authP.oneAccount') }}</p>
    </div>
    <div class="mx-auto grid max-w-5xl gap-5 md:grid-cols-3">
      <NuxtLink :to="localized('/register-buyer')" class="pc-card block">
        <p class="pc-kicker">{{ $t('authP.rrBuyer') }}</p>
        <h2 class="mt-3 text-xl font-bold text-white">{{ $t('authP.srcSolution') }}</h2>
        <p class="mt-2 text-sm text-slate-400">{{ $t('authP.srcSolutionDesc') }}</p>
      </NuxtLink>
      <NuxtLink :to="localized('/register-supplier')" class="pc-card block">
        <p class="pc-kicker">{{ $t('authP.rrSupplier') }}</p>
        <h2 class="mt-3 text-xl font-bold text-white">{{ $t('authP.sellProducts') }}</h2>
        <p class="mt-2 text-sm text-slate-400">{{ $t('authP.sellDesc') }}</p>
      </NuxtLink>
      <div class="pc-card opacity-70">
        <p class="pc-kicker-muted">{{ $t('authP.platformStaff') }}</p>
        <h2 class="mt-3 text-xl font-bold text-white">{{ $t('authP.inviteOnly') }}</h2>
        <p class="mt-2 text-sm text-slate-400">{{ $t('authP.inviteOnlyDesc') }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ middleware: 'guest' })
</script>
