import type { ScanMode } from '../../types'

export const OFFLINE_SCAN_STORAGE_KEY = 'vorrio.offline-scans.v1'
const MAX_OFFLINE_SCANS = 100

export interface OfflineScanEntry {
  id: string
  barcode: string
  mode: ScanMode
  clientMutationId: string
  createdAt: string
  attempts: number
  lastError: string | null
}

export interface OfflineScanStorage {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
  removeItem: (key: string) => void
}

const modes = new Set<ScanMode>(['identify', 'add', 'consume', 'open', 'shopping'])

const isEntry = (value: unknown): value is OfflineScanEntry => {
  if (!value || typeof value !== 'object') return false
  const entry = value as Partial<OfflineScanEntry>
  return typeof entry.id === 'string'
    && typeof entry.barcode === 'string'
    && typeof entry.mode === 'string'
    && modes.has(entry.mode as ScanMode)
    && typeof entry.clientMutationId === 'string'
    && typeof entry.createdAt === 'string'
    && typeof entry.attempts === 'number'
    && (entry.lastError === null || typeof entry.lastError === 'string')
}

export function readOfflineScans(storage: OfflineScanStorage): OfflineScanEntry[] {
  try {
    const raw = storage.getItem(OFFLINE_SCAN_STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter(isEntry).slice(0, MAX_OFFLINE_SCANS) : []
  } catch {
    return []
  }
}

function writeOfflineScans(storage: OfflineScanStorage, entries: OfflineScanEntry[]) {
  if (!entries.length) {
    storage.removeItem(OFFLINE_SCAN_STORAGE_KEY)
    return
  }
  storage.setItem(OFFLINE_SCAN_STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_OFFLINE_SCANS)))
}

export function queueOfflineScan(
  storage: OfflineScanStorage,
  input: Pick<OfflineScanEntry, 'barcode' | 'mode' | 'clientMutationId'> & {
    id: string
    createdAt: string
  },
): { entries: OfflineScanEntry[]; status: 'added' | 'duplicate' | 'full' } {
  const barcode = input.barcode.trim()
  const current = readOfflineScans(storage)
  const duplicate = current.some((entry) => entry.barcode === barcode && entry.mode === input.mode)
  if (duplicate) return { entries: current, status: 'duplicate' }
  if (current.length >= MAX_OFFLINE_SCANS) return { entries: current, status: 'full' }
  const entries = [
    ...current,
    {
      ...input,
      barcode,
      attempts: 0,
      lastError: null,
    },
  ]
  writeOfflineScans(storage, entries)
  return { entries, status: 'added' }
}

export function removeOfflineScan(storage: OfflineScanStorage, id: string): OfflineScanEntry[] {
  const entries = readOfflineScans(storage).filter((entry) => entry.id !== id)
  writeOfflineScans(storage, entries)
  return entries
}

export function markOfflineScanFailed(
  storage: OfflineScanStorage,
  id: string,
  message: string,
): OfflineScanEntry[] {
  const entries = readOfflineScans(storage).map((entry) => entry.id === id
    ? { ...entry, attempts: entry.attempts + 1, lastError: message }
    : entry)
  writeOfflineScans(storage, entries)
  return entries
}
