type SitemapProduct = {
  slug?: string
  updated_at?: string
  created_at?: string
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

export default defineEventHandler(async (event) => {
  const origin = getRequestURL(event).origin
  const now = new Date().toISOString()
  const urls: Array<{ loc: string; lastmod?: string; priority?: string; changefreq?: string }> = [
    { loc: '/', priority: '1.0', changefreq: 'daily' },
    { loc: '/products', priority: '0.9', changefreq: 'daily' },
    { loc: '/solutions', priority: '0.8', changefreq: 'weekly' },
    { loc: '/ai-building-brain', priority: '0.8', changefreq: 'weekly' },
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

  const body = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls.map((item) => [
      '  <url>',
      `    <loc>${escapeXml(new URL(item.loc, origin).toString())}</loc>`,
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
