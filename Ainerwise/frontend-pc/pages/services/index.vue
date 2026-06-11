<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('services.title') }}</h1>
        <p class="mt-3 text-slate-300">{{ $t('services.subtitle') }}</p>
      </div>

      <div class="glass-panel p-6 sm:p-8 mb-8 border-primary-500/40 shadow-[0_0_24px_rgba(14,165,233,0.12)]">
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-primary-400">{{ $t('services.defaultKicker') }}</p>
        <h2 class="mt-2 text-2xl font-semibold text-white">{{ $t('services.defaultTitle') }}</h2>
        <p class="mt-3 max-w-4xl text-sm leading-6 text-slate-300">{{ $t('services.defaultText') }}</p>
        <p class="mt-4 text-sm font-medium text-amber-300">{{ $t('services.onSiteNotice') }}</p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="pkg in packages" :key="pkg.id" class="glass-panel p-6 transition border-primary-500/30 hover:border-primary-500/50 hover:shadow-[0_0_15px_rgba(14,165,233,0.3)]">
          <h2 class="text-xl font-semibold text-white">{{ packageName(pkg) }}</h2>
          <p class="text-primary-400 font-medium mt-1">{{ packageTerm(pkg) }}</p>
          <p class="mt-3 text-sm text-slate-300">{{ packageDescription(pkg) }}</p>
          <div v-if="pkg.included_services_json" class="mt-4 border-t border-white/10 pt-4">
            <h3 class="text-sm font-medium text-slate-400 mb-2">{{ $t('services.included') }}</h3>
            <ul class="space-y-1">
              <li v-for="s in packageServices(pkg)" :key="s" class="text-sm text-slate-300 flex items-start gap-2">
                <span class="text-emerald-400">&#10003;</span> {{ s }}
              </li>
            </ul>
          </div>
          <NuxtLink to="/submit-requirement" class="mt-6 btn-primary block text-center text-sm shadow-[0_0_15px_rgba(14,165,233,0.3)]">{{ $t('services.getQuote') }}</NuxtLink>
        </div>
      </div>

      <div class="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="glass-panel p-5 border-white/10">
          <h3 class="font-semibold text-white">{{ $t('services.boundaryWarrantyTitle') }}</h3>
          <p class="mt-2 text-sm leading-6 text-slate-300">{{ $t('services.boundaryWarrantyText') }}</p>
        </div>
        <div class="glass-panel p-5 border-white/10">
          <h3 class="font-semibold text-white">{{ $t('services.boundaryOnSiteTitle') }}</h3>
          <p class="mt-2 text-sm leading-6 text-slate-300">{{ $t('services.boundaryOnSiteText') }}</p>
        </div>
        <div class="glass-panel p-5 border-white/10">
          <h3 class="font-semibold text-white">{{ $t('services.boundarySparesTitle') }}</h3>
          <p class="mt-2 text-sm leading-6 text-slate-300">{{ $t('services.boundarySparesText') }}</p>
        </div>
      </div>

      <p class="mt-6 text-xs leading-5 text-slate-500">{{ $t('services.contractNote') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const { t, te, tm, rt } = useI18n()
const { demoServicePackages } = useDemoCatalog()
const packages = ref<any[]>(demoServicePackages)

function packageTerm(pkg: any) {
  const key = `services.packages.${pkg.slug}.term`
  return te(key) ? t(key) : pkg.price_rule_json?.term_label || `${pkg.years} ${t('services.years')}`
}

function packageName(pkg: any) {
  const key = `services.packages.${pkg.slug}.name`
  return te(key) ? t(key) : pkg.name
}

function packageDescription(pkg: any) {
  const key = `services.packages.${pkg.slug}.description`
  return te(key) ? t(key) : pkg.description
}

function packageServices(pkg: any) {
  const key = `services.packages.${pkg.slug}.included`
  return te(`services.packages.${pkg.slug}.name`) ? (tm(key) as any[]).map(service => rt(service)) : pkg.included_services_json
}

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/service-packages')
    packages.value = res.items || res || []
  } catch {}

  if (!packages.value.length) {
    packages.value = demoServicePackages
  }
})
</script>
