type ApiErrorPayload = {
  detail?: unknown
}

const validationMessage = (value: unknown): string | null => {
  if (typeof value === 'string' && value.trim()) return value.trim()
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
  return location ? `${location}: ${message}` : message
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
