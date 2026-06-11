<template>
  <ResourceManager
    :title="t('lc.ssTitle')"
    :description="t('lc.ssDesc')"
    endpoint="/supplier-scorecards"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.ssEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const rating = (key: string, labelKey: string) => ({ key, label: `${t(labelKey)} (${t('lc.ratingHint')})`, type: 'number', step: '1' })

const columns = computed(() => [
  { key: 'supplier_name', label: t('lc.supplier') },
  { key: 'quality', label: t('lc.quality') },
  { key: 'delivery', label: t('lc.delivery') },
  { key: 'response', label: t('lc.response') },
  { key: 'warranty_cooperation', label: t('lc.warrantyShort') },
  { key: 'price_stability', label: t('lc.price') },
  { key: 'overall_score', label: t('lc.overall'), format: (v: any) => (v == null ? '—' : Number(v).toFixed(2)) },
])

const fields = computed(() => [
  { key: 'supplier_name', label: t('lc.supplierName'), full: true },
  { key: 'company_id', label: t('lc.companyId'), placeholder: t('common.uuidOptional') },
  rating('quality', 'lc.quality'),
  rating('delivery', 'lc.delivery'),
  rating('response', 'lc.response'),
  rating('warranty_cooperation', 'lc.warrantyCoop'),
  rating('documentation', 'lc.documentation'),
  rating('price_stability', 'lc.priceStability'),
  rating('long_term_fit', 'lc.longTermFit'),
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
