<template>
  <ResourceManager
    :title="t('lc.pfrTitle')"
    :description="t('lc.pfrDesc')"
    endpoint="/platform-fee-rules"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.pfrEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const solutionLines = ['buildingbrain', 'energyguard', 'storageguard', 'aquaguard', 'kitchenguard', 'assetpulse', 'factorypulse', 'agribrain']
const sizes = ['any', 'small', 'medium', 'large']
const feeTypes = ['fixed', 'percentage', 'hybrid']

const columns = computed(() => [
  { key: 'name', label: t('lc.name') },
  { key: 'solution_line', label: t('lc.line') },
  { key: 'project_size_band', label: t('lc.projectSize') },
  { key: 'fee_type', label: t('lc.feeType') },
  { key: 'percentage', label: '%', format: (v: any) => (v == null ? '—' : `${(Number(v) * 100).toFixed(1)}%`) },
  { key: 'fixed_fee', label: t('lc.fixed'), format: (v: any) => (v == null ? '—' : `€${v}`) },
  { key: 'is_active', label: t('lc.active') },
])

const fields = computed(() => [
  { key: 'name', label: t('lc.name'), full: true },
  { key: 'solution_line', label: t('lc.solutionLine'), type: 'select', options: solutionLines },
  { key: 'project_size_band', label: t('lc.projectSize'), type: 'select', options: sizes },
  { key: 'fee_type', label: t('lc.feeType'), type: 'select', options: feeTypes },
  { key: 'percentage', label: t('lc.percentage'), type: 'number', step: 'any' },
  { key: 'fixed_fee', label: t('lc.fixedFee'), type: 'number', step: 'any' },
  { key: 'min_fee', label: t('lc.minFee'), type: 'number', step: 'any' },
  { key: 'max_fee', label: t('lc.maxFee'), type: 'number', step: 'any' },
  { key: 'is_active', label: t('lc.active'), type: 'checkbox' },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
