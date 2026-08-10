<template>
  <div v-if="solution">
    <KnxPageHero
      :eyebrow="line ? $t('solutions.eyebrow') : $t('solutions.catalogEyebrow')"
      :title="solution.title"
      :subtitle="solution.description"
      :crumbs="[
        { label: $t('nav.home'), to: '/' },
        { label: $t('nav.solutions'), to: '/solutions' },
        { label: line?.name || solution.title },
      ]"
      :badges="heroBadges"
    >
      <template #actions>
        <NuxtLink :to="localized(`/submit-requirement?solution=${solution.slug}`)" class="btn-primary">
          {{ $t('solutions.submitCta') }}
        </NuxtLink>
        <NuxtLink :to="localized('/ai-building-brain')" class="btn-secondary">{{ $t('home.intelligenceExplore') }}</NuxtLink>
      </template>

      <!-- Scenarios read best as the hero aside: they answer "is this for me?" -->
      <template v-if="solution.target_scenarios_json?.length" #aside>
        <div class="glass-panel p-6">
          <h2 class="knx-eyebrow">{{ $t('solutions.targetScenarios') }}</h2>
          <div class="mt-4 flex flex-wrap gap-2">
            <span v-for="s in solution.target_scenarios_json" :key="s" class="knx-pill">{{ s }}</span>
          </div>
        </div>
      </template>
    </KnxPageHero>

    <!-- Building systems this line touches (KNX-style capability grid) -->
    <KnxSectionBlock
      v-if="line?.systems?.length"
      :eyebrow="$t('solutions.eyebrow')"
      :title="$t('solutions.systemsTitle')"
      :subtitle="$t('solutions.systemsSubtitle')"
    >
      <KnxIconGrid :items="line.systems.map(s => ({ icon: s.icon, label: s.label }))" :columns="4" />
    </KnxSectionBlock>

    <!-- The differentiator: what the AI layer adds beyond a bus install -->
    <KnxSectionBlock
      v-if="line?.aiCapabilities?.length"
      :eyebrow="$t('solutions.badgeAi')"
      :title="$t('solutions.aiTitle')"
      :subtitle="$t('solutions.aiSubtitle')"
      tinted
    >
      <div class="grid gap-4 md:grid-cols-2">
        <div v-for="cap in line.aiCapabilities" :key="cap" class="glass-panel flex gap-4 p-5">
          <span class="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-sm font-bold text-indigo-600">✦</span>
          <p class="text-sm leading-relaxed text-slate-300">{{ cap }}</p>
        </div>
      </div>
    </KnxSectionBlock>

    <!-- Pain points -->
    <KnxSectionBlock
      v-if="solution.pain_points_json?.length"
      :title="$t('solutions.commonPainPoints')"
    >
      <ul class="grid gap-3 md:grid-cols-2">
        <li v-for="p in solution.pain_points_json" :key="p" class="glass-panel flex items-start gap-3 p-4">
          <span class="mt-0.5 text-rose-500">✕</span>
          <span class="text-sm text-slate-300">{{ p }}</span>
        </li>
      </ul>
    </KnxSectionBlock>

    <!-- What stays monitored -->
    <KnxSectionBlock
      v-if="line?.monitoring?.length"
      :title="$t('solutions.monitoringTitle')"
      :subtitle="$t('solutions.monitoringSubtitle')"
      tinted
    >
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="m in line.monitoring" :key="m" class="glass-panel p-5">
          <FeatureIcon name="sensor" size="sm" :style="{ color: 'var(--brand-strong, #38bdf8)' }" />
          <p class="mt-3 text-sm font-medium text-white">{{ m }}</p>
        </div>
      </div>
    </KnxSectionBlock>

    <!-- Budget tiers -->
    <KnxSectionBlock v-if="solution.budget_tiers_json" :title="$t('solutions.budgetTiers')">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="(tier, key) in solution.budget_tiers_json" :key="key" class="glass-panel p-5">
          <h3 class="font-semibold text-white">{{ tier.label }}</h3>
          <p class="mt-1 text-sm text-slate-400">{{ tier.description }}</p>
          <p v-if="tier.starting_from" class="mt-3 text-lg font-bold" :style="{ color: 'var(--brand-strong, #38bdf8)' }">
            {{ $t('services.startingFrom') }} &euro;{{ tier.starting_from }}
          </p>
        </div>
      </div>
    </KnxSectionBlock>

    <!-- Lifecycle content (StorageGuard and other lifecycle lines) -->
    <template v-if="solution.lifecycle_content_json">
      <KnxSectionBlock
        v-if="solution.lifecycle_content_json.monitoring_points?.length"
        :title="$t('solutions.monitoringPoints')"
        :subtitle="solution.lifecycle_content_json.headline"
        tinted
      >
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div v-for="point in solution.lifecycle_content_json.monitoring_points" :key="point.name" class="glass-panel p-5">
            <h3 class="font-semibold text-white">{{ point.name }}</h3>
            <p class="mt-1 text-sm text-slate-300">{{ point.detail }}</p>
          </div>
        </div>
      </KnxSectionBlock>

      <div class="container-main px-4 sm:px-6 lg:px-8">
        <section v-if="solution.lifecycle_content_json.alert_channels?.length" class="glass-panel mb-6 p-6">
          <h2 class="mb-4 text-lg font-semibold text-white">{{ $t('solutions.alertChannels') }}</h2>
          <div class="flex flex-wrap gap-2">
            <span v-for="ch in solution.lifecycle_content_json.alert_channels" :key="ch" class="knx-pill">{{ ch }}</span>
          </div>
        </section>

        <div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section v-if="solution.lifecycle_content_json.reports?.length" class="glass-panel p-6">
            <h2 class="mb-4 text-lg font-semibold text-white">{{ $t('solutions.complianceReports') }}</h2>
            <ul class="space-y-2">
              <li v-for="r in solution.lifecycle_content_json.reports" :key="r" class="flex items-start gap-2 text-sm text-slate-300">
                <span :style="{ color: 'var(--brand-strong, #38bdf8)' }">▸</span>{{ r }}
              </li>
            </ul>
          </section>
          <section v-if="solution.lifecycle_content_json.calibration_consumables?.length" class="glass-panel p-6">
            <h2 class="mb-4 text-lg font-semibold text-white">{{ $t('solutions.calibrationConsumables') }}</h2>
            <ul class="space-y-2">
              <li v-for="c in solution.lifecycle_content_json.calibration_consumables" :key="c" class="flex items-start gap-2 text-sm text-slate-300">
                <span :style="{ color: 'var(--brand-strong, #38bdf8)' }">▸</span>{{ c }}
              </li>
            </ul>
          </section>
        </div>

        <section v-if="solution.lifecycle_content_json.recurring_charges?.length" class="glass-panel mb-6 p-6">
          <h2 class="mb-2 text-lg font-semibold text-white">{{ $t('solutions.recurringValue') }}</h2>
          <p class="mb-4 text-sm text-slate-400">{{ $t('solutions.recurringValueDesc') }}</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="charge in solution.lifecycle_content_json.recurring_charges" :key="charge" class="knx-pill">{{ charge }}</span>
          </div>
        </section>

        <section v-if="solution.lifecycle_content_json.amc_options?.length" class="mb-6">
          <h2 class="mb-4 text-lg font-semibold text-white">{{ $t('solutions.amcOptions') }}</h2>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div v-for="amc in solution.lifecycle_content_json.amc_options" :key="amc.name" class="glass-panel p-5">
              <h3 class="font-semibold text-white">{{ amc.name }} {{ $t('solutions.amcSuffix') }}</h3>
              <p class="mt-1 text-sm text-slate-300">{{ amc.detail }}</p>
            </div>
          </div>
        </section>

        <div v-if="solution.lifecycle_content_json.service_boundary" class="mb-6 rounded-xl border border-amber-500/30 bg-amber-400/10 p-4 text-sm text-amber-700">
          {{ solution.lifecycle_content_json.service_boundary }}
        </div>
      </div>
    </template>

    <!-- Delivery flow -->
    <KnxSectionBlock v-if="solution.delivery_flow_json?.length" :title="$t('solutions.deliveryFlow')" tinted>
      <div class="flex flex-wrap items-center gap-2">
        <template v-for="(step, i) in solution.delivery_flow_json" :key="i">
          <span class="glass-panel px-4 py-2 text-sm font-medium text-white">{{ step }}</span>
          <span v-if="i < solution.delivery_flow_json.length - 1" class="text-slate-400">→</span>
        </template>
      </div>
    </KnxSectionBlock>

    <!-- Sibling lines keep visitors moving between the eight pages -->
    <KnxSectionBlock v-if="relatedLines.length" :title="$t('solutions.relatedTitle')">
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <NuxtLink
          v-for="rel in relatedLines"
          :key="rel.key"
          :to="localized(`/solutions/${rel.slug}`)"
          class="knx-tile group"
        >
          <span class="flex h-11 w-11 items-center justify-center rounded-xl" :style="{ backgroundColor: 'var(--brand-soft, rgba(14,165,233,.12))' }">
            <FeatureIcon :name="rel.icon" class="transition-transform group-hover:scale-110" :style="{ color: 'var(--brand-strong, #38bdf8)' }" />
          </span>
          <span class="text-sm font-semibold">{{ rel.name }}</span>
          <span class="text-xs text-slate-400">{{ $t(`mtx.${rel.key}_scene`) }}</span>
        </NuxtLink>
      </div>
    </KnxSectionBlock>

    <KnxCtaBand
      :title="$t('home.ctaTitle')"
      :subtitle="$t('home.ctaSubtitle')"
      :primary-to="`/submit-requirement?solution=${solution.slug}`"
      :primary-label="$t('solutions.submitCta')"
      secondary-to="/solutions"
      :secondary-label="$t('solutions.title')"
    />
  </div>

  <div v-else class="section-padding">
    <div class="container-main">
      <div v-if="loading" class="glass-panel p-8 text-center text-sm text-slate-400">{{ $t('common.loading') }}</div>
      <div v-else-if="error" class="glass-panel border-red-500/30 p-6 text-center text-sm text-red-300">
        <p>{{ error }}</p>
        <button class="btn-primary mt-4" @click="loadSolution">{{ $t('common.retry') }}</button>
      </div>
      <div v-else class="glass-panel p-8 text-center text-sm text-slate-400">
        {{ $t('solutions.empty') }}
        <div class="mt-4"><NuxtLink :to="localized('/solutions')" class="btn-secondary">{{ $t('solutions.title') }}</NuxtLink></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const route = useRoute()
const { t } = useI18n()
const { apiFetch } = useApi()
const { lines, bySlug } = useSolutionLines()
const { localizeSolution } = useLocalizedCatalog()

const solution = ref<any>(null)
const loading = ref(true)
const error = ref('')

/** Presentation metadata for the eight named lines; null for catalogue entries. */
const line = computed(() => bySlug(String(route.params.slug)))

const heroBadges = computed(() => {
  const badges: Array<{ label: string; ai?: boolean }> = []
  if (line.value) {
    badges.push({ label: t(`mtx.${line.value.tagKey}`) })
    badges.push({ label: t('solutions.badgeKnx') })
    if (line.value.aiCapabilities.length) badges.push({ label: t('solutions.badgeAi'), ai: true })
  }
  return badges
})

const relatedLines = computed(() =>
  lines.filter((l) => l.slug !== String(route.params.slug)).slice(0, 4)
)

async function loadSolution() {
  loading.value = true
  error.value = ''
  try {
    const raw = await apiFetch<any>(`/solutions/${route.params.slug}`)
    solution.value = localizeSolution(raw)
  } catch (e: any) {
    solution.value = null
    if (e?.response?.status !== 404) {
      error.value = e?.data?.detail || e?.message || t('solutions.loadError')
    }
  } finally {
    loading.value = false
  }
}

useHead({ title: () => `${solution.value?.title || t('solutions.title')} — AinerWise` })
onMounted(loadSolution)
</script>
