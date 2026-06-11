<template>
  <div class="h5-app">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { initAuth, user } = useAuth()
const { mode } = usePortalMode()

const partnerRoles = ['service_partner', 'partner_worker', 'maintenance_worker']
const customerRoles = ['buyer', 'customer_user']
const customerProtectedPrefixes = ['/dashboard', '/projects', '/profile']

function enforcePortalRole() {
  if (!user.value || route.path === '/access-denied' || route.path === '/login') return
  const role = user.value.role
  const customerProtected = customerProtectedPrefixes.some(prefix =>
    route.path === prefix || route.path.startsWith(`${prefix}/`))
  const denied = mode === 'partner'
    ? !partnerRoles.includes(role)
    : customerProtected && !customerRoles.includes(role)
  if (denied) navigateTo('/access-denied')
}

onMounted(async () => {
  await initAuth()
  enforcePortalRole()
})

watch([user, () => route.path], enforcePortalRole)

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover' },
    { name: 'apple-mobile-web-app-capable', content: 'yes' },
    { name: 'apple-mobile-web-app-status-bar-style', content: 'default' },
    { name: 'theme-color', content: '#ffffff' },
  ],
})
</script>

<style>
html, body {
  overscroll-behavior-y: none;
  -webkit-tap-highlight-color: transparent;
}
.h5-app {
  min-height: 100dvh;
  background: #f5f7fa;
}
/* Safe area support for bottom nav */
@supports (padding-bottom: env(safe-area-inset-bottom)) {
  .safe-bottom {
    padding-bottom: env(safe-area-inset-bottom);
  }
}
</style>
