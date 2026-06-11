import { useAuthStore } from '~/stores/auth'

export default defineNuxtPlugin(async (nuxtApp) => {
  const authStore = useAuthStore()
  authStore.hydrate()
  if (authStore.accessToken) {
    await authStore.fetchMe()
  }
})
