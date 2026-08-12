import {
  AlertCircle,
  ArrowLeft,
  Banana,
  Barcode,
  Bell,
  BellRing,
  Boxes,
  Camera,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  History,
  Home,
  Info,
  KeyRound,
  FileUp,
  LoaderCircle,
  LogOut,
  Mail,
  Milk,
  MonitorSmartphone,
  PackageCheck,
  PackageSearch,
  PackagePlus,
  ReceiptText,
  Search,
  Settings,
  ShieldCheck,
  Sandwich,
  Sparkles,
  Unplug,
  UserPlus,
  UserRound,
  X,
} from 'lucide-react'
import { startAuthentication, startRegistration } from '@simplewebauthn/browser'
import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, ApiError, ApiNetworkError } from './api'
import type {
  AppStatus,
  ApiToken,
  ApiTokenScope,
  ApiTokenScopeId,
  AuthenticatedUser,
  AuthSession,
  ExperienceState,
  CatalogProduct,
  CatalogProductCreateInput,
  GrocyMasterData,
  HouseholdInvitation,
  HouseholdInvitationPublic,
  HouseholdMember,
  NotificationState,
  ProductCandidate,
  ProductCandidateSearch,
  Receipt,
  ReceiptItem,
  Screen,
  SecurityState,
  SettingsData,
  TotpSetup,
} from './types'
import { ScannerScreen } from './features/scanner/ScannerScreen'
import { CatalogScreen } from './features/catalog/CatalogScreen'
import { ShoppingScreen } from './features/shopping/ShoppingScreen'
import { LaunchReadinessPanel } from './features/settings/LaunchReadinessPanel'
import { automaticExperienceSurface } from './experience'

const providerDefaults: Record<SettingsData['provider']['type'], { baseUrl: string; model: string }> = {
  cortecs: { baseUrl: 'https://api.cortecs.ai/v1', model: '' },
  openai: { baseUrl: 'https://api.openai.com/v1', model: 'gpt-5.4-mini' },
  openrouter: { baseUrl: 'https://openrouter.ai/api/v1', model: '' },
  ollama: { baseUrl: 'http://host.docker.internal:11434/v1', model: 'qwen2.5vl:7b' },
  'openai-compatible': { baseUrl: '', model: '' },
  anthropic: { baseUrl: 'https://api.anthropic.com/v1', model: 'claude-sonnet-4-5' },
}

const openAiModels = [
  { id: 'gpt-5.4-mini', label: 'GPT-5.4 mini · empfohlen' },
  { id: 'gpt-5-mini', label: 'GPT-5 mini · günstig' },
  { id: 'gpt-5.6-luna', label: 'GPT-5.6 Luna · sehr günstig' },
  { id: 'gpt-5.6-terra', label: 'GPT-5.6 Terra · maximale Qualität' },
]

const apiTokenPresets: Record<'homeassistant' | 'scanner' | 'custom', { name: string; scopes: ApiTokenScopeId[] }> = {
  homeassistant: {
    name: 'Home Assistant',
    scopes: ['status:read', 'catalog:read', 'stock:read', 'shopping:read'],
  },
  scanner: {
    name: 'Handscanner',
    scopes: ['catalog:read', 'stock:read', 'shopping:read', 'scans:read', 'scans:write'],
  },
  custom: { name: 'Lokaler Dienst', scopes: ['status:read'] },
}

const euro = (value: number | null | undefined) =>
  value == null
    ? '–'
    : new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)

const quantity = (value: number) =>
  new Intl.NumberFormat('de-DE', { maximumFractionDigits: 3 }).format(value)

const OFFLINE_AUTH_HINT_KEY = 'vorrio.offline-authenticated.v1'

const rememberAuthenticatedDevice = (authenticated: boolean) => {
  try {
    if (authenticated) window.localStorage.setItem(OFFLINE_AUTH_HINT_KEY, '1')
    else window.localStorage.removeItem(OFFLINE_AUTH_HINT_KEY)
  } catch {
    // Offline access remains optional when device storage is unavailable.
  }
}

const wasAuthenticatedOnDevice = () => {
  try {
    return window.localStorage.getItem(OFFLINE_AUTH_HINT_KEY) === '1'
  } catch {
    return false
  }
}

const shortDate = (value: string | null | undefined) => {
  if (!value) return 'Heute'
  const date = new Date(`${value}T12:00:00`)
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: 'short' }).format(date)
}

function App() {
  const [inviteToken, setInviteToken] = useState(() => new URLSearchParams(window.location.search).get('invite'))
  const [authenticated, setAuthenticated] = useState<boolean | null>(null)
  const [currentUser, setCurrentUser] = useState<AuthenticatedUser | null>(null)
  const [offlineMode, setOfflineMode] = useState(false)
  const [needsSetup, setNeedsSetup] = useState(false)
  const [identifierRequired, setIdentifierRequired] = useState(false)
  const [screen, setScreen] = useState<Screen>('home')
  const [status, setStatus] = useState<AppStatus | null>(null)
  const [experience, setExperience] = useState<ExperienceState | null>(null)
  const [guideOpen, setGuideOpen] = useState(false)
  const [releaseNotesOpen, setReleaseNotesOpen] = useState(false)
  const [experienceBusy, setExperienceBusy] = useState(false)
  const [receipts, setReceipts] = useState<Receipt[]>([])
  const [activeReceipt, setActiveReceipt] = useState<Receipt | null>(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ kind: 'success' | 'error'; text: string } | null>(null)

  const refresh = useCallback(async () => {
    const [nextStatus, nextReceipts] = await Promise.all([api.status(), api.receipts()])
    setStatus(nextStatus)
    setReceipts(nextReceipts)
  }, [])

  useEffect(() => {
    api
      .authState()
      .then((state) => {
        setNeedsSetup(state.needs_setup)
        setAuthenticated(state.authenticated)
        setCurrentUser(state.user)
        setIdentifierRequired(Boolean(state.identifier_required))
        setOfflineMode(false)
        rememberAuthenticatedDevice(state.authenticated)
      })
      .catch((error) => {
        if (error instanceof ApiNetworkError && wasAuthenticatedOnDevice()) {
          setAuthenticated(true)
          setOfflineMode(true)
          setMessage({ kind: 'error', text: 'Offline-Modus: Scans werden nur lokal vorgemerkt und später bestätigt.' })
          return
        }
        setAuthenticated(false)
      })
  }, [])

  useEffect(() => {
    if (!authenticated) return
    refresh().catch((error) => {
      if (error instanceof ApiNetworkError) setOfflineMode(true)
      setMessage({ kind: 'error', text: error instanceof ApiNetworkError
        ? 'Offline-Modus: Scans werden nur lokal vorgemerkt und später bestätigt.'
        : error.message })
    })
  }, [authenticated, refresh])

  useEffect(() => {
    if (!authenticated || offlineMode) return
    api.experience().then((nextExperience) => {
      setExperience(nextExperience)
      const automaticSurface = automaticExperienceSurface(nextExperience)
      if (automaticSurface === 'onboarding') setGuideOpen(true)
      else if (automaticSurface === 'release') setReleaseNotesOpen(true)
    }).catch((error) => {
      setMessage({ kind: 'error', text: `Einführung konnte nicht geladen werden: ${(error as Error).message}` })
    })
  }, [authenticated, offlineMode])

  useEffect(() => {
    if (!offlineMode) return undefined
    const reconnect = () => {
      api.authState().then((state) => {
        rememberAuthenticatedDevice(state.authenticated)
        setNeedsSetup(state.needs_setup)
        setAuthenticated(state.authenticated)
        setCurrentUser(state.user)
        setIdentifierRequired(Boolean(state.identifier_required))
        setOfflineMode(false)
        if (state.authenticated) refresh().catch(() => undefined)
      }).catch(() => undefined)
    }
    window.addEventListener('online', reconnect)
    return () => window.removeEventListener('online', reconnect)
  }, [offlineMode, refresh])

  const openReceipt = async (id: string) => {
    setBusy(true)
    try {
      const receipt = await api.receipt(id)
      setActiveReceipt(receipt)
      setScreen('review')
    } catch (error) {
      setMessage({ kind: 'error', text: (error as Error).message })
    } finally {
      setBusy(false)
    }
  }

  const analyzeFile = async (file?: File) => {
    if (!file) return
    setBusy(true)
    setMessage(null)
    try {
      const receipt = await api.analyze(file)
      setActiveReceipt(receipt)
      setScreen('review')
      if (receipt.duplicate) {
        setMessage({ kind: 'success', text: 'Dieser Bon war schon vorhanden – vorhandene Prüfung geöffnet.' })
      }
      await refresh()
    } catch (error) {
      const text = (error as Error).message
      setMessage({ kind: 'error', text })
      if (error instanceof ApiError && error.status === 409) setScreen('settings')
    } finally {
      setBusy(false)
    }
  }

  if (inviteToken) return <InvitationAccept token={inviteToken} onSuccess={(state) => {
    window.history.replaceState({}, '', window.location.pathname)
    setInviteToken(null)
    rememberAuthenticatedDevice(true)
    setAuthenticated(true)
    setCurrentUser(state.user)
    setIdentifierRequired(true)
  }} />
  if (authenticated === null) return <Splash />
  if (needsSetup) return <Setup onSuccess={(state) => { rememberAuthenticatedDevice(true); setNeedsSetup(false); setAuthenticated(true); setCurrentUser(state.user) }} />
  if (!authenticated) return <Login identifierRequired={identifierRequired} onSuccess={(state) => { rememberAuthenticatedDevice(true); setAuthenticated(true); setCurrentUser(state.user); setIdentifierRequired(Boolean(state.identifier_required)) }} />

  const readOnly = currentUser?.role === 'viewer'

  const completeGuide = async (destination: Screen) => {
    setExperienceBusy(true)
    try {
      const nextExperience = await api.updateExperience({
        complete_onboarding: true,
        acknowledge_current_version: true,
      })
      setExperience(nextExperience)
      setGuideOpen(false)
      setReleaseNotesOpen(false)
      setScreen(readOnly && destination === 'scan' ? 'catalog' : destination)
    } catch (error) {
      setMessage({ kind: 'error', text: (error as Error).message })
    } finally {
      setExperienceBusy(false)
    }
  }

  const acknowledgeRelease = async () => {
    setExperienceBusy(true)
    try {
      const nextExperience = await api.updateExperience({ acknowledge_current_version: true })
      setExperience(nextExperience)
      setReleaseNotesOpen(false)
    } catch (error) {
      setMessage({ kind: 'error', text: (error as Error).message })
    } finally {
      setExperienceBusy(false)
    }
  }

  return (
    <main className="app-shell">
      <DesktopNav selected={screen} onSelect={setScreen} status={status} role={currentUser?.role || 'viewer'} />
      <div className="app-workspace">
        {message && <Toast {...message} onClose={() => setMessage(null)} />}
        {busy && <BusyOverlay />}

        {screen === 'home' && (
          <HomeScreen
            status={status}
            receipts={receipts}
            onCapture={analyzeFile}
            onOpenReceipt={openReceipt}
            readOnly={readOnly}
          />
        )}
        {screen === 'scan' && !readOnly && <ScannerScreen onNotice={(kind, text) => {
          setMessage({ kind, text })
          refresh().catch(() => undefined)
        }} />}
        {screen === 'history' && <ShoppingScreen receipts={receipts} onOpenReceipt={openReceipt} readOnly={readOnly} canManageBudget={currentUser?.role === 'owner' || currentUser?.role === 'admin'} onNotice={(kind, text) => {
          setMessage({ kind, text })
          refresh().catch(() => undefined)
        }} />}
        {screen === 'catalog' && <CatalogScreen grocyEnabled={Boolean(status?.grocy_enabled)} role={currentUser?.role || 'viewer'} onNotice={(kind, text) => {
          setMessage({ kind, text })
          refresh().catch(() => undefined)
        }} />}
        {screen === 'settings' && (
          <SettingsScreen
            currentUser={currentUser}
            version={experience?.current_version || status?.version || ''}
            onOpenGuide={() => setGuideOpen(true)}
            onOpenReleaseNotes={() => setReleaseNotesOpen(true)}
            onIdentityChange={setCurrentUser}
            onSaved={async (text) => {
              setMessage({ kind: 'success', text })
              await refresh()
            }}
            onLogout={async () => {
              await api.logout()
              rememberAuthenticatedDevice(false)
              setMessage(null)
              setExperience(null)
              setGuideOpen(false)
              setReleaseNotesOpen(false)
              setAuthenticated(false)
              setCurrentUser(null)
            }}
          />
        )}
        {screen === 'review' && activeReceipt && (
          <ReviewScreen
            receipt={activeReceipt}
            readOnly={readOnly}
            onBack={() => {
              setScreen('home')
              refresh().catch(() => undefined)
            }}
            onChange={setActiveReceipt}
            onImported={async (nextReceipt, imported, failed, grocyFailed) => {
              setActiveReceipt(nextReceipt)
              setMessage({
                kind: failed ? 'error' : 'success',
                text: failed
                  ? `${imported} Artikel übernommen, ${failed} bitte prüfen.`
                  : grocyFailed
                    ? `${imported} Artikel sind in Vorrio. ${grocyFailed} Grocy-Exporte sind offen.`
                    : `${imported} Artikel wurden in den Vorrio-Bestand übernommen.`,
              })
              await refresh()
            }}
          />
        )}

        {screen !== 'review' && <BottomNav selected={screen} onSelect={setScreen} role={currentUser?.role || 'viewer'} />}
        {guideOpen && <OnboardingGuide
          readOnly={readOnly}
          busy={experienceBusy}
          onComplete={completeGuide}
          onDismiss={() => setGuideOpen(false)}
        />}
        {releaseNotesOpen && experience && <ReleaseNotesDialog
          experience={experience}
          busy={experienceBusy}
          onAcknowledge={acknowledgeRelease}
          onDismiss={() => setReleaseNotesOpen(false)}
        />}
      </div>
    </main>
  )
}

function Splash() {
  return (
    <main className="splash">
      <img src="/pwa-icon.png" alt="" />
      <LoaderCircle className="spin" aria-label="App wird geladen" />
    </main>
  )
}

function Login({ identifierRequired, onSuccess }: { identifierRequired: boolean; onSuccess: (state: Awaited<ReturnType<typeof api.login>>) => void }) {
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [mfaChallenge, setMfaChallenge] = useState('')
  const [securityCode, setSecurityCode] = useState('')
  const [recoveryMode, setRecoveryMode] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (recoveryMode) {
        const state = await api.recoveryLogin(identifier, securityCode)
        onSuccess(state)
        return
      }
      if (mfaChallenge) {
        const state = await api.verifyMfa(mfaChallenge, securityCode)
        onSuccess(state)
        return
      }
      const state = await api.login(password, identifier)
      if (state.mfa_required && state.mfa_challenge) {
        setMfaChallenge(state.mfa_challenge)
        setPassword('')
        return
      }
      onSuccess(state)
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const loginWithPasskey = async () => {
    setBusy(true)
    setError('')
    try {
      const begin = await api.beginPasskeyAuthentication()
      const credential = await startAuthentication({ optionsJSON: begin.options as never })
      onSuccess(await api.completePasskeyAuthentication(begin.challenge_id, credential))
    } catch (nextError) {
      setError((nextError as Error).message || 'Passkey-Anmeldung wurde abgebrochen.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <img className="login-icon" src="/pwa-icon.png" alt="" />
        <h1>Vorrio</h1>
        <p>Einkäufe, Vorräte und Produktwissen einfach im eigenen Haushalt verwalten.</p>
        <form onSubmit={submit}>
          {(identifierRequired || recoveryMode) && !mfaChallenge && <>
            <label htmlFor="identifier">E-Mail</label>
            <input id="identifier" type="email" value={identifier} onChange={(event) => setIdentifier(event.target.value)} autoComplete="username" autoFocus />
          </>}
          {!mfaChallenge && !recoveryMode && <>
            <label htmlFor="password">{identifierRequired ? 'Passwort' : 'Haushalts-Passwort'}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              autoFocus={!identifierRequired}
            />
          </>}
          {(mfaChallenge || recoveryMode) && <>
            <label htmlFor="security-code">{recoveryMode ? 'Wiederherstellungscode' : 'Code aus der Authenticator-App'}</label>
            <input id="security-code" value={securityCode} onChange={(event) => setSecurityCode(event.target.value)} autoComplete={recoveryMode ? 'off' : 'one-time-code'} inputMode={recoveryMode ? 'text' : 'numeric'} autoFocus />
            {mfaChallenge && <small className="login-helper">Alternativ funktioniert hier ein noch unbenutzter Wiederherstellungscode.</small>}
          </>}
          {error && <p className="field-error">{error}</p>}
          <button className="button primary full" disabled={busy || (recoveryMode ? !identifier || !securityCode : mfaChallenge ? !securityCode : !password || (identifierRequired && !identifier))}>
            {busy ? <LoaderCircle className="spin" /> : <Sparkles />}
            {recoveryMode ? 'Konto wiederherstellen' : mfaChallenge ? 'Code bestätigen' : 'Anmelden'}
          </button>
          {!mfaChallenge && !recoveryMode && typeof window.PublicKeyCredential !== 'undefined' && <button type="button" className="button tertiary full passkey-login" onClick={loginWithPasskey} disabled={busy || !window.isSecureContext}><KeyRound /> Mit Passkey anmelden</button>}
          {!mfaChallenge && <button type="button" className="text-button" onClick={() => { setRecoveryMode(!recoveryMode); setSecurityCode(''); setError('') }}>{recoveryMode ? 'Zur normalen Anmeldung' : 'Wiederherstellungscode verwenden'}</button>}
          {mfaChallenge && <button type="button" className="text-button" onClick={() => { setMfaChallenge(''); setSecurityCode(''); setError('') }}>Zurück</button>}
        </form>
      </section>
    </main>
  )
}

const roleLabels: Record<AuthenticatedUser['role'], string> = {
  owner: 'Owner',
  admin: 'Admin',
  member: 'Mitglied',
  viewer: 'Nur ansehen',
}

function InvitationAccept({ token, onSuccess }: { token: string; onSuccess: (state: Awaited<ReturnType<typeof api.acceptHouseholdInvitation>>) => void }) {
  const [invitation, setInvitation] = useState<HouseholdInvitationPublic | null>(null)
  const [password, setPassword] = useState('')
  const [repeat, setRepeat] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.householdInvitation(token).then(setInvitation).catch((nextError) => setError((nextError as Error).message))
  }, [token])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (password !== repeat) {
      setError('Die Passwörter stimmen nicht überein.')
      return
    }
    setBusy(true)
    setError('')
    try {
      onSuccess(await api.acceptHouseholdInvitation(token, password))
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel invitation-panel">
        <img className="login-icon" src="/pwa-icon.png" alt="" />
        <h1>Einladung zu Vorrio</h1>
        {!invitation && !error && <div className="inline-loading"><LoaderCircle className="spin" /> Einladung wird geprüft…</div>}
        {invitation && <>
          <p><strong>{invitation.display_name}</strong>, du wurdest zu <strong>{invitation.household_name}</strong> eingeladen.</p>
          <div className="invitation-summary"><Mail /><span><strong>{invitation.email}</strong><small>Rolle: {roleLabels[invitation.role]}</small></span></div>
          <form onSubmit={submit}>
            <label htmlFor="invite-password">Eigenes Passwort</label>
            <input id="invite-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" minLength={10} autoFocus />
            <label htmlFor="invite-repeat">Passwort wiederholen</label>
            <input id="invite-repeat" type="password" value={repeat} onChange={(event) => setRepeat(event.target.value)} autoComplete="new-password" minLength={10} />
            {error && <p className="field-error">{error}</p>}
            <button className="button primary full" disabled={busy || password.length < 10 || repeat.length < 10}>
              {busy ? <LoaderCircle className="spin" /> : <CheckCircle2 />} Konto erstellen
            </button>
          </form>
        </>}
        {!invitation && error && <p className="field-error">{error}</p>}
      </section>
    </main>
  )
}

function Setup({ onSuccess }: { onSuccess: (state: Awaited<ReturnType<typeof api.setup>>) => void }) {
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [repeat, setRepeat] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (password !== repeat) {
      setError('Die Passwörter stimmen nicht überein.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const state = await api.setup(password, displayName)
      onSuccess(state)
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <img className="login-icon" src="/pwa-icon.png" alt="" />
        <h1>Fast geschafft</h1>
        <p>Lege den ersten Owner und das Haushalts-Passwort für Vorrio fest.</p>
        <form onSubmit={submit}>
          <label htmlFor="owner-name">Dein Name</label>
          <input id="owner-name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} autoComplete="name" minLength={2} autoFocus />
          <label htmlFor="new-password">Neues Passwort</label>
          <input id="new-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" minLength={10} />
          <label htmlFor="repeat-password">Passwort wiederholen</label>
          <input id="repeat-password" type="password" value={repeat} onChange={(event) => setRepeat(event.target.value)} autoComplete="new-password" minLength={10} />
          {error && <p className="field-error">{error}</p>}
          <button className="button primary full" disabled={busy || displayName.trim().length < 2 || password.length < 10 || repeat.length < 10}>
            {busy ? <LoaderCircle className="spin" /> : <CheckCircle2 />}
            App einrichten
          </button>
        </form>
      </section>
    </main>
  )
}

function HomeScreen({
  status,
  receipts,
  onCapture,
  onOpenReceipt,
  readOnly,
}: {
  status: AppStatus | null
  receipts: Receipt[]
  onCapture: (file?: File) => void
  onOpenReceipt: (id: string) => void
  readOnly: boolean
}) {
  const cameraInput = useRef<HTMLInputElement>(null)
  const uploadInput = useRef<HTMLInputElement>(null)
  const recent = receipts.slice(0, 2)
  const connected = Boolean(status)
  const connectionLabel = status?.grocy_enabled
    ? status.grocy_connected
      ? `Eigener Katalog · Grocy verbunden`
      : `Eigener Katalog · Grocy offline`
    : `Eigener Katalog · ${status?.catalog.products || 0} ${(status?.catalog.products || 0) === 1 ? 'Produkt' : 'Produkte'}`

  return (
    <div className="screen home-screen">
      <header className="brand-header">
        <div className="brand-lockup">
          <ReceiptText aria-hidden="true" />
          <strong>Vorrio</strong>
        </div>
        <div className={`connection-state ${connected ? 'connected' : 'disconnected'}`}>
          <span />
          {connectionLabel}
        </div>
      </header>

      <div className="home-workspace">
        <div className="home-capture-column">
          <section className="intro">
            <h1>Einkauf übernehmen</h1>
            <p>Bon fotografieren – Vorrio bereitet Bestand und Preise vor.</p>
          </section>

          {!readOnly ? <section className="capture-panel" aria-label="Bon erfassen">
            <div className="scan-stage">
              <i className="corner top-left" />
              <i className="corner top-right" />
              <i className="corner bottom-left" />
              <i className="corner bottom-right" />
              <img src="/assets/receipt-folded.png" alt="Gefalteter Kassenbon" />
              <span className="camera-orb"><Camera /></span>
            </div>
            <input
              ref={cameraInput}
              className="visually-hidden"
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(event) => {
                onCapture(event.target.files?.[0])
                event.currentTarget.value = ''
              }}
            />
            <input
              ref={uploadInput}
              className="visually-hidden"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic,application/pdf,.pdf"
              onChange={(event) => {
                onCapture(event.target.files?.[0])
                event.currentTarget.value = ''
              }}
            />
            <button className="button primary full" onClick={() => cameraInput.current?.click()}>
              <Camera /> Bon fotografieren
            </button>
            <button className="button secondary full" onClick={() => uploadInput.current?.click()}>
              <FileUp /> Bild oder PDF hochladen
            </button>
          </section> : <section className="read-only-callout"><ShieldCheck /><div><strong>Nur ansehen</strong><p>Du kannst Vorräte, Preise, Listen und Bons lesen. Änderungen sind für diese Rolle gesperrt.</p></div></section>}
        </div>

        <section className="recent-section">
        <h2>Letzte Einkäufe</h2>
        {recent.length ? (
          <div className="purchase-list">
            {recent.map((receipt) => (
              <button className="purchase-row" key={receipt.id} onClick={() => onOpenReceipt(receipt.id)}>
                <span className="purchase-icon"><PackageCheck /></span>
                <span className="purchase-copy">
                  <strong>{receipt.store_name || 'Einkauf'}</strong>
                  <span>{shortDate(receipt.purchase_date)} · {receipt.item_count || 0} Artikel · {euro(receipt.total)}</span>
                </span>
                <span className={`purchase-status ${receipt.status}`}>
                  {receipt.status === 'imported' ? 'Übernommen' : receipt.review_count ? 'Prüfen' : 'Bereit'}
                </span>
                <ChevronRight />
              </button>
            ))}
          </div>
        ) : (
          <div className="empty-row">
            <ReceiptText />
            <span><strong>Noch kein Einkauf</strong>Dein erster fotografierter Bon erscheint hier.</span>
          </div>
        )}
        </section>
      </div>
    </div>
  )
}

function ReviewScreen({
  receipt,
  readOnly,
  onBack,
  onChange,
  onImported,
}: {
  receipt: Receipt
  readOnly: boolean
  onBack: () => void
  onChange: (receipt: Receipt) => void
  onImported: (receipt: Receipt, imported: number, failed: number, grocyFailed: number) => void
}) {
  const [mappingItem, setMappingItem] = useState<ReceiptItem | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [importError, setImportError] = useState('')
  const items = receipt.items || []
  const visible = expanded ? items : items.slice(0, 4)
  const ready = items.filter((item) => item.catalog_product_id && !item.imported).length
  const review = items.filter((item) => !item.catalog_product_id).length
  const imported = items.filter((item) => Boolean(item.imported)).length
  const allImported = items.length > 0 && imported === items.length
  const itemValue = items.reduce((sum, item) => {
    const value = item.total_price ?? (
      item.unit_price == null ? 0 : item.unit_price * item.quantity
    )
    return sum + value
  }, 0)
  const adjustment = receipt.total == null ? 0 : receipt.total - itemValue

  const doImport = async () => {
    setImportError('')
    setBusy(true)
    try {
      const result = await api.importReceipt(receipt.id)
      onImported(result.receipt, result.imported, result.failed, result.grocy_failed)
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Die Übernahme ist fehlgeschlagen')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="review-screen">
      <header className="review-header">
        <button className="icon-button" onClick={onBack} aria-label="Zurück"><ArrowLeft /></button>
        <h1>Einkauf prüfen</h1>
        <span className="header-spacer" />
      </header>
      <div className="receipt-edge" aria-hidden="true" />
      <section className="review-summary">
        <p>{items.length} Artikel erkannt · {receipt.store_name || 'Geschäft offen'}</p>
        <div className="review-counts">
          {imported > 0 && <strong className="imported"><CheckCircle2 /> {imported} übernommen</strong>}
          {imported > 0 && (ready > 0 || review > 0) && <i />}
          {ready > 0 && <strong className="ready"><CheckCircle2 /> {ready} bereit</strong>}
          {ready > 0 && review > 0 && <i />}
          {review > 0 && <strong className="needs-review"><AlertCircle /> {review} prüfen</strong>}
        </div>
      </section>

      <section className="receipt-items">
        {visible.map((item) => (
          <ReceiptItemRow item={item} key={item.id} readOnly={readOnly} onMap={() => setMappingItem(item)} />
        ))}
        {items.length > 4 && (
          <button className="show-all" onClick={() => setExpanded((value) => !value)}>
            {expanded ? 'Weniger anzeigen' : `Alle ${items.length} Artikel anzeigen`}
            <ChevronDown className={expanded ? 'rotated' : ''} />
          </button>
        )}
      </section>

      <section className="import-bar">
        <div className="total-line"><span>Bon-Gesamt</span><strong>{euro(receipt.total)}</strong></div>
        {Math.abs(adjustment) >= 0.01 && (
          <p className="adjustment-note">
            <strong>{euro(itemValue)} Warenwert</strong>
            <span>
              {adjustment > 0
                ? `${euro(adjustment)} Pfand/Bonposten bleiben außerhalb des Vorrats.`
                : `${euro(Math.abs(adjustment))} Rabatte/Bonposten sind im Gesamtbetrag verrechnet.`}
            </span>
          </p>
        )}
        {readOnly ? (
          <div className="read-only-callout compact"><ShieldCheck /><span><strong>Nur ansehen</strong><small>Zuordnen und Übernehmen sind für diese Rolle gesperrt.</small></span></div>
        ) : (
          <button className={`button primary full ${allImported ? 'complete' : ''}`} disabled={!ready || busy} onClick={doImport}>
            {busy ? <LoaderCircle className="spin" /> : <CheckCircle2 />}
            {allImported ? `${imported} Artikel im Vorrat` : `${ready} Artikel in den Vorrat`}
          </button>
        )}
        {importError && <p className="field-error" role="alert">{importError}</p>}
        <button className="text-button" onClick={onBack}>{allImported ? 'Zurück zur Übersicht' : 'Später fortsetzen'}</button>
      </section>

      {mappingItem && !readOnly && (
        <ProductPicker
          receiptId={receipt.id}
          item={mappingItem}
          onClose={() => setMappingItem(null)}
          onMapped={(next) => { onChange(next); setMappingItem(null) }}
        />
      )}
    </div>
  )
}

function ReceiptItemRow({ item, readOnly, onMap }: { item: ReceiptItem; readOnly: boolean; onMap: () => void }) {
  const mapped = Boolean(item.catalog_product_id)
  const imported = Boolean(item.imported)
  const unitPrice = item.unit_price ?? (item.total_price && item.quantity ? item.total_price / item.quantity : null)
  const totalPrice = item.total_price ?? (unitPrice == null ? null : unitPrice * item.quantity)
  const hasQuantityBreakdown = Math.abs(item.quantity - 1) > 0.0001 && unitPrice != null
  const packageLabel = item.catalog_variant_package_amount && item.catalog_variant_package_unit
    ? `${quantity(item.catalog_variant_package_amount)} ${item.catalog_variant_package_unit}`
    : null
  const variantDetail = [
    item.catalog_variant_brand,
    item.catalog_variant_name,
    packageLabel,
  ].filter(Boolean).join(' · ')
  const productDetail = variantDetail || item.catalog_product_name || item.suggested_catalog_product_name || 'Noch nicht zugeordnet'
  const detail = hasQuantityBreakdown
    ? `${productDetail} · ${quantity(item.quantity)} × ${euro(unitPrice)}`
    : productDetail
  const reasonFallback: Record<string, string> = {
    barcode: 'Barcode stimmt exakt',
    learned_store: 'Für dieses Geschäft gelernt',
    confirmed_alias: 'Schon einmal bestätigt',
    exact_name: 'Produktname stimmt exakt',
    manual: 'Manuell zugeordnet',
    fuzzy_name: `${Math.round(item.suggested_catalog_product_score || item.match_score || 0)} % ähnlich – bitte prüfen`,
    unresolved: 'Noch nicht zugeordnet',
  }
  const evidenceLabel = imported
    ? 'Im Vorrio-Bestand'
    : item.match_evidence?.[0]?.label || reasonFallback[item.match_reason] || (
      item.suggested_catalog_product_name
        ? `${Math.round(item.suggested_catalog_product_score || 0)} % ähnlich – bitte prüfen`
        : mapped
          ? 'Produkt zugeordnet'
          : 'Noch nicht zugeordnet'
    )
  return (
    <button
      className={`receipt-item ${mapped ? '' : 'unresolved'} ${item.suggested_catalog_product_name ? 'suggested' : ''} ${imported ? 'imported' : ''}`}
      onClick={onMap}
      disabled={imported || readOnly}
    >
      <span className={`item-icon ${item.catalog_product_image_url ? 'has-image' : ''}`}>
        {mapped ? <ProductIcon name={item.normalized_name || item.raw_name} /> : <AlertCircle />}
        {item.catalog_product_image_url && (
          <img
            src={item.catalog_product_image_url}
            alt=""
            loading="lazy"
            onError={(event) => { event.currentTarget.style.display = 'none' }}
          />
        )}
      </span>
      <span className="item-copy">
        <strong>{item.normalized_name || item.raw_name}</strong>
        <small>{detail}</small>
        <span className={`match-evidence ${mapped || imported ? 'resolved' : item.suggested_catalog_product_name ? 'suggestion' : 'unresolved'}`}>
          {evidenceLabel}
        </span>
      </span>
      <span className="item-price">{euro(totalPrice)}</span>
      {mapped ? <CheckCircle2 className="mapped-check" /> : <span className="map-action">{readOnly ? 'Offen' : item.suggested_catalog_product_name ? 'Prüfen' : 'Zuordnen'}</span>}
      {imported || readOnly ? <span aria-hidden="true" /> : <ChevronRight />}
    </button>
  )
}

function ProductIcon({ name }: { name: string }) {
  const value = name.toLowerCase()
  if (value.includes('banan')) return <Banana />
  if (value.includes('milch')) return <Milk />
  if (value.includes('brot') || value.includes('toast')) return <Sandwich />
  return <PackageCheck />
}

type MissingMasterSuggestions = {
  location: string | null
  unit: string | null
  group: string | null
}

function MissingMasterSuggestion({
  label,
  value,
  accepted,
  onValueChange,
  onToggle,
  children,
}: {
  label: string
  value: string
  accepted: boolean
  onValueChange: (value: string) => void
  onToggle: () => void
  children?: ReactNode
}) {
  return (
    <section className="missing-master-suggestion">
      <div className="missing-master-heading">
        <Sparkles />
        <div>
          <strong>„{value || 'Ohne Namen'}“ fehlt im Vorrio-Katalog</strong>
          <small>Vorhandenen Wert oben wählen oder den Vorschlag bearbeiten und neu anlegen.</small>
        </div>
      </div>
      <label>{label}-Vorschlag umbenennen<input value={value} onChange={(event) => onValueChange(event.target.value)} /></label>
      {children}
      <button
        type="button"
        className={`master-create-choice ${accepted ? 'accepted' : ''}`}
        aria-pressed={accepted}
        disabled={!value.trim()}
        onClick={onToggle}
      >
        {accepted ? <CheckCircle2 /> : <PackagePlus />}
        {accepted ? `„${value}“ wird neu angelegt` : `${label} neu anlegen`}
      </button>
    </section>
  )
}

function ProductPicker({
  receiptId,
  item,
  onClose,
  onMapped,
}: {
  receiptId: string
  item: ReceiptItem
  onClose: () => void
  onMapped: (receipt: Receipt) => void
}) {
  const [query, setQuery] = useState(item.normalized_name || item.raw_name)
  const [products, setProducts] = useState<CatalogProduct[]>([])
  const [candidateSearch, setCandidateSearch] = useState<ProductCandidateSearch | null>(null)
  const [candidateBusy, setCandidateBusy] = useState(true)
  const [selectedCandidate, setSelectedCandidate] = useState<ProductCandidate | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)
  const [masterData, setMasterData] = useState<GrocyMasterData | null>(null)
  const [draft, setDraft] = useState<CatalogProductCreateInput | null>(null)
  const [missingMaster, setMissingMaster] = useState<MissingMasterSuggestions>({
    location: null,
    unit: null,
    group: null,
  })

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setBusy(true)
      api.products(query).then(setProducts).catch((next) => setError(next.message)).finally(() => setBusy(false))
    }, 220)
    return () => window.clearTimeout(timer)
  }, [query])

  useEffect(() => {
    let active = true
    setCandidateBusy(true)
    api.itemCandidates(receiptId, item.id)
      .then((result) => { if (active) setCandidateSearch(result) })
      .catch((next) => { if (active) setError(next.message) })
      .finally(() => { if (active) setCandidateBusy(false) })
    return () => { active = false }
  }, [receiptId, item.id])

  const choose = async (product: Pick<CatalogProduct, 'id' | 'name'>) => {
    setBusy(true)
    try {
      onMapped(await api.mapItem(receiptId, item.id, product))
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const firstMatching = (
    rows: { id: number; name: string }[],
    terms: string[],
  ) => {
    for (const term of terms) {
      const needle = term.trim().toLowerCase()
      if (!needle) continue
      const row = rows.find((candidate) => candidate.name.toLowerCase().includes(needle))
      if (row) return row
    }
    return undefined
  }

  const exactMatching = (
    rows: { id: number; name: string }[],
    term: string,
  ) => rows.find((candidate) => candidate.name.trim().localeCompare(term.trim(), 'de', { sensitivity: 'base' }) === 0)

  const confirmExistingCandidate = async (candidate: ProductCandidate) => {
    if (!candidate.local_product_id) return
    setBusy(true)
    setError('')
    try {
      onMapped(await api.confirmItemCandidate(receiptId, item.id, {
        source: candidate.source,
        external_id: candidate.external_id,
        product_id: candidate.local_product_id,
        name: null,
        location_id: null,
        new_location_name: null,
        new_location_is_freezer: false,
        quantity_unit_id: null,
        new_quantity_unit_name: null,
        product_group_id: null,
        new_product_group_name: null,
        default_best_before_days: 0,
        remember: true,
      }))
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const openCreate = async (candidate: ProductCandidate | null = null) => {
    setBusy(true)
    setError('')
    try {
      const master = await api.catalogMasterData()
      if (!master.locations.length || !master.quantity_units.length) {
        throw new Error('In Vorrio fehlen Lagerorte oder Mengeneinheiten.')
      }
      const value = `${candidate?.name || item.normalized_name || ''} ${item.raw_name}`.toLowerCase()
      const chilled = /(mortadella|salami|frischkäse|salat|joghurt|froop|pudding|porridge|highpro)/.test(value)
      const bathroom = /(gesichtswasser|pflege|kosmetik)/.test(value)
      const locationSuggestion = item.suggested_location?.trim() || ''
      const exactLocation = locationSuggestion ? exactMatching(master.locations, locationSuggestion) : undefined
      const location = exactLocation || (!locationSuggestion
        ? firstMatching(master.locations, [bathroom ? 'badezimmer' : chilled ? 'kühlschrank' : 'vorratskammer', 'kammer'])
        : undefined)
      const unitTerms = value.includes('banan')
        ? ['kilogramm', 'kg']
        : /(froop|joghurt|pudding)/.test(value)
          ? ['becher']
          : /(red bull|r\.bull|rb sea)/.test(value)
            ? ['dose']
            : bathroom
              ? ['flasche']
              : ['packung', 'pack', 'stück', 'piece']
      const unitSuggestion = item.suggested_unit?.trim() || ''
      const exactUnit = unitSuggestion ? exactMatching(master.quantity_units, unitSuggestion) : undefined
      const unit = exactUnit || (!unitSuggestion ? firstMatching(master.quantity_units, unitTerms) : undefined)
      const groupTerms = bathroom
        ? ['haushalt', 'pflege']
        : chilled
          ? ['kühl']
          : /(banan|heidelbe|tomat)/.test(value)
            ? ['obst', 'gemüse']
            : /(bröt|brezel)/.test(value)
              ? ['back']
              : /(heineken|red bull|r\.bull|rb sea)/.test(value)
                ? ['getränk']
                : ['vorrat', 'snack']
      const groupSuggestion = item.suggested_product_group?.trim() || ''
      const exactGroup = groupSuggestion ? exactMatching(master.product_groups, groupSuggestion) : undefined
      const group = exactGroup || (!groupSuggestion ? firstMatching(master.product_groups, groupTerms) : undefined)
      const fallbackBestBeforeDays = bathroom
        ? 730
        : /(bröt|brezel)/.test(value)
          ? 3
          : chilled
            ? 10
            : /(banan|heidelbe|tomat)/.test(value)
              ? 7
              : 180
      const bestBeforeDays = item.suggested_best_before_days ?? fallbackBestBeforeDays
      setSelectedCandidate(candidate)
      setMasterData(master)
      setMissingMaster({
        location: locationSuggestion && !exactLocation ? locationSuggestion : null,
        unit: unitSuggestion && !exactUnit ? unitSuggestion : null,
        group: groupSuggestion && !exactGroup ? groupSuggestion : null,
      })
      setDraft({
        name: candidate?.name || item.normalized_name || item.raw_name,
        location_id: location?.id || (locationSuggestion ? null : master.locations[0].id),
        new_location_name: null,
        new_location_is_freezer: /(tiefkühl|gefrier|freezer)/i.test(locationSuggestion),
        quantity_unit_id: unit?.id || (unitSuggestion ? null : master.quantity_units[0].id),
        new_quantity_unit_name: null,
        product_group_id: group?.id || null,
        new_product_group_name: null,
        default_best_before_days: bestBeforeDays,
        minimum_stock_quantity: 0,
        shopping_target_quantity: 0,
        brand: candidate?.brand || item.brand,
        barcode: candidate?.barcode || item.barcode,
        remember: true,
      })
      setCreating(true)
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const createProduct = async (event: FormEvent) => {
    event.preventDefault()
    if (!draft) return
    setBusy(true)
    setError('')
    try {
      if (selectedCandidate) {
        onMapped(await api.confirmItemCandidate(receiptId, item.id, {
          source: selectedCandidate.source,
          external_id: selectedCandidate.external_id,
          product_id: null,
          name: draft.name,
          location_id: draft.location_id,
          new_location_name: draft.new_location_name,
          new_location_is_freezer: draft.new_location_is_freezer,
          quantity_unit_id: draft.quantity_unit_id,
          new_quantity_unit_name: draft.new_quantity_unit_name,
          product_group_id: draft.product_group_id,
          new_product_group_name: draft.new_product_group_name,
          default_best_before_days: draft.default_best_before_days,
          remember: draft.remember,
        }))
      } else {
        onMapped(await api.createAndMapProduct(receiptId, item.id, draft))
      }
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const canCreate = Boolean(
    draft?.name.trim()
    && (draft.location_id || draft.new_location_name?.trim())
    && (draft.quantity_unit_id || draft.new_quantity_unit_name?.trim()),
  )

  return (
    <div className="sheet-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="product-sheet" role="dialog" aria-modal="true" aria-label="Vorrio-Produkt zuordnen" onMouseDown={(event) => event.stopPropagation()}>
        <div className="sheet-handle" />
        <header><div><h2>{creating ? (selectedCandidate ? 'Produktvorschlag übernehmen' : 'Neues Vorrio-Produkt') : 'Produkt zuordnen'}</h2><p>{item.raw_name}</p></div><button className="icon-button" onClick={onClose} aria-label="Zuordnung schließen"><X /></button></header>
        {error && <p className="field-error">{error}</p>}
        {creating && masterData && draft ? (
          <form className="product-create-form" onSubmit={createProduct}>
            {selectedCandidate && (
              <div className="selected-candidate-summary">
                <span className="candidate-image">
                  <PackageSearch />
                  {selectedCandidate.image_url && <img src={selectedCandidate.image_url} alt="" onError={(event) => { event.currentTarget.style.display = 'none' }} />}
                </span>
                <span><small>Echter Treffer · {Math.round(selectedCandidate.score)} % passend</small><strong>{selectedCandidate.name}</strong><em>{[selectedCandidate.brand, selectedCandidate.quantity].filter(Boolean).join(' · ') || 'Keine weiteren Packungsdaten'}</em></span>
              </div>
            )}
            <label>Produktname<input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} autoFocus /></label>
            <div className="create-form-grid">
              <label>Vorhandene Lagerorte ({masterData.locations.length})<select value={draft.location_id ?? ''} onChange={(event) => setDraft({ ...draft, location_id: event.target.value ? Number(event.target.value) : null, new_location_name: null })}><option value="">Bitte wählen</option>{masterData.locations.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
              <label>Vorhandene Einheiten ({masterData.quantity_units.length})<select value={draft.quantity_unit_id ?? ''} onChange={(event) => setDraft({ ...draft, quantity_unit_id: event.target.value ? Number(event.target.value) : null, new_quantity_unit_name: null })}><option value="">Bitte wählen</option>{masterData.quantity_units.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            </div>
            {missingMaster.location && (
              <MissingMasterSuggestion
                label="Lagerort"
                value={missingMaster.location}
                accepted={Boolean(draft.new_location_name)}
                onValueChange={(next) => {
                  setMissingMaster({ ...missingMaster, location: next })
                  setDraft({ ...draft, new_location_name: draft.new_location_name == null ? null : next, new_location_is_freezer: /(tiefkühl|gefrier|freezer)/i.test(next) })
                }}
                onToggle={() => setDraft({ ...draft, location_id: null, new_location_name: draft.new_location_name ? null : missingMaster.location })}
              >
                {draft.new_location_name && (
                  <label className="freezer-choice"><input type="checkbox" checked={draft.new_location_is_freezer} onChange={(event) => setDraft({ ...draft, new_location_is_freezer: event.target.checked })} /> Als Gefrierstandort markieren</label>
                )}
              </MissingMasterSuggestion>
            )}
            {missingMaster.unit && (
              <MissingMasterSuggestion
                label="Einheit"
                value={missingMaster.unit}
                accepted={Boolean(draft.new_quantity_unit_name)}
                onValueChange={(next) => {
                  setMissingMaster({ ...missingMaster, unit: next })
                  setDraft({ ...draft, new_quantity_unit_name: draft.new_quantity_unit_name == null ? null : next })
                }}
                onToggle={() => setDraft({ ...draft, quantity_unit_id: null, new_quantity_unit_name: draft.new_quantity_unit_name ? null : missingMaster.unit })}
              />
            )}
            <div className="create-form-grid">
              <label>Vorhandene Produktgruppen ({masterData.product_groups.length})<select value={draft.product_group_id ?? ''} onChange={(event) => setDraft({ ...draft, product_group_id: event.target.value ? Number(event.target.value) : null, new_product_group_name: null })}><option value="">Keine Gruppe</option>{masterData.product_groups.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
              <label>Haltbarkeit (Tage)<input type="number" min="0" max="3650" value={draft.default_best_before_days} onChange={(event) => setDraft({ ...draft, default_best_before_days: Number(event.target.value) })} /></label>
            </div>
            {missingMaster.group && (
              <MissingMasterSuggestion
                label="Produktgruppe"
                value={missingMaster.group}
                accepted={Boolean(draft.new_product_group_name)}
                onValueChange={(next) => {
                  setMissingMaster({ ...missingMaster, group: next })
                  setDraft({ ...draft, new_product_group_name: draft.new_product_group_name == null ? null : next })
                }}
                onToggle={() => setDraft({ ...draft, product_group_id: null, new_product_group_name: draft.new_product_group_name ? null : missingMaster.group })}
              />
            )}
            <p className="create-helper">
              Vorhandene Vorrio-Werte werden niemals nur wegen einer Ähnlichkeit gewählt. Fehlende Vorschläge werden erst nach deiner sichtbaren Bestätigung angelegt. Erkannte Barcodes und Marken werden als Produktvariante gespeichert.
            </p>
            <button className="button primary full" disabled={busy || !canCreate}>{busy ? <LoaderCircle className="spin" /> : <PackagePlus />} {draft.new_location_name || draft.new_quantity_unit_name || draft.new_product_group_name ? 'Produkt & Stammdaten anlegen' : 'Anlegen & zuordnen'}</button>
            <button type="button" className="text-button" onClick={() => { setCreating(false); setSelectedCandidate(null) }}>Zurück zur Suche</button>
          </form>
        ) : (
          <>
            <label className="search-field"><Search /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Vorrio-Produkt suchen" autoFocus /></label>
            <section className="candidate-section">
              <div className="candidate-heading">
                <div><Sparkles /><span><strong>Echte Produktvorschläge</strong><small>{candidateSearch?.ai_ranked ? 'Von deiner KI für diesen Einkauf sortiert' : 'Nach Bontext und Geschäft sortiert'}</small></span></div>
                {candidateSearch?.cached && <small>zwischengespeichert</small>}
              </div>
              {candidateBusy && <div className="candidate-loading"><LoaderCircle className="spin" /><span><strong>Passende Produkte werden gesucht</strong><small>Reale Bilder und Packungsdaten, keine erfundenen Treffer.</small></span></div>}
              {!candidateBusy && candidateSearch?.candidates.map((candidate) => (
                <button
                  type="button"
                  className="candidate-card"
                  key={candidate.external_id}
                  onClick={() => candidate.local_product_id ? confirmExistingCandidate(candidate) : openCreate(candidate)}
                  disabled={busy}
                >
                  <span className="candidate-image">
                    <PackageSearch />
                    {candidate.image_url && <img src={candidate.image_url} alt="" loading="lazy" onError={(event) => { event.currentTarget.style.display = 'none' }} />}
                  </span>
                  <span className="candidate-copy">
                    <span><strong>{candidate.name}</strong><em>{[candidate.brand, candidate.quantity].filter(Boolean).join(' · ') || 'Packungsdaten offen'}</em></span>
                    <span className="candidate-evidence">
                      <small>{Math.round(candidate.score)} % passend</small>
                      {candidate.store_match && <small>Geschäft passt</small>}
                      {candidate.local_product_id && <small>Schon in Vorrio</small>}
                    </span>
                    <small className="candidate-reason">{candidate.ai_reason || candidate.evidence[0]?.label || 'Bitte Produkt prüfen'}</small>
                  </span>
                  <ChevronRight />
                </button>
              ))}
              {!candidateBusy && candidateSearch && !candidateSearch.candidates.length && (
                <p className="candidate-empty">Keine verlässlichen externen Treffer. Du kannst weiterhin ein Vorrio-Produkt wählen oder neu anlegen.</p>
              )}
              {candidateSearch?.warnings.map((warning) => <p className="candidate-warning" key={warning}>{warning}</p>)}
              <p className="candidate-attribution">Produktdaten: Open Food Facts · Auswahl wird erst nach deiner Bestätigung gelernt.</p>
            </section>
            <div className="product-results">
              {item.suggested_catalog_product_id && item.suggested_catalog_product_name && (
                <button className="suggested-product" onClick={() => choose({ id: item.suggested_catalog_product_id!, name: item.suggested_catalog_product_name! })}>
                  <span><small>Vorschlag · {Math.round(item.suggested_catalog_product_score || 0)} % ähnlich</small>{item.suggested_catalog_product_name}</span><ChevronRight />
                </button>
              )}
              {busy && <div className="inline-loading"><LoaderCircle className="spin" /> Suche Produkte…</div>}
              {!busy && products.map((product) => (
                <button key={product.id} onClick={() => choose(product)}><span>{product.name}</span><ChevronRight /></button>
              ))}
              {!busy && !products.length && <p className="no-results">Kein passendes Vorrio-Produkt gefunden.</p>}
            </div>
            <button type="button" className="create-product-entry" onClick={() => openCreate()} disabled={busy}><PackagePlus /><span><strong>Neues Produkt anlegen</strong><small>Mit Lagerort, Einheit und Haltbarkeit</small></span><ChevronRight /></button>
          </>
        )}
      </section>
    </div>
  )
}

function SettingsScreen({
  currentUser,
  version,
  onOpenGuide,
  onOpenReleaseNotes,
  onIdentityChange,
  onSaved,
  onLogout,
}: {
  currentUser: AuthenticatedUser | null
  version: string
  onOpenGuide: () => void
  onOpenReleaseNotes: () => void
  onIdentityChange: (user: AuthenticatedUser | null) => void
  onSaved: (text: string) => void
  onLogout: () => void
}) {
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [identity, setIdentity] = useState<AuthenticatedUser | null>(currentUser)
  const [sessions, setSessions] = useState<AuthSession[]>([])
  const [apiTokens, setApiTokens] = useState<ApiToken[]>([])
  const [apiTokenScopes, setApiTokenScopes] = useState<ApiTokenScope[]>([])
  const [apiTokenPreset, setApiTokenPreset] = useState<'homeassistant' | 'scanner' | 'custom'>('homeassistant')
  const [apiTokenName, setApiTokenName] = useState(apiTokenPresets.homeassistant.name)
  const [selectedApiTokenScopes, setSelectedApiTokenScopes] = useState<ApiTokenScopeId[]>(apiTokenPresets.homeassistant.scopes)
  const [apiTokenExpiresDays, setApiTokenExpiresDays] = useState(90)
  const [freshApiToken, setFreshApiToken] = useState('')
  const [security, setSecurity] = useState<SecurityState | null>(null)
  const [notifications, setNotifications] = useState<NotificationState | null>(null)
  const [currentPushDeviceId, setCurrentPushDeviceId] = useState<string | null>(null)
  const [totpSetup, setTotpSetup] = useState<TotpSetup | null>(null)
  const [totpCode, setTotpCode] = useState('')
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([])
  const [reauthPassword, setReauthPassword] = useState('')
  const [reauthCode, setReauthCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [repeatPassword, setRepeatPassword] = useState('')
  const [passkeyName, setPasskeyName] = useState('Mein Passkey')
  const [members, setMembers] = useState<HouseholdMember[]>([])
  const [invitations, setInvitations] = useState<HouseholdInvitation[]>([])
  const [inviteName, setInviteName] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<Exclude<AuthenticatedUser['role'], 'owner'>>('member')
  const [freshInviteLink, setFreshInviteLink] = useState('')
  const [displayName, setDisplayName] = useState(currentUser?.display_name === 'Owner einrichten' ? '' : currentUser?.display_name || '')
  const [email, setEmail] = useState(currentUser?.email || '')
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.me(), api.authSessions(), api.security(), api.notificationState()])
      .then(async ([auth, nextSessions, nextSecurity, nextNotifications]) => {
        setIdentity(auth.user)
        onIdentityChange(auth.user)
        setDisplayName(auth.user?.display_name === 'Owner einrichten' ? '' : auth.user?.display_name || '')
        setEmail(auth.user?.email || '')
        setSessions(nextSessions)
        setSecurity(nextSecurity)
        setNotifications(nextNotifications)
        if (window.isSecureContext && 'serviceWorker' in navigator && 'PushManager' in window) {
          try {
            const registration = await navigator.serviceWorker.ready
            const subscription = await registration.pushManager.getSubscription()
            if (subscription) {
              const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(subscription.endpoint))
              const fingerprint = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('').slice(0, 16)
              setCurrentPushDeviceId(nextNotifications.subscriptions.find((device) => device.endpoint_fingerprint === fingerprint)?.id || null)
            }
          } catch {
            setCurrentPushDeviceId(null)
          }
        }
        if (auth.user?.role === 'owner') setSettings(await api.settings())
        if (auth.user?.role === 'owner' || auth.user?.role === 'admin') {
          const [nextMembers, nextInvitations, nextApiTokens, nextApiTokenScopes] = await Promise.all([
            api.householdMembers(),
            api.householdInvitations(),
            api.apiTokens(),
            api.apiTokenScopes(),
          ])
          setMembers(nextMembers)
          setInvitations(nextInvitations)
          setApiTokens(nextApiTokens)
          setApiTokenScopes(nextApiTokenScopes)
        }
        setLoaded(true)
      })
      .catch((next) => {
        setError(next.message)
        setLoaded(true)
      })
  }, [])

  const refreshSecurity = async () => setSecurity(await api.security())

  const pushAvailable = window.isSecureContext
    && 'serviceWorker' in navigator
    && 'PushManager' in window
    && 'Notification' in window

  const urlBase64ToUint8Array = (value: string) => {
    const padded = value + '='.repeat((4 - value.length % 4) % 4)
    const raw = window.atob(padded.replace(/-/g, '+').replace(/_/g, '/'))
    return Uint8Array.from(raw, (character) => character.charCodeAt(0))
  }

  const enablePush = async () => {
    if (!notifications || !pushAvailable) {
      setError('Push-Mitteilungen benötigen die installierte Vorrio-PWA über HTTPS.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') throw new Error('Mitteilungen wurden im Browser nicht erlaubt.')
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(notifications.public_key),
      })
      const serialized = subscription.toJSON()
      if (!serialized.endpoint || !serialized.keys?.p256dh || !serialized.keys?.auth) {
        throw new Error('Der Browser hat keine vollständige Push-Anmeldung geliefert.')
      }
      const device = await api.registerPushSubscription({
        endpoint: serialized.endpoint,
        keys: { p256dh: serialized.keys.p256dh, auth: serialized.keys.auth },
        device_name: 'Vorrio-Gerät',
      })
      const next = await api.saveNotificationPreferences({
        ...notifications.preferences,
        push_enabled: true,
      })
      setNotifications(next)
      setCurrentPushDeviceId(device.id)
      onSaved('Dieses Gerät erhält jetzt Vorratsmeldungen.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const saveNotificationPreferences = async () => {
    if (!notifications) return
    setBusy(true)
    setError('')
    try {
      const next = await api.saveNotificationPreferences(notifications.preferences)
      setNotifications(next)
      onSaved('Benachrichtigungen wurden gespeichert.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const testPush = async () => {
    if (!currentPushDeviceId) return
    setBusy(true)
    setError('')
    try {
      const response = await api.testPushNotification(currentPushDeviceId)
      if (!response.delivered) throw new Error('Der Push-Dienst hat die Testmeldung abgelehnt.')
      setNotifications(await api.notificationState())
      onSaved('Testmeldung wurde an dieses Gerät gesendet.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const disablePushDevice = async () => {
    if (!currentPushDeviceId || !window.confirm('Push-Mitteilungen auf diesem Gerät wirklich beenden?')) return
    setBusy(true)
    setError('')
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()
      if (subscription) await subscription.unsubscribe()
      await api.revokePushSubscription(currentPushDeviceId)
      const next = await api.notificationState()
      setNotifications(next)
      setCurrentPushDeviceId(null)
      onSaved('Dieses Gerät wurde aus den Vorratsmeldungen entfernt.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const confirmIdentity = async () => {
    setBusy(true)
    setError('')
    try {
      const next = await api.reauthenticate(reauthPassword, reauthCode)
      setSecurity(next)
      setReauthPassword('')
      setReauthCode('')
      onSaved('Identität bestätigt. Sicherheitsänderungen sind jetzt zehn Minuten freigegeben.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const addPasskey = async () => {
    if (!window.isSecureContext || typeof window.PublicKeyCredential === 'undefined') {
      setError('Passkeys benötigen Vorrio über die private HTTPS-Adresse.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const begin = await api.beginPasskeyRegistration()
      const credential = await startRegistration({ optionsJSON: begin.options as never })
      await api.completePasskeyRegistration(begin.challenge_id, credential, passkeyName.trim() || 'Mein Passkey')
      await refreshSecurity()
      onSaved('Passkey wurde sicher hinzugefügt.')
    } catch (nextError) {
      setError((nextError as Error).message || 'Passkey-Einrichtung wurde abgebrochen.')
    } finally {
      setBusy(false)
    }
  }

  const removePasskey = async (id: string) => {
    if (!window.confirm('Diesen Passkey wirklich entfernen?')) return
    setBusy(true)
    setError('')
    try {
      setSecurity(await api.deletePasskey(id))
      onSaved('Passkey wurde entfernt.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const beginTotp = async () => {
    setBusy(true)
    setError('')
    try {
      setTotpSetup(await api.setupTotp())
      setTotpCode('')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const confirmTotp = async () => {
    setBusy(true)
    setError('')
    try {
      const response = await api.enableTotp(totpCode)
      setRecoveryCodes(response.recovery_codes)
      setTotpSetup(null)
      setTotpCode('')
      await refreshSecurity()
      onSaved('Authenticator-App ist jetzt aktiv.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const disableTotp = async () => {
    if (!window.confirm('Authenticator-App wirklich deaktivieren? Passkeys und Wiederherstellungscodes bleiben bestehen.')) return
    setBusy(true)
    try {
      setSecurity(await api.disableTotp())
      onSaved('Authenticator-App wurde deaktiviert.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const replaceRecoveryCodes = async () => {
    if (security?.recovery_codes_remaining && !window.confirm('Alle bisherigen Wiederherstellungscodes werden sofort ungültig. Fortfahren?')) return
    setBusy(true)
    setError('')
    try {
      const response = await api.regenerateRecoveryCodes()
      setRecoveryCodes(response.codes)
      await refreshSecurity()
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const copyRecoveryCodes = async () => {
    try {
      await navigator.clipboard.writeText(recoveryCodes.join('\n'))
      onSaved('Wiederherstellungscodes wurden kopiert.')
    } catch {
      setError('Codes konnten nicht automatisch kopiert werden.')
    }
  }

  const selectApiTokenPreset = (preset: 'homeassistant' | 'scanner' | 'custom') => {
    setApiTokenPreset(preset)
    setApiTokenName(apiTokenPresets[preset].name)
    setSelectedApiTokenScopes(apiTokenPresets[preset].scopes)
    setFreshApiToken('')
  }

  const toggleApiTokenScope = (scope: ApiTokenScopeId) => {
    setApiTokenPreset('custom')
    setSelectedApiTokenScopes((current) => current.includes(scope)
      ? current.filter((item) => item !== scope)
      : [...current, scope])
  }

  const createApiToken = async () => {
    if (!apiTokenName.trim() || !selectedApiTokenScopes.length) return
    setBusy(true)
    setError('')
    setFreshApiToken('')
    try {
      const created = await api.createApiToken(apiTokenName.trim(), selectedApiTokenScopes, apiTokenExpiresDays)
      setFreshApiToken(created.token)
      setApiTokens(await api.apiTokens())
      onSaved('API-Token erstellt. Der vollständige Wert wird nur jetzt angezeigt.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const copyApiToken = async () => {
    try {
      await navigator.clipboard.writeText(freshApiToken)
      onSaved('API-Token wurde kopiert.')
    } catch {
      setError('API-Token konnte nicht automatisch kopiert werden.')
    }
  }

  const revokeApiToken = async (token: ApiToken) => {
    if (!window.confirm(`API-Token „${token.name}“ wirklich sofort sperren?`)) return
    setBusy(true)
    setError('')
    try {
      await api.revokeApiToken(token.id)
      setApiTokens(await api.apiTokens())
      onSaved('API-Token wurde sofort gesperrt.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const changePassword = async () => {
    if (newPassword.length < 10 || newPassword !== repeatPassword) {
      setError('Das neue Passwort braucht mindestens zehn Zeichen und beide Eingaben müssen übereinstimmen.')
      return
    }
    setBusy(true)
    setError('')
    try {
      setSecurity(await api.changePassword(newPassword))
      setNewPassword('')
      setRepeatPassword('')
      setSessions(await api.authSessions())
      onSaved('Passwort geändert; alle anderen Sitzungen wurden beendet.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const refreshFamily = async () => {
    const [nextMembers, nextInvitations] = await Promise.all([api.householdMembers(), api.householdInvitations()])
    setMembers(nextMembers)
    setInvitations(nextInvitations)
  }

  const createInvitation = async () => {
    if (!inviteName.trim() || !inviteEmail.trim()) return
    setBusy(true)
    setError('')
    setFreshInviteLink('')
    try {
      const invitation = await api.createHouseholdInvitation({
        display_name: inviteName.trim(),
        email: inviteEmail.trim(),
        role: inviteRole,
        expires_hours: 72,
      })
      const link = `${window.location.origin}${window.location.pathname}?invite=${encodeURIComponent(invitation.invite_token || '')}`
      setFreshInviteLink(link)
      setInviteName('')
      setInviteEmail('')
      await refreshFamily()
      onSaved('Einmal-Einladung wurde erstellt und ist 72 Stunden gültig.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const copyInviteLink = async () => {
    try {
      await navigator.clipboard.writeText(freshInviteLink)
      onSaved('Einladungslink wurde kopiert.')
    } catch {
      setError('Link konnte nicht automatisch kopiert werden. Bitte markiere ihn manuell.')
    }
  }

  const revokeInvitation = async (invitation: HouseholdInvitation) => {
    if (!window.confirm(`Einladung für ${invitation.display_name} wirklich zurückziehen?`)) return
    setBusy(true)
    try {
      await api.revokeHouseholdInvitation(invitation.id)
      await refreshFamily()
      onSaved('Einladung wurde zurückgezogen.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const updateMember = async (member: HouseholdMember, role: HouseholdMember['role'], active: boolean) => {
    const action = active ? 'ändern' : 'sperren'
    if (!window.confirm(`${member.display_name} wirklich ${action}?`)) return
    setBusy(true)
    setError('')
    try {
      await api.updateHouseholdMember(member.id, role, active)
      await refreshFamily()
      onSaved(active ? 'Rolle wurde aktualisiert.' : 'Zugang und aktive Sitzungen wurden gesperrt.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const saveOwner = async () => {
    if (displayName.trim().length < 2) return
    setBusy(true)
    setError('')
    try {
      const auth = await api.updateOwnerProfile(displayName.trim(), email.trim() || null)
      setIdentity(auth.user)
      onIdentityChange(auth.user)
      await refreshFamily()
      onSaved('Owner-Profil wurde lokal gespeichert.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const revokeSession = async (session: AuthSession) => {
    const question = session.current
      ? 'Diese aktuelle Sitzung wirklich beenden?'
      : `${session.device_name} wirklich abmelden?`
    if (!window.confirm(question)) return
    setBusy(true)
    setError('')
    try {
      const response = await api.revokeAuthSession(session.id)
      if (!response.authenticated) {
        onLogout()
        return
      }
      setSessions(await api.authSessions())
      onSaved('Die ausgewählte Gerätesitzung wurde beendet.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const revokeOthers = async () => {
    if (!window.confirm('Alle anderen Browser und Geräte jetzt abmelden?')) return
    setBusy(true)
    setError('')
    try {
      const response = await api.revokeOtherAuthSessions()
      setSessions(await api.authSessions())
      onSaved(response.revoked === 1 ? 'Eine andere Sitzung wurde beendet.' : `${response.revoked} andere Sitzungen wurden beendet.`)
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const save = async (event?: FormEvent) => {
    event?.preventDefault()
    if (!settings) return
    setBusy(true)
    setError('')
    try {
      const saved = await api.saveSettings(settings)
      setSettings(saved)
      onSaved('Einstellungen wurden sicher gespeichert.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const test = async (kind: 'grocy' | 'provider') => {
    if (!settings) return
    setBusy(true)
    setError('')
    setResult('')
    try {
      await api.saveSettings(settings)
      if (kind === 'grocy') await api.testGrocy()
      else await api.testProvider()
      setResult(kind === 'grocy' ? 'Grocy ist erreichbar.' : 'KI-Anbieter ist erreichbar.')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const migrateGrocyCatalog = async () => {
    if (!settings || !window.confirm('Vorhandene Grocy-Stammdaten und Produkte jetzt zusätzlich in Vorrio übernehmen? In Grocy wird nichts verändert.')) return
    setBusy(true)
    setError('')
    setResult('')
    try {
      await api.saveSettings(settings)
      const response = await api.importGrocyCatalog()
      setResult(`${response.imported.products} Grocy-Produkte wurden in Vorrio abgeglichen. Vorhandene Einträge blieben erhalten.`)
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (!loaded) return <div className="screen center-loading">{error || <LoaderCircle className="spin" />}</div>

  const updateProvider = (type: SettingsData['provider']['type']) => {
    if (!settings) return
    const preset = providerDefaults[type]
    setSettings({ ...settings, provider: { ...settings.provider, type, base_url: preset.baseUrl, model: preset.model } })
  }

  return (
    <div className="screen settings-screen">
      {result && <Toast kind="success" text={result} onClose={() => setResult('')} />}
      {error && <Toast kind="error" text={error} onClose={() => setError('')} />}
      <header className="page-header"><div><h1>Einstellungen</h1><p>Verbindungen und Datenschutz.</p></div></header>
      <form onSubmit={save}>
        <section className="settings-section help-version-section">
          <div className="section-heading"><Info /><div><h2>Hilfe & Version</h2><p>Den roten Faden erneut ansehen oder die Änderungen dieser Version nachlesen.</p></div></div>
          <div className="help-version-card">
            <span><strong>Vorrio {version ? `v${version}` : ''}</strong><small>Self-hosted · Local-first</small></span>
            <span className="help-version-actions">
              <button type="button" onClick={onOpenGuide}>Einführung öffnen</button>
              <button type="button" onClick={onOpenReleaseNotes}>Was ist neu?</button>
            </span>
          </div>
        </section>
        <section className={`settings-section identity-section ${identity?.owner_setup_complete ? '' : 'needs-setup'}`}>
          <div className="section-heading"><ShieldCheck /><div><h2>Konto & Sicherheit</h2><p>Dein persönlicher Zugang und alle aktiven Browser-Sitzungen.</p></div></div>
          {!identity?.owner_setup_complete && <p className="identity-notice"><UserRound /> Benenne jetzt den bisherigen Haushaltszugang. Dein Passwort und alle Vorrio-Daten bleiben unverändert.</p>}
          <div className="identity-role"><span>{identity?.display_name || 'Owner einrichten'}</span><strong>{roleLabels[identity?.role || 'viewer']}</strong></div>
          {identity?.role === 'owner' && <>
            <label>Name<input value={displayName} minLength={2} maxLength={100} autoComplete="name" onChange={(event) => setDisplayName(event.target.value)} /></label>
            <label>Login-E-Mail<input type="email" value={email} maxLength={320} autoComplete="email" placeholder="Vor der ersten Einladung erforderlich" onChange={(event) => setEmail(event.target.value)} /></label>
            <button type="button" className="button tertiary" onClick={saveOwner} disabled={busy || displayName.trim().length < 2}>Owner speichern</button>
          </>}

          {security && <div className="account-security">
            <div className="security-status-row">
              <span className={security.recent_authentication ? 'security-ok' : 'security-pending'}><ShieldCheck /> {security.recent_authentication ? 'Identität bestätigt' : 'Bestätigung erforderlich'}</span>
              <small>Sensible Änderungen bleiben nach Bestätigung zehn Minuten frei.</small>
            </div>
            {!security.recent_authentication && <div className="reauth-box">
              <h3>Sicherheitsänderungen freigeben</h3>
              <label>Aktuelles Passwort<input type="password" value={reauthPassword} autoComplete="current-password" onChange={(event) => setReauthPassword(event.target.value)} /></label>
              {security.totp_enabled && <label>Authenticator- oder Wiederherstellungscode<input value={reauthCode} autoComplete="one-time-code" inputMode="numeric" onChange={(event) => setReauthCode(event.target.value)} /></label>}
              <button type="button" className="button tertiary" disabled={busy || !reauthPassword || (security.totp_enabled && !reauthCode)} onClick={confirmIdentity}>Identität bestätigen</button>
            </div>}

            <div className="security-method">
              <div><h3><KeyRound /> Passkeys</h3><p>Mit Face ID, Touch ID, Windows Hello oder Sicherheitsschlüssel ohne Passwort anmelden.</p></div>
              {security.passkeys.map((passkey) => <div className="passkey-row" key={passkey.id}><span><strong>{passkey.name}</strong><small>{passkey.backed_up ? 'Synchronisierter Passkey' : 'Gerätegebundener Passkey'} · angelegt {new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium' }).format(new Date(passkey.created_at))}</small></span><button type="button" onClick={() => removePasskey(passkey.id)} disabled={busy || !security.recent_authentication}>Entfernen</button></div>)}
              {!window.isSecureContext && <p className="security-note">Zum Einrichten bitte die private HTTPS-Adresse von Vorrio öffnen.</p>}
              <label>Name für neuen Passkey<input value={passkeyName} maxLength={100} onChange={(event) => setPasskeyName(event.target.value)} /></label>
              <button type="button" className="button tertiary" onClick={addPasskey} disabled={busy || !security.recent_authentication || !window.isSecureContext}><KeyRound /> Passkey hinzufügen</button>
            </div>

            <div className="security-method">
              <div><h3>Authenticator-App</h3><p>Optionaler sechsstelliger Code zusätzlich zum Passwort.</p></div>
              {!security.totp_enabled && !totpSetup && <button type="button" className="button tertiary" onClick={beginTotp} disabled={busy || !security.recent_authentication}>Einrichten</button>}
              {totpSetup && <div className="totp-setup">
                <img src={totpSetup.qr_data_uri} alt="QR-Code für die Authenticator-App" />
                <p>Scanne den QR-Code. Falls nötig, gib diesen Schlüssel manuell ein:</p>
                <code>{totpSetup.secret}</code>
                <label>Ersten sechsstelligen Code<input value={totpCode} inputMode="numeric" autoComplete="one-time-code" maxLength={8} onChange={(event) => setTotpCode(event.target.value)} /></label>
                <button type="button" className="button tertiary" onClick={confirmTotp} disabled={busy || totpCode.replace(/\s/g, '').length !== 6}>Aktivieren</button>
              </div>}
              {security.totp_enabled && <div className="enabled-factor"><span><Check /> Aktiv</span><button type="button" onClick={disableTotp} disabled={busy || !security.recent_authentication}>Deaktivieren</button></div>}
            </div>

            <div className="security-method">
              <div><h3>Wiederherstellungscodes</h3><p>{security.recovery_codes_remaining} unbenutzte Einmalcodes. Offline und getrennt von Vorrio aufbewahren.</p></div>
              {!identity?.email && <p className="security-note">Speichere eine Login-E-Mail, damit du einen Code bei der Kontowiederherstellung deinem Konto zuordnen kannst.</p>}
              <button type="button" className="button tertiary" onClick={replaceRecoveryCodes} disabled={busy || !security.recent_authentication}>{security.recovery_codes_remaining ? 'Codes ersetzen' : 'Codes erstellen'}</button>
              {recoveryCodes.length > 0 && <div className="recovery-codes"><strong>Nur jetzt sichtbar – sicher abspeichern</strong><div>{recoveryCodes.map((code) => <code key={code}>{code}</code>)}</div><button type="button" onClick={copyRecoveryCodes}>Alle kopieren</button></div>}
            </div>

            {(identity?.role === 'owner' || identity?.role === 'admin') && <div className="security-method api-token-method">
              <div><h3><KeyRound /> API-Tokens</h3><p>Eigene, begrenzte Zugänge für Home Assistant, Handscanner und lokale Dienste – ohne dein Passwort weiterzugeben.</p></div>
              {apiTokens.length > 0 && <div className="api-token-list">{apiTokens.map((token) => (
                <div className="api-token-row" key={token.id}>
                  <span>
                    <strong>{token.name}</strong>
                    <code>vor_pat_{token.token_prefix}_…</code>
                    <small>Gültig bis {new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium' }).format(new Date(token.expires_at))}{token.last_used_at ? ` · zuletzt ${new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium' }).format(new Date(token.last_used_at))}` : ' · noch nie benutzt'}</small>
                    <span className="api-token-scope-chips">{token.scopes.map((scope) => <em key={scope}>{apiTokenScopes.find((item) => item.id === scope)?.label || scope}</em>)}</span>
                  </span>
                  <button type="button" onClick={() => revokeApiToken(token)} disabled={busy || !security.recent_authentication}>Sperren</button>
                </div>
              ))}</div>}
              {!apiTokens.length && <p className="security-note">Noch kein API-Token angelegt.</p>}

              <div className="api-token-builder">
                <label>Vorlage<select value={apiTokenPreset} onChange={(event) => selectApiTokenPreset(event.target.value as 'homeassistant' | 'scanner' | 'custom')}>
                  <option value="homeassistant">Home Assistant · nur lesen</option>
                  <option value="scanner">Handscanner · Scanaktionen</option>
                  <option value="custom">Eigene Auswahl</option>
                </select></label>
                <label>Name<input value={apiTokenName} minLength={2} maxLength={100} onChange={(event) => setApiTokenName(event.target.value)} /></label>
                <label>Gültigkeit<select value={apiTokenExpiresDays} onChange={(event) => setApiTokenExpiresDays(Number(event.target.value))}>
                  <option value={30}>30 Tage</option>
                  <option value={90}>90 Tage</option>
                  <option value={180}>180 Tage</option>
                  <option value={365}>1 Jahr</option>
                </select></label>
                <fieldset><legend>Berechtigungen</legend>{apiTokenScopes.map((scope) => <label className="api-token-scope" key={scope.id}>
                  <input type="checkbox" checked={selectedApiTokenScopes.includes(scope.id)} onChange={() => toggleApiTokenScope(scope.id)} />
                  <span><strong>{scope.label}</strong><small>{scope.description}</small></span>
                </label>)}</fieldset>
                <button type="button" className="button tertiary" onClick={createApiToken} disabled={busy || !security.recent_authentication || apiTokenName.trim().length < 2 || !selectedApiTokenScopes.length}>Token erstellen</button>
              </div>

              {freshApiToken && <div className="fresh-api-token"><strong>Nur jetzt sichtbar – direkt kopieren</strong><p>Lege den Wert als Secret im Zielsystem ab. Vorrio kann ihn später nicht erneut anzeigen.</p><textarea readOnly value={freshApiToken} aria-label="Neuer API-Token" /><button type="button" onClick={copyApiToken}>Token kopieren</button></div>}
            </div>}

            <div className="security-method password-change">
              <div><h3>Passwort ändern</h3><p>Danach werden alle anderen Vorrio-Sitzungen automatisch beendet.</p></div>
              <label>Neues Passwort<input type="password" minLength={10} autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></label>
              <label>Passwort wiederholen<input type="password" minLength={10} autoComplete="new-password" value={repeatPassword} onChange={(event) => setRepeatPassword(event.target.value)} /></label>
              <button type="button" className="button tertiary" onClick={changePassword} disabled={busy || !security.recent_authentication || newPassword.length < 10 || newPassword !== repeatPassword}>Passwort ändern</button>
            </div>
          </div>}

          <div className="session-heading"><MonitorSmartphone /><div><h3>Angemeldete Geräte</h3><p>Jede Sitzung läuft serverseitig und kann sofort widerrufen werden.</p></div></div>
          <div className="session-list">
            {sessions.map((session) => (
              <div className="session-row" key={session.id}>
                <div><strong>{session.device_name}</strong><small>{session.current ? 'Dieses Gerät' : `Zuletzt aktiv ${new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(session.last_seen_at))}`}</small></div>
                <button type="button" onClick={() => revokeSession(session)} disabled={busy} aria-label={`${session.device_name} abmelden`}><LogOut /></button>
              </div>
            ))}
          </div>
          {sessions.some((session) => !session.current) && <button type="button" className="button tertiary revoke-others" onClick={revokeOthers} disabled={busy}>Andere Geräte abmelden</button>}
        </section>

        {notifications && <section className="settings-section notification-section">
          <div className="section-heading"><BellRing /><div><h2>Vorratsmeldungen</h2><p>Einmal melden, wenn etwas knapp wird oder bald abläuft – bis sich der Zustand wieder normalisiert.</p></div></div>
          {!pushAvailable && <p className="notification-hint"><Bell /> Öffne die installierte Vorrio-PWA über die private HTTPS-Adresse. Erst dann darf iPhone, Android oder der Desktop Push-Mitteilungen empfangen.</p>}
          {pushAvailable && !currentPushDeviceId && <div className="push-onboarding">
            <span><strong>Auf diesem Gerät aktivieren</strong><small>Vorrio fragt erst nach deinem Klick nach der Browser-Erlaubnis.</small></span>
            <button type="button" className="button tertiary" onClick={enablePush} disabled={busy}><Bell /> Mitteilungen erlauben</button>
          </div>}
          {currentPushDeviceId && <div className="push-device-current">
            <span className="push-device-status"><Check /> <span><strong>Dieses Gerät ist bereit</strong><small>Push-Verbindung aktiv</small></span></span>
            <span className="push-device-actions"><button type="button" onClick={testPush} disabled={busy}>Test senden</button><button type="button" onClick={disablePushDevice} disabled={busy}>Entfernen</button></span>
          </div>}

          <div className="notification-options">
            <label className="toggle-row"><span><strong>Benachrichtigungen verwenden</strong><small>Der Hauptschalter für dein Vorrio-Konto.</small></span><input type="checkbox" checked={notifications.preferences.push_enabled} disabled={!notifications.subscriptions.length} onChange={(event) => setNotifications({ ...notifications, preferences: { ...notifications.preferences, push_enabled: event.target.checked } })} /></label>
            <label className="toggle-row"><span><strong>Mindestbestand</strong><small>Meldet erst beim Eintritt in „knapp“ und danach nicht erneut, bis aufgefüllt wurde.</small></span><input type="checkbox" checked={notifications.preferences.low_stock_enabled} onChange={(event) => setNotifications({ ...notifications, preferences: { ...notifications.preferences, low_stock_enabled: event.target.checked } })} /></label>
            <label className="toggle-row"><span><strong>Haltbarkeit</strong><small>Lose mit Restbestand im gewählten Zeitfenster.</small></span><input type="checkbox" checked={notifications.preferences.expiry_enabled} onChange={(event) => setNotifications({ ...notifications, preferences: { ...notifications.preferences, expiry_enabled: event.target.checked } })} /></label>
            {notifications.preferences.expiry_enabled && <label className="expiry-days">Wie früh warnen?<select value={notifications.preferences.expiry_days_before} onChange={(event) => setNotifications({ ...notifications, preferences: { ...notifications.preferences, expiry_days_before: Number(event.target.value) } })}><option value={0}>Am Ablauftag</option><option value={3}>3 Tage vorher</option><option value={7}>7 Tage vorher</option><option value={14}>14 Tage vorher</option><option value={30}>30 Tage vorher</option></select></label>}
          </div>
          <div className="notification-summary">
            <span><strong>{notifications.active_low_stock_events}</strong><small>knapp</small></span>
            <span><strong>{notifications.active_expiry_events}</strong><small>ablaufnah</small></span>
            <span><strong>{notifications.subscriptions.length}</strong><small>Geräte</small></span>
          </div>
          <button type="button" className="button tertiary notification-save" onClick={saveNotificationPreferences} disabled={busy}>Meldungen speichern</button>
          <p className="notification-footnote">Auf iPhone und iPad funktioniert Push ab iOS/iPadOS 16.4 in der zum Home-Bildschirm hinzugefügten Vorrio-App.</p>
        </section>}

        {(identity?.role === 'owner' || identity?.role === 'admin') && <section className="settings-section family-section">
          <div className="section-heading"><UserPlus /><div><h2>Familie & Rollen</h2><p>Einmal-Link erstellen, Mitglieder verwalten und Zugänge sofort sperren.</p></div></div>
          {identity.role === 'owner' && !identity.email && <p className="identity-notice"><Mail /> Speichere zuerst deine eigene Login-E-Mail. Sobald mehrere Konten existieren, meldet sich jede Person mit E-Mail und eigenem Passwort an.</p>}
          <div className="member-list">
            {members.map((member) => (
              <div className={`member-row ${member.active ? '' : 'inactive'}`} key={member.id}>
                <div className="member-summary"><span className="member-avatar">{member.display_name.slice(0, 1).toUpperCase()}</span><span><strong>{member.display_name}</strong><small>{member.email || 'Keine Login-E-Mail'} · {member.active_session_count} aktive {member.active_session_count === 1 ? 'Sitzung' : 'Sitzungen'}</small></span></div>
                <div className="member-controls">
                  {member.role === 'owner' ? <span className="role-chip">Owner</span> : <select
                    aria-label={`Rolle von ${member.display_name}`}
                    value={member.role}
                    disabled={busy || !member.active || (identity.role === 'admin' && member.role === 'admin')}
                    onChange={(event) => updateMember(member, event.target.value as HouseholdMember['role'], true)}
                  >
                    {identity.role === 'owner' && <option value="admin">Admin</option>}
                    <option value="member">Mitglied</option>
                    <option value="viewer">Nur ansehen</option>
                  </select>}
                  {member.role !== 'owner' && member.id !== identity.id && <button type="button" onClick={() => updateMember(member, member.role, !member.active)} disabled={busy || (identity.role === 'admin' && member.role === 'admin')}>{member.active ? 'Sperren' : 'Freigeben'}</button>}
                </div>
              </div>
            ))}
          </div>

          <div className="invite-builder">
            <h3>Person einladen</h3>
            <p>Der Link funktioniert einmal und läuft nach 72 Stunden ab.</p>
            <label>Name<input value={inviteName} maxLength={100} onChange={(event) => setInviteName(event.target.value)} /></label>
            <label>E-Mail<input type="email" value={inviteEmail} maxLength={320} autoComplete="off" onChange={(event) => setInviteEmail(event.target.value)} /></label>
            <label>Rolle<select value={inviteRole} onChange={(event) => setInviteRole(event.target.value as Exclude<AuthenticatedUser['role'], 'owner'>)}>
              {identity.role === 'owner' && <option value="admin">Admin</option>}
              <option value="member">Mitglied</option>
              <option value="viewer">Nur ansehen</option>
            </select></label>
            <button type="button" className="button tertiary" onClick={createInvitation} disabled={busy || !identity.email || inviteName.trim().length < 2 || !inviteEmail.trim()}>Einmal-Link erstellen</button>
            {freshInviteLink && <div className="fresh-invite"><strong>Jetzt privat teilen</strong><p>Der vollständige Link wird nur dieses eine Mal angezeigt.</p><input readOnly value={freshInviteLink} aria-label="Neuer Einladungslink" /><button type="button" onClick={copyInviteLink}>Link kopieren</button></div>}
          </div>

          {invitations.length > 0 && <div className="pending-invites"><h3>Offene Einladungen</h3>{invitations.map((invitation) => <div key={invitation.id}><span><strong>{invitation.display_name}</strong><small>{invitation.email} · {roleLabels[invitation.role]}</small></span><button type="button" onClick={() => revokeInvitation(invitation)} disabled={busy}>Zurückziehen</button></div>)}</div>}
        </section>}

        {settings && <section className="settings-section connector-section">
          <div className="section-heading"><Boxes /><div><h2>Grocy-Connector</h2><p>Optionaler Import und einseitiger Export. Vorrio bleibt die Hauptdatenbank.</p></div></div>
          <label className="toggle-row"><span><strong>Grocy verwenden</strong><small>Kann jederzeit deaktiviert werden; Schlüssel und Zuordnungen bleiben erhalten.</small></span><input type="checkbox" checked={settings.grocy.enabled} onChange={(event) => setSettings({ ...settings, grocy: { ...settings.grocy, enabled: event.target.checked } })} /></label>
          <label>Grocy-Adresse<input value={settings.grocy.url} onChange={(event) => setSettings({ ...settings, grocy: { ...settings.grocy, url: event.target.value } })} /></label>
          <label>API-Key<input type="password" value={settings.grocy.api_key || ''} placeholder={settings.grocy.api_key_configured ? 'Gespeicherter Schlüssel bleibt erhalten' : 'GROCY-API-KEY'} onChange={(event) => setSettings({ ...settings, grocy: { ...settings.grocy, api_key: event.target.value || null } })} /></label>
          <div className="settings-actions">
            <button type="button" className="button tertiary" onClick={() => test('grocy')} disabled={busy}>Verbindung prüfen</button>
            <button type="button" className="button tertiary" onClick={migrateGrocyCatalog} disabled={busy || (!settings.grocy.api_key && !settings.grocy.api_key_configured)}>Katalog übernehmen</button>
          </div>
        </section>}

        {settings && <section className="settings-section provider-section">
          <div className="section-heading"><Sparkles /><div><h2>KI-Anbieter</h2><p>Das Bonbild wird nur an den gewählten Anbieter gesendet.</p></div></div>
          <label>Anbieter<select value={settings.provider.type} onChange={(event) => updateProvider(event.target.value as SettingsData['provider']['type'])}>
            <option value="cortecs">Cortecs</option><option value="openai">OpenAI</option><option value="openrouter">OpenRouter</option><option value="ollama">Ollama lokal</option><option value="anthropic">Anthropic</option><option value="openai-compatible">Andere OpenAI-kompatible API</option>
          </select></label>
          <label>Basis-URL<input value={settings.provider.base_url} onChange={(event) => setSettings({ ...settings, provider: { ...settings.provider, base_url: event.target.value } })} /></label>
          {settings.provider.type === 'openai' ? (
            <>
              <label>Vision-Modell<select
                value={openAiModels.some((model) => model.id === settings.provider.model) ? settings.provider.model : 'custom'}
                onChange={(event) => setSettings({ ...settings, provider: { ...settings.provider, model: event.target.value === 'custom' ? '' : event.target.value } })}
              >
                {openAiModels.map((model) => <option key={model.id} value={model.id}>{model.label}</option>)}
                <option value="custom">Eigene Modellkennung</option>
              </select></label>
              {!openAiModels.some((model) => model.id === settings.provider.model) && (
                <label>Eigene Modellkennung<input value={settings.provider.model} placeholder="z. B. gpt-4.1-mini" onChange={(event) => setSettings({ ...settings, provider: { ...settings.provider, model: event.target.value } })} /></label>
              )}
              <p className="model-helper">GPT-5.4 mini ist die ausgewogene Empfehlung für Bons. Das bisherige Modell bleibt gespeichert, bis du bewusst wechselst.</p>
            </>
          ) : (
            <label>Vision-Modell<input value={settings.provider.model} placeholder="Modellkennung des Anbieters" onChange={(event) => setSettings({ ...settings, provider: { ...settings.provider, model: event.target.value } })} /></label>
          )}
          <label>API-Key<input type="password" value={settings.provider.api_key || ''} placeholder={settings.provider.api_key_configured ? 'Gespeicherter Schlüssel bleibt erhalten' : settings.provider.type === 'ollama' ? 'Für Ollama nicht erforderlich' : 'API-Key'} onChange={(event) => setSettings({ ...settings, provider: { ...settings.provider, api_key: event.target.value || null } })} /></label>
          <button type="button" className="button tertiary" onClick={() => test('provider')} disabled={busy}>Anbieter prüfen</button>
        </section>}

        {settings && <section className="settings-section privacy-section">
          <div className="section-heading"><CheckCircle2 /><div><h2>Datenschutz</h2><p>Du entscheidest, wie lange Bonbilder bleiben.</p></div></div>
          <label className="toggle-row"><span><strong>Nach Analyse löschen</strong><small>Erkannte Daten und Zuordnungen bleiben erhalten.</small></span><input type="checkbox" checked={settings.privacy.delete_image_after_analysis} onChange={(event) => setSettings({ ...settings, privacy: { ...settings.privacy, delete_image_after_analysis: event.target.checked } })} /></label>
          {!settings.privacy.delete_image_after_analysis && <label>Aufbewahrung in Tagen<input type="number" min="0" max="365" value={settings.privacy.retention_days} onChange={(event) => setSettings({ ...settings, privacy: { ...settings.privacy, retention_days: Number(event.target.value) } })} /></label>}
        </section>}

        {identity?.role === 'owner' && security && <LaunchReadinessPanel recentAuthentication={security.recent_authentication} />}

        {settings && <button className="button primary full" disabled={busy}>{busy ? <LoaderCircle className="spin" /> : <Check />} Einstellungen speichern</button>}
        <button type="button" className="logout-button" onClick={onLogout}><LogOut /> Abmelden</button>
      </form>
    </div>
  )
}

const navigationItems: { id: Exclude<Screen, 'review'>; label: string; icon: typeof Home }[] = [
  { id: 'home', label: 'Start', icon: Home },
  { id: 'scan', label: 'Scannen', icon: Barcode },
  { id: 'catalog', label: 'Vorrat', icon: Boxes },
  { id: 'history', label: 'Einkäufe', icon: History },
  { id: 'settings', label: 'Einstellungen', icon: Settings },
]

function visibleNavigation(role: AuthenticatedUser['role']) {
  return role === 'viewer' ? navigationItems.filter((item) => item.id !== 'scan') : navigationItems
}

function DesktopNav({ selected, onSelect, status, role }: { selected: Screen; onSelect: (screen: Screen) => void; status: AppStatus | null; role: AuthenticatedUser['role'] }) {
  return (
    <aside className="desktop-nav">
      <button className="desktop-brand" onClick={() => onSelect('home')}><ReceiptText /><strong>Vorrio</strong></button>
      <nav aria-label="Hauptnavigation">
        {visibleNavigation(role).map(({ id, label, icon: Icon }) => (
          <button key={id} className={selected === id ? 'selected' : ''} onClick={() => onSelect(id)}><Icon /><span>{label}</span></button>
        ))}
      </nav>
      <div className="desktop-local-state"><span /><strong>Local-first</strong><small>{status ? `${status.catalog.products} ${status.catalog.products === 1 ? 'Produkt' : 'Produkte'} · v${status.version}` : 'Verbindung wird geprüft'}</small></div>
    </aside>
  )
}

function BottomNav({ selected, onSelect, role }: { selected: Screen; onSelect: (screen: Screen) => void; role: AuthenticatedUser['role'] }) {
  return <nav className="bottom-nav" aria-label="Hauptnavigation">{visibleNavigation(role).map(({ id, label, icon: Icon }) => <button key={id} className={`${selected === id ? 'selected' : ''} ${id === 'scan' ? 'scan-nav-item' : ''}`} onClick={() => onSelect(id)}><Icon /><span>{label}</span></button>)}</nav>
}

function OnboardingGuide({
  readOnly,
  busy,
  onComplete,
  onDismiss,
}: {
  readOnly: boolean
  busy: boolean
  onComplete: (destination: Screen) => void
  onDismiss: () => void
}) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDismiss()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [onDismiss])

  return <div className="experience-backdrop" role="presentation">
    <section className="experience-dialog onboarding-dialog" role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
      <header className="experience-header">
        <span className="experience-brand"><ReceiptText /><strong>Vorrio</strong></span>
        <span className="experience-step">Schritt {step + 1} von 3</span>
        <button type="button" className="icon-button" onClick={onDismiss} aria-label="Einführung später fortsetzen"><X /></button>
      </header>
      <div className="experience-progress" aria-label={`Schritt ${step + 1} von 3`}><span style={{ width: `${((step + 1) / 3) * 100}%` }} /></div>

      <div className="experience-content">
        {step === 0 && <>
          <span className="experience-hero-icon"><Sparkles /></span>
          <p className="experience-eyebrow">Willkommen</p>
          <h1 id="onboarding-title">Dein Einkauf wird zum verlässlichen Vorrat.</h1>
          <p className="experience-lead">Vorrio verbindet Bons, einzelne Produktscans und deinen aktuellen Bestand. Du prüfst jeden Vorschlag, bevor sich etwas ändert.</p>
          <div className="journey-strip" aria-label="Vorrio Ablauf">
            <span><ReceiptText /><strong>Einkauf</strong></span><ChevronRight />
            <span><CheckCircle2 /><strong>Prüfen</strong></span><ChevronRight />
            <span><Boxes /><strong>Vorrat</strong></span>
          </div>
        </>}

        {step === 1 && <>
          <p className="experience-eyebrow">Zwei einfache Wege</p>
          <h1 id="onboarding-title">Nimm immer den kürzesten Weg.</h1>
          <div className="experience-choice-grid">
            <article><span><ReceiptText /></span><div><strong>Ganzer Einkauf</strong><p>Bon fotografieren oder PDF hochladen. Vorrio erkennt Artikel und Preise und lässt dich alles prüfen.</p></div></article>
            {!readOnly && <article><span><Barcode /></span><div><strong>Ein Produkt</strong><p>Barcode scannen, um gezielt einzulagern, zu verbrauchen, zu öffnen oder auf die Einkaufsliste zu setzen.</p></div></article>}
            <article><span><Boxes /></span><div><strong>Nachsehen</strong><p>Unter „Vorrat“ findest du Mengen und Produktwissen, unter „Einkäufe“ Listen, Bons, Preise und Budget.</p></div></article>
          </div>
        </>}

        {step === 2 && <>
          <span className="experience-hero-icon safe"><ShieldCheck /></span>
          <p className="experience-eyebrow">Du behältst die Kontrolle</p>
          <h1 id="onboarding-title">Vorschlag zuerst. Änderung erst nach Bestätigung.</h1>
          <ul className="experience-checklist">
            <li><Check /> KI- und Datenbanktreffer werden sichtbar erklärt.</li>
            <li><Check /> Unklare Produkte bleiben zur Prüfung offen.</li>
            <li><Check /> Deine Daten bleiben in deiner eigenen Vorrio-Installation.</li>
          </ul>
          <div className="experience-start-actions">
            {readOnly ? <button type="button" className="button primary full" disabled={busy} onClick={() => onComplete('catalog')}><Boxes /> Vorrat ansehen</button> : <>
              <button type="button" className="button primary full" disabled={busy} onClick={() => onComplete('home')}><Camera /> Ersten Bon erfassen</button>
              <button type="button" className="button secondary full" disabled={busy} onClick={() => onComplete('scan')}><Barcode /> Produkt scannen</button>
            </>}
          </div>
        </>}
      </div>

      {step < 2 && <footer className="experience-footer">
        {step > 0 ? <button type="button" className="text-button" onClick={() => setStep((current) => current - 1)}>Zurück</button> : <button type="button" className="text-button" onClick={onDismiss}>Später</button>}
        <button type="button" className="button primary" onClick={() => setStep((current) => current + 1)}>Weiter <ChevronRight /></button>
      </footer>}
    </section>
  </div>
}

function ReleaseNotesDialog({
  experience,
  busy,
  onAcknowledge,
  onDismiss,
}: {
  experience: ExperienceState
  busy: boolean
  onAcknowledge: () => void
  onDismiss: () => void
}) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDismiss()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [onDismiss])

  return <div className="experience-backdrop" role="presentation">
    <section className="experience-dialog release-dialog" role="dialog" aria-modal="true" aria-labelledby="release-title">
      <header className="experience-header">
        <span className="release-badge"><Sparkles /> Aktualisiert</span>
        <button type="button" className="icon-button" onClick={onDismiss} aria-label="Versionshinweise später lesen"><X /></button>
      </header>
      <div className="experience-content">
        <p className="experience-eyebrow">Neu in Vorrio {experience.release.version}</p>
        <h1 id="release-title">{experience.release.title}</h1>
        <p className="experience-lead">{experience.release.summary}</p>
        <ul className="release-highlights">
          {experience.release.highlights.map((highlight) => <li key={highlight}><CheckCircle2 /><span>{highlight}</span></li>)}
        </ul>
      </div>
      <footer className="release-footer">
        <button type="button" className="text-button" onClick={onDismiss}>Später lesen</button>
        <button type="button" className="button primary" disabled={busy} onClick={onAcknowledge}>{busy ? <LoaderCircle className="spin" /> : <Check />} Verstanden</button>
      </footer>
    </section>
  </div>
}

function BusyOverlay() {
  return <div className="busy-overlay"><div><LoaderCircle className="spin" /><strong>Bon wird gelesen</strong><span>Artikel und Preise werden vorbereitet.</span></div></div>
}

function Toast({ kind, text, onClose }: { kind: 'success' | 'error'; text: string; onClose: () => void }) {
  return <div className={`toast ${kind}`} role={kind === 'error' ? 'alert' : 'status'}>{kind === 'success' ? <CheckCircle2 /> : <AlertCircle />}<span>{text}</span><button onClick={onClose} aria-label="Meldung schließen"><X /></button></div>
}

export default App
