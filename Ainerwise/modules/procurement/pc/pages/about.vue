<template>
  <div class="min-h-screen bg-slate-950 text-white">
    <section class="relative overflow-hidden px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
      <div class="absolute inset-0">
        <div class="absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.08)_1px,transparent_1px)] bg-[size:96px_96px]"></div>
        <div class="absolute -left-32 top-20 h-96 w-96 rounded-full bg-cyan-500/15 blur-3xl"></div>
        <div class="absolute -right-24 bottom-10 h-[28rem] w-[28rem] rounded-full bg-emerald-500/10 blur-3xl"></div>
        <div class="absolute inset-0 bg-gradient-to-b from-slate-950/70 via-slate-950/90 to-slate-950"></div>
      </div>

      <div class="relative mx-auto max-w-4xl">
        <h1 class="text-center text-3xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
          {{ appStore.t('about.title') }}
        </h1>

        <div class="mt-10 space-y-6 rounded-[1.75rem] border border-cyan-400/25 bg-white/[0.06] p-8 leading-relaxed text-slate-300 shadow-[0_0_30px_rgba(14,165,233,0.1)] backdrop-blur-xl">
          <p>{{ appStore.t('about.p1') }}</p>
          <p>{{ appStore.t('about.p2') }}</p>

          <h2 class="mt-8 border-b border-white/10 pb-2 text-xl font-bold text-white">
            {{ appStore.t('about.approachTitle') }}
          </h2>
          <p>{{ appStore.t('about.approachText') }}</p>

          <h2 class="mt-8 border-b border-white/10 pb-2 text-xl font-bold text-white">
            {{ appStore.t('about.techTitle') }}
          </h2>
          <ul class="list-disc space-y-2 pl-6 text-cyan-200">
            <li>{{ appStore.t('about.tech1') }}</li>
            <li>{{ appStore.t('about.tech2') }}</li>
            <li>{{ appStore.t('about.tech3') }}</li>
            <li>{{ appStore.t('about.tech4') }}</li>
          </ul>

          <h2 class="mt-8 border-b border-white/10 pb-2 text-xl font-bold text-white">
            {{ appStore.t('about.regionsTitle') }}
          </h2>
          <p>{{ appStore.t('about.regionsText') }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '~/stores/app'

definePageMeta({ layout: 'default' })

const appStore = useAppStore()
</script>
