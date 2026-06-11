<template>
  <aside class="portal-sidebar w-64 flex-shrink-0 hidden lg:flex flex-col overflow-y-auto z-10">
    <div class="px-5 py-5 border-b border-slate-100">
      <NuxtLink to="/" class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <span class="text-white font-black text-sm">A</span>
        </div>
        <div>
          <span class="text-base font-bold text-slate-800 tracking-tight">AinerWise</span>
          <span class="block text-[10px] text-blue-500 font-semibold tracking-wider uppercase">Client Portal</span>
        </div>
      </NuxtLink>
    </div>

    <div class="px-4 py-4 border-b border-slate-100">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center shadow-md shadow-blue-500/20">
          <span class="text-sm font-bold text-white">{{ userInitial }}</span>
        </div>
        <div class="min-w-0">
          <p class="text-sm font-semibold text-slate-800 truncate">{{ user?.full_name || 'User' }}</p>
          <p class="text-xs text-slate-400 truncate">{{ user?.email }}</p>
        </div>
      </div>
    </div>

    <nav class="flex-1 py-4 px-3 space-y-1">
      <NuxtLink
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        class="portal-nav-item group flex items-center gap-3 px-3 py-2.5 text-[13px] rounded-xl transition-all duration-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50"
        active-class="!text-blue-600 !bg-blue-50 font-semibold shadow-sm"
      >
        <span class="text-lg">{{ item.emoji }}</span>
        <span>{{ item.label }}</span>
      </NuxtLink>
    </nav>

    <div class="px-4 pb-4">
      <div class="rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 p-4">
        <p class="text-xs font-semibold text-blue-700 mb-1">Need Help?</p>
        <p class="text-xs text-blue-500/80 leading-relaxed">Contact our team for smart building consultation.</p>
        <NuxtLink to="/contact" class="inline-block mt-2 text-xs font-semibold text-blue-600 hover:text-blue-700">
          Get Support &rarr;
        </NuxtLink>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
const { t } = useI18n({ useScope: 'global' })
const { user } = useAuth()

const userInitial = computed(() => {
  const name = user.value?.full_name || user.value?.email || 'U'
  return name.charAt(0).toUpperCase()
})

const menuItems = computed(() => [
  { to: '/portal', label: t('portal.dashboard'), emoji: '📊' },
  { to: '/portal/leads', label: t('portal.myLeads'), emoji: '📋' },
  { to: '/portal/quotes', label: t('portal.myQuotes'), emoji: '💰' },
  { to: '/portal/projects', label: t('portal.myProjects'), emoji: '🏗️' },
  { to: '/portal/tickets', label: t('portal.myTickets'), emoji: '🎫' },
  { to: '/portal/profile', label: t('portal.profile'), emoji: '👤' },
])
</script>

<style scoped>
.portal-sidebar {
  background: #ffffff;
  border-right: 1px solid rgba(226,232,240,0.8);
  box-shadow: 2px 0 12px rgba(0,0,0,0.03);
}
</style>
