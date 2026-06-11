export default defineNuxtRouteMiddleware(async () => {
  if (import.meta.server) return;

  const authStore = useAuthStore();

  if (!authStore.accessToken) {
    authStore.hydrate();
  }

  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchMe();
  }

  if (authStore.isLoggedIn) {
    if (authStore.isBuyer) return navigateTo("/buyer/home");
    if (authStore.isSupplier) return navigateTo("/supplier/pings");
    if (authStore.isAdmin) return navigateTo("/admin/dashboard");
  }
});
