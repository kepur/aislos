<template>
  <article v-if="page" class="max-w-3xl mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold text-gray-900 mb-6">{{ page.title }}</h1>
    <div class="prose-content text-gray-700 leading-relaxed space-y-4">
      <template v-for="(block, i) in blocks" :key="i">
        <h2 v-if="block.type === 'h2'" class="text-xl font-semibold text-gray-900 mt-8">{{ block.text }}</h2>
        <h3 v-else-if="block.type === 'h3'" class="text-lg font-semibold text-gray-900 mt-6">{{ block.text }}</h3>
        <ul v-else-if="block.type === 'ul'" class="list-disc pl-6 space-y-1">
          <li v-for="(item, j) in block.items" :key="j">{{ item }}</li>
        </ul>
        <p v-else>{{ block.text }}</p>
      </template>
    </div>
    <div class="mt-12 border-t pt-6 text-sm text-gray-500">
      <p v-if="page.ai_generated" class="mb-3">{{ $t('insights.aiNotice') }}</p>
      <NuxtLink to="/submit-requirement" class="inline-block bg-gray-900 text-white rounded-xl px-5 py-2.5 text-sm font-medium hover:bg-gray-700">
        {{ $t('insights.cta') }}
      </NuxtLink>
    </div>
  </article>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiFetch } = useApi()

const { data: page } = await useAsyncData(`insight-${route.params.slug}`, () =>
  apiFetch<any>(`/seo/pages/${route.params.slug}`).catch(() => null),
)

if (!page.value) {
  throw createError({ statusCode: 404, statusMessage: 'Page not found' })
}

const blocks = computed(() => {
  const out: any[] = []
  let list: string[] | null = null
  for (const raw of (page.value?.content_md || '').split('\n')) {
    const line = raw.trim()
    if (line.startsWith('- ') || line.startsWith('* ')) {
      if (!list) { list = []; out.push({ type: 'ul', items: list }) }
      list.push(line.slice(2))
      continue
    }
    list = null
    if (!line) continue
    if (line.startsWith('### ')) out.push({ type: 'h3', text: line.slice(4) })
    else if (line.startsWith('## ')) out.push({ type: 'h2', text: line.slice(3) })
    else if (line.startsWith('# ')) continue
    else out.push({ type: 'p', text: line })
  }
  return out
})

useHead(() => ({
  title: `${page.value?.title} — AinerWise`,
  meta: [{ name: 'description', content: page.value?.meta_description || '' }],
}))
</script>
