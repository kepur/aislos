<template>
  <div class="min-h-screen procurement-layout text-slate-100">
    <header class="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
      <div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div class="flex items-center gap-3">
          <NuxtLink :to="brand.homePath" class="text-sm font-semibold text-white">
            {{ brandLabel }}
          </NuxtLink>
          <span :class="['rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider', brand.badge]">
            {{ $t('procurement.workspace') }}
          </span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <span v-if="policy" class="hidden sm:inline text-slate-400">
            {{ $t('procurement.mode') }}: {{ policy.default_procurement_mode }}
          </span>
          <LanguageSwitcher class="procurement-lang" />
          <button type="button" class="text-slate-400 hover:text-red-400" @click="logout">
            {{ $t('nav.logout') }}
          </button>
        </div>
      </div>
    </header>
    <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import type { PortalPolicy } from '~/composables/useProcurement'

const { logout } = useAuth()
const { t } = useI18n()
const policy = useState<PortalPolicy | null>('procurement-portal-policy', () => null)
const { brand, portalKey } = useProcurementBrand(policy)

const brandLabel = computed(() =>
  portalKey.value === 'cebu' ? t('procurement.brands.cebu') : t('procurement.brands.aislos'),
)
</script>

<style scoped>
.procurement-layout {
  background: radial-gradient(circle at top, rgba(15, 118, 110, 0.12), transparent 45%),
    linear-gradient(180deg, #020617 0%, #0f172a 100%);
}
:deep(.procurement-lang select) {
  background: rgba(15, 23, 42, 0.8) !important;
  border-color: rgba(148, 163, 184, 0.3) !important;
  color: #e2e8f0 !important;
}
</style>
