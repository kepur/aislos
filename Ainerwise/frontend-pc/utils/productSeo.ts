export type SeoProduct = {
  id?: string
  name?: string
  public_name?: string | null
  slug?: string
  brand?: string | null
  description?: string | null
  images_json?: string[] | null
  image_url?: string | null
  list_price?: number | string | null
  currency?: string | null
  moq?: number | null
  warranty_years?: number | null
  service_available?: boolean | null
  supply_tier?: string | null
  scenario_tags_json?: string[] | null
  certifications_json?: string[] | null
}

const SITE_NAME = 'AinerWise'
const DEFAULT_DESCRIPTION =
  'AinerWise verified smart building products, AI procurement, local service, installation and lifecycle support.'

export function cleanSeoText(value?: string | null) {
  return String(value || '').replace(/\s+/g, ' ').trim()
}

export function truncateSeo(value: string, max = 155) {
  const text = cleanSeoText(value)
  if (text.length <= max) return text
  return `${text.slice(0, Math.max(0, max - 1)).trim()}...`
}

export function firstProductImage(product?: SeoProduct | null) {
  const images = Array.isArray(product?.images_json) ? product?.images_json : []
  return images?.[0] || product?.image_url || ''
}

export function productDisplayName(product?: SeoProduct | null) {
  return cleanSeoText(product?.public_name || product?.name || 'AinerWise Product')
}

export function productSeoTitle(product?: SeoProduct | null) {
  const name = productDisplayName(product)
  const brand = cleanSeoText(product?.brand)
  const prefix = brand && !name.toLowerCase().includes(brand.toLowerCase())
    ? `${brand} ${name}`
    : name
  return truncateSeo(`${prefix} | Smart Building Product | ${SITE_NAME}`, 70)
}

export function productSeoDescription(product?: SeoProduct | null) {
  const parts = [
    product?.description,
    product?.supply_tier,
    product?.service_available ? 'Includes local service and lifecycle support.' : '',
  ].map(cleanSeoText).filter(Boolean)
  return truncateSeo(parts.join(' ') || DEFAULT_DESCRIPTION)
}

export function absoluteSeoUrl(pathOrUrl: string, origin: string) {
  if (!pathOrUrl) return ''
  try {
    return new URL(pathOrUrl, origin).toString()
  } catch {
    return pathOrUrl
  }
}

export function productJsonLd(product: SeoProduct, canonicalUrl: string, origin: string) {
  const image = firstProductImage(product)
  const data: Record<string, any> = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: productDisplayName(product),
    description: productSeoDescription(product),
    sku: product.slug || product.id,
    url: canonicalUrl,
  }
  if (product.brand) {
    data.brand = { '@type': 'Brand', name: cleanSeoText(product.brand) }
  }
  if (image) {
    data.image = [absoluteSeoUrl(image, origin)]
  }
  if (product.list_price) {
    data.offers = {
      '@type': 'Offer',
      price: String(product.list_price),
      priceCurrency: product.currency || 'EUR',
      availability: 'https://schema.org/InStock',
      url: canonicalUrl,
    }
  }
  if (product.moq) {
    data.minimumOrderQuantity = product.moq
  }
  return data
}

export function productItemListJsonLd(products: SeoProduct[], canonicalUrl: string, origin: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'AinerWise Product Catalog',
    url: canonicalUrl,
    itemListElement: products.slice(0, 50).map((product, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      url: absoluteSeoUrl(`/products/${product.slug || product.id}`, origin),
      name: productDisplayName(product),
    })),
  }
}
