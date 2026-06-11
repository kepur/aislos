<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('solutions.title') }}</h1>
        <p class="mt-3 text-slate-300">{{ $t('solutions.subtitle') }}</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
        <NuxtLink
          v-for="solution in solutions"
          :key="solution.slug"
          :to="`/solutions/${solution.slug}`"
          class="glass-panel p-6 transition border-primary-500/30 hover:shadow-[0_0_15px_rgba(14,165,233,0.3)]"
        >
          <h2 class="text-xl font-semibold text-white">{{ solution.title }}</h2>
          <p class="mt-2 text-slate-300 text-sm line-clamp-4">{{ solution.description }}</p>
          <div v-if="solution.target_scenarios_json" class="mt-3 flex flex-wrap gap-1">
            <span v-for="s in solution.target_scenarios_json" :key="s" class="text-xs bg-primary-900/50 text-primary-300 border border-primary-500/30 px-2 py-0.5 rounded">{{ s }}</span>
          </div>
          <span class="mt-4 inline-block text-sm text-primary-400 font-medium hover:text-primary-300">{{ $t('solutions.learnMore') }} &rarr;</span>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const solutions = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/solutions')
    solutions.value = res.items || res || []
  } catch {}
})
</script>
