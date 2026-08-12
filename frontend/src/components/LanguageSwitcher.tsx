import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { changeLocale, currentLocale, supportedLocales } from '../i18n'
import type { SupportedLocale } from '../types'

type Props = {
  compact?: boolean
  value?: SupportedLocale
  onChange?: (locale: SupportedLocale) => Promise<void> | void
}

const localeLabels: Record<SupportedLocale, string> = {
  de: 'Deutsch',
  en: 'English',
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
      <span><Languages />{compact ? null : t('Oberflächensprache')}</span>
      <select
        value={selected}
        aria-label={t('Oberflächensprache')}
        onChange={(event) => void select(event.target.value as SupportedLocale)}
      >
        {supportedLocales.map((locale) => (
          <option key={locale} value={locale}>{t(localeLabels[locale])}</option>
        ))}
      </select>
    </label>
  )
}
