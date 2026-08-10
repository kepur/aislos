<template>
  <div>
    <KnxPageHero
      :eyebrow="$t('brain.eyebrow')"
      :title="$t('brain.processTitle')"
      :subtitle="$t('brain.processSubtitle')"
      :crumbs="[
        { label: $t('nav.home'), to: '/' },
        { label: $t('nav.aiBrain'), to: '/ai-building-brain' },
        { label: $t('brain.processNav') },
      ]"
    >
      <template #actions>
        <NuxtLink :to="localized('/submit-requirement')" class="btn-primary">{{ $t('brain.startAssessment') }}</NuxtLink>
        <NuxtLink :to="localized('/solutions')" class="btn-secondary">{{ $t('nav.solutions') }}</NuxtLink>
      </template>
    </KnxPageHero>

    <KnxBrainNav />

    <!-- Assess -> Match -> Deliver, the existing operating model -->
    <KnxSectionBlock
      :eyebrow="$t('brain.stagesEyebrow')"
      :title="$t('brain.stagesTitle')"
      :subtitle="$t('brain.stagesSubtitle')"
    >
      <div class="grid gap-5 lg:grid-cols-3">
        <div v-for="(stage, i) in stages" :key="stage.kicker" class="glass-panel relative p-7">
          <span
            class="absolute right-6 top-6 text-4xl font-black opacity-10"
            :style="{ color: 'var(--brand-strong, #38bdf8)' }"
          >{{ i + 1 }}</span>
          <FeatureIcon :name="stage.icon" size="lg" :style="{ color: 'var(--brand-strong, #38bdf8)' }" />
          <p class="knx-eyebrow mt-4">{{ stage.kicker }}</p>
          <h3 class="mt-2 text-lg font-bold text-white">{{ stage.title }}</h3>
          <p class="mt-3 text-sm leading-relaxed text-slate-300">{{ stage.text }}</p>
        </div>
      </div>
    </KnxSectionBlock>

    <!-- Where a human must sign off. This is a promise, so it gets its own block. -->
    <KnxSectionBlock
      :eyebrow="$t('brain.gateEyebrow')"
      :title="$t('brain.gateTitle')"
      :subtitle="$t('brain.gateSubtitle')"
      tinted
    >
      <div class="grid gap-4 md:grid-cols-2">
        <div class="glass-panel p-6">
          <span class="knx-pill-ai">✦ {{ $t('brain.aiDoes') }}</span>
          <ul class="mt-4 space-y-2.5">
            <li v-for="item in aiDoes" :key="item" class="flex gap-2 text-sm text-slate-300">
              <span class="text-indigo-500">✦</span>{{ item }}
            </li>
          </ul>
        </div>
        <div class="glass-panel p-6">
          <span class="knx-pill">{{ $t('brain.humanDoes') }}</span>
          <ul class="mt-4 space-y-2.5">
            <li v-for="item in humanDoes" :key="item" class="flex gap-2 text-sm text-slate-300">
              <span :style="{ color: 'var(--brand-strong, #38bdf8)' }">✓</span>{{ item }}
            </li>
          </ul>
        </div>
      </div>
      <p class="mt-6 rounded-xl border border-amber-500/30 bg-amber-400/10 p-5 text-sm leading-relaxed text-amber-700">
        {{ $t('brain.gateNote') }}
      </p>
    </KnxSectionBlock>

    <!-- Lifecycle: the part that keeps paying after handover -->
    <KnxSectionBlock
      :eyebrow="$t('brain.lifecycleEyebrow')"
      :title="$t('brain.lifecycleTitle')"
      :subtitle="$t('brain.lifecycleSubtitle')"
    >
      <KnxIconGrid :items="lifecycleItems" :columns="4" />
    </KnxSectionBlock>

    <KnxCtaBand
      :title="$t('brain.ctaTitle')"
      :subtitle="$t('brain.ctaSubtitle')"
      primary-to="/submit-requirement"
      :primary-label="$t('brain.startAssessment')"
      secondary-to="/ai-building-brain"
      :secondary-label="$t('brain.overviewNav')"
    />
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()

// Reuses the home page's operating-model copy so the story stays identical
// wherever a visitor first meets it.
const stages = computed(() => [
  { kicker: t('home.opAssess'), title: t('home.opAssessTitle'), text: t('home.opAssessText'), icon: 'ai-brain' },
  { kicker: t('home.opMatch'), title: t('home.opMatchTitle'), text: t('home.opMatchText'), icon: 'network' },
  { kicker: t('home.opDeliver'), title: t('home.opDeliverTitle'), text: t('home.opDeliverText'), icon: 'installer' },
])

const aiDoes = computed(() => [
  t('brain.aiDoes1'), t('brain.aiDoes2'), t('brain.aiDoes3'), t('brain.aiDoes4'),
])
const humanDoes = computed(() => [
  t('brain.humanDoes1'), t('brain.humanDoes2'), t('brain.humanDoes3'), t('brain.humanDoes4'),
])

const lifecycleItems = computed(() => [
  { icon: 'sensor', label: t('brain.lc1'), hint: t('brain.lc1Hint') },
  { icon: 'lifecycle', label: t('brain.lc2'), hint: t('brain.lc2Hint') },
  { icon: 'installer', label: t('brain.lc3'), hint: t('brain.lc3Hint') },
  { icon: 'ai-brain', label: t('brain.lc4'), hint: t('brain.lc4Hint'), ai: true },
])

useHead({ title: () => `${t('brain.processTitle')} — AinerWise` })
</script>
