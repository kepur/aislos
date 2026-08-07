<template>
  <div class="relative min-h-screen">
    <ClientOnly>
      <LazyGlobal3DBackground v-if="isDark" />
    </ClientOnly>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
const { initAuth } = useAuth()
const { loadAccess } = usePortalManifest()
const { theme, isDark } = useTheme()
await useAinerwiseSeo()
// Two classes: `dark`/`light` drives the shared surface baseline, while the
// theme key lets the KNX palette override on top without touching the other
// two themes' rules.
useHead({
  htmlAttrs: {
    class: computed(() => `${isDark.value ? 'dark' : 'light'} theme-${theme.value}`),
  },
})
onMounted(async () => {
  await initAuth()
  await loadAccess()
})
</script>
