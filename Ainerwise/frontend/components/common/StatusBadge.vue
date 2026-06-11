<template>
  <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide', colorClass]">
    {{ label || status?.replace(/_/g, ' ') }}
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{
  status: string
  label?: string
}>()

const colorMap: Record<string, string> = {
  // Green family
  approved: 'bg-emerald-500/15 text-emerald-400',
  verified: 'bg-emerald-500/15 text-emerald-400',
  active: 'bg-emerald-500/15 text-emerald-400',
  won: 'bg-emerald-500/15 text-emerald-400',
  resolved: 'bg-emerald-500/15 text-emerald-400',
  accepted: 'bg-emerald-500/15 text-emerald-400',
  completed: 'bg-emerald-500/15 text-emerald-400',
  // Blue family
  new: 'bg-blue-500/15 text-blue-400',
  open: 'bg-blue-500/15 text-blue-400',
  qualified: 'bg-blue-500/15 text-blue-400',
  // Yellow/Amber family
  pending: 'bg-amber-500/15 text-amber-400',
  in_progress: 'bg-amber-500/15 text-amber-400',
  // Purple family
  sent: 'bg-purple-500/15 text-purple-400',
  // Red family
  rejected: 'bg-red-500/15 text-red-400',
  suspended: 'bg-red-500/15 text-red-400',
  lost: 'bg-red-500/15 text-red-400',
  critical: 'bg-red-500/15 text-red-400',
  // Gray family
  draft: 'bg-slate-500/15 text-slate-400',
  closed: 'bg-slate-500/15 text-slate-400',
  expired: 'bg-slate-500/15 text-slate-400',
  // Priority
  low: 'bg-slate-500/15 text-slate-400',
  medium: 'bg-blue-500/15 text-blue-400',
  high: 'bg-orange-500/15 text-orange-400',
}

const colorClass = computed(() => colorMap[props.status] || 'bg-slate-500/15 text-slate-400')
</script>
