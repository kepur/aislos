<template>
  <div>
    <KnxPageHero
      :eyebrow="$t('brain.eyebrow')"
      :title="$t('brain.levelsTitle')"
      :subtitle="$t('brain.levelsSubtitle')"
      :crumbs="[
        { label: $t('nav.home'), to: '/' },
        { label: $t('nav.aiBrain'), to: '/ai-building-brain' },
        { label: $t('brain.levelsNav') },
      ]"
    >
      <template #actions>
        <NuxtLink :to="localized('/submit-requirement')" class="btn-primary">{{ $t('brain.startAssessment') }}</NuxtLink>
        <NuxtLink :to="localized('/ai-building-brain/process')" class="btn-secondary">{{ $t('brain.processNav') }}</NuxtLink>
      </template>
    </KnxPageHero>

    <KnxBrainNav />

    <!-- L1 to L6, with an explicit line for where a bus stops -->
    <KnxSectionBlock
      :eyebrow="$t('brain.ladderEyebrow')"
      :title="$t('brain.ladderTitle')"
      :subtitle="$t('brain.ladderSubtitle')"
    >
      <div class="space-y-3">
        <div
          v-for="lvl in levels"
          :key="lvl.level"
          class="glass-panel flex flex-col gap-4 p-6 sm:flex-row sm:items-start"
        >
          <div class="flex-shrink-0">
            <span
              class="flex h-12 w-12 items-center justify-center rounded-xl text-base font-black"
              :style="lvl.knx
                ? { backgroundColor: 'var(--brand-soft, rgba(14,165,233,.12))', color: 'var(--brand-strong, #38bdf8)' }
                : { backgroundColor: '#eef0ff', color: '#4338ca' }"
            >{{ lvl.level }}</span>
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="text-lg font-bold text-white">{{ lvl.name }}</h3>
              <span v-if="lvl.knx" class="knx-pill !text-[10px]">{{ $t('brain.reachableWithBus') }}</span>
              <span v-else class="knx-pill-ai !text-[10px]">✦ {{ $t('brain.needsBrain') }}</span>
            </div>
            <p class="mt-2 text-sm leading-relaxed text-slate-300">{{ lvl.text }}</p>
          </div>
        </div>
      </div>

      <p class="mt-8 rounded-xl border p-5 text-sm leading-relaxed text-slate-300"
         :style="{ borderColor: 'var(--hairline, rgba(255,255,255,.1))', backgroundColor: 'var(--surface-alt, transparent)' }">
        {{ $t('brain.ladderNote') }}
      </p>
    </KnxSectionBlock>

    <!-- Proposal tiers, mapped onto the ladder -->
    <KnxSectionBlock
      :eyebrow="$t('brain.tiersEyebrow')"
      :title="$t('brain.tiersTitle')"
      :subtitle="$t('brain.tiersSubtitle')"
      tinted
    >
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="tier in proposalTiers" :key="tier.name" class="glass-panel flex flex-col p-6">
          <span class="knx-pill !text-[10px]">{{ tier.level }}</span>
          <h3 class="mt-3 text-lg font-bold text-white">{{ tier.name }}</h3>
          <p class="mt-2 flex-1 text-sm leading-relaxed text-slate-300">{{ tier.text }}</p>
          <div class="mt-4 border-t pt-4" :style="{ borderColor: 'var(--hairline, rgba(255,255,255,.1))' }">
            <p class="text-sm font-semibold text-white">{{ tier.estimate }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ tier.note }}</p>
          </div>
        </div>
      </div>
    </KnxSectionBlock>

    <!-- Feature boundaries: what "available" actually means -->
    <KnxSectionBlock
      :eyebrow="$t('brain.boundaryEyebrow')"
      :title="$t('brain.boundaryTitle')"
      :subtitle="$t('brain.boundarySubtitle')"
    >
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div v-for="tag in featureTags" :key="tag.name" class="glass-panel p-5">
          <h3 class="font-semibold text-white">{{ tag.name }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-300">{{ tag.text }}</p>
        </div>
      </div>
    </KnxSectionBlock>

    <KnxCtaBand
      :title="$t('brain.ctaTitle')"
      :subtitle="$t('brain.ctaSubtitle')"
      primary-to="/submit-requirement"
      :primary-label="$t('brain.startAssessment')"
      secondary-to="/ai-building-brain/process"
      :secondary-label="$t('brain.processNav')"
    />
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const { levels, proposalTiers, featureTags } = useBuildingBrain()

useHead({ title: () => `${t('brain.levelsTitle')} — AinerWise` })
</script>
