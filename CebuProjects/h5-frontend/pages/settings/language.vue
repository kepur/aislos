<template>
  <div class="min-h-screen bg-slate-50">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-bold text-slate-900">{{ $t("common.language") }}</h1>
    </div>

    <div class="bg-white mx-4 mt-4 rounded-2xl shadow-card overflow-hidden">
      <button type="button"
        v-for="l in supportedLocales"
        :key="l.code"
        class="w-full px-4 py-4 flex items-center justify-between border-b border-slate-50 last:border-0 active:bg-slate-50"
        @click="select(l.code)"
      >
        <span class="text-slate-900 font-medium">{{ l.name }}</span>
        <svg v-if="locale === l.code" class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { SUPPORTED_LOCALES, setLocale } from "~/plugins/i18n";

definePageMeta({ layout: "default" });

const { locale } = useI18n({ useScope: "global" });
const supportedLocales = SUPPORTED_LOCALES;

function select(lang: string) {
  setLocale(lang);
}
</script>
