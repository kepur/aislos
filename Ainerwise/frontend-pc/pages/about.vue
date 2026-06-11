<template>
  <div class="section-padding">
    <div class="container-main max-w-4xl">
      <h1 class="text-3xl font-bold text-white text-center drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('about.title') }}</h1>

      <div class="mt-10 glass-panel p-8 space-y-6 text-slate-300 leading-relaxed border-primary-500/30 shadow-[0_0_30px_rgba(14,165,233,0.1)]">
        <p>{{ $t('about.p1') }}</p>
        <p>{{ $t('about.p2') }}</p>

        <h2 class="text-xl font-bold text-white mt-8 mb-4 border-b border-white/10 pb-2">{{ $t('about.approachTitle') }}</h2>
        <p>{{ $t('about.approachText') }}</p>

        <h2 class="text-xl font-bold text-white mt-8 mb-4 border-b border-white/10 pb-2">{{ $t('about.techTitle') }}</h2>
        <ul class="list-disc pl-6 space-y-2 text-primary-200">
          <li>{{ $t('about.tech1') }}</li>
          <li>{{ $t('about.tech2') }}</li>
          <li>{{ $t('about.tech3') }}</li>
          <li>{{ $t('about.tech4') }}</li>
        </ul>

      </div>
    </div>
  </div>
</template>
