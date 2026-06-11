import { createI18n } from "vue-i18n";
import en from "~/locales/en.json";
import zh from "~/locales/zh.json";
import tl from "~/locales/tl.json";
import ja from "~/locales/ja.json";
import ko from "~/locales/ko.json";
import es from "~/locales/es.json";
import th from "~/locales/th.json";
import vi from "~/locales/vi.json";
import id from "~/locales/id.json";
import ar from "~/locales/ar.json";

export const SUPPORTED_LOCALES = [
  { code: "en", name: "English" },
  { code: "zh", name: "中文" },
  { code: "tl", name: "Tagalog" },
  { code: "ja", name: "日本語" },
  { code: "ko", name: "한국어" },
  { code: "es", name: "Español" },
  { code: "th", name: "ไทย" },
  { code: "vi", name: "Tiếng Việt" },
  { code: "id", name: "Bahasa Indonesia" },
  { code: "ar", name: "العربية" },
];

const RTL_LOCALES = ["ar"];
const LOCALE_CODES = new Set(SUPPORTED_LOCALES.map((locale) => locale.code));
const PC_TO_H5_LOCALE: Record<string, string> = {
  EN: "en",
  ZH: "zh",
  TL: "tl",
  JA: "ja",
  KO: "ko",
  ES: "es",
  TH: "th",
  VI: "vi",
  ID: "id",
  AR: "ar",
};
const H5_TO_PC_LOCALE: Record<string, string> = Object.fromEntries(
  Object.entries(PC_TO_H5_LOCALE).map(([pc, h5]) => [h5, pc])
);
let globalLocaleRef: { value: string } | null = null;

function normalizeLocale(value?: string | null) {
  if (!value) return "en";
  const fromPc = PC_TO_H5_LOCALE[value.toUpperCase()];
  const normalized = fromPc || value.toLowerCase();
  return LOCALE_CODES.has(normalized) ? normalized : "en";
}

function applyLocale(lang: string) {
  const normalized = normalizeLocale(lang);
  if (globalLocaleRef) {
    globalLocaleRef.value = normalized;
  }
  if (import.meta.client) {
    localStorage.setItem("h5_locale", normalized);
    localStorage.setItem("pp_language", H5_TO_PC_LOCALE[normalized] || "EN");
    document.cookie = `pp_language=${H5_TO_PC_LOCALE[normalized] || "EN"}; path=/; max-age=31536000`;
    document.documentElement.dir = RTL_LOCALES.includes(normalized) ? "rtl" : "ltr";
    document.documentElement.lang = normalized;
  }
}

export default defineNuxtPlugin((nuxtApp) => {
  let savedLocale = "en";
  if (import.meta.client) {
    savedLocale = normalizeLocale(localStorage.getItem("h5_locale") || localStorage.getItem("pp_language"));
  }

  const i18n = createI18n({
    legacy: false,
    globalInjection: true,
    locale: savedLocale,
    fallbackLocale: "en",
    messages: { en, zh, tl, ja, ko, es, th, vi, id, ar },
  });
  globalLocaleRef = i18n.global.locale as unknown as { value: string };

  if (import.meta.client) {
    applyLocale(savedLocale);
    window.addEventListener("storage", (event) => {
      if (event.key === "pp_language" || event.key === "h5_locale") {
        applyLocale(event.newValue || "en");
      }
    });
  }

  nuxtApp.vueApp.use(i18n);
});

export function setLocale(lang: string) {
  applyLocale(lang);
}
