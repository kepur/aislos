<template>
  <div class="min-h-screen flex flex-col pb-[72px] md:pb-0">
    <AppHeader />
    <main class="flex-1">
      <slot />
    </main>
    <AppFooter class="hidden md:block" />
    <MobileBottomNav />
  </div>
</template>
