import { Activity, Database, Download, HardDrive, LoaderCircle, ShieldAlert, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../../api'
import type { ExportPreview, OperationsOverview } from '../../types'
import { formatDate, formatNumber, translate } from '../../i18n'

const ERASE_CONFIRMATION = 'HAUSHALT ENDGÜLTIG LÖSCHEN'

const bytes = (value: number) => {
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${formatNumber(value / 1024, { maximumFractionDigits: 1 })} KB`
  return `${formatNumber(value / 1024 / 1024, { maximumFractionDigits: 1 })} MB`
}

const actionLabel = (action: string) => action
  .replace(/^GET /, `${translate('Gelesen')}: `)
  .replace(/^POST /, `${translate('Ausgeführt')}: `)
  .replace(/^PUT /, `${translate('Aktualisiert')}: `)
  .replace(/^PATCH /, `${translate('Geändert')}: `)
  .replace(/^DELETE /, `${translate('Gelöscht')}: `)
  .replace('portable_export', translate('Datenexport erstellt'))
  .replace('manual_retention', translate('Aufbewahrung angewendet'))
  .replace('scheduled_retention', translate('Automatische Aufbewahrung'))

export function LaunchReadinessPanel({ recentAuthentication }: { recentAuthentication: boolean }) {
  const [overview, setOverview] = useState<OperationsOverview | null>(null)
  const [exportPreview, setExportPreview] = useState<ExportPreview | null>(null)
  const [includeFiles, setIncludeFiles] = useState(true)
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState<'export' | 'retention' | 'erase' | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const eraseConfirmationLabel = translate(ERASE_CONFIRMATION)

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
      setMessage(translate('Der portable Vorrio-Export wurde heruntergeladen.'))
      await refresh()
    } catch (next) {
      setError(next instanceof Error ? next.message : translate('Export fehlgeschlagen'))
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
      setMessage(translate('{{count}} Bondateien gelöscht; erkannte Einkaufsdaten bleiben erhalten.', { count: result.deleted_file_count }))
      await refresh()
    } catch (next) {
      setError(next instanceof Error ? next.message : translate('Bereinigung fehlgeschlagen'))
    } finally {
      setBusy(null)
    }
  }

  const eraseHousehold = async () => {
    if (confirmation !== eraseConfirmationLabel) return
    const accepted = window.confirm(translate('Wirklich alle Vorrio-Daten dieses Haushalts unwiderruflich löschen?'))
    if (!accepted) return
    setBusy('erase')
    setError('')
    try {
      await api.eraseHousehold(ERASE_CONFIRMATION)
      window.location.assign('/')
    } catch (next) {
      setError(next instanceof Error ? next.message : translate('Löschung fehlgeschlagen'))
      setBusy(null)
    }
  }

  return <>
    <section className="settings-section operations-section">
      <div className="section-heading"><Activity /><div><h2>{translate("Betrieb & Verlauf")}</h2><p>{translate("Datenschutzfreundlicher Zustand der lokalen Installation.")}</p></div></div>
      {!overview ? <p className="operations-loading"><LoaderCircle className="spin" /> {translate("Betriebsdaten werden geladen")}</p> : <>
        <div className="operations-metrics">
          <article><Database /><span><strong>{overview.database_integrity === 'ok' ? translate('In Ordnung') : overview.database_integrity}</strong><small>{translate("Datenbank ·")} {bytes(overview.database_bytes)}</small></span></article>
          <article title={translate("Abgelehnte Eingaben und durch Sicherheitsregeln blockierte Aktionen")}><ShieldAlert /><span><strong>{overview.counts.failures_24h}</strong><small>{translate("Abgewiesen in 24 Stunden")}</small></span></article>
          <article><Activity /><span><strong>{overview.counts.active_sessions}</strong><small>{translate("Aktive Sitzungen")}</small></span></article>
          <article><HardDrive /><span><strong>{overview.retention.retained_file_count}</strong><small>{translate("Gespeicherte Bondateien")}</small></span></article>
        </div>
        <div className="audit-list">
          <h3>{translate("Letzte wichtige Vorgänge")}</h3>
          {overview.recent_events.length === 0 ? <p>{translate("Noch keine Vorgänge protokolliert.")}</p> : overview.recent_events.slice(0, 12).map((event) => <div key={event.id}>
            <span className={`audit-state ${event.outcome}`} />
            <span><strong>{actionLabel(event.action)}</strong><small>{event.actor_label} · {formatDate(event.created_at, { dateStyle: 'medium', timeStyle: 'short' })}</small></span>
          </div>)}
        </div>
      </>}
    </section>

    <section className="settings-section portability-section">
      <div className="section-heading"><Download /><div><h2>{translate("Daten mitnehmen")}</h2><p>{translate("Lesbarer ZIP-Export ohne Passwörter, Tokens oder API-Schlüssel.")}</p></div></div>
      {exportPreview && <div className="export-summary"><strong>{translate('{{count}} Produkte', { count: exportPreview.counts.products })} · {translate('{{count}} Bons', { count: exportPreview.counts.receipts })}</strong><small>{translate('{{count}} eigene Produktbilder immer enthalten', { count: exportPreview.product_image_file_count })} · {translate('{{count}} Bondateien optional', { count: exportPreview.receipt_file_count })}</small></div>}
      <label className="toggle-row"><span><strong>{translate("Bondateien einschließen")}</strong><small>{translate("Ohne Auswahl enthält das ZIP weiterhin alle erkannten Daten.")}</small></span><input type="checkbox" checked={includeFiles} onChange={(event) => setIncludeFiles(event.target.checked)} /></label>
      <button type="button" className="button tertiary" onClick={downloadExport} disabled={busy !== null || !recentAuthentication}>{busy === 'export' ? <LoaderCircle className="spin" /> : <Download />} {translate("Export herunterladen")}</button>
      {!recentAuthentication && <p className="safety-hint">{translate("Bestätige oben zuerst noch einmal deine Identität.")}</p>}
    </section>

    <section className="settings-section retention-section">
      <div className="section-heading"><HardDrive /><div><h2>{translate("Aufbewahrung anwenden")}</h2><p>{translate("Entfernt nur abgelaufene Bondateien. Artikel, Preise und Bestand bleiben.")}</p></div></div>
      {overview && <p className="retention-preview"><strong>{translate('{{count}} Dateien fällig', { count: overview.retention.expired_file_count })}</strong><span>{translate('{{size}} können jetzt freigegeben werden.', { size: bytes(overview.retention.expired_bytes) })}</span></p>}
      <button type="button" className="button tertiary" onClick={runRetention} disabled={busy !== null || !recentAuthentication || !overview?.retention.expired_file_count}>{busy === 'retention' ? <LoaderCircle className="spin" /> : <Trash2 />} {translate("Jetzt bereinigen")}</button>
    </section>

    <section className="settings-section danger-section">
      <div className="section-heading"><ShieldAlert /><div><h2>{translate("Gefahrenzone")}</h2><p>{translate("Löscht diesen Haushalt mit Konten, Vorrat, Bons und Einstellungen endgültig.")}</p></div></div>
      <label>{translate("Zur Bestätigung exakt eingeben")}<input value={confirmation} autoComplete="off" placeholder={eraseConfirmationLabel} onChange={(event) => setConfirmation(event.target.value)} /></label>
      <button type="button" className="button danger" onClick={eraseHousehold} disabled={busy !== null || !recentAuthentication || confirmation !== eraseConfirmationLabel}>{busy === 'erase' ? <LoaderCircle className="spin" /> : <Trash2 />} {translate("Haushalt endgültig löschen")}</button>
    </section>
    {message && <p className="settings-result">{message}</p>}
    {error && <p className="field-error">{error}</p>}
  </>
}
