<script setup lang="ts">
/**
 * The standalone supplier marketplace is now a filter on the unified catalogue
 * rather than a page of its own — same listings, same category rail, same
 * verified/trust controls, plus the official products alongside them.
 *
 * The route stays as a redirect because it is linked from the buyer workspace,
 * older emails and the 4106 site. Listing detail pages under
 * /market/marketplace/[id] are untouched.
 */
import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

const route = useRoute()
const prefix = getLocalePrefixFromPath(route.path)
const target = prefix ? withLocalePrefix('/catalog', prefix) : '/catalog'

// Carry the visitor's filters across so a bookmarked marketplace URL still
// lands on the same slice of the catalogue.
const query: Record<string, string> = { source: 'supplier' }
if (route.query.q) query.keyword = String(route.query.q)
if (route.query.keyword) query.keyword = String(route.query.keyword)
if (route.query.category_schema_id) query.category_id = String(route.query.category_schema_id)
if (route.query.market_mode) query.market_mode = String(route.query.market_mode)
if (route.query.sort === 'trust') query.sort = 'trust'

await navigateTo({ path: target, query }, { redirectCode: 302, replace: true })
</script>

<template>
  <div />
</template>
