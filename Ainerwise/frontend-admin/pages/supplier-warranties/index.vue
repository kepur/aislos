<template>
  <ResourceManager
    :title="t('lc.swTitle')"
    :description="t('lc.swDesc')"
    endpoint="/supplier-warranties"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.swEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const warrantyTypes = ['repair', 'replacement', 'parts_only', 'return_to_factory']
const shipping = ['supplier', 'ainerwise', 'customer', 'shared']

const columns = computed(() => [
  { key: 'warranty_years', label: t('lc.years') },
  { key: 'warranty_type', label: t('lc.type') },
  { key: 'shipping_responsibility', label: t('lc.shipping') },
  { key: 'response_time_days', label: t('lc.responseDays') },
  { key: 'spare_parts_available', label: t('lc.spares') },
  { key: 'warranty_region_limit', label: t('lc.regionLimit') },
])

const fields = computed(() => [
  { key: 'supplier_id', label: t('lc.supplierId'), placeholder: t('common.uuidOptional') },
  { key: 'product_id', label: t('lc.productId'), placeholder: t('common.uuidOptional') },
  { key: 'warranty_years', label: t('lc.warrantyYears'), type: 'number' },
  { key: 'warranty_type', label: t('lc.warrantyType'), type: 'select', options: warrantyTypes },
  { key: 'shipping_responsibility', label: t('lc.shippingResp'), type: 'select', options: shipping },
  { key: 'response_time_days', label: t('lc.responseTimeDays'), type: 'number' },
  { key: 'warranty_region_limit', label: t('lc.regionLimit') },
  { key: 'spare_parts_available', label: t('lc.sparesAvailable'), type: 'checkbox' },
  { key: 'firmware_support', label: t('lc.firmwareSupport'), type: 'checkbox' },
  { key: 'remote_debug_support', label: t('lc.remoteDebug'), type: 'checkbox' },
  { key: 'api_protocol_support', label: t('lc.apiSupport'), type: 'checkbox' },
  { key: 'replacement_policy', label: t('lc.replacementPolicy'), type: 'textarea', full: true },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
