export type PortalManifest = {
  portal_key: string
  version: number
  physical_frontend: 'pc' | 'h5' | 'admin'
  layout: string
  home_route: string
  theme_key: string
  menu_keys: string[]
  route_allowlist: string[]
  required_grants: string[]
  pwa_manifest_key?: string | null
  offline_policy_key?: string | null
  legacy_portal_mode?: string | null
  migration_note?: string | null
  display_name: string
}

export type PortalSummary = Pick<
  PortalManifest,
  'portal_key' | 'display_name' | 'physical_frontend' | 'home_route' | 'legacy_portal_mode'
>

export type PortalMembership = {
  id: string
  workspace_id: string
  membership_type: string
  status: string
  company_id?: string | null
}

const LEGACY_MODE_MAP: Record<string, string> = {
  aislos: 'aislos',
  store: 'store',
  developer: 'developer',
}

function matchAllowlist(path: string, patterns: string[]): boolean {
  const normalized = path.split('?')[0]
  return patterns.some((pattern) => {
    if (pattern.endsWith('/**')) {
      const base = pattern.slice(0, -3)
      return normalized === base || normalized.startsWith(`${base}/`)
    }
    return normalized === pattern
  })
}

export function usePortalManifest() {
  const physicalFrontend = 'pc' as const
  const apiBase = useApiBase()
  const { mode, isPathAllowed: legacyPathAllowed } = usePortalMode()
  const { token } = useAuth()
  const manifest = useState<PortalManifest | null>('portal-manifest', () => null)
  const loadedKey = useState<string | null>('portal-manifest-loaded-key', () => null)
  const error = useState('portal-manifest-error', () => '')
  const availablePortals = useState<PortalSummary[]>('portal-access-items', () => [])
  const memberships = useState<PortalMembership[]>('portal-access-memberships', () => [])
  const accessLoaded = useState('portal-access-loaded', () => false)
  const accessError = useState('portal-access-error', () => '')
  const activeWorkspaceId = useState<string | null>('portal-active-workspace', () => null)
  const activePortalCookie = useCookie<string | null>('ainerwise_active_portal', { sameSite: 'lax' })
  const activeWorkspaceCookie = useCookie<string | null>('ainerwise_active_workspace', { sameSite: 'lax' })
  const availableForFrontend = computed(() =>
    availablePortals.value.filter(item => item.physical_frontend === physicalFrontend),
  )

  function canonicalKey(portalKey?: string) {
    const raw = portalKey || mode
    if (raw === 'aislos' && typeof window !== 'undefined') {
      const path = window.location.pathname
      if (path === '/procurement' || path.startsWith('/procurement/')) {
        return 'procurement'
      }
    }
    return LEGACY_MODE_MAP[raw] || raw
  }

  async function load(portalKey?: string) {
    error.value = ''
    const key = canonicalKey(portalKey)
    try {
      manifest.value = await $fetch<PortalManifest>(
        `${apiBase}/portal-manifests/resolve/${encodeURIComponent(key)}`,
      )
      loadedKey.value = manifest.value.portal_key
    } catch (e: any) {
      error.value = e?.data?.detail || e?.message || 'Unknown portal'
      manifest.value = null
      loadedKey.value = null
    }
  }

  async function loadAccess(force = false) {
    if (accessLoaded.value && !force) return true
    accessError.value = ''
    if (!token.value) {
      availablePortals.value = []
      memberships.value = []
      accessLoaded.value = true
      return true
    }
    try {
      const data = await $fetch<{ items: PortalSummary[]; memberships: PortalMembership[] }>(
        `${apiBase}/auth/me/portals`,
        { headers: { Authorization: `Bearer ${token.value}` } },
      )
      availablePortals.value = data.items
      memberships.value = data.memberships
      const savedWorkspace = activeWorkspaceCookie.value
      activeWorkspaceId.value = data.memberships.some(item => item.workspace_id === savedWorkspace)
        ? savedWorkspace
        : data.memberships.length === 1 ? data.memberships[0].workspace_id : null
      activeWorkspaceCookie.value = activeWorkspaceId.value
      accessLoaded.value = true
      return true
    } catch (e: any) {
      availablePortals.value = []
      memberships.value = []
      activeWorkspaceId.value = null
      accessLoaded.value = false
      accessError.value = e?.data?.detail || e?.message || 'Unable to load portal access'
      return false
    }
  }

  function isPortalAvailable(portalKey: string) {
    return availablePortals.value.some(item => item.portal_key === canonicalKey(portalKey))
  }

  async function switchPortal(portalKey: string, workspaceId?: string | null) {
    if (!token.value) {
      throw new Error('Authenticated Core session required')
    }
    const data = await $fetch<{ portal_key: string; workspace_id?: string | null; manifest: PortalManifest }>(
      `${apiBase}/auth/portal-switch`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${token.value}` },
        body: { portal_key: canonicalKey(portalKey), workspace_id: workspaceId || activeWorkspaceId.value },
      },
    )
    manifest.value = data.manifest
    loadedKey.value = data.portal_key
    activeWorkspaceId.value = data.workspace_id || null
    activePortalCookie.value = data.portal_key
    activeWorkspaceCookie.value = activeWorkspaceId.value
    return data.manifest
  }

  async function switchAndNavigate(portalKey: string, workspaceId?: string | null) {
    const selected = await switchPortal(portalKey, workspaceId)
    return navigateTo(selected.home_route)
  }

  function selectWorkspace(workspaceId: string | null) {
    if (workspaceId && !memberships.value.some(item => item.workspace_id === workspaceId)) {
      throw new Error('Workspace is not available for this account')
    }
    activeWorkspaceId.value = workspaceId
    activeWorkspaceCookie.value = workspaceId
  }

  function isRouteAllowed(path: string) {
    if (manifest.value?.route_allowlist?.length) {
      return matchAllowlist(path, manifest.value.route_allowlist)
    }
    return legacyPathAllowed(path)
  }

  return {
    manifest,
    loadedKey,
    error,
    availablePortals,
    memberships,
    accessLoaded,
    accessError,
    activeWorkspaceId,
    activePortalCookie,
    availableForFrontend,
    load,
    loadAccess,
    isPortalAvailable,
    switchPortal,
    switchAndNavigate,
    selectWorkspace,
    isRouteAllowed,
    canonicalKey,
  }
}
