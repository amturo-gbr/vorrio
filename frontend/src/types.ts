export type Screen = 'home' | 'scan' | 'catalog' | 'history' | 'settings' | 'review'
export type ScanMode = 'identify' | 'add' | 'consume' | 'open' | 'shopping'
export type SupportedLocale = 'de' | 'en'

export interface AuthenticatedUser {
  id: string
  display_name: string
  email: string | null
  role: 'owner' | 'admin' | 'member' | 'viewer'
  household_id: string
  household_name: string
  owner_setup_complete: boolean
  preferred_locale: SupportedLocale
}

export interface AuthenticationState {
  authenticated: boolean
  needs_setup: boolean
  needs_owner_setup: boolean
  identifier_required: boolean
  mfa_required?: boolean
  mfa_challenge?: string | null
  mfa_methods?: Array<'totp' | 'recovery_code'>
  user: AuthenticatedUser | null
}

export interface ReleaseNote {
  version: string
  title: string
  summary: string
  highlights: string[]
}

export interface ExperienceState {
  current_version: string
  onboarding_completed: boolean
  onboarding_required: boolean
  last_acknowledged_version: string | null
  release_notes_pending: boolean
  release: ReleaseNote
}

export interface AuthSession {
  id: string
  device_name: string
  created_at: string
  last_seen_at: string
  expires_at: string
  authenticated_at: string
  authentication_method: string
  current: boolean
}

export type ApiTokenScopeId =
  | 'status:read'
  | 'catalog:read'
  | 'stock:read'
  | 'shopping:read'
  | 'shopping:write'
  | 'scans:read'
  | 'scans:write'

export interface ApiTokenScope {
  id: ApiTokenScopeId
  label: string
  description: string
}

export interface ApiToken {
  id: string
  name: string
  token_prefix: string
  scopes: ApiTokenScopeId[]
  expires_at: string
  created_at: string
  last_used_at: string | null
}

export interface ApiTokenCreated extends ApiToken {
  token: string
}

export interface Passkey {
  id: string
  name: string
  device_type: string
  backed_up: boolean
  transports: string[]
  created_at: string
  last_used_at: string | null
}

export interface SecurityState {
  passkeys: Passkey[]
  totp_enabled: boolean
  recovery_codes_remaining: number
  recent_authentication: boolean
  recent_authentication_until: string | null
  secure_context_required: boolean
}

export interface PushDevice {
  id: string
  endpoint_fingerprint: string
  device_name: string
  active: boolean
  failure_count: number
  created_at: string
  updated_at: string
  last_success_at: string | null
  last_failure_at: string | null
}

export interface NotificationPreferences {
  push_enabled: boolean
  low_stock_enabled: boolean
  expiry_enabled: boolean
  expiry_days_before: number
}

export interface NotificationState {
  public_key: string
  secure_context_required: boolean
  preferences: NotificationPreferences
  subscriptions: PushDevice[]
  active_low_stock_events: number
  active_expiry_events: number
  last_checked_at: string | null
}

export interface TotpSetup {
  secret: string
  provisioning_uri: string
  qr_data_uri: string
}

export interface WebAuthnOptions {
  challenge_id: string
  options: Record<string, unknown>
}

export interface HouseholdMember {
  id: string
  display_name: string
  email: string | null
  role: AuthenticatedUser['role']
  active: boolean
  active_session_count: number
  created_at: string
  updated_at: string
}

export interface HouseholdInvitation {
  id: string
  display_name: string
  email: string
  role: Exclude<AuthenticatedUser['role'], 'owner'>
  expires_at: string
  created_at: string
  invite_token?: string | null
}

export interface HouseholdInvitationPublic {
  valid: boolean
  household_name: string
  display_name: string
  email: string
  role: Exclude<AuthenticatedUser['role'], 'owner'>
  expires_at: string
}

export interface ReceiptItem {
  id: string
  raw_name: string
  normalized_name: string | null
  quantity: number
  unit_price: number | null
  total_price: number | null
  barcode: string | null
  brand: string | null
  best_before_date: string | null
  suggested_location: string | null
  suggested_unit: string | null
  suggested_product_group: string | null
  suggested_best_before_days: number | null
  suggestion_confidence: number | null
  catalog_product_id: string | null
  catalog_product_name: string | null
  catalog_variant_id: string | null
  catalog_product_image_url: string | null
  catalog_variant_name: string | null
  catalog_variant_brand: string | null
  catalog_variant_package_amount: number | null
  catalog_variant_package_unit: string | null
  suggested_catalog_product_id: string | null
  suggested_catalog_product_name: string | null
  suggested_catalog_product_score: number | null
  grocy_product_id: number | null
  grocy_product_name: string | null
  match_status: string
  match_score: number | null
  match_reason: string
  match_evidence: Array<{
    source: string
    label: string
    confidence: number
    automatic: boolean
  }>
  suggested_product_id: number | null
  suggested_product_name: string | null
  suggested_product_score: number | null
  imported: number
  import_error?: string | null
}

export interface Receipt {
  id: string
  store_name: string | null
  retailer?: string | null
  store_number?: string | null
  store_address?: string | null
  purchase_date: string | null
  currency: string
  total: number | null
  status: 'review' | 'imported' | 'partial'
  item_count?: number
  imported_count?: number
  review_count: number
  ready_count?: number
  created_at: string
  items?: ReceiptItem[]
  duplicate?: boolean
}

export interface AppStatus {
  grocy_configured: boolean
  grocy_enabled: boolean
  grocy_connected: boolean
  provider_configured: boolean
  provider: string
  version: string
  catalog: {
    products: number
    variants: number
    barcodes: number
    stock_lots: number
  }
}

export interface SettingsData {
  grocy: {
    enabled: boolean
    url: string
    api_key?: string | null
    api_key_configured?: boolean
  }
  provider: {
    type: 'cortecs' | 'openai' | 'openrouter' | 'ollama' | 'openai-compatible' | 'anthropic'
    base_url: string
    model: string
    api_key?: string | null
    api_key_configured?: boolean
  }
  privacy: {
    delete_image_after_analysis: boolean
    retention_days: number
  }
}

export interface RetentionPreview {
  delete_after_analysis: boolean
  retention_days: number
  retained_file_count: number
  retained_bytes: number
  expired_file_count: number
  expired_bytes: number
  cutoff: string
}

export interface ExportPreview {
  household_name: string
  counts: Record<string, number>
  receipt_file_count: number
  receipt_file_bytes: number
  product_image_file_count: number
  product_image_file_bytes: number
  excluded_secret_categories: string[]
}

export interface OperationsAuditEvent {
  id: string
  category: string
  action: string
  outcome: string
  created_at: string
  actor_label: string
}

export interface OperationsOverview {
  database_integrity: string
  database_bytes: number
  counts: {
    active_users: number
    active_sessions: number
    active_api_tokens: number
    active_push_devices: number
    pending_receipts: number
    products: number
    stock_lots: number
    failures_24h: number
  }
  retention: RetentionPreview
  recent_events: OperationsAuditEvent[]
  generated_at: string
}

export interface RetentionRunResult {
  deleted_file_count: number
  deleted_bytes: number
  cleared_receipt_count: number
  rejected_path_count: number
  completed_at: string
}

export interface GrocyProduct {
  id: number
  name: string
}

export interface GrocyMasterItem {
  id: number
  name: string
  description?: string | null
  is_freezer?: number | null
  name_plural?: string | null
  usage_count?: number
  active?: number
  created_at?: string | null
  updated_at?: string | null
}

export interface GrocyMasterData {
  locations: GrocyMasterItem[]
  quantity_units: GrocyMasterItem[]
  product_groups: GrocyMasterItem[]
}

export interface GrocyProductCreateInput {
  name: string
  location_id: number | null
  new_location_name: string | null
  new_location_is_freezer: boolean
  quantity_unit_id: number | null
  new_quantity_unit_name: string | null
  product_group_id: number | null
  new_product_group_name: string | null
  default_best_before_days: number
  remember: boolean
}

export interface CatalogProduct {
  id: string
  name: string
  normalized_name?: string
  product_group_id?: number | null
  product_group_name: string | null
  default_location_id?: number | null
  default_location_name: string | null
  default_quantity_unit_id?: number | null
  default_quantity_unit_name: string | null
  default_best_before_days: number
  minimum_stock_quantity: number
  shopping_target_quantity: number
  image_url: string | null
  variant_count: number
  barcode_count: number
  stock_quantity: number
  grocy_product_id: number | null
}

export interface CatalogBarcode {
  barcode: string
  symbology: string | null
  is_primary: number
  created_at: string
  updated_at: string
}

export interface CatalogVariant {
  id: string
  product_id: string
  name: string | null
  brand: string | null
  package_amount: number | null
  package_unit: string | null
  image_url: string | null
  created_at: string
  updated_at: string
  barcodes: CatalogBarcode[]
  receipt_count: number
  stock_lot_count: number
}

export interface CatalogProductDetail extends CatalogProduct {
  notes: string
  active: number
  created_at: string
  updated_at: string
  variants: CatalogVariant[]
}

export interface CatalogPriceHistoryItem {
  receipt_item_id: string
  receipt_id: string
  purchase_date: string | null
  store_name: string | null
  retailer: string | null
  currency: string
  quantity: number
  unit_price: number | null
  total_price: number | null
  barcode: string | null
  catalog_variant_id: string | null
  variant_name: string | null
  brand: string | null
  package_amount: number | null
  package_unit: string | null
}

export interface PriceStoreSummary {
  store_key: string
  store_name: string
  latest_price: number
  latest_date: string | null
  lowest_price: number
  average_price: number
  observation_count: number
}

export interface PriceProductSummary {
  product_id: string
  product_name: string
  image_url: string | null
  quantity_unit_name: string | null
  currency: string
  observation_count: number
  store_count: number
  latest_price: number
  latest_date: string | null
  latest_store: string
  previous_price: number | null
  lowest_price: number
  highest_price: number
  change_amount: number | null
  change_percent: number | null
  stores: PriceStoreSummary[]
}

export interface PriceInsightsResponse {
  products: PriceProductSummary[]
  product_count: number
  store_count: number
  observation_count: number
  generated_at: string
}

export interface BudgetSettings {
  configured: boolean
  monthly_limit: number | null
  currency: 'EUR'
  warning_percent: number
  updated_at: string | null
}

export interface BudgetCurrentPeriod {
  month: string
  start_date: string
  as_of_date: string
  spent: number
  receipt_count: number
  average_receipt: number
  remaining: number | null
  percent_used: number | null
  forecast: number
  days_elapsed: number
  days_total: number
  days_remaining: number
  daily_available: number | null
  status: 'unconfigured' | 'on_track' | 'watch' | 'over'
  latest_purchase_date: string | null
}

export interface BudgetComparison {
  start_date: string
  end_date: string
  spent: number
  receipt_count: number
  change_amount: number
  change_percent: number | null
}

export interface BudgetMonth {
  month: string
  spent: number
  receipt_count: number
  is_current: boolean
}

export interface BudgetStore {
  store_key: string
  store_name: string
  spent: number
  receipt_count: number
  share_percent: number
}

export interface BudgetDataQuality {
  confirmed_receipt_count: number
  counted_receipt_count: number
  pending_receipt_count: number
  missing_total_count: number
  other_currency_receipt_count: number
  coverage_percent: number
}

export interface BudgetOverviewResponse {
  settings: BudgetSettings
  current_period: BudgetCurrentPeriod
  comparison: BudgetComparison
  months: BudgetMonth[]
  stores: BudgetStore[]
  data_quality: BudgetDataQuality
  generated_at: string
}

export type StockCountSource = 'manual' | 'grocy_review'

export interface StockCountLineInput {
  product_id: string
  variant_id: string | null
  location_id: number | null
  counted_quantity: number
  best_before_date: string | null
  unit_price: number | null
  note: string
}

export interface StockCountLine extends StockCountLineInput {
  id: string
  session_id: string
  product_name: string
  variant_name: string | null
  variant_brand: string | null
  location_name: string | null
  quantity_unit_name: string | null
  previous_quantity: number
  quantity_delta: number
  movement_count: number
  created_at: string
}

export interface StockCountSession {
  id: string
  client_mutation_id: string
  source: StockCountSource
  note: string
  status: 'confirmed'
  line_count: number
  changed_count: number
  created_at: string
  lines: StockCountLine[]
}

export interface GrocyStockPreviewItem {
  product_id: string
  product_name: string
  grocy_product_id: number
  current_quantity: number
  proposed_quantity: number
  quantity_delta: number
  default_location_id: number | null
  default_location_name: string | null
  quantity_unit_name: string | null
  best_before_date: string | null
}

export interface GrocyStockPreview {
  items: GrocyStockPreviewItem[]
  unmapped: Array<{ grocy_product_id: number; product_name: string | null; quantity: number }>
  generated_at: string
}

export interface CatalogProductUpdateInput {
  name: string
  product_group_id: number | null
  default_location_id: number | null
  default_quantity_unit_id: number | null
  default_best_before_days: number
  minimum_stock_quantity: number
  shopping_target_quantity: number
  image_url: string | null
  notes: string
  expected_updated_at: string
}

export interface CatalogVariantInput {
  name: string | null
  brand: string | null
  package_amount: number | null
  package_unit: string | null
  image_url: string | null
}

export type CatalogMasterKind = 'locations' | 'quantity-units' | 'product-groups'

export interface CatalogMasterInput {
  name: string
  description: string
  is_freezer: boolean
  name_plural: string | null
}

export interface ProductCandidate {
  external_id: string
  barcode: string
  name: string
  brand: string | null
  quantity: string | null
  image_url: string | null
  stores: string[]
  source: 'open_facts'
  source_label: string
  source_url: string | null
  database_license: string | null
  image_license: string | null
  attribution: string | null
  score: number
  ai_confidence: number | null
  ai_reason: string | null
  store_match: boolean
  local_product_id: string | null
  local_product_name: string | null
  evidence: Array<{ source: string; label: string }>
}

export interface ProductCandidateSearch {
  query: string
  store_name: string | null
  receipt_unit_price: number | null
  currency: string
  source: 'open_facts'
  cached: boolean
  ai_ranked: boolean
  candidates: ProductCandidate[]
  warnings: string[]
}

export interface ProductCandidateConfirmInput {
  source: 'open_facts'
  external_id: string
  product_id: string | null
  name: string | null
  location_id: number | null
  new_location_name: string | null
  new_location_is_freezer: boolean
  quantity_unit_id: number | null
  new_quantity_unit_name: string | null
  product_group_id: number | null
  new_product_group_name: string | null
  default_best_before_days: number
  remember: boolean
}

export interface CatalogProductCreateInput {
  name: string
  location_id: number | null
  new_location_name: string | null
  new_location_is_freezer: boolean
  quantity_unit_id: number | null
  new_quantity_unit_name: string | null
  product_group_id: number | null
  new_product_group_name: string | null
  default_best_before_days: number
  minimum_stock_quantity: number
  shopping_target_quantity: number
  brand: string | null
  barcode: string | null
  remember: boolean
}

export interface ShoppingListItem {
  id: string
  product_id: string | null
  product_name: string | null
  product_image_url: string | null
  label: string
  desired_quantity: number
  checked: number
  notes: string
  quantity_unit_name: string | null
  stock_quantity: number
  minimum_stock_quantity: number
  shopping_target_quantity: number
  created_at: string
  updated_at: string
}

export interface ShoppingLowStockItem {
  product_id: string
  product_name: string
  product_image_url: string | null
  current_quantity: number
  minimum_quantity: number
  target_quantity: number
  suggested_quantity: number
  quantity_unit_name: string | null
  existing_item_id: string | null
  existing_desired_quantity: number | null
}

export interface ShoppingLowStockResponse {
  items: ShoppingLowStockItem[]
  generated_at: string
}

export interface ShoppingGeneration {
  id: string
  client_mutation_id: string
  requested_count: number
  created_count: number
  updated_count: number
  unchanged_count: number
  skipped_count: number
  created_at: string
  items: Array<{
    id: string
    run_id: string
    product_id: string
    product_name: string
    shopping_item_id: string | null
    current_quantity: number
    minimum_quantity: number
    target_quantity: number
    suggested_quantity: number
    quantity_unit_name: string | null
    action: 'created' | 'updated' | 'unchanged' | 'skipped'
    created_at: string
  }>
}

export interface ScanDraft {
  id: string
  barcode_raw: string
  barcode_normalized: string
  symbology: string | null
  mode: ScanMode
  status: 'resolved' | 'unresolved' | 'confirmed' | 'discarded'
  resolution_source: 'local' | 'cache' | 'open_facts' | 'unresolved'
  product_id: string | null
  variant_id: string | null
  product_name: string | null
  product_image_url: string | null
  default_location_id: number | null
  default_location_name: string | null
  default_quantity_unit_id: number | null
  default_quantity_unit_name: string | null
  brand: string | null
  variant_name: string | null
  package_amount: number | null
  package_unit: string | null
  stock_quantity: number
  suggestion: {
    name?: string | null
    brand?: string | null
    quantity?: string | null
    image_url?: string | null
    categories?: string | null
    product_type?: string | null
    source?: string | null
    source_url?: string | null
    attribution?: string | null
    database_license?: string | null
  } | null
  upstream_error: string | null
  action_result: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ScanConfirmInput {
  client_mutation_id: string
  product_id?: string | null
  name?: string | null
  brand?: string | null
  variant_name?: string | null
  package_amount?: number | null
  package_unit?: string | null
  image_url?: string | null
  location_id?: number | null
  quantity_unit_id?: number | null
  product_group_id?: number | null
  default_best_before_days?: number
  quantity: number
  best_before_date?: string | null
  unit_price?: number | null
}
