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
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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

      <!-- Lifecycle landing (StorageGuard and future lifecycle solution lines) -->
      <template v-if="solution.lifecycle_content_json">
        <p v-if="solution.lifecycle_content_json.headline" class="mt-10 text-lg font-semibold text-primary-200">
          {{ solution.lifecycle_content_json.headline }}
        </p>

        <section v-if="solution.lifecycle_content_json.monitoring_points?.length" class="mt-8">
          <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.monitoringPoints') }}</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div v-for="point in solution.lifecycle_content_json.monitoring_points" :key="point.name" class="glass-panel p-5 border-primary-500/30">
              <h3 class="font-semibold text-white">{{ point.name }}</h3>
              <p class="text-sm text-slate-300 mt-1">{{ point.detail }}</p>
            </div>
          </div>
        </section>

        <section v-if="solution.lifecycle_content_json.alert_channels?.length" class="mt-8 glass-panel p-6 border-white/10">
          <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.alertChannels') }}</h2>
          <div class="flex flex-wrap gap-2">
            <span v-for="ch in solution.lifecycle_content_json.alert_channels" :key="ch" class="bg-primary-900/50 border border-primary-500/30 text-primary-300 px-3 py-1 rounded-full text-sm">{{ ch }}</span>
          </div>
        </section>

        <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section v-if="solution.lifecycle_content_json.reports?.length" class="glass-panel p-6 border-white/10">
            <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.complianceReports') }}</h2>
            <ul class="space-y-2">
              <li v-for="r in solution.lifecycle_content_json.reports" :key="r" class="flex items-start gap-2 text-slate-300 text-sm">
                <span class="text-primary-400 mt-0.5">&#9656;</span>{{ r }}
              </li>
            </ul>
          </section>
          <section v-if="solution.lifecycle_content_json.calibration_consumables?.length" class="glass-panel p-6 border-white/10">
            <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.calibrationConsumables') }}</h2>
            <ul class="space-y-2">
              <li v-for="c in solution.lifecycle_content_json.calibration_consumables" :key="c" class="flex items-start gap-2 text-slate-300 text-sm">
                <span class="text-primary-400 mt-0.5">&#9656;</span>{{ c }}
              </li>
            </ul>
          </section>
        </div>

        <section v-if="solution.lifecycle_content_json.recurring_charges?.length" class="mt-8 glass-panel p-6 border-primary-500/30">
          <h2 class="text-xl font-semibold text-white mb-2">{{ $t('solutions.recurringValue') }}</h2>
          <p class="text-sm text-slate-400 mb-4">{{ $t('solutions.recurringValueDesc') }}</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="charge in solution.lifecycle_content_json.recurring_charges" :key="charge" class="bg-emerald-400/10 border border-emerald-500/30 text-emerald-200 px-3 py-1 rounded-full text-sm">{{ charge }}</span>
          </div>
        </section>

        <section v-if="solution.lifecycle_content_json.amc_options?.length" class="mt-8">
          <h2 class="text-xl font-semibold text-white mb-4">{{ $t('solutions.amcOptions') }}</h2>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div v-for="amc in solution.lifecycle_content_json.amc_options" :key="amc.name" class="glass-panel p-5 border-primary-500/30">
              <h3 class="font-semibold text-white">{{ amc.name }} {{ $t('solutions.amcSuffix') }}</h3>
              <p class="text-sm text-slate-300 mt-1">{{ amc.detail }}</p>
            </div>
          </div>
        </section>

        <div v-if="solution.lifecycle_content_json.service_boundary" class="mt-8 bg-amber-400/10 border border-amber-500/30 p-4 text-sm text-amber-200">
          {{ solution.lifecycle_content_json.service_boundary }}
        </div>
      </template>

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
const { demoSolutions } = useDemoCatalog()
const solution = ref<any>(demoSolutions.find((item) => item.slug === route.params.slug) || null)

onMounted(async () => {
  try {
    solution.value = await apiFetch<any>(`/solutions/${route.params.slug}`)
  } catch {}

  if (!solution.value) {
    solution.value = demoSolutions.find((item) => item.slug === route.params.slug)
  }
})
</script>
