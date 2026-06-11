<template>
  <div class="kiosk-layout">
    <slot />
  </div>
</template>

<style scoped>
.kiosk-layout {
  min-height: 100dvh;
  background: #0f172a;
  color: #f8fafc;
  overflow: hidden;
  user-select: none;
}
</style>
