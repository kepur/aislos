// Breadcrumb / page title — maps the current route to a translated admin label,
// falling back to a humanized slug for routes without a key.
const PAGE_KEY_BY_SLUG: Record<string, string> = {
  '': 'admin.dashboard',
  leads: 'admin.leads',
  projects: 'admin.projects',
  quotes: 'admin.quotes',
  proposals: 'admin.proposals',
  tickets: 'admin.tickets',
  inquiries: 'admin.inquiries',
  products: 'admin.products',
  categories: 'admin.categories',
  solutions: 'admin.solutions',
  'service-packages': 'admin.servicePackages',
  compatibility: 'admin.compatibility',
  'warranty-policies': 'admin.warrantyPolicies',
  'monitoring-points': 'admin.monitoringPoints',
  'amc-contracts': 'admin.amcContracts',
  'supplier-warranties': 'admin.supplierWarranties',
  'customer-warranties': 'admin.customerWarranties',
  inventory: 'admin.spareInventory',
  maintenance: 'admin.maintenance',
  calibration: 'admin.calibration',
  'lifecycle-dashboard': 'admin.lifecycleDashboard',
  'renewal-queue': 'admin.renewalQueue',
  'supplier-scorecards': 'admin.supplierScorecards',
  'project-finance': 'admin.projectFinance',
  'platform-fee-rules': 'admin.platformFeeRules',
  vendors: 'admin.vendors',
  'service-partners': 'admin.servicePartners',
  users: 'admin.users',
  companies: 'admin.companies',
  'ai-runs': 'admin.aiRuns',
  'integration-events': 'admin.events',
  certifications: 'admin.certifications',
  regions: 'admin.regions',
  'audit-logs': 'admin.auditLogs',
  settings: 'admin.settings',
}

export function usePageTitle() {
  const route = useRoute()
  const { t, te } = useI18n({ useScope: 'global' })

  return computed(() => {
    const slug = route.path.replace(/^\//, '').split('/')[0]
    const key = PAGE_KEY_BY_SLUG[slug]
    if (key && te(key)) return t(key)
    if (!slug) return t('admin.dashboard')
    return slug.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  })
}
