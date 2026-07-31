const SHELL_CACHE = 'field-worker-v2'
const API_CACHE = 'field-worker-api-v2'
const SHELL = ['/field/today', '/manifest.webmanifest']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL).catch(() => undefined)),
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => ![SHELL_CACHE, API_CACHE].includes(k)).map((k) => caches.delete(k))),
    ).then(() => self.clients.claim()),
  )
})

function isFieldApi(url) {
  return url.pathname.startsWith('/api/v1/field/')
}

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  if (event.request.method === 'GET' && isFieldApi(url)) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone()
            caches.open(API_CACHE).then((cache) => cache.put(event.request, copy))
          }
          return response
        })
        .catch(() => caches.match(event.request).then((cached) => cached || Response.error())),
    )
    return
  }

  if (event.request.method !== 'GET' || !url.pathname.startsWith('/field')) return

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request).then((response) => {
        const copy = response.clone()
        caches.open(SHELL_CACHE).then((cache) => cache.put(event.request, copy))
        return response
      })
      return cached || network
    }),
  )
})
