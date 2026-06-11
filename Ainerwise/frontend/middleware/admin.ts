export default defineNuxtRouteMiddleware((to) => {
  const { isLoggedIn, isAdmin } = useAuth()

  if (!isLoggedIn.value) {
    return navigateTo('/login')
  }

  if (!isAdmin.value) {
    return navigateTo('/')
  }
})
