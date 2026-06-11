<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">{{ $t('marketingIntegration.hubTitle') }}</h1>
      <p class="admin-page-desc">{{ $t('marketingIntegration.hubDesc') }}</p>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <NuxtLink
        v-for="card in cards"
        :key="card.to"
        :to="card.to"
        class="glass-panel p-5 hover:border-cyan-500/30 transition block"
      >
        <p class="text-lg font-semibold text-white">{{ card.title }}</p>
        <p class="mt-2 text-sm text-slate-400">{{ card.desc }}</p>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { t } = useI18n()

const cards = computed(() => [
  {
    to: '/marketing/briefs',
    title: t('marketingIntegration.briefsTitle'),
    desc: t('marketingIntegration.briefsDesc'),
  },
  {
    to: '/marketing/clients',
    title: t('marketingIntegration.clientsTitle'),
    desc: t('marketingIntegration.clientsDesc'),
  },
  {
    to: '/marketing/imported-assets',
    title: t('marketingIntegration.importedTitle'),
    desc: t('marketingIntegration.importedDesc'),
  },
])
</script>
