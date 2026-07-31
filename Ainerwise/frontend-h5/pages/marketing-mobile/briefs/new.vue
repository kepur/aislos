<template>
  <div class="space-y-4 p-4">
    <div>
      <NuxtLink to="/marketing-mobile/briefs" class="text-xs font-semibold text-violet-600">Back to briefs</NuxtLink>
      <h1 class="mt-2 text-xl font-bold text-slate-900">Create creative brief</h1>
    </div>
    <form class="m-card space-y-3" @submit.prevent="submit">
      <input v-model.trim="form.title" required class="m-input" placeholder="Brief title" />
      <textarea v-model.trim="form.objective" required rows="3" class="m-input" placeholder="Business objective" />
      <textarea v-model.trim="form.headline" required rows="3" class="m-input" placeholder="Approved copy or headline" />
      <input v-model.trim="form.audience" class="m-input" placeholder="Audience segment" />
      <input v-model.trim="form.tone" class="m-input" placeholder="Brand tone" />
      <div class="grid grid-cols-2 gap-2">
        <select v-model="form.media_type" class="m-input"><option>image</option><option>video</option><option>audio</option></select>
        <select v-model="form.channel" class="m-input"><option>instagram</option><option>linkedin</option><option>facebook</option><option>email</option></select>
      </div>
      <p class="rounded-xl bg-violet-50 p-3 text-[11px] text-violet-700">The approved brief is exported through the standard API. AinerN2D remains an independent media engine.</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      <button :disabled="busy" class="m-btn-primary bg-violet-600">Create draft</button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'marketing-mobile' })
const api = useMarketingMobile()
const busy = ref(false)
const error = ref('')
const form = reactive({ title: '', objective: '', headline: '', audience: '', tone: '', media_type: 'image', channel: 'instagram' })
async function submit() {
  busy.value = true
  error.value = ''
  try {
    const brief = await api.createBrief({
      title: form.title,
      objective: form.objective,
      version: {
        copy_json: { headline: form.headline },
        audience_json: { segment: form.audience },
        brand_constraints_json: { tone: form.tone },
        deliverables_json: [{
          key: `${form.channel}-${form.media_type}`,
          media_type: form.media_type,
          channel: form.channel,
          language: 'en',
          format: form.media_type === 'video' ? 'mp4' : 'png',
          variant_count: 1,
        }],
        compliance_json: {},
      },
    })
    await navigateTo(`/marketing-mobile/briefs/${brief.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}
</script>

