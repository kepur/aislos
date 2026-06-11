export default defineNuxtRouteMiddleware((to) => {
  const { isLoggedIn, isAdmin } = useAuth()

  if (isLoggedIn.value) {
    if (isAdmin.value) {
      return navigateTo('/admin')
    }
    return navigateTo('/portal')
  }
})
