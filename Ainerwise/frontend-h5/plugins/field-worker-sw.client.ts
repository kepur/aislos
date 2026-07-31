export default defineNuxtPlugin(() => {
  if (!import.meta.client || !('serviceWorker' in navigator)) return
  if (window.location.pathname.startsWith('/field') || window.location.pathname === '/field/today') {
    navigator.serviceWorker.register('/field-worker-sw.js').catch(() => {})
  }
})
