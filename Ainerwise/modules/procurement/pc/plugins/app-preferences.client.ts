export default defineNuxtPlugin(() => {
  const appStore = useAppStore()

  appStore.hydrate()
  appStore.fetchMarketLocalizationConfig()
  appStore.$subscribe(() => {
    appStore.persist()
    appStore.applyDocumentLocale()
  })
})
