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
        p.replace(/^\/api\/admin\/shipping/, '/api/v1/cebu-compat/admin/shipping')
      ),
      '/api/admin/deposits': coreProxy((p) =>
        p.replace(/^\/api\/admin\/deposits/, '/api/v1/cebu-compat/admin/deposits')
      ),
      '/api/admin/payouts': coreProxy((p) =>
        p.replace(/^\/api\/admin\/payouts/, '/api/v1/cebu-compat/admin/payouts')
      ),
      '/api/admin/escrow': coreProxy((p) =>
        p.replace(/^\/api\/admin\/escrow/, '/api/v1/cebu-compat/admin/escrow')
      ),
      '/api/admin/payment-events': coreProxy((p) =>
        p.replace(/^\/api\/admin\/payment-events/, '/api/v1/cebu-compat/admin/payment-events')
      ),
      '/api/admin/settlement-events': coreProxy((p) =>
        p.replace(/^\/api\/admin\/settlement-events/, '/api/v1/cebu-compat/admin/settlement-events')
      ),
      '/api/admin/payment-region-configs': coreProxy((p) =>
        p.replace(/^\/api\/admin\/payment-region-configs/, '/api/v1/cebu-compat/admin/payment-region-configs')
      ),
      '/api/admin/regions': coreProxy((p) =>
        p.replace(/^\/api\/admin\/regions/, '/api/v1/cebu-compat/admin/regions')
      ),
      '/api/admin/trust': coreProxy((p) =>
        p.replace(/^\/api\/admin\/trust/, '/api/v1/cebu-compat/admin/trust')
      ),
      '/api/admin/backups/config': coreProxy((p) =>
        p.replace(/^\/api\/admin\/backups\/config/, '/api/v1/cebu-compat/admin/backups/config')
      ),
      '/api/admin/ai': coreProxy((p) =>
        p.replace(/^\/api\/admin\/ai/, '/api/v1/cebu-compat/admin/ai')
      ),
      '/api/admin/maps': coreProxy((p) =>
        p.replace(/^\/api\/admin\/maps/, '/api/v1/cebu-compat/admin/maps')
      ),
      '/api/admin/ad-campaigns': coreProxy((p) =>
        p.replace(/^\/api\/admin\/ad-campaigns/, '/api/v1/cebu-compat/admin/ad-campaigns')
      ),
      '/api/admin/intents': coreProxy((p) =>
        p.replace(/^\/api\/admin\/intents/, '/api/v1/cebu-compat/admin/intents')
      ),
      '/api/admin/offers': coreProxy((p) =>
        p.replace(/^\/api\/admin\/offers/, '/api/v1/cebu-compat/admin/offers')
      ),
      '/api/admin/disputes': coreProxy((p) =>
        p.replace(/^\/api\/admin\/disputes/, '/api/v1/cebu-compat/admin/disputes')
      ),
      '/api/admin/risk-flags': coreProxy((p) =>
        p.replace(/^\/api\/admin\/risk-flags/, '/api/v1/cebu-compat/admin/risk-flags')
      ),
      '/api/admin/verification': coreProxy((p) =>
        p.replace(/^\/api\/admin\/verification/, '/api/v1/cebu-compat/admin/verification')
      ),
      '/api/admin/kyc-media': coreProxy((p) =>
        p.replace(/^\/api\/admin\/kyc-media/, '/api/v1/cebu-compat/admin/kyc-media')
      ),
      '/api/admin/orders': coreProxy((p) =>
        p.replace(/^\/api\/admin\/orders/, '/api/v1/cebu-compat/admin/orders')
      ),
      '/api/admin/users': coreProxy((p) =>
        p.replace(/^\/api\/admin\/users/, '/api/v1/cebu-compat/admin/users')
      ),
      '/api/admin/staff': coreProxy((p) =>
        p.replace(/^\/api\/admin\/staff/, '/api/v1/cebu-compat/admin/staff')
      ),
      '/api/admin/companies': coreProxy((p) =>
        p.replace(/^\/api\/admin\/companies/, '/api/v1/cebu-compat/admin/companies')
      ),
      '/api/admin/settings': coreProxy((p) =>
        p.replace(/^\/api\/admin\/settings/, '/api/v1/cebu-compat/admin/settings')
      ),
      '/api/admin': coreProxy((p) => p.replace(/^\/api\/admin/, '/api/v1/admin/cebu')),
      '/api': coreProxy((p) => p.replace(/^\/api/, '/api/v1/cebu-compat'))
    }
  }
})
