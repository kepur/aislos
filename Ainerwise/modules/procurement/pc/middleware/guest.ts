export default defineNuxtRouteMiddleware(() => {
  if (import.meta.server) return;

  const authStore = useAuthStore();
  if (authStore.isLoggedIn) {
    if (authStore.isBuyer) return navigateTo("/buyer/dashboard");
    if (authStore.isSupplier) return navigateTo("/supplier/dashboard");
    if (authStore.isAdmin) return navigateTo("/admin/dashboard");
  }
});
