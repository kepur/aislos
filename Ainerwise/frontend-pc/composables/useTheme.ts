// AISLOS theme mode — SSR-safe via cookie. Defaults to dark (preserves current look).
// Light theme rolls out to public pages first; workspace stays dark until tokenized.
export function useTheme() {
  const theme = useCookie<'dark' | 'light'>('aislos_theme', {
    default: () => 'dark',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 365,
  })
  const isDark = computed(() => theme.value !== 'light')
  function toggle() {
    theme.value = isDark.value ? 'light' : 'dark'
  }
  function set(value: 'dark' | 'light') {
    theme.value = value
  }
  return { theme, isDark, toggle, set }
}
