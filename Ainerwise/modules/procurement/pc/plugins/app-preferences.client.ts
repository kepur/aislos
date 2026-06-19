export default defineNuxtPlugin(() => {
  const appStore = useAppStore()

  appStore.hydrate()
  appStore.$subscribe(() => {
    appStore.persist()
    appStore.applyDocumentLocale()
  })
})
