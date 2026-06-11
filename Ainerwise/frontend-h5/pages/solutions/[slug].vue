<template>
  <div class="px-4 py-4">
    <!-- Back -->
    <NuxtLink to="/solutions" class="inline-flex items-center gap-1 text-xs font-medium text-blue-500 mb-4">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
      </svg>
      {{ $t('common.back') }}
    </NuxtLink>

    <div v-if="solution" class="space-y-4">
      <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div class="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center mb-4">
          <svg class="w-7 h-7 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-slate-800">{{ solution.title }}</h1>
        <p class="text-sm text-slate-500 mt-2 leading-relaxed">{{ solution.description }}</p>

        <div v-if="solution.target_scenarios_json" class="mt-4 flex flex-wrap gap-1.5">
          <span v-for="s in solution.target_scenarios_json" :key="s"
            class="text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full font-medium">{{ s }}</span>
        </div>
      </div>

      <div v-if="solution.key_components_json" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Key Components</h2>
        <div class="space-y-2">
          <div v-for="comp in solution.key_components_json" :key="comp"
            class="flex items-center gap-2 text-sm text-slate-600">
            <div class="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0"></div>
            {{ comp }}
          </div>
        </div>
      </div>

      <div v-if="solution.budget_tiers_json" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Budget Direction</h2>
        <div class="space-y-2">
          <div v-for="(tier, key) in solution.budget_tiers_json" :key="key" class="rounded-xl bg-slate-50 p-3">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-xs font-bold text-slate-800">{{ tier.label }}</h3>
              <span v-if="tier.starting_from" class="text-xs font-bold text-blue-600">from €{{ tier.starting_from }}</span>
              <span v-else class="text-[10px] font-semibold text-slate-500">Custom</span>
            </div>
            <p class="mt-1 text-[11px] leading-relaxed text-slate-500">{{ tier.description }}</p>
          </div>
        </div>
        <p class="mt-3 rounded-xl bg-amber-50 p-3 text-[11px] leading-relaxed text-amber-700">
          AI estimate only. Final quote requires manual review, site survey, supplier confirmation, and signed contract.
        </p>
      </div>

      <!-- Lifecycle landing (StorageGuard and future lifecycle solution lines) -->
      <template v-if="solution.lifecycle_content_json">
        <div v-if="solution.lifecycle_content_json.monitoring_points?.length" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('solutions.monitoringPoints') }}</h2>
          <div class="space-y-2">
            <div v-for="point in solution.lifecycle_content_json.monitoring_points" :key="point.name" class="rounded-xl bg-slate-50 p-3">
              <h3 class="text-xs font-bold text-slate-800">{{ point.name }}</h3>
              <p class="mt-1 text-[11px] leading-relaxed text-slate-500">{{ point.detail }}</p>
            </div>
          </div>
        </div>

        <div v-if="solution.lifecycle_content_json.alert_channels?.length" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('solutions.alertChannels') }}</h2>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="ch in solution.lifecycle_content_json.alert_channels" :key="ch" class="text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full font-medium">{{ ch }}</span>
          </div>
        </div>

        <div v-if="solution.lifecycle_content_json.reports?.length" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('solutions.complianceReports') }}</h2>
          <div class="space-y-2">
            <div v-for="r in solution.lifecycle_content_json.reports" :key="r" class="flex items-start gap-2 text-xs text-slate-600">
              <div class="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0 mt-1.5"></div>{{ r }}
            </div>
          </div>
        </div>

        <div v-if="solution.lifecycle_content_json.calibration_consumables?.length" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('solutions.calibrationConsumables') }}</h2>
          <div class="space-y-2">
            <div v-for="c in solution.lifecycle_content_json.calibration_consumables" :key="c" class="flex items-start gap-2 text-xs text-slate-600">
              <div class="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0 mt-1.5"></div>{{ c }}
            </div>
          </div>
        </div>

        <div v-if="solution.lifecycle_content_json.recurring_charges?.length" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-1">{{ $t('solutions.recurringValue') }}</h2>
          <p class="text-[11px] text-slate-400 mb-3">Long-term serviced facility, not a one-time device sale.</p>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="charge in solution.lifecycle_content_json.recurring_charges" :key="charge" class="text-xs text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full font-medium">{{ charge }}</span>
          </div>
        </div>

        <div v-if="solution.lifecycle_content_json.amc_options?.length" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('solutions.amcOptions') }}</h2>
          <div class="space-y-2">
            <div v-for="amc in solution.lifecycle_content_json.amc_options" :key="amc.name" class="rounded-xl bg-slate-50 p-3">
              <h3 class="text-xs font-bold text-slate-800">{{ amc.name }} {{ $t('solutions.amcSuffix') }}</h3>
              <p class="mt-1 text-[11px] leading-relaxed text-slate-500">{{ amc.detail }}</p>
            </div>
          </div>
        </div>

        <p v-if="solution.lifecycle_content_json.service_boundary" class="rounded-xl bg-amber-50 p-3 text-[11px] leading-relaxed text-amber-700">
          {{ solution.lifecycle_content_json.service_boundary }}
        </p>
      </template>

      <!-- CTA -->
      <div class="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl p-5 text-center text-white">
        <h3 class="text-base font-bold">Interested in this solution?</h3>
        <p class="text-xs text-blue-100 mt-1">Let our team help you get started</p>
        <NuxtLink to="/submit-requirement"
          class="inline-block mt-3 text-xs font-semibold bg-white text-blue-600 px-6 py-2.5 rounded-full shadow-md">
          {{ $t('nav.submitRequirement') }}
        </NuxtLink>
      </div>
    </div>

    <div v-else class="text-center py-20 text-slate-400">
      <div class="text-4xl mb-3">🔍</div>
      <p class="text-sm">Loading solution details...</p>
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
    const res = await apiFetch<any>(`/solutions/${route.params.slug}`)
    solution.value = res
  } catch {}
  if (!solution.value) {
    solution.value = demoSolutions.find((item) => item.slug === route.params.slug)
  }
})
</script>
