<template>
  <ResourceManager
    :title="t('lc.mpTitle')"
    :description="t('lc.mpDesc')"
    endpoint="/monitoring-points"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.mpEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const solutionLines = ['buildingbrain', 'energyguard', 'storageguard', 'aquaguard', 'kitchenguard', 'assetpulse', 'factorypulse', 'agribrain']
const pointTypes = ['temperature', 'humidity', 'door', 'power', 'ph', 'conductivity', 'turbidity', 'cod', 'gas', 'co', 'smoke', 'water_leak', 'vibration', 'current', 'energy', 'asset_tag', 'other']
const statuses = ['active', 'inactive', 'fault', 'maintenance']

const columns = computed(() => [
  { key: 'site', label: t('lc.site') },
  { key: 'device_name', label: t('lc.device') },
  { key: 'point_type', label: t('lc.type') },
  { key: 'unit', label: t('lc.unit') },
  { key: 'status', label: t('lc.status') },
  { key: 'next_calibration_at', label: t('lc.nextCalibration') },
])

const fields = computed(() => [
  { key: 'site', label: t('lc.site') },
  { key: 'device_name', label: t('lc.deviceName') },
  { key: 'solution_line', label: t('lc.solutionLine'), type: 'select', options: solutionLines },
  { key: 'point_type', label: t('lc.pointType'), type: 'select', options: pointTypes },
  { key: 'unit', label: t('lc.unit'), placeholder: 'C, %RH, ...' },
  { key: 'threshold_min', label: t('lc.thresholdMin'), type: 'number', step: 'any' },
  { key: 'threshold_max', label: t('lc.thresholdMax'), type: 'number', step: 'any' },
  { key: 'calibration_cycle_months', label: t('lc.calCycleMonths'), type: 'number' },
  { key: 'last_calibrated_at', label: t('lc.lastCalibrated'), type: 'date' },
  { key: 'next_calibration_at', label: t('lc.nextCalibration'), type: 'date' },
  { key: 'status', label: t('lc.status'), type: 'select', options: statuses },
  { key: 'project_id', label: t('lc.projectId'), placeholder: t('common.uuidOptional') },
  { key: 'product_id', label: t('lc.productId'), placeholder: t('common.uuidOptional') },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
