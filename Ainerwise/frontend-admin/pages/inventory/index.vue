<template>
  <ResourceManager
    :title="t('lc.invTitle')"
    :description="t('lc.invDesc')"
    endpoint="/inventory-items"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.invEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const columns = computed(() => [
  { key: 'name', label: t('lc.item') },
  { key: 'location', label: t('lc.location') },
  { key: 'quantity', label: t('lc.qty') },
  { key: 'reserved_quantity', label: t('lc.reserved') },
  { key: 'reorder_level', label: t('lc.reorderAt') },
  { key: 'expiry_date', label: t('lc.expiry') },
])

const fields = computed(() => [
  { key: 'name', label: t('lc.itemName'), full: true },
  { key: 'location', label: t('lc.location') },
  { key: 'quantity', label: t('lc.quantity'), type: 'number' },
  { key: 'reserved_quantity', label: t('lc.reserved'), type: 'number' },
  { key: 'min_stock_level', label: t('lc.minStock'), type: 'number' },
  { key: 'reorder_level', label: t('lc.reorderLevel'), type: 'number' },
  { key: 'cost', label: t('lc.unitCost'), type: 'number', step: 'any' },
  { key: 'currency', label: t('lc.currency'), placeholder: 'EUR' },
  { key: 'expiry_date', label: t('lc.expiryDate'), type: 'date' },
  { key: 'last_checked_at', label: t('lc.lastChecked'), type: 'date' },
  { key: 'product_id', label: t('lc.productId'), placeholder: t('common.uuidOptional') },
  { key: 'supplier_id', label: t('lc.supplierId'), placeholder: t('common.uuidOptional') },
  { key: 'reserved_for_project_id', label: t('lc.reservedForProject'), placeholder: t('common.uuidOptional') },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
