<template>
  <section class="knx-hub relative overflow-hidden py-16 lg:py-24">
    <!-- Star field: pure CSS, no asset to load -->
    <div class="knx-hub-stars pointer-events-none absolute inset-0" aria-hidden="true" />

    <div class="container-main relative px-4 sm:px-6 lg:px-8">
      <div class="mx-auto max-w-3xl text-center">
        <span class="knx-hub-eyebrow">{{ eyebrow }}</span>
        <h2 class="mt-3 text-3xl font-bold tracking-tight text-white lg:text-5xl">{{ title }}</h2>
        <p class="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-emerald-100/80">{{ subtitle }}</p>
        <NuxtLink v-if="ctaTo" :to="ctaTo" class="knx-hub-cta mt-8">
          {{ ctaLabel }}
          <span class="knx-hub-cta-arrow">→</span>
        </NuxtLink>
      </div>

      <!-- Hub: suppliers on the left, building systems on the right, the AI
           brain in the middle. Flowing links are drawn behind the cards. -->
      <div class="relative mt-14 grid items-center gap-6 lg:mt-20 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
        <!-- Connecting curves (desktop only — meaningless when stacked) -->
        <svg
          class="pointer-events-none absolute inset-0 hidden h-full w-full lg:block"
          viewBox="0 0 1000 620"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="knxHubLineL" x1="0" x2="1">
              <stop offset="0%" stop-color="#34d399" stop-opacity="0" />
              <stop offset="100%" stop-color="#34d399" stop-opacity=".55" />
            </linearGradient>
            <linearGradient id="knxHubLineR" x1="0" x2="1">
              <stop offset="0%" stop-color="#34d399" stop-opacity=".55" />
              <stop offset="100%" stop-color="#34d399" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path
            v-for="(d, i) in leftCurves"
            :key="`l${i}`"
            :d="d"
            fill="none"
            stroke="url(#knxHubLineL)"
            stroke-width="1.2"
          />
          <path
            v-for="(d, i) in rightCurves"
            :key="`r${i}`"
            :d="d"
            fill="none"
            stroke="url(#knxHubLineR)"
            stroke-width="1.2"
          />
          <!-- Travelling light pulses along two of the paths -->
          <circle r="3" fill="#6ee7b7">
            <animateMotion :path="leftCurves[1]" dur="4.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0;1;1;0" dur="4.5s" repeatCount="indefinite" />
          </circle>
          <circle r="3" fill="#6ee7b7">
            <animateMotion :path="rightCurves[3]" dur="5.5s" begin="1.2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0;1;1;0" dur="5.5s" begin="1.2s" repeatCount="indefinite" />
          </circle>
        </svg>

        <!-- Left column: the supply chain -->
        <div class="relative z-10 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-1">
          <div v-for="s in suppliers" :key="s" class="knx-hub-card">
            <span class="text-sm font-semibold">{{ s }}</span>
          </div>
        </div>

        <!-- Centre: the AI brain -->
        <div class="relative z-10 flex justify-center py-6 lg:py-0">
          <div class="knx-hub-core">
            <div class="knx-hub-ring knx-hub-ring-1" />
            <div class="knx-hub-ring knx-hub-ring-2" />
            <div class="knx-hub-ring knx-hub-ring-3" />
            <div class="knx-hub-core-inner">
              <FeatureIcon name="ai-brain" class="h-10 w-10 text-white" />
              <span class="mt-2 text-center text-sm font-bold leading-tight text-white">{{ coreLabel }}</span>
            </div>
          </div>
        </div>

        <!-- Right column: the building systems -->
        <div class="relative z-10 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-1">
          <div v-for="sys in systems" :key="sys.label" class="knx-hub-card knx-hub-card-icon">
            <FeatureIcon :name="sys.icon" size="sm" class="text-emerald-700" />
            <span class="text-sm font-semibold">{{ sys.label }}</span>
          </div>
        </div>
      </div>

      <div v-if="footnoteTo" class="mt-10 text-center">
        <NuxtLink :to="footnoteTo" class="text-sm font-semibold text-emerald-300 hover:text-emerald-200">
          {{ footnoteLabel }} →
        </NuxtLink>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    eyebrow: string
    title: string
    subtitle: string
    coreLabel: string
    suppliers: string[]
    systems: Array<{ icon: string; label: string }>
    ctaTo?: string
    ctaLabel?: string
    footnoteTo?: string
    footnoteLabel?: string
  }>(),
  { ctaLabel: 'Learn more', footnoteLabel: 'View all' }
)

/**
 * Curves are hand-tuned against the 1000x620 viewBox so they read as cables
 * fanning into the core rather than generic arcs.
 */
const leftCurves = [
  'M 40 60  C 230 90, 300 250, 470 300',
  'M 40 150 C 230 170, 320 260, 470 305',
  'M 40 240 C 240 250, 340 290, 470 310',
  'M 40 330 C 240 330, 340 320, 470 315',
  'M 40 420 C 240 410, 340 350, 470 320',
  'M 40 510 C 240 490, 340 380, 470 325',
  'M 40 580 C 240 550, 340 400, 470 330',
]
const rightCurves = [
  'M 530 300 C 700 250, 770 90, 960 60',
  'M 530 305 C 700 260, 780 170, 960 150',
  'M 530 310 C 700 290, 780 250, 960 240',
  'M 530 315 C 700 320, 780 330, 960 330',
  'M 530 320 C 700 350, 780 410, 960 420',
  'M 530 325 C 700 380, 780 490, 960 510',
  'M 530 330 C 700 400, 780 550, 960 580',
]
</script>

<style scoped>
/* Deep teal canvas — the contrast is what makes the green glow read. */
.knx-hub {
  background: radial-gradient(ellipse at 50% 45%, #0d3b33 0%, #072722 55%, #05201c 100%);
}

.knx-hub-stars {
  background-image:
    radial-gradient(1.5px 1.5px at 12% 18%, rgba(110, 231, 183, .5), transparent),
    radial-gradient(1.5px 1.5px at 78% 12%, rgba(110, 231, 183, .35), transparent),
    radial-gradient(1.5px 1.5px at 34% 72%, rgba(110, 231, 183, .4), transparent),
    radial-gradient(1.5px 1.5px at 88% 62%, rgba(110, 231, 183, .3), transparent),
    radial-gradient(1.5px 1.5px at 22% 46%, rgba(110, 231, 183, .25), transparent),
    radial-gradient(1.5px 1.5px at 62% 88%, rgba(110, 231, 183, .3), transparent);
}

.knx-hub-eyebrow {
  @apply inline-block text-xs font-bold uppercase tracking-[0.2em] text-emerald-400;
}

.knx-hub-cta {
  @apply inline-flex items-center gap-3 rounded-full px-7 py-3.5 text-base font-semibold transition;
  background: #22c55e;
  color: #052e26;
}
.knx-hub-cta:hover { background: #4ade80; }
.knx-hub-cta-arrow {
  @apply flex h-8 w-8 items-center justify-center rounded-full text-sm;
  background: #052e26;
  color: #4ade80;
}

/* White cards float above the dark canvas — the KNX contrast device. */
.knx-hub-card {
  @apply flex items-center justify-center rounded-xl bg-white px-4 py-4 text-center text-slate-800 shadow-lg transition;
  min-height: 62px;
}
.knx-hub-card:hover { transform: translateX(2px); box-shadow: 0 8px 28px rgba(16, 185, 129, .25); }
.knx-hub-card-icon { @apply flex-col gap-1.5; }

/* Concentric glow rings around the core. */
.knx-hub-core {
  @apply relative flex items-center justify-center;
  width: 260px;
  height: 260px;
}
.knx-hub-ring {
  @apply absolute rounded-full;
}
.knx-hub-ring-1 { inset: 0; background: rgba(16, 185, 129, .12); }
.knx-hub-ring-2 { inset: 34px; background: rgba(16, 185, 129, .20); }
.knx-hub-ring-3 { inset: 68px; background: rgba(16, 185, 129, .34); }
.knx-hub-core-inner {
  @apply relative flex flex-col items-center justify-center rounded-full p-6;
  width: 132px;
  height: 132px;
  background: linear-gradient(160deg, #10b981, #059669);
  box-shadow: 0 0 42px rgba(16, 185, 129, .55);
}

@media (prefers-reduced-motion: reduce) {
  .knx-hub circle animateMotion { display: none; }
}
</style>
