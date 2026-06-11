export interface DeliverableSpec {
  key: string
  media_type: string
  channel: string
  language: string
  format: string
  width?: number | null
  height?: number | null
  duration_seconds?: number | null
  variant_count?: number
  required_text?: string[] | null
  notes?: string | null
}

export interface BriefVersionContent {
  copy_json?: Record<string, unknown> | null
  audience_json?: Record<string, unknown> | null
  brand_constraints_json?: Record<string, unknown> | null
  channel_specs_json?: Record<string, unknown> | null
  deliverables_json?: DeliverableSpec[] | null
  source_refs_json?: Record<string, unknown> | null
  compliance_json?: Record<string, unknown> | null
}

export interface BriefVersion extends BriefVersionContent {
  id: string
  brief_id: string
  version: number
  status: string
  content_hash?: string | null
  created_at: string
  updated_at: string
}

export interface CreativeBrief {
  id: string
  title: string
  objective?: string | null
  status: string
  campaign_id?: string | null
  region_id?: string | null
  current_version_id?: string | null
  current_version?: BriefVersion | null
  created_at: string
  updated_at: string
}

export interface MediaRequest {
  id: string
  brief_version_id: string
  deliverable_key: string
  status: string
  submitted_asset_count: number
  progress_percent?: number | null
  progress_message?: string | null
  failure_code?: string | null
  failure_message?: string | null
  external_job_ref?: string | null
  completed_at?: string | null
  created_at: string
  updated_at: string
}

export interface IntegrationClient {
  id: string
  name: string
  key_prefix: string
  status: string
  scopes_json: string[]
  allowed_region_ids_json?: string[] | null
  last_used_at?: string | null
  created_at: string
  updated_at: string
}

export interface IntegrationClientCreated extends IntegrationClient {
  client_secret: string
}

export interface MarketingAssetRow {
  id: string
  kind: string
  channel?: string | null
  lang: string
  title?: string | null
  content?: string | null
  status: string
  ai_generated: boolean
  created_at: string
}

export const INTEGRATION_SCOPES = [
  'briefs:read',
  'briefs:claim',
  'briefs:progress',
  'assets:upload',
  'assets:submit',
] as const

export function emptyBriefVersion(): BriefVersionContent {
  return {
    copy_json: { headline: '' },
    audience_json: { segment: '' },
    brand_constraints_json: { tone: '' },
    channel_specs_json: {},
    deliverables_json: [],
    compliance_json: { disclaimer: '' },
  }
}

export function emptyDeliverable(): DeliverableSpec {
  return {
    key: '',
    media_type: 'image',
    channel: 'instagram',
    language: 'en',
    format: 'png',
    width: 1080,
    height: 1080,
    variant_count: 1,
    required_text: [],
    notes: '',
  }
}

export function useMarketingIntegration() {
  const { apiFetch } = useApi()

  async function listBriefs(params?: { status?: string; skip?: number; limit?: number }) {
    const q = new URLSearchParams()
    if (params?.status) q.set('status', params.status)
    if (params?.skip != null) q.set('skip', String(params.skip))
    if (params?.limit != null) q.set('limit', String(params.limit))
    const suffix = q.toString() ? `?${q}` : ''
    return apiFetch<{ items: CreativeBrief[]; total: number }>(`/admin/marketing/creative-briefs${suffix}`)
  }

  async function getBrief(briefId: string) {
    return apiFetch<CreativeBrief>(`/admin/marketing/creative-briefs/${briefId}`)
  }

  async function createBrief(body: {
    title: string
    objective?: string
    campaign_id?: string
    region_id?: string
    version: BriefVersionContent
  }) {
    return apiFetch<CreativeBrief>('/admin/marketing/creative-briefs', { method: 'POST', body })
  }

  async function createBriefVersion(briefId: string, version: BriefVersionContent) {
    return apiFetch<BriefVersion>(`/admin/marketing/creative-briefs/${briefId}/versions`, {
      method: 'POST',
      body: version,
    })
  }

  async function updateBriefVersion(versionId: string, version: BriefVersionContent) {
    return apiFetch<BriefVersion>(`/admin/marketing/creative-brief-versions/${versionId}`, {
      method: 'PUT',
      body: version,
    })
  }

  async function submitBriefReview(versionId: string) {
    return apiFetch<BriefVersion>(`/admin/marketing/creative-brief-versions/${versionId}/submit-review`, {
      method: 'POST',
    })
  }

  async function approveBrief(versionId: string, notes?: string) {
    return apiFetch<BriefVersion>(`/admin/marketing/creative-brief-versions/${versionId}/approve`, {
      method: 'POST',
      body: { notes: notes || null },
    })
  }

  async function rejectBrief(versionId: string, reason: string) {
    return apiFetch<BriefVersion>(`/admin/marketing/creative-brief-versions/${versionId}/reject`, {
      method: 'POST',
      body: { reason },
    })
  }

  async function copyRejectedToDraft(versionId: string) {
    return apiFetch<BriefVersion>(`/admin/marketing/creative-brief-versions/${versionId}/copy-draft`, {
      method: 'POST',
    })
  }

  async function listMediaRequests(versionId: string) {
    return apiFetch<MediaRequest[]>(`/admin/marketing/creative-brief-versions/${versionId}/media-requests`)
  }

  async function createMediaRequests(versionId: string) {
    return apiFetch<MediaRequest[]>(
      `/admin/marketing/creative-brief-versions/${versionId}/create-media-requests`,
      { method: 'POST' },
    )
  }

  async function listIntegrationClients() {
    return apiFetch<{ items: IntegrationClient[]; total: number }>('/admin/marketing/integration-clients')
  }

  async function createIntegrationClient(body: {
    name: string
    scopes: string[]
    allowed_region_ids?: string[]
  }) {
    return apiFetch<IntegrationClientCreated>('/admin/marketing/integration-clients', {
      method: 'POST',
      body,
    })
  }

  async function suspendIntegrationClient(clientId: string) {
    return apiFetch<IntegrationClient>(`/admin/marketing/integration-clients/${clientId}/suspend`, {
      method: 'POST',
    })
  }

  async function revokeIntegrationClient(clientId: string) {
    return apiFetch<IntegrationClient>(`/admin/marketing/integration-clients/${clientId}/revoke`, {
      method: 'POST',
    })
  }

  async function rotateIntegrationSecret(clientId: string) {
    return apiFetch<IntegrationClientCreated>(
      `/admin/marketing/integration-clients/${clientId}/rotate-secret`,
      { method: 'POST' },
    )
  }

  async function listMarketingAssets(status?: string) {
    const suffix = status ? `?status=${encodeURIComponent(status)}` : ''
    return apiFetch<{ items: MarketingAssetRow[]; total: number }>(`/admin/marketing/assets${suffix}`)
  }

  async function approveAsset(assetId: string, notes?: string) {
    return apiFetch(`/admin/marketing/assets/${assetId}/approve`, {
      method: 'POST',
      body: { notes: notes || null },
    })
  }

  async function rejectAsset(assetId: string, notes: string) {
    return apiFetch(`/admin/marketing/assets/${assetId}/reject`, {
      method: 'POST',
      body: { notes },
    })
  }

  async function scheduleAsset(assetId: string, platform: string, scheduledAt: string) {
    return apiFetch(`/admin/marketing/assets/${assetId}/schedule`, {
      method: 'POST',
      body: { platform, scheduled_at: scheduledAt },
    })
  }

  return {
    listBriefs,
    getBrief,
    createBrief,
    createBriefVersion,
    updateBriefVersion,
    submitBriefReview,
    approveBrief,
    rejectBrief,
    copyRejectedToDraft,
    listMediaRequests,
    createMediaRequests,
    listIntegrationClients,
    createIntegrationClient,
    suspendIntegrationClient,
    revokeIntegrationClient,
    rotateIntegrationSecret,
    listMarketingAssets,
    approveAsset,
    rejectAsset,
    scheduleAsset,
  }
}
