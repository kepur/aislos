<template>
  <section class="aw-immersive-hero knx-on-dark relative isolate overflow-hidden border-b border-white/10">
    <div class="aw-immersive-hero__bg-layer absolute inset-0" aria-hidden="true">
      <slot name="background">
        <div class="aw-immersive-hero__bg absolute inset-0" :style="{ backgroundImage: `url(${backgroundImage})` }" />
      </slot>
    </div>
    <div class="aw-immersive-hero__grid absolute inset-0" aria-hidden="true" />
    <div class="aw-immersive-hero__beam aw-immersive-hero__beam-a" aria-hidden="true" />
    <div class="aw-immersive-hero__beam aw-immersive-hero__beam-b" aria-hidden="true" />

    <div class="container-main relative px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <nav v-if="crumbs.length" class="mb-8 flex flex-wrap items-center gap-2 text-sm">
        <template v-for="(crumb, i) in crumbs" :key="crumb.to || crumb.label">
          <NuxtLink
            v-if="crumb.to"
            :to="crumb.to"
            class="text-emerald-100/70 transition hover:text-white"
          >{{ crumb.label }}</NuxtLink>
          <span v-else class="text-emerald-100/70">{{ crumb.label }}</span>
          <span v-if="i < crumbs.length - 1" class="text-emerald-100/35">/</span>
        </template>
      </nav>

      <div class="aw-hero-layout" :class="hideAside ? 'aw-hero-layout--single' : ''">
        <div>
          <div v-if="badges.length" class="mb-5 flex flex-wrap gap-2">
            <span v-for="badge in badges" :key="badge.label" :class="badge.ai ? 'aw-hero-pill aw-hero-pill--ai' : 'aw-hero-pill'">
              <span v-if="badge.ai">✦</span>{{ badge.label }}
            </span>
          </div>

          <p v-if="eyebrow" class="aw-hero-eyebrow">{{ eyebrow }}</p>
          <h1 class="aw-hero-title mt-4 max-w-4xl font-black text-white">
            {{ title }}
          </h1>
          <p v-if="subtitle" class="aw-hero-subtitle mt-6 max-w-3xl">
            {{ subtitle }}
          </p>

          <div v-if="primaryTo || secondaryTo" class="mt-10 flex flex-col gap-3 sm:flex-row">
            <NuxtLink v-if="primaryTo" :to="primaryTo" class="aw-hero-primary">
              {{ primaryLabel }}
              <span>→</span>
            </NuxtLink>
            <NuxtLink v-if="secondaryTo" :to="secondaryTo" class="aw-hero-secondary">
              {{ secondaryLabel }}
            </NuxtLink>
          </div>
        </div>

        <div v-if="!hideAside" class="relative">
          <div v-if="showOrbit" class="aw-orbit" aria-hidden="true">
            <span class="aw-orbit__ring aw-orbit__ring-a" />
            <span class="aw-orbit__ring aw-orbit__ring-b" />
            <span class="aw-orbit__core">
              <span class="aw-orbit__core-label">{{ coreLabel }}</span>
            </span>
          </div>
          <slot name="aside">
            <div class="aw-hero-panel">
              <div class="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                <div v-for="stat in stats" :key="stat.label" class="aw-hero-stat">
                  <strong>{{ stat.value }}</strong>
                  <span>{{ stat.label }}</span>
                </div>
              </div>
              <div v-if="nodes.length" class="mt-5 grid gap-2">
                <div v-for="node in nodes" :key="node" class="aw-hero-node">
                  <span />
                  <p>{{ node }}</p>
                </div>
              </div>
            </div>
          </slot>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface Crumb { label: string; to?: string }
interface Badge { label: string; ai?: boolean }
interface Stat { value: string; label: string }

withDefaults(
  defineProps<{
    backgroundImage: string
    title: string
    eyebrow?: string
    subtitle?: string
    primaryTo?: string
    primaryLabel?: string
    secondaryTo?: string
    secondaryLabel?: string
    coreLabel?: string
    showOrbit?: boolean
    hideAside?: boolean
    crumbs?: Crumb[]
    badges?: Badge[]
    stats?: Stat[]
    nodes?: string[]
  }>(),
  {
    eyebrow: '',
    subtitle: '',
    primaryTo: '',
    primaryLabel: '',
    secondaryTo: '',
    secondaryLabel: '',
    coreLabel: 'AinerWise AI',
    showOrbit: true,
    hideAside: false,
    crumbs: () => [],
    badges: () => [],
    stats: () => [],
    nodes: () => [],
  }
)
</script>

<style scoped>
.aw-immersive-hero {
  min-height: 690px;
  background:
    radial-gradient(circle at 78% 24%, rgba(34, 197, 94, .18), transparent 32%),
    radial-gradient(circle at 16% 68%, rgba(14, 165, 233, .1), transparent 32%),
    linear-gradient(135deg, #020617, #04130f 52%, #020617);
}
.aw-immersive-hero__bg-layer {
  overflow: hidden;
}
.aw-immersive-hero__bg {
  background-size: cover;
  background-position: center;
  opacity: .88;
  transform: scale(1.01);
}
.aw-immersive-hero__bg::after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 58% 54% at 26% 50%, rgba(2, 6, 23, .08), rgba(2, 6, 23, .58) 66%, rgba(2, 6, 23, .88)),
    linear-gradient(90deg, rgba(2, 6, 23, .88), rgba(2, 6, 23, .42) 48%, rgba(2, 6, 23, .76));
}
.aw-immersive-hero__grid {
  background-image:
    linear-gradient(rgba(209, 250, 229, .08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(209, 250, 229, .08) 1px, transparent 1px);
  background-size: 84px 84px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, .8), transparent 92%);
  opacity: .55;
}
.aw-hero-layout {
  display: grid;
  gap: 3rem;
}
@media (min-width: 1024px) {
  .aw-hero-layout {
    grid-template-columns: 1.05fr .95fr;
    align-items: center;
  }
  .aw-hero-layout--single {
    grid-template-columns: minmax(0, .64fr) minmax(0, .36fr);
  }
}
.aw-immersive-hero__beam {
  position: absolute;
  height: 2px;
  width: 52vw;
  background: linear-gradient(90deg, transparent, rgba(110, 231, 183, .95), transparent);
  filter: drop-shadow(0 0 18px rgba(52, 211, 153, .8));
  opacity: .54;
}
.aw-immersive-hero__beam-a {
  right: 5vw;
  top: 24%;
  transform: rotate(-13deg);
}
.aw-immersive-hero__beam-b {
  left: 12vw;
  bottom: 18%;
  transform: rotate(10deg);
}
.aw-hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: .5rem;
  color: #a7f3d0;
  font-size: .75rem;
  font-weight: 900;
  letter-spacing: .24em;
  text-transform: uppercase;
}
.aw-hero-eyebrow::before {
  content: "";
  width: 2.25rem;
  height: 2px;
  background: #6ee7b7;
  box-shadow: 0 0 18px rgba(110, 231, 183, .9);
}
.aw-hero-title {
  font-size: clamp(3rem, 5.7vw, 5.7rem);
  line-height: .98;
  letter-spacing: -.055em;
  text-wrap: balance;
  text-shadow: 0 28px 80px rgba(0, 0, 0, .42);
}
.aw-hero-subtitle {
  color: rgba(236, 253, 245, .84);
  font-size: clamp(1.05rem, 1.45vw, 1.42rem);
  line-height: 1.72;
  text-shadow: 0 18px 60px rgba(0, 0, 0, .38);
}
.aw-hero-pill {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  border: 1px solid rgba(167, 243, 208, .25);
  border-radius: 999px;
  background: rgba(6, 78, 59, .34);
  color: rgba(236, 253, 245, .92);
  padding: .45rem .75rem;
  font-size: .68rem;
  font-weight: 900;
  letter-spacing: .16em;
  text-transform: uppercase;
  backdrop-filter: blur(14px);
}
.aw-hero-pill--ai {
  border-color: rgba(125, 211, 252, .34);
  background: rgba(14, 116, 144, .28);
  color: #cffafe;
}
.aw-hero-primary,
.aw-hero-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: .6rem;
  border-radius: 999px;
  padding: .95rem 1.35rem;
  font-weight: 900;
  transition: transform .18s ease, background .18s ease, border-color .18s ease;
}
.aw-hero-primary {
  background: #22c55e;
  color: #022c22;
  box-shadow: 0 18px 45px rgba(34, 197, 94, .28);
}
.aw-hero-primary:hover {
  background: #86efac;
  transform: translateY(-2px);
}
.aw-hero-secondary {
  border: 1px solid rgba(236, 253, 245, .2);
  background: rgba(2, 44, 34, .72);
  color: #ecfdf5;
}
.aw-hero-secondary:hover {
  border-color: rgba(236, 253, 245, .42);
  background: rgba(6, 78, 59, .86);
  transform: translateY(-2px);
}
.aw-orbit {
  position: absolute;
  inset: -5rem -1rem auto auto;
  width: min(30vw, 360px);
  aspect-ratio: 1;
  opacity: .86;
  pointer-events: none;
}
.aw-orbit__ring,
.aw-orbit__core {
  position: absolute;
  inset: 0;
  border-radius: 999px;
}
.aw-orbit__ring {
  border: 1px solid rgba(167, 243, 208, .22);
  box-shadow: inset 0 0 42px rgba(52, 211, 153, .1), 0 0 46px rgba(52, 211, 153, .12);
}
.aw-orbit__ring-a { animation: aw-spin 22s linear infinite; }
.aw-orbit__ring-b {
  inset: 16%;
  border-color: rgba(125, 211, 252, .24);
  animation: aw-spin 16s linear reverse infinite;
}
.aw-orbit__core {
  inset: 34%;
  display: grid;
  place-items: center;
  background: radial-gradient(circle, rgba(110, 231, 183, .3), rgba(6, 78, 59, .28));
  border: 1px solid rgba(167, 243, 208, .34);
}
.aw-orbit__core-label {
  max-width: 6rem;
  color: #ecfdf5;
  font-size: .7rem;
  font-weight: 900;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: .14em;
}
.aw-hero-panel {
  position: relative;
  margin-top: 6rem;
  border: 1px solid rgba(236, 253, 245, .14);
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(2, 6, 23, .72), rgba(6, 78, 59, .38));
  padding: 1.1rem;
  box-shadow: 0 26px 80px rgba(2, 6, 23, .4), inset 0 1px 0 rgba(255, 255, 255, .08);
  backdrop-filter: blur(18px);
}
.aw-hero-stat {
  border: 1px solid rgba(236, 253, 245, .12);
  border-radius: 18px;
  background: rgba(255, 255, 255, .06);
  padding: 1rem;
}
.aw-hero-stat strong {
  display: block;
  color: #ecfdf5;
  font-size: 1.55rem;
  line-height: 1;
}
.aw-hero-stat span {
  margin-top: .45rem;
  display: block;
  color: rgba(209, 250, 229, .72);
  font-size: .76rem;
  font-weight: 700;
}
.aw-hero-node {
  display: flex;
  align-items: center;
  gap: .7rem;
  border: 1px solid rgba(236, 253, 245, .1);
  border-radius: 16px;
  background: rgba(2, 6, 23, .36);
  padding: .75rem .9rem;
}
.aw-hero-node span {
  width: .55rem;
  height: .55rem;
  border-radius: 999px;
  background: #6ee7b7;
  box-shadow: 0 0 20px rgba(110, 231, 183, .9);
}
.aw-hero-node p {
  color: rgba(236, 253, 245, .86);
  font-size: .84rem;
  font-weight: 700;
}
@keyframes aw-spin {
  to { transform: rotate(360deg); }
}
@media (max-width: 1023px) {
  .aw-orbit { display: none; }
  .aw-hero-panel { margin-top: 0; }
}
@media (max-width: 640px) {
  .aw-immersive-hero { min-height: 620px; }
  .aw-hero-title { font-size: clamp(2.45rem, 12vw, 3.5rem); }
}
</style>
