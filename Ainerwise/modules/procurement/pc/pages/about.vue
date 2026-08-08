<template>
  <div class="min-h-screen bg-slate-50">
    <section class="mx-auto max-w-7xl px-6 py-12">
      <!-- Hero -->
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
              <UButton
                :to="localizedPath('/supplier-onboarding')"
                color="white"
                variant="ghost"
                size="lg"
                class="text-white hover:bg-white/10 hover:text-white"
              >
                {{ appStore.t('about.becomeSupplier') }}
              </UButton>
            </div>
            <div class="mt-10 flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-slate-300">
              <div class="flex items-center">
                <UIcon name="i-heroicons-shield-check" class="mr-2 h-5 w-5 text-emerald-400" />
                {{ appStore.t('about.trustEscrow') }}
              </div>
              <div class="flex items-center">
                <UIcon name="i-heroicons-check-badge" class="mr-2 h-5 w-5 text-indigo-300" />
                {{ appStore.t('about.trustVerified') }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pillars -->
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

      <!-- How it works -->
      <div class="mt-8 rounded-[2rem] border border-slate-200 bg-white px-6 py-10 shadow-sm lg:px-10">
        <div class="mx-auto max-w-2xl text-center">
          <p class="text-sm font-black uppercase tracking-[0.2em] text-indigo-500">{{ appStore.t('about.howKicker') }}</p>
          <h2 class="mt-3 text-3xl font-black text-slate-950">{{ appStore.t('about.howTitle') }}</h2>
          <p class="mt-4 text-lg leading-7 text-slate-600">{{ appStore.t('about.howSubtitle') }}</p>
        </div>

        <div class="relative mt-12 grid gap-8 md:grid-cols-5">
          <div class="absolute left-0 top-8 z-0 hidden h-0.5 w-full bg-indigo-100 md:block"></div>
          <div
            v-for="(step, index) in howSteps"
            :key="step.title"
            class="relative z-10 flex flex-col items-center bg-white p-4 text-center"
          >
            <div
              class="mb-4 flex h-16 w-16 items-center justify-center rounded-full border-4 border-white shadow-sm"
              :class="index === howSteps.length - 1 ? 'bg-emerald-100 text-emerald-600' : 'bg-indigo-100 text-indigo-600'"
            >
              <UIcon :name="step.icon" class="h-8 w-8" />
            </div>
            <h4 class="mb-2 font-bold text-slate-900">{{ index + 1 }}. {{ step.title }}</h4>
            <p class="text-sm leading-6 text-slate-600">{{ step.body }}</p>
          </div>
        </div>
      </div>

      <!-- Operating model -->
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

      <!-- Company story -->
      <div class="mt-8 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm lg:p-10">
        <p class="text-sm font-black uppercase tracking-[0.2em] text-indigo-500">{{ appStore.t('about.storyKicker') }}</p>
        <h2 class="mt-3 text-3xl font-black text-slate-950">{{ appStore.t('about.storyTitle') }}</h2>

        <div class="mt-6 grid gap-8 lg:grid-cols-2">
          <div class="space-y-5 leading-7 text-slate-600">
            <p>{{ appStore.t('about.p1') }}</p>
            <p>{{ appStore.t('about.p2') }}</p>

            <div class="pt-2">
              <h3 class="border-b border-slate-100 pb-2 text-lg font-black text-slate-950">{{ appStore.t('about.approachTitle') }}</h3>
              <p class="mt-4">{{ appStore.t('about.approachText') }}</p>
            </div>
          </div>

          <div class="space-y-6">
            <div class="rounded-2xl border border-slate-100 bg-slate-50 p-6">
              <h3 class="text-lg font-black text-slate-950">{{ appStore.t('about.techTitle') }}</h3>
              <ul class="mt-4 space-y-3">
                <li v-for="item in techItems" :key="item" class="flex items-start text-sm leading-6 text-slate-600">
                  <UIcon name="i-heroicons-check-circle" class="mr-2 mt-0.5 h-5 w-5 shrink-0 text-emerald-500" />
                  {{ item }}
                </li>
              </ul>
            </div>

            <div class="rounded-2xl border border-slate-100 bg-slate-50 p-6">
              <h3 class="text-lg font-black text-slate-950">{{ appStore.t('about.regionsTitle') }}</h3>
              <p class="mt-3 text-sm leading-6 text-slate-600">{{ appStore.t('about.regionsText') }}</p>
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

const howSteps = computed(() => [
  {
    icon: 'i-heroicons-pencil-square',
    title: appStore.t('about.how1Title'),
    body: appStore.t('about.how1Body'),
  },
  {
    icon: 'i-heroicons-envelope-open',
    title: appStore.t('about.how2Title'),
    body: appStore.t('about.how2Body'),
  },
  {
    icon: 'i-heroicons-scale',
    title: appStore.t('about.how3Title'),
    body: appStore.t('about.how3Body'),
  },
  {
    icon: 'i-heroicons-lock-closed',
    title: appStore.t('about.how4Title'),
    body: appStore.t('about.how4Body'),
  },
  {
    icon: 'i-heroicons-check-badge',
    title: appStore.t('about.how5Title'),
    body: appStore.t('about.how5Body'),
  },
])

const flowSteps = computed(() => [
  appStore.t('about.step1'),
  appStore.t('about.step2'),
  appStore.t('about.step3'),
  appStore.t('about.step4'),
])

const techItems = computed(() => [
  appStore.t('about.tech1'),
  appStore.t('about.tech2'),
  appStore.t('about.tech3'),
  appStore.t('about.tech4'),
])

function localizedPath(path: string) {
  return appStore.localizedPath(path)
}
</script>
