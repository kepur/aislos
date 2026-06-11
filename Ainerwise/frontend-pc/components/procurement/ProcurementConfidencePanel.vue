<template>
  <section class="pc-card mb-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 class="text-sm font-bold text-white">{{ $t('procurement.confidence.title') }}</h2>
        <p class="mt-1 text-sm text-slate-400">{{ phaseMessage }}</p>
      </div>
      <div class="text-right">
        <p class="text-2xl font-bold" :class="scoreClass">{{ displayScore }}</p>
        <p class="text-xs text-slate-500">{{ $t('procurement.confidence.overall') }}</p>
      </div>
    </div>

    <div class="mt-4 grid gap-3 sm:grid-cols-3">
      <div class="rounded-lg bg-white/5 p-3">
        <p class="text-xs text-slate-500">{{ $t('procurement.confidence.facts') }}</p>
        <p class="mt-1 font-semibold text-white">{{ factsScore }}</p>
      </div>
      <div class="rounded-lg bg-white/5 p-3">
        <p class="text-xs text-slate-500">{{ $t('procurement.confidence.boq') }}</p>
        <p class="mt-1 font-semibold text-white">{{ boqScore }}</p>
      </div>
      <div class="rounded-lg bg-white/5 p-3">
        <p class="text-xs text-slate-500">{{ $t('procurement.confidence.allowed') }}</p>
        <p class="mt-1 text-sm font-medium text-white">{{ allowedActions }}</p>
      </div>
    </div>

    <div v-if="missingFacts.length" class="mt-4 rounded-lg border border-amber-400/30 bg-amber-400/10 p-4">
      <p class="text-sm font-semibold text-amber-200">{{ $t('procurement.confidence.missingFacts') }}</p>
      <ul class="mt-2 space-y-1 text-sm text-amber-100/90">
        <li v-for="fact in missingFacts" :key="fact.id">
          {{ fact.label }}
          <span v-if="fact.assumption" class="text-amber-200/70"> — {{ fact.assumption }}</span>
        </li>
      </ul>
    </div>

    <p v-if="phase === 'estimate' && disclaimer" class="mt-4 text-sm text-slate-400">
      {{ disclaimer }}
    </p>
  </section>
</template>

<script setup lang="ts">
import type { ProcurementFact } from '~/composables/useProcurement'
import { confidencePhase, parseConfidence } from '~/composables/useProcurement'

const props = defineProps<{
  overall: string | number
  factsScore: string | number
  boqScore: string | number
  facts: ProcurementFact[]
  gate?: Record<string, string | number>
  disclaimer?: string | null
  projectStatus?: string
}>()

const { t } = useI18n()

const overallNum = computed(() => parseConfidence(props.overall))
const phase = computed(() => confidencePhase(overallNum.value, props.gate))

const displayScore = computed(() => overallNum.value.toFixed(3))

const missingFacts = computed(() =>
  props.facts.filter(f => f.required && !f.user_confirmed),
)

const phaseMessage = computed(() => {
  if (phase.value === 'ask') return t('procurement.confidence.phaseAsk')
  if (phase.value === 'estimate') return t('procurement.confidence.phaseEstimate')
  if (props.projectStatus === 'in_review') return t('procurement.confidence.phaseInReview')
  if (props.projectStatus === 'review_approved') return t('procurement.confidence.phaseReviewReady')
  return t('procurement.confidence.phaseReview')
})

const allowedActions = computed(() => {
  if (props.projectStatus === 'boq_frozen' || props.projectStatus === 'packaged') {
    return t('procurement.actions.packages')
  }
  if (props.projectStatus === 'rfq_published') return t('procurement.actions.done')
  if (phase.value === 'ask') return t('procurement.actions.confirmFacts')
  if (phase.value === 'estimate') return t('procurement.actions.estimateOnly')
  if (props.projectStatus === 'in_review') return t('procurement.actions.waitReview')
  if (props.projectStatus === 'review_approved') return t('procurement.actions.freeze')
  return t('procurement.actions.submitReview')
})

const scoreClass = computed(() => {
  if (phase.value === 'ask') return 'text-amber-300'
  if (phase.value === 'estimate') return 'text-cyan-300'
  return 'text-emerald-300'
})
</script>
