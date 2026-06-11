<template>
  <ResourceManager
    :title="t('lc.calTitle')"
    :description="t('lc.calDesc')"
    endpoint="/calibration-records"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.calEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const results = ['pass', 'fail', 'adjusted']

const columns = computed(() => [
  { key: 'calibration_date', label: t('lc.calibrated') },
  { key: 'next_due_date', label: t('lc.nextDue') },
  { key: 'calibration_method', label: t('lc.method') },
  { key: 'technician', label: t('lc.technician') },
  { key: 'result', label: t('lc.result') },
])

const fields = computed(() => [
  { key: 'calibration_date', label: t('lc.calibrationDate'), type: 'date' },
  { key: 'next_due_date', label: t('lc.nextDueDate'), type: 'date' },
  { key: 'calibration_method', label: t('lc.method'), placeholder: 'e.g. reference probe comparison' },
  { key: 'technician', label: t('lc.technician') },
  { key: 'result', label: t('lc.result'), type: 'select', options: results },
  { key: 'monitoring_point_id', label: t('lc.monitoringPointId'), placeholder: t('common.uuidOptional') },
  { key: 'project_id', label: t('lc.projectId'), placeholder: t('common.uuidOptional') },
  { key: 'certificate_file_id', label: t('lc.certificateFileId'), placeholder: t('common.uuidOptional') },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
