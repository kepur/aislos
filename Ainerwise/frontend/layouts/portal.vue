<template>
  <div class="portal-layout min-h-screen flex">
    <!-- Sidebar -->
    <PortalSidebar />

    <!-- Mobile overlay -->
    <Transition name="fade">
      <div v-if="mobileOpen" class="fixed inset-0 bg-black/30 z-40 lg:hidden" @click="mobileOpen = false" />
    </Transition>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <header class="portal-topbar sticky top-0 z-30 px-4 sm:px-6 h-14 flex items-center justify-between">
        <!-- Mobile menu -->
        <button @click="mobileOpen = !mobileOpen" class="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div class="hidden lg:block">
          <span class="text-sm font-medium text-slate-600">{{ $t('portal.dashboard') }}</span>
        </div>

        <div class="flex items-center gap-3">
          <LanguageSwitcher class="portal-lang-switch" />
          <NuxtLink to="/submit-requirement"
            class="hidden sm:inline-flex items-center gap-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-4 py-2 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all">
            + New Requirement
          </NuxtLink>
          <button @click="logout" class="text-sm text-slate-400 hover:text-red-500 transition p-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { user, logout } = useAuth()
const mobileOpen = ref(false)
</script>

<style scoped>
.portal-layout {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e8eef6 100%);
}
.portal-topbar {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226,232,240,0.6);
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Override LanguageSwitcher for light theme */
:deep(.portal-lang-switch select) {
  background: rgba(241,245,249,0.8) !important;
  border-color: rgba(203,213,225,0.6) !important;
  color: #475569 !important;
}
:deep(.portal-lang-switch select option) {
  background: white !important;
  color: #1e293b !important;
}
</style>
