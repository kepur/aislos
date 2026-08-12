<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <header class="sticky top-0 z-40 border-b border-blue-400/15 bg-slate-950/90 backdrop-blur">
      <div class="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
        <div class="flex min-w-0 items-center gap-4">
          <NuxtLink :to="localized('/partner')" class="shrink-0">
            <span class="block text-sm font-bold text-white">AinerWise Partner</span>
            <span class="block text-[10px] uppercase tracking-[0.2em] text-blue-300">{{ $t('partner.companyWorkspace') }}</span>
          </NuxtLink>
          <nav class="hidden items-center gap-1 lg:flex">
            <NuxtLink v-for="item in nav" :key="item.to" :to="localized(item.to)" class="rounded-lg px-3 py-2 text-xs font-semibold text-slate-400 hover:bg-white/5 hover:text-white" active-class="!bg-blue-500/15 !text-blue-200">
              {{ item.label }}
            </NuxtLink>
          </nav>
        </div>
        <div class="flex items-center gap-3">
          <span class="hidden text-xs text-slate-500 sm:inline">{{ user?.email }}</span>
          <button class="rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-400 hover:border-red-400/30 hover:text-red-300" @click="logout">{{ $t('partner.logout') }}</button>
        </div>
      </div>
      <nav class="flex gap-1 overflow-x-auto border-t border-white/5 px-4 py-2 lg:hidden">
        <NuxtLink v-for="item in nav" :key="item.to" :to="localized(item.to)" class="shrink-0 rounded-lg px-3 py-2 text-xs font-semibold text-slate-400" active-class="!bg-blue-500/15 !text-blue-200">
          {{ item.label }}
        </NuxtLink>
      </nav>
    </header>
    <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8"><slot /></main>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { user, logout } = useAuth()
const { t } = useI18n()
const nav = computed(() => [
  { to: '/partner', label: t('partner.navOverview') },
  { to: '/partner/rfqs', label: t('partner.navRfqs') },
  { to: '/partner/work-packages', label: t('partner.navPackages') },
  { to: '/partner/crews', label: t('partner.navCrews') },
  { to: '/partner/workers', label: t('partner.navWorkers') },
  { to: '/partner/tasks', label: t('partner.navTasks') },
  { to: '/partner/calendar', label: t('partner.navSchedule') },
  { to: '/partner/performance', label: t('partner.navPerformance') },
])
</script>
