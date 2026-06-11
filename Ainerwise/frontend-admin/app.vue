<template>
  <div class="admin-app min-h-screen" :class="{ 'theme-light': isLight && !isLoginPage, 'admin-login-shell': isLoginPage }">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { initAuth } = useAuth()
const { isLight } = useAdminTheme()

const isLoginPage = computed(() => route.path === '/login')

onMounted(() => initAuth())
</script>

<style>
.admin-app {
  background: linear-gradient(135deg, #0a0f1e 0%, #0d1325 50%, #0f172a 100%);
}
.admin-login-shell {
  background: transparent !important;
}
</style>
