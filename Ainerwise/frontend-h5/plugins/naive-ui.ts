import { setup } from '@css-render/vue3-ssr'
import { defineNuxtPlugin } from '#app'

export default defineNuxtPlugin((nuxtApp) => {
  if (import.meta.server) {
    const { collect } = setup(nuxtApp.vueApp)
    nuxtApp.ssrContext!.head = nuxtApp.ssrContext!.head || []
    nuxtApp.hook('app:rendered', () => {
      const cssContent = collect()
      ;(nuxtApp.ssrContext!.head as any[]).push(cssContent)
    })
  }
})
