import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const coreApiTarget = process.env.VITE_CORE_API_PROXY || 'http://localhost:8000'

const coreProxy = (rewrite) => ({
  target: coreApiTarget,
  rewrite,
  changeOrigin: true
})

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },
  server: {
    port: 4108,
    proxy: {
      '/api/auth': coreProxy((p) => p.replace(/^\/api\/auth/, '/api/v1/auth')),
      '/api/users': coreProxy((p) => p.replace(/^\/api\/users/, '/api/v1/cebu-compat/users')),
      '/api/admin/shipping': coreProxy((p) =>
        p.replace(/^\/api\/admin\/shipping/, '/api/v1/admin/cebu-trade/shipping')
      ),
      '/api/admin/deposits': coreProxy((p) =>
        p.replace(/^\/api\/admin\/deposits/, '/api/v1/admin/cebu-trade/deposits')
      ),
      '/api/admin/payouts': coreProxy((p) =>
        p.replace(/^\/api\/admin\/payouts/, '/api/v1/admin/cebu-trade/payouts')
      ),
      '/api/admin/ad-campaigns': coreProxy((p) =>
        p.replace(/^\/api\/admin\/ad-campaigns/, '/api/v1/admin/cebu-trade/ads/campaigns')
      ),
      '/api/admin': coreProxy((p) => p.replace(/^\/api\/admin/, '/api/v1/admin/cebu')),
      '/api': coreProxy((p) => p.replace(/^\/api/, '/api/v1/cebu-compat'))
    }
  }
})
