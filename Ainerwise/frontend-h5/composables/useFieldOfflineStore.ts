const DB_NAME = 'ainerwise-field-v1'
const DB_VERSION = 2

export type CachedFieldTask = {
  id: string
  title: string
  task_type: string
  status: string
  offline_version: number
  site_json?: Record<string, unknown> | null
  checklist_json?: Record<string, unknown> | null
  schedule_start?: string | null
  cached_at: string
}

export type OfflineQueueItem = {
  idempotency_key: string
  type: 'status' | 'evidence'
  task_id: string
  status?: string
  offline_version?: number
  evidence_type?: string
  payload_json?: Record<string, unknown>
  blob_key?: string
  conflict?: boolean
  server_offline_version?: number
  detail?: string
  created_at: string
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onerror = () => reject(req.error)
    req.onsuccess = () => resolve(req.result)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains('tasks')) {
        db.createObjectStore('tasks', { keyPath: 'id' })
      }
      if (!db.objectStoreNames.contains('queue')) {
        db.createObjectStore('queue', { keyPath: 'idempotency_key' })
      }
      if (!db.objectStoreNames.contains('blobs')) {
        db.createObjectStore('blobs')
      }
    }
  })
}

async function withStore<T>(storeName: string, mode: IDBTransactionMode, fn: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, mode)
    const store = tx.objectStore(storeName)
    const request = fn(store)
    request.onsuccess = () => resolve(request.result as T)
    request.onerror = () => reject(request.error)
  })
}

export function useFieldOfflineStore() {
  async function cacheTasks(tasks: CachedFieldTask[]) {
    if (!import.meta.client) return
    const db = await openDb()
    const tx = db.transaction('tasks', 'readwrite')
    const store = tx.objectStore('tasks')
    const keep = new Set(tasks.map(t => t.id))
    for (const task of tasks) {
      store.put({ ...task, cached_at: new Date().toISOString() })
    }
    const all = await new Promise<CachedFieldTask[]>((resolve, reject) => {
      const req = store.getAll()
      req.onsuccess = () => resolve(req.result as CachedFieldTask[])
      req.onerror = () => reject(req.error)
    })
    for (const row of all) {
      if (!keep.has(row.id)) store.delete(row.id)
    }
  }

  async function getCachedTasks(): Promise<CachedFieldTask[]> {
    if (!import.meta.client) return []
    return withStore('tasks', 'readonly', store => store.getAll())
  }

  async function enqueue(item: OfflineQueueItem) {
    if (!import.meta.client) return
    await withStore('queue', 'readwrite', store => store.put(item))
  }

  async function listQueue(): Promise<OfflineQueueItem[]> {
    if (!import.meta.client) return []
    return withStore('queue', 'readonly', store => store.getAll())
  }

  async function dequeue(idempotency_key: string) {
    if (!import.meta.client) return
    await withStore('queue', 'readwrite', store => store.delete(idempotency_key))
  }

  async function putBlob(key: string, blob: Blob) {
    if (!import.meta.client) return
    await withStore('blobs', 'readwrite', store => store.put(blob, key))
  }

  async function getBlob(key: string): Promise<Blob | undefined> {
    if (!import.meta.client) return undefined
    return withStore('blobs', 'readonly', store => store.get(key))
  }

  async function deleteBlob(key: string) {
    if (!import.meta.client) return
    await withStore('blobs', 'readwrite', store => store.delete(key))
  }

  async function clearAll() {
    if (!import.meta.client) return
    const db = await openDb()
    for (const name of ['tasks', 'queue', 'blobs'] as const) {
      const tx = db.transaction(name, 'readwrite')
      tx.objectStore(name).clear()
    }
  }

  return { cacheTasks, getCachedTasks, enqueue, listQueue, dequeue, putBlob, getBlob, deleteBlob, clearAll }
}
