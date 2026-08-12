<template>
  <footer class="bg-slate-900/60 backdrop-blur-md border-t border-white/10 text-slate-300">
    <div class="container-main px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <span class="text-xl font-bold text-white">AinerWise</span>
          <p class="mt-3 text-sm text-gray-400">{{ $t('footer.tagline') }}</p>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-white uppercase tracking-wider">{{ $t('footer.solutions') }}</h3>
          <ul class="mt-3 space-y-2">
            <li><NuxtLink :to="localized('/solutions/smart-hotel')" class="text-sm hover:text-white">{{ $t('footer.smartHotel') }}</NuxtLink></li>
            <li><NuxtLink :to="localized('/solutions/smart-villa')" class="text-sm hover:text-white">{{ $t('footer.smartVilla') }}</NuxtLink></li>
            <li><NuxtLink :to="localized('/solutions/cctv-access-control')" class="text-sm hover:text-white">{{ $t('footer.cctvAccess') }}</NuxtLink></li>
            <li><NuxtLink :to="localized('/solutions/knx-lighting')" class="text-sm hover:text-white">{{ $t('footer.knxLighting') }}</NuxtLink></li>
            <li><NuxtLink :to="localized('/solutions/solar-energy-monitoring')" class="text-sm hover:text-white">{{ $t('footer.solarEnergy') }}</NuxtLink></li>
          </ul>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-white uppercase tracking-wider">{{ $t('footer.company') }}</h3>
          <ul class="mt-3 space-y-2">
            <li><NuxtLink :to="localized('/about')" class="text-sm hover:text-white">{{ $t('footer.about') }}</NuxtLink></li>
            <li><NuxtLink :to="localized('/supplier-application')" class="text-sm hover:text-white">{{ $t('nav.supplierApplication') }}</NuxtLink></li>
            <li><NuxtLink :to="localized('/contact')" class="text-sm hover:text-white">{{ $t('footer.contact') }}</NuxtLink></li>
          </ul>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-white uppercase tracking-wider">{{ $t('footer.contact') }}</h3>
          <ul class="mt-3 space-y-2">
            <li class="text-sm">{{ $t('mktP.belgrade') }}</li>
            <li class="text-sm">info@ainerwise.com</li>
          </ul>
        </div>
      </div>
      <div class="mt-8 pt-8 border-t border-gray-800 text-center">
        <p class="text-sm text-gray-500">&copy; {{ new Date().getFullYear() }} {{ $t('footer.copyright') }}</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
</script>

