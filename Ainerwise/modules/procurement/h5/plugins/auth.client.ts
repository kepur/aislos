export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore();
  authStore.hydrate();
  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchMe();
  }
});
