<template>
  <div class="mobile-layout">
    <ClientOnly>
      <MobileHeader />
    </ClientOnly>
    <main class="mobile-content">
      <slot />
    </main>
    <ClientOnly>
      <BottomNav />
    </ClientOnly>
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
