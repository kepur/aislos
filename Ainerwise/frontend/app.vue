<template>
  <div class="relative min-h-screen">
    <!-- 3D Background only for public pages (default layout) -->
    <Global3DBackground v-if="showBackground" />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()

const showBackground = computed(() => {
  const path = route.path
  // Hide 3D background for admin and portal layouts
  return !path.startsWith('/admin') && !path.startsWith('/portal')
})
</script>
