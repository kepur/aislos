<template>
  <div class="px-4 py-4 space-y-4">
    <h1 class="text-lg font-bold text-slate-800">{{ $t('home.servicesTitle') }}</h1>
    <p class="text-xs text-slate-400">{{ $t('home.servicesSubtitle') }}</p>

    <div class="bg-blue-50 rounded-2xl p-4 border border-blue-100">
      <p class="text-[10px] font-semibold uppercase tracking-wider text-blue-500">{{ $t('services.defaultKicker') }}</p>
      <h2 class="mt-1 text-base font-bold text-blue-900">{{ $t('services.defaultTitle') }}</h2>
      <p class="mt-2 text-xs leading-5 text-blue-800/75">{{ $t('services.defaultText') }}</p>
      <p class="mt-2 text-xs font-medium text-amber-700">{{ $t('services.onSiteNotice') }}</p>
    </div>

    <div class="space-y-3">
      <div v-for="pkg in packages" :key="pkg.name"
        class="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-slate-800">{{ packageName(pkg) }}</h3>
          <span class="text-xs font-medium text-blue-500 bg-blue-50 px-2 py-0.5 rounded-full">{{ packageTerm(pkg) }}</span>
        </div>
        <p class="text-xs text-slate-400">{{ packageDescription(pkg) }}</p>
        <div class="mt-3 flex flex-wrap gap-1">
          <span v-for="f in packageServices(pkg)" :key="f" class="text-[10px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded">{{ f }}</span>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm space-y-3">
      <div>
        <h3 class="text-xs font-semibold text-slate-700">{{ $t('services.boundaryWarrantyTitle') }}</h3>
        <p class="mt-1 text-xs leading-5 text-slate-400">{{ $t('services.boundaryWarrantyText') }}</p>
      </div>
      <div>
        <h3 class="text-xs font-semibold text-slate-700">{{ $t('services.boundaryOnSiteTitle') }}</h3>
        <p class="mt-1 text-xs leading-5 text-slate-400">{{ $t('services.boundaryOnSiteText') }}</p>
      </div>
      <div>
        <h3 class="text-xs font-semibold text-slate-700">{{ $t('services.boundarySparesTitle') }}</h3>
        <p class="mt-1 text-xs leading-5 text-slate-400">{{ $t('services.boundarySparesText') }}</p>
      </div>
    </div>

    <div class="bg-blue-50 rounded-2xl p-5 text-center border border-blue-100">
      <h3 class="text-sm font-bold text-blue-800">Need a custom service plan?</h3>
      <NuxtLink to="/contact" class="inline-block mt-3 text-xs font-semibold bg-blue-500 text-white px-6 py-2 rounded-full">
        Contact Us
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t, te, tm, rt } = useI18n()
const { demoServicePackages } = useDemoCatalog()
const packages = demoServicePackages

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
</script>
