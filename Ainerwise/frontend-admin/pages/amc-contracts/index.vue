<template>
  <ResourceManager
    :title="t('lc.amcTitle')"
    :description="t('lc.amcDesc')"
    endpoint="/amc-contracts"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.amcEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const packages = ['basic', 'compliance', 'commercial', 'premium', 'enterprise']
const pricingModes = ['percentage', 'point_based', 'site_based', 'service_level']
const renewalStatuses = ['active', 'renewal_due', 'renewed', 'lapsed', 'cancelled']

const columns = computed(() => [
  { key: 'package', label: t('lc.package') },
  { key: 'pricing_mode', label: t('lc.pricing') },
  { key: 'recurring_fee', label: t('lc.annualFee'), format: (v: any, r: any) => (v != null ? `${r.currency || 'EUR'} ${v}` : '—') },
  { key: 'renewal_status', label: t('lc.renewal') },
  { key: 'start_date', label: t('lc.start') },
  { key: 'end_date', label: t('lc.end') },
])

const fields = computed(() => [
  { key: 'package', label: t('lc.package'), type: 'select', options: packages },
  { key: 'pricing_mode', label: t('lc.pricingMode'), type: 'select', options: pricingModes },
  { key: 'recurring_fee', label: t('lc.annualRecurringFee'), type: 'number', step: 'any' },
  { key: 'currency', label: t('lc.currency'), placeholder: 'EUR' },
  { key: 'renewal_status', label: t('lc.renewalStatus'), type: 'select', options: renewalStatuses },
  { key: 'start_date', label: t('lc.startDate'), type: 'date' },
  { key: 'end_date', label: t('lc.endDate'), type: 'date' },
  { key: 'included_visits_per_year', label: t('lc.includedVisits'), type: 'number' },
  { key: 'response_target_hours', label: t('lc.responseTarget'), type: 'number' },
  { key: 'project_id', label: t('lc.projectId'), placeholder: t('common.uuidOptional') },
  { key: 'customer_id', label: t('lc.customerId'), placeholder: t('common.uuidOptional') },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
