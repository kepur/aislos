<template>
  <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900/90 backdrop-blur-lg border-t border-white/10 flex items-center justify-around z-50 h-[72px] pb-safe shadow-[0_-5px_15px_rgba(0,0,0,0.3)]">
    <NuxtLink to="/" class="flex flex-col items-center justify-center w-full h-full text-slate-400 hover:text-primary-400 transition" exact-active-class="text-primary-400">
      <span class="text-2xl mb-1">🏠</span>
      <span class="text-[10px] font-medium">Home</span>
    </NuxtLink>
    <NuxtLink to="/solutions" class="flex flex-col items-center justify-center w-full h-full text-slate-400 hover:text-primary-400 transition" active-class="text-primary-400">
      <span class="text-2xl mb-1">💡</span>
      <span class="text-[10px] font-medium">{{ $t('nav.solutions') }}</span>
    </NuxtLink>
    <NuxtLink to="/submit-requirement" class="flex flex-col items-center justify-center w-full h-full text-slate-400 hover:text-primary-400 transition relative" active-class="text-primary-400">
      <div class="absolute -top-5 bg-primary-600 rounded-full w-12 h-12 flex items-center justify-center shadow-[0_0_15px_rgba(14,165,233,0.5)] border-4 border-slate-900">
        <span class="text-white text-xl">✨</span>
      </div>
      <span class="text-[10px] font-medium mt-6">AI Forge</span>
    </NuxtLink>
    <NuxtLink to="/products" class="flex flex-col items-center justify-center w-full h-full text-slate-400 hover:text-primary-400 transition" active-class="text-primary-400">
      <span class="text-2xl mb-1">📦</span>
      <span class="text-[10px] font-medium">{{ $t('nav.products') }}</span>
    </NuxtLink>
    <NuxtLink :to="isLoggedIn ? (isAdmin ? '/admin' : '/portal') : '/login'" class="flex flex-col items-center justify-center w-full h-full text-slate-400 hover:text-primary-400 transition" :class="{ 'text-primary-400': $route.path.startsWith('/admin') || $route.path.startsWith('/portal') || $route.path.startsWith('/login') }">
      <span class="text-2xl mb-1">👤</span>
      <span class="text-[10px] font-medium">{{ isLoggedIn ? $t('nav.dashboard') : $t('nav.login') }}</span>
    </NuxtLink>
  </nav>
</template>

<script setup lang="ts">
const { isLoggedIn, isAdmin } = useAuth()
</script>
