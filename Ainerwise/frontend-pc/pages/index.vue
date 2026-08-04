<template>
  <div>
    <AinerwiseImmersiveHero
      background-image="/images/brand/ainerwise-grand-building.svg"
      :eyebrow="$t('home.heroKicker')"
      :title="$t('home.heroTitle')"
      :subtitle="$t('home.heroSubtitle')"
      :badges="stageBadges"
      :stats="stageSignals"
      :nodes="heroSignals"
      primary-to="/submit-requirement"
      :primary-label="$t('home.heroCta1')"
      secondary-to="/ai-building-brain"
      :secondary-label="$t('home.heroCta2')"
      :core-label="$t('home.hubCore')"
    >
      <template #aside>
        <div class="aw-home-command">
          <div class="aw-home-command__header">
            <p>{{ $t('home.stageTitle') }}</p>
            <span>{{ $t('home.stageCredit') }}</span>
          </div>
          <BuildingBrainMap compact />
          <div class="aw-home-command__signals">
            <div v-for="signal in stageSignals" :key="signal.label">
              <strong>{{ signal.value }}</strong>
              <span>{{ signal.label }}</span>
            </div>
          </div>
        </div>
      </template>
    </AinerwiseImmersiveHero>

    <section class="aw-home-flow knx-on-dark">
      <div class="container-main px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
        <div class="grid gap-5 lg:grid-cols-4">
          <div class="aw-home-flow__intro">
            <p class="knx-eyebrow">{{ $t('home.layersEyebrow') }}</p>
            <h2>{{ $t('home.layersTitle') }}</h2>
            <p>{{ $t('home.layersSubtitle') }}</p>
            <a :href="marketUrl" class="aw-home-flow__link">{{ $t('procurement.title') }} →</a>
          </div>
          <div v-for="item in operatingModel" :key="item.kicker" class="aw-home-flow__card">
            <span>{{ item.kicker }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.text }}</p>
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
        <div v-if="contentLoading" class="glass-panel p-8 text-center text-sm text-slate-400">Loading published solutions...</div>
        <div v-else-if="solutionsError" class="glass-panel border-red-500/30 p-6 text-center text-sm text-red-300">
          <p>{{ solutionsError }}</p>
          <button class="btn-primary mt-4" @click="loadPublicContent">Retry</button>
        </div>
        <div v-else-if="!solutions.length" class="glass-panel p-8 text-center text-sm text-slate-400">
          No solutions are currently published.
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
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
        <div v-if="contentLoading" class="glass-panel p-8 text-center text-sm text-slate-400">Loading service plans...</div>
        <div v-else-if="servicesError" class="glass-panel border-red-500/30 p-6 text-center text-sm text-red-300">
          <p>{{ servicesError }}</p>
          <button class="btn-primary mt-4" @click="loadPublicContent">Retry</button>
        </div>
        <div v-else-if="!servicePackages.length" class="glass-panel p-8 text-center text-sm text-slate-400">
          No service plans are currently published.
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
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

    <KnxEcosystemHub
      :eyebrow="$t('home.hubEyebrow')"
      :title="$t('home.hubTitle')"
      :subtitle="$t('home.hubSubtitle')"
      :core-label="$t('home.hubCore')"
      :suppliers="hubSuppliers"
      :systems="hubSystems"
      cta-to="/ai-building-brain"
      :cta-label="$t('home.intelligenceExplore')"
      footnote-to="/solutions"
      :footnote-label="$t('home.hubFootnote')"
    />

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
              <FeatureIcon :name="reason.icon" class="text-primary-300" />
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
const publicConfig = useRuntimeConfig().public

// Left of the hub: the supply chain we actually source from. Right: the
// building systems we integrate. Both are ours — no third-party marks.
const hubSuppliers = computed<string[]>(() => [
  t('home.hubSupplier1'),
  t('home.hubSupplier2'),
  t('home.hubSupplier3'),
  t('home.hubSupplier4'),
  t('home.hubSupplier5'),
  t('home.hubSupplier6'),
  t('home.hubSupplier7'),
])

const hubSystems = computed(() => [
  { icon: 'lighting', label: t('home.sysLighting') },
  { icon: 'hvac', label: t('home.sysHvac') },
  { icon: 'shading', label: t('home.sysShading') },
  { icon: 'energy', label: t('home.sysEnergy') },
  { icon: 'security', label: t('home.sysSecurity') },
  { icon: 'automation', label: t('home.sysScenes') },
  { icon: 'network', label: t('home.sysNetwork') },
])
const marketUrl = publicConfig.marketUrl as string

const solutions = ref<any[]>([])
const servicePackages = ref<any[]>([])
const contentLoading = ref(true)
const solutionsError = ref('')
const servicesError = ref('')

const heroSignals = [
  'AI Need Analysis',
  'Smart Hardware',
  'Procurement OS',
  'Partner Delivery',
  'AMC + Support',
]

const stageBadges = computed(() => [
  { label: t('home.stageBadge1') },
  { label: t('home.stageBadge2'), ai: true },
  { label: t('home.stageBadge3') },
])

const stageSignals = computed(() => [
  { value: t('home.stageSignal1Value'), label: t('home.stageSignal1Label') },
  { value: t('home.stageSignal2Value'), label: t('home.stageSignal2Label') },
  { value: t('home.stageSignal3Value'), label: t('home.stageSignal3Label') },
])

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
  { icon: 'ai-brain', title: t('home.whyAI'), desc: t('home.whyAIDesc') },
  { icon: 'supply-chain', title: t('home.whySupply'), desc: t('home.whySupplyDesc') },
  { icon: 'installer', title: t('home.whyLocal'), desc: t('home.whyLocalDesc') },
  { icon: 'lifecycle', title: t('home.whyLifecycle'), desc: t('home.whyLifecycleDesc') },
])

async function loadPublicContent() {
  contentLoading.value = true
  solutionsError.value = ''
  servicesError.value = ''
  const [solutionsResult, servicesResult] = await Promise.allSettled([
    apiFetch<any>('/solutions'),
    apiFetch<any>('/service-packages'),
  ])
  if (solutionsResult.status === 'fulfilled') {
    solutions.value = (solutionsResult.value.items || solutionsResult.value || []).slice(0, 6)
  } else {
    solutions.value = []
    const error: any = solutionsResult.reason
    solutionsError.value = error?.data?.detail || error?.message || 'Unable to load solutions.'
  }
  if (servicesResult.status === 'fulfilled') {
    servicePackages.value = servicesResult.value.items || servicesResult.value || []
  } else {
    servicePackages.value = []
    const error: any = servicesResult.reason
    servicesError.value = error?.data?.detail || error?.message || 'Unable to load service plans.'
  }
  contentLoading.value = false
}

onMounted(loadPublicContent)
</script>

<style scoped>
.aw-home-command {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(236, 253, 245, .14);
  border-radius: 30px;
  background:
    radial-gradient(circle at 70% 12%, rgba(45, 212, 191, .18), transparent 34%),
    linear-gradient(145deg, rgba(2, 6, 23, .78), rgba(6, 78, 59, .34));
  padding: 1rem;
  box-shadow: 0 28px 80px rgba(2, 6, 23, .42), inset 0 1px 0 rgba(255, 255, 255, .08);
  backdrop-filter: blur(20px);
}
.aw-home-command__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: .45rem .6rem 1rem;
}
.aw-home-command__header p {
  color: #ecfdf5;
  font-size: .84rem;
  font-weight: 900;
}
.aw-home-command__header span {
  color: rgba(209, 250, 229, .66);
  font-size: .72rem;
  font-weight: 700;
}
.aw-home-command__signals {
  margin-top: 1rem;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .7rem;
}
.aw-home-command__signals div {
  border: 1px solid rgba(236, 253, 245, .12);
  border-radius: 18px;
  background: rgba(255, 255, 255, .06);
  padding: .8rem;
}
.aw-home-command__signals strong {
  display: block;
  color: #ecfdf5;
  font-size: 1.3rem;
  line-height: 1;
}
.aw-home-command__signals span {
  margin-top: .35rem;
  display: block;
  color: rgba(209, 250, 229, .72);
  font-size: .72rem;
  font-weight: 800;
}
.aw-home-flow {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 16% 20%, rgba(16, 185, 129, .2), transparent 30%),
    radial-gradient(circle at 76% 10%, rgba(34, 211, 238, .12), transparent 28%),
    linear-gradient(135deg, #020617, #06231d 56%, #020617);
}
.aw-home-flow::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(209, 250, 229, .06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(209, 250, 229, .06) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(to bottom, black, transparent);
  pointer-events: none;
}
.aw-home-flow__intro,
.aw-home-flow__card {
  position: relative;
  min-height: 260px;
  border: 1px solid rgba(236, 253, 245, .12);
  border-radius: 24px;
  background: linear-gradient(145deg, rgba(15, 23, 42, .58), rgba(6, 78, 59, .24));
  padding: 1.4rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .06);
  backdrop-filter: blur(16px);
}
.aw-home-flow__intro {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.aw-home-flow__intro h2 {
  margin-top: .8rem;
  color: #fff;
  font-size: clamp(1.8rem, 4vw, 3.2rem);
  font-weight: 900;
  line-height: 1.04;
}
.aw-home-flow__intro p:not(.knx-eyebrow) {
  margin-top: 1rem;
  color: rgba(209, 250, 229, .78);
  font-size: .95rem;
  line-height: 1.7;
}
.aw-home-flow__link {
  margin-top: 1.2rem;
  color: #86efac;
  font-weight: 900;
}
.aw-home-flow__card span {
  color: #86efac;
  font-size: .72rem;
  font-weight: 900;
  letter-spacing: .18em;
  text-transform: uppercase;
}
.aw-home-flow__card h3 {
  margin-top: 1.3rem;
  color: #fff;
  font-size: 1.35rem;
  font-weight: 900;
  line-height: 1.15;
}
.aw-home-flow__card p {
  margin-top: .9rem;
  color: rgba(226, 245, 237, .78);
  font-size: .92rem;
  line-height: 1.7;
}
</style>
