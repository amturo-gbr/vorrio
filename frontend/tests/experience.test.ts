import assert from 'node:assert/strict'
import test from 'node:test'
import { automaticExperienceSurface } from '../src/experience.ts'
import type { ExperienceState } from '../src/types.ts'

const state = (overrides: Partial<ExperienceState>): ExperienceState => ({
  current_version: '0.8.23',
  onboarding_completed: true,
  onboarding_required: false,
  last_acknowledged_version: '0.8.23',
  release_notes_pending: false,
  release: {
    version: '0.8.23',
    title: 'Test',
    summary: 'Test',
    highlights: [],
  },
  ...overrides,
})

test('first-run onboarding has priority over release notes', () => {
  assert.equal(automaticExperienceSurface(state({
    onboarding_completed: false,
    onboarding_required: true,
    last_acknowledged_version: null,
    release_notes_pending: true,
  })), 'onboarding')
})

test('an acknowledged household only sees release notes after an upgrade', () => {
  assert.equal(automaticExperienceSurface(state({
    last_acknowledged_version: '0.8.18',
    release_notes_pending: true,
  })), 'release')
  assert.equal(automaticExperienceSurface(state({})), null)
})
