<template>
  <div>
    <KnxPageHero
      :eyebrow="$t('brain.eyebrow')"
      :title="$t('brain.overviewTitle')"
      :subtitle="$t('brain.overviewSubtitle')"
      :crumbs="[{ label: $t('nav.home'), to: '/' }, { label: $t('nav.aiBrain') }]"
      :badges="[
        { label: $t('solutions.badgeKnx') },
        { label: $t('brain.badgeBeyondBus'), ai: true },
      ]"
    >
      <template #actions>
        <NuxtLink to="/submit-requirement" class="btn-primary">{{ $t('brain.startAssessment') }}</NuxtLink>
        <NuxtLink to="/ai-building-brain-demo" class="btn-secondary">{{ $t('brain.open3d') }}</NuxtLink>
      </template>
    </KnxPageHero>

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
const active = computed(() => scenarios.find((s) => s.key === activeKey.value) || scenarios[0])

const busItems = computed(() => [
  t('brain.bus1'), t('brain.bus2'), t('brain.bus3'), t('brain.bus4'),
])
const brainItems = computed(() => [
  t('brain.ai1'), t('brain.ai2'), t('brain.ai3'), t('brain.ai4'),
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
</style>
