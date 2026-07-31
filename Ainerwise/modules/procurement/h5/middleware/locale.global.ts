import {
  H5_LOCALE_TO_URI_PREFIX,
  getLocalePrefixFromPath,
  localeFromPrefix,
  normalizeH5Locale,
  withLocalePrefix,
} from "~/utils/localeRoutes";
import { setLocale } from "~/plugins/i18n";

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
    const savedPrefix = localStorage.getItem("h5_locale_prefix") || "";
    if (savedPrefix) return navigateTo(withLocalePrefix(to.fullPath, savedPrefix), { replace: true });
  }
});
