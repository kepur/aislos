<template>
  <div>
    <AinerwiseImmersiveHero
      background-image="/images/brand/ainerwise-solutions-bg.svg"
      :eyebrow="$t('solutions.eyebrow')"
      :title="$t('solutions.title')"
      :subtitle="$t('solutions.subtitle')"
      :crumbs="[{ label: $t('nav.home'), to: '/' }, { label: $t('nav.solutions') }]"
      :badges="solutionHeroBadges"
      :stats="solutionHeroStats"
      :nodes="solutionHeroNodes"
      primary-to="/submit-requirement"
      :primary-label="$t('nav.submitRequirement')"
      secondary-to="/ai-building-brain"
      :secondary-label="$t('home.intelligenceExplore')"
      :core-label="$t('home.hubCore')"
    />

    <!-- The eight lines, as a KNX-style capability grid -->
    <KnxSectionBlock
      :eyebrow="$t('solutions.linesEyebrow')"
      :title="$t('home.solutionsTitle')"
      :subtitle="$t('home.solutionsSubtitle')"
      centered
    >
      <div class="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        <NuxtLink
          v-for="line in lines"
          :key="line.key"
          :to="`/solutions/${line.slug}`"
          class="glass-panel group flex flex-col p-6 transition"
        >
          <div class="flex items-start justify-between gap-3">
            <span
              class="flex h-12 w-12 items-center justify-center rounded-xl"
              :style="{ backgroundColor: 'var(--brand-soft, rgba(14,165,233,.12))' }"
            >
              <FeatureIcon
                :name="line.icon"
                class="transition-transform group-hover:scale-110"
                :style="{ color: 'var(--brand-strong, #38bdf8)' }"
              />
            </span>
            <span class="knx-pill !text-[10px]">{{ $t(`mtx.${line.tagKey}`) }}</span>
          </div>

          <h3 class="mt-4 text-lg font-bold text-white">{{ line.name }}</h3>
          <p class="mt-1 text-xs text-slate-400">{{ $t(`mtx.${line.key}_scene`) }}</p>

          <dl class="mt-4 flex-1 space-y-3 text-xs">
            <div>
              <dt class="font-semibold text-rose-400/90">{{ $t('mtx.risk') }}</dt>
              <dd class="mt-0.5 text-slate-300">{{ $t(`mtx.${line.key}_risk`) }}</dd>
            </div>
            <div>
              <dt class="font-semibold" :style="{ color: 'var(--brand-strong, #38bdf8)' }">{{ $t('mtx.outcome') }}</dt>
              <dd class="mt-0.5 text-slate-300">{{ $t(`mtx.${line.key}_outcome`) }}</dd>
            </div>
          </dl>

          <span class="mt-5 inline-flex items-center gap-1 text-sm font-semibold" :style="{ color: 'var(--brand-strong, #38bdf8)' }">
            {{ $t('solutions.learnMore') }}
            <span class="transition-transform group-hover:translate-x-1">→</span>
          </span>
        </NuxtLink>
      </div>
    </KnxSectionBlock>

    <!-- What every line has in common: the AI layer on top of the bus -->
    <KnxSectionBlock
      :eyebrow="$t('solutions.commonEyebrow')"
      :title="$t('solutions.commonTitle')"
      :subtitle="$t('solutions.commonSubtitle')"
      centered
      tinted
    >
      <KnxIconGrid :items="commonCapabilities" :columns="4" />
      <p class="mx-auto mt-8 max-w-3xl text-center text-xs leading-relaxed text-slate-400">
        {{ $t('mtx.guardrail') }}
      </p>
    </KnxSectionBlock>

    <!-- Backend catalogue: everything published, including partner solutions -->
    <KnxSectionBlock
      :eyebrow="$t('solutions.catalogEyebrow')"
      :title="$t('solutions.catalogTitle')"
      :subtitle="$t('solutions.catalogSubtitle')"
    >
      <div v-if="loading" class="glass-panel p-8 text-center text-sm text-slate-400">
        {{ $t('common.loading') }}
      </div>
      <div v-else-if="error" class="glass-panel border-red-500/30 p-6 text-center text-sm text-red-300">
        <p>{{ error }}</p>
        <button class="btn-primary mt-4" @click="loadSolutions">{{ $t('common.retry') }}</button>
      </div>
      <div v-else-if="!catalogue.length" class="glass-panel p-8 text-center text-sm text-slate-400">
        {{ $t('solutions.empty') }}
      </div>
      <div v-else class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <NuxtLink
          v-for="solution in catalogue"
          :key="solution.slug"
          :to="`/solutions/${solution.slug}`"
          class="glass-panel p-6 transition"
        >
          <h3 class="text-lg font-semibold text-white">{{ solution.title }}</h3>
          <p class="mt-2 line-clamp-3 text-sm text-slate-300">{{ solution.description }}</p>
          <div v-if="solution.target_scenarios_json?.length" class="mt-3 flex flex-wrap gap-1.5">
            <span v-for="s in solution.target_scenarios_json.slice(0, 3)" :key="s" class="knx-pill !text-[10px]">{{ s }}</span>
          </div>
          <span class="mt-4 inline-block text-sm font-semibold" :style="{ color: 'var(--brand-strong, #38bdf8)' }">
            {{ $t('solutions.learnMore') }} →
          </span>
        </NuxtLink>
      </div>
    </KnxSectionBlock>

    <KnxCtaBand
      :title="$t('home.ctaTitle')"
      :subtitle="$t('home.ctaSubtitle')"
      primary-to="/submit-requirement"
      :primary-label="$t('nav.submitRequirement')"
      secondary-to="/contact"
      :secondary-label="$t('nav.contact')"
    />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { apiFetch } = useApi()
const { lines } = useSolutionLines()
const { localizeSolution } = useLocalizedCatalog()

const lineSlugs = new Set(lines.map((l) => l.slug))

const { data: solutionsData, pending: loading, error: loadError, refresh: loadSolutions } = await useAsyncData(
  'solutions-catalogue',
  async () => {
    const res = await apiFetch<any>('/solutions')
    return res.items || res || []
  },
  { default: () => [] },
)

const error = computed(() =>
  loadError.value
    ? (loadError.value as any)?.data?.detail || (loadError.value as any)?.message || t('solutions.loadError')
    : '',
)

const catalogue = computed(() =>
  (solutionsData.value || [])
    .filter((s: any) => !lineSlugs.has(s.slug) && !String(s.slug).startsWith('private-solution-'))
    .map(localizeSolution),
)

const commonCapabilities = computed(() => [
  { icon: 'ai-brain', label: t('solutions.capAssess'), hint: t('solutions.capAssessHint'), ai: true },
  { icon: 'network', label: t('solutions.capIntegrate'), hint: t('solutions.capIntegrateHint') },
  { icon: 'sensor', label: t('solutions.capMonitor'), hint: t('solutions.capMonitorHint') },
  { icon: 'lifecycle', label: t('solutions.capService'), hint: t('solutions.capServiceHint') },
])

const solutionHeroBadges = computed(() => [
  { label: t('solutions.badgeKnx') },
  { label: t('solutions.badgeAi'), ai: true },
  { label: t('procurement.title') },
])
const solutionHeroStats = computed(() => [
  { value: '8', label: t('solutions.linesEyebrow') },
  { value: 'AI', label: t('solutions.capAssess') },
  { value: 'RFQ', label: t('procurement.title') },
])
const solutionHeroNodes = computed(() => lines.slice(0, 5).map((line) => line.name))

useHead({ title: () => `${t('solutions.title')} — AinerWise` })
</script>
