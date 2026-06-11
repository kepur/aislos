export default defineNuxtPlugin(async () => {
  const appStore = useAppStore()
  const language = useCookie<string | null>('pp_language')
  const currency = useCookie<string | null>('pp_currency')

  if (language.value) appStore.setLanguage(language.value)
  await appStore.fetchPaymentRegionConfig('PH')
  if (currency.value) appStore.setCurrency(currency.value)
})
