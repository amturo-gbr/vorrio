import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { changeLocale, currentLocale, localeManifest, supportedLocales } from '../i18n'
import type { SupportedLocale } from '../types'

type Props = {
  compact?: boolean
  value?: SupportedLocale
  onChange?: (locale: SupportedLocale) => Promise<void> | void
}

export function LanguageSwitcher({ compact = false, value, onChange }: Props) {
  const { t } = useTranslation()
  const selected = value || currentLocale()

  const select = async (locale: SupportedLocale) => {
    if (onChange) await onChange(locale)
    else await changeLocale(locale)
  }

  return (
    <label className={`language-switcher${compact ? ' compact' : ''}`}>
      <span><Languages />{compact ? null : t('language.interface_label')}</span>
      <select
        value={selected}
        aria-label={t('language.interface_label')}
        onChange={(event) => void select(event.target.value as SupportedLocale)}
      >
        {supportedLocales.map((locale) => (
          <option key={locale} value={locale}>{localeManifest(locale).native_name}</option>
        ))}
      </select>
    </label>
  )
}
