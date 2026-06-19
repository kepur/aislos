import { createI18n } from 'vue-i18n'
import en from './en'
import zh from './zh'
import tl from './tl'
import ja from './ja'
import ko from './ko'
import es from './es'
import th from './th'
import vi from './vi'
import id from './id'
import ar from './ar'

export const SUPPORTED_LOCALES = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: 'English' },
  { code: 'tl', name: 'Tagalog' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
  { code: 'es', name: 'Español' },
  { code: 'th', name: 'ไทย' },
  { code: 'vi', name: 'Tiếng Việt' },
  { code: 'id', name: 'Bahasa Indonesia' },
  { code: 'ar', name: 'العربية' },
]

const RTL_LOCALES = ['ar']

const savedLocale = localStorage.getItem('admin_locale') || 'zh'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: { en, zh, tl, ja, ko, es, th, vi, id, ar },
})

export function applyDirection(lang) {
  document.documentElement.dir = RTL_LOCALES.includes(lang) ? 'rtl' : 'ltr'
  document.documentElement.lang = lang
}

applyDirection(savedLocale)

export default i18n
