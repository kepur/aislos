<template>
  <div class="brain-hero-visual" @mouseenter="paused = true" @mouseleave="paused = false">
    <ClientOnly>
      <BuildingBrain3D
        :level="activeLevel"
        :scenario-key="activeScenario.key"
        variant="hero"
        :show-readout="false"
      />
      <template #fallback>
        <div class="brain-hero-fallback" />
      </template>
    </ClientOnly>

    <div class="brain-hero-glass brain-hero-status">
      <span class="brain-hero-live-dot" />
      <span>{{ t('brain.heroVisualLive') }}</span>
      <strong>{{ activeLevel }}</strong>
    </div>

    <div class="brain-hero-glass brain-hero-copy">
      <p class="brain-hero-eyebrow">{{ t('brain.heroVisualEyebrow') }}</p>
      <h3>{{ t('brain.heroVisualTitle') }}</h3>
      <p>{{ t('brain.heroVisualSubtitle') }}</p>

      <div class="brain-hero-levels" :aria-label="t('brain.heroVisualLevel')">
        <button
          v-for="(level, index) in levels"
          :key="level"
          type="button"
          class="brain-hero-level"
          :class="activeLevel === level ? 'brain-hero-level--active' : ''"
          @click="pickLevel(index)"
        >
          <strong>{{ level }}</strong>
          <span>{{ levelLabel(level) }}</span>
        </button>
      </div>
    </div>

    <div class="brain-hero-glass brain-hero-context">
      <div>
        <p>{{ t('brain.heroVisualScene') }}</p>
        <strong>{{ activeScenario.name }}</strong>
      </div>
      <span>{{ activeScenario.level }}</span>
    </div>

    <div class="brain-hero-scenes" :aria-label="t('brain.demoScenario')">
      <button
        v-for="(scenario, index) in visibleScenarios"
        :key="scenario.key"
        type="button"
        class="brain-hero-scene"
        :class="activeScenario.key === scenario.key ? 'brain-hero-scene--active' : ''"
        @click="pickScenario(index)"
      >
        {{ scenario.name }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
type BrainLevel = 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6'

const { t } = useI18n()
const { scenarios } = useBuildingBrain()

const levels: BrainLevel[] = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']
const activeLevelIndex = ref(3)
const activeScenarioIndex = ref(0)
const paused = ref(false)
let timer: ReturnType<typeof window.setInterval> | undefined

const activeLevel = computed(() => levels[activeLevelIndex.value] || 'L4')
const activeScenario = computed(() => scenarios[activeScenarioIndex.value] || scenarios[0])
const visibleScenarios = computed(() => scenarios.slice(0, 5))

function levelLabel(level: BrainLevel) {
  return t(`brain.heroLevel${level}`)
}

function pickLevel(index: number) {
  activeLevelIndex.value = index
}

function pickScenario(index: number) {
  activeScenarioIndex.value = index
}

onMounted(() => {
  timer = window.setInterval(() => {
    if (paused.value) return
    activeLevelIndex.value = (activeLevelIndex.value + 1) % levels.length
    if (activeLevelIndex.value % 2 === 0) {
      activeScenarioIndex.value = (activeScenarioIndex.value + 1) % visibleScenarios.value.length
    }
  }, 3800)
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.brain-hero-visual {
  position: relative;
  min-height: 560px;
  overflow: hidden;
  border: 1px solid rgba(167, 243, 208, 0.18);
  border-radius: 32px;
  background: rgba(2, 6, 23, 0.62);
  box-shadow: 0 28px 90px rgba(2, 6, 23, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.brain-hero-fallback {
  min-height: 560px;
  background:
    radial-gradient(circle at 50% 42%, rgba(20, 184, 166, 0.28), transparent 32%),
    linear-gradient(135deg, #020617, #061428 48%, #04251e);
}

.brain-hero-glass {
  position: absolute;
  z-index: 2;
  border: 1px solid rgba(167, 243, 208, 0.16);
  background: rgba(2, 6, 23, 0.68);
  color: #ecfdf5;
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 60px rgba(2, 6, 23, 0.38);
}

.brain-hero-status {
  top: 18px;
  left: 18px;
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  border-radius: 999px;
  padding: 0.55rem 0.75rem;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.brain-hero-status strong {
  color: #67e8f9;
}

.brain-hero-live-dot {
  width: 0.52rem;
  height: 0.52rem;
  border-radius: 999px;
  background: #34d399;
  box-shadow: 0 0 18px rgba(52, 211, 153, 0.9);
}

.brain-hero-copy {
  right: 18px;
  top: 18px;
  width: min(410px, calc(100% - 36px));
  border-radius: 24px;
  padding: 1rem;
}

.brain-hero-eyebrow {
  margin: 0;
  color: #6ee7b7;
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.brain-hero-copy h3 {
  margin: 0.45rem 0 0;
  color: #fff;
  font-size: clamp(1.35rem, 2.4vw, 2.2rem);
  font-weight: 950;
  letter-spacing: -0.04em;
}

.brain-hero-copy p:last-of-type {
  margin: 0.6rem 0 0;
  color: rgba(226, 232, 240, 0.82);
  font-size: 0.88rem;
  line-height: 1.55;
}

.brain-hero-levels {
  margin-top: 0.9rem;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 0.35rem;
}

.brain-hero-level {
  min-width: 0;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  padding: 0.45rem 0.35rem;
  text-align: left;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.brain-hero-level strong,
.brain-hero-level span {
  display: block;
}

.brain-hero-level strong {
  color: #ecfdf5;
  font-size: 0.86rem;
  line-height: 1;
}

.brain-hero-level span {
  margin-top: 0.25rem;
  overflow: hidden;
  color: rgba(209, 250, 229, 0.62);
  font-size: 0.58rem;
  font-weight: 800;
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brain-hero-level:hover,
.brain-hero-level--active {
  border-color: rgba(52, 211, 153, 0.8);
  background: rgba(16, 185, 129, 0.18);
  transform: translateY(-1px);
}

.brain-hero-context {
  left: 18px;
  bottom: 86px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  width: min(420px, calc(100% - 36px));
  border-radius: 22px;
  padding: 0.9rem 1rem;
}

.brain-hero-context p {
  margin: 0;
  color: rgba(209, 250, 229, 0.62);
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.brain-hero-context strong {
  display: block;
  margin-top: 0.28rem;
  color: #fff;
  font-size: 1rem;
}

.brain-hero-context > span {
  color: #a7f3d0;
  font-size: 0.85rem;
  font-weight: 900;
}

.brain-hero-scenes {
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 18px;
  z-index: 2;
  display: flex;
  gap: 0.45rem;
  overflow-x: auto;
  padding-bottom: 0.05rem;
}

.brain-hero-scene {
  flex: 0 0 auto;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.72);
  color: rgba(226, 232, 240, 0.84);
  padding: 0.52rem 0.78rem;
  font-size: 0.72rem;
  font-weight: 850;
  transition: border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
}

.brain-hero-scene--active,
.brain-hero-scene:hover {
  border-color: rgba(52, 211, 153, 0.82);
  background: rgba(6, 78, 59, 0.8);
  color: #ecfdf5;
}

@media (max-width: 1280px) {
  .brain-hero-copy {
    position: absolute;
    left: 18px;
    right: 18px;
    top: auto;
    bottom: 152px;
    width: auto;
  }

  .brain-hero-context {
    display: none;
  }
}

@media (max-width: 640px) {
  .brain-hero-visual,
  .brain-hero-fallback {
    min-height: 620px;
  }

  .brain-hero-levels {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
