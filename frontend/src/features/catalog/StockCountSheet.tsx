import {
  ArrowLeft,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleMinus,
  CirclePlus,
  CloudDownload,
  ClipboardCheck,
  LoaderCircle,
  PackageCheck,
  Search,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import type {
  CatalogProductDetail,
  GrocyMasterData,
  StockCountLineInput,
  StockCountSession,
  StockCountSource,
} from '../../types'

type Notice = (kind: 'success' | 'error', text: string) => void
type DetailDraft = { location_id: number | null; variant_id: string | null; best_before_date: string }

const formatQuantity = (value: number) =>
  new Intl.NumberFormat('de-DE', { maximumFractionDigits: 3 }).format(value)

const mutationId = () =>
  `count_${typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}_${Math.random().toString(16).slice(2)}`}`

export function StockCountSheet({
  grocyEnabled,
  onClose,
  onCommitted,
  onNotice,
}: {
  grocyEnabled: boolean
  onClose: () => void
  onCommitted: () => Promise<void>
  onNotice: Notice
}) {
  const [products, setProducts] = useState<CatalogProductDetail[]>([])
  const [masterData, setMasterData] = useState<GrocyMasterData | null>(null)
  const [counts, setCounts] = useState<Record<string, string>>({})
  const [details, setDetails] = useState<Record<string, DetailDraft>>({})
  const [expanded, setExpanded] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [phase, setPhase] = useState<'count' | 'review' | 'done'>('count')
  const [source, setSource] = useState<StockCountSource>('manual')
  const [note, setNote] = useState('')
  const [sourceMessage, setSourceMessage] = useState('')
  const [busy, setBusy] = useState(true)
  const [session, setSession] = useState<StockCountSession | null>(null)
  const [clientMutationId] = useState(mutationId)

  useEffect(() => {
    Promise.all([api.stockCountProducts(), api.catalogMasterData()])
      .then(([loadedProducts, loadedMaster]) => {
        setProducts(loadedProducts)
        setMasterData(loadedMaster)
      })
      .catch((error) => onNotice('error', (error as Error).message))
      .finally(() => setBusy(false))
    // Load once for the isolated count session; a confirmed count closes or reloads it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase('de-DE')
    if (!needle) return products
    return products.filter((product) =>
      [product.name, product.product_group_name, product.default_location_name]
        .filter(Boolean)
        .some((value) => String(value).toLocaleLowerCase('de-DE').includes(needle)),
    )
  }, [products, query])

  const reviewed = useMemo(() => products.flatMap((product) => {
    const raw = counts[product.id]
    if (raw === undefined || raw === '') return []
    const counted = Number(raw)
    if (!Number.isFinite(counted) || counted < 0) return []
    const detail = details[product.id] || {
      location_id: product.default_location_id ?? null,
      variant_id: null,
      best_before_date: '',
    }
    return [{ product, counted, detail, delta: counted - product.stock_quantity }]
  }), [counts, details, products])

  const enteredCount = Object.values(counts).filter((value) => value !== '').length
  const invalidCount = enteredCount - reviewed.length

  const setCount = (product: CatalogProductDetail, value: string) => {
    if (value !== '' && Number(value) < 0) return
    setCounts((current) => ({ ...current, [product.id]: value }))
    if (value !== '' && !details[product.id]) {
      setDetails((current) => ({
        ...current,
        [product.id]: {
          location_id: product.default_location_id ?? null,
          variant_id: null,
          best_before_date: '',
        },
      }))
    }
  }

  const step = (product: CatalogProductDetail, direction: -1 | 1) => {
    const raw = counts[product.id]
    const base = raw === undefined || raw === '' ? product.stock_quantity : Number(raw)
    setCount(product, String(Math.max(0, Math.round((base + direction) * 1000) / 1000)))
  }

  const loadGrocy = async () => {
    setBusy(true)
    try {
      const preview = await api.grocyStockPreview()
      const nextCounts: Record<string, string> = {}
      const nextDetails: Record<string, DetailDraft> = {}
      for (const item of preview.items) {
        nextCounts[item.product_id] = String(item.proposed_quantity)
        nextDetails[item.product_id] = {
          location_id: item.default_location_id,
          variant_id: null,
          best_before_date: item.best_before_date || '',
        }
      }
      setCounts(nextCounts)
      setDetails(nextDetails)
      setSource('grocy_review')
      setSourceMessage(
        `${preview.items.length} Grocy-Werte als Vorschlag geladen.${preview.unmapped.length ? ` ${preview.unmapped.length} nicht zugeordnete Grocy-Produkte wurden ausgelassen.` : ''}`,
      )
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const commit = async () => {
    const lines: StockCountLineInput[] = reviewed.map(({ product, counted, detail }) => ({
      product_id: product.id,
      variant_id: detail.variant_id,
      location_id: detail.location_id,
      counted_quantity: counted,
      best_before_date: detail.best_before_date || null,
      unit_price: null,
      note: '',
    }))
    setBusy(true)
    try {
      const result = await api.createStockCount({
        client_mutation_id: clientMutationId,
        source,
        note,
        lines,
      })
      setSession(result)
      setPhase('done')
      await onCommitted()
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="sheet-backdrop" role="presentation">
      <section className="product-sheet stock-count-sheet" role="dialog" aria-modal="true" aria-label="Bestand zählen">
        <span className="sheet-handle" />
        <header>
          <div>
            <h2>{phase === 'count' ? 'Bestand zählen' : phase === 'review' ? 'Zählung prüfen' : 'Bestand aktualisiert'}</h2>
            <p>{phase === 'count' ? 'Nur eingetragene Produkte werden verändert' : phase === 'review' ? 'Vorher und gezählte Menge direkt vergleichen' : 'Die Differenzen wurden nachvollziehbar gebucht'}</p>
          </div>
          <button type="button" className="icon-close" onClick={onClose} aria-label="Bestandszählung schließen"><X /></button>
        </header>

        {busy && !products.length ? (
          <div className="inline-loading stock-count-loading"><LoaderCircle className="spin" /> Katalog vorbereiten…</div>
        ) : phase === 'count' ? (
          <>
            <div className="stock-count-toolbar">
              <label className="search-field"><Search /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Produkt oder Lagerort suchen" /></label>
              {grocyEnabled && <button type="button" className="button tertiary compact" disabled={busy} onClick={loadGrocy}>{busy ? <LoaderCircle className="spin" /> : <CloudDownload />} Grocy-Vorschlag</button>}
            </div>
            {sourceMessage && <p className="stock-count-source"><Check /> {sourceMessage}</p>}
            <div className="stock-count-progress"><span style={{ width: `${products.length ? Math.min(100, (enteredCount / products.length) * 100) : 0}%` }} /><strong>{enteredCount} von {products.length} erfasst</strong></div>
            <div className="stock-count-list">
              {filtered.map((product) => {
                const raw = counts[product.id] ?? ''
                const isEntered = raw !== ''
                const detail = details[product.id] || { location_id: product.default_location_id ?? null, variant_id: null, best_before_date: '' }
                return (
                  <article className={isEntered ? 'counted' : ''} key={product.id}>
                    <div className="stock-count-row">
                      <span className="catalog-icon">{product.image_url ? <img src={product.image_url} alt="" onError={(event) => { event.currentTarget.hidden = true }} /> : <PackageCheck />}</span>
                      <span className="stock-count-copy"><strong>{product.name}</strong><small>Aktuell {formatQuantity(product.stock_quantity)} {product.default_quantity_unit_name || 'Einheiten'}</small></span>
                      <div className="stock-count-input">
                        <button type="button" onClick={() => step(product, -1)} aria-label={`${product.name} um eins verringern`}><CircleMinus /></button>
                        <input aria-label={`Gezählte Menge ${product.name}`} inputMode="decimal" type="number" min="0" step="0.001" placeholder="–" value={raw} onChange={(event) => setCount(product, event.target.value)} />
                        <button type="button" onClick={() => step(product, 1)} aria-label={`${product.name} um eins erhöhen`}><CirclePlus /></button>
                      </div>
                      {isEntered && <button type="button" className="count-detail-toggle" aria-label={`Details für ${product.name}`} onClick={() => setExpanded(expanded === product.id ? null : product.id)}>{expanded === product.id ? <ChevronUp /> : <ChevronDown />}</button>}
                    </div>
                    {expanded === product.id && isEntered && masterData && (
                      <div className="stock-count-details">
                        <label>Lagerort<select value={detail.location_id ?? ''} onChange={(event) => setDetails({ ...details, [product.id]: { ...detail, location_id: event.target.value ? Number(event.target.value) : null } })}><option value="">Kein Lagerort</option>{masterData.locations.map((location) => <option value={location.id} key={location.id}>{location.name}</option>)}</select></label>
                        <label>Variante<select value={detail.variant_id ?? ''} onChange={(event) => setDetails({ ...details, [product.id]: { ...detail, variant_id: event.target.value || null } })}><option value="">Allgemeines Produkt</option>{product.variants.map((variant) => <option value={variant.id} key={variant.id}>{[variant.brand, variant.name, variant.package_amount && variant.package_unit ? `${formatQuantity(variant.package_amount)} ${variant.package_unit}` : null].filter(Boolean).join(' · ')}</option>)}</select></label>
                        <label>Mindesthaltbar bis<input type="date" value={detail.best_before_date} onChange={(event) => setDetails({ ...details, [product.id]: { ...detail, best_before_date: event.target.value } })} /></label>
                      </div>
                    )}
                  </article>
                )
              })}
              {!filtered.length && <p className="empty-inline">Kein passendes Produkt gefunden.</p>}
            </div>
            <footer className="stock-count-footer">
              <span><strong>{enteredCount} erfasst</strong><small>Nicht ausgefüllte Produkte bleiben unverändert.</small></span>
              <button type="button" className="button primary" disabled={!reviewed.length || invalidCount > 0} onClick={() => setPhase('review')}><ClipboardCheck /> Änderungen prüfen</button>
            </footer>
          </>
        ) : phase === 'review' ? (
          <>
            <div className="stock-review-summary"><strong>{reviewed.length} Produkte geprüft</strong><span>{reviewed.filter((line) => Math.abs(line.delta) > 1e-9).length} mit Änderung</span></div>
            <div className="stock-review-list">
              {reviewed.map(({ product, counted, delta }) => (
                <article key={product.id}>
                  <span><strong>{product.name}</strong><small>{product.default_quantity_unit_name || 'Einheiten'}</small></span>
                  <span className="stock-review-values"><small>{formatQuantity(product.stock_quantity)} vorher</small><strong>{formatQuantity(counted)} gezählt</strong><em className={delta > 0 ? 'positive' : delta < 0 ? 'negative' : ''}>{delta > 0 ? '+' : ''}{formatQuantity(delta)}</em></span>
                </article>
              ))}
            </div>
            <label className="stock-count-note">Notiz zur Zählung<textarea rows={2} maxLength={1000} value={note} placeholder="Optional, z. B. Vorratskammer komplett gezählt" onChange={(event) => setNote(event.target.value)} /></label>
            <p className="stock-review-safety"><Check /> Erst diese Bestätigung erzeugt Bestandsbewegungen. Die Zählung bleibt danach im Verlauf nachvollziehbar.</p>
            <footer className="stock-count-footer review-actions">
              <button type="button" className="button tertiary" disabled={busy} onClick={() => setPhase('count')}><ArrowLeft /> Zurück</button>
              <button type="button" className="button primary" disabled={busy} onClick={commit}>{busy ? <LoaderCircle className="spin" /> : <ClipboardCheck />} {reviewed.length} Produkte übernehmen</button>
            </footer>
          </>
        ) : (
          <div className="stock-count-done">
            <span><CheckCircle2 /></span>
            <h3>{session?.changed_count || 0} Bestände geändert</h3>
            <p>{session?.line_count || 0} gezählte Produkte wurden geprüft. Jede Differenz ist im Bewegungsjournal dokumentiert.</p>
            <div><strong>{source === 'grocy_review' ? 'Geprüfter Grocy-Vorschlag' : 'Manuelle Zählung'}</strong><small>{note || 'Ohne zusätzliche Notiz'}</small></div>
            <button type="button" className="button primary full" onClick={onClose}><CheckCircle2 /> Fertig</button>
          </div>
        )}
      </section>
    </div>
  )
}
