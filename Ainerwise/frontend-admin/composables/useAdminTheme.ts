export type AdminTheme = 'dark' | 'light'

const STORAGE_KEY = 'admin-theme'

export function useAdminTheme() {
  const theme = useState<AdminTheme>('admin-theme', () => 'dark')

  function applyTheme(value: AdminTheme) {
    if (!import.meta.client) return
    document.documentElement.classList.toggle('theme-light', value === 'light')
    localStorage.setItem(STORAGE_KEY, value)
  }

  function initTheme() {
    if (!import.meta.client) return
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'light' || saved === 'dark') {
      theme.value = saved
    }
    applyTheme(theme.value)
  }

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    applyTheme(theme.value)
  }

  const isLight = computed(() => theme.value === 'light')

  return { theme, isLight, toggleTheme, initTheme }
}
