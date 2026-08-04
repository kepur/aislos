import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import i18n, { applyDirection } from '@/i18n'
import {
  ADMIN_LOCALE_PREFIXES,
  applyRouteLocale,
  currentLocalePrefix,
  getLocalePrefixFromPath,
  stripLocalePrefix,
  withLocalePrefix,
} from '@/utils/localeRoutes'

const routes = [
  { path: '/login',         component: () => import('@/pages/Login.vue'),         meta: { public: true } },
  { path: '/',              redirect: (to) => withLocalePrefix('/dashboard', getLocalePrefixFromPath(to.path) || currentLocalePrefix(to.path)) },
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
  { path: '/syndication',   component: () => import('@/pages/Syndication.vue') },
  { path: '/analytics',     component: () => import('@/pages/Analytics.vue') },
  { path: '/:pathMatch(.*)*', redirect: (to) => withLocalePrefix('/dashboard', getLocalePrefixFromPath(to.path) || currentLocalePrefix(to.path)) },
]

function localeAliases(path) {
  const cleanPath = path === '/' ? '' : path
  return ADMIN_LOCALE_PREFIXES.map(prefix => `/${prefix}${cleanPath}`)
}

function withAliases(route) {
  if (route.path.includes(':pathMatch')) return route
  return {
    ...route,
    alias: Array.from(new Set([...(route.alias || []), ...localeAliases(route.path)])),
  }
}

const router = createRouter({ history: createWebHistory(), routes: routes.map(withAliases) })

router.beforeEach(async (to) => {
  const prefix = applyRouteLocale(to.path, i18n.global.locale, applyDirection) || currentLocalePrefix(to.path)
  const cleanPath = stripLocalePrefix(to.path)
  if (to.query.lang) return withLocalePrefix(cleanPath, prefix)
  if (to.meta.public) return true
  const auth = useAuthStore()
  if (!auth.token) return withLocalePrefix('/login', prefix)
  if (!auth.user) {
    try { await auth.fetchMe() } catch { return withLocalePrefix('/login', prefix) }
  }
  return true
})

export default router
