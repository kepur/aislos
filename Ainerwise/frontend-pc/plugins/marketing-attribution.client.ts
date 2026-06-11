export default defineNuxtPlugin(() => {
  const { captureAttribution } = useMarketingAttribution()
  captureAttribution()
})
