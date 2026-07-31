<template>
  <div class="min-h-dvh bg-amber-50/50">
    <ClientOnly><MobileHeader /></ClientOnly>
    <main class="pb-20"><slot /></main>
    <ClientOnly><BottomNav /></ClientOnly>
  </div>
</template>

