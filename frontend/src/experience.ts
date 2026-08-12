import type { ExperienceState } from './types'

export type AutomaticExperienceSurface = 'onboarding' | 'release' | null

export function automaticExperienceSurface(state: ExperienceState): AutomaticExperienceSurface {
  if (state.onboarding_required) return 'onboarding'
  if (state.release_notes_pending) return 'release'
  return null
}
