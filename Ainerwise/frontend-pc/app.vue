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
const { isDark } = useTheme()
useHead({ htmlAttrs: { class: computed(() => (isDark.value ? 'dark' : 'light')) } })
onMounted(async () => {
  await initAuth()
  await loadAccess()
})
</script>
