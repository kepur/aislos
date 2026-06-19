import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login',         component: () => import('@/pages/Login.vue'),         meta: { public: true } },
  { path: '/',              redirect: '/dashboard' },
  { path: '/dashboard',     component: () => import('@/pages/Dashboard.vue') },
  { path: '/users',         component: () => import('@/pages/Users.vue') },
  { path: '/staff',         component: () => import('@/pages/Staff.vue') },
  { path: '/companies',     component: () => import('@/pages/Companies.vue') },
  { path: '/verification',  component: () => import('@/pages/Verification.vue') },
  { path: '/kyc-media',     component: () => import('@/pages/KYCMedia.vue') },
  { path: '/intents',       component: () => import('@/pages/Intents.vue') },
  { path: '/orders',        component: () => import('@/pages/Orders.vue') },
  { path: '/disputes',      component: () => import('@/pages/Disputes.vue') },
  { path: '/escrow',        component: () => import('@/pages/Escrow.vue') },
  { path: '/payments',      component: () => import('@/pages/Payments.vue') },
  { path: '/shipping',      component: () => import('@/pages/Shipping.vue') },
  { path: '/regions',       component: () => import('@/pages/Regions.vue') },
  { path: '/risk',          component: () => import('@/pages/Risk.vue') },
  { path: '/trust',         component: () => import('@/pages/Trust.vue') },
  { path: '/notifications', component: () => import('@/pages/Notifications.vue') },
  { path: '/integrations',  component: () => import('@/pages/Integrations.vue') },
  { path: '/backups',       component: () => import('@/pages/Backups.vue') },
  { path: '/settings',      component: () => import('@/pages/Settings.vue') },
  { path: '/audit',         component: () => import('@/pages/Audit.vue') },
  { path: '/marketplace',   component: () => import('@/pages/Marketplace.vue') },
  { path: '/ad-campaigns',  component: () => import('@/pages/AdCampaigns.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const auth = useAuthStore()
  if (!auth.token) return '/login'
  if (!auth.user) {
    try { await auth.fetchMe() } catch { return '/login' }
  }
  return true
})

export default router
