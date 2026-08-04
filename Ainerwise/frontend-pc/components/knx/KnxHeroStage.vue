<template>
  <section class="knx-stage relative overflow-hidden">
    <!-- Building visual, drawn rather than photographed: no third-party
         project imagery, and it scales cleanly at any viewport. -->
    <svg
      class="knx-stage-art absolute inset-0 h-full w-full"
      viewBox="0 0 1600 900"
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="knxSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0b3a32" />
          <stop offset="55%" stop-color="#124b3f" />
          <stop offset="100%" stop-color="#0a2a25" />
        </linearGradient>
        <linearGradient id="knxFacade" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#e8ece9" />
          <stop offset="55%" stop-color="#c3cdc7" />
          <stop offset="100%" stop-color="#8d9a94" />
        </linearGradient>
        <linearGradient id="knxGlass" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#1d5f52" />
          <stop offset="100%" stop-color="#0f3b33" />
        </linearGradient>
        <!-- The signature device: a green light traced along the silhouette -->
        <filter id="knxGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="9" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <rect width="1600" height="900" fill="url(#knxSky)" />

      <!-- Distant skyline for depth -->
      <g opacity=".28" fill="#0a332c">
        <rect x="60" y="560" width="120" height="340" />
        <rect x="200" y="620" width="90" height="280" />
        <rect x="1320" y="590" width="110" height="310" />
        <rect x="1450" y="640" width="120" height="260" />
      </g>

      <!-- Main tower -->
      <g>
        <path d="M470 210 L1130 150 L1130 900 L470 900 Z" fill="url(#knxFacade)" />
        <path d="M1130 150 L1290 250 L1290 900 L1130 900 Z" fill="#7d8b85" />

        <!-- Diagrid: the lattice that gives the facade its character -->
        <g stroke="#f2f5f3" stroke-width="7" fill="none" opacity=".85">
          <path v-for="(d, i) in diagrid" :key="i" :d="d" />
        </g>

        <!-- Lit interiors -->
        <g fill="url(#knxGlass)">
          <rect v-for="(w, i) in windows" :key="i" :x="w.x" :y="w.y" :width="w.w" :height="w.h" opacity=".9" />
        </g>
        <g fill="#ffd9a0" opacity=".75">
          <rect v-for="(w, i) in litWindows" :key="`lit${i}`" :x="w.x" :y="w.y" :width="w.w" :height="w.h" />
        </g>

        <!-- Ground floor glow -->
        <rect x="470" y="800" width="660" height="100" fill="#f6c98a" opacity=".22" />
      </g>

      <!-- Traced silhouette -->
      <path
        class="knx-stage-outline"
        d="M470 210 L1130 150 L1290 250 L1290 900 L470 900 Z"
        fill="none"
        stroke="#4ade80"
        stroke-width="5"
        filter="url(#knxGlow)"
      />

      <!-- Foreground haze so the headline always sits on something calm -->
      <rect width="1600" height="900" fill="url(#knxSky)" opacity=".42" />
    </svg>

    <!-- Copy -->
    <div class="relative flex min-h-[560px] flex-col items-center justify-center px-4 py-24 text-center sm:px-6 lg:min-h-[660px] lg:py-32">
      <span v-if="eyebrow" class="knx-stage-eyebrow">{{ eyebrow }}</span>
      <h1 class="mt-4 max-w-5xl text-4xl font-bold leading-[1.08] tracking-tight text-white sm:text-5xl lg:text-7xl">
        {{ title }}
      </h1>
      <p v-if="subtitle" class="mt-6 max-w-2xl text-lg text-emerald-50/85 lg:text-2xl">{{ subtitle }}</p>

      <div class="mt-10 flex flex-col gap-3 sm:flex-row">
        <NuxtLink :to="primaryTo" class="knx-stage-cta">
          {{ primaryLabel }}
          <span class="knx-stage-cta-arrow">→</span>
        </NuxtLink>
        <NuxtLink v-if="secondaryTo" :to="secondaryTo" class="knx-stage-ghost">{{ secondaryLabel }}</NuxtLink>
      </div>
    </div>

    <!-- Credit line, mirroring how project photography is attributed -->
    <p v-if="credit" class="absolute bottom-5 right-5 text-right text-xs leading-relaxed text-emerald-100/50">
      {{ credit }}
    </p>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    eyebrow?: string
    primaryTo: string
    primaryLabel: string
    secondaryTo?: string
    secondaryLabel?: string
    credit?: string
  }>(),
  { secondaryLabel: '' }
)

/** Diamond lattice across the tower face. */
const diagrid = (() => {
  const paths: string[] = []
  const top = 210
  const bottom = 900
  const left = 470
  const right = 1130
  const step = 110
  for (let x = left - 440; x < right + 440; x += step) {
    paths.push(`M ${x} ${bottom} L ${x + 440} ${top}`)
    paths.push(`M ${x} ${top} L ${x + 440} ${bottom}`)
  }
  return paths
})()

/** Window bands, with a scattered few lit to suggest an occupied building. */
const windows = (() => {
  const out: Array<{ x: number; y: number; w: number; h: number }> = []
  for (let row = 0; row < 11; row++) {
    for (let col = 0; col < 7; col++) {
      out.push({ x: 500 + col * 90, y: 250 + row * 58, w: 62, h: 34 })
    }
  }
  return out
})()

const litWindows = windows.filter((_, i) => [3, 9, 14, 22, 27, 35, 41, 48, 55, 63, 70].includes(i))
</script>

<style scoped>
.knx-stage { background: #0a2a25; }
.knx-stage-art { object-fit: cover; }

.knx-stage-outline {
  animation: knx-trace 6s ease-in-out infinite;
}
@keyframes knx-trace {
  0%, 100% { opacity: .55; }
  50% { opacity: 1; }
}

.knx-stage-eyebrow {
  @apply inline-block rounded-full px-4 py-1.5 text-xs font-bold uppercase tracking-[0.2em];
  background: rgba(74, 222, 128, .16);
  color: #86efac;
}

.knx-stage-cta {
  @apply inline-flex items-center gap-3 rounded-full py-4 pl-8 pr-3 text-base font-semibold transition;
  background: #22c55e;
  color: #052e26;
}
.knx-stage-cta:hover { background: #4ade80; }
.knx-stage-cta-arrow {
  @apply flex h-9 w-9 items-center justify-center rounded-full text-sm;
  background: #052e26;
  color: #4ade80;
}
.knx-stage-ghost {
  @apply inline-flex items-center justify-center rounded-full border px-8 py-4 text-base font-semibold text-white transition;
  border-color: rgba(255, 255, 255, .4);
}
.knx-stage-ghost:hover { background: rgba(255, 255, 255, .12); }

@media (prefers-reduced-motion: reduce) {
  .knx-stage-outline { animation: none; opacity: .85; }
}
</style>
