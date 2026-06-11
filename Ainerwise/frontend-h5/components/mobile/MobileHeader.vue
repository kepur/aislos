<template>
  <header class="mobile-header">
    <NuxtLink :to="homePath" class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
        <span class="text-white font-black text-xs">A</span>
      </div>
      <span class="text-base font-bold text-slate-800">{{ portal.shortName }}</span>
    </NuxtLink>

    <div class="flex items-center gap-2">
      <LanguageSwitcher class="h5-lang" />
      <NuxtLink
        v-if="!isLoggedIn"
        to="/login"
        class="text-xs font-semibold text-white bg-blue-500 px-3 py-1.5 rounded-full hover:bg-blue-600 transition"
      >
        {{ $t('auth.login') }}
      </NuxtLink>
      <NuxtLink
        v-else
        to="/profile"
        class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center"
      >
        <span class="text-xs font-bold text-white">{{ userInitial }}</span>
      </NuxtLink>
    </div>
  </header>
</template>

<script setup lang="ts">
const { user, isLoggedIn } = useAuth()
const { portal } = usePortalMode()
const homePath = portal.home

const userInitial = computed(() => {
  const name = user.value?.full_name || user.value?.email || 'U'
  return name.charAt(0).toUpperCase()
})
</script>

<style scoped>
.mobile-header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

:deep(.h5-lang select) {
  background: rgba(241,245,249,0.8) !important;
  border-color: rgba(203,213,225,0.5) !important;
  color: #475569 !important;
  font-size: 11px !important;
  padding: 2px 6px !important;
  border-radius: 6px !important;
}
:deep(.h5-lang select option) {
  background: white !important;
  color: #1e293b !important;
}
</style>
