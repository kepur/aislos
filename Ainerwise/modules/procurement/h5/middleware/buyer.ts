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

  if (!authStore.isLoggedIn) return navigateTo(pathTo("/auth/login"));
  if (!authStore.isBuyer) return navigateTo(pathTo("/"));
});
