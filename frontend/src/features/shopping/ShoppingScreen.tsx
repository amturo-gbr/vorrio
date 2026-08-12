import {
  Check,
  ChevronRight,
  ClipboardList,
  History,
  LoaderCircle,
  Minus,
  PackageCheck,
  Plus,
  ReceiptText,
  RefreshCw,
  ShoppingBasket,
  Sparkles,
  BarChart3,
  WalletCards,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import type { Receipt, ShoppingListItem, ShoppingLowStockItem } from '../../types'
import { BudgetOverview } from './BudgetOverview'
import { PriceInsights } from './PriceInsights'
import { formatCurrency, formatDate, formatNumber, translate } from '../../i18n'

type Notice = (kind: 'success' | 'error', text: string) => void

const formatQuantity = (value: number) => formatNumber(value)

const euro = (value: number | null | undefined) => formatCurrency(value)

const shortDate = (value: string | null | undefined) => {
  if (!value) return translate('Heute')
  return formatDate(new Date(`${value}T12:00:00`), { day: '2-digit', month: 'short' })
}

const needsListChange = (item: ShoppingLowStockItem) =>
  !item.existing_item_id || (item.existing_desired_quantity || 0) + 1e-9 < item.suggested_quantity

export function ShoppingScreen({
  receipts,
  onOpenReceipt,
  onNotice,
  readOnly,
  canManageBudget,
}: {
  receipts: Receipt[]
  onOpenReceipt: (id: string) => void
  onNotice: Notice
  readOnly: boolean
  canManageBudget: boolean
}) {
  const [tab, setTab] = useState<'list' | 'budget' | 'prices' | 'history'>('list')
  const [items, setItems] = useState<ShoppingListItem[]>([])
  const [lowStock, setLowStock] = useState<ShoppingLowStockItem[]>([])
  const [loading, setLoading] = useState(true)
  const [busyItem, setBusyItem] = useState<string | null>(null)
  const [refillOpen, setRefillOpen] = useState(false)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const [nextItems, preview] = await Promise.all([
        api.shoppingList(),
        api.shoppingLowStock(),
      ])
      setItems(nextItems)
      setLowStock(preview.items.filter(needsListChange))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setLoading(false)
    }
  }, [onNotice])

  useEffect(() => {
    reload().catch(() => undefined)
  }, [reload])

  const updateItem = async (item: ShoppingListItem, desiredQuantity: number, checked = false) => {
    setBusyItem(item.id)
    try {
      const updated = await api.updateShoppingItem(item.id, {
        desired_quantity: Math.max(0.001, desiredQuantity),
        checked,
        notes: item.notes,
        expected_updated_at: item.updated_at,
      })
      if (checked) {
        setItems((current) => current.filter((row) => row.id !== item.id))
        onNotice('success', translate('{{product}} ist erledigt.', { product: item.product_name || item.label }))
      } else {
        setItems((current) => current.map((row) => row.id === item.id ? updated : row))
      }
      const preview = await api.shoppingLowStock()
      setLowStock(preview.items.filter(needsListChange))
    } catch (error) {
      onNotice('error', (error as Error).message)
      await reload()
    } finally {
      setBusyItem(null)
    }
  }

  return (
    <div className="screen simple-screen shopping-screen">
      <header className="page-header shopping-page-header">
        <div><h1>{translate("Einkäufe")}</h1><p>{translate("Gemeinsame Liste und deine verarbeiteten Bons.")}</p></div>
        {tab === 'list' && (
          <button className="button tertiary compact" type="button" onClick={() => reload()} disabled={loading}>
            <RefreshCw className={loading ? 'spin' : ''} /> {translate("Aktualisieren")}
          </button>
        )}
      </header>

      <div className="shopping-tabs" role="tablist" aria-label={translate("Einkaufsbereiche")}>
        <button role="tab" aria-selected={tab === 'list'} className={tab === 'list' ? 'selected' : ''} onClick={() => setTab('list')}>
          <ClipboardList /> {translate("Liste")} <span>{items.length}</span>
        </button>
        <button role="tab" aria-selected={tab === 'budget'} className={tab === 'budget' ? 'selected' : ''} onClick={() => setTab('budget')}>
          <WalletCards /> {translate("Budget")}
        </button>
        <button role="tab" aria-selected={tab === 'prices'} className={tab === 'prices' ? 'selected' : ''} onClick={() => setTab('prices')}>
          <BarChart3 /> {translate("Preise")}
        </button>
        <button role="tab" aria-selected={tab === 'history'} className={tab === 'history' ? 'selected' : ''} onClick={() => setTab('history')}>
          <History /> {translate("Bons")} <span>{receipts.length}</span>
        </button>
      </div>

      {tab === 'list' ? (
        <section className="shopping-list-panel" aria-label={translate("Einkaufsliste")}>
          {lowStock.length > 0 && !readOnly && (
            <button className="refill-callout" type="button" onClick={() => setRefillOpen(true)}>
              <span><Sparkles /></span>
              <span><strong>{translate('{{count}} Produkte werden knapp', { count: lowStock.length })}</strong><small>{translate("Mindestbestände prüfen und gezielt auffüllen")}</small></span>
              <span>{translate("Auffüllen")}</span>
              <ChevronRight />
            </button>
          )}

          {loading ? (
            <div className="inline-loading shopping-loading"><LoaderCircle className="spin" /> {translate("Einkaufsliste laden…")}</div>
          ) : items.length ? (
            <div className="shopping-items">
              <div className="shopping-list-heading"><h2>{translate("Offene Liste")}</h2><span>{translate('{{count}} Einträge', { count: items.length })}</span></div>
              {items.map((item) => (
                <article className="shopping-item" key={item.id}>
                  <button
                    className="shopping-check"
                    type="button"
                    aria-label={translate('{{product}} erledigen', { product: item.product_name || item.label })}
                    disabled={readOnly || busyItem === item.id}
                    onClick={() => updateItem(item, item.desired_quantity, true)}
                  >
                    {busyItem === item.id ? <LoaderCircle className="spin" /> : <Check />}
                  </button>
                  <span className="shopping-product-image">
                    {item.product_image_url ? <img src={item.product_image_url} alt="" onError={(event) => { event.currentTarget.hidden = true }} /> : <PackageCheck />}
                  </span>
                  <span className="shopping-item-copy">
                    <strong>{item.product_name || item.label}</strong>
                    <small>{formatQuantity(item.stock_quantity)} {item.quantity_unit_name || translate('Einheiten')} · {translate('Ziel')} {formatQuantity(item.shopping_target_quantity)}</small>
                  </span>
                  <span className="shopping-stepper" aria-label={translate('Menge für {{product}}', { product: item.product_name || item.label })}>
                    <button type="button" aria-label={translate("Menge verringern")} disabled={readOnly || busyItem === item.id || item.desired_quantity <= 1} onClick={() => updateItem(item, item.desired_quantity - 1)}><Minus /></button>
                    <strong>{formatQuantity(item.desired_quantity)}</strong>
                    <button type="button" aria-label={translate("Menge erhöhen")} disabled={readOnly || busyItem === item.id} onClick={() => updateItem(item, item.desired_quantity + 1)}><Plus /></button>
                  </span>
                </article>
              ))}
            </div>
          ) : (
            <div className="shopping-empty">
              <span><ShoppingBasket /></span>
              <h2>{translate("Alles besorgt")}</h2>
              <p>{translate("Deine Liste ist leer. Neue Artikel kommen per Scanner oder nach geprüfter Mindestbestand-Empfehlung dazu.")}</p>
            </div>
          )}
        </section>
      ) : tab === 'budget' ? (
        <BudgetOverview canManage={canManageBudget} onNotice={onNotice} />
      ) : tab === 'prices' ? (
        <PriceInsights onNotice={onNotice} />
      ) : (
        <HistoryList receipts={receipts} onOpenReceipt={onOpenReceipt} />
      )}

      {refillOpen && !readOnly && (
        <RefillSheet
          items={lowStock}
          onClose={() => setRefillOpen(false)}
          onGenerated={async (message) => {
            setRefillOpen(false)
            onNotice('success', message)
            await reload()
          }}
          onNotice={onNotice}
        />
      )}
    </div>
  )
}

function HistoryList({ receipts, onOpenReceipt }: { receipts: Receipt[]; onOpenReceipt: (id: string) => void }) {
  return (
    <div className="history-list shopping-history">
      {receipts.map((receipt) => (
        <button key={receipt.id} className="history-row" onClick={() => onOpenReceipt(receipt.id)}>
          <span className="history-date">{shortDate(receipt.purchase_date)}</span>
          <span className="history-main"><strong>{receipt.store_name || translate('Einkauf')}</strong><small>{translate('{{count}} Artikel', { count: receipt.item_count || 0 })}</small></span>
          <strong>{euro(receipt.total)}</strong>
          <ChevronRight />
        </button>
      ))}
      {!receipts.length && <div className="empty-page"><ReceiptText /><h2>{translate("Noch keine Bons")}</h2><p>{translate("Nach dem ersten Bon entsteht hier dein Einkaufsverlauf.")}</p></div>}
    </div>
  )
}

function RefillSheet({
  items,
  onClose,
  onGenerated,
  onNotice,
}: {
  items: ShoppingLowStockItem[]
  onClose: () => void
  onGenerated: (message: string) => Promise<void>
  onNotice: Notice
}) {
  const [selected, setSelected] = useState<Set<string>>(() => new Set(items.map((item) => item.product_id)))
  const [busy, setBusy] = useState(false)
  const selectedItems = useMemo(() => items.filter((item) => selected.has(item.product_id)), [items, selected])

  const toggle = (productId: string) => {
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(productId)) next.delete(productId)
      else next.add(productId)
      return next
    })
  }

  const generate = async () => {
    setBusy(true)
    try {
      const result = await api.generateShoppingList({
        client_mutation_id: `shopping-${crypto.randomUUID()}`,
        product_ids: selectedItems.map((item) => item.product_id),
      })
      const changed = result.created_count + result.updated_count
      await onGenerated(changed
        ? translate('{{count}} Einträge wurden zur Einkaufsliste hinzugefügt.', { count: changed })
        : translate('Die Einkaufsliste war bereits aktuell.'))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="sheet-backdrop" role="presentation">
      <section className="product-sheet refill-sheet" role="dialog" aria-modal="true" aria-label={translate("Auffüllen prüfen")}>
        <span className="sheet-handle" />
        <header>
          <div><h2>{translate("Auffüllen prüfen")}</h2><p>{translate("Vorrio ändert erst nach deiner Bestätigung die Liste.")}</p></div>
          <button type="button" className="icon-close" onClick={onClose} aria-label={translate("Vorschläge schließen")}><X /></button>
        </header>
        <div className="refill-summary"><Sparkles /><span><strong>{items.length} {translate("Vorschläge")}</strong><small>{translate("Aus aktuellem Bestand, Mindestbestand und Auffüllziel")}</small></span></div>
        <div className="refill-list">
          {items.map((item) => {
            const active = selected.has(item.product_id)
            return (
              <button type="button" className={`refill-row ${active ? 'selected' : ''}`} key={item.product_id} onClick={() => toggle(item.product_id)}>
                <span className="refill-select">{active && <Check />}</span>
                <span className="shopping-product-image">
                  {item.product_image_url ? <img src={item.product_image_url} alt="" onError={(event) => { event.currentTarget.hidden = true }} /> : <PackageCheck />}
                </span>
                <span className="refill-copy">
                  <strong>{item.product_name}</strong>
                  <small>{translate("Da")} {formatQuantity(item.current_quantity)} {translate("· Minimum")} {formatQuantity(item.minimum_quantity)} {translate("· Ziel")} {formatQuantity(item.target_quantity)}</small>
                  {item.existing_item_id && <em>{translate("Schon auf der Liste:")} {formatQuantity(item.existing_desired_quantity || 0)}</em>}
                </span>
                <span className="refill-amount"><small>{translate("Nachkaufen")}</small><strong>{formatQuantity(item.suggested_quantity)}</strong><small>{item.quantity_unit_name || translate('Einheiten')}</small></span>
              </button>
            )
          })}
        </div>
        <div className="refill-footer">
          <span><strong>{selectedItems.length}</strong> {translate("ausgewählt")}</span>
          <button className="button primary" type="button" disabled={busy || !selectedItems.length} onClick={generate}>
            {busy ? <LoaderCircle className="spin" /> : <ShoppingBasket />} {translate("Zur Einkaufsliste")}
          </button>
        </div>
      </section>
    </div>
  )
}
