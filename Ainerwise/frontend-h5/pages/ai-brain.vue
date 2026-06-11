<template>
  <div class="px-4 py-4 space-y-4">
    <!-- Hero -->
    <div class="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-5 text-white relative overflow-hidden">
      <div class="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-blue-500/10"></div>
      <div class="absolute bottom-0 left-0 w-24 h-24 rounded-full bg-indigo-500/10"></div>
      <div class="relative z-10">
        <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500/30 to-indigo-500/30 border border-white/10 flex items-center justify-center mb-3">
          <svg class="w-7 h-7 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
          </svg>
        </div>
        <h1 class="text-xl font-bold">AI Building Brain</h1>
        <p class="text-sm text-slate-300 mt-1">Smart buildings, factory automation, energy, product matching, and system orchestration</p>
      </div>
    </div>

    <!-- What AI Brain Does -->
    <div class="space-y-2">
      <h2 class="text-sm font-bold text-slate-800 px-1">What AI Brain Can Do</h2>
      <div v-for="feature in features" :key="feature.title"
        class="bg-white rounded-xl p-4 border border-slate-100 shadow-sm flex items-start gap-3">
        <div :class="['w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', feature.bg]">
          <span class="text-lg">{{ feature.emoji }}</span>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-slate-800">{{ feature.title }}</h3>
          <p class="text-xs text-slate-400 mt-0.5">{{ feature.desc }}</p>
        </div>
      </div>
    </div>

    <!-- AI Consultation CTA (requires login) -->
    <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-center">
      <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center mb-3">
        <svg class="w-8 h-8 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
        </svg>
      </div>
      <h3 class="text-base font-bold text-slate-800">Start AI Consultation</h3>
      <p class="text-xs text-slate-400 mt-1">Describe your project and get AI-powered preliminary assessment</p>

      <button v-if="!isLoggedIn" @click="goLogin"
        class="mt-4 w-full text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 rounded-xl shadow-md shadow-blue-500/20">
        Login to Start
      </button>
      <NuxtLink v-else to="/submit-requirement"
        class="mt-4 inline-block w-full text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 rounded-xl shadow-md shadow-blue-500/20 text-center">
        Start Assessment
      </NuxtLink>
    </div>

    <!-- Intelligence Levels preview -->
    <div>
      <h2 class="text-sm font-bold text-slate-800 mb-3 px-1">Intelligence Levels</h2>
      <div class="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
        <div v-for="level in levels" :key="level.level"
          class="flex-shrink-0 w-44 bg-white rounded-xl p-3 border border-slate-100 shadow-sm">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-xs font-bold text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-2 py-0.5 rounded-md">{{ level.level }}</span>
            <span class="text-[10px] text-slate-400 font-medium">{{ level.status }}</span>
          </div>
          <h3 class="text-xs font-semibold text-slate-800">{{ level.name }}</h3>
          <p class="text-[10px] text-slate-400 mt-1 line-clamp-2">{{ level.text }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { isLoggedIn } = useAuth()

function goLogin() {
  navigateTo('/login?redirect=/submit-requirement')
}

const features = [
  { title: 'Project Assessment', desc: 'AI analyzes your building requirements, goals, budget and site conditions', emoji: '🔍', bg: 'bg-blue-50' },
  { title: 'Product Matching', desc: 'Match protocols, certifications, compatibility and regional availability', emoji: '🎯', bg: 'bg-emerald-50' },
  { title: 'Solution Design', desc: 'Generate preliminary system architecture and component list', emoji: '📐', bg: 'bg-indigo-50' },
  { title: 'Cost Estimation', desc: 'Preliminary budgeting based on real product data and local rates', emoji: '💰', bg: 'bg-amber-50' },
  { title: 'Industrial Automation', desc: 'Factory lines, PLC/SCADA, machine energy, compressed air, chillers, robots, and OT gateway planning', emoji: '🏭', bg: 'bg-orange-50' },
  { title: 'Lifecycle Planning', desc: 'Maintenance schedules, upgrade paths, and long-term support plans', emoji: '🔄', bg: 'bg-purple-50' },
]

const levels = computed(() => [
  { level: 'L1', name: t('intelligence.l1'), status: t('intelligence.l1Status'), text: t('intelligence.l1Text') },
  { level: 'L2', name: t('intelligence.l2'), status: t('intelligence.l2Status'), text: t('intelligence.l2Text') },
  { level: 'L3', name: t('intelligence.l3'), status: t('intelligence.l3Status'), text: t('intelligence.l3Text') },
  { level: 'L4', name: t('intelligence.l4'), status: t('intelligence.l4Status'), text: t('intelligence.l4Text') },
  { level: 'L5', name: t('intelligence.l5'), status: t('intelligence.l5Status'), text: t('intelligence.l5Text') },
  { level: 'L6', name: t('intelligence.l6'), status: t('intelligence.l6Status'), text: t('intelligence.l6Text') },
])
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>
