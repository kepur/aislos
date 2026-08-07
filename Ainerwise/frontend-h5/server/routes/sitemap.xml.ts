type SitemapProduct = {
  slug?: string
  updated_at?: string
  created_at?: string
}

type SitemapUrl = {
  loc: string
  baseLoc?: string
  lastmod?: string
  priority?: string
  changefreq?: string
}

const LOCALE_PREFIX: Record<string, string> = {
  en: 'en',
  zh: 'cn',
  sr: 'rs',
  pl: 'pl',
}

function escapeXml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function serverApiBase() {
  const config = useRuntimeConfig()
  const configured = String(config.public.apiBase || 'http://localhost:8000/api/v1').replace(/\/$/, '')
  try {
    const url = new URL(configured)
    if (url.hostname === 'localhost' || url.hostname === '127.0.0.1') {
      url.hostname = 'backend'
    }
    return url.toString().replace(/\/$/, '')
  } catch {
    return configured
  }
}

async function enabledLocales() {
  try {
    const res = await $fetch<any>(`${serverApiBase()}/seo/config`)
    const locales = Array.isArray(res?.enabled_locales) ? res.enabled_locales : []
    const filtered = locales.filter((locale: string) => LOCALE_PREFIX[locale])
    return filtered.length ? filtered : ['en', 'zh', 'sr', 'pl']
  } catch {
    return ['en', 'zh', 'sr', 'pl']
  }
}

function withLocale(path: string, locale: string) {
  const prefix = LOCALE_PREFIX[locale] || locale
  return `/${prefix}${path === '/' ? '' : path}`
}

function hrefLang(locale: string) {
  if (locale === 'zh') return 'zh-CN'
  if (locale === 'sr') return 'sr-RS'
  if (locale === 'pl') return 'pl-PL'
  return 'en'
}

function expandLocalizedUrls(urls: SitemapUrl[], locales: string[]): SitemapUrl[] {
  const expanded: SitemapUrl[] = []
  for (const item of urls) {
    expanded.push({ ...item, baseLoc: item.loc })
    for (const locale of locales) {
      expanded.push({ ...item, loc: withLocale(item.loc, locale), baseLoc: item.loc })
    }
  }
  return expanded
}

function alternateXml(item: SitemapUrl, origin: string, locales: string[]) {
  const base = item.baseLoc || item.loc
  const links = locales.map(locale =>
    `    <xhtml:link rel="alternate" hreflang="${hrefLang(locale)}" href="${escapeXml(new URL(withLocale(base, locale), origin).toString())}" />`)
  links.push(`    <xhtml:link rel="alternate" hreflang="x-default" href="${escapeXml(new URL(withLocale(base, 'en'), origin).toString())}" />`)
  return links
}

export default defineEventHandler(async (event) => {
  const origin = getRequestURL(event).origin
  const now = new Date().toISOString()
  const locales = await enabledLocales()
  const urls: SitemapUrl[] = [
    { loc: '/', priority: '1.0', changefreq: 'daily' },
    { loc: '/products', priority: '0.9', changefreq: 'daily' },
    { loc: '/solutions', priority: '0.8', changefreq: 'weekly' },
    { loc: '/ai-brain', priority: '0.8', changefreq: 'weekly' },
    { loc: '/submit-requirement', priority: '0.7', changefreq: 'monthly' },
  ]

  try {
    const res = await $fetch<{ items?: SitemapProduct[] } | SitemapProduct[]>(`${serverApiBase()}/products?limit=100`)
    const products = Array.isArray(res) ? res : res.items || []
    for (const product of products) {
      if (!product.slug) continue
      urls.push({
        loc: `/products/${product.slug}`,
        lastmod: product.updated_at || product.created_at || now,
        priority: '0.8',
        changefreq: 'weekly',
      })
    }
  } catch {
    // Keep the sitemap valid even when the API is temporarily unavailable.
  }

  const localizedUrls = expandLocalizedUrls(urls, locales)
  const body = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ...localizedUrls.map((item) => [
      '  <url>',
      `    <loc>${escapeXml(new URL(item.loc, origin).toString())}</loc>`,
      ...alternateXml(item, origin, locales),
      `    <lastmod>${escapeXml(item.lastmod || now)}</lastmod>`,
      item.changefreq ? `    <changefreq>${item.changefreq}</changefreq>` : '',
      item.priority ? `    <priority>${item.priority}</priority>` : '',
      '  </url>',
    ].filter(Boolean).join('\n')),
    '</urlset>',
    '',
  ].join('\n')

  setHeader(event, 'Content-Type', 'application/xml; charset=utf-8')
  return body
})
