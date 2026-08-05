export default defineNuxtPlugin(async () => {
  const appStore = useAppStore();
  appStore.hydrate();
  await appStore.fetchMarketLocalizationConfig();
  await appStore.fetchPaymentRegionConfig(appStore.regionCountry || "RS");
});
