<template>
  <ResourceManager
    :title="t('lc.cwTitle')"
    :description="t('lc.cwDesc')"
    endpoint="/customer-warranties"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.cwEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const warrantyModels = ['pass_through', 'managed', 'fast_replacement', 'premium_amc']

const columns = computed(() => [
  { key: 'warranty_model', label: t('lc.model') },
  { key: 'start_date', label: t('lc.start') },
  { key: 'end_date', label: t('lc.end') },
  { key: 'included_on_site_visits_per_year', label: t('lc.onsitePerYearShort') },
  { key: 'spare_parts_included', label: t('lc.spares') },
  { key: 'max_claims_per_year', label: t('lc.maxClaimsShort') },
])

const fields = computed(() => [
  { key: 'warranty_model', label: t('lc.warrantyModel'), type: 'select', options: warrantyModels },
  { key: 'start_date', label: t('lc.startDate'), type: 'date' },
  { key: 'end_date', label: t('lc.endDate'), type: 'date' },
  { key: 'included_on_site_visits_per_year', label: t('lc.onsitePerYear'), type: 'number' },
  { key: 'max_claims_per_year', label: t('lc.maxClaims'), type: 'number' },
  { key: 'included_labor', label: t('lc.includesLabor'), type: 'checkbox' },
  { key: 'included_remote_support', label: t('lc.includesRemote'), type: 'checkbox' },
  { key: 'spare_parts_included', label: t('lc.sparePartsIncluded'), type: 'checkbox' },
  { key: 'project_id', label: t('lc.projectId'), placeholder: t('common.uuidOptional') },
  { key: 'customer_id', label: t('lc.customerId'), placeholder: t('common.uuidOptional') },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
