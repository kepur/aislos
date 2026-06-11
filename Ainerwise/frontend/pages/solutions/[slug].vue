<template>
  <div v-if="solution" class="section-padding">
    <div class="container-main">
      <NuxtLink to="/solutions" class="text-sm text-primary-400 hover:underline">&larr; {{ $t('solutions.title') }}</NuxtLink>

      <h1 class="text-3xl font-bold text-white mt-4 drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ solution.title }}</h1>
      <p class="mt-4 text-slate-300 text-lg">{{ solution.description }}</p>

      <!-- Target Scenarios -->
      <section v-if="solution.target_scenarios_json?.length" class="mt-10">
        <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.targetScenarios') }}</h2>
        <div class="flex flex-wrap gap-2">
          <span v-for="s in solution.target_scenarios_json" :key="s" class="bg-primary-900/50 border border-primary-500/30 text-primary-300 px-3 py-1 rounded-full text-sm">{{ s }}</span>
        </div>
      </section>

      <!-- Pain Points -->
      <section v-if="solution.pain_points_json?.length" class="mt-10 glass-panel p-6 border-white/10">
        <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.commonPainPoints') }}</h2>
        <ul class="space-y-2">
          <li v-for="p in solution.pain_points_json" :key="p" class="flex items-start gap-2 text-slate-300">
            <span class="text-red-400 mt-0.5">&#10007;</span>
            {{ p }}
          </li>
        </ul>
      </section>

      <!-- Budget Tiers -->
      <section v-if="solution.budget_tiers_json" class="mt-10">
        <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.budgetTiers') }}</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div
            v-for="(tier, key) in solution.budget_tiers_json"
            :key="key"
            class="glass-panel p-5 border-primary-500/30"
          >
            <h3 class="font-semibold text-white">{{ tier.label }}</h3>
            <p class="text-sm text-slate-400 mt-1">{{ tier.description }}</p>
            <p v-if="tier.starting_from" class="mt-2 text-lg font-bold text-primary-400">
              {{ $t('services.startingFrom') }} &euro;{{ tier.starting_from }}
            </p>
          </div>
        </div>
      </section>

      <!-- Delivery Flow -->
      <section v-if="solution.delivery_flow_json?.length" class="mt-10 glass-panel p-6 border-primary-500/30">
        <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.deliveryFlow') }}</h2>
        <div class="flex flex-wrap gap-2 items-center">
          <template v-for="(step, i) in solution.delivery_flow_json" :key="i">
            <span class="bg-primary-900/40 border border-primary-500/50 text-primary-300 px-3 py-1 rounded text-sm font-medium">{{ step }}</span>
            <span v-if="i < solution.delivery_flow_json.length - 1" class="text-slate-500">&rarr;</span>
          </template>
        </div>
      </section>

      <!-- CTA -->
      <div class="mt-12 text-center">
        <NuxtLink :to="`/submit-requirement?solution=${solution.slug}`" class="btn-primary text-lg shadow-[0_0_15px_rgba(14,165,233,0.3)]">
          {{ $t('solutions.submitCta') }}
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiFetch } = useApi()
const solution = ref<any>(null)

onMounted(async () => {
  try {
    solution.value = await apiFetch<any>(`/solutions/${route.params.slug}`)
  } catch {}
})
</script>
