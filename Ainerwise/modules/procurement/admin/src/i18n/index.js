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
import sr from './sr'

export const SUPPORTED_LOCALES = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'sr', name: 'Srpski' },
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

const prefix = window.location.pathname.split('/').filter(Boolean)[0]
const prefixLocale = { en: 'en', cn: 'zh', rs: 'sr' }[prefix]
const savedLocale = prefixLocale || localStorage.getItem('admin_locale') || 'en'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: { en, zh, sr, tl, ja, ko, es, th, vi, id, ar },
})

export function applyDirection(lang) {
  document.documentElement.dir = RTL_LOCALES.includes(lang) ? 'rtl' : 'ltr'
  document.documentElement.lang = lang
}

applyDirection(savedLocale)
localStorage.setItem('admin_locale', savedLocale)
if (prefixLocale) localStorage.setItem('admin_locale_prefix', prefix)

export default i18n
