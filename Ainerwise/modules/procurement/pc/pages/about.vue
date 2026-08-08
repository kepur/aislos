<template>
  <div class="min-h-screen bg-slate-50">
    <section class="mx-auto max-w-7xl px-6 py-12">
      <div class="overflow-hidden rounded-[2rem] border border-slate-200 bg-slate-950 shadow-2xl shadow-slate-200/70">
        <div class="relative px-8 py-12 text-white lg:px-12">
          <div class="absolute inset-0 opacity-70">
            <div class="absolute right-[-120px] top-[-160px] h-[360px] w-[360px] rounded-full bg-indigo-500/30 blur-3xl"></div>
            <div class="absolute bottom-[-160px] left-[25%] h-[300px] w-[300px] rounded-full bg-emerald-400/20 blur-3xl"></div>
          </div>
          <div class="relative max-w-3xl">
            <p class="text-sm font-black uppercase tracking-[0.24em] text-emerald-300">{{ appStore.t('about.kicker') }}</p>
            <h1 class="mt-4 text-4xl font-black leading-tight lg:text-6xl">{{ appStore.t('about.title') }}</h1>
            <p class="mt-5 text-lg leading-8 text-slate-300">{{ appStore.t('about.subtitle') }}</p>
            <div class="mt-8 flex flex-wrap gap-3">
              <UButton :to="localizedPath('/marketplace')" color="emerald" size="lg">{{ appStore.t('about.openMarket') }}</UButton>
              <UButton :to="localizedPath('/post-request')" color="white" variant="outline" size="lg">{{ appStore.t('action.postRequest') }}</UButton>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-8 grid gap-4 md:grid-cols-3">
        <div
          v-for="pillar in pillars"
          :key="pillar.title"
          class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <UIcon :name="pillar.icon" class="h-6 w-6" />
          </div>
          <h2 class="mt-5 text-xl font-black text-slate-950">{{ pillar.title }}</h2>
          <p class="mt-3 text-sm leading-6 text-slate-600">{{ pillar.body }}</p>
        </div>
      </div>

      <div class="mt-8 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
        <div class="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <p class="text-sm font-black uppercase tracking-[0.2em] text-indigo-500">{{ appStore.t('about.flowKicker') }}</p>
            <h2 class="mt-3 text-3xl font-black text-slate-950">{{ appStore.t('about.flowTitle') }}</h2>
            <p class="mt-4 leading-7 text-slate-600">{{ appStore.t('about.flowBody') }}</p>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <div
              v-for="step in flowSteps"
              :key="step"
              class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4 text-sm font-bold text-slate-700"
            >
              {{ step }}
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '~/stores/app'

definePageMeta({ layout: 'default' })

const appStore = useAppStore()

const pillars = computed(() => [
  {
    icon: 'i-heroicons-shopping-bag',
    title: appStore.t('about.pillar1Title'),
    body: appStore.t('about.pillar1Body'),
  },
  {
    icon: 'i-heroicons-cpu-chip',
    title: appStore.t('about.pillar2Title'),
    body: appStore.t('about.pillar2Body'),
  },
  {
    icon: 'i-heroicons-wrench-screwdriver',
    title: appStore.t('about.pillar3Title'),
    body: appStore.t('about.pillar3Body'),
  },
])

const flowSteps = computed(() => [
  appStore.t('about.step1'),
  appStore.t('about.step2'),
  appStore.t('about.step3'),
  appStore.t('about.step4'),
])

function localizedPath(path: string) {
  return appStore.localizedPath(path)
}
</script>
