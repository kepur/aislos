<template>
  <div class="min-h-dvh bg-[#f4f2ff]">
    <ClientOnly>
      <MobileHeader />
    </ClientOnly>
    <main class="pb-20">
      <slot />
    </main>
    <ClientOnly>
      <BottomNav />
    </ClientOnly>
  </div>
</template>

