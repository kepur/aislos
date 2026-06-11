<template>
  <ResourceManager
    :title="t('lc.mtTitle')"
    :description="t('lc.mtDesc')"
    endpoint="/maintenance-schedules"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.mtEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const taskTypes = ['inspection', 'calibration', 'battery_replace', 'probe_replace', 'firmware_update', 'report_review']
const statuses = ['scheduled', 'due', 'in_progress', 'done', 'skipped']

const columns = computed(() => [
  { key: 'device_name', label: t('lc.device') },
  { key: 'task_type', label: t('lc.task') },
  { key: 'due_date', label: t('lc.due') },
  { key: 'frequency_months', label: t('lc.everyMonths') },
  { key: 'status', label: t('lc.status') },
  { key: 'covered_by_amc', label: t('lc.amc') },
])

const fields = computed(() => [
  { key: 'device_name', label: t('lc.deviceName') },
  { key: 'task_type', label: t('lc.taskType'), type: 'select', options: taskTypes },
  { key: 'due_date', label: t('lc.dueDate'), type: 'date' },
  { key: 'frequency_months', label: t('lc.frequencyMonths'), type: 'number' },
  { key: 'status', label: t('lc.status'), type: 'select', options: statuses },
  { key: 'cost', label: t('lc.cost'), type: 'number', step: 'any' },
  { key: 'covered_by_amc', label: t('lc.coveredByAmc'), type: 'checkbox' },
  { key: 'project_id', label: t('lc.projectId'), placeholder: t('common.uuidOptional') },
  { key: 'monitoring_point_id', label: t('lc.monitoringPointId'), placeholder: t('common.uuidOptional') },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
