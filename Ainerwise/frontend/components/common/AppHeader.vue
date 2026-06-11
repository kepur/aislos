<template>
  <header class="bg-slate-900/60 backdrop-blur-md border-b border-white/10 sticky top-0 z-50">
    <div class="container-main flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
      <NuxtLink to="/" class="flex items-center gap-2">
        <span class="text-xl font-bold text-primary-400 drop-shadow-[0_0_8px_rgba(14,165,233,0.5)]">AinerWise</span>
      </NuxtLink>

      <!-- Desktop Nav -->
      <nav class="hidden md:flex items-center gap-6">
        <NuxtLink to="/solutions" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ $t('nav.solutions') }}</NuxtLink>
        <NuxtLink to="/ai-building-brain" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ $t('nav.aiBrain') }}</NuxtLink>
        <NuxtLink to="/products" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ $t('nav.products') }}</NuxtLink>
        <NuxtLink to="/services" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ $t('nav.services') }}</NuxtLink>
        <NuxtLink to="/about" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ $t('nav.about') }}</NuxtLink>
        <NuxtLink to="/contact" class="text-sm font-medium text-slate-300 hover:text-white transition">{{ $t('nav.contact') }}</NuxtLink>
      </nav>

      <div class="flex items-center gap-3">
        <LanguageSwitcher />
        
        <div class="hidden md:flex items-center gap-3">
          <template v-if="isLoggedIn">
            <NuxtLink :to="isAdmin ? '/admin' : '/portal'" class="text-sm font-medium text-primary-400 hover:text-primary-300">
              {{ $t('nav.dashboard') }}
            </NuxtLink>
            <button @click="logout" class="text-sm text-slate-400 hover:text-red-400">{{ $t('nav.logout') }}</button>
          </template>
          <template v-else>
            <NuxtLink to="/login" class="text-sm font-medium text-slate-300 hover:text-white">{{ $t('nav.login') }}</NuxtLink>
            <NuxtLink to="/submit-requirement" class="bg-primary-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-primary-500 transition shadow-[0_0_10px_rgba(14,165,233,0.3)]">{{ $t('nav.submitRequirement') }}</NuxtLink>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
const { isLoggedIn, isAdmin, logout } = useAuth()
</script>
