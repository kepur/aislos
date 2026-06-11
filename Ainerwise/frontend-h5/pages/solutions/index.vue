<template>
  <div class="px-4 py-4">
    <h1 class="text-lg font-bold text-slate-800 mb-1">{{ $t('solutions.title') }}</h1>
    <p class="text-xs text-slate-400 mb-4">{{ $t('solutions.subtitle') }}</p>

    <div class="space-y-3">
      <NuxtLink
        v-for="solution in solutions"
        :key="solution.slug"
        :to="`/solutions/${solution.slug}`"
        class="block bg-white rounded-xl p-4 border border-slate-100 shadow-sm active:bg-slate-50 transition"
      >
        <div class="flex items-start gap-3">
          <div class="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-sm font-semibold text-slate-800">{{ solution.title }}</h2>
            <p class="text-xs text-slate-400 mt-1 line-clamp-2">{{ solution.description }}</p>
            <div v-if="solution.target_scenarios_json" class="mt-2 flex flex-wrap gap-1">
              <span v-for="s in solution.target_scenarios_json.slice(0, 3)" :key="s"
                class="text-[10px] text-blue-500 bg-blue-50 px-2 py-0.5 rounded-full">{{ s }}</span>
            </div>
          </div>
          <svg class="w-4 h-4 text-slate-300 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </div>
      </NuxtLink>

    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const { demoSolutions } = useDemoCatalog()
const solutions = ref<any[]>(demoSolutions)

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/solutions')
    solutions.value = res.items || res || []
  } catch {}
  if (!solutions.value.length) {
    solutions.value = demoSolutions
  }
})
</script>
