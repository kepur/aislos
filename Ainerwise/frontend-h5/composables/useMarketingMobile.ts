export interface MarketingDeliverable {
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

export interface MarketingBriefVersion {
  id: string
  brief_id: string
  version: number
  status: string
  copy_json?: Record<string, any> | null
  audience_json?: Record<string, any> | null
  brand_constraints_json?: Record<string, any> | null
  channel_specs_json?: Record<string, any> | null
  deliverables_json?: MarketingDeliverable[] | null
  source_refs_json?: Record<string, any> | null
  compliance_json?: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface MarketingBrief {
  id: string
  title: string
  objective?: string | null
  status: string
  current_version?: MarketingBriefVersion | null
  created_at: string
  updated_at: string
}

export interface MarketingAsset {
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

export function useMarketingMobile() {
  const { apiFetch } = useApi()

  function query(params: Record<string, string | number | undefined>) {
    const value = new URLSearchParams()
    Object.entries(params).forEach(([key, item]) => {
      if (item !== undefined && item !== '') value.set(key, String(item))
    })
    return value.toString() ? `?${value}` : ''
  }

  const dashboard = () => apiFetch<any>('/marketing/dashboard')
  const listBriefs = (status?: string) =>
    apiFetch<{ items: MarketingBrief[]; total: number }>(
      `/admin/marketing/creative-briefs${query({ status, limit: 100 })}`,
    )
  const getBrief = (id: string) =>
    apiFetch<MarketingBrief>(`/admin/marketing/creative-briefs/${id}`)
  const createBrief = (body: Record<string, any>) =>
    apiFetch<MarketingBrief>('/admin/marketing/creative-briefs', { method: 'POST', body })
  const updateVersion = (id: string, body: Record<string, any>) =>
    apiFetch(`/admin/marketing/creative-brief-versions/${id}`, { method: 'PUT', body })
  const submitReview = (id: string) =>
    apiFetch(`/admin/marketing/creative-brief-versions/${id}/submit-review`, { method: 'POST' })
  const approveBrief = (id: string, notes?: string) =>
    apiFetch(`/admin/marketing/creative-brief-versions/${id}/approve`, {
      method: 'POST',
      body: { notes: notes || null },
    })
  const rejectBrief = (id: string, reason: string) =>
    apiFetch(`/admin/marketing/creative-brief-versions/${id}/reject`, {
      method: 'POST',
      body: { reason },
    })
  const copyDraft = (id: string) =>
    apiFetch(`/admin/marketing/creative-brief-versions/${id}/copy-draft`, { method: 'POST' })
  const listMediaRequests = (id: string) =>
    apiFetch<any[]>(`/admin/marketing/creative-brief-versions/${id}/media-requests`)
  const createMediaRequests = (id: string) =>
    apiFetch<any[]>(`/admin/marketing/creative-brief-versions/${id}/create-media-requests`, {
      method: 'POST',
    })
  const listAssets = (status?: string) =>
    apiFetch<{ items: MarketingAsset[]; total: number }>(
      `/admin/marketing/assets${query({ status, limit: 100 })}`,
    )
  const approveAsset = (id: string, notes?: string) =>
    apiFetch(`/admin/marketing/assets/${id}/approve`, {
      method: 'POST',
      body: { notes: notes || null },
    })
  const rejectAsset = (id: string, notes: string) =>
    apiFetch(`/admin/marketing/assets/${id}/reject`, { method: 'POST', body: { notes } })
  const scheduleAsset = (id: string, platform: string, scheduledAt: string) =>
    apiFetch(`/admin/marketing/assets/${id}/schedule`, {
      method: 'POST',
      body: { platform, scheduled_at: scheduledAt },
    })
  const listActivities = (status?: string) =>
    apiFetch<{ items: any[]; total: number }>(`/marketing/activities${query({ status, limit: 100 })}`)
  const listPublishJobs = (status?: string) =>
    apiFetch<{ items: any[]; total: number }>(
      `/admin/marketing/publish-jobs${query({ status, limit: 100 })}`,
    )

  return {
    dashboard,
    listBriefs,
    getBrief,
    createBrief,
    updateVersion,
    submitReview,
    approveBrief,
    rejectBrief,
    copyDraft,
    listMediaRequests,
    createMediaRequests,
    listAssets,
    approveAsset,
    rejectAsset,
    scheduleAsset,
    listActivities,
    listPublishJobs,
  }
}

