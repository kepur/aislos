<template>
  <div class="brain-hero-visual">
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

    <div class="brain-hero-scrim" />
    <div class="brain-hero-level-dots" aria-hidden="true">
      <span
        v-for="level in levels"
        :key="level"
        :class="activeLevel === level ? 'is-active' : ''"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
type BrainLevel = 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6'

const { scenarios } = useBuildingBrain()

const levels: BrainLevel[] = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']
const activeLevelIndex = ref(3)
const activeScenarioIndex = ref(0)
let timer: ReturnType<typeof window.setInterval> | undefined

const activeLevel = computed(() => levels[activeLevelIndex.value] || 'L4')
const activeScenario = computed(() => scenarios[activeScenarioIndex.value] || scenarios[0])
const visibleScenarios = computed(() => scenarios.slice(0, 6))

onMounted(() => {
  timer = window.setInterval(() => {
    activeLevelIndex.value = (activeLevelIndex.value + 1) % levels.length
    if (activeLevelIndex.value % 2 === 0) {
      activeScenarioIndex.value = (activeScenarioIndex.value + 1) % visibleScenarios.value.length
    }
  }, 4200)
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.brain-hero-visual {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 62% 38%, rgba(20, 184, 166, 0.22), transparent 30%),
    radial-gradient(circle at 22% 62%, rgba(14, 165, 233, 0.14), transparent 34%),
    linear-gradient(135deg, #020617 0%, #061428 48%, #04251e 100%);
  pointer-events: none;
}

.brain-hero-visual :deep(.brain3d) {
  min-height: 760px;
  height: 100%;
  opacity: 0.9;
  transform: translateX(10%) scale(1.08);
}

.brain-hero-fallback {
  min-height: 760px;
  height: 100%;
  background:
    radial-gradient(circle at 58% 42%, rgba(20, 184, 166, 0.28), transparent 32%),
    linear-gradient(135deg, #020617, #061428 48%, #04251e);
}

.brain-hero-scrim {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(2, 6, 23, 0.95) 0%, rgba(2, 6, 23, 0.72) 34%, rgba(2, 6, 23, 0.22) 62%, rgba(2, 6, 23, 0.62) 100%),
    linear-gradient(0deg, rgba(2, 6, 23, 0.92) 0%, transparent 42%, rgba(2, 6, 23, 0.32) 100%),
    radial-gradient(circle at 74% 46%, transparent 0%, rgba(2, 6, 23, 0.18) 38%, rgba(2, 6, 23, 0.74) 100%);
}

.brain-hero-level-dots {
  position: absolute;
  right: clamp(1.5rem, 4vw, 4rem);
  bottom: clamp(1.5rem, 4vw, 3.5rem);
  display: flex;
  gap: 0.5rem;
  opacity: 0.78;
}

.brain-hero-level-dots span {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 999px;
  background: rgba(209, 250, 229, 0.32);
  box-shadow: 0 0 18px rgba(110, 231, 183, 0.16);
  transition: width 0.28s ease, background 0.28s ease, box-shadow 0.28s ease;
}

.brain-hero-level-dots span.is-active {
  width: 1.75rem;
  background: rgba(52, 211, 153, 0.95);
  box-shadow: 0 0 22px rgba(52, 211, 153, 0.72);
}

@media (max-width: 768px) {
  .brain-hero-visual :deep(.brain3d) {
    transform: translateX(16%) scale(1.08);
  }

  .brain-hero-scrim {
    background:
      linear-gradient(90deg, rgba(2, 6, 23, 0.96), rgba(2, 6, 23, 0.58)),
      linear-gradient(0deg, rgba(2, 6, 23, 0.92), transparent 45%);
  }
}
</style>
