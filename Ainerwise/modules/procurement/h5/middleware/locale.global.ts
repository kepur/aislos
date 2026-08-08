import {
  H5_LOCALE_TO_URI_PREFIX,
  getLocalePrefixFromPath,
  localeFromPrefix,
  normalizeH5Locale,
  withLocalePrefix,
} from "~/utils/localeRoutes";
import { setLocale } from "~/plugins/i18n";

function readCookie(name: string) {
  if (!import.meta.client) return "";
  const found = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${name}=`));
  return found ? decodeURIComponent(found.slice(name.length + 1)) : "";
}

function supportedPrefixForLocale(locale: string) {
  return H5_LOCALE_TO_URI_PREFIX[normalizeH5Locale(locale)] || "";
}

function preferredClientPrefix() {
  if (!import.meta.client) return "";

  const savedPrefix = localStorage.getItem("h5_locale_prefix") || "";
  if (savedPrefix && localeFromPrefix(savedPrefix)) return savedPrefix;

  const savedLocale = supportedPrefixForLocale(
    localStorage.getItem("h5_locale") ||
      localStorage.getItem("pp_language") ||
      readCookie("pp_language")
  );
  if (savedLocale) return savedLocale;

  const browserLanguages = navigator.languages?.length
    ? navigator.languages
    : [navigator.language || ""];
  for (const browserLanguage of browserLanguages) {
    const browserPrefix = supportedPrefixForLocale(browserLanguage);
    if (browserPrefix) return browserPrefix;
  }

  return H5_LOCALE_TO_URI_PREFIX.en;
}

export default defineNuxtRouteMiddleware((to) => {
  const prefix = getLocalePrefixFromPath(to.path);
  if (prefix) {
    setLocale(localeFromPrefix(prefix));
    if (import.meta.client) localStorage.setItem("h5_locale_prefix", prefix);
    return;
  }

  const requested = normalizeH5Locale(String(to.query.lang || ""));
  if (requested) {
    setLocale(requested);
    const targetPrefix = H5_LOCALE_TO_URI_PREFIX[requested];
    if (targetPrefix) return navigateTo(withLocalePrefix(to.fullPath, targetPrefix), { replace: true });
    return;
  }

  if (import.meta.client) {
    const targetPrefix = preferredClientPrefix();
    if (targetPrefix) {
      setLocale(localeFromPrefix(targetPrefix));
      localStorage.setItem("h5_locale_prefix", targetPrefix);
      return navigateTo(withLocalePrefix(to.fullPath, targetPrefix), { replace: true });
    }
  }
});
