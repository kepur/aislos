export default defineNuxtPlugin(async () => {
  const appStore = useAppStore()
  const language = useCookie<string | null>('pp_language')
  const currency = useCookie<string | null>('pp_currency')
  const regionCountry = useCookie<string | null>('pp_region_country')

  if (language.value) appStore.setLanguage(language.value)
  if (regionCountry.value) appStore.regionCountry = String(regionCountry.value).toUpperCase().slice(0, 2)
  await appStore.fetchMarketLocalizationConfig()
  await appStore.fetchPaymentRegionConfig(appStore.regionCountry || 'RS')
  if (currency.value) appStore.setCurrency(currency.value)
})
