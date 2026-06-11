<template>
  <div>
    <section class="text-white">
      <div class="container-main px-4 sm:px-6 lg:px-8 pt-14 lg:pt-20">
        <div class="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-10 items-center">
          <div class="pb-8 lg:pb-16 glass-panel p-8">
            <p class="text-sm font-semibold uppercase tracking-wider text-emerald-400">
              {{ $t('home.heroKicker') }}
            </p>
            <h1 class="mt-4 text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight text-white">
              {{ $t('home.heroTitle') }}
            </h1>
            <p class="mt-5 text-lg text-slate-300 max-w-2xl">
              {{ $t('home.heroSubtitle') }}
            </p>
            <div class="mt-8 flex flex-col sm:flex-row gap-3">
              <NuxtLink to="/submit-requirement" class="bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-500 transition">
                {{ $t('home.heroCta1') }}
              </NuxtLink>
              <NuxtLink to="/procurement" class="glass-panel text-emerald-300 px-6 py-3 font-semibold hover:bg-white/10 transition">
                {{ $t('procurement.title') }}
              </NuxtLink>
              <NuxtLink to="/ai-building-brain" class="glass-panel text-cyan-300 px-6 py-3 font-semibold hover:bg-white/10 transition">
                {{ $t('home.heroCta2') }}
              </NuxtLink>
              <NuxtLink to="/demo-login" class="glass-panel text-slate-300 px-6 py-3 font-semibold hover:bg-white/10 transition">
                {{ $t('home.heroCta3') }}
              </NuxtLink>
            </div>
            <div class="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-slate-300">
              <div v-for="signal in heroSignals" :key="signal" class="glass-panel px-3 py-2 text-center">
                {{ signal }}
              </div>
            </div>
          </div>
          <div class="lg:-mb-10">
            <BuildingBrainMap compact />
          </div>
        </div>
      </div>
    </section>

    <section class="section-padding">
      <div class="container-main">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div v-for="item in operatingModel" :key="item.kicker" class="glass-panel p-6 hover:border-primary-500/50 transition">
            <p class="text-xs font-semibold uppercase tracking-wider text-primary-400">{{ item.kicker }}</p>
            <h2 class="mt-2 font-bold text-white text-xl">{{ item.title }}</h2>
            <p class="mt-2 text-sm text-slate-300">{{ item.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Solution Matrix (FI.0.5) -->
    <section class="section-padding">
      <div class="container-main">
        <div class="text-center mb-12">
          <h2 class="text-2xl sm:text-3xl font-bold text-white">{{ $t('home.solutionsTitle') }}</h2>
          <p class="mt-3 text-slate-300 max-w-2xl mx-auto">{{ $t('home.solutionsSubtitle') }}</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
          <div
            v-for="line in solutionMatrix"
            :key="line.key"
            class="glass-panel p-5 flex flex-col hover:border-primary-400/60 transition"
          >
            <div class="flex items-center justify-between gap-2">
              <h3 class="text-base font-bold text-white">{{ line.name }}</h3>
              <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                :class="line.tagClass">{{ $t(`mtx.${line.tagKey}`) }}</span>
            </div>
            <p class="mt-2 text-xs text-slate-400">{{ $t(`mtx.${line.key}_scene`) }}</p>
            <dl class="mt-3 space-y-2 text-xs flex-1">
              <div>
                <dt class="text-red-300/80 font-semibold">{{ $t('mtx.risk') }}</dt>
                <dd class="text-slate-300">{{ $t(`mtx.${line.key}_risk`) }}</dd>
              </div>
              <div>
                <dt class="text-primary-300 font-semibold">{{ $t('mtx.outcome') }}</dt>
                <dd class="text-slate-300">{{ $t(`mtx.${line.key}_outcome`) }}</dd>
              </div>
              <div>
                <dt class="text-emerald-300 font-semibold">{{ $t('mtx.recurring') }}</dt>
                <dd class="text-slate-300">{{ $t(`mtx.${line.key}_recurring`) }}</dd>
              </div>
            </dl>
            <NuxtLink :to="line.cta" class="mt-4 text-sm text-primary-400 font-medium hover:text-primary-300">
              {{ $t(`mtx.${line.ctaKey}`) }} &rarr;
            </NuxtLink>
          </div>
        </div>

        <!-- Public copy guardrail (FI.0.6) -->
        <div class="mt-10 glass-panel border-amber-500/30 bg-amber-400/5 p-5 text-center">
          <p class="text-sm text-amber-200/90 max-w-3xl mx-auto">{{ $t('mtx.guardrail') }}</p>
        </div>
      </div>
    </section>

    <!-- Explore solution detail pages -->
    <section class="section-padding">
      <div class="container-main">
        <div class="text-center mb-12">
          <h2 class="text-2xl sm:text-3xl font-bold text-white">{{ $t('mtx.explore') }}</h2>
          <p class="mt-3 text-slate-300 max-w-2xl mx-auto">{{ $t('mtx.exploreDesc') }}</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <NuxtLink
            v-for="solution in solutions"
            :key="solution.slug"
            :to="`/solutions/${solution.slug}`"
            class="group glass-panel p-6 hover:border-primary-400 hover:shadow-lg hover:shadow-primary-500/20 transition-all duration-300"
          >
            <div class="w-12 h-12 bg-primary-900/50 rounded-lg flex items-center justify-center mb-4 border border-primary-500/30">
              <span class="text-primary-400 text-xl">&#9889;</span>
            </div>
            <h3 class="text-lg font-semibold text-white group-hover:text-primary-400 transition-colors">{{ solution.title }}</h3>
            <p class="mt-2 text-sm text-slate-300 line-clamp-3">{{ solution.description }}</p>
            <span class="mt-3 inline-block text-sm text-primary-400 font-medium">{{ $t('solutions.learnMore') }} &rarr;</span>
          </NuxtLink>
        </div>
      </div>
    </section>

    <section class="section-padding">
      <div class="container-main">
        <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-10">
          <div>
            <p class="text-sm font-semibold uppercase tracking-wider text-primary-400">{{ $t('home.intelligenceKicker') }}</p>
            <h2 class="mt-2 text-2xl sm:text-3xl font-bold text-white">{{ $t('home.intelligenceTitle') }}</h2>
          </div>
          <NuxtLink to="/ai-building-brain" class="text-sm font-semibold text-primary-400 hover:text-primary-300">
            {{ $t('home.intelligenceExplore') }} &rarr;
          </NuxtLink>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <div v-for="level in intelligenceLevels" :key="level.level" class="glass-panel p-6">
            <div class="flex items-center justify-between gap-3">
              <span class="text-sm font-bold text-primary-400">{{ level.level }}</span>
              <span class="text-xs font-semibold px-2 py-1 bg-white/10 rounded text-slate-200">{{ level.status }}</span>
            </div>
            <h3 class="mt-3 font-bold text-white text-lg">{{ level.name }}</h3>
            <p class="mt-2 text-sm text-slate-300">{{ level.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Service Packages Section -->
    <section class="section-padding">
      <div class="container-main">
        <div class="text-center mb-12">
          <h2 class="text-2xl sm:text-3xl font-bold text-white">{{ $t('home.servicesTitle') }}</h2>
          <p class="mt-3 text-slate-300 max-w-2xl mx-auto">{{ $t('home.servicesSubtitle') }}</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
          <div
            v-for="pkg in servicePackages"
            :key="pkg.slug"
            class="glass-panel p-5 hover:border-primary-400 transition"
          >
            <h3 class="font-semibold text-white">{{ pkg.name }}</h3>
            <p class="text-sm text-primary-300 mt-1">{{ pkg.years }} {{ $t('services.years') }}</p>
            <p class="text-xs text-slate-300 mt-2 line-clamp-3">{{ pkg.description }}</p>
            <NuxtLink to="/services" class="mt-3 inline-block text-xs text-primary-400 font-medium">{{ $t('common.viewDetails') }}</NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Why AinerWise Section -->
    <section class="section-padding">
      <div class="container-main">
        <div class="text-center mb-12">
          <h2 class="text-2xl sm:text-3xl font-bold text-white">{{ $t('home.whyTitle') }}</h2>
          <p class="mt-3 text-slate-300">{{ $t('home.whySubtitle') }}</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          <div v-for="reason in whyReasons" :key="reason.title" class="text-center glass-panel p-6">
            <div class="w-14 h-14 bg-primary-900/50 border border-primary-500/30 rounded-full flex items-center justify-center mx-auto mb-4 shadow-[0_0_15px_rgba(14,165,233,0.3)]">
              <span class="text-2xl">{{ reason.emoji }}</span>
            </div>
            <h3 class="font-semibold text-white">{{ reason.title }}</h3>
            <p class="mt-2 text-sm text-slate-300">{{ reason.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="section-padding">
      <div class="container-main">
        <div class="glass-panel border-primary-500/50 bg-primary-900/20 text-center p-12">
          <h2 class="text-2xl sm:text-3xl font-bold text-white">{{ $t('home.ctaTitle') }}</h2>
          <p class="mt-3 text-primary-200 max-w-2xl mx-auto">{{ $t('home.ctaSubtitle') }}</p>
          <div class="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <NuxtLink to="/submit-requirement" class="bg-primary-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-400 transition shadow-[0_0_20px_rgba(14,165,233,0.4)]">
              {{ $t('nav.submitRequirement') }}
            </NuxtLink>
            <NuxtLink to="/supplier-application" class="glass-panel text-white px-8 py-3 font-semibold hover:bg-white/10 transition">
              {{ $t('nav.supplierApplication') }}
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { apiFetch } = useApi()
const { demoServicePackages, demoSolutions } = useDemoCatalog()

const solutions = ref<any[]>(demoSolutions.slice(0, 6))
const servicePackages = ref<any[]>(demoServicePackages)

const heroSignals = [
  'Buildings + Energy',
  'Cold Chain + Storage',
  'Kitchen + Water Safety',
  'Assets + Industrial',
  'Compliance + AMC',
]

const TAG_FLAGSHIP = 'bg-cyan-500/15 text-cyan-300'
const TAG_NOW = 'bg-emerald-500/15 text-emerald-300'
const TAG_ROADMAP = 'bg-white/10 text-slate-300'
const TAG_PARTNER = 'bg-amber-500/15 text-amber-300'

// FI.0.5 — solution matrix. Display text (scene/risk/outcome/recurring/tag/cta)
// is resolved from i18n (mtx.*) so it translates; only structure lives here.
const solutionMatrix = [
  { key: 'buildingbrain', name: 'BuildingBrain', tagKey: 'tag_flagship', tagClass: TAG_FLAGSHIP, cta: '/ai-building-brain', ctaKey: 'cta_brain' },
  { key: 'storageguard', name: 'StorageGuard', tagKey: 'tag_now', tagClass: TAG_NOW, cta: '/solutions/storageguard', ctaKey: 'cta_storage' },
  { key: 'kitchenguard', name: 'KitchenGuard', tagKey: 'tag_roadmap', tagClass: TAG_ROADMAP, cta: '/submit-requirement', ctaKey: 'cta_assess' },
  { key: 'aquaguard', name: 'AquaGuard', tagKey: 'tag_partner', tagClass: TAG_PARTNER, cta: '/submit-requirement', ctaKey: 'cta_assess' },
  { key: 'energyguard', name: 'EnergyGuard', tagKey: 'tag_roadmap', tagClass: TAG_ROADMAP, cta: '/submit-requirement', ctaKey: 'cta_assess' },
  { key: 'factorypulse', name: 'FactoryPulse', tagKey: 'tag_roadmap', tagClass: TAG_ROADMAP, cta: '/submit-requirement', ctaKey: 'cta_assess' },
  { key: 'assetpulse', name: 'AssetPulse', tagKey: 'tag_roadmap', tagClass: TAG_ROADMAP, cta: '/submit-requirement', ctaKey: 'cta_assess' },
  { key: 'agribrain', name: 'AgriBrain', tagKey: 'tag_future', tagClass: TAG_ROADMAP, cta: '/submit-requirement', ctaKey: 'cta_assess' },
]

const operatingModel = computed(() => [
  {
    kicker: t('home.opAssess'),
    title: t('home.opAssessTitle'),
    text: t('home.opAssessText'),
  },
  {
    kicker: t('home.opMatch'),
    title: t('home.opMatchTitle'),
    text: t('home.opMatchText'),
  },
  {
    kicker: t('home.opDeliver'),
    title: t('home.opDeliverTitle'),
    text: t('home.opDeliverText'),
  },
])

const intelligenceLevels = computed(() => [
  { level: 'L1', name: t('intelligence.l1'), status: t('intelligence.l1Status'), text: t('intelligence.l1Text') },
  { level: 'L2', name: t('intelligence.l2'), status: t('intelligence.l2Status'), text: t('intelligence.l2Text') },
  { level: 'L3', name: t('intelligence.l3'), status: t('intelligence.l3Status'), text: t('intelligence.l3Text') },
  { level: 'L4', name: t('intelligence.l4'), status: t('intelligence.l4Status'), text: t('intelligence.l4Text') },
  { level: 'L5', name: t('intelligence.l5'), status: t('intelligence.l5Status'), text: t('intelligence.l5Text') },
  { level: 'L6', name: t('intelligence.l6'), status: t('intelligence.l6Status'), text: t('intelligence.l6Text') },
])

const whyReasons = computed(() => [
  { emoji: '&#129302;', title: t('home.whyAI'), desc: t('home.whyAIDesc') },
  { emoji: '&#128230;', title: t('home.whySupply'), desc: t('home.whySupplyDesc') },
  { emoji: '&#128736;', title: t('home.whyLocal'), desc: t('home.whyLocalDesc') },
  { emoji: '&#128337;', title: t('home.whyLifecycle'), desc: t('home.whyLifecycleDesc') },
])

onMounted(async () => {
  try {
    const [solRes, pkgRes] = await Promise.all([
      apiFetch<any>('/solutions'),
      apiFetch<any>('/service-packages'),
    ])
    solutions.value = solRes.items || solRes || []
    servicePackages.value = pkgRes.items || pkgRes || []
  } catch {
    // API might not be ready yet during initial development
  }

  if (!solutions.value.length) {
    solutions.value = demoSolutions.slice(0, 6)
  }
  if (!servicePackages.value.length) {
    servicePackages.value = demoServicePackages
  }
})
</script>
