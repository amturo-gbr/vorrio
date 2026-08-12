import {
  AlertTriangle,
  CheckCircle2,
  LoaderCircle,
  Pencil,
  ReceiptText,
  Store,
  TrendingDown,
  TrendingUp,
  WalletCards,
} from 'lucide-react'
import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import type { BudgetOverviewResponse } from '../../types'
import { formatCurrency, formatDate, formatNumber, translate } from '../../i18n'

type Notice = (kind: 'success' | 'error', text: string) => void

const euro = (value: number | null | undefined) => formatCurrency(value)

const monthLabel = (value: string) => formatDate(new Date(`${value}-15T12:00:00`), {
  month: 'long',
  year: 'numeric',
})

const shortMonth = (value: string) => formatDate(new Date(`${value}-15T12:00:00`), {
  month: 'short',
  year: '2-digit',
})

const statusCopy: Record<BudgetOverviewResponse['current_period']['status'], { title: string; text: string }> = {
  unconfigured: { title: 'Noch ohne Monatsziel', text: 'Lege ein gemeinsames Budget fest, sobald die ersten bestätigten Bons eine gute Basis bilden.' },
  on_track: { title: 'Im grünen Bereich', text: 'Ausgaben und aktuelle Hochrechnung liegen innerhalb des Monatsziels.' },
  watch: { title: 'Budget im Blick behalten', text: 'Die Warnschwelle oder die Hochrechnung für diesen Monat wurde erreicht.' },
  over: { title: 'Monatsziel erreicht', text: 'Die bestätigten Ausgaben liegen auf oder über dem eingestellten Monatsbudget.' },
}

export function BudgetOverview({
  canManage,
  onNotice,
}: {
  canManage: boolean
  onNotice: Notice
}) {
  const [overview, setOverview] = useState<BudgetOverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(false)
  const [monthlyLimit, setMonthlyLimit] = useState('')
  const [warningPercent, setWarningPercent] = useState(80)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const next = await api.budgetOverview(6)
      setOverview(next)
      setMonthlyLimit(next.settings.monthly_limit == null ? '' : formatNumber(next.settings.monthly_limit, { maximumFractionDigits: 2 }))
      setWarningPercent(next.settings.warning_percent)
      setEditing(!next.settings.configured && canManage)
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setLoading(false)
    }
  }, [canManage, onNotice])

  useEffect(() => {
    load().catch(() => undefined)
  }, [load])

  const highestMonth = useMemo(() => {
    if (!overview) return 1
    return Math.max(overview.settings.monthly_limit || 0, ...overview.months.map((month) => month.spent), 1)
  }, [overview])

  const save = async (event: FormEvent) => {
    event.preventDefault()
    const rawLimit = monthlyLimit.trim()
    const normalizedLimit = rawLimit.includes(',')
      ? rawLimit.replace(/\./g, '').replace(',', '.')
      : rawLimit
    const parsed = Number(normalizedLimit)
    if (!Number.isFinite(parsed) || parsed < 1 || parsed > 1_000_000) {
      onNotice('error', translate('Bitte ein Monatsbudget zwischen 1 und 1.000.000 Euro eingeben.'))
      return
    }
    setSaving(true)
    try {
      await api.updateBudgetSettings(parsed, warningPercent)
      await load()
      setEditing(false)
      onNotice('success', translate('Das gemeinsame Monatsbudget wurde gespeichert.'))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const clear = async () => {
    if (!window.confirm(translate('Monatsbudget entfernen? Deine Bons und Auswertungen bleiben vollständig erhalten.'))) return
    setSaving(true)
    try {
      await api.updateBudgetSettings(null, warningPercent)
      await load()
      onNotice('success', translate('Das Monatsziel wurde entfernt. Deine Ausgaben bleiben sichtbar.'))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="inline-loading budget-loading"><LoaderCircle className="spin" /> {translate("Haushaltsbudget aus bestätigten Bons laden…")}</div>
  }
  if (!overview) return null

  const current = overview.current_period
  const comparison = overview.comparison
  const status = statusCopy[current.status]
  const progress = Math.min(Math.max(current.percent_used || 0, 0), 100)
  const comparisonDirection = comparison.change_amount === 0 ? 'neutral' : comparison.change_amount < 0 ? 'positive' : 'negative'
  const comparisonText = comparison.receipt_count === 0
    ? translate('Noch kein vergleichbarer Vormonatszeitraum')
    : translate('{{amount}} {{direction}} als bis zum gleichen Tag im Vormonat', {
      amount: euro(Math.abs(comparison.change_amount)),
      direction: translate(comparison.change_amount <= 0 ? 'weniger' : 'mehr'),
    })

  return (
    <section className="budget-overview" aria-label={translate("Haushaltsbudget")}>
      <article className={`budget-hero ${current.status}`}>
        <header>
          <span className="budget-hero-icon"><WalletCards /></span>
          <span><small>{translate("Haushaltsbudget")}</small><h2>{monthLabel(current.month)}</h2></span>
          {canManage && overview.settings.configured && (
            <button type="button" className="budget-edit" onClick={() => setEditing((value) => !value)}><Pencil /> {translate("Anpassen")}</button>
          )}
        </header>
        <div className="budget-hero-grid">
          <div className="budget-spent">
            <small>{translate("Bestätigt ausgegeben")}</small>
            <strong>{euro(current.spent)}</strong>
            <span>{overview.settings.configured
              ? translate('von {{amount}}', { amount: euro(overview.settings.monthly_limit) })
              : translate('{{count}} bestätigte Bons', { count: current.receipt_count })}</span>
          </div>
          <div className="budget-state-copy">
            {current.status === 'on_track' ? <CheckCircle2 /> : current.status === 'unconfigured' ? <WalletCards /> : <AlertTriangle />}
            <span><strong>{translate(status.title)}</strong><small>{translate(status.text)}</small></span>
          </div>
        </div>
        {overview.settings.configured && (
          <div className="budget-progress">
            <span><strong>{formatNumber(current.percent_used || 0, { maximumFractionDigits: 1 })} %</strong><small>{translate('{{count}} Tage verbleiben', { count: current.days_remaining })}</small></span>
            <progress max="100" value={progress} aria-label={translate('{{percent}} Prozent des Monatsbudgets verwendet', { percent: formatNumber(progress, { maximumFractionDigits: 1 }) })} />
          </div>
        )}
      </article>

      {editing && canManage && (
        <form className="budget-editor" onSubmit={save}>
          <div>
            <span><strong>{translate("Monatsziel festlegen")}</strong><small>{translate("Gemeinsam für alle Familienkonten · aktuell nur EUR")}</small></span>
          </div>
          <label>{translate("Monatsbudget")}
            <span className="budget-money-input"><input inputMode="decimal" value={monthlyLimit} onChange={(event) => setMonthlyLimit(event.target.value)} placeholder={translate("z. B. 650")} aria-label={translate("Monatsbudget in Euro")} /><strong>€</strong></span>
          </label>
          <label>{translate("Warnung ab")}
            <select value={warningPercent} onChange={(event) => setWarningPercent(Number(event.target.value))}>
              <option value={70}>70 %</option>
              <option value={80}>80 %</option>
              <option value={90}>90 %</option>
              <option value={100}>100 %</option>
            </select>
          </label>
          <div className="budget-editor-actions">
            <button type="submit" className="button primary" disabled={saving}>{saving ? <LoaderCircle className="spin" /> : <CheckCircle2 />} {translate("Budget speichern")}</button>
            {overview.settings.configured && <button type="button" className="button tertiary" disabled={saving} onClick={clear}>{translate("Budget entfernen")}</button>}
          </div>
        </form>
      )}

      <div className="budget-kpis">
        <article><small>{translate("Noch verfügbar")}</small><strong className={current.remaining != null && current.remaining < 0 ? 'negative' : ''}>{euro(current.remaining)}</strong><span>{current.daily_available == null ? translate('Monatsziel noch offen') : translate('{{amount}} pro verbleibendem Tag', { amount: euro(current.daily_available) })}</span></article>
        <article><small>{translate("Hochrechnung")}</small><strong>{current.receipt_count ? euro(current.forecast) : '–'}</strong><span>{current.receipt_count ? translate('aus {{count}} Kalendertagen', { count: current.days_elapsed }) : translate('Noch kein bestätigter Bon im Monat')}</span></article>
        <article className={comparisonDirection}><small>{translate("Zum Vormonat")}</small><strong>{comparison.receipt_count ? `${comparison.change_amount > 0 ? '+' : ''}${euro(comparison.change_amount)}` : '–'}</strong><span>{comparisonText}</span></article>
        <article><small>{translate("Durchschnitt pro Bon")}</small><strong>{current.receipt_count ? euro(current.average_receipt) : '–'}</strong><span>{translate('{{count}} gezählte Bon-Gesamtsummen', { count: current.receipt_count })}</span></article>
      </div>

      <div className="budget-workspace">
        <section className="budget-panel budget-history-panel">
          <div className="budget-section-title"><TrendingUp /><span><h3>{translate("Sechs Monate")}</h3><p>{translate("Nur ausdrücklich übernommene Bons")}</p></span></div>
          <div className="budget-month-list">
            {overview.months.map((month) => (
              <article key={month.month} className={month.is_current ? 'current' : ''}>
                <span><strong>{shortMonth(month.month)}</strong><small>{translate('{{count}} Bons', { count: month.receipt_count })}</small></span>
                <span className="budget-bar"><i style={{ width: `${Math.max(month.spent / highestMonth * 100, month.spent ? 2 : 0)}%` }} /></span>
                <strong>{euro(month.spent)}</strong>
              </article>
            ))}
          </div>
        </section>

        <section className="budget-panel budget-store-panel">
          <div className="budget-section-title"><Store /><span><h3>{translate("Geschäfte im Monat")}</h3><p>{translate("Anteil an bestätigten Bon-Gesamtsummen")}</p></span></div>
          {overview.stores.length ? (
            <div className="budget-store-list">
              {overview.stores.map((store) => (
                <article key={store.store_key}>
                  <span><strong>{store.store_name}</strong><small>{translate('{{count}} Bons', { count: store.receipt_count })} · {formatNumber(store.share_percent, { maximumFractionDigits: 1 })} %</small></span>
                  <strong>{euro(store.spent)}</strong>
                  <span className="budget-store-bar"><i style={{ width: `${store.share_percent}%` }} /></span>
                </article>
              ))}
            </div>
          ) : <div className="budget-empty"><ReceiptText /><p>{translate("Noch keine bestätigte Bon-Gesamtsumme in diesem Monat.")}</p></div>}
        </section>
      </div>

      <aside className="budget-data-note">
        <ReceiptText />
        <span>
          <strong>{overview.data_quality.counted_receipt_count} {translate("von")} {overview.data_quality.confirmed_receipt_count} {translate("bestätigten Bons fließen ein")}</strong>
          <small>
            {overview.data_quality.pending_receipt_count
              ? `${translate('{{count}} Bons warten noch auf deine Prüfung.', { count: overview.data_quality.pending_receipt_count })} `
              : `${translate('Keine offenen Bons aus diesem Monat.')} `}
            {overview.data_quality.missing_total_count ? `${translate('{{count}} ohne Gesamtsumme.', { count: overview.data_quality.missing_total_count })} ` : ''}
            {overview.data_quality.other_currency_receipt_count ? `${translate('{{count}} in anderer Währung.', { count: overview.data_quality.other_currency_receipt_count })} ` : ''}
            {translate("Keine Bankdaten und keine behaupteten Live-Marktpreise.")}
          </small>
        </span>
        {comparisonDirection === 'positive' ? <TrendingDown /> : comparisonDirection === 'negative' ? <TrendingUp /> : null}
      </aside>
    </section>
  )
}
