import { translate } from './i18n.ts'

type ApiErrorPayload = {
  detail?: unknown
}

const dynamicMessages: Array<{
  pattern: RegExp
  render: (match: RegExpMatchArray) => string
}> = [
  {
    pattern: /^Dem API-Token fehlt die Berechtigung (.+)$/,
    render: (match) => translate('Dem API-Token fehlt die Berechtigung {{scope}}', { scope: match[1] }),
  },
  {
    pattern: /^(.+) wurde nicht gefunden oder ist archiviert$/,
    render: (match) => translate('{{item}} wurde nicht gefunden oder ist archiviert', { item: match[1] }),
  },
  {
    pattern: /^Nur (.+) im Bestand$/,
    render: (match) => translate('Nur {{quantity}} im Bestand', { quantity: match[1] }),
  },
  {
    pattern: /^(Grocy ist nicht erreichbar|Open Facts ist nicht erreichbar|Open-Facts-Suche ist nicht erreichbar|KI-Sortierung nicht verfügbar):\s*(.+)$/,
    render: (match) => `${translate(match[1])}: ${match[2]}`,
  },
]

export const localizeApiMessage = (message: string): string => {
  const normalized = message.trim()
  const translated = translate(normalized)
  if (translated !== normalized) return translated
  for (const entry of dynamicMessages) {
    const match = normalized.match(entry.pattern)
    if (match) return entry.render(match)
  }
  return normalized
}

const validationMessage = (value: unknown): string | null => {
  if (typeof value === 'string' && value.trim()) return localizeApiMessage(value)
  if (!value || typeof value !== 'object') return null

  const item = value as Record<string, unknown>
  const message = [item.message, item.msg, item.error]
    .find((candidate) => typeof candidate === 'string' && candidate.trim())
  if (typeof message !== 'string') return null

  const location = Array.isArray(item.loc)
    ? item.loc
      .filter((part) => part !== 'body' && part !== 'query' && part !== 'path')
      .map(String)
      .join(' → ')
    : ''
  const localized = localizeApiMessage(message)
  return location ? `${location}: ${localized}` : localized
}

export const apiErrorMessage = (payload: unknown, status: number): string => {
  const detail = payload && typeof payload === 'object'
    ? (payload as ApiErrorPayload).detail
    : null

  if (Array.isArray(detail)) {
    const messages = detail.map(validationMessage).filter((message): message is string => Boolean(message))
    if (messages.length) return messages.join(' · ')
  }

  const message = validationMessage(detail)
  return message || `HTTP ${status}`
}
