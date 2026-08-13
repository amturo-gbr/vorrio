import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'
import {
  defaultLocale,
  isSupportedLocale,
  loadLocaleCatalog,
  localeManifest,
  supportedLocales,
} from './locales/registry.ts'
import type { SupportedLocale } from './locales/registry.ts'

export { localeManifest, supportedLocales }
export const LOCALE_STORAGE_KEY = 'vorrio.locale.v1'

export const resolveLocale = (value: string | null | undefined): SupportedLocale => {
  const language = String(value || '').trim().toLowerCase().split('-')[0]
  return isSupportedLocale(language) ? language : defaultLocale
}

const browserLocale = (): SupportedLocale => {
  if (typeof window !== 'undefined') {
    try {
      const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY)
      if (stored) return resolveLocale(stored)
    } catch {
      // Browser detection remains available when storage is blocked.
    }
  }
  return resolveLocale(typeof navigator === 'undefined' ? defaultLocale : navigator.language)
}

const loadedLocales = new Set<SupportedLocale>()

export const ensureLocaleLoaded = async (locale: SupportedLocale): Promise<void> => {
  if (loadedLocales.has(locale) || i18n.hasResourceBundle(locale, 'translation')) return
  const catalog = await loadLocaleCatalog(locale)
  i18n.addResourceBundle(locale, 'translation', catalog, true, true)
  loadedLocales.add(locale)
}

const applyDocumentLocale = (language: string) => {
  const locale = resolveLocale(language)
  if (typeof document === 'undefined') return
  document.documentElement.lang = locale
  document.documentElement.dir = localeManifest(locale).direction
  document.querySelector<HTMLLinkElement>('link[rel="manifest"]')?.setAttribute(
    'href',
    `/manifest-${locale}.webmanifest`,
  )
}

const initialize = async (): Promise<void> => {
  let initialLocale = browserLocale()
  const fallbackCatalog = await loadLocaleCatalog(defaultLocale)
  loadedLocales.add(defaultLocale)
  let initialCatalog = fallbackCatalog
  if (initialLocale !== defaultLocale) {
    try {
      initialCatalog = await loadLocaleCatalog(initialLocale)
      loadedLocales.add(initialLocale)
    } catch {
      initialLocale = defaultLocale
    }
  }

  await i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      resources: {
        [defaultLocale]: { translation: fallbackCatalog },
        [initialLocale]: { translation: initialCatalog },
      },
      lng: initialLocale,
      supportedLngs: supportedLocales,
      nonExplicitSupportedLngs: true,
      fallbackLng: defaultLocale,
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

  applyDocumentLocale(i18n.resolvedLanguage || i18n.language)
  i18n.on('languageChanged', applyDocumentLocale)
}

export const i18nReady = initialize()

export const currentLocale = (): SupportedLocale =>
  resolveLocale(i18n.resolvedLanguage || i18n.language || browserLocale())

export const changeLocale = async (locale: SupportedLocale): Promise<void> => {
  await i18nReady
  await ensureLocaleLoaded(locale)
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
