<template>
  <div>
    <NuxtLayout>
      <NuxtPage :key="route.fullPath" :page-key="route.fullPath" />
    </NuxtLayout>
    <UNotifications />
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
</script>
