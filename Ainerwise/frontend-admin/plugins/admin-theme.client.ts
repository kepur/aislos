export default defineNuxtPlugin(() => {
  const { initTheme } = useAdminTheme()
  initTheme()
})
