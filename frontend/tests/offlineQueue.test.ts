import assert from 'node:assert/strict'
import test from 'node:test'
import {
  markOfflineScanFailed,
  OFFLINE_SCAN_STORAGE_KEY,
  queueOfflineScan,
  readOfflineScans,
  removeOfflineScan,
  type OfflineScanStorage,
} from '../src/features/scanner/offlineQueue.ts'

class MemoryStorage implements OfflineScanStorage {
  private values = new Map<string, string>()

  getItem(key: string) {
    return this.values.get(key) ?? null
  }

  setItem(key: string, value: string) {
    this.values.set(key, value)
  }

  removeItem(key: string) {
    this.values.delete(key)
  }
}

test('offline scans retain one stable mutation id and deduplicate the same action', () => {
  const storage = new MemoryStorage()
  const first = queueOfflineScan(storage, {
    id: 'local-1',
    barcode: ' 4000000000016 ',
    mode: 'add',
    clientMutationId: 'resolve-offline-1',
    createdAt: '2026-08-11T10:00:00.000Z',
  })
  const duplicate = queueOfflineScan(storage, {
    id: 'local-2',
    barcode: '4000000000016',
    mode: 'add',
    clientMutationId: 'resolve-offline-2',
    createdAt: '2026-08-11T10:01:00.000Z',
  })
  const otherMode = queueOfflineScan(storage, {
    id: 'local-3',
    barcode: '4000000000016',
    mode: 'identify',
    clientMutationId: 'resolve-offline-3',
    createdAt: '2026-08-11T10:02:00.000Z',
  })

  assert.equal(first.status, 'added')
  assert.equal(duplicate.status, 'duplicate')
  assert.equal(otherMode.status, 'added')
  assert.deepEqual(readOfflineScans(storage).map((entry) => entry.clientMutationId), [
    'resolve-offline-1',
    'resolve-offline-3',
  ])
})

test('failed scans remain reviewable and successful removal clears storage', () => {
  const storage = new MemoryStorage()
  queueOfflineScan(storage, {
    id: 'local-1',
    barcode: '4000000000016',
    mode: 'shopping',
    clientMutationId: 'resolve-offline-1',
    createdAt: '2026-08-11T10:00:00.000Z',
  })

  const failed = markOfflineScanFailed(storage, 'local-1', 'Nicht erreichbar')
  assert.equal(failed[0]?.attempts, 1)
  assert.equal(failed[0]?.lastError, 'Nicht erreichbar')
  assert.deepEqual(removeOfflineScan(storage, 'local-1'), [])
  assert.equal(storage.getItem(OFFLINE_SCAN_STORAGE_KEY), null)
})

test('invalid persisted data never becomes a queued mutation', () => {
  const storage = new MemoryStorage()
  storage.setItem(OFFLINE_SCAN_STORAGE_KEY, '{broken')
  assert.deepEqual(readOfflineScans(storage), [])
})

test('offline queue fails closed instead of dropping an older scan when full', () => {
  const storage = new MemoryStorage()
  for (let index = 0; index < 100; index += 1) {
    queueOfflineScan(storage, {
      id: `local-${index}`,
      barcode: `400000000${String(index).padStart(3, '0')}`,
      mode: 'identify',
      clientMutationId: `resolve-offline-${index}`,
      createdAt: '2026-08-11T10:00:00.000Z',
    })
  }
  const overflow = queueOfflineScan(storage, {
    id: 'local-overflow',
    barcode: '9999999999999',
    mode: 'identify',
    clientMutationId: 'resolve-offline-overflow',
    createdAt: '2026-08-11T10:01:00.000Z',
  })

  assert.equal(overflow.status, 'full')
  assert.equal(readOfflineScans(storage).length, 100)
  assert.equal(readOfflineScans(storage)[0]?.id, 'local-0')
})
