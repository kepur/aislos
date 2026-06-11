// Conversational AI assistant client. Calls the backend /ai/assistant endpoint
// (OpenAI-compatible agent, configured in Admin → Integrations). Degrades
// gracefully: when the AI is not configured, `enabled` is false and callers
// fall back to the scripted question flow.
export function useAssistant() {
  const { apiFetch } = useApi()
  const enabled = ref(false)

  async function checkStatus() {
    try {
      const r = await apiFetch<any>('/ai/assistant/status')
      enabled.value = !!r?.configured
    } catch {
      enabled.value = false
    }
    return enabled.value
  }

  async function ask(category: string, messages: Array<{ role: string; content: string }>, collected: Record<string, any> = {}) {
    return await apiFetch<any>('/ai/assistant', {
      method: 'POST',
      body: { category, messages, collected },
    })
  }

  return { enabled, checkStatus, ask }
}
