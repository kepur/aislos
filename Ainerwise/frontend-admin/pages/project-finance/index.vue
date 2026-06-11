<template>
  <ResourceManager
    :title="t('lc.pfTitle')"
    :description="t('lc.pfDesc')"
    endpoint="/project-finances"
    :columns="columns"
    :fields="fields"
    :empty-text="t('lc.pfEmpty')"
  />
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { t } = useI18n({ useScope: 'global' })

const solutionLines = ['buildingbrain', 'energyguard', 'storageguard', 'aquaguard', 'kitchenguard', 'assetpulse', 'factorypulse', 'agribrain']
const money = (v: any) => (v == null ? '—' : `€${Number(v).toLocaleString()}`)

const columns = computed(() => [
  { key: 'solution_line', label: t('lc.line') },
  { key: 'contract_total', label: t('lc.contract'), format: money },
  { key: 'gross_profit', label: t('lc.grossProfit'), format: money },
  { key: 'gross_margin_percent', label: t('lc.margin'), format: (v: any) => (v == null ? '—' : `${Number(v).toFixed(1)}%`) },
  { key: 'first_year_profit', label: t('lc.firstYearProfit'), format: money },
  { key: 'ltv_3_year', label: t('lc.ltv3'), format: money },
  { key: 'ltv_5_year', label: t('lc.ltv5'), format: money },
])

const num = (key: string, label: string) => ({ key, label, type: 'number', step: 'any' })

const fields = computed(() => [
  { key: 'solution_line', label: t('lc.solutionLine'), type: 'select', options: solutionLines },
  { key: 'currency', label: t('lc.currency'), placeholder: 'EUR' },
  num('contract_total', t('lc.contractTotal')),
  num('hardware_revenue', t('lc.hardwareRevenue')),
  num('design_fee', t('lc.designFee')),
  num('installation_fee', t('lc.installationFee')),
  num('integration_fee', t('lc.integrationFee')),
  num('platform_fee', t('lc.platformFee')),
  num('project_management_fee', t('lc.pmFee')),
  num('amc_fee_year_1', t('lc.amcYear1')),
  num('amc_fee_annual', t('lc.amcAnnual')),
  num('consumable_revenue_estimate', t('lc.consumableRev')),
  num('calibration_revenue_estimate', t('lc.calibrationRev')),
  num('report_revenue_estimate', t('lc.reportRev')),
  num('alarm_monitoring_revenue_estimate', t('lc.alarmRev')),
  num('supplier_cost', t('lc.supplierCost')),
  num('shipping_cost', t('lc.shippingCost')),
  num('customs_cost', t('lc.customsCost')),
  num('local_installer_cost', t('lc.installerCost')),
  num('labor_cost', t('lc.laborCost')),
  num('travel_cost', t('lc.travelCost')),
  num('spare_parts_cost', t('lc.sparePartsCost')),
  num('warranty_reserve_cost', t('lc.warrantyReserveCost')),
  num('annual_service_cost', t('lc.annualServiceCost')),
  { key: 'project_id', label: t('lc.projectId'), placeholder: t('common.uuidOptional') },
  { key: 'customer_id', label: t('lc.customerId'), placeholder: t('common.uuidOptional') },
  { key: 'notes', label: t('lc.notes'), type: 'textarea', full: true },
])
</script>
