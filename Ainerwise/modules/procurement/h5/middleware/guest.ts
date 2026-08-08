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

  const pathTo = (path: string) => {
    const prefix =
      getLocalePrefixFromPath(to.path) ||
      (import.meta.client ? localStorage.getItem("h5_locale_prefix") || "" : "");
    return prefix ? withLocalePrefix(path, prefix) : path;
  };

  if (authStore.isLoggedIn) {
    if (authStore.isBuyer) return navigateTo(pathTo("/buyer/home"));
    if (authStore.isSupplier) return navigateTo(pathTo("/supplier/pings"));
    if (authStore.isAdmin) return navigateTo(pathTo("/admin/dashboard"));
  }
});
