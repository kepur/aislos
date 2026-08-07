<template>
  <div class="min-h-screen bg-slate-50 pb-24">
    <header class="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-slate-100 bg-white/95 px-4 pt-safe backdrop-blur">
      <NuxtLink :to="localizedPath('/marketplace')" class="text-sm font-bold text-indigo-700">
        {{ t('common.back') }}
      </NuxtLink>
      <h1 class="truncate text-base font-extrabold text-slate-900">{{ copy.title }}</h1>
    </header>

    <main class="space-y-4 px-4 py-5">
      <section class="rounded-3xl bg-white p-5 shadow-card">
        <p class="text-xs font-black uppercase tracking-[0.18em] text-indigo-600">{{ copy.kicker }}</p>
        <h2 class="mt-2 text-2xl font-extrabold leading-tight text-slate-950">{{ copy.heading }}</h2>
        <p class="mt-2 text-sm leading-6 text-slate-500">{{ copy.subtitle }}</p>
      </section>

      <section class="space-y-3">
        <button
          v-for="option in publishOptions"
          :key="option.value"
          type="button"
          class="w-full rounded-3xl border bg-white p-4 text-left shadow-card transition active:scale-[0.99]"
          :class="option.border"
          @click="go(option.to)"
        >
          <div class="flex items-center justify-between gap-4">
            <div>
              <p class="text-xs font-black uppercase tracking-[0.16em]" :class="option.kickerClass">
                {{ option.kicker }}
              </p>
              <h3 class="mt-1 text-lg font-extrabold text-slate-950">{{ option.title }}</h3>
              <p class="mt-1 text-xs leading-5 text-slate-500">{{ option.desc }}</p>
            </div>
            <span class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-lg font-black" :class="option.iconClass">→</span>
          </div>
        </button>
      </section>

      <section class="rounded-2xl border border-amber-100 bg-amber-50 p-4">
        <p class="text-xs leading-5 text-amber-800">{{ copy.note }}</p>
      </section>
    </main>

    <MarketBottomBar />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

definePageMeta({ layout: 'default' })
useHead({ title: 'List item' })

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n({ useScope: 'global' })

const copyByLocale: Record<string, Record<string, string>> = {
  en: {
    title: 'List item',
    kicker: 'AinerWise Market',
    heading: 'Choose how this product enters the market.',
    subtitle: 'New, enterprise recycled and personal used items share the same AinerWise Market feed. The item status decides warranty and visibility rules.',
    newKicker: 'New',
    newTitle: 'New company product',
    newDesc: 'For supplier catalog items, official products, B2B/B2C sales and RFQ matching.',
    recycledKicker: 'Recycled',
    recycledTitle: 'Enterprise recycled or refurbished',
    recycledDesc: 'For business resale with condition notes and warranty requirements.',
    usedKicker: 'Used',
    usedTitle: 'Personal used item',
    usedDesc: 'For individual second-hand items. Warranty can be optional.',
    note: 'AinerWise keeps all listings in one market. Buyers filter by category, country, price and item status instead of switching apps.',
  },
  zh: {
    title: '发布商品',
    kicker: 'AinerWise Market',
    heading: '选择这个商品如何进入市场。',
    subtitle: '全新、企业回收再售和个人二手都进入同一个 AinerWise Market。商品状态决定保修、可见性和交易规则。',
    newKicker: '全新',
    newTitle: '企业全新商品',
    newDesc: '用于供应商目录、官方推荐、B2B/B2C 销售和 RFQ 匹配。',
    recycledKicker: '回收再售',
    recycledTitle: '企业回收或翻新商品',
    recycledDesc: '用于企业再销售，需要填写成色说明和保修信息。',
    usedKicker: '二手',
    usedTitle: '个人二手商品',
    usedDesc: '用于个人闲置或二手设备，保修可以为空。',
    note: 'AinerWise 只有一个市场。买家按品类、国家、价格和商品状态筛选，不需要切换到另一个 App。',
  },
  sr: {
    title: 'Dodaj proizvod',
    kicker: 'AinerWise Market',
    heading: 'Izaberite kako proizvod ulazi u market.',
    subtitle: 'Novi, firmno obnovljeni i polovni proizvodi koriste isti AinerWise Market feed.',
    newKicker: 'Novo',
    newTitle: 'Novi proizvod firme',
    newDesc: 'Za katalog dobavljaca, B2B/B2C prodaju i RFQ povezivanje.',
    recycledKicker: 'Obnovljeno',
    recycledTitle: 'Firmno obnovljeno',
    recycledDesc: 'Za preprodaju firme uz stanje i garanciju.',
    usedKicker: 'Polovno',
    usedTitle: 'Licni polovni proizvod',
    usedDesc: 'Za privatne polovne artikle. Garancija nije obavezna.',
    note: 'AinerWise koristi jedan market. Kupci filtriraju po kategoriji, drzavi, ceni i stanju proizvoda.',
  },
  pl: {
    title: 'Dodaj produkt',
    kicker: 'AinerWise Market',
    heading: 'Wybierz, jak produkt trafi do rynku.',
    subtitle: 'Nowe, firmowo odnowione i prywatne używane produkty są w jednym AinerWise Market.',
    newKicker: 'Nowe',
    newTitle: 'Nowy produkt firmowy',
    newDesc: 'Dla katalogu dostawcy, sprzedaży B2B/B2C i dopasowań RFQ.',
    recycledKicker: 'Odnowione',
    recycledTitle: 'Firmowo odnowione',
    recycledDesc: 'Do odsprzedaży przez firmę z opisem stanu i gwarancją.',
    usedKicker: 'Używane',
    usedTitle: 'Prywatny używany produkt',
    usedDesc: 'Dla prywatnych używanych przedmiotów. Gwarancja może być opcjonalna.',
    note: 'AinerWise ma jeden market. Kupujący filtrują po kategorii, kraju, cenie i stanie produktu.',
  },
}

const copy = computed(() => copyByLocale[locale.value] || copyByLocale.en)

const publishOptions = computed(() => [
  {
    value: 'new',
    kicker: copy.value.newKicker,
    title: copy.value.newTitle,
    desc: copy.value.newDesc,
    to: '/supplier/catalog?action=create&listing_origin=new',
    border: 'border-indigo-100',
    kickerClass: 'text-indigo-600',
    iconClass: 'bg-indigo-50 text-indigo-700',
  },
  {
    value: 'enterprise_recycled',
    kicker: copy.value.recycledKicker,
    title: copy.value.recycledTitle,
    desc: copy.value.recycledDesc,
    to: '/supplier/catalog?action=create&listing_origin=enterprise_recycled',
    border: 'border-emerald-100',
    kickerClass: 'text-emerald-600',
    iconClass: 'bg-emerald-50 text-emerald-700',
  },
  {
    value: 'personal_secondhand',
    kicker: copy.value.usedKicker,
    title: copy.value.usedTitle,
    desc: copy.value.usedDesc,
    to: '/secondhand/sell?listing_origin=personal_secondhand',
    border: 'border-amber-100',
    kickerClass: 'text-amber-600',
    iconClass: 'bg-amber-50 text-amber-700',
  },
])

function localizedPath(path: string) {
  const prefix = getLocalePrefixFromPath(route.path) || (import.meta.client ? localStorage.getItem('h5_locale_prefix') || '' : '')
  return prefix ? withLocalePrefix(path, prefix) : path
}

function go(path: string) {
  router.push(localizedPath(path))
}
</script>
