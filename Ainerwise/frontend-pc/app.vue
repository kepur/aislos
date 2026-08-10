<template>
  <div class="relative min-h-screen">
    <ClientOnly>
      <!-- Each theme gets its own scene rather than only dark having one:
           dark keeps the particle network, knx gets a floor plan with signal
           pulses, light gets drifting wireframe solids. -->
      <LazyGlobal3DBackground v-if="theme === 'dark'" />
      <LazyKnxGridBackground v-else-if="theme === 'knx'" />
      <LazyLightPrismBackground v-else />
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
