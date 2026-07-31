<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-violet-600">Publishing operations</p><h1 class="mt-1 text-xl font-bold text-slate-900">Schedule</h1></div>
    <div class="m-card">
      <h2 class="text-sm font-bold text-slate-800">Media publish jobs</h2>
      <div v-for="job in jobs" :key="job.id" class="mt-3 rounded-xl bg-violet-50 p-3">
        <div class="flex justify-between gap-3"><p class="text-xs font-semibold text-slate-700">{{ job.platform }}</p><span class="status-pill bg-white text-violet-600">{{ job.status }}</span></div>
        <p class="mt-2 text-[10px] text-slate-400">{{ formatDate(job.scheduled_at) }}</p>
        <p v-if="job.error_message" class="mt-2 text-xs text-red-600">{{ job.error_message }}</p>
      </div>
      <p v-if="!jobs.length" class="py-3 text-center text-xs text-slate-400">No media publish jobs.</p>
    </div>
    <div class="m-card">
      <h2 class="text-sm font-bold text-slate-800">Marketing activities</h2>
      <div v-for="activity in activities" :key="activity.id" class="mt-3 rounded-xl bg-slate-50 p-3">
        <div class="flex justify-between gap-3"><p class="text-xs font-semibold text-slate-700">{{ activity.subject || activity.activity_type }}</p><span class="status-pill bg-violet-50 text-violet-600">{{ activity.status }}</span></div>
        <p class="mt-1 text-[10px] text-slate-400">{{ activity.channel }} · {{ formatDate(activity.scheduled_at) }}</p>
      </div>
      <p v-if="!activities.length" class="py-3 text-center text-xs text-slate-400">No scheduled activities.</p>
    </div>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'marketing-mobile' })
const api = useMarketingMobile()
const jobs = ref<any[]>([])
const activities = ref<any[]>([])
const error = ref('')
const formatDate = (value?: string) => value ? new Date(value).toLocaleString() : 'Not scheduled'
onMounted(async () => {
  try {
    const [jobData, activityData] = await Promise.all([api.listPublishJobs(), api.listActivities('scheduled')])
    jobs.value = jobData.items
    activities.value = activityData.items
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
})
</script>

