export function useFileUpload() {
  const { apiFetch } = useApi()
  const uploading = ref(false)
  const progress = ref(0)
  const error = ref<string | null>(null)

  async function uploadFile(
    file: File,
    _options: { folder?: string } = {}
  ): Promise<{ file_key: string; download_url: string } | null> {
    uploading.value = true
    progress.value = 0
    error.value = null

    try {
      // 1. Get presigned upload URL from backend
      const { upload_url, object_name } = await apiFetch<{
        upload_url: string
        object_name: string
      }>(`/files/upload-url?filename=${encodeURIComponent(file.name)}&content_type=${encodeURIComponent(file.type || 'application/octet-stream')}`, {
        method: 'POST',
      })

      // 2. Upload directly to MinIO using presigned URL
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('PUT', upload_url)
        xhr.setRequestHeader('Content-Type', file.type)

        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            progress.value = Math.round((e.loaded / e.total) * 100)
          }
        }

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve()
          } else {
            reject(new Error(`Upload failed: ${xhr.status}`))
          }
        }

        xhr.onerror = () => reject(new Error('Upload failed'))
        xhr.send(file)
      })

      // 3. Get download URL
      const { download_url } = await apiFetch<{ download_url: string }>(
        `/files/download-url?object_name=${encodeURIComponent(object_name)}`
      )

      progress.value = 100
      return { file_key: object_name, download_url }
    } catch (e: any) {
      error.value = e?.message || 'Upload failed'
      return null
    } finally {
      uploading.value = false
    }
  }

  return {
    uploadFile,
    uploading,
    progress,
    error,
  }
}
