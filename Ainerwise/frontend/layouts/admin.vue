<template>
  <div class="admin-layout min-h-screen flex" :class="{ 'theme-light': theme === 'light' }">
    <!-- Sidebar -->
    <AdminSidebar />

    <!-- Mobile sidebar overlay -->
    <Transition name="fade">
      <div v-if="mobileOpen" class="fixed inset-0 bg-black/60 z-40 lg:hidden" @click="mobileOpen = false" />
    </Transition>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <header class="admin-topbar sticky top-0 z-30 px-4 sm:px-6 h-14 flex items-center justify-between">
        <!-- Mobile menu button -->
        <button @click="mobileOpen = !mobileOpen" class="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <!-- Breadcrumb / page title area -->
        <div class="hidden lg:flex items-center gap-2 text-sm">
          <span class="text-slate-500">Admin</span>
          <span class="text-slate-600">/</span>
          <span class="text-slate-300 font-medium">{{ currentPage }}</span>
        </div>

        <!-- Right side -->
        <div class="flex items-center gap-3">
          <button @click="toggleTheme" class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition flex items-center justify-center">
            <span v-if="theme === 'light'" class="text-lg leading-none">🌙</span>
            <span v-else class="text-lg leading-none">☀️</span>
          </button>
          
          <LanguageSwitcher />

          <!-- Notifications bell -->
          <button class="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
            <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-cyan-400 rounded-full shadow-[0_0_6px_rgba(6,182,212,0.6)]"></span>
          </button>

          <!-- User menu -->
          <div class="flex items-center gap-2 pl-3 border-l border-white/5">
            <div class="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center">
              <span class="text-xs font-bold text-white">{{ userInitial }}</span>
            </div>
            <span class="text-sm text-slate-300 hidden sm:inline">{{ user?.full_name || user?.email }}</span>
            <button @click="logout" class="text-xs text-slate-500 hover:text-red-400 transition ml-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-4 sm:p-6 overflow-auto">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'admin' })
const { user, logout } = useAuth()
const route = useRoute()
const mobileOpen = ref(false)

// Theme toggle with localStorage persistence
const theme = ref('dark')
onMounted(() => {
  const saved = localStorage.getItem('admin-theme')
  if (saved) theme.value = saved
})
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('admin-theme', theme.value)
}

const userInitial = computed(() => {
  const name = user.value?.full_name || user.value?.email || 'A'
  return name.charAt(0).toUpperCase()
})

const currentPage = computed(() => {
  const path = route.path.replace('/admin', '').replace(/^\//, '')
  if (!path) return 'Dashboard'
  return path.split('/')[0].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
})
</script>

<style scoped>
.admin-layout {
  background: linear-gradient(135deg, #0a0f1e 0%, #0d1325 50%, #0f172a 100%);
}
.admin-topbar {
  background: rgba(15,23,42,0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
