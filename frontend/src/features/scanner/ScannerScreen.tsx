import {
  AlertCircle,
  Barcode,
  Camera,
  Check,
  CheckCircle2,
  CircleMinus,
  CloudUpload,
  Keyboard,
  ListPlus,
  LoaderCircle,
  PackageOpen,
  PackagePlus,
  RefreshCw,
  Search,
  ShoppingCart,
  Trash2,
  WifiOff,
  X,
} from 'lucide-react'
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, ApiError, ApiNetworkError } from '../../api'
import type {
  CatalogProduct,
  GrocyMasterData,
  ScanConfirmInput,
  ScanDraft,
  ScanMode,
} from '../../types'
import {
  markOfflineScanFailed,
  queueOfflineScan,
  readOfflineScans,
  removeOfflineScan,
  type OfflineScanEntry,
  type OfflineScanStorage,
} from './offlineQueue'
import { currentLocale, formatDate, formatNumber, translate } from '../../i18n'

const modes: { id: ScanMode; label: string; icon: typeof Barcode; action: string; description: string }[] = [
  { id: 'identify', label: 'Erkennen', icon: Barcode, action: 'Produkt bestätigen', description: 'ordnet das Produkt zu, ohne den Bestand zu ändern' },
  { id: 'add', label: 'Einlagern', icon: PackagePlus, action: 'In den Vorrat', description: 'erhöht den Bestand um die gewählte Menge' },
  { id: 'consume', label: 'Verbrauchen', icon: CircleMinus, action: 'Verbrauch buchen', description: 'zieht die gewählte Menge vom Bestand ab' },
  { id: 'open', label: 'Öffnen', icon: PackageOpen, action: 'Als geöffnet markieren', description: 'markiert die älteste passende Packung als geöffnet' },
  { id: 'shopping', label: 'Einkaufsliste', icon: ListPlus, action: 'Zur Einkaufsliste', description: 'setzt oder erhöht den offenen Einkaufslisten-Eintrag' },
]

const mutationId = (prefix: string) =>
  `${prefix}_${globalThis.crypto?.randomUUID?.() || `${Date.now()}_${Math.random().toString(16).slice(2)}`}`

const sourceLabel = (scan: ScanDraft) => {
  if (scan.resolution_source === 'local') return translate('Eigener Vorrio-Katalog')
  if (scan.resolution_source === 'cache') return translate('Open-Facts-Cache')
  if (scan.resolution_source === 'open_facts') return scan.suggestion?.source || 'Open Facts'
  return translate('Noch nicht erkannt')
}

const productTitle = (scan: ScanDraft) =>
  scan.product_name || scan.suggestion?.name || translate('Unbekanntes Produkt')

const formatQuantity = (value: number) => formatNumber(value)

const localQueueStorage = (): OfflineScanStorage | null => {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

function playFeedback(success: boolean) {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext
    if (!AudioContextClass) return
    const context = new AudioContextClass()
    const oscillator = context.createOscillator()
    const gain = context.createGain()
    oscillator.frequency.value = success ? 720 : 260
    gain.gain.setValueAtTime(0.045, context.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.12)
    oscillator.connect(gain).connect(context.destination)
    oscillator.start()
    oscillator.stop(context.currentTime + 0.12)
    oscillator.addEventListener('ended', () => void context.close())
  } catch {
    // Audio feedback is optional and must never block a scan.
  }
}

declare global {
  interface Window {
    webkitAudioContext?: typeof AudioContext
  }
}

interface ScannerScreenProps {
  onNotice: (kind: 'success' | 'error', text: string) => void
}

export function ScannerScreen({ onNotice }: ScannerScreenProps) {
  const [mode, setMode] = useState<ScanMode>('identify')
  const [barcode, setBarcode] = useState('')
  const [scan, setScan] = useState<ScanDraft | null>(null)
  const [unresolved, setUnresolved] = useState<ScanDraft[]>([])
  const [masterData, setMasterData] = useState<GrocyMasterData | null>(null)
  const [products, setProducts] = useState<CatalogProduct[]>([])
  const [productQuery, setProductQuery] = useState('')
  const [selectedProductId, setSelectedProductId] = useState('')
  const [name, setName] = useState('')
  const [brand, setBrand] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [locationId, setLocationId] = useState<number | null>(null)
  const [quantityUnitId, setQuantityUnitId] = useState<number | null>(null)
  const [productGroupId, setProductGroupId] = useState<number | null>(null)
  const [bestBeforeDate, setBestBeforeDate] = useState('')
  const [unitPrice, setUnitPrice] = useState('')
  const [busy, setBusy] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [online, setOnline] = useState(() => navigator.onLine)
  const [offlineScans, setOfflineScans] = useState<OfflineScanEntry[]>(() => {
    const storage = localQueueStorage()
    return storage ? readOfflineScans(storage) : []
  })
  const [error, setError] = useState('')
  const [cameraState, setCameraState] = useState<'idle' | 'starting' | 'active'>('idle')
  const videoRef = useRef<HTMLVideoElement>(null)
  const scannerControlsRef = useRef<{ stop: () => void } | null>(null)
  const manualInputRef = useRef<HTMLInputElement>(null)
  const resultRef = useRef<HTMLElement>(null)

  const refreshReviewData = useCallback(async () => {
    const [nextUnresolved, nextMasterData, nextProducts] = await Promise.all([
      api.unresolvedScans(),
      api.catalogMasterData(),
      api.catalogProducts(),
    ])
    setUnresolved(nextUnresolved)
    setMasterData(nextMasterData)
    setProducts(nextProducts)
  }, [])

  useEffect(() => {
    refreshReviewData().catch((nextError) => setError((nextError as Error).message))
  }, [refreshReviewData])

  const stopCamera = useCallback(() => {
    scannerControlsRef.current?.stop()
    scannerControlsRef.current = null
    const stream = videoRef.current?.srcObject
    if (stream instanceof MediaStream) stream.getTracks().forEach((track) => track.stop())
    if (videoRef.current) videoRef.current.srcObject = null
    setCameraState('idle')
  }, [])

  useEffect(() => stopCamera, [stopCamera])

  useEffect(() => {
    if (!scan || !window.matchMedia('(max-width: 959px)').matches) return undefined
    const frame = window.requestAnimationFrame(() => {
      resultRef.current?.scrollIntoView({
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
        block: 'start',
      })
    })
    return () => window.cancelAnimationFrame(frame)
  }, [scan?.id, scan?.status])

  const loadScan = useCallback((nextScan: ScanDraft) => {
    setScan(nextScan)
    setMode(nextScan.mode)
    setBarcode(nextScan.barcode_normalized)
    setSelectedProductId(nextScan.product_id || '')
    setName(nextScan.product_name || nextScan.suggestion?.name || '')
    setBrand(nextScan.brand || nextScan.suggestion?.brand || '')
    setLocationId(nextScan.default_location_id)
    setQuantityUnitId(nextScan.default_quantity_unit_id)
    setProductGroupId(null)
    setQuantity(1)
    setBestBeforeDate('')
    setUnitPrice('')
  }, [])

  const enqueueOffline = useCallback((value: string, queuedMode: ScanMode, clientMutationId: string) => {
    const storage = localQueueStorage()
    if (!storage) {
      setError(translate('Der lokale Gerätespeicher ist nicht verfügbar. Der Code konnte nicht vorgemerkt werden.'))
      playFeedback(false)
      return false
    }
    const result = queueOfflineScan(storage, {
      id: mutationId('offline'),
      barcode: value,
      mode: queuedMode,
      clientMutationId,
      createdAt: new Date().toISOString(),
    })
    setOfflineScans(result.entries)
    if (result.status === 'full') {
      setError(translate('Die Offline-Warteschlange ist voll. Bitte zuerst vorhandene Scans synchronisieren oder entfernen.'))
      playFeedback(false)
      return false
    }
    setBarcode('')
    setError('')
    playFeedback(true)
    onNotice('success', result.status === 'added'
      ? translate('Scan lokal vorgemerkt. Nach der Verbindung wird er zur Prüfung synchronisiert.')
      : translate('Dieser Code wartet mit derselben Aktion bereits auf die Synchronisierung.'))
    return true
  }, [onNotice])

  const syncOfflineScans = useCallback(async () => {
    const storage = localQueueStorage()
    if (!storage || syncing || !navigator.onLine) return
    const pending = readOfflineScans(storage)
    if (!pending.length) {
      setOfflineScans([])
      return
    }
    setSyncing(true)
    setError('')
    let synced = 0
    let lastResolved: ScanDraft | null = null
    try {
      for (const entry of pending) {
        try {
          const resolved = await api.resolveScan(entry.barcode, entry.mode, entry.clientMutationId)
          lastResolved = resolved
          synced += 1
          setOfflineScans(removeOfflineScan(storage, entry.id))
        } catch (nextError) {
          const message = (nextError as Error).message
          setOfflineScans(markOfflineScanFailed(storage, entry.id, message))
          if (nextError instanceof ApiNetworkError) {
            setOnline(navigator.onLine)
            setError(translate('Die Verbindung ist wieder unterbrochen. Offene Scans bleiben lokal gespeichert.'))
            break
          }
          if (nextError instanceof ApiError && nextError.status === 401) {
            setError(translate('Bitte Vorrio nach der Wiederverbindung neu anmelden. Die Scans bleiben lokal gespeichert.'))
            break
          }
        }
      }
      if (lastResolved) loadScan(lastResolved)
      if (synced) {
        onNotice('success', translate('{{count}} Scans wurden synchronisiert und warten auf Bestätigung.', { count: synced }))
        try {
          await refreshReviewData()
        } catch (nextError) {
          setError((nextError as Error).message)
        }
      }
    } finally {
      setSyncing(false)
    }
  }, [loadScan, onNotice, refreshReviewData, syncing])

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true)
      void syncOfflineScans()
    }
    const handleOffline = () => setOnline(false)
    const handleStorage = () => {
      const storage = localQueueStorage()
      if (storage) setOfflineScans(readOfflineScans(storage))
    }
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    window.addEventListener('storage', handleStorage)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('storage', handleStorage)
    }
  }, [syncOfflineScans])

  const resolveCode = useCallback(async (rawCode: string) => {
    const value = rawCode.trim()
    if (!value || busy) return
    const normalized = value.replace(/[\s-]+/g, '')
    if (!/^\d{4,18}$/.test(normalized)) {
      setError(translate('Der Code muss aus 4 bis 18 Ziffern bestehen.'))
      playFeedback(false)
      return
    }
    const clientMutationId = mutationId('resolve')
    setBusy(true)
    setError('')
    stopCamera()
    if (!navigator.onLine) {
      enqueueOffline(value, mode, clientMutationId)
      setBusy(false)
      return
    }
    try {
      const resolved = await api.resolveScan(value, mode, clientMutationId)
      loadScan(resolved)
      playFeedback(Boolean(resolved.product_id || resolved.suggestion?.name))
      await refreshReviewData()
    } catch (nextError) {
      if (nextError instanceof ApiNetworkError) {
        setOnline(navigator.onLine)
        enqueueOffline(value, mode, clientMutationId)
        return
      }
      const message = (nextError as Error).message
      setError(message)
      playFeedback(false)
    } finally {
      setBusy(false)
    }
  }, [busy, enqueueOffline, loadScan, mode, refreshReviewData, stopCamera])

  const startCamera = async () => {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError(translate('Die Kamera braucht HTTPS. Manuelle Eingabe und Handscanner funktionieren auch über die lokale HTTP-Adresse.'))
      manualInputRef.current?.focus()
      return
    }
    setError('')
    setCameraState('starting')
    try {
      const { BrowserMultiFormatReader } = await import('@zxing/browser')
      const reader = new BrowserMultiFormatReader(undefined, {
        delayBetweenScanAttempts: 100,
        delayBetweenScanSuccess: 800,
      })
      const controls = await reader.decodeFromConstraints(
        {
          audio: false,
          video: {
            facingMode: { ideal: 'environment' },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
        },
        videoRef.current || undefined,
        (result, _error, activeControls) => {
          if (!result) return
          activeControls.stop()
          void resolveCode(result.getText())
        },
      )
      scannerControlsRef.current = controls
      setCameraState('active')
    } catch (nextError) {
      stopCamera()
      const message = nextError instanceof Error ? nextError.message : translate('Kamera konnte nicht gestartet werden')
      setError(translate('Kamera nicht verfügbar: {{message}}', { message }))
    }
  }

  const submitManual = (event: FormEvent) => {
    event.preventDefault()
    void resolveCode(barcode)
  }

  const reset = () => {
    stopCamera()
    setScan(null)
    setBarcode('')
    setSelectedProductId('')
    setName('')
    setBrand('')
    setError('')
    window.setTimeout(() => manualInputRef.current?.focus(), 0)
  }

  const confirm = async (event: FormEvent) => {
    event.preventDefault()
    if (!scan) return
    setBusy(true)
    setError('')
    const input: ScanConfirmInput = {
      client_mutation_id: mutationId('confirm'),
      product_id: selectedProductId || scan.product_id || null,
      name: selectedProductId || scan.product_id ? null : name,
      brand: brand || null,
      image_url: scan.suggestion?.image_url || null,
      location_id: locationId,
      quantity_unit_id: quantityUnitId,
      product_group_id: productGroupId,
      quantity,
      best_before_date: bestBeforeDate || null,
      unit_price: unitPrice ? Number(unitPrice.replace(',', '.')) : null,
    }
    try {
      const confirmed = await api.confirmScan(scan.id, input)
      loadScan(confirmed)
      playFeedback(true)
      onNotice('success', translate('{{product}}: {{action}} erledigt.', {
        product: productTitle(confirmed),
        action: translate(modes.find((item) => item.id === confirmed.mode)?.action || 'Aktion'),
      }))
      await refreshReviewData()
    } catch (nextError) {
      const message = (nextError as Error).message
      setError(message)
      playFeedback(false)
    } finally {
      setBusy(false)
    }
  }

  const discard = async (draft: ScanDraft) => {
    try {
      await api.discardScan(draft.id)
      if (scan?.id === draft.id) reset()
      await refreshReviewData()
    } catch (nextError) {
      setError((nextError as Error).message)
    }
  }

  const discardOffline = (id: string) => {
    const storage = localQueueStorage()
    if (storage) setOfflineScans(removeOfflineScan(storage, id))
  }

  const filteredProducts = useMemo(() => {
    const needle = productQuery.trim().toLocaleLowerCase(currentLocale())
    if (!needle) return products.slice(0, 12)
    return products.filter((product) => product.name.toLocaleLowerCase(currentLocale()).includes(needle)).slice(0, 12)
  }, [productQuery, products])

  const activeMode = modes.find((item) => item.id === mode) || modes[0]
  const ActiveModeIcon = activeMode.icon
  const requiresProductChoice = Boolean(scan && !scan.product_id)
  const canConfirm = Boolean(
    scan &&
    scan.status !== 'confirmed' &&
    (scan.product_id || selectedProductId || name.trim()),
  )

  return (
    <div className={`screen scanner-screen${scan ? ' has-scan' : ''}`}>
      <header className="page-header scanner-header">
        <div>
          <h1>{translate("Produkt scannen")}</h1>
          <p>{translate("Kamera, Handscanner oder Code – Vorrio ändert erst nach deiner Bestätigung etwas.")}</p>
        </div>
        {scan ? <button className="button tertiary scanner-reset" onClick={reset}><RefreshCw /> {translate("Neu scannen")}</button> : null}
      </header>

      <div className="scan-mode-bar" role="tablist" aria-label={translate("Scan-Aktion")}>
        {modes.map(({ id, label, icon: Icon, description }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={mode === id}
            aria-label={translate('{{label}}: {{description}}', { label: translate(label), description: translate(description) })}
            className={mode === id ? 'selected' : ''}
            onClick={() => {
              setMode(id)
              if (scan && scan.status !== 'confirmed') {
                api.updateScan(scan.id, { mode: id }).then(loadScan).catch((nextError) => setError(nextError.message))
              }
            }}
          >
            <Icon />
            <span>{translate(label)}</span>
          </button>
        ))}
      </div>
      <p className="scan-mode-help" aria-live="polite">
        <ActiveModeIcon />
        <span><strong>{translate(activeMode.label)}</strong> {translate(activeMode.description)}.</span>
      </p>

      {!online || offlineScans.length ? (
        <section className={`offline-scan-panel${online ? '' : ' is-offline'}`} aria-label={translate("Offline-Scans")}>
          <header>
            <span className="offline-scan-icon">{online ? <CloudUpload /> : <WifiOff />}</span>
            <span>
              <strong>{online ? translate('{{count}} Scans warten', { count: offlineScans.length }) : translate('Offline scannen')}</strong>
              <small>{translate(online
                ? 'Codes werden zur Prüfung synchronisiert – noch ohne Bestandsänderung.'
                : 'Codes bleiben nur auf diesem Gerät und werden später zur Prüfung übertragen.')}</small>
            </span>
            {offlineScans.length ? (
              <button className="button tertiary compact" type="button" disabled={!online || syncing} onClick={() => void syncOfflineScans()}>
                {syncing ? <LoaderCircle className="spin" /> : <CloudUpload />}
                {translate(syncing ? 'Abgleich läuft' : 'Jetzt abgleichen')}
              </button>
            ) : null}
          </header>
          {offlineScans.length ? (
            <div className="offline-scan-list">
              {offlineScans.map((entry) => (
                <div className="offline-scan-row" key={entry.id}>
                  <Barcode />
                  <span>
                    <strong>{entry.barcode}</strong>
                    <small>
                      {translate(modes.find((item) => item.id === entry.mode)?.label || entry.mode)}
                      {' · '}
                      {formatDate(entry.createdAt, { hour: '2-digit', minute: '2-digit' })}
                    </small>
                    {entry.lastError ? <em>{entry.lastError}</em> : null}
                  </span>
                  <button type="button" className="discard-scan" onClick={() => discardOffline(entry.id)} aria-label={translate('{{barcode}} aus Offline-Warteschlange entfernen', { barcode: entry.barcode })}>
                    <Trash2 />
                  </button>
                </div>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {error ? <p className="scanner-error scanner-page-error" role="alert"><AlertCircle /> {error}</p> : null}

      <div className={`scanner-workspace${scan ? ' has-scan' : ''}`}>
        {!scan ? <section className="scanner-capture" aria-label={translate("Barcode erfassen")}>
          <div className={`camera-preview ${cameraState}`}>
            <video ref={videoRef} muted playsInline aria-label={translate("Kameravorschau")} />
            <i className="camera-frame top-left" />
            <i className="camera-frame top-right" />
            <i className="camera-frame bottom-left" />
            <i className="camera-frame bottom-right" />
            {cameraState !== 'active' ? (
              <div className="camera-empty">
                {cameraState === 'starting' ? <LoaderCircle className="spin" /> : <Camera />}
                <strong>{translate(cameraState === 'starting' ? 'Kamera wird vorbereitet' : 'Barcode mit der Kamera erfassen')}</strong>
                <span>{translate("Das Bild bleibt auf diesem Gerät.")}</span>
                <button className="button primary" onClick={startCamera} disabled={cameraState === 'starting'}>
                  <Camera /> {translate("Kamera starten")}
                </button>
              </div>
            ) : (
              <button className="camera-stop" onClick={stopCamera}><X /> {translate("Kamera schließen")}</button>
            )}
          </div>

          <div className="scanner-divider"><span>{translate("oder")}</span></div>
          <form className="barcode-form" onSubmit={submitManual}>
            <label htmlFor="barcode-input">{translate("Barcode manuell eingeben")}</label>
            <div>
              <span><Barcode /></span>
              <input
                id="barcode-input"
                ref={manualInputRef}
                inputMode="numeric"
                minLength={4}
                maxLength={100}
                autoComplete="off"
                enterKeyHint="go"
                value={barcode}
                onChange={(event) => setBarcode(event.target.value)}
                placeholder={translate("z. B. 4000000000016")}
                disabled={busy}
              />
              <button className="button primary" disabled={busy || !barcode.trim()}>
                {busy ? <LoaderCircle className="spin" /> : <Search />} {translate("Code prüfen")}
              </button>
            </div>
          </form>
          <p className="keyboard-hint"><Keyboard /> {translate("Handscanner funktionieren hier wie eine Tastatur: scannen und Enter.")}</p>
        </section> : null}

        <aside ref={resultRef} className="scanner-result" aria-live="polite">
          {!scan ? (
            <div className="scanner-empty-result">
              <Barcode />
              <h2>{translate("Bereit zum Scannen")}</h2>
              <p>{translate("Wähle die Aktion, erfasse den Code und prüfe das Ergebnis.")}</p>
            </div>
          ) : scan.status === 'confirmed' ? (
            <div className="scanner-confirmed">
              <CheckCircle2 />
              <h2>{translate("Erledigt")}</h2>
              <strong>{productTitle(scan)}</strong>
              <p>{translate('{{action}} wurde genau einmal gespeichert.', { action: translate(activeMode.action) })}</p>
              <button className="button primary" onClick={reset}><RefreshCw /> {translate("Nächstes Produkt")}</button>
            </div>
          ) : (
            <form className="scan-review-form" onSubmit={confirm}>
              <div className={`resolution-state ${scan.product_id || scan.suggestion?.name ? 'found' : 'unknown'}`}>
                {scan.product_id || scan.suggestion?.name ? <CheckCircle2 /> : <AlertCircle />}
                <span>
                  <strong>{translate(scan.product_id || scan.suggestion?.name ? 'Produkt gefunden' : 'Unbekannter Code')}</strong>
                  <small>{sourceLabel(scan)}</small>
                </span>
              </div>

              <div className="scan-product-summary">
                {scan.product_image_url || scan.suggestion?.image_url ? (
                  <img
                    src={scan.product_image_url || scan.suggestion?.image_url || ''}
                    alt=""
                    loading="lazy"
                    referrerPolicy="no-referrer"
                  />
                ) : <span className="product-placeholder"><ShoppingCart /></span>}
                <div>
                  <h2>{productTitle(scan)}</h2>
                  <p>{scan.brand || scan.suggestion?.brand || translate('Marke nicht bekannt')}</p>
                  <code>{scan.barcode_normalized}</code>
                  <small>{scan.symbology}</small>
                </div>
              </div>

              {scan.product_id ? (
                <div className="local-match-row">
                  <span><Check /> {translate("Lokal zugeordnet")}</span>
                  <strong>{scan.product_name}</strong>
                  <small>{formatQuantity(scan.stock_quantity)} {scan.default_quantity_unit_name || translate('Einheiten')} {translate("im Bestand")}</small>
                </div>
              ) : (
                <fieldset className="product-assignment">
                  <legend>{translate("Produkt zuordnen")}</legend>
                  <label>
                    {translate("Vorhandenes Produkt (optional)")}
                    <span className="assignment-search"><Search /><input value={productQuery} onChange={(event) => setProductQuery(event.target.value)} placeholder={translate("Katalog durchsuchen")} /></span>
                  </label>
                  {productQuery ? (
                    <div className="assignment-results">
                      {filteredProducts.map((product) => (
                        <button
                          type="button"
                          key={product.id}
                          className={selectedProductId === product.id ? 'selected' : ''}
                          onClick={() => {
                            setSelectedProductId(product.id)
                            setName(product.name)
                          }}
                        >
                          <span>{product.name}</span><small>{product.default_location_name || translate('Kein Lagerort')}</small>
                        </button>
                      ))}
                    </div>
                  ) : null}
                  <div className="or-separator"><span>{translate("oder neu anlegen")}</span></div>
                  <label>{translate("Produktname")}<input value={name} onChange={(event) => { setName(event.target.value); setSelectedProductId('') }} placeholder={translate("z. B. Filterkaffee")} required={!selectedProductId} /></label>
                  <label>{translate("Marke (optional)")}<input value={brand} onChange={(event) => setBrand(event.target.value)} placeholder={translate("z. B. Lavazza")} /></label>
                </fieldset>
              )}

              <div className="scan-action-fields">
                {mode !== 'identify' && mode !== 'open' ? (
                  <label>{translate("Menge")}<input type="number" min="0.001" step="0.001" value={quantity} onChange={(event) => setQuantity(Number(event.target.value))} /></label>
                ) : null}
                {mode === 'add' ? (
                  <>
                    <label>{translate("Lagerort")}<select value={locationId || ''} onChange={(event) => setLocationId(event.target.value ? Number(event.target.value) : null)}>
                      <option value="">{translate("Produktstandard")}</option>
                      {masterData?.locations.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
                    </select></label>
                    <label>{translate("Einheit")}<select value={quantityUnitId || ''} onChange={(event) => setQuantityUnitId(event.target.value ? Number(event.target.value) : null)}>
                      <option value="">{translate("Produktstandard")}</option>
                      {masterData?.quantity_units.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
                    </select></label>
                    {requiresProductChoice ? <label>{translate("Produktgruppe")}<select value={productGroupId || ''} onChange={(event) => setProductGroupId(event.target.value ? Number(event.target.value) : null)}>
                      <option value="">{translate("Noch offen")}</option>
                      {masterData?.product_groups.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
                    </select></label> : null}
                    <label>{translate("Mindestens haltbar bis")}<input type="date" value={bestBeforeDate} onChange={(event) => setBestBeforeDate(event.target.value)} /></label>
                    <label>{translate("Preis pro Einheit")}<input inputMode="decimal" value={unitPrice} onChange={(event) => setUnitPrice(event.target.value)} placeholder={translate("optional")} /></label>
                  </>
                ) : null}
              </div>

              {scan.upstream_error ? <p className="upstream-note">{translate("Externe Suche war nicht erreichbar. Du kannst trotzdem lokal zuordnen.")}</p> : null}
              <button className="button primary full scan-confirm" disabled={busy || !canConfirm}>
                {busy ? <LoaderCircle className="spin" /> : <ActiveModeIcon />} {translate(activeMode.action)}
              </button>
            </form>
          )}

          <section className="unresolved-inbox">
            <header>
              <div><AlertCircle /><h2>{translate("Unbekannte Codes")}</h2></div>
              <span>{unresolved.length}</span>
            </header>
            {unresolved.length ? unresolved.slice(0, 5).map((draft) => (
              <div className="unresolved-row" key={draft.id}>
                <button type="button" onClick={() => loadScan(draft)}>
                  <Barcode /><span><strong>{draft.suggestion?.name || draft.barcode_normalized}</strong><small>{draft.suggestion?.name ? draft.barcode_normalized : translate('Noch nicht zugeordnet')}</small></span>
                </button>
                <button className="discard-scan" type="button" onClick={() => void discard(draft)} aria-label={translate('{{barcode}} verwerfen', { barcode: draft.barcode_normalized })}><Trash2 /></button>
              </div>
            )) : <p>{translate("Keine offenen Codes.")}</p>}
          </section>
        </aside>
      </div>
    </div>
  )
}
