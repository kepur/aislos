<template>
  <section class="portal-card overflow-hidden !p-0">
    <div class="flex items-center justify-between gap-4 bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-5 text-white">
      <div>
        <h2 class="text-base font-bold">{{ report.title || 'Monthly Compliance Summary' }}</h2>
        <p class="mt-1 text-xs text-cyan-100">{{ report.period }}</p>
      </div>
      <span v-if="report.sample" class="rounded-full bg-white/20 px-3 py-1 text-[10px] font-bold uppercase tracking-wider">
        Sample
      </span>
    </div>

    <div class="space-y-5 p-6">
      <div v-if="report.rooms?.length" class="grid gap-4 lg:grid-cols-3">
        <div v-for="room in report.rooms" :key="room.name" class="rounded-xl bg-slate-50 p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm font-bold text-slate-800">{{ room.name }}</p>
              <p class="mt-1 text-xs text-slate-400">Target {{ room.target }}</p>
            </div>
            <span class="text-sm font-bold" :class="complianceTextClass(room.compliance_pct)">
              {{ formatPct(room.compliance_pct) }}
            </span>
          </div>
          <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200">
            <div
              class="h-full rounded-full"
              :class="complianceBarClass(room.compliance_pct)"
              :style="{ width: `${Math.min(100, room.compliance_pct ?? 0)}%` }"
            />
          </div>
          <p class="mt-2 text-xs text-slate-500">
            {{ room.excursions ?? 0 }} excursion{{ (room.excursions ?? 0) === 1 ? '' : 's' }}
            <template v-if="room.max_excursion_min"> · longest {{ room.max_excursion_min }} min</template>
          </p>
        </div>
      </div>

      <div class="grid gap-3 sm:grid-cols-3">
        <div class="rounded-xl bg-slate-50 p-4 text-center">
          <p class="text-xl font-bold text-slate-800">{{ report.door_events ?? 0 }}</p>
          <p class="mt-1 text-xs font-medium text-slate-400">Door events</p>
        </div>
        <div class="rounded-xl bg-slate-50 p-4 text-center">
          <p class="text-xl font-bold text-slate-800">{{ report.outage_events ?? 0 }}</p>
          <p class="mt-1 text-xs font-medium text-slate-400">Outages</p>
        </div>
        <div class="rounded-xl bg-slate-50 p-4 text-center">
          <p class="text-xl font-bold text-slate-800">{{ report.alerts_sent ?? 0 }}</p>
          <p class="mt-1 text-xs font-medium text-slate-400">Alerts sent</p>
        </div>
      </div>

      <p v-if="report.calibration_status" class="text-xs text-slate-500">
        <span class="font-semibold text-slate-700">Calibration:</span> {{ report.calibration_status }}
      </p>
      <p class="rounded-xl bg-amber-50 p-4 text-xs leading-relaxed text-amber-700">
        Sample report for demonstration. Customer-specific compliance reporting is configured during onboarding;
        figures here are illustrative only.
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{ report: Record<string, any> }>()

function formatPct(value: number | undefined) {
  if (value === undefined || value === null) return '—'
  return `${Number(value).toFixed(1)}%`
}

function complianceTextClass(value: number | undefined) {
  if ((value ?? 0) >= 99.9) return 'text-emerald-600'
  if ((value ?? 0) >= 99) return 'text-amber-600'
  return 'text-red-600'
}

function complianceBarClass(value: number | undefined) {
  if ((value ?? 0) >= 99.9) return 'bg-emerald-500'
  if ((value ?? 0) >= 99) return 'bg-amber-500'
  return 'bg-red-500'
}
</script>
