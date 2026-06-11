<template>
  <div class="mobile-layout">
    <MobileHeader />
    <main class="mobile-content">
      <slot />
    </main>
    <BottomNav />
  </div>
</template>

<style scoped>
.mobile-layout {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}
.mobile-content {
  flex: 1;
  padding-bottom: 72px; /* space for bottom nav + extra */
}
</style>
