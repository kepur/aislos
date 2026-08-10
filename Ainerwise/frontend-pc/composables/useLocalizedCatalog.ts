/**
 * Localize catalogue records that still arrive from the API in English.
 * Falls back to the API string when no i18n key exists.
 */

export function useLocalizedCatalog() {
  const { t, te, tm, rt } = useI18n({ useScope: 'global' })

  function tx(key: string, fallback: string) {
    return te(key) ? t(key) : fallback
  }

  function localizeSolution(solution: any) {
    if (!solution?.slug) return solution
    const base = `solutions.bySlug.${solution.slug}`
    const scenariosKey = `${base}.scenarios`
    const scenarios = te(scenariosKey)
      ? asStringList(tm(scenariosKey), rt)
      : solution.target_scenarios_json
    return {
      ...solution,
      title: tx(`${base}.title`, solution.title),
      description: tx(`${base}.description`, solution.description),
      target_scenarios_json: scenarios,
    }
  }

  function localizeCategory(category: any) {
    if (!category?.slug) return category
    return {
      ...category,
      name: tx(`products.categories.${category.slug}`, category.name),
    }
  }

  function localizeProduct(product: any) {
    if (!product?.slug) return product
    return {
      ...product,
      name: tx(`products.items.${product.slug}.name`, product.name),
    }
  }

  return { localizeSolution, localizeCategory, localizeProduct, tx }
}

/** vue-i18n `tm()` array items need `rt()` to become display strings. */
function asStringList(raw: unknown, rt: (message: unknown) => string): string[] {
  const values = Array.isArray(raw)
    ? raw
    : raw && typeof raw === 'object'
      ? Object.values(raw as Record<string, unknown>)
      : []
  return values
    .map((item) => {
      if (typeof item === 'string') return item
      if (item == null) return ''
      try {
        const resolved = rt(item)
        if (typeof resolved === 'string' && resolved && resolved !== '[object Object]') return resolved
      } catch {
        /* fall through */
      }
      return ''
    })
    .filter(Boolean)
}
