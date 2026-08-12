import {
  Archive,
  Barcode,
  Camera,
  Check,
  ChevronRight,
  CirclePlus,
  ClipboardCheck,
  Database,
  LoaderCircle,
  ImageUp,
  MapPin,
  PackageCheck,
  PackagePlus,
  PackageSearch,
  Pencil,
  Save,
  Search,
  Snowflake,
  Tags,
  Trash2,
  Weight,
  X,
} from 'lucide-react'
import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../../api'
import type {
  CatalogMasterInput,
  CatalogMasterKind,
  CatalogProduct,
  CatalogProductCreateInput,
  CatalogProductDetail,
  CatalogProductUpdateInput,
  CatalogVariant,
  CatalogVariantInput,
  GrocyMasterData,
  GrocyMasterItem,
  AuthenticatedUser,
} from '../../types'
import { StockCountSheet } from './StockCountSheet'
import { formatNumber, translate } from '../../i18n'

const formatQuantity = (value: number) => formatNumber(value)

const countLabel = (value: number, singular: string, plural: string) =>
  `${formatNumber(value)} ${translate(value === 1 ? singular : plural)}`

const emptyVariant: CatalogVariantInput = {
  name: null,
  brand: null,
  package_amount: null,
  package_unit: null,
  image_url: null,
}

const emptyMaster: CatalogMasterInput = {
  name: '',
  description: '',
  is_freezer: false,
  name_plural: null,
}

type Notice = (kind: 'success' | 'error', text: string) => void

export function CatalogScreen({ onNotice, grocyEnabled, role }: { onNotice: Notice; grocyEnabled: boolean; role: AuthenticatedUser['role'] }) {
  const [products, setProducts] = useState<CatalogProduct[]>([])
  const [query, setQuery] = useState('')
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<CatalogProductDetail | null>(null)
  const [masterData, setMasterData] = useState<GrocyMasterData | null>(null)
  const [masterOpen, setMasterOpen] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [stockCountOpen, setStockCountOpen] = useState(false)
  const canManageCatalog = role === 'owner' || role === 'admin'
  const canCountStock = role !== 'viewer'

  const loadProducts = async (nextQuery = query) => {
    setBusy(true)
    try {
      setProducts(await api.catalogProducts(nextQuery))
      setError('')
    } catch (nextError) {
      setError((nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const loadMasterData = async () => {
    const master = await api.catalogMasterData()
    setMasterData(master)
    return master
  }

  useEffect(() => {
    const timer = window.setTimeout(() => loadProducts(query), 180)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query])

  const openProduct = async (productId: string) => {
    setBusy(true)
    try {
      const [product] = await Promise.all([
        api.catalogProduct(productId),
        masterData ? Promise.resolve(masterData) : loadMasterData(),
      ])
      setSelected(product)
    } catch (nextError) {
      onNotice('error', (nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const productUpdated = async (product: CatalogProductDetail, message?: string) => {
    setSelected(product)
    await loadProducts()
    if (message) onNotice('success', message)
  }

  const openMasterData = async () => {
    setBusy(true)
    try {
      await loadMasterData()
      setMasterOpen(true)
    } catch (nextError) {
      onNotice('error', (nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const openCreateProduct = async () => {
    setBusy(true)
    try {
      await (masterData ? Promise.resolve(masterData) : loadMasterData())
      setCreateOpen(true)
    } catch (nextError) {
      onNotice('error', (nextError as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen simple-screen catalog-screen">
      <header className="page-header catalog-page-header">
        <div><h1>{translate("Vorrat")}</h1><p>{translate("Produkte, Packungen und Stammdaten an einem Ort.")}</p></div>
        <div className="catalog-header-actions">
          {canCountStock && <button className="button tertiary compact" type="button" onClick={() => setStockCountOpen(true)}><ClipboardCheck /> {translate("Zählen")}</button>}
          {canManageCatalog && <button className="button tertiary compact" type="button" onClick={openCreateProduct}><CirclePlus /> {translate("Produkt")}</button>}
          {canManageCatalog && <button className="button tertiary compact" type="button" onClick={openMasterData}><Database /> {translate("Stammdaten")}</button>}
        </div>
      </header>
      <label className="search-field catalog-search"><Search /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={translate("Produkt suchen")} /></label>
      {error && <p className="field-error" role="alert">{error}</p>}
      {busy ? (
        <div className="inline-loading"><LoaderCircle className="spin" /> {translate("Produkte laden…")}</div>
      ) : products.length ? (
        <div className="catalog-list">
          {products.map((product) => {
            const content = <>
              <span className="catalog-icon">
                {product.image_url ? <img src={product.image_url} alt="" onError={(event) => { event.currentTarget.hidden = true }} /> : <PackageCheck />}
              </span>
              <span className="catalog-copy">
                <strong>{product.name}</strong>
                <small>{[product.product_group_name, product.default_location_name].filter(Boolean).join(' · ') || translate('Stammdaten noch offen')}</small>
                {(product.variant_count > 0 || product.barcode_count > 0) && <em>{countLabel(product.variant_count, 'Variante', 'Varianten')} · {countLabel(product.barcode_count, 'Barcode', 'Barcodes')}</em>}
              </span>
              <span className="catalog-stock"><strong>{formatQuantity(product.stock_quantity)}</strong><small>{product.default_quantity_unit_name || translate('Einheiten')}</small></span>
              {canManageCatalog && <ChevronRight />}
            </>
            return canManageCatalog
              ? <button className="catalog-row catalog-row-button" key={product.id} onClick={() => openProduct(product.id)}>{content}</button>
              : <article className="catalog-row catalog-row-readonly" key={product.id}>{content}</article>
          })}
        </div>
      ) : (
        <div className="empty-page"><PackageSearch /><h2>{translate("Keine Produkte gefunden")}</h2><p>{translate(grocyEnabled ? 'Lege dein erstes Produkt an, übernimm den Grocy-Katalog oder ordne Artikel beim nächsten Bon zu.' : 'Lege dein erstes Produkt an oder ordne Artikel beim nächsten Bon zu.')}</p></div>
      )}

      {selected && masterData && (
        <ProductEditor
          product={selected}
          masterData={masterData}
          onClose={() => setSelected(null)}
          onUpdated={productUpdated}
          onNotice={onNotice}
        />
      )}

      {masterOpen && masterData && (
        <MasterDataManager
          data={masterData}
          onClose={() => setMasterOpen(false)}
          onChanged={async () => {
            await loadMasterData()
            await loadProducts()
          }}
          onNotice={onNotice}
        />
      )}

      {createOpen && masterData && (
        <CreateProductSheet
          masterData={masterData}
          onClose={() => setCreateOpen(false)}
          onCreated={async (product) => {
            setCreateOpen(false)
            setSelected(product)
            await loadProducts()
            onNotice('success', translate('Produkt wurde angelegt und kann jetzt ergänzt werden.'))
          }}
          onNotice={onNotice}
        />
      )}

      {stockCountOpen && (
        <StockCountSheet
          grocyEnabled={grocyEnabled}
          onClose={() => setStockCountOpen(false)}
          onCommitted={async () => {
            await loadProducts()
            onNotice('success', translate('Bestandszählung wurde übernommen.'))
          }}
          onNotice={onNotice}
        />
      )}
    </div>
  )
}

function CreateProductSheet({ masterData, onClose, onCreated, onNotice }: { masterData: GrocyMasterData; onClose: () => void; onCreated: (product: CatalogProductDetail) => Promise<void>; onNotice: Notice }) {
  const [draft, setDraft] = useState<CatalogProductCreateInput>({
    name: '',
    location_id: masterData.locations.find((row) => row.name === 'Vorratskammer')?.id ?? masterData.locations[0]?.id ?? null,
    new_location_name: null,
    new_location_is_freezer: false,
    quantity_unit_id: masterData.quantity_units.find((row) => row.name === 'Packung')?.id ?? masterData.quantity_units[0]?.id ?? null,
    new_quantity_unit_name: null,
    product_group_id: null,
    new_product_group_name: null,
    default_best_before_days: 0,
    minimum_stock_quantity: 0,
    shopping_target_quantity: 0,
    brand: null,
    barcode: null,
    remember: true,
  })
  const [busy, setBusy] = useState(false)
  const invalidRule = draft.shopping_target_quantity > 0 && draft.shopping_target_quantity <= draft.minimum_stock_quantity

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    try {
      await onCreated(await api.createCatalogProduct(draft))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="sheet-backdrop" role="presentation">
      <section className="product-sheet create-product-sheet" role="dialog" aria-modal="true" aria-label={translate("Produkt anlegen")}>
        <span className="sheet-handle" />
        <header><div><h2>{translate("Produkt anlegen")}</h2><p>{translate("Erst das Haushaltsprodukt, Packungen danach")}</p></div><button type="button" className="icon-close" onClick={onClose} aria-label={translate("Produktanlage schließen")}><X /></button></header>
        <form className="catalog-product-form" onSubmit={submit}>
          <label>{translate("Produktname")}<input autoFocus required value={draft.name} placeholder={translate("z. B. Milch")} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></label>
          <div className="catalog-form-grid">
            <label>{translate("Lagerort")}<select value={draft.location_id ?? ''} onChange={(event) => setDraft({ ...draft, location_id: event.target.value ? Number(event.target.value) : null })}><option value="">{translate("Kein Standard")}</option>{masterData.locations.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            <label>{translate("Einheit")}<select value={draft.quantity_unit_id ?? ''} onChange={(event) => setDraft({ ...draft, quantity_unit_id: event.target.value ? Number(event.target.value) : null })}><option value="">{translate("Keine Einheit")}</option>{masterData.quantity_units.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            <label>{translate("Produktgruppe")}<select value={draft.product_group_id ?? ''} onChange={(event) => setDraft({ ...draft, product_group_id: event.target.value ? Number(event.target.value) : null })}><option value="">{translate("Keine Gruppe")}</option>{masterData.product_groups.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            <label>{translate("Standard-Haltbarkeit")}<input type="number" min="0" max="3650" value={draft.default_best_before_days} onChange={(event) => setDraft({ ...draft, default_best_before_days: Number(event.target.value) })} /></label>
          </div>
          <div className="reorder-rule-editor">
            <div><strong>{translate("Automatisch nachkaufen")}</strong><small>{translate("Vorschlag anzeigen, sobald der Bestand knapp wird.")}</small></div>
            <label>{translate("Mindestbestand")}<input type="number" min="0" step="any" value={draft.minimum_stock_quantity} onChange={(event) => setDraft({ ...draft, minimum_stock_quantity: Number(event.target.value) })} /></label>
            <label>{translate("Auffüllen bis")}<input type="number" min="0" step="any" value={draft.shopping_target_quantity} onChange={(event) => setDraft({ ...draft, shopping_target_quantity: Number(event.target.value) })} /></label>
            <p className={invalidRule ? 'field-error' : ''}>{translate(invalidRule ? 'Das Auffüllziel muss größer als der Mindestbestand sein.' : 'Auffüllen bis 0 lässt die Regel deaktiviert.')}</p>
          </div>
          <p className="create-helper">{translate("Marke, Packungsgröße, Bild und Barcode ergänzt du anschließend als konkrete Variante.")}</p>
          <button className="button primary full" disabled={busy || !draft.name.trim() || invalidRule}>{busy ? <LoaderCircle className="spin" /> : <PackagePlus />} {translate("Produkt anlegen")}</button>
        </form>
      </section>
    </div>
  )
}

function ProductEditor({
  product,
  masterData,
  onClose,
  onUpdated,
  onNotice,
}: {
  product: CatalogProductDetail
  masterData: GrocyMasterData
  onClose: () => void
  onUpdated: (product: CatalogProductDetail, message?: string) => Promise<void>
  onNotice: Notice
}) {
  const [form, setForm] = useState<CatalogProductUpdateInput>(() => productForm(product))
  const [busy, setBusy] = useState(false)
  const [imageBusy, setImageBusy] = useState(false)
  const [showNewVariant, setShowNewVariant] = useState(false)
  const cameraInput = useRef<HTMLInputElement>(null)
  const uploadInput = useRef<HTMLInputElement>(null)
  const preservedDraft = useRef<CatalogProductUpdateInput | null>(null)
  const invalidRule = form.shopping_target_quantity > 0 && form.shopping_target_quantity <= form.minimum_stock_quantity
  const managedImage = Boolean(form.image_url?.startsWith(`/api/v1/catalog/products/${product.id}/image`))

  useEffect(() => {
    setForm(preservedDraft.current || productForm(product))
    preservedDraft.current = null
  }, [product])

  const save = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    try {
      const updated = await api.updateCatalogProduct(product.id, form)
      await onUpdated(updated, translate('Produkt wurde gespeichert.'))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const uploadImage = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setImageBusy(true)
    try {
      const updated = await api.uploadCatalogProductImage(product.id, file)
      preservedDraft.current = {
        ...form,
        image_url: updated.image_url,
        expected_updated_at: updated.updated_at,
      }
      await onUpdated(updated, translate('Dein Produktbild wurde lokal gespeichert.'))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setImageBusy(false)
    }
  }

  const removeImage = async () => {
    setImageBusy(true)
    try {
      const updated = await api.deleteCatalogProductImage(product.id)
      preservedDraft.current = {
        ...form,
        image_url: null,
        expected_updated_at: updated.updated_at,
      }
      await onUpdated(updated, translate('Produktbild wurde entfernt.'))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setImageBusy(false)
    }
  }

  return (
    <div className="sheet-backdrop" role="presentation">
      <section className="product-sheet catalog-editor-sheet" role="dialog" aria-modal="true" aria-label={translate("Produkt bearbeiten")}>
        <span className="sheet-handle" />
        <header>
          <div><h2>{translate("Produkt bearbeiten")}</h2><p>{translate("Allgemeine Daten und konkrete Packungen")}</p></div>
          <button type="button" className="icon-close" onClick={onClose} aria-label={translate("Produkt schließen")}><X /></button>
        </header>

        <form className="catalog-product-form" onSubmit={save}>
          <div className="catalog-product-hero">
            <span className="catalog-product-image">
              {form.image_url ? <img src={form.image_url} alt="" onError={(event) => { event.currentTarget.hidden = true }} /> : <PackageCheck />}
            </span>
            <label>{translate("Produktname")}<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          </div>
          <div className="catalog-form-grid">
            <label>{translate("Lagerort")}<select value={form.default_location_id ?? ''} onChange={(event) => setForm({ ...form, default_location_id: event.target.value ? Number(event.target.value) : null })}><option value="">{translate("Kein Standard")}</option>{masterData.locations.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            <label>{translate("Einheit")}<select value={form.default_quantity_unit_id ?? ''} onChange={(event) => setForm({ ...form, default_quantity_unit_id: event.target.value ? Number(event.target.value) : null })}><option value="">{translate("Keine Einheit")}</option>{masterData.quantity_units.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            <label>{translate("Produktgruppe")}<select value={form.product_group_id ?? ''} onChange={(event) => setForm({ ...form, product_group_id: event.target.value ? Number(event.target.value) : null })}><option value="">{translate("Keine Gruppe")}</option>{masterData.product_groups.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            <label>{translate("Standard-Haltbarkeit")}<input type="number" min="0" max="3650" value={form.default_best_before_days} onChange={(event) => setForm({ ...form, default_best_before_days: Number(event.target.value) })} /><small>{translate("Tage ab Einkauf, 0 = unbekannt")}</small></label>
          </div>
          <section className="product-image-editor" aria-labelledby="product-image-heading">
            <div>
              <strong id="product-image-heading">{translate("Produktbild")}</strong>
              <small>{translate(managedImage ? 'Eigenes Bild · privat in Vorrio gespeichert' : form.image_url ? 'Bild von einer externen Adresse' : 'Noch kein Produktbild gewählt')}</small>
            </div>
            <div className="product-image-actions">
              <button type="button" className="button tertiary compact" onClick={() => cameraInput.current?.click()} disabled={imageBusy}>{imageBusy ? <LoaderCircle className="spin" /> : <Camera />} {translate("Foto aufnehmen")}</button>
              <button type="button" className="button tertiary compact" onClick={() => uploadInput.current?.click()} disabled={imageBusy}><ImageUp /> {translate("Bild hochladen")}</button>
              {form.image_url && <button type="button" className="button quiet compact image-remove" onClick={removeImage} disabled={imageBusy}><Trash2 /> {translate("Entfernen")}</button>}
            </div>
            <input ref={cameraInput} className="visually-hidden-file" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={uploadImage} />
            <input ref={uploadInput} className="visually-hidden-file" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" onChange={uploadImage} />
            <details className="external-image-url">
              <summary>{translate("Stattdessen externe Bildadresse verwenden")}</summary>
              <label>{translate("Bildadresse")}<input inputMode="url" value={managedImage ? '' : form.image_url || ''} placeholder={translate("https://…")} onChange={(event) => setForm({ ...form, image_url: event.target.value || null })} /></label>
              <small>{translate("Die Adresse wird erst mit „Produkt speichern“ übernommen. Eigene Uploads ersetzen sie sofort.")}</small>
            </details>
          </section>
          <div className="reorder-rule-editor">
            <div><strong>{translate("Automatisch nachkaufen")}</strong><small>{translate("Wenn der Bestand das Minimum erreicht, schlägt Vorrio die Menge bis zum Ziel vor.")}</small></div>
            <label>{translate("Mindestbestand")}<input type="number" min="0" step="any" value={form.minimum_stock_quantity} onChange={(event) => setForm({ ...form, minimum_stock_quantity: Number(event.target.value) })} /></label>
            <label>{translate("Auffüllen bis")}<input type="number" min="0" step="any" value={form.shopping_target_quantity} onChange={(event) => setForm({ ...form, shopping_target_quantity: Number(event.target.value) })} /></label>
            <p className={invalidRule ? 'field-error' : ''}>{translate(invalidRule ? 'Das Auffüllziel muss größer als der Mindestbestand sein.' : 'Auffüllen bis 0 deaktiviert die Regel. Änderungen landen nie ungeprüft auf der Liste.')}</p>
          </div>
          <label>{translate("Notizen")}<textarea rows={3} value={form.notes} placeholder={translate("Optional für den Haushalt")} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>
          <button className="button primary full" disabled={busy || invalidRule}>{busy ? <LoaderCircle className="spin" /> : <Save />} {translate("Produkt speichern")}</button>
        </form>

        <section className="variant-section">
          <div className="section-heading compact-heading">
            <div><h3>{translate("Packungen & Barcodes")}</h3><p>{translate("Marken und Größen gehören als Variante zum Produkt.")}</p></div>
            <button type="button" className="button tertiary compact" onClick={() => setShowNewVariant(!showNewVariant)}><CirclePlus /> {translate("Variante")}</button>
          </div>
          {showNewVariant && (
            <NewVariantForm
              productId={product.id}
              onCancel={() => setShowNewVariant(false)}
              onCreated={async (updated) => {
                setShowNewVariant(false)
                await onUpdated(updated, translate('Variante wurde angelegt.'))
              }}
              onNotice={onNotice}
            />
          )}
          <div className="variant-list">
            {product.variants.map((variant) => (
              <VariantEditor key={variant.id} variant={variant} onUpdated={onUpdated} onNotice={onNotice} />
            ))}
            {!product.variants.length && <p className="empty-inline">{translate("Noch keine konkrete Packung. Das allgemeine Produkt funktioniert trotzdem.")}</p>}
          </div>
        </section>
      </section>
    </div>
  )
}

function productForm(product: CatalogProductDetail): CatalogProductUpdateInput {
  return {
    name: product.name,
    product_group_id: product.product_group_id ?? null,
    default_location_id: product.default_location_id ?? null,
    default_quantity_unit_id: product.default_quantity_unit_id ?? null,
    default_best_before_days: product.default_best_before_days,
    minimum_stock_quantity: product.minimum_stock_quantity,
    shopping_target_quantity: product.shopping_target_quantity,
    image_url: product.image_url,
    notes: product.notes,
    expected_updated_at: product.updated_at,
  }
}

function NewVariantForm({ productId, onCancel, onCreated, onNotice }: { productId: string; onCancel: () => void; onCreated: (product: CatalogProductDetail) => Promise<void>; onNotice: Notice }) {
  const [draft, setDraft] = useState<CatalogVariantInput>(emptyVariant)
  const [busy, setBusy] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    try {
      await onCreated(await api.createCatalogVariant(productId, draft))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="variant-editor new-variant" onSubmit={submit}>
      <strong>{translate("Neue Variante")}</strong>
      <VariantFields value={draft} onChange={setDraft} />
      <div className="row-actions"><button type="button" className="button tertiary compact" onClick={onCancel}>{translate("Abbrechen")}</button><button className="button primary compact" disabled={busy}>{busy ? <LoaderCircle className="spin" /> : <PackagePlus />} {translate("Anlegen")}</button></div>
    </form>
  )
}

function VariantEditor({ variant, onUpdated, onNotice }: { variant: CatalogVariant; onUpdated: (product: CatalogProductDetail, message?: string) => Promise<void>; onNotice: Notice }) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<CatalogVariantInput>(() => variantForm(variant))
  const [barcode, setBarcode] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => setDraft(variantForm(variant)), [variant])

  const execute = async (operation: () => Promise<CatalogProductDetail>, message: string) => {
    setBusy(true)
    try {
      await onUpdated(await operation(), message)
      setBarcode('')
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className={`variant-editor ${open ? 'open' : ''}`}>
      <button type="button" className="variant-summary" onClick={() => setOpen(!open)}>
        <span className="variant-image">{variant.image_url ? <img src={variant.image_url} alt="" onError={(event) => { event.currentTarget.hidden = true }} /> : <Barcode />}</span>
        <span><strong>{variant.brand || variant.name || translate('Unbenannte Variante')}</strong><small>{[variant.name !== variant.brand ? variant.name : null, variant.package_amount && variant.package_unit ? `${formatQuantity(variant.package_amount)} ${variant.package_unit}` : null].filter(Boolean).join(' · ') || translate('Packungsdaten offen')}</small><em>{countLabel(variant.barcodes.length, 'Barcode', 'Barcodes')} · {countLabel(variant.receipt_count, 'Bon', 'Bons')}</em></span>
        <Pencil />
      </button>
      {open && (
        <div className="variant-body">
          <VariantFields value={draft} onChange={setDraft} />
          <div className="barcode-manager">
            <strong>{translate("Barcodes")}</strong>
            {variant.barcodes.map((entry) => <span className="barcode-chip" key={entry.barcode}><span><b>{entry.barcode}</b><small>{entry.symbology || 'Code'}</small></span><button type="button" aria-label={translate('Barcode {{barcode}} entfernen', { barcode: entry.barcode })} onClick={() => execute(() => api.deleteCatalogBarcode(variant.id, entry.barcode), translate('Barcode wurde entfernt.'))} disabled={busy}><X /></button></span>)}
            <div className="barcode-add"><input value={barcode} inputMode="numeric" placeholder={translate("Barcode scannen oder eingeben")} onChange={(event) => setBarcode(event.target.value)} /><button type="button" className="button tertiary compact" disabled={busy || barcode.trim().length < 4} onClick={() => execute(() => api.createCatalogBarcode(variant.id, barcode), translate('Barcode wurde gespeichert.'))}><CirclePlus /> {translate("Hinzufügen")}</button></div>
          </div>
          <div className="row-actions variant-actions">
            <button type="button" className={`button ${confirmDelete ? 'danger' : 'ghost-danger'} compact`} disabled={busy || variant.receipt_count > 0 || variant.stock_lot_count > 0} onClick={() => confirmDelete ? execute(() => api.deleteCatalogVariant(variant.id), translate('Variante wurde gelöscht.')) : setConfirmDelete(true)}><Trash2 /> {translate(confirmDelete ? 'Wirklich löschen' : 'Variante löschen')}</button>
            <button type="button" className="button primary compact" disabled={busy} onClick={() => execute(() => api.updateCatalogVariant(variant.id, { ...draft, expected_updated_at: variant.updated_at }), translate('Variante wurde gespeichert.'))}><Check /> {translate("Speichern")}</button>
          </div>
          {(variant.receipt_count > 0 || variant.stock_lot_count > 0) && <p className="protected-note">{translate("Diese Variante bleibt geschützt, weil Bons oder Bestände darauf verweisen.")}</p>}
        </div>
      )}
    </article>
  )
}

function variantForm(variant: CatalogVariant): CatalogVariantInput {
  return {
    name: variant.name,
    brand: variant.brand,
    package_amount: variant.package_amount,
    package_unit: variant.package_unit,
    image_url: variant.image_url,
  }
}

function VariantFields({ value, onChange }: { value: CatalogVariantInput; onChange: (value: CatalogVariantInput) => void }) {
  return (
    <div className="catalog-form-grid variant-fields">
      <label>{translate("Marke")}<input value={value.brand || ''} onChange={(event) => onChange({ ...value, brand: event.target.value || null })} /></label>
      <label>{translate("Variantenname")}<input value={value.name || ''} placeholder={translate("z. B. Barista")} onChange={(event) => onChange({ ...value, name: event.target.value || null })} /></label>
      <label>{translate("Menge")}<input type="number" min="0" step="0.01" value={value.package_amount ?? ''} onChange={(event) => onChange({ ...value, package_amount: event.target.value ? Number(event.target.value) : null })} /></label>
      <label>{translate("Packungseinheit")}<input value={value.package_unit || ''} placeholder={translate("ml, g, Stück …")} onChange={(event) => onChange({ ...value, package_unit: event.target.value || null })} /></label>
      <label className="wide-field">{translate("Bild-URL")}<input inputMode="url" value={value.image_url || ''} placeholder={translate("https://…")} onChange={(event) => onChange({ ...value, image_url: event.target.value || null })} /></label>
    </div>
  )
}

const masterDefinitions: Array<{ kind: CatalogMasterKind; key: keyof GrocyMasterData; label: string; singular: string; icon: typeof MapPin }> = [
  { kind: 'locations', key: 'locations', label: 'Lagerorte', singular: 'Lagerort', icon: MapPin },
  { kind: 'quantity-units', key: 'quantity_units', label: 'Einheiten', singular: 'Einheit', icon: Weight },
  { kind: 'product-groups', key: 'product_groups', label: 'Gruppen', singular: 'Gruppe', icon: Tags },
]

function MasterDataManager({ data, onClose, onChanged, onNotice }: { data: GrocyMasterData; onClose: () => void; onChanged: () => Promise<void>; onNotice: Notice }) {
  const [kind, setKind] = useState<CatalogMasterKind>('locations')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [draft, setDraft] = useState<CatalogMasterInput>(emptyMaster)
  const [busy, setBusy] = useState(false)
  const [confirmArchive, setConfirmArchive] = useState(false)
  const definition = masterDefinitions.find((entry) => entry.kind === kind) || masterDefinitions[0]
  const MasterIcon = definition.icon
  const rows = data[definition.key]
  const selected = useMemo(() => rows.find((row) => row.id === selectedId) || null, [rows, selectedId])

  const select = (row: GrocyMasterItem | null) => {
    setSelectedId(row?.id ?? null)
    setDraft(row ? {
      name: row.name,
      description: row.description || '',
      is_freezer: Boolean(row.is_freezer),
      name_plural: row.name_plural || null,
    } : emptyMaster)
    setConfirmArchive(false)
  }

  useEffect(() => select(null), [kind])

  const save = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    try {
      if (selected) {
        await api.updateCatalogMaster(kind, selected.id, { ...draft, expected_updated_at: selected.updated_at || '' })
        onNotice('success', translate('{{type}} wurde gespeichert.', { type: translate(definition.singular) }))
      } else {
        await api.createCatalogMaster(kind, draft)
        onNotice('success', translate('{{type}} wurde angelegt.', { type: translate(definition.singular) }))
      }
      await onChanged()
      select(null)
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const archive = async () => {
    if (!selected) return
    if (!confirmArchive) {
      setConfirmArchive(true)
      return
    }
    setBusy(true)
    try {
      await api.archiveCatalogMaster(kind, selected.id)
      await onChanged()
      select(null)
      onNotice('success', translate('Eintrag wurde archiviert.'))
    } catch (error) {
      onNotice('error', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="sheet-backdrop" role="presentation">
      <section className="product-sheet master-data-sheet" role="dialog" aria-modal="true" aria-label={translate("Stammdaten verwalten")}>
        <span className="sheet-handle" />
        <header><div><h2>{translate("Stammdaten")}</h2><p>{translate("Umbenennen, ergänzen und sauber zuordnen")}</p></div><button type="button" className="icon-close" onClick={onClose} aria-label={translate("Stammdaten schließen")}><X /></button></header>
        <nav className="master-tabs" aria-label={translate("Stammdatentyp")}>
          {masterDefinitions.map(({ kind: tabKind, label, icon: Icon }) => <button type="button" className={kind === tabKind ? 'selected' : ''} key={tabKind} onClick={() => setKind(tabKind)}><Icon /> {translate(label)}</button>)}
        </nav>
        <div className="master-data-workspace">
          <div className="master-data-list">
            <button type="button" className={!selected ? 'selected new-master-row' : 'new-master-row'} onClick={() => select(null)}><CirclePlus /><span><strong>{translate("Neu anlegen")}</strong><small>{translate(definition.singular)}</small></span></button>
            {rows.map((row) => <button type="button" className={selected?.id === row.id ? 'selected' : ''} key={row.id} onClick={() => select(row)}><span className="master-type-icon">{kind === 'locations' && row.is_freezer ? <Snowflake /> : <MasterIcon />}</span><span><strong>{row.name}</strong><small>{countLabel(row.usage_count || 0, 'Produkt', 'Produkte')}</small></span><ChevronRight /></button>)}
          </div>
          <form className="master-data-form" onSubmit={save}>
            <div className="section-heading compact-heading"><div><h3>{selected ? translate('{{name}} bearbeiten', { name: selected.name }) : translate('{{type}} anlegen', { type: translate(definition.singular) })}</h3><p>{translate("Änderungen gelten sofort überall in Vorrio.")}</p></div></div>
            <label>{translate("Name")}<input required value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></label>
            {kind === 'quantity-units' && <label>{translate("Mehrzahl")}<input value={draft.name_plural || ''} placeholder={translate("z. B. Flaschen")} onChange={(event) => setDraft({ ...draft, name_plural: event.target.value || null })} /></label>}
            <label>{translate("Beschreibung")}<textarea rows={3} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></label>
            {kind === 'locations' && <label className="toggle-row"><span><strong>{translate("Gefrierstandort")}</strong><small>{translate("Für Tiefkühlware und Temperaturhinweise.")}</small></span><input type="checkbox" checked={draft.is_freezer} onChange={(event) => setDraft({ ...draft, is_freezer: event.target.checked })} /></label>}
            <button className="button primary full" disabled={busy || !draft.name.trim()}>{busy ? <LoaderCircle className="spin" /> : <Save />} {translate(selected ? 'Änderungen speichern' : 'Eintrag anlegen')}</button>
            {selected && <button type="button" className={`button ${confirmArchive ? 'danger' : 'ghost-danger'} full`} disabled={busy || Boolean(selected.usage_count)} onClick={archive}><Archive /> {translate(confirmArchive ? 'Wirklich archivieren' : 'Eintrag archivieren')}</button>}
            {selected && Boolean(selected.usage_count) && <p className="protected-note">{translate('Wird noch von {{count}} Produkten verwendet. Ordne diese Produkte zuerst neu zu.', { count: selected.usage_count || 0 })}</p>}
          </form>
        </div>
      </section>
    </div>
  )
}
