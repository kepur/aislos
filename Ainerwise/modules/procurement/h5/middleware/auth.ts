import { getLocalePrefixFromPath, withLocalePrefix } from "~/utils/localeRoutes";

export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return;

  const authStore = useAuthStore();

  if (!authStore.accessToken) {
    authStore.hydrate();
  }

  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchMe();
  }

  if (!authStore.isLoggedIn) {
    const prefix =
      getLocalePrefixFromPath(to.path) ||
      (import.meta.client ? localStorage.getItem("h5_locale_prefix") || "" : "");
    const loginPath = `/auth/login?redirect=${encodeURIComponent(to.fullPath)}`;
    return navigateTo(prefix ? withLocalePrefix(loginPath, prefix) : loginPath);
  }
});
