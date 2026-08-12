import { Activity, Database, Download, HardDrive, LoaderCircle, ShieldAlert, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../../api'
import type { ExportPreview, OperationsOverview } from '../../types'

const ERASE_CONFIRMATION = 'HAUSHALT ENDGÜLTIG LÖSCHEN'

const bytes = (value: number) => {
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

const actionLabel = (action: string) => action
  .replace(/^GET /, 'Gelesen: ')
  .replace(/^POST /, 'Ausgeführt: ')
  .replace(/^PUT /, 'Aktualisiert: ')
  .replace(/^PATCH /, 'Geändert: ')
  .replace(/^DELETE /, 'Gelöscht: ')
  .replace('portable_export', 'Datenexport erstellt')
  .replace('manual_retention', 'Aufbewahrung angewendet')
  .replace('scheduled_retention', 'Automatische Aufbewahrung')

export function LaunchReadinessPanel({ recentAuthentication }: { recentAuthentication: boolean }) {
  const [overview, setOverview] = useState<OperationsOverview | null>(null)
  const [exportPreview, setExportPreview] = useState<ExportPreview | null>(null)
  const [includeFiles, setIncludeFiles] = useState(true)
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState<'export' | 'retention' | 'erase' | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const refresh = async () => {
    const [nextOverview, nextExport] = await Promise.all([
      api.operationsOverview(),
      api.exportPreview(),
    ])
    setOverview(nextOverview)
    setExportPreview(nextExport)
  }

  useEffect(() => {
    refresh().catch((next) => setError(next.message))
  }, [])

  const downloadExport = async () => {
    setBusy('export')
    setError('')
    setMessage('')
    try {
      const result = await api.downloadHouseholdExport(includeFiles)
      const href = URL.createObjectURL(result.blob)
      const anchor = document.createElement('a')
      anchor.href = href
      anchor.download = result.filename
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(href)
      setMessage('Der portable Vorrio-Export wurde heruntergeladen.')
      await refresh()
    } catch (next) {
      setError(next instanceof Error ? next.message : 'Export fehlgeschlagen')
    } finally {
      setBusy(null)
    }
  }

  const runRetention = async () => {
    setBusy('retention')
    setError('')
    setMessage('')
    try {
      const result = await api.runRetention()
      setMessage(`${result.deleted_file_count} Bondateien gelöscht; erkannte Einkaufsdaten bleiben erhalten.`)
      await refresh()
    } catch (next) {
      setError(next instanceof Error ? next.message : 'Bereinigung fehlgeschlagen')
    } finally {
      setBusy(null)
    }
  }

  const eraseHousehold = async () => {
    if (confirmation !== ERASE_CONFIRMATION) return
    const accepted = window.confirm('Wirklich alle Vorrio-Daten dieses Haushalts unwiderruflich löschen?')
    if (!accepted) return
    setBusy('erase')
    setError('')
    try {
      await api.eraseHousehold(confirmation)
      window.location.assign('/')
    } catch (next) {
      setError(next instanceof Error ? next.message : 'Löschung fehlgeschlagen')
      setBusy(null)
    }
  }

  return <>
    <section className="settings-section operations-section">
      <div className="section-heading"><Activity /><div><h2>Betrieb & Verlauf</h2><p>Datenschutzfreundlicher Zustand der lokalen Installation.</p></div></div>
      {!overview ? <p className="operations-loading"><LoaderCircle className="spin" /> Betriebsdaten werden geladen</p> : <>
        <div className="operations-metrics">
          <article><Database /><span><strong>{overview.database_integrity === 'ok' ? 'In Ordnung' : overview.database_integrity}</strong><small>Datenbank · {bytes(overview.database_bytes)}</small></span></article>
          <article><ShieldAlert /><span><strong>{overview.counts.failures_24h}</strong><small>Fehler in 24 Stunden</small></span></article>
          <article><Activity /><span><strong>{overview.counts.active_sessions}</strong><small>Aktive Sitzungen</small></span></article>
          <article><HardDrive /><span><strong>{overview.retention.retained_file_count}</strong><small>Gespeicherte Bondateien</small></span></article>
        </div>
        <div className="audit-list">
          <h3>Letzte wichtige Vorgänge</h3>
          {overview.recent_events.length === 0 ? <p>Noch keine Vorgänge protokolliert.</p> : overview.recent_events.slice(0, 12).map((event) => <div key={event.id}>
            <span className={`audit-state ${event.outcome}`} />
            <span><strong>{actionLabel(event.action)}</strong><small>{event.actor_label} · {new Date(event.created_at).toLocaleString('de-DE')}</small></span>
          </div>)}
        </div>
      </>}
    </section>

    <section className="settings-section portability-section">
      <div className="section-heading"><Download /><div><h2>Daten mitnehmen</h2><p>Lesbarer ZIP-Export ohne Passwörter, Tokens oder API-Schlüssel.</p></div></div>
      {exportPreview && <div className="export-summary"><strong>{exportPreview.counts.products} Produkte · {exportPreview.counts.receipts} Bons</strong><small>{exportPreview.product_image_file_count} eigene Produktbilder immer enthalten · {exportPreview.receipt_file_count} Bondateien optional</small></div>}
      <label className="toggle-row"><span><strong>Bondateien einschließen</strong><small>Ohne Auswahl enthält das ZIP weiterhin alle erkannten Daten.</small></span><input type="checkbox" checked={includeFiles} onChange={(event) => setIncludeFiles(event.target.checked)} /></label>
      <button type="button" className="button tertiary" onClick={downloadExport} disabled={busy !== null || !recentAuthentication}>{busy === 'export' ? <LoaderCircle className="spin" /> : <Download />} Export herunterladen</button>
      {!recentAuthentication && <p className="safety-hint">Bestätige oben zuerst noch einmal deine Identität.</p>}
    </section>

    <section className="settings-section retention-section">
      <div className="section-heading"><HardDrive /><div><h2>Aufbewahrung anwenden</h2><p>Entfernt nur abgelaufene Bondateien. Artikel, Preise und Bestand bleiben.</p></div></div>
      {overview && <p className="retention-preview"><strong>{overview.retention.expired_file_count} Dateien fällig</strong><span>{bytes(overview.retention.expired_bytes)} können jetzt freigegeben werden.</span></p>}
      <button type="button" className="button tertiary" onClick={runRetention} disabled={busy !== null || !recentAuthentication || !overview?.retention.expired_file_count}>{busy === 'retention' ? <LoaderCircle className="spin" /> : <Trash2 />} Jetzt bereinigen</button>
    </section>

    <section className="settings-section danger-section">
      <div className="section-heading"><ShieldAlert /><div><h2>Gefahrenzone</h2><p>Löscht diesen Haushalt mit Konten, Vorrat, Bons und Einstellungen endgültig.</p></div></div>
      <label>Zur Bestätigung exakt eingeben<input value={confirmation} autoComplete="off" placeholder={ERASE_CONFIRMATION} onChange={(event) => setConfirmation(event.target.value)} /></label>
      <button type="button" className="button danger" onClick={eraseHousehold} disabled={busy !== null || !recentAuthentication || confirmation !== ERASE_CONFIRMATION}>{busy === 'erase' ? <LoaderCircle className="spin" /> : <Trash2 />} Haushalt endgültig löschen</button>
    </section>
    {message && <p className="settings-result">{message}</p>}
    {error && <p className="field-error">{error}</p>}
  </>
}
