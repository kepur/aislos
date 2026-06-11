<template>
  <div class="section-padding">
    <div class="container-main max-w-2xl">
      <h1 class="text-3xl font-bold text-white text-center drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('contact.title') }}</h1>
      <p class="mt-3 text-slate-300 text-center">{{ $t('contact.subtitle') }}</p>

      <div class="mt-10 glass-panel p-8 space-y-6 border-primary-500/30 shadow-[0_0_30px_rgba(14,165,233,0.1)]">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <h3 class="font-semibold text-white">{{ $t('contact.email') }}</h3>
            <p class="text-slate-400 mt-1">info@ainerwise.com</p>
          </div>
          <div>
            <h3 class="font-semibold text-white">{{ $t('contact.location') }}</h3>
            <p class="text-slate-400 mt-1">Belgrade, Serbia</p>
          </div>
          <div>
            <h3 class="font-semibold text-white">{{ $t('contact.telegram') }}</h3>
            <p class="text-slate-400 mt-1">@ainerwise</p>
          </div>
          <div>
            <h3 class="font-semibold text-white">{{ $t('contact.whatsapp') }}</h3>
            <p class="text-slate-400 mt-1">{{ $t('contact.whatsappNote') }}</p>
          </div>
        </div>

        <hr class="border-white/10" />

        <form @submit.prevent class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <input type="text" :placeholder="$t('contact.yourName')" class="input-field" />
            <input type="email" :placeholder="$t('contact.emailPlaceholder')" class="input-field" />
          </div>
          <input type="text" :placeholder="$t('contact.subject')" class="input-field" />
          <textarea rows="4" :placeholder="$t('contact.message')" class="input-field"></textarea>
          <button type="submit" class="btn-primary shadow-[0_0_15px_rgba(14,165,233,0.3)] w-full sm:w-auto">{{ $t('contact.send') }}</button>
        </form>
      </div>
    </div>
  </div>
</template>
