<template>
  <div class="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between gap-2 px-4 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white">
      <div>
        <h2 class="text-sm font-bold">{{ report.title || 'Monthly Compliance Summary' }}</h2>
        <p class="text-[11px] text-cyan-100">{{ report.period }}</p>
      </div>
      <span v-if="report.sample" class="text-[9px] font-bold uppercase tracking-wider bg-white/20 px-2 py-1 rounded-full">
        Sample
      </span>
    </div>

    <div class="p-4 space-y-3">
      <!-- Per-room compliance -->
      <div v-if="report.rooms?.length" class="space-y-2">
        <div
          v-for="room in report.rooms"
          :key="room.name"
          class="rounded-xl bg-slate-50 p-3"
        >
          <div class="flex items-center justify-between gap-2">
            <div>
              <p class="text-xs font-bold text-slate-800">{{ room.name }}</p>
              <p class="text-[11px] text-slate-400">Target {{ room.target }}</p>
            </div>
            <span
              class="text-xs font-bold"
              :class="(room.compliance_pct ?? 0) >= 99.9 ? 'text-emerald-600' : (room.compliance_pct ?? 0) >= 99 ? 'text-amber-600' : 'text-red-600'"
            >
              {{ formatPct(room.compliance_pct) }}
            </span>
          </div>
          <!-- Compliance bar -->
          <div class="mt-2 h-1.5 rounded-full bg-slate-200 overflow-hidden">
            <div
              class="h-full rounded-full"
              :class="(room.compliance_pct ?? 0) >= 99.9 ? 'bg-emerald-500' : (room.compliance_pct ?? 0) >= 99 ? 'bg-amber-500' : 'bg-red-500'"
              :style="{ width: `${Math.min(100, room.compliance_pct ?? 0)}%` }"
            />
          </div>
          <p class="mt-1.5 text-[11px] text-slate-500">
            {{ room.excursions ?? 0 }} excursion{{ (room.excursions ?? 0) === 1 ? '' : 's' }}
            <template v-if="room.max_excursion_min"> · longest {{ room.max_excursion_min }} min</template>
          </p>
        </div>
      </div>

      <!-- Event totals -->
      <div class="grid grid-cols-3 gap-2">
        <div class="rounded-xl bg-slate-50 p-2.5 text-center">
          <p class="text-base font-bold text-slate-800">{{ report.door_events ?? 0 }}</p>
          <p class="text-[10px] text-slate-400 font-medium">Door events</p>
        </div>
        <div class="rounded-xl bg-slate-50 p-2.5 text-center">
          <p class="text-base font-bold text-slate-800">{{ report.outage_events ?? 0 }}</p>
          <p class="text-[10px] text-slate-400 font-medium">Outages</p>
        </div>
        <div class="rounded-xl bg-slate-50 p-2.5 text-center">
          <p class="text-base font-bold text-slate-800">{{ report.alerts_sent ?? 0 }}</p>
          <p class="text-[10px] text-slate-400 font-medium">Alerts sent</p>
        </div>
      </div>

      <p v-if="report.calibration_status" class="text-[11px] text-slate-500">
        <span class="font-semibold text-slate-700">Calibration:</span> {{ report.calibration_status }}
      </p>

      <p class="rounded-xl bg-amber-50 p-3 text-[11px] leading-relaxed text-amber-700">
        Sample report for demonstration. Customer-specific compliance reporting is configured during onboarding;
        figures here are illustrative only.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ report: Record<string, any> }>()

function formatPct(value: number | undefined) {
  if (value === undefined || value === null) return '—'
  return `${Number(value).toFixed(1)}%`
}
</script>
