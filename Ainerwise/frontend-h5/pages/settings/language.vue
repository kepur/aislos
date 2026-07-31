<template>
  <div class="space-y-4 p-4">
    <h1 class="text-xl font-bold text-slate-800">Language</h1>
    <div class="m-card space-y-2">
      <button v-for="item in languages" :key="item.code" class="flex w-full items-center justify-between rounded-xl px-3 py-3 text-left" :class="language === item.code ? 'bg-blue-50 text-blue-600' : 'text-slate-700'" @click="select(item.code)">
        <span class="font-medium">{{ item.name }}</span>
        <span v-if="language === item.code">Selected</span>
      </button>
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })
const api = useCommerce()
const language = ref('en')
const message = ref('')
const error = ref('')
const languages = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'tl', name: 'Filipino' },
]
async function select(code: string) {
  error.value = ''
  try {
    await api.updateBuyerAccount({ language: code })
    language.value = code
    message.value = 'Language preference saved.'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to save language.'
  }
}
onMounted(async () => {
  try {
    language.value = (await api.getBuyerAccount()).user.language || 'en'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to load language.'
  }
})
</script>
