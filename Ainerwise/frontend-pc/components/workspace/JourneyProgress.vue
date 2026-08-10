<template>
  <div class="pc-card !p-5">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-sm font-bold ws-title">{{ $t('journey.title') }}</h3>
      <span class="text-xs ws-faint">{{ $t('journey.stageOf', { current: activeIndex + 1, total: stages.length }) }}</span>
    </div>

    <ol class="journey-rail">
      <li v-for="(stage, index) in stages" :key="stage.key" class="journey-stage">
        <!-- Connector sits behind the lamp so the rail reads as one line. -->
        <span v-if="index > 0" class="journey-link" :class="{ 'journey-link--lit': index <= activeIndex }"></span>
        <span
          class="journey-lamp"
          :class="{
            'journey-lamp--done': index < activeIndex,
            'journey-lamp--current': index === activeIndex,
          }"
        >
          <UIcon v-if="index < activeIndex" name="i-heroicons-check" class="h-3.5 w-3.5" />
          <span v-else class="journey-lamp__dot"></span>
        </span>
        <p class="journey-label" :class="{ 'journey-label--active': index <= activeIndex }">{{ stage.label }}</p>
      </li>
    </ol>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  /** Raw status from a request, order or project. */
  status?: string | null
  /** Optional explicit stage key, when the caller knows better than the status. */
  stageKey?: string | null
}>()

const { t } = useI18n()

// The buyer journey, in the order the nav presents it. Each stage lists the
// status fragments that mean "this stage has been reached".
const STAGES = [
  { key: 'requested', match: ['draft', 'new', 'created', 'requested'] },
  { key: 'offers', match: ['published', 'active', 'receiving', 'quoted', 'offer'] },
  { key: 'awarded', match: ['awarded', 'confirmed', 'accepted', 'won'] },
  { key: 'escrow', match: ['paid', 'escrow', 'awaiting_payment'] },
  { key: 'delivery', match: ['in_progress', 'shipped', 'delivery', 'delivered', 'dispatch'] },
  { key: 'install', match: ['install', 'commission', 'on_site', 'scheduled'] },
  { key: 'accepted', match: ['completed', 'complete', 'closed', 'signed_off', 'verified'] },
  { key: 'service', match: ['maintenance', 'service', 'warranty', 'support'] },
]

const stages = computed(() =>
  STAGES.map(stage => ({ key: stage.key, label: t(`journey.stage.${stage.key}`) })),
)

const activeIndex = computed(() => {
  if (props.stageKey) {
    const explicit = STAGES.findIndex(s => s.key === props.stageKey)
    if (explicit >= 0) return explicit
  }
  const raw = String(props.status || '').toLowerCase()
  if (!raw) return 0
  // Walk backwards so a later stage wins when fragments overlap
  // (e.g. "delivered" matches both delivery and accepted vocabularies).
  for (let i = STAGES.length - 1; i >= 0; i -= 1) {
    if (STAGES[i].match.some(token => raw.includes(token))) return i
  }
  return 0
})
</script>

<style scoped>
.journey-rail {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}
.journey-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  text-align: center;
}
.journey-link {
  position: absolute;
  top: 0.85rem;
  right: 50%;
  width: 100%;
  height: 2px;
  background: var(--hairline-soft);
  transition: background 0.25s ease;
}
.journey-link--lit { background: var(--accent); }

.journey-lamp {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  border: 2px solid var(--hairline-soft);
  background: var(--card-bg);
  color: var(--accent-contrast);
  transition: all 0.25s ease;
}
.journey-lamp__dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 999px;
  background: var(--text-faint);
  transition: background 0.25s ease;
}
.journey-lamp--done {
  border-color: var(--accent);
  background: var(--accent);
}
.journey-lamp--current {
  border-color: var(--accent);
  background: var(--accent);
  /* The current stage is the one thing worth drawing the eye to. */
  box-shadow: 0 0 0 4px var(--accent-soft), 0 0 16px var(--accent);
}
.journey-lamp--current .journey-lamp__dot { background: var(--accent-contrast); }

.journey-label {
  margin: 0;
  font-size: 0.72rem;
  line-height: 1.3;
  color: var(--text-faint);
  transition: color 0.25s ease;
}
.journey-label--active {
  color: var(--page-text);
  font-weight: 600;
}

@media (prefers-reduced-motion: reduce) {
  .journey-lamp,
  .journey-link,
  .journey-label,
  .journey-lamp__dot { transition: none; }
}

@media (max-width: 900px) {
  .journey-rail { grid-template-columns: repeat(4, minmax(0, 1fr)); row-gap: 1.4rem; }
  /* On two rows the connector into each row's first lamp would dangle. */
  .journey-stage:nth-child(4n + 1) .journey-link { display: none; }
}
</style>
