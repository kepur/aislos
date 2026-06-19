<template>
  <div class="space-y-4">
    <!-- Tab switcher -->
    <div class="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
      <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
        :class="activeTab === tab.id ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-700'">
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Review Queue -->
    <div v-if="activeTab === 'queue'" class="space-y-4">
    <p class="text-sm text-slate-500">{{ $t('verification.desc') }}</p>

    <div v-if="!loading && !queue.length" class="card p-12 text-center">
      <p class="text-3xl mb-2">✅</p>
      <p class="font-medium text-slate-700">{{ $t('verification.noPending') }}</p>
    </div>

    <div v-else class="space-y-4">
      <div v-if="loading" v-for="n in 3" :key="n" class="card p-5 animate-pulse"><div class="h-4 bg-slate-100 rounded w-1/2 mb-2"></div><div class="h-3 bg-slate-100 rounded w-3/4"></div></div>

      <div v-for="item in queue" :key="item.id" class="card p-5">
        <div class="flex items-start justify-between mb-3">
          <div>
            <p class="font-semibold text-slate-900">{{ $t('companies.name') }}: {{ item.company_id?.slice(0,8) }}</p>
            <p class="text-xs text-slate-400">{{ $t('verification.submitted') }} {{ fmtRelative(item.created_at) }}</p>
          </div>
          <span :class="statusBadge(item.status)" class="badge">{{ item.status }}</span>
        </div>

        <div v-if="item._docs" class="mb-4 space-y-2">
          <div v-for="doc in item._docs" :key="doc.id" class="bg-slate-50 rounded-lg p-3 space-y-2">
            <div class="flex items-center gap-3 flex-wrap">
              <span>📄</span>
              <div class="flex-1">
                <p class="text-sm font-medium text-slate-700">{{ doc.doc_type }}</p>
                <p class="text-xs text-slate-400">{{ doc.original_filename || 'No filename' }}</p>
              </div>
              <span :class="doc.status==='APPROVED'?'badge-green':doc.status==='REJECTED'?'badge-red':'badge-amber'" class="badge">{{ doc.status }}</span>
              <a v-if="doc.file_url" :href="doc.file_url" target="_blank" class="text-xs text-primary-600 font-medium hover:underline">{{ $t('common.view') }}</a>
              <button v-if="aiKycEnabled && !doc._aiResult" class="btn badge-blue text-xs px-2 py-1" :disabled="doc._analyzing" @click="analyzeDoc(doc)">
                {{ doc._analyzing ? $t('ai.analyzing') : $t('ai.analyze') }}
              </button>
              <button v-if="doc.status !== 'REJECTED'" class="text-xs text-red-500 font-medium hover:underline" @click="flagRisk(doc)">🚩 Flag Risk</button>
            </div>
            <!-- AI Analysis Result -->
            <div v-if="doc._aiResult" class="mt-2 border-t border-slate-200 pt-2 space-y-1 text-xs">
              <div v-if="!doc._aiResult.ok" class="text-red-600">{{ doc._aiResult.error }}</div>
              <template v-else-if="doc._aiResult.analysis">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-semibold text-slate-700">{{ $t('ai.authenticity') }}:</span>
                  <span :class="authBadge(doc._aiResult.analysis.authenticity)" class="badge">
                    {{ authLabel(doc._aiResult.analysis.authenticity) }}
                  </span>
                  <span class="text-slate-500">{{ $t('ai.confidence_label') }}: {{ Math.round((doc._aiResult.analysis.confidence||0)*100) }}%</span>
                  <span v-if="doc._aiResult.analysis.tamper_suspected" class="badge badge-red">⚠️ Tamper suspected</span>
                  <span v-if="doc._aiResult.analysis.photoshop_suspected" class="badge badge-red">🎨 PS suspected</span>
                  <span v-if="doc._aiResult.analysis.text_photo_consistency === false" class="badge badge-amber">📝 Text/photo mismatch</span>
                </div>
                <div v-if="doc._aiResult.analysis.summary" class="text-slate-600 italic">"{{ doc._aiResult.analysis.summary }}"</div>
                <div v-if="doc._aiResult.analysis.extracted_fields" class="grid grid-cols-2 gap-1 mt-1 text-slate-700">
                  <div v-for="(v,k) in doc._aiResult.analysis.extracted_fields" :key="k" v-show="v">
                    <span class="text-slate-400">{{ k }}:</span> {{ v }}
                  </div>
                </div>
                <div v-if="doc._aiResult.analysis.concerns?.length" class="mt-1">
                  <p class="text-amber-700 font-medium">{{ $t('ai.analysis') }}:</p>
                  <ul class="list-disc list-inside text-amber-600">
                    <li v-for="(c,i) in doc._aiResult.analysis.concerns" :key="i">{{ c }}</li>
                  </ul>
                </div>
              </template>
            </div>
          </div>
          <p v-if="!item._docs.length" class="text-xs text-slate-400">{{ $t('verification.noDocsYet') }}</p>
        </div>
        <button v-else class="btn btn-secondary text-xs mb-4" @click="loadDocs(item)">{{ $t('verification.loadDocs') }}</button>

        <div v-if="item.status === 'SUBMITTED'" class="flex gap-2 pt-3 border-t border-slate-100">
          <button class="btn btn-success flex-1 text-xs py-2" @click="decide(item.company_id, 'APPROVED', 'Approved via admin console')">{{ $t('common.approve') }}</button>
          <button class="btn btn-danger flex-1 text-xs py-2" @click="decide(item.company_id, 'REJECTED', 'Rejected via admin console')">{{ $t('common.reject') }}</button>
          <button class="btn btn-secondary flex-1 text-xs py-2" @click="decide(item.company_id, 'NEEDS_INFO', 'Additional info needed')">{{ $t('verification.needInfo') }}</button>
        </div>
      </div>
    </div><!-- closes v-else list -->
    </div><!-- end tab:queue -->

    <!-- Tab: KYC Media Library -->
    <div v-if="activeTab === 'media'" class="space-y-4">
      <div class="flex items-center justify-between">
        <p class="text-sm text-slate-500">All uploaded KYC documents with AI analysis history.</p>
        <div class="flex gap-2">
          <select v-model="mediaFilter.status" class="input text-sm py-1.5 h-auto" @change="loadMedia">
            <option value="">All statuses</option>
            <option value="PENDING">Pending</option>
            <option value="ACCEPTED">Accepted</option>
            <option value="REJECTED">Rejected</option>
          </select>
          <button class="btn btn-secondary text-xs" :disabled="batchAnalyzing" @click="batchAnalyze">
            {{ batchAnalyzing ? 'Analyzing…' : '🤖 Batch Analyze (top 20)' }}
          </button>
        </div>
      </div>

      <div v-if="mediaLoading" class="space-y-2">
        <div v-for="n in 5" :key="n" class="card p-4 animate-pulse"><div class="h-4 bg-slate-100 rounded w-2/3"></div></div>
      </div>

      <div v-else-if="!mediaFiles.length" class="card p-10 text-center text-slate-400">No documents found.</div>

      <div v-else class="space-y-2">
        <div v-for="doc in mediaFiles" :key="doc.id" class="card p-4">
          <div class="flex items-start gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap mb-1">
                <span class="font-medium text-sm text-slate-800">{{ doc.doc_type || '—' }}</span>
                <span :class="docStatusBadge(doc.status)" class="badge">{{ doc.status }}</span>
                <span v-if="doc.latest_analysis" :class="authBadge(doc.latest_analysis.authenticity)" class="badge text-xs">AI: {{ doc.latest_analysis.authenticity }}</span>
                <span v-if="doc.latest_analysis?.risk_score > 0.5" class="badge badge-red text-xs">Risk {{ Math.round(doc.latest_analysis.risk_score * 100) }}%</span>
                <span v-if="doc.latest_analysis?.tamper_suspected" class="badge badge-red text-xs">⚠️ Tamper</span>
                <span v-if="doc.latest_analysis?.photoshop_suspected" class="badge badge-red text-xs">🎨 PS</span>
              </div>
              <p class="text-xs text-slate-400 truncate">{{ doc.original_filename || doc.file_url }}</p>
              <p class="text-xs text-slate-400">Company: {{ doc.company_id?.slice(0,8) }} · {{ fmtDate(doc.created_at) }}</p>
              <div v-if="doc.latest_analysis" class="mt-1 flex gap-3 text-xs text-slate-500">
                <span>Confidence: {{ Math.round((doc.latest_analysis.confidence || 0)*100) }}%</span>
                <span>Action: {{ doc.latest_analysis.recommended_action }}</span>
                <span>{{ fmtDate(doc.latest_analysis.created_at) }}</span>
              </div>
            </div>
            <div class="flex flex-col gap-1.5 flex-shrink-0">
              <a v-if="doc.file_url" :href="doc.file_url" target="_blank" class="btn btn-secondary text-xs py-1 px-2">View</a>
              <button class="btn btn-secondary text-xs py-1 px-2" :disabled="doc._analyzing" @click="analyzeMediaDoc(doc)">{{ doc._analyzing ? '…' : '🤖 AI' }}</button>
              <button v-if="doc.status !== 'REJECTED'" class="text-xs text-red-500 font-medium hover:underline px-1" @click="flagMediaRisk(doc)">🚩 Flag</button>
            </div>
          </div>
        </div>
      </div>
    </div><!-- end tab:media -->

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, fmtRelative, fmtDate } from '@/utils/api'

const props = defineProps({ initialTab: { type: String, default: 'queue' } })
const { t } = useI18n()
const activeTab = ref(props.initialTab)
const tabs = [
  { id: 'queue', label: '📋 Review Queue' },
  { id: 'media', label: '🗂️ KYC Media Library' },
]

const loading = ref(true)
const queue = ref([])
const aiKycEnabled = ref(false)

// Media library state
const mediaLoading = ref(false)
const mediaFiles = ref([])
const batchAnalyzing = ref(false)
const mediaFilter = reactive({ status: '', offset: 0 })

function statusBadge(s) {
  return { SUBMITTED:'badge-amber', APPROVED:'badge-green', REJECTED:'badge-red', NEEDS_INFO:'badge-blue' }[s] || 'badge-gray'
}
function docStatusBadge(s) {
  return { PENDING:'badge-amber', ACCEPTED:'badge-green', REJECTED:'badge-red' }[s] || 'badge-gray'
}
function authBadge(a) {
  return { AUTHENTIC:'badge-green', SUSPICIOUS:'badge-amber', FAKE:'badge-red' }[a] || 'badge-gray'
}
function authLabel(a) {
  return { AUTHENTIC: t('ai.authentic'), SUSPICIOUS: t('ai.suspicious'), FAKE: t('ai.fake') }[a] || a
}

async function loadDocs(item) {
  try {
    const { data } = await api.get(`/admin/verification/${item.company_id}/documents`)
    item._docs = data
  } catch { item._docs = [] }
}

async function analyzeDoc(doc) {
  doc._analyzing = true
  try {
    const { data } = await api.post('/admin/ai/analyze-kyc-document', { document_id: doc.id, doc_type: doc.doc_type })
    doc._aiResult = data
  } catch (e) {
    doc._aiResult = { ok: false, error: e.response?.data?.detail || 'Failed' }
  }
  doc._analyzing = false
}

async function flagRisk(doc) {
  const reason = prompt('Reason for flagging this document:')
  if (reason === null) return
  try {
    await api.post(`/admin/kyc-media/files/${doc.id}/flag-risk`, { reason })
    doc.status = 'REJECTED'
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function decide(companyId, decision, reason) {
  try {
    const { data } = await api.post(`/admin/verification/${companyId}/decide`, { decision, decision_reason: reason })
    const idx = queue.value.findIndex(q => q.company_id === companyId)
    if (idx >= 0) queue.value[idx] = { ...queue.value[idx], status: data.status }
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function loadAiConfig() {
  try {
    const { data } = await api.get('/admin/ai/config')
    aiKycEnabled.value = data.enabled && data.kyc_enabled
  } catch { aiKycEnabled.value = false }
}

// Media library
async function loadMedia() {
  mediaLoading.value = true
  mediaFilter.offset = 0
  try {
    const params = { limit: 100, offset: 0 }
    if (mediaFilter.status) params.status = mediaFilter.status
    const { data } = await api.get('/admin/kyc-media/files', { params })
    mediaFiles.value = data
  } catch { mediaFiles.value = [] }
  mediaLoading.value = false
}

async function analyzeMediaDoc(doc) {
  doc._analyzing = true
  try {
    const { data } = await api.post('/admin/ai/analyze-kyc-document', { document_id: doc.id })
    if (data.ok && data.analysis) {
      const a = data.analysis
      doc.latest_analysis = {
        authenticity: a.authenticity || 'SUSPICIOUS',
        confidence: a.confidence || 0,
        risk_score: a.overall_risk_score || 0,
        tamper_suspected: a.tamper_suspected,
        photoshop_suspected: a.photoshop_suspected,
        recommended_action: a.recommended_action || 'MANUAL_REVIEW',
        created_at: new Date().toISOString(),
      }
    }
  } catch {}
  doc._analyzing = false
}

async function flagMediaRisk(doc) {
  const reason = prompt('Reason for flagging:')
  if (reason === null) return
  try {
    await api.post(`/admin/kyc-media/files/${doc.id}/flag-risk`, { reason })
    doc.status = 'REJECTED'
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function batchAnalyze() {
  batchAnalyzing.value = true
  const pending = mediaFiles.value.filter(d => !d.latest_analysis).slice(0, 20)
  if (!pending.length) {
    alert('No unanalyzed documents in current list.')
    batchAnalyzing.value = false
    return
  }
  try {
    const { data } = await api.post('/admin/ai/batch-analyze-kyc', { document_ids: pending.map(d => d.id) })
    if (data.ok) {
      for (const result of (data.results || [])) {
        const doc = mediaFiles.value.find(d => d.id === result.document_id)
        if (doc && result.ok && result.analysis) {
          const a = result.analysis
          doc.latest_analysis = {
            authenticity: a.authenticity || 'SUSPICIOUS',
            confidence: a.confidence || 0,
            risk_score: a.overall_risk_score || 0,
            tamper_suspected: a.tamper_suspected,
            photoshop_suspected: a.photoshop_suspected,
            recommended_action: a.recommended_action || 'MANUAL_REVIEW',
            created_at: new Date().toISOString(),
          }
        }
      }
      alert(`Analyzed ${data.count} documents.`)
    }
  } catch (e) { alert(e.response?.data?.detail || 'Batch analysis failed') }
  batchAnalyzing.value = false
}

onMounted(async () => {
  const [q] = await Promise.all([
    api.get('/admin/verification/queue').then(r => r.data).catch(() => []),
    loadAiConfig(),
  ])
  queue.value = q
  loading.value = false
  loadMedia()
})
</script>
