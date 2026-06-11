export type PortalPolicy = {
  portal_key: string
  version: number
  default_procurement_mode: string
  allowed_project_types: string[]
  price_visibility_rule: string
  supplier_visibility_rule: string
  visible_categories: string[] | null
  confidence_gate: Record<string, string | number>
}

export type ProcurementProject = {
  id: string
  title: string
  description: string | null
  project_type: string
  portal_key: string
  status: string
  country: string | null
  region: string | null
  city: string | null
  facts_score: string
  boq_score: string
  overall_confidence: string
  current_boq_version_id: string | null
  policy_snapshot_json: Record<string, unknown>
  created_at: string
}

export type ProcurementFact = {
  id: string
  template_key: string
  label: string
  value_json: unknown
  required: boolean
  critical: boolean
  confidence: string
  user_confirmed: boolean
  assumption: string | null
}

export type ProcurementPackage = {
  id: string
  title: string
  trade: string
  commercial_type: string
  procurement_mode: string
  region: string | null
  status: string
  revision: number
  items: Array<{ id: string; boq_item_id: string; quantity: string }>
  candidate_partners: Array<Record<string, unknown>>
}

export type ConfidencePhase = 'ask' | 'estimate' | 'review' | 'ready'

export function parseConfidence(value: string | number | null | undefined): number {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n : 0
}

export function confidencePhase(
  overall: number,
  gate: Record<string, string | number> | undefined,
): ConfidencePhase {
  const askBelow = parseConfidence(gate?.ask_below ?? 0.6)
  const reviewAbove = parseConfidence(gate?.review_above ?? 0.8)
  if (overall < askBelow) return 'ask'
  if (overall < reviewAbove) return 'estimate'
  if (overall >= reviewAbove) return 'review'
  return 'estimate'
}

export function useProcurement() {
  const { apiFetch } = useApi()

  async function fetchPortalPolicy(): Promise<PortalPolicy> {
    return apiFetch<PortalPolicy>('/procurement/portal-policy')
  }

  async function listProjects(): Promise<{ items: ProcurementProject[]; total: number }> {
    return apiFetch('/procurement/projects')
  }

  async function createProject(body: {
    project_type: string
    title: string
    description?: string
    country?: string
    region?: string
    city?: string
  }): Promise<ProcurementProject> {
    return apiFetch('/procurement/projects', { method: 'POST', body })
  }

  async function getProject(id: string): Promise<ProcurementProject> {
    return apiFetch(`/procurement/projects/${id}`)
  }

  async function listFacts(projectId: string): Promise<ProcurementFact[]> {
    return apiFetch(`/procurement/projects/${projectId}/facts`)
  }

  async function patchFact(
    projectId: string,
    factId: string,
    body: { value_json?: unknown; user_confirmed?: boolean; assumption?: string },
  ): Promise<ProcurementFact> {
    return apiFetch(`/procurement/projects/${projectId}/facts/${factId}`, {
      method: 'PATCH',
      body,
    })
  }

  async function analyzeProject(projectId: string): Promise<Record<string, unknown>> {
    return apiFetch(`/procurement/projects/${projectId}/analyze`, {
      method: 'POST',
      body: {},
    })
  }

  async function getBoq(projectId: string): Promise<Record<string, unknown>> {
    return apiFetch(`/procurement/projects/${projectId}/boq`)
  }

  async function submitBoqReview(projectId: string, boqVersionId?: string): Promise<Record<string, unknown>> {
    return apiFetch(`/procurement/projects/${projectId}/boq/review`, {
      method: 'POST',
      body: boqVersionId ? { boq_version_id: boqVersionId } : {},
    })
  }

  async function freezeBoq(projectId: string, boqVersionId?: string): Promise<Record<string, unknown>> {
    return apiFetch(`/procurement/projects/${projectId}/boq/freeze`, {
      method: 'POST',
      body: boqVersionId ? { boq_version_id: boqVersionId } : {},
    })
  }

  async function listPackages(projectId: string): Promise<ProcurementPackage[]> {
    return apiFetch(`/procurement/projects/${projectId}/packages`)
  }

  async function generatePackages(projectId: string): Promise<{
    project_status: string
    packages: ProcurementPackage[]
  }> {
    return apiFetch(`/procurement/projects/${projectId}/packages/generate`, { method: 'POST' })
  }

  async function patchPackage(
    projectId: string,
    packageId: string,
    body: { title?: string; procurement_mode?: string; status?: string },
  ): Promise<ProcurementPackage> {
    return apiFetch(`/procurement/projects/${projectId}/packages/${packageId}`, {
      method: 'PATCH',
      body,
    })
  }

  async function publishRfq(
    projectId: string,
    packageId: string,
    body: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return apiFetch(`/procurement/projects/${projectId}/packages/${packageId}/publish-rfq`, {
      method: 'POST',
      body,
    })
  }

  return {
    fetchPortalPolicy,
    listProjects,
    createProject,
    getProject,
    listFacts,
    patchFact,
    analyzeProject,
    getBoq,
    submitBoqReview,
    freezeBoq,
    listPackages,
    generatePackages,
    patchPackage,
    publishRfq,
  }
}
