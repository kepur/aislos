<template>
  <aside class="customer-sidebar hidden w-64 flex-shrink-0 flex-col overflow-y-auto lg:flex">
    <div class="border-b border-slate-100 px-5 py-5">
      <NuxtLink to="/portal" class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/20">
          <span class="text-sm font-black text-white">A</span>
        </div>
        <div>
          <span class="text-base font-bold tracking-tight text-slate-800">AinerWise</span>
          <span class="block text-[10px] font-semibold uppercase tracking-wider text-blue-500">{{ $t('portal.shell.workspace') }}</span>
        </div>
      </NuxtLink>
    </div>

    <div class="border-b border-slate-100 px-4 py-4">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 shadow-md shadow-blue-500/20">
          <span class="text-sm font-bold text-white">{{ userInitial }}</span>
        </div>
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold text-slate-800">{{ user?.full_name || $t('portal.shell.customer') }}</p>
          <p class="truncate text-xs text-slate-400">{{ user?.email }}</p>
        </div>
      </div>
    </div>

    <nav class="flex-1 space-y-1 px-3 py-4">
      <NuxtLink
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] text-slate-500 transition hover:bg-slate-50 hover:text-slate-800"
        active-class="!bg-blue-50 !text-blue-600 font-semibold shadow-sm"
      >
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 text-[10px] font-black uppercase text-slate-500">{{ item.code }}</span>
        <span>{{ item.label }}</span>
      </NuxtLink>
    </nav>

    <div class="px-4 pb-4">
      <div class="rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
        <p class="text-xs font-semibold text-blue-700">{{ $t('portal.shell.promoTitle') }}</p>
        <p class="mt-1 text-xs leading-relaxed text-blue-500/80">{{ $t('portal.shell.promoBody') }}</p>
        <NuxtLink to="/portal/tickets" class="mt-2 inline-block text-xs font-semibold text-blue-600">{{ $t('portal.shell.openSupport') }}</NuxtLink>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { user } = useAuth()

const userInitial = computed(() => (user.value?.full_name || user.value?.email || 'C').charAt(0).toUpperCase())
const menuItems = computed(() => [
  { to: '/portal', label: t('portal.shell.navOverview'), code: 'OV' },
  { to: '/portal/leads', label: t('portal.shell.navRequirements'), code: 'RQ' },
  { to: '/portal/procurement', label: t('portal.shell.navProcurement'), code: 'PO' },
  { to: '/portal/approvals', label: t('portal.shell.navApprovals'), code: 'AP' },
  { to: '/portal/projects', label: t('portal.shell.navProjects'), code: 'PR' },
  { to: '/portal/installations', label: t('portal.shell.navInstallations'), code: 'IN' },
  { to: '/portal/assets', label: t('portal.shell.navAssets'), code: 'AS' },
  { to: '/portal/tickets', label: t('portal.shell.navAfterSales'), code: 'SV' },
  { to: '/portal/profile', label: t('portal.shell.navProfile'), code: 'ME' },
])
</script>

<style scoped>
.customer-sidebar {
  background: #ffffff;
  border-right: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.03);
}
</style>
