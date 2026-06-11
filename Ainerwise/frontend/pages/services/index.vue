<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('services.title') }}</h1>
        <p class="mt-3 text-slate-300">{{ $t('services.subtitle') }}</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="pkg in packages" :key="pkg.id" class="glass-panel p-6 transition border-primary-500/30 hover:border-primary-500/50 hover:shadow-[0_0_15px_rgba(14,165,233,0.3)]">
          <h2 class="text-xl font-semibold text-white">{{ pkg.name }}</h2>
          <p class="text-primary-400 font-medium mt-1">{{ pkg.years }} {{ $t('services.years') }}</p>
          <p class="mt-3 text-sm text-slate-300">{{ pkg.description }}</p>
          <div v-if="pkg.included_services_json" class="mt-4 border-t border-white/10 pt-4">
            <h3 class="text-sm font-medium text-slate-400 mb-2">{{ $t('services.included') }}</h3>
            <ul class="space-y-1">
              <li v-for="s in pkg.included_services_json" :key="s" class="text-sm text-slate-300 flex items-start gap-2">
                <span class="text-emerald-400">&#10003;</span> {{ s }}
              </li>
            </ul>
          </div>
          <NuxtLink to="/submit-requirement" class="mt-6 btn-primary block text-center text-sm shadow-[0_0_15px_rgba(14,165,233,0.3)]">{{ $t('services.getQuote') }}</NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const packages = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/service-packages')
    packages.value = res.items || res || []
  } catch {}
})
</script>
