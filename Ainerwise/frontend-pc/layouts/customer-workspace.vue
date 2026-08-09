<template>
  <div class="portal-layout flex min-h-screen">
    <!-- nuxt.config sets pathPrefix: false, so the component name carries no
         directory prefix. The old double-prefixed name resolved to nothing and
         the sidebar silently disappeared, leaving a phone-like single column. -->
    <CustomerWorkspaceSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <header class="portal-topbar sticky top-0 z-30 flex h-14 items-center justify-between px-4 sm:px-6">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wider text-blue-500">{{ $t('portal.shell.brand') }}</p>
          <p class="text-[11px] text-slate-400">{{ $t('portal.shell.tagline') }}</p>
        </div>
        <div class="flex items-center gap-3">
          <LanguageSwitcher class="portal-lang-switch" />
          <NuxtLink to="/submit-requirement" class="hidden rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 px-4 py-2 text-sm font-medium text-white sm:inline-flex">
            {{ $t('nav.submitRequirement') }}
          </NuxtLink>
          <button class="rounded-lg p-2 text-sm text-slate-400 hover:bg-red-50 hover:text-red-500" @click="logout">{{ $t('nav.logout') }}</button>
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
