type LocaleCode = 'en' | 'zh' | 'sr' | 'pl'

type SeoPageCopy = {
  title: Record<LocaleCode, string>
  description: Record<LocaleCode, string>
}

const LOCALE_PREFIX: Record<LocaleCode, string> = {
  en: 'en',
  zh: 'cn',
  sr: 'rs',
  pl: 'pl',
}

const LOCALE_META: Record<string, string> = {
  en: 'en_US',
  zh: 'zh_CN',
  sr: 'sr_RS',
  pl: 'pl_PL',
}

const HREFLANG: Record<LocaleCode, string> = {
  en: 'en',
  zh: 'zh-CN',
  sr: 'sr-RS',
  pl: 'pl-PL',
}

const DEFAULT_REGION: Record<string, any> = {
  RS: { name: 'Serbia', cities: ['Belgrade', 'Novi Sad'] },
  PL: { name: 'Poland', cities: ['Warsaw', 'Krakow'] },
  RO: { name: 'Romania', cities: ['Bucharest', 'Cluj'] },
  PH: { name: 'Philippines', cities: ['Cebu', 'Manila'] },
  CN: { name: 'China', cities: ['Shenzhen', 'Guangzhou'] },
  NZ: { name: 'New Zealand', cities: ['Auckland', 'Wellington'] },
  AU: { name: 'Australia', cities: ['Sydney', 'Melbourne'] },
}

const REGION_LOCALE_COPY: Record<string, Partial<Record<LocaleCode, { name: string, cities: string[] }>>> = {
  RS: {
    en: { name: 'Serbia', cities: ['Belgrade', 'Novi Sad'] },
    zh: { name: '塞尔维亚', cities: ['贝尔格莱德', '诺维萨德'] },
    sr: { name: 'Srbiju', cities: ['Beograd', 'Novi Sad'] },
    pl: { name: 'Serbii', cities: ['Belgrad', 'Nowy Sad'] },
  },
  PL: {
    en: { name: 'Poland', cities: ['Warsaw', 'Krakow'] },
    zh: { name: '波兰', cities: ['华沙', '克拉科夫'] },
    sr: { name: 'Poljsku', cities: ['Varšava', 'Krakov'] },
    pl: { name: 'Polski', cities: ['Warszawa', 'Kraków'] },
  },
  RO: {
    en: { name: 'Romania', cities: ['Bucharest', 'Cluj'] },
    zh: { name: '罗马尼亚', cities: ['布加勒斯特', '克卢日'] },
    sr: { name: 'Rumuniju', cities: ['Bukurešt', 'Kluž'] },
    pl: { name: 'Rumunii', cities: ['Bukareszt', 'Kluż'] },
  },
  PH: {
    en: { name: 'Philippines', cities: ['Cebu', 'Manila'] },
    zh: { name: '菲律宾', cities: ['宿务', '马尼拉'] },
    sr: { name: 'Filipine', cities: ['Sebu', 'Manila'] },
    pl: { name: 'Filipin', cities: ['Cebu', 'Manila'] },
  },
}

const SITE_COPY: Record<string, SeoPageCopy> = {
  '/': {
    title: {
      en: 'AinerWise | AI Smart Building, Procurement and Lifecycle Service',
      zh: 'AinerWise | AI 智能建筑、采购与全生命周期服务',
      sr: 'AinerWise | AI pametne zgrade, nabavka i servis',
      pl: 'AinerWise | AI inteligentne budynki, zakupy i serwis',
    },
    description: {
      en: 'Tell AinerWise what you need. AI helps design, source, compare, procure, deliver and maintain smart building solutions.',
      zh: '告诉 AinerWise 你的需求，AI 协助完成方案设计、采购比价、交付安装和长期维护。',
      sr: 'Recite AinerWise šta vam treba. AI pomaže u dizajnu, nabavci, poređenju, isporuci i održavanju pametnih zgrada.',
      pl: 'Powiedz AinerWise, czego potrzebujesz. AI pomaga projektować, kupować, porównywać, wdrażać i utrzymywać inteligentne budynki.',
    },
  },
  '/solutions': {
    title: {
      en: 'Smart Building Solutions | AinerWise',
      zh: '智能建筑解决方案 | AinerWise',
      sr: 'Rešenja za pametne zgrade | AinerWise',
      pl: 'Rozwiązania inteligentnych budynków | AinerWise',
    },
    description: {
      en: 'AI-assisted smart building solutions for villas, hotels, offices, retail, solar, energy, CCTV, access control, HVAC and KNX projects.',
      zh: '面向别墅、酒店、办公室、零售、光伏、能源、监控、门禁、暖通和 KNX 项目的 AI 智能建筑解决方案。',
      sr: 'AI rešenja za vile, hotele, kancelarije, maloprodaju, solar, energiju, CCTV, pristup, HVAC i KNX projekte.',
      pl: 'Rozwiązania AI dla willi, hoteli, biur, sklepów, fotowoltaiki, energii, CCTV, kontroli dostępu, HVAC i KNX.',
    },
  },
  '/products': {
    title: {
      en: 'Verified Smart Building Product Catalog | AinerWise',
      zh: '认证智能建筑产品目录 | AinerWise',
      sr: 'Provereni katalog proizvoda za pametne zgrade | AinerWise',
      pl: 'Zweryfikowany katalog produktów smart building | AinerWise',
    },
    description: {
      en: 'Explore verified smart building hardware with AI procurement, China supply chain, local installation and lifecycle support.',
      zh: '浏览认证智能建筑硬件，支持 AI 采购、中国供应链、本地安装和生命周期服务。',
      sr: 'Pregledajte provereni hardver za pametne zgrade uz AI nabavku, kineski lanac dobave, lokalnu instalaciju i servis.',
      pl: 'Przeglądaj zweryfikowany sprzęt smart building z zakupami AI, chińskim łańcuchem dostaw, lokalnym montażem i serwisem.',
    },
  },
  '/ai-building-brain': {
    title: {
      en: 'AI Building Brain L1-L6 | AinerWise',
      zh: 'AI 建筑大脑 L1-L6 | AinerWise',
      sr: 'AI mozak zgrade L1-L6 | AinerWise',
      pl: 'AI mózg budynku L1-L6 | AinerWise',
    },
    description: {
      en: 'Understand the AinerWise AI Building Brain: connected control, sensors, optimization, AI assistance, local AI and autonomous operations.',
      zh: '了解 AinerWise AI 建筑大脑：联网控制、传感器、优化运行、AI 辅助、本地 AI 与未来自主运营。',
      sr: 'Upoznajte AinerWise AI mozak zgrade: kontrola, senzori, optimizacija, AI asistencija, lokalni AI i autonomne operacije.',
      pl: 'Poznaj AinerWise AI Building Brain: sterowanie, sensory, optymalizacja, asysta AI, lokalne AI i autonomiczne operacje.',
    },
  },
  '/services': {
    title: {
      en: 'Smart Building Service Packages | AinerWise',
      zh: '智能建筑服务套餐 | AinerWise',
      sr: 'Servisni paketi za pametne zgrade | AinerWise',
      pl: 'Pakiety serwisowe smart building | AinerWise',
    },
    description: {
      en: 'Installation, commissioning, remote support, preventive maintenance, AMC and lifecycle upgrade packages for smart buildings.',
      zh: '智能建筑安装、调试、远程支持、预防性维护、AMC 和生命周期升级服务套餐。',
      sr: 'Instalacija, puštanje u rad, daljinska podrška, preventivno održavanje, AMC i nadogradnje za pametne zgrade.',
      pl: 'Instalacja, uruchomienie, wsparcie zdalne, konserwacja, AMC i modernizacje cyklu życia dla smart building.',
    },
  },
  '/submit-requirement': {
    title: {
      en: 'Submit a Smart Building Requirement | AinerWise',
      zh: '提交智能建筑需求 | AinerWise',
      sr: 'Pošaljite zahtev za pametnu zgradu | AinerWise',
      pl: 'Wyślij wymagania smart building | AinerWise',
    },
    description: {
      en: 'Start with a requirement. AinerWise AI collects facts, finds missing details, drafts BOQ and routes the project for review.',
      zh: '从一句需求开始。AinerWise AI 收集事实、追问缺口、生成 BOQ 草案，并进入人工审核。',
      sr: 'Počnite od zahteva. AinerWise AI prikuplja činjenice, nalazi praznine, pravi BOQ nacrt i šalje na pregled.',
      pl: 'Zacznij od wymagań. AinerWise AI zbiera fakty, wykrywa braki, tworzy szkic BOQ i kieruje projekt do weryfikacji.',
    },
  },
  '/about': {
    title: {
      en: 'About AinerWise | AI Solution & Procurement Platform',
      zh: '关于 AinerWise | AI 方案与采购平台',
      sr: 'O AinerWise | AI platforma za rešenja i nabavku',
      pl: 'O AinerWise | Platforma AI rozwiązań i zakupów',
    },
    description: {
      en: 'AinerWise is the customer experience layer for AI shopping, procurement, smart building solutions, delivery and lifecycle service.',
      zh: 'AinerWise 是面向客户的 AI Shopping、AI Procurement、智能建筑方案、交付和生命周期服务入口。',
      sr: 'AinerWise je korisnički sloj za AI kupovinu, nabavku, rešenja za pametne zgrade, isporuku i servis.',
      pl: 'AinerWise to warstwa klienta dla zakupów AI, zakupów, rozwiązań smart building, dostaw i serwisu.',
    },
  },
  '/contact': {
    title: {
      en: 'Contact AinerWise | Smart Building Project Intake',
      zh: '联系 AinerWise | 智能建筑项目咨询',
      sr: 'Kontakt AinerWise | Upit za projekat pametne zgrade',
      pl: 'Kontakt AinerWise | Zapytanie o projekt smart building',
    },
    description: {
      en: 'Contact AinerWise for smart building, AI procurement, supplier, partner, installation and lifecycle support inquiries.',
      zh: '联系 AinerWise，咨询智能建筑、AI 采购、供应商、合作伙伴、安装和生命周期服务。',
      sr: 'Kontaktirajte AinerWise za pametne zgrade, AI nabavku, dobavljače, partnere, instalaciju i servis.',
      pl: 'Skontaktuj się z AinerWise w sprawie smart building, zakupów AI, dostawców, partnerów, montażu i serwisu.',
    },
  },
}

function stripLocalePrefix(path: string) {
  const clean = path.split('?')[0].split('#')[0] || '/'
  const next = clean.replace(/^\/(en|cn|rs|pl)(?=\/|$)/, '') || '/'
  return next === '' ? '/' : next
}

function bestPageKey(path: string) {
  const normalized = stripLocalePrefix(path)
  if (normalized.startsWith('/products/')) return '/products'
  if (normalized.startsWith('/solutions/')) return '/solutions'
  if (normalized.startsWith('/ai-building-brain/')) return '/ai-building-brain'
  return SITE_COPY[normalized] ? normalized : '/'
}

function apiBaseForServer() {
  const config = useRuntimeConfig()
  const configured = String(config.public.apiBase || 'http://localhost:8000/api/v1').replace(/\/$/, '')
  try {
    const url = new URL(configured)
    if (import.meta.server && (url.hostname === 'localhost' || url.hostname === '127.0.0.1')) {
      url.hostname = 'backend'
    }
    return url.toString().replace(/\/$/, '')
  } catch {
    return configured
  }
}

function withLocale(path: string, locale: string) {
  const normalized = stripLocalePrefix(path)
  const prefix = LOCALE_PREFIX[(locale as LocaleCode) || 'en'] || locale
  return `/${prefix}${normalized === '/' ? '' : normalized}`
}

function pickRegion(config: any, cookieValue?: string | null) {
  const code = String(cookieValue || config?.default_region_code || 'RS').toUpperCase()
  return {
    code,
    ...(DEFAULT_REGION[code] || { name: code, cities: [] }),
    ...(config?.region_overrides?.[code] || {}),
  }
}

function displayRegion(locale: LocaleCode, region: any) {
  const localized = REGION_LOCALE_COPY[region.code]?.[locale]
  const overrideNames = region.localized_names && typeof region.localized_names === 'object' ? region.localized_names : {}
  const overrideCities = region.localized_cities && typeof region.localized_cities === 'object' ? region.localized_cities : {}
  return {
    name: overrideNames[locale] || localized?.name || region.name || region.code,
    cities: Array.isArray(overrideCities[locale])
      ? overrideCities[locale]
      : (localized?.cities || region.cities || []),
  }
}

function regionPhrase(locale: string, region: any) {
  const display = displayRegion((locale as LocaleCode) || 'en', region)
  const cityPart = Array.isArray(display.cities) && display.cities.length ? ` (${display.cities.join(', ')})` : ''
  const name = display.name
  const phrases: Record<string, string> = {
    zh: `面向${name}${cityPart}本地项目优化，覆盖本地服务、采购、安装和长期维护。`,
    sr: `Optimizovano za ${name}${cityPart}: lokalni servis, nabavka, instalacija i dugoročno održavanje.`,
    pl: `Zoptymalizowane dla ${name}${cityPart}: lokalny serwis, zakupy, montaż i utrzymanie.`,
    en: `Optimized for ${name}${cityPart}: local service, procurement, installation and lifecycle support.`,
  }
  return phrases[locale] || phrases.en
}

export async function useAinerwiseSeo() {
  const route = useRoute()
  const requestUrl = useRequestURL()
  const { locale } = useI18n({ useScope: 'global' })
  const regionCookie = useCookie<string | null>('ainerwise_region_code', { sameSite: 'lax' })

  const { data } = await useAsyncData(
    'ainerwise-public-seo-config',
    () => $fetch<any>(`${apiBaseForServer()}/seo/config`).catch(() => null),
    { default: () => null },
  )

  const seoConfig = computed(() => data.value || {})
  const activeLocale = computed(() => (['en', 'zh', 'sr', 'pl'].includes(locale.value) ? locale.value : 'en') as LocaleCode)
  const normalizedPath = computed(() => stripLocalePrefix(route.path))
  const pageKey = computed(() => bestPageKey(route.path))
  const pageCopy = computed(() => SITE_COPY[pageKey.value] || SITE_COPY['/'])
  const pageOverride = computed(() => seoConfig.value?.page_overrides?.[normalizedPath.value] || seoConfig.value?.page_overrides?.[pageKey.value] || {})
  const region = computed(() => pickRegion(seoConfig.value, regionCookie.value))
  const enabledLocales = computed(() => {
    const configured = Array.isArray(seoConfig.value?.enabled_locales) ? seoConfig.value.enabled_locales : ['en', 'zh', 'sr', 'pl']
    return configured.filter((item: string) => ['en', 'zh', 'sr', 'pl'].includes(item))
  })
  const canonicalUrl = computed(() => new URL(withLocale(route.path, activeLocale.value), requestUrl.origin).toString())
  const title = computed(() => pageOverride.value?.title?.[activeLocale.value] || pageCopy.value.title[activeLocale.value] || pageCopy.value.title.en)
  const description = computed(() => {
    const base = pageOverride.value?.description?.[activeLocale.value] || pageCopy.value.description[activeLocale.value] || pageCopy.value.description.en
    return `${base} ${regionPhrase(activeLocale.value, region.value)}`.slice(0, 300)
  })

  useSeoMeta({
    title: () => title.value,
    description: () => description.value,
    ogTitle: () => title.value,
    ogDescription: () => description.value,
    ogType: 'website',
    ogUrl: () => canonicalUrl.value,
    ogLocale: () => LOCALE_META[activeLocale.value] || 'en_US',
    twitterCard: 'summary_large_image',
    twitterTitle: () => title.value,
    twitterDescription: () => description.value,
  })

  useHead(() => ({
    htmlAttrs: {
      lang: HREFLANG[activeLocale.value],
    },
    link: [
      { key: 'canonical', rel: 'canonical', href: canonicalUrl.value },
      ...enabledLocales.value.map((code: string) => ({
        key: `alternate-${code}`,
        rel: 'alternate',
        hreflang: HREFLANG[code as LocaleCode] || code,
        href: new URL(withLocale(route.path, code), requestUrl.origin).toString(),
      })),
      {
        key: 'alternate-x-default',
        rel: 'alternate',
        hreflang: 'x-default',
        href: new URL(withLocale(route.path, 'en'), requestUrl.origin).toString(),
      },
    ],
    meta: [
      { key: 'geo-region', name: 'geo.region', content: region.value.code },
      { key: 'audience', name: 'audience', content: 'business, property owners, hotels, villas, facility managers, integrators' },
    ],
  }))
}
