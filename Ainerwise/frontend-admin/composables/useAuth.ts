import { createSharedAuth } from '@ainerwise/shared-auth'

const ADMIN_WORKBENCH_ROLES = new Set([
  'super_admin',
  'admin',
  'sales_manager',
  'project_manager',
  'finance',
  'marketing_operator',
])

export function useAuth() {
  return createSharedAuth({
    apiBase: useApiBase(),
    adminRoles: ADMIN_WORKBENCH_ROLES,
    logoutRedirect: '/login',
  })
}
