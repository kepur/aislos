<template>
  <div
    class="admin-app min-h-screen"
    :class="[
      isLoginPage ? 'admin-login-shell theme-dark' : themeClass,
    ]"
  >
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { initAuth } = useAuth()
const { loadAccess } = usePortalManifest()
const { isLight } = useAdminTheme()

const isLoginPage = computed(() => route.path === '/login')
const themeClass = computed(() => (isLight.value ? 'theme-light' : 'theme-dark'))

onMounted(async () => {
  await initAuth()
  await loadAccess()
})
</script>

<style>
.admin-app {
  background: linear-gradient(135deg, #0a0f1e 0%, #0d1325 50%, #0f172a 100%);
}
.admin-app.theme-light {
  background: #f8fafc;
}
.admin-app.theme-dark {
  background: linear-gradient(135deg, #0a0f1e 0%, #0d1325 50%, #0f172a 100%);
}
.admin-login-shell {
  background: transparent !important;
}
</style>
