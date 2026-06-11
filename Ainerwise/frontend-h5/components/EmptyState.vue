<template>
  <div class="text-center py-10 text-slate-400">
    <div class="text-2xl mb-2">📭</div>
    <p class="text-xs">{{ text }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ text: string }>()
</script>
