import type { CachedFieldTask, OfflineQueueItem } from './useFieldOfflineStore'

function newIdempotencyKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`
}

export function useFieldWorkerSync() {
  const { apiFetch } = useApi()
  const { cacheTasks, getCachedTasks, enqueue, listQueue, dequeue, putBlob, getBlob, deleteBlob } = useFieldOfflineStore()
  const online = useOnline()
  const syncing = ref(false)
  const lastSyncAt = ref<string | null>(null)

  async function refreshToday() {
    try {
      const data = await apiFetch<{ items: CachedFieldTask[] }>('/field/tasks/today')
      const items = (data.items || []).map(t => ({
        ...t,
        cached_at: new Date().toISOString(),
      }))
      await cacheTasks(items)
      return items
    } catch {
      return getCachedTasks()
    }
  }

  async function flushQueue() {
    if (!online.value || syncing.value) return
    const pending = await listQueue()
    if (!pending.length) return
    syncing.value = true
    try {
      const prepared: OfflineQueueItem[] = []
      for (const item of pending) {
        if (!item.blob_key) {
          prepared.push(item)
          continue
        }
        const blob = await getBlob(item.blob_key)
        if (!blob) {
          await dequeue(item.idempotency_key)
          continue
        }
        const filename = String(item.payload_json?.filename || `field-photo-${Date.now()}.jpg`)
        const contentType = blob.type || String(item.payload_json?.content_type || 'image/jpeg')
        const presigned = await apiFetch<{ upload_url: string; object_name: string }>(
          `/files/upload-url?filename=${encodeURIComponent(filename)}&content_type=${encodeURIComponent(contentType)}`,
          { method: 'POST' },
        )
        await $fetch(presigned.upload_url, { method: 'PUT', body: blob })
        prepared.push({
          ...item,
          blob_key: undefined,
          payload_json: {
            object_name: presigned.object_name,
            filename,
            content_type: contentType,
            captured_at: item.payload_json?.captured_at,
          },
        })
      }
      if (!prepared.length) return
      const res = await apiFetch<{ items: Array<{ idempotency_key: string; status: string; conflict?: boolean; server_offline_version?: number; detail?: string }> }>(
        '/field/sync',
        { method: 'POST', body: { items: prepared } },
      )
      for (const row of res.items || []) {
        if (row.status === 'ok') {
          const original = pending.find(item => item.idempotency_key === row.idempotency_key)
          if (original?.blob_key) await deleteBlob(original.blob_key)
          await dequeue(row.idempotency_key)
        } else if (row.status === 'conflict') {
          const original = pending.find(item => item.idempotency_key === row.idempotency_key)
          if (original) {
            await enqueue({
              ...original,
              conflict: true,
              server_offline_version: row.server_offline_version,
              detail: row.detail || 'version_conflict',
            })
          }
        }
      }
      lastSyncAt.value = new Date().toISOString()
      await refreshToday()
    } finally {
      syncing.value = false
    }
  }

  async function queueStatusChange(task: CachedFieldTask, status: string) {
    const item: OfflineQueueItem = {
      idempotency_key: newIdempotencyKey('status'),
      type: 'status',
      task_id: task.id,
      status,
      offline_version: task.offline_version,
      created_at: new Date().toISOString(),
    }
    await enqueue(item)
    if (online.value) {
      await flushQueue()
    }
  }

  async function queueEvidence(taskId: string, evidence_type: string, payload_json: Record<string, unknown>) {
    const item: OfflineQueueItem = {
      idempotency_key: newIdempotencyKey('evidence'),
      type: 'evidence',
      task_id: taskId,
      evidence_type,
      payload_json,
      created_at: new Date().toISOString(),
    }
    await enqueue(item)
    if (online.value) {
      await flushQueue()
    }
  }

  async function queuePhotoEvidence(taskId: string, file: File) {
    const idempotencyKey = newIdempotencyKey('photo')
    const blobKey = `field-photo:${idempotencyKey}`
    await putBlob(blobKey, file)
    await enqueue({
      idempotency_key: idempotencyKey,
      type: 'evidence',
      task_id: taskId,
      evidence_type: 'photo',
      blob_key: blobKey,
      payload_json: {
        filename: file.name || `field-photo-${Date.now()}.jpg`,
        content_type: file.type || 'image/jpeg',
        captured_at: new Date().toISOString(),
      },
      created_at: new Date().toISOString(),
    })
    if (online.value) await flushQueue()
  }

  async function resolveConflict(idempotencyKey: string, strategy: 'retry' | 'discard') {
    const pending = await listQueue()
    const item = pending.find(row => row.idempotency_key === idempotencyKey)
    if (!item) return
    if (strategy === 'discard') {
      if (item.blob_key) await deleteBlob(item.blob_key)
      await dequeue(idempotencyKey)
      return
    }
    await enqueue({
      ...item,
      conflict: false,
      offline_version: item.server_offline_version ?? item.offline_version,
      server_offline_version: undefined,
      detail: undefined,
    })
    await flushQueue()
  }

  watch(online, val => {
    if (val) flushQueue()
  })

  if (import.meta.client) {
    onMounted(() => {
      flushQueue()
      window.addEventListener('online', flushQueue)
    })
    onUnmounted(() => {
      window.removeEventListener('online', flushQueue)
    })
  }

  return {
    online,
    syncing,
    lastSyncAt,
    refreshToday,
    flushQueue,
    queueStatusChange,
    queueEvidence,
    queuePhotoEvidence,
    listQueue,
    resolveConflict,
    getCachedTasks,
  }
}
