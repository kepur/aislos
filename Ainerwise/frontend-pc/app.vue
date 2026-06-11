<template>
  <div class="relative min-h-screen">
    <Global3DBackground />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
const { initAuth } = useAuth()
onMounted(() => initAuth())
</script>
