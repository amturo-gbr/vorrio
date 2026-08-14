export interface CameraScanCandidate {
  code: string
  matches: number
  lastSeenAt: number
}

export interface CameraScanObservation {
  candidate: CameraScanCandidate
  confirmed: boolean
}

export const CAMERA_MATCH_WINDOW_MS = 1_800
export const CAMERA_REQUIRED_MATCHES = 2

export function observeCameraCode(
  previous: CameraScanCandidate | null,
  rawCode: string,
  observedAt: number,
): CameraScanObservation {
  const code = rawCode.trim().replace(/[\s-]+/g, '')
  const continuesCandidate = Boolean(
    previous &&
    previous.code === code &&
    observedAt - previous.lastSeenAt <= CAMERA_MATCH_WINDOW_MS,
  )
  const candidate = {
    code,
    matches: continuesCandidate ? previous!.matches + 1 : 1,
    lastSeenAt: observedAt,
  }
  return {
    candidate,
    confirmed: Boolean(code) && candidate.matches >= CAMERA_REQUIRED_MATCHES,
  }
}
