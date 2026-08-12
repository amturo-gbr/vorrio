import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'
import german from './locales/de/translation.json' with { type: 'json' }
import english from './locales/en/translation.json' with { type: 'json' }
import type { SupportedLocale } from './types'

export const supportedLocales: SupportedLocale[] = ['de', 'en']
export const LOCALE_STORAGE_KEY = 'vorrio.locale.v1'

export const resolveLocale = (value: string | null | undefined): SupportedLocale => {
  const language = String(value || '').trim().toLowerCase().split('-')[0]
  return language === 'en' ? 'en' : 'de'
}

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      de: { translation: german },
      en: { translation: english },
    },
    supportedLngs: supportedLocales,
    nonExplicitSupportedLngs: true,
    fallbackLng: 'de',
    keySeparator: false,
    nsSeparator: false,
    returnNull: false,
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: LOCALE_STORAGE_KEY,
      caches: ['localStorage'],
    },
    react: { useSuspense: false },
  })

const applyDocumentLocale = (language: string) => {
  const locale = resolveLocale(language)
  if (typeof document === 'undefined') return
  document.documentElement.lang = locale
  document.documentElement.dir = i18n.dir(locale)
  document.querySelector<HTMLLinkElement>('link[rel="manifest"]')?.setAttribute(
    'href',
    `/manifest-${locale}.webmanifest`,
  )
}

applyDocumentLocale(i18n.resolvedLanguage || i18n.language)
i18n.on('languageChanged', applyDocumentLocale)

export const currentLocale = (): SupportedLocale =>
  resolveLocale(i18n.resolvedLanguage || i18n.language)

export const changeLocale = async (locale: SupportedLocale): Promise<void> => {
  try {
    if (typeof window !== 'undefined') window.localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // The in-memory choice still works when storage is unavailable.
  }
  await i18n.changeLanguage(locale)
}

export const translate = (message: string, options?: Record<string, unknown>): string =>
  i18n.t(message, options)

export const formatNumber = (
  value: number,
  options: Intl.NumberFormatOptions = { maximumFractionDigits: 3 },
): string => new Intl.NumberFormat(currentLocale(), options).format(value)

export const formatCurrency = (
  value: number | null | undefined,
  currency = 'EUR',
): string => value == null
  ? '–'
  : new Intl.NumberFormat(currentLocale(), { style: 'currency', currency }).format(value)

export const formatDate = (
  value: Date | string | number,
  options: Intl.DateTimeFormatOptions,
): string => new Intl.DateTimeFormat(currentLocale(), options).format(new Date(value))

export default i18n
