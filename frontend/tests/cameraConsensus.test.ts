import assert from 'node:assert/strict'
import test from 'node:test'
import {
  CAMERA_MATCH_WINDOW_MS,
  observeCameraCode,
} from '../src/features/scanner/cameraConsensus.ts'

test('camera accepts a code only after two matching observations', () => {
  const first = observeCameraCode(null, ' 4006-381333931 ', 1_000)
  const second = observeCameraCode(first.candidate, '4006381333931', 1_300)

  assert.equal(first.confirmed, false)
  assert.equal(second.confirmed, true)
  assert.equal(second.candidate.code, '4006381333931')
})

test('camera resets consensus for a changed or stale code', () => {
  const first = observeCameraCode(null, '4006381333931', 1_000)
  const changed = observeCameraCode(first.candidate, '4388860678727', 1_200)
  const stale = observeCameraCode(
    changed.candidate,
    '4388860678727',
    1_200 + CAMERA_MATCH_WINDOW_MS + 1,
  )

  assert.equal(changed.confirmed, false)
  assert.equal(changed.candidate.matches, 1)
  assert.equal(stale.confirmed, false)
  assert.equal(stale.candidate.matches, 1)
})
