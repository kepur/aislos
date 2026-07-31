<template>
  <div class="min-h-dvh bg-gradient-to-b from-blue-50/70 to-slate-50">
    <ClientOnly><MobileHeader /></ClientOnly>
    <main class="pb-20"><slot /></main>
    <ClientOnly><BottomNav /></ClientOnly>
  </div>
</template>
