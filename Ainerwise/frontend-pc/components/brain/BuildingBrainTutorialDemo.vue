<template>
  <div class="tutorial-demo" :style="accentStyle">
    <div class="tutorial-demo-bg" aria-hidden="true">
      <span v-for="dot in dots" :key="dot.id" :style="dot.style" />
    </div>

    <div class="tutorial-topbar">
      <div>
        <p class="tutorial-kicker">{{ $t('brain.tutorialKicker') }}</p>
        <h3>{{ $t('brain.tutorialTitle') }}</h3>
      </div>
      <div class="tutorial-live">
        <span />
        {{ $t('brain.tutorialLive') }}
      </div>
    </div>

    <div class="tutorial-grid">
      <aside class="tutorial-steps" aria-label="AinerWise AI Brain tutorial steps">
        <button
          v-for="(step, index) in tutorialSteps"
          :key="step.key"
          type="button"
          class="tutorial-step"
          :class="{ 'tutorial-step-active': index === activeStepIndex }"
          @click="activeStepIndex = index"
        >
          <small>{{ String(index + 1).padStart(2, '0') }}</small>
          <span>{{ step.title }}</span>
        </button>
      </aside>

      <section class="tutorial-main-card">
        <div class="tutorial-step-label">
          {{ $t('brain.tutorialStep') }} {{ activeStepIndex + 1 }} / {{ tutorialSteps.length }}
        </div>
        <h2>{{ activeStep.title }}</h2>
        <p>{{ activeStep.description }}</p>

        <div class="tutorial-conversation">
          <div class="bubble bubble-user">
            <span>{{ $t('brain.tutorialUserNeed') }}</span>
            <strong>{{ scenarioPrompt }}</strong>
          </div>
          <div class="bubble bubble-ai">
            <span>{{ $t('brain.tutorialAiReply') }}</span>
            <strong>{{ activeStep.aiReply }}</strong>
          </div>
        </div>

        <div class="tutorial-output-grid">
          <div v-for="item in activeStep.outputs" :key="item.label" class="tutorial-output">
            <small>{{ item.label }}</small>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>

      <aside class="tutorial-preview">
        <div class="preview-card preview-card-primary">
          <p>{{ $t('brain.tutorialCurrentScenario') }}</p>
          <h4>{{ scenario.name }}</h4>
          <span>{{ scenario.level }} · {{ selectedLevelName }}</span>
        </div>

        <div class="preview-card">
          <div class="preview-card-head">
            <p>{{ $t('brain.tutorialFactMap') }}</p>
            <strong>{{ factCompletion }}%</strong>
          </div>
          <div class="progress-shell">
            <i :style="{ width: `${factCompletion}%` }" />
          </div>
          <ul>
            <li v-for="item in factItems" :key="item">{{ item }}</li>
          </ul>
        </div>

        <div class="preview-card">
          <div class="preview-card-head">
            <p>{{ $t('brain.tutorialDeliverables') }}</p>
            <strong>{{ selectedLevel }}</strong>
          </div>
          <div class="deliverable-list">
            <span v-for="item in deliverables" :key="item">{{ item }}</span>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BrainScenario } from '~/composables/useBuildingBrain'

type BrainLevel = 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6'

const props = defineProps<{
  scenario: BrainScenario
  selectedLevel: BrainLevel
}>()

const { t } = useI18n()
const activeStepIndex = ref(0)

const levelIndex = computed(() => Number(props.selectedLevel.slice(1)) || 4)
const selectedLevelName = computed(() => t(`brain.demoLevel${props.selectedLevel}`))
const accentStyle = computed(() => ({
  '--tutorial-accent': accentColor.value,
  '--tutorial-accent-soft': `${accentColor.value}22`,
  '--tutorial-accent-mid': `${accentColor.value}44`,
}))

const accentColor = computed(() => {
  if (props.selectedLevel === 'L1' || props.selectedLevel === 'L2') return '#38bdf8'
  if (props.selectedLevel === 'L3') return '#22c55e'
  if (props.selectedLevel === 'L4') return '#34d399'
  if (props.selectedLevel === 'L5') return '#60a5fa'
  return '#a78bfa'
})

const scenarioPrompt = computed(() => {
  if (props.scenario.key === 'villa') return t('brain.tutorialPromptVilla')
  if (props.scenario.key === 'school') return t('brain.tutorialPromptSchool')
  if (props.scenario.key === 'apartment') return t('brain.tutorialPromptApartment')
  if (props.scenario.key === 'office') return t('brain.tutorialPromptOffice')
  if (props.scenario.key === 'factory') return t('brain.tutorialPromptFactory')
  if (props.scenario.key === 'hotel') return t('brain.tutorialPromptHotel')
  return t('brain.tutorialPromptEnergy')
})

const tutorialSteps = computed(() => [
  {
    key: 'need',
    title: t('brain.tutorialNeedTitle'),
    description: t('brain.tutorialNeedDesc'),
    aiReply: t('brain.tutorialNeedReply'),
    outputs: [
      { label: t('brain.tutorialOutputScope'), value: props.scenario.type },
      { label: t('brain.tutorialOutputLevel'), value: props.scenario.level },
      { label: t('brain.tutorialOutputRisk'), value: props.scenario.boundary },
    ],
  },
  {
    key: 'facts',
    title: t('brain.tutorialFactsTitle'),
    description: t('brain.tutorialFactsDesc'),
    aiReply: props.scenario.sense.slice(0, 2).join(' · '),
    outputs: [
      { label: t('brain.tutorialOutputKnown'), value: String(Math.min(8, 3 + levelIndex.value)) },
      { label: t('brain.tutorialOutputQuestions'), value: String(Math.max(1, 6 - levelIndex.value)) },
      { label: t('brain.tutorialOutputConfidence'), value: `${factCompletion.value}%` },
    ],
  },
  {
    key: 'system',
    title: t('brain.tutorialSystemTitle'),
    description: t('brain.tutorialSystemDesc'),
    aiReply: props.scenario.control.slice(0, 2).join(' · '),
    outputs: [
      { label: t('brain.tutorialOutputBus'), value: levelIndex.value <= 2 ? t('brain.reachableWithBus') : t('brain.needsBrain') },
      { label: t('brain.tutorialOutputSystems'), value: String(systemCount.value) },
      { label: t('brain.tutorialOutputRegion'), value: t('brain.tutorialRegionReady') },
    ],
  },
  {
    key: 'commercial',
    title: t('brain.tutorialCommercialTitle'),
    description: t('brain.tutorialCommercialDesc'),
    aiReply: t('brain.tutorialCommercialReply'),
    outputs: [
      { label: 'BOQ', value: t('brain.tutorialBoqReady') },
      { label: 'RFQ', value: t('brain.tutorialRfqReady') },
      { label: t('brain.tutorialSnapshot'), value: t('brain.tutorialSnapshotValue') },
    ],
  },
  {
    key: 'delivery',
    title: t('brain.tutorialDeliveryTitle'),
    description: t('brain.tutorialDeliveryDesc'),
    aiReply: props.scenario.maintain.slice(0, 2).join(' · '),
    outputs: [
      { label: t('brain.tutorialOutputTasks'), value: String(4 + levelIndex.value) },
      { label: t('brain.tutorialOutputEvidence'), value: t('brain.tutorialEvidenceValue') },
      { label: t('brain.tutorialOutputLifecycle'), value: 'AMC' },
    ],
  },
])

const activeStep = computed(() => tutorialSteps.value[activeStepIndex.value] || tutorialSteps.value[0])
const factCompletion = computed(() => Math.min(95, 52 + levelIndex.value * 7))
const systemCount = computed(() => Math.min(12, props.scenario.sense.length + props.scenario.control.length + Math.max(0, levelIndex.value - 2)))

const factItems = computed(() => [
  props.scenario.sense[0],
  props.scenario.control[0],
  props.scenario.optimize[0],
].filter(Boolean))

const deliverables = computed(() => [
  'AI Facts',
  'BOQ',
  'Budget',
  'RFQ',
  levelIndex.value >= 4 ? 'Human Review' : 'Installer Check',
  levelIndex.value >= 5 ? 'Local AI Box' : 'AMC Plan',
])

const dots = computed(() => Array.from({ length: 18 }, (_, index) => ({
  id: index,
  style: {
    left: `${6 + ((index * 19) % 88)}%`,
    top: `${8 + ((index * 31) % 78)}%`,
    animationDelay: `${(index % 6) * 0.45}s`,
    opacity: String(0.25 + (index % 4) * 0.12),
  },
})))

watch(() => props.selectedLevel, () => {
  activeStepIndex.value = Math.min(tutorialSteps.value.length - 1, Math.max(0, levelIndex.value - 2))
})

watch(() => props.scenario.key, () => {
  activeStepIndex.value = 0
})
</script>

<style scoped>
.tutorial-demo {
  position: relative;
  min-height: 560px;
  overflow: hidden;
  border-radius: 30px;
  border: 1px solid rgba(125, 211, 252, 0.18);
  background:
    radial-gradient(circle at 76% 18%, var(--tutorial-accent-soft), transparent 28%),
    radial-gradient(circle at 18% 82%, rgba(14, 165, 233, 0.18), transparent 34%),
    linear-gradient(145deg, rgba(2, 6, 23, 0.98), rgba(8, 22, 38, 0.96) 48%, rgba(4, 31, 27, 0.92));
  color: #e2e8f0;
  box-shadow: 0 28px 90px rgba(2, 6, 23, 0.46);
}

.tutorial-demo::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(rgba(148, 163, 184, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.06) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: radial-gradient(circle at 50% 44%, black, transparent 78%);
}

.tutorial-demo-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.tutorial-demo-bg::before,
.tutorial-demo-bg::after {
  content: "";
  position: absolute;
  width: 520px;
  height: 520px;
  border: 1px solid var(--tutorial-accent-mid);
  border-radius: 999px;
  transform: rotate(-18deg);
}

.tutorial-demo-bg::before {
  top: 80px;
  left: 45%;
}

.tutorial-demo-bg::after {
  right: -170px;
  bottom: -230px;
}

.tutorial-demo-bg span {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--tutorial-accent);
  box-shadow: 0 0 22px var(--tutorial-accent);
  animation: pulse-dot 3.2s ease-in-out infinite;
}

.tutorial-topbar,
.tutorial-grid {
  position: relative;
  z-index: 1;
}

.tutorial-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 30px 18px;
}

.tutorial-kicker {
  color: var(--tutorial-accent);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.tutorial-topbar h3 {
  margin-top: 8px;
  font-size: clamp(24px, 3vw, 40px);
  font-weight: 950;
  line-height: 1.04;
  color: white;
}

.tutorial-live {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.74);
  padding: 9px 13px;
  font-size: 12px;
  font-weight: 800;
  color: #cbd5e1;
  white-space: nowrap;
}

.tutorial-live span {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: var(--tutorial-accent);
  box-shadow: 0 0 18px var(--tutorial-accent);
}

.tutorial-grid {
  display: grid;
  grid-template-columns: minmax(130px, .32fr) minmax(0, 1fr) minmax(230px, .58fr);
  gap: 18px;
  padding: 0 30px 30px;
}

.tutorial-steps {
  display: grid;
  gap: 10px;
  align-content: start;
}

.tutorial-step {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 10px;
  align-items: center;
  min-height: 58px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.56);
  padding: 10px;
  text-align: left;
  color: #cbd5e1;
  transition: transform .18s ease, border-color .18s ease, background .18s ease;
}

.tutorial-step:hover {
  border-color: var(--tutorial-accent-mid);
  transform: translateY(-1px);
}

.tutorial-step small {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
  font-size: 11px;
  font-weight: 900;
}

.tutorial-step span {
  font-size: 13px;
  font-weight: 850;
  line-height: 1.25;
}

.tutorial-step-active {
  border-color: var(--tutorial-accent);
  background: linear-gradient(135deg, var(--tutorial-accent-soft), rgba(15, 23, 42, 0.78));
  color: #f8fafc;
}

.tutorial-step-active small {
  background: var(--tutorial-accent);
  color: #04111d;
}

.tutorial-main-card,
.preview-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(2, 6, 23, 0.66);
  backdrop-filter: blur(16px);
}

.tutorial-main-card {
  min-height: 420px;
  border-radius: 26px;
  padding: 30px;
}

.tutorial-step-label {
  display: inline-flex;
  border-radius: 999px;
  background: var(--tutorial-accent-soft);
  padding: 7px 11px;
  color: var(--tutorial-accent);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .14em;
  text-transform: uppercase;
}

.tutorial-main-card h2 {
  margin-top: 20px;
  max-width: 720px;
  color: white;
  font-size: clamp(28px, 4.2vw, 56px);
  font-weight: 950;
  line-height: 1.02;
}

.tutorial-main-card p {
  margin-top: 16px;
  max-width: 660px;
  color: #cbd5e1;
  font-size: 16px;
  line-height: 1.75;
}

.tutorial-conversation {
  display: grid;
  gap: 12px;
  margin-top: 24px;
}

.bubble {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  padding: 14px 16px;
}

.bubble span {
  display: block;
  margin-bottom: 5px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .13em;
  text-transform: uppercase;
}

.bubble strong {
  color: #f8fafc;
  font-size: 14px;
  line-height: 1.55;
}

.bubble-user {
  background: rgba(15, 23, 42, 0.72);
}

.bubble-ai {
  background: linear-gradient(135deg, var(--tutorial-accent-soft), rgba(14, 165, 233, 0.10));
}

.tutorial-output-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.tutorial-output {
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.045);
  padding: 14px;
}

.tutorial-output small {
  display: block;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 850;
}

.tutorial-output strong {
  display: block;
  margin-top: 5px;
  color: #f8fafc;
  font-size: 13px;
  line-height: 1.35;
}

.tutorial-preview {
  display: grid;
  gap: 14px;
  align-content: start;
}

.preview-card {
  border-radius: 22px;
  padding: 18px;
}

.preview-card-primary {
  background: linear-gradient(135deg, var(--tutorial-accent-soft), rgba(15, 23, 42, 0.72));
}

.preview-card p {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.preview-card h4 {
  margin-top: 8px;
  color: white;
  font-size: 20px;
  font-weight: 900;
  line-height: 1.2;
}

.preview-card span {
  display: inline-flex;
  margin-top: 10px;
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 700;
}

.preview-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.preview-card-head strong {
  color: var(--tutorial-accent);
  font-size: 22px;
  font-weight: 950;
}

.progress-shell {
  height: 8px;
  margin-top: 12px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.16);
}

.progress-shell i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--tutorial-accent), #7dd3fc);
}

.preview-card ul {
  margin-top: 13px;
  display: grid;
  gap: 8px;
}

.preview-card li {
  color: #cbd5e1;
  font-size: 13px;
  line-height: 1.35;
}

.deliverable-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.deliverable-list span {
  margin: 0;
  border: 1px solid var(--tutorial-accent-mid);
  border-radius: 999px;
  background: var(--tutorial-accent-soft);
  padding: 7px 10px;
  color: #e2e8f0;
  font-size: 12px;
  font-weight: 850;
}

@keyframes pulse-dot {
  0%, 100% {
    transform: scale(.8);
    filter: blur(0);
  }
  50% {
    transform: scale(1.45);
    filter: blur(.2px);
  }
}

@media (max-width: 1180px) {
  .tutorial-grid {
    grid-template-columns: 1fr;
  }
  .tutorial-steps {
    display: flex;
    overflow-x: auto;
    padding-bottom: 4px;
  }
  .tutorial-step {
    min-width: 190px;
  }
  .tutorial-preview {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .tutorial-topbar {
    flex-direction: column;
    padding: 22px 20px 14px;
  }
  .tutorial-grid {
    padding: 0 20px 20px;
  }
  .tutorial-main-card {
    padding: 22px;
  }
  .tutorial-output-grid,
  .tutorial-preview {
    grid-template-columns: 1fr;
  }
}
</style>
