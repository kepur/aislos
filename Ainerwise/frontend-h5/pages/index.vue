<template>
  <div class="px-4 py-4 space-y-5">
    <!-- Hero card -->
    <div class="hero-card rounded-2xl p-5 text-white relative overflow-hidden">
      <div class="relative z-10">
        <p class="text-xs font-semibold uppercase tracking-wider text-blue-200">{{ $t('home.heroKicker') }}</p>
        <h1 class="mt-2 text-xl font-bold leading-snug">{{ $t('home.heroTitle') }}</h1>
        <p class="mt-2 text-xs text-blue-100 leading-relaxed line-clamp-2">{{ $t('home.heroSubtitle') }}</p>
        <div class="mt-4 flex gap-2">
          <NuxtLink to="/submit-requirement" class="text-xs font-semibold bg-white text-blue-600 px-4 py-2 rounded-full shadow-sm">
            {{ $t('home.heroCta1') }}
          </NuxtLink>
          <NuxtLink to="/ai-brain" class="text-xs font-semibold bg-white/20 backdrop-blur-sm text-white px-4 py-2 rounded-full border border-white/30">
            AI Brain Demo
          </NuxtLink>
        </div>
      </div>
      <!-- Decorative circles -->
      <div class="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/10"></div>
      <div class="absolute -bottom-4 -right-4 w-20 h-20 rounded-full bg-white/5"></div>
    </div>

    <!-- Protocol tags -->
    <div class="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 scrollbar-hide">
      <span v-for="signal in heroSignals" :key="signal"
        class="flex-shrink-0 text-[10px] font-medium text-slate-500 bg-white px-3 py-1.5 rounded-full border border-slate-100 shadow-sm">
        {{ signal }}
      </span>
    </div>

    <!-- Operating model -->
    <div class="grid grid-cols-3 gap-2">
      <div v-for="item in operatingModel" :key="item.kicker"
        class="bg-white rounded-xl p-3 text-center border border-slate-100 shadow-sm">
        <div class="w-10 h-10 mx-auto rounded-full bg-blue-50 flex items-center justify-center mb-2">
          <span class="text-lg">{{ item.emoji }}</span>
        </div>
        <p class="text-[10px] font-bold text-blue-500 uppercase tracking-wide">{{ item.kicker }}</p>
        <p class="text-xs font-semibold text-slate-700 mt-1 line-clamp-2">{{ item.title }}</p>
      </div>
    </div>

    <!-- Solutions section -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-base font-bold text-slate-800">{{ $t('home.solutionsTitle') }}</h2>
        <NuxtLink to="/solutions" class="text-xs font-semibold text-blue-500">{{ $t('common.viewAll') }} &rarr;</NuxtLink>
      </div>
      <div class="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
        <NuxtLink
          v-for="solution in solutions"
          :key="solution.slug"
          :to="`/solutions/${solution.slug}`"
          class="flex-shrink-0 w-52 bg-white rounded-xl p-4 border border-slate-100 shadow-sm hover:shadow-md transition"
        >
          <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mb-3">
            <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-slate-800 line-clamp-1">{{ solution.title }}</h3>
          <p class="text-xs text-slate-400 mt-1 line-clamp-2">{{ solution.description }}</p>
        </NuxtLink>

        <!-- Placeholder if no solutions from API -->
      </div>
    </div>

    <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
      <p class="text-[10px] font-bold uppercase tracking-wider text-blue-500">China Tier-1 Supply Chain</p>
      <p class="mt-1 text-xs leading-relaxed text-slate-500">
        AinerWise positions the catalog around project-grade Chinese leaders and verified ecosystem partners, not cheap commodity sourcing.
      </p>
      <div class="mt-3 flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
        <span v-for="partner in demoSupplyPartners" :key="partner.name" class="flex-shrink-0 rounded-full bg-blue-50 px-3 py-1 text-[10px] font-semibold text-blue-600">
          {{ partner.name }}
        </span>
      </div>
    </div>

    <!-- Intelligence Levels -->
    <div>
      <h2 class="text-base font-bold text-slate-800 mb-3">{{ $t('home.intelligenceKicker') }}</h2>
      <div class="space-y-2">
        <div v-for="level in intelligenceLevels" :key="level.level"
          class="bg-white rounded-xl p-3 flex items-center gap-3 border border-slate-100 shadow-sm">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center flex-shrink-0">
            <span class="text-xs font-bold text-white">{{ level.level }}</span>
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-800 truncate">{{ level.name }}</h3>
              <span class="text-[10px] font-medium text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full flex-shrink-0 ml-2">{{ level.status }}</span>
            </div>
            <p class="text-xs text-slate-400 mt-0.5 line-clamp-1">{{ level.text }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Why AinerWise -->
    <div>
      <h2 class="text-base font-bold text-slate-800 mb-3">{{ $t('home.whyTitle') }}</h2>
      <div class="grid grid-cols-2 gap-2">
        <div v-for="reason in whyReasons" :key="reason.title"
          class="bg-white rounded-xl p-4 text-center border border-slate-100 shadow-sm">
          <div class="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-2">
            <span class="text-xl">{{ reason.emoji }}</span>
          </div>
          <h3 class="text-xs font-semibold text-slate-700">{{ reason.title }}</h3>
          <p class="text-[10px] text-slate-400 mt-1 line-clamp-2">{{ reason.desc }}</p>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div class="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl p-5 text-center text-white">
      <h2 class="text-lg font-bold">{{ $t('home.ctaTitle') }}</h2>
      <p class="text-xs text-blue-100 mt-1">{{ $t('home.ctaSubtitle') }}</p>
      <div class="mt-4 flex gap-2 justify-center">
        <NuxtLink to="/submit-requirement" class="text-xs font-semibold bg-white text-blue-600 px-5 py-2.5 rounded-full shadow-md">
          {{ $t('nav.submitRequirement') }}
        </NuxtLink>
        <NuxtLink to="/contact" class="text-xs font-semibold bg-white/20 text-white px-5 py-2.5 rounded-full border border-white/30">
          {{ $t('nav.contact') }}
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { apiFetch } = useApi()
const { demoSolutions, demoSupplyPartners } = useDemoCatalog()

const solutions = ref<any[]>(demoSolutions.slice(0, 6))

const heroSignals = ['Buildings', 'Cold Chain', 'Kitchen', 'Water', 'Energy', 'Industrial']

const operatingModel = computed(() => [
  { kicker: t('home.opAssess'), title: t('home.opAssessTitle'), emoji: '🔍' },
  { kicker: t('home.opMatch'), title: t('home.opMatchTitle'), emoji: '🎯' },
  { kicker: t('home.opDeliver'), title: t('home.opDeliverTitle'), emoji: '🚀' },
])

const intelligenceLevels = computed(() => [
  { level: 'L1', name: t('intelligence.l1'), status: t('intelligence.l1Status'), text: t('intelligence.l1Text') },
  { level: 'L2', name: t('intelligence.l2'), status: t('intelligence.l2Status'), text: t('intelligence.l2Text') },
  { level: 'L3', name: t('intelligence.l3'), status: t('intelligence.l3Status'), text: t('intelligence.l3Text') },
  { level: 'L4', name: t('intelligence.l4'), status: t('intelligence.l4Status'), text: t('intelligence.l4Text') },
  { level: 'L5', name: t('intelligence.l5'), status: t('intelligence.l5Status'), text: t('intelligence.l5Text') },
  { level: 'L6', name: t('intelligence.l6'), status: t('intelligence.l6Status'), text: t('intelligence.l6Text') },
])

const whyReasons = computed(() => [
  { emoji: '🤖', title: t('home.whyAI'), desc: t('home.whyAIDesc') },
  { emoji: '📦', title: t('home.whySupply'), desc: t('home.whySupplyDesc') },
  { emoji: '🔧', title: t('home.whyLocal'), desc: t('home.whyLocalDesc') },
  { emoji: '🕐', title: t('home.whyLifecycle'), desc: t('home.whyLifecycleDesc') },
])

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/solutions')
    solutions.value = res.items || res || []
  } catch {}
  if (!solutions.value.length) {
    solutions.value = demoSolutions.slice(0, 6)
  }
})
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%);
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
