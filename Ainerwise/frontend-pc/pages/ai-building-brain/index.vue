<template>
  <div>
    <AinerwiseImmersiveHero
      background-image="/images/brand/ainerwise-ai-brain-bg.svg"
      :eyebrow="$t('brain.eyebrow')"
      :title="$t('brain.overviewTitle')"
      :subtitle="$t('brain.overviewSubtitle')"
      :crumbs="[{ label: $t('nav.home'), to: '/' }, { label: $t('nav.aiBrain') }]"
      :badges="brainHeroBadges"
      :stats="brainHeroStats"
      :nodes="brainHeroNodes"
      primary-to="/submit-requirement"
      :primary-label="$t('brain.startAssessment')"
      :core-label="$t('home.hubCore')"
      :show-orbit="false"
    >
      <template #aside>
        <BuildingBrainHeroVisual />
      </template>
    </AinerwiseImmersiveHero>

    <KnxBrainNav />

    <!-- The honest framing: the bus does control, the brain does the rest -->
    <KnxSectionBlock
      :eyebrow="$t('brain.differenceEyebrow')"
      :title="$t('brain.differenceTitle')"
      :subtitle="$t('brain.differenceSubtitle')"
      centered
    >
      <div class="grid gap-5 md:grid-cols-2">
        <div class="glass-panel p-7">
          <span class="knx-pill">{{ $t('brain.busLabel') }}</span>
          <h3 class="mt-4 text-lg font-bold text-white">{{ $t('brain.busTitle') }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-300">{{ $t('brain.busText') }}</p>
          <ul class="mt-4 space-y-2 text-sm text-slate-300">
            <li v-for="item in busItems" :key="item" class="flex gap-2">
              <span :style="{ color: 'var(--brand-strong, #38bdf8)' }">▸</span>{{ item }}
            </li>
          </ul>
        </div>
        <div class="glass-panel p-7">
          <span class="knx-pill-ai">✦ {{ $t('brain.brainLabel') }}</span>
          <h3 class="mt-4 text-lg font-bold text-white">{{ $t('brain.brainTitle') }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-300">{{ $t('brain.brainText') }}</p>
          <ul class="mt-4 space-y-2 text-sm text-slate-300">
            <li v-for="item in brainItems" :key="item" class="flex gap-2">
              <span class="text-indigo-500">✦</span>{{ item }}
            </li>
          </ul>
        </div>
      </div>
    </KnxSectionBlock>

    <!-- Four capability layers -->
    <KnxSectionBlock
      :eyebrow="$t('brain.capabilityEyebrow')"
      :title="$t('brain.capabilityTitle')"
      :subtitle="$t('brain.capabilitySubtitle')"
      centered
      tinted
    >
      <KnxIconGrid
        :items="capabilityBlocks.map(b => ({ key: b.key, icon: b.icon, label: b.kicker, hint: b.title, ai: b.key === 'optimize' }))"
        :columns="4"
      />
    </KnxSectionBlock>

    <!-- Scenario picker: same content as the 3D demo, readable without WebGL -->
    <KnxSectionBlock
      :eyebrow="$t('brain.scenarioEyebrow')"
      :title="$t('brain.scenarioTitle')"
      :subtitle="$t('brain.scenarioSubtitle')"
    >
      <div class="mb-8 flex flex-wrap gap-2">
        <button
          v-for="s in scenarios"
          :key="s.key"
          type="button"
          class="knx-chip"
          :class="activeKey === s.key ? 'knx-chip-active' : ''"
          @click="activeKey = s.key"
        >{{ s.name }}</button>
      </div>

      <div class="glass-panel p-7">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="knx-eyebrow">{{ active.type }}</p>
            <h3 class="mt-2 text-2xl font-bold text-white">{{ active.name }}</h3>
          </div>
          <div class="flex flex-wrap gap-2">
            <span class="knx-pill">{{ active.level }}</span>
            <span class="knx-pill">{{ active.boundary }}</span>
          </div>
        </div>
        <p class="mt-4 max-w-3xl leading-relaxed text-slate-300">{{ active.positioning }}</p>

        <div class="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          <div v-for="block in capabilityBlocks" :key="block.key">
            <div class="flex items-center gap-2">
              <FeatureIcon :name="block.icon" size="sm" :style="{ color: 'var(--brand-strong, #38bdf8)' }" />
              <p class="knx-eyebrow">{{ block.kicker }}</p>
            </div>
            <p class="mt-1 text-sm font-semibold text-white">{{ block.title }}</p>
            <ul class="mt-3 space-y-1.5">
              <li v-for="item in active[block.key]" :key="item" class="flex gap-2 text-sm text-slate-300">
                <span class="text-slate-400">·</span>{{ item }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </KnxSectionBlock>

    <section id="brain-visual-layer" class="immersive-demo knx-on-dark">
      <div class="container-main immersive-demo-shell px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <div class="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] lg:items-stretch">
          <div class="immersive-demo-scene">
            <ClientOnly>
              <BuildingBrain3D :level="selectedLevel" :scenario-key="activeKey" />
              <template #fallback>
                <div class="min-h-[460px] bg-slate-950"></div>
              </template>
            </ClientOnly>
          </div>

          <aside class="immersive-demo-panel">
            <p class="knx-eyebrow">{{ $t('brain.demoEyebrow') }}</p>
            <h2 class="mt-3 text-3xl font-bold text-white">{{ $t('brain.demoTitle') }}</h2>
            <p class="mt-4 leading-relaxed text-slate-300">{{ $t('brain.demoSubtitle') }}</p>

            <div class="mt-8">
              <p class="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">{{ $t('brain.demoLevel') }}</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <button
                  v-for="level in demoLevelOptions"
                  :key="level.key"
                  type="button"
                  class="demo-control"
                  :class="selectedLevel === level.key ? 'demo-control-active' : ''"
                  @click="selectedLevel = level.key"
                >
                  {{ level.key }} · {{ level.label }}
                </button>
              </div>
            </div>

            <div class="mt-8">
              <p class="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">{{ $t('brain.demoScenario') }}</p>
              <div class="mt-3 grid gap-2">
                <button
                  v-for="scenario in scenarios"
                  :key="scenario.key"
                  type="button"
                  class="demo-scenario"
                  :class="activeKey === scenario.key ? 'demo-scenario-active' : ''"
                  @click="activeKey = scenario.key"
                >
                  <span>{{ scenario.name }}</span>
                  <small>{{ scenario.level }}</small>
                </button>
              </div>
            </div>

            <div class="mt-8 pc-notice-warning">
              {{ $t('brain.demoNotice') }}
            </div>
          </aside>
        </div>
      </div>
    </section>

    <KnxCtaBand
      :title="$t('brain.ctaTitle')"
      :subtitle="$t('brain.ctaSubtitle')"
      primary-to="/submit-requirement"
      :primary-label="$t('brain.startAssessment')"
      secondary-to="/ai-building-brain/levels"
      :secondary-label="$t('brain.levelsNav')"
    />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { scenarios, capabilityBlocks } = useBuildingBrain()

const activeKey = ref(scenarios[0].key)
const selectedLevel = ref<'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6'>('L4')
const active = computed(() => scenarios.find((s) => s.key === activeKey.value) || scenarios[0])

const demoLevelOptions = computed(() => [
  { key: 'L1' as const, label: t('brain.demoLevelL1') },
  { key: 'L2' as const, label: t('brain.demoLevelL2') },
  { key: 'L3' as const, label: t('brain.demoLevelL3') },
  { key: 'L4' as const, label: t('brain.demoLevelL4') },
  { key: 'L5' as const, label: t('brain.demoLevelL5') },
  { key: 'L6' as const, label: t('brain.demoLevelL6') },
])

const busItems = computed(() => [
  t('brain.bus1'), t('brain.bus2'), t('brain.bus3'), t('brain.bus4'),
])
const brainItems = computed(() => [
  t('brain.ai1'), t('brain.ai2'), t('brain.ai3'), t('brain.ai4'),
])

const brainHeroBadges = computed(() => [
  { label: t('solutions.badgeKnx') },
  { label: t('brain.badgeBeyondBus'), ai: true },
  { label: t('brain.capabilityTitle') },
])
const brainHeroStats = computed(() => [
  { value: 'L1-L6', label: t('home.intelligenceKicker') },
  { value: '7', label: t('brain.scenarioTitle') },
  { value: '24/7', label: t('home.whyLifecycle') },
])
const brainHeroNodes = computed(() => [
  t('brain.ai1'),
  t('brain.ai2'),
  t('brain.ai3'),
  t('brain.ai4'),
])

useHead({ title: () => `${t('brain.overviewTitle')} — AinerWise` })
</script>

<style scoped>
.knx-chip {
  @apply rounded-full border px-4 py-2 text-sm font-medium transition;
  border-color: var(--hairline, rgba(255, 255, 255, .15));
  color: var(--ink-muted, #cbd5e1);
}
.knx-chip:hover { border-color: var(--brand, #0ea5e9); }
.knx-chip-active {
  background: var(--brand, #0ea5e9);
  border-color: var(--brand, #0ea5e9);
  color: #fff;
}

.immersive-demo {
  position: relative;
  scroll-margin-top: 92px;
  overflow: hidden;
  background:
    radial-gradient(circle at 72% 20%, rgba(20, 184, 166, 0.26), transparent 30%),
    radial-gradient(circle at 26% 68%, rgba(59, 130, 246, 0.22), transparent 32%),
    linear-gradient(135deg, #020617 0%, #071324 48%, #05231c 100%);
}
.immersive-demo::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(rgba(148, 163, 184, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.06) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: radial-gradient(circle at 50% 45%, black, transparent 78%);
}
.immersive-demo-shell {
  position: relative;
  z-index: 1;
}
.immersive-demo-scene {
  min-height: 520px;
  overflow: hidden;
  border: 1px solid rgba(125, 211, 252, 0.18);
  border-radius: 30px;
  background: #020617;
  box-shadow: 0 28px 90px rgba(2, 6, 23, 0.46);
}
.immersive-demo-scene :deep(.brain3d) {
  min-height: 520px;
  height: 520px;
}
.immersive-demo-panel {
  border: 1px solid rgba(125, 211, 252, 0.18);
  border-radius: 30px;
  background: rgba(2, 6, 23, 0.74);
  padding: 28px;
  color: #e2e8f0;
  backdrop-filter: blur(18px);
}
.demo-control,
.demo-scenario {
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
  transition: border-color .18s ease, background .18s ease, color .18s ease, transform .18s ease;
}
.demo-control {
  border-radius: 999px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 800;
}
.demo-control:hover,
.demo-scenario:hover {
  border-color: rgba(52, 211, 153, 0.58);
  background: rgba(16, 185, 129, 0.10);
}
.demo-control-active,
.demo-scenario-active {
  border-color: rgba(52, 211, 153, 0.9);
  background: rgba(16, 185, 129, 0.18);
  color: #d1fae5;
}
.demo-scenario {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  border-radius: 16px;
  padding: 12px 14px;
  text-align: left;
  font-size: 14px;
  font-weight: 700;
}
.demo-scenario small {
  color: rgba(190, 225, 212, 0.72);
  font-size: 12px;
  font-weight: 800;
}
@media (max-width: 1024px) {
  .immersive-demo-scene,
  .immersive-demo-scene :deep(.brain3d) {
    min-height: 460px;
    height: 460px;
  }
}
</style>
