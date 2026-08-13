import germanManifest from './de/manifest.json' with { type: 'json' }
import englishManifest from './en/manifest.json' with { type: 'json' }
import germanCatalog from './de/translation.json' with { type: 'json' }

export type LocaleDirection = 'ltr' | 'rtl'
export type LocaleTier = 'official' | 'community'

export type LocaleManifest = {
  schema_version: 1
  locale: string
  native_name: string
  english_name: string
  direction: LocaleDirection
  fallback_locale: string
  tier: LocaleTier
  catalog_mode: 'complete' | 'source-fallback'
  catalog_version: number
  minimum_vorrio_version: string
  completion: number
  capabilities: string[]
}

type TranslationCatalog = Record<string, string>
type LocaleModule = { default: TranslationCatalog }
type LocaleDefinition = {
  manifest: LocaleManifest
  load: () => Promise<LocaleModule>
}

const definition = (
  manifest: LocaleManifest,
  load: () => Promise<LocaleModule>,
): LocaleDefinition => ({ manifest, load })

export const localeRegistry = {
  de: definition(
    germanManifest as LocaleManifest,
    async () => ({ default: germanCatalog }),
  ),
  en: definition(
    englishManifest as LocaleManifest,
    () => import('./en/translation.json', { with: { type: 'json' } }),
  ),
} as const

export type SupportedLocale = keyof typeof localeRegistry

export const supportedLocales = Object.freeze(
  Object.keys(localeRegistry) as SupportedLocale[],
)

export const defaultLocale: SupportedLocale = 'de'

export const isSupportedLocale = (value: string): value is SupportedLocale =>
  Object.prototype.hasOwnProperty.call(localeRegistry, value)

export const localeManifest = (locale: SupportedLocale): LocaleManifest =>
  localeRegistry[locale].manifest

export const loadLocaleCatalog = async (
  locale: SupportedLocale,
): Promise<TranslationCatalog> => (await localeRegistry[locale].load()).default
