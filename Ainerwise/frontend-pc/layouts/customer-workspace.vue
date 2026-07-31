<template>
  <div class="portal-layout flex min-h-screen">
    <CustomerCustomerWorkspaceSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <header class="portal-topbar sticky top-0 z-30 flex h-14 items-center justify-between px-4 sm:px-6">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wider text-blue-500">AinerWise Customer Workspace</p>
          <p class="text-[11px] text-slate-400">Your outcomes, procurement, delivery, and lifecycle</p>
        </div>
        <div class="flex items-center gap-3">
          <PortalSwitcher />
          <LanguageSwitcher class="portal-lang-switch" />
          <NuxtLink to="/submit-requirement" class="hidden rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 px-4 py-2 text-sm font-medium text-white sm:inline-flex">
            New requirement
          </NuxtLink>
          <button class="rounded-lg p-2 text-sm text-slate-400 hover:bg-red-50 hover:text-red-500" @click="logout">Sign out</button>
        </div>
      </header>
      <main class="flex-1 overflow-auto p-4 sm:p-6 lg:p-8"><slot /></main>
    </div>
  </div>
</template>

<script setup lang="ts">
const { logout } = useAuth()
</script>

<style scoped>
.portal-layout {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e8eef6 100%);
}
.portal-topbar {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}
</style>
