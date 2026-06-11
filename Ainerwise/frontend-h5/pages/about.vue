<template>
  <div class="px-4 py-4 space-y-4">
    <h1 class="text-lg font-bold text-slate-800">{{ $t('about.title') }}</h1>

    <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm space-y-4 text-sm text-slate-600 leading-relaxed">
      <p>{{ $t('about.p1') }}</p>
      <p>{{ $t('about.p2') }}</p>

      <h2 class="text-base font-bold text-slate-800 pt-2">{{ $t('about.approachTitle') }}</h2>
      <p>{{ $t('about.approachText') }}</p>

      <h2 class="text-base font-bold text-slate-800 pt-2">{{ $t('about.techTitle') }}</h2>
      <ul class="list-disc pl-5 space-y-1 text-slate-500">
        <li>{{ $t('about.tech1') }}</li>
        <li>{{ $t('about.tech2') }}</li>
        <li>{{ $t('about.tech3') }}</li>
        <li>{{ $t('about.tech4') }}</li>
      </ul>

    </div>

    <!-- Contact CTA -->
    <div class="bg-blue-50 rounded-2xl p-5 text-center border border-blue-100">
      <h3 class="text-sm font-bold text-blue-800">Get in Touch</h3>
      <p class="text-xs text-blue-600/70 mt-1">We're based in Belgrade, Serbia</p>
      <NuxtLink to="/contact" class="inline-block mt-3 text-xs font-semibold bg-blue-500 text-white px-6 py-2 rounded-full">
        Contact Us
      </NuxtLink>
    </div>
  </div>
</template>
