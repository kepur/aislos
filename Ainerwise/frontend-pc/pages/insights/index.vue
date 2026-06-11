<template>
  <div class="max-w-5xl mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold text-gray-900 mb-2">{{ $t('insights.title') }}</h1>
    <p class="text-gray-500 mb-8">{{ $t('insights.subtitle') }}</p>
    <div class="grid gap-6 md:grid-cols-2">
      <NuxtLink
        v-for="p in pages"
        :key="p.slug"
        :to="`/insights/${p.slug}`"
        class="block border border-gray-200 rounded-2xl p-6 hover:border-gray-400 hover:shadow-sm transition"
      >
        <h2 class="text-lg font-semibold text-gray-900 mb-2">{{ p.title }}</h2>
        <p class="text-sm text-gray-500 line-clamp-3">{{ p.meta_description }}</p>
      </NuxtLink>
    </div>
    <p v-if="!pages.length" class="text-gray-400 py-12 text-center">{{ $t('insights.empty') }}</p>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const { locale } = useI18n()
const pages = ref<any[]>([])

const { data } = await useAsyncData('insights', () =>
  apiFetch<any>(`/seo/pages?lang=${locale.value}`).catch(() => ({ items: [] })),
)
pages.value = data.value?.items || []

useHead({ title: 'Insights — AinerWise' })
</script>
