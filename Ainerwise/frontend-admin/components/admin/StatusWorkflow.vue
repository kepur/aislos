<template>
  <div class="admin-card">
    <h2 class="admin-section-title mb-4">Status</h2>
    <div class="flex items-center gap-3 mb-4">
      <StatusBadge :status="currentStatus" />
      <span class="text-sm admin-muted">Current status</span>
    </div>
    <div v-if="allowedTransitions.length" class="flex flex-wrap gap-2">
      <button
        v-for="transition in allowedTransitions"
        :key="transition.to"
        :class="[
          'px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors',
          transition.variant === 'danger'
            ? 'border-red-300 text-red-700 hover:bg-red-50'
            : transition.variant === 'success'
              ? 'border-green-300 text-green-700 hover:bg-green-50'
              : transition.variant === 'warning'
                ? 'border-yellow-300 text-yellow-700 hover:bg-yellow-50'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50',
        ]"
        :disabled="loading"
        @click="$emit('transition', transition.to)"
      >
        {{ transition.label }}
      </button>
    </div>
    <p v-else class="text-sm admin-muted">No transitions available from this status.</p>
  </div>
</template>

<script setup lang="ts">
interface Transition {
  to: string
  label: string
  variant?: 'default' | 'success' | 'danger' | 'warning'
}

const props = defineProps<{
  currentStatus: string
  entity: 'lead' | 'product' | 'vendor' | 'quote' | 'project' | 'ticket'
  loading?: boolean
}>()

defineEmits<{
  transition: [status: string]
}>()

const workflowMap: Record<string, Record<string, Transition[]>> = {
  lead: {
    new: [
      { to: 'contacted', label: 'Mark Contacted', variant: 'default' },
      { to: 'ai_analyzing', label: 'Send to AI', variant: 'warning' },
      { to: 'qualified', label: 'Qualify', variant: 'success' },
      { to: 'closed', label: 'Close', variant: 'danger' },
    ],
    contacted: [
      { to: 'ai_analyzing', label: 'Send to AI', variant: 'warning' },
      { to: 'qualified', label: 'Qualify', variant: 'success' },
      { to: 'closed', label: 'Close', variant: 'danger' },
    ],
    ai_analyzing: [
      { to: 'ai_completed', label: 'AI Done', variant: 'success' },
    ],
    ai_completed: [
      { to: 'qualified', label: 'Qualify', variant: 'success' },
      { to: 'closed', label: 'Close', variant: 'danger' },
    ],
    qualified: [
      { to: 'quoting', label: 'Start Quoting', variant: 'default' },
      { to: 'closed', label: 'Close', variant: 'danger' },
    ],
    quoting: [
      { to: 'won', label: 'Won', variant: 'success' },
      { to: 'lost', label: 'Lost', variant: 'danger' },
    ],
    won: [],
    lost: [
      { to: 'new', label: 'Reopen', variant: 'default' },
    ],
    closed: [
      { to: 'new', label: 'Reopen', variant: 'default' },
    ],
  },
  product: {
    draft: [
      { to: 'pending_review', label: 'Submit for Review', variant: 'warning' },
    ],
    pending_review: [
      { to: 'approved', label: 'Approve', variant: 'success' },
      { to: 'rejected', label: 'Reject', variant: 'danger' },
    ],
    approved: [
      { to: 'active', label: 'Activate', variant: 'success' },
      { to: 'draft', label: 'Back to Draft', variant: 'default' },
    ],
    active: [
      { to: 'inactive', label: 'Deactivate', variant: 'warning' },
    ],
    inactive: [
      { to: 'active', label: 'Reactivate', variant: 'success' },
    ],
    rejected: [
      { to: 'draft', label: 'Back to Draft', variant: 'default' },
    ],
  },
  vendor: {
    pending: [
      { to: 'approved', label: 'Approve', variant: 'success' },
      { to: 'rejected', label: 'Reject', variant: 'danger' },
    ],
    approved: [
      { to: 'suspended', label: 'Suspend', variant: 'warning' },
    ],
    rejected: [
      { to: 'pending', label: 'Reconsider', variant: 'default' },
    ],
    suspended: [
      { to: 'approved', label: 'Reactivate', variant: 'success' },
    ],
  },
  quote: {
    draft: [
      { to: 'sent', label: 'Send to Client', variant: 'default' },
    ],
    sent: [
      { to: 'accepted', label: 'Client Accepted', variant: 'success' },
      { to: 'rejected', label: 'Client Rejected', variant: 'danger' },
      { to: 'expired', label: 'Mark Expired', variant: 'warning' },
    ],
    accepted: [],
    rejected: [
      { to: 'draft', label: 'Revise', variant: 'default' },
    ],
    expired: [
      { to: 'draft', label: 'Revise', variant: 'default' },
    ],
  },
  project: {
    planning: [
      { to: 'site_survey', label: 'Schedule Survey', variant: 'default' },
      { to: 'closed', label: 'Cancel', variant: 'danger' },
    ],
    site_survey: [
      { to: 'quotation_confirmed', label: 'Confirm Quote', variant: 'success' },
      { to: 'planning', label: 'Back to Planning', variant: 'warning' },
      { to: 'closed', label: 'Cancel', variant: 'danger' },
    ],
    quotation_confirmed: [
      { to: 'procurement', label: 'Start Procurement', variant: 'default' },
      { to: 'closed', label: 'Cancel', variant: 'danger' },
    ],
    procurement: [
      { to: 'delivery', label: 'Ship / Deliver', variant: 'default' },
    ],
    delivery: [
      { to: 'installation', label: 'Start Installation', variant: 'default' },
    ],
    installation: [
      { to: 'testing', label: 'Start Testing', variant: 'default' },
      { to: 'delivery', label: 'Awaiting Parts', variant: 'warning' },
    ],
    testing: [
      { to: 'handover', label: 'Handover to Client', variant: 'success' },
      { to: 'installation', label: 'Back to Install', variant: 'warning' },
    ],
    handover: [
      { to: 'maintenance', label: 'Enter Maintenance', variant: 'default' },
    ],
    maintenance: [
      { to: 'closed', label: 'Close Project', variant: 'danger' },
    ],
    closed: [
      { to: 'planning', label: 'Reopen', variant: 'default' },
    ],
  },
  ticket: {
    open: [
      { to: 'in_progress', label: 'Start Working', variant: 'default' },
      { to: 'closed', label: 'Close', variant: 'danger' },
    ],
    in_progress: [
      { to: 'resolved', label: 'Resolved', variant: 'success' },
      { to: 'open', label: 'Reopen', variant: 'warning' },
    ],
    resolved: [
      { to: 'closed', label: 'Close', variant: 'default' },
      { to: 'open', label: 'Reopen', variant: 'warning' },
    ],
    closed: [
      { to: 'open', label: 'Reopen', variant: 'default' },
    ],
  },
}

const allowedTransitions = computed((): Transition[] => {
  const entityMap = workflowMap[props.entity]
  if (!entityMap) return []
  return entityMap[props.currentStatus] || []
})
</script>
