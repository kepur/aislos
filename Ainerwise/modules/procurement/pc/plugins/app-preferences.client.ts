export default defineNuxtPlugin(() => {
  const appStore = useAppStore()

  appStore.hydrate()
  appStore.fetchMarketLocalizationConfig()
  appStore.fetchPaymentRegionConfig(appStore.regionCountry || 'RS')
  appStore.$subscribe(() => {
    appStore.persist()
    appStore.applyDocumentLocale()
  })
})
