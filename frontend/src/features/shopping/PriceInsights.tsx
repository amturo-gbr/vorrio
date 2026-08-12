import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  History,
  LoaderCircle,
  PackageCheck,
  Search,
  Store,
  Tag,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import type {
  CatalogPriceHistoryItem,
  PriceInsightsResponse,
  PriceProductSummary,
} from '../../types'
import { currentLocale, formatCurrency, formatDate, formatNumber, translate } from '../../i18n'

type Notice = (kind: 'success' | 'error', text: string) => void

const euro = (value: number | null | undefined) => formatCurrency(value)

const shortDate = (value: string | null | undefined) => {
  if (!value) return translate('Datum unbekannt')
  return formatDate(new Date(`${value}T12:00:00`), { day: '2-digit', month: 'short', year: '2-digit' })
}

const packageLabel = (item: CatalogPriceHistoryItem) => {
  const amount = item.package_amount == null
    ? ''
    : formatNumber(item.package_amount)
  return [item.brand, item.variant_name, amount && item.package_unit ? `${amount} ${item.package_unit}` : '']
    .filter(Boolean)
    .join(' · ')
}

export function PriceInsights({ onNotice }: { onNotice: Notice }) {
  const [overview, setOverview] = useState<PriceInsightsResponse | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [history, setHistory] = useState<CatalogPriceHistoryItem[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(false)

  const loadOverview = useCallback(async () => {
    setLoading(true)
    try {
      const next = await api.priceInsights()
      setOverview(next)
      setSelectedId((current) => current && next.products.some((item) => item.product_id === current)
        ? current
        : next.products[0]?.product_id || null)
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setLoading(false)
    }
  }, [onNotice])

  useEffect(() => {
    loadOverview().catch(() => undefined)
  }, [loadOverview])

  useEffect(() => {
    if (!selectedId) {
      setHistory([])
      return
    }
    setHistoryLoading(true)
    api.catalogProductPriceHistory(selectedId)
      .then(setHistory)
      .catch((error) => onNotice('error', (error as Error).message))
      .finally(() => setHistoryLoading(false))
  }, [onNotice, selectedId])

  const products = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase(currentLocale())
    if (!needle) return overview?.products || []
    return (overview?.products || []).filter((product) =>
      `${product.product_name} ${product.latest_store}`.toLocaleLowerCase(currentLocale()).includes(needle))
  }, [overview, query])
  const selected = overview?.products.find((product) => product.product_id === selectedId) || null

  if (loading) {
    return <div className="inline-loading price-loading"><LoaderCircle className="spin" /> {translate("Preise aus bestätigten Bons laden…")}</div>
  }

  if (!overview?.products.length) {
    return (
      <div className="price-empty">
        <span><BarChart3 /></span>
        <h2>{translate("Noch kein Preisverlauf")}</h2>
        <p>{translate("Sobald ein zugeordneter Bon in den Vorrat übernommen wurde, entsteht hier automatisch dein privates Preiswissen.")}</p>
      </div>
    )
  }

  return (
    <section className="price-insights" aria-label={translate("Preiswissen")}>
      <div className="price-disclaimer"><Tag /><span><strong>{translate("Deine bestätigten Bonpreise")}</strong><small>{translate("Historische Werte – keine Livepreise oder Verfügbarkeitsanzeige.")}</small></span></div>
      <div className="price-overview-stats">
        <article><strong>{overview.product_count}</strong><span>{translate("Produkte mit Preisen")}</span></article>
        <article><strong>{overview.store_count}</strong><span>{translate("Geschäfte erkannt")}</span></article>
        <article><strong>{overview.observation_count}</strong><span>{translate("Preisbeobachtungen")}</span></article>
      </div>

      <div className="price-workspace">
        <aside className="price-product-browser">
          <label className="price-search"><Search /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={translate("Produkt suchen")} /></label>
          <div className="price-product-list">
            {products.map((product) => <ProductChoice key={product.product_id} product={product} selected={product.product_id === selectedId} onSelect={() => setSelectedId(product.product_id)} />)}
            {!products.length && <p className="price-no-result">{translate("Kein Produkt mit Preisverlauf gefunden.")}</p>}
          </div>
        </aside>

        {selected && (
          <div className="price-detail">
            <header className="price-product-header">
              <span className="price-product-image">{selected.image_url ? <img src={selected.image_url} alt="" /> : <PackageCheck />}</span>
              <span><small>{translate("Preisverlauf")}</small><h2>{selected.product_name}</h2><p>{translate("Zuletzt bei")} {selected.latest_store} · {shortDate(selected.latest_date)}</p></span>
            </header>

            <div className="price-kpis">
              <article><small>{translate("Zuletzt")}</small><strong>{euro(selected.latest_price)}</strong><span>{translate("pro")} {selected.quantity_unit_name || translate('Einheit')}</span></article>
              <article><small>{translate("Bisher am günstigsten")}</small><strong>{euro(selected.lowest_price)}</strong><span>{translate("aus")} {selected.observation_count} {translate("Käufen")}</span></article>
              <article className={selected.change_amount == null ? '' : selected.change_amount <= 0 ? 'positive' : 'negative'}>
                <small>{translate("Seit dem Kauf davor")}</small>
                <strong>{selected.change_amount == null ? '–' : `${selected.change_amount > 0 ? '+' : ''}${euro(selected.change_amount)}`}</strong>
                <span>{selected.change_percent == null ? translate('Noch kein Vergleich') : `${selected.change_percent > 0 ? '+' : ''}${formatNumber(selected.change_percent)} %`}</span>
              </article>
            </div>

            <section className="store-comparison">
              <div className="price-section-title"><Store /><span><h3>{translate("Geschäfte vergleichen")}</h3><p>{translate("Jeweils der zuletzt bestätigte Preis")}</p></span></div>
              <div className="store-price-list">
                {selected.stores.map((store, index) => (
                  <article key={store.store_key} className={index === 0 && selected.stores.length > 1 ? 'best' : ''}>
                    <span className="store-rank">{index + 1}</span>
                    <span className="store-copy"><strong>{store.store_name}</strong><small>{store.observation_count}{translate("× gesehen · zuletzt")} {shortDate(store.latest_date)}</small></span>
                    <span className="store-price"><strong>{euro(store.latest_price)}</strong><small>{translate("Tiefst")} {euro(store.lowest_price)}</small></span>
                  </article>
                ))}
              </div>
            </section>

            <section className="price-history-panel">
              <div className="price-section-title"><History /><span><h3>{translate("Verlauf")}</h3><p>{translate("Neueste bestätigte Käufe zuerst")}</p></span></div>
              {historyLoading ? <div className="inline-loading"><LoaderCircle className="spin" /> {translate("Verlauf laden…")}</div> : (
                <div className="price-history-list">
                  {history.filter((item) => item.unit_price != null).map((item, index) => {
                    const previous = history[index + 1]?.unit_price
                    const down = previous != null && item.unit_price != null && item.unit_price < previous
                    const up = previous != null && item.unit_price != null && item.unit_price > previous
                    return (
                      <article key={item.receipt_item_id}>
                        <span className={`history-trend ${down ? 'down' : up ? 'up' : ''}`}>{down ? <ArrowDownRight /> : up ? <ArrowUpRight /> : <span />}</span>
                        <span className="history-price-copy"><strong>{item.retailer || item.store_name || translate('Geschäft')}</strong><small>{packageLabel(item) || translate('Standardvariante')} · {shortDate(item.purchase_date)}</small></span>
                        <strong>{euro(item.unit_price)}</strong>
                      </article>
                    )
                  })}
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </section>
  )
}

function ProductChoice({ product, selected, onSelect }: { product: PriceProductSummary; selected: boolean; onSelect: () => void }) {
  const direction = product.change_amount == null ? 'neutral' : product.change_amount <= 0 ? 'down' : 'up'
  return (
    <button type="button" className={`price-product-choice ${selected ? 'selected' : ''}`} onClick={onSelect}>
      <span className="price-product-thumb">{product.image_url ? <img src={product.image_url} alt="" /> : <PackageCheck />}</span>
      <span><strong>{product.product_name}</strong><small>{product.latest_store} · {shortDate(product.latest_date)}</small></span>
      <span className={`price-choice-value ${direction}`}><strong>{euro(product.latest_price)}</strong><small>{direction === 'down' ? translate('günstiger') : direction === 'up' ? translate('teurer') : `${product.observation_count}×`}</small></span>
    </button>
  )
}
