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
    return navigateTo(`/login?redirect=${encodeURIComponent(to.path)}`);
  }
});
