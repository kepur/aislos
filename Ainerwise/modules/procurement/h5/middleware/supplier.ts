export default defineNuxtRouteMiddleware(async () => {
  if (import.meta.server) return;

  const authStore = useAuthStore();

  if (!authStore.accessToken) {
    authStore.hydrate();
  }

  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchMe();
  }

  if (!authStore.isLoggedIn) return navigateTo("/auth/login");
  if (!authStore.isSupplier) return navigateTo("/");
});
