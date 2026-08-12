import type {
  AppStatus,
  AuthenticationState,
  ExperienceState,
  AuthSession,
  ApiToken,
  ApiTokenCreated,
  ApiTokenScope,
  ApiTokenScopeId,
  Passkey,
  SecurityState,
  TotpSetup,
  WebAuthnOptions,
  HouseholdInvitation,
  HouseholdInvitationPublic,
  HouseholdMember,
  CatalogMasterInput,
  CatalogMasterKind,
  CatalogProduct,
  CatalogProductCreateInput,
  CatalogProductDetail,
  CatalogProductUpdateInput,
  CatalogVariantInput,
  GrocyMasterItem,
  ProductCandidateConfirmInput,
  ProductCandidateSearch,
  GrocyMasterData,
  Receipt,
  ScanConfirmInput,
  ScanDraft,
  ScanMode,
  SettingsData,
  StockCountLineInput,
  StockCountSession,
  StockCountSource,
  GrocyStockPreview,
  ShoppingGeneration,
  ShoppingListItem,
  ShoppingLowStockResponse,
  CatalogPriceHistoryItem,
  PriceInsightsResponse,
  BudgetOverviewResponse,
  BudgetSettings,
  NotificationPreferences,
  NotificationState,
  PushDevice,
  ExportPreview,
  OperationsOverview,
  RetentionPreview,
  RetentionRunResult,
} from './types'
import { apiErrorMessage } from './apiError'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export class ApiNetworkError extends Error {
  constructor(message = 'Vorrio ist gerade nicht erreichbar.') {
    super(message)
    this.name = 'ApiNetworkError'
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  let response: Response
  try {
    response = await fetch(path, {
      ...options,
      headers,
      credentials: 'same-origin',
    })
  } catch {
    throw new ApiNetworkError()
  }
  const payload = response.headers.get('content-type')?.includes('application/json')
    ? await response.json()
    : null
  if (!response.ok) {
    throw new ApiError(apiErrorMessage(payload, response.status), response.status)
  }
  return payload as T
}

async function download(path: string): Promise<{ blob: Blob; filename: string }> {
  let response: Response
  try {
    response = await fetch(path, { credentials: 'same-origin' })
  } catch {
    throw new ApiNetworkError()
  }
  if (!response.ok) {
    const payload = response.headers.get('content-type')?.includes('application/json')
      ? await response.json()
      : null
    throw new ApiError(apiErrorMessage(payload, response.status), response.status)
  }
  const disposition = response.headers.get('content-disposition') || ''
  const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || 'vorrio-export.zip'
  return { blob: await response.blob(), filename }
}

export const api = {
  authState: () => request<AuthenticationState>('/api/v1/auth/state'),
  me: () => request<AuthenticationState>('/api/v1/auth/me'),
  setup: (password: string, displayName: string) =>
    request<AuthenticationState>('/api/v1/auth/setup', {
      method: 'POST',
      body: JSON.stringify({ password, display_name: displayName }),
    }),
  login: (password: string, identifier?: string) =>
    request<AuthenticationState>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ password, identifier: identifier || null }),
    }),
  verifyMfa: (challenge: string, code: string) =>
    request<AuthenticationState>('/api/v1/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify({ challenge, code }),
    }),
  recoveryLogin: (identifier: string, code: string) =>
    request<AuthenticationState>('/api/v1/auth/recovery', {
      method: 'POST',
      body: JSON.stringify({ identifier, code }),
    }),
  security: () => request<SecurityState>('/api/v1/auth/security'),
  notificationState: () => request<NotificationState>('/api/v1/notifications/state'),
  saveNotificationPreferences: (preferences: NotificationPreferences) =>
    request<NotificationState>('/api/v1/notifications/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    }),
  registerPushSubscription: (subscription: {
    endpoint: string
    keys: { p256dh: string; auth: string }
    device_name: string
  }) => request<PushDevice>('/api/v1/notifications/subscriptions', {
    method: 'POST',
    body: JSON.stringify(subscription),
  }),
  revokePushSubscription: (subscriptionId: string) =>
    request<{ revoked: number; authenticated: boolean }>(
      `/api/v1/notifications/subscriptions/${encodeURIComponent(subscriptionId)}`,
      { method: 'DELETE' },
    ),
  testPushNotification: (subscriptionId: string) =>
    request<{ delivered: number; failed: number }>('/api/v1/notifications/test', {
      method: 'POST',
      body: JSON.stringify({ subscription_id: subscriptionId }),
    }),
  reauthenticate: (password: string, code?: string) =>
    request<SecurityState>('/api/v1/auth/reauthenticate', {
      method: 'POST',
      body: JSON.stringify({ password, code: code || null }),
    }),
  changePassword: (password: string) =>
    request<SecurityState>('/api/v1/auth/password', {
      method: 'PUT',
      body: JSON.stringify({ password }),
    }),
  setupTotp: () => request<TotpSetup>('/api/v1/auth/totp/setup', { method: 'POST' }),
  enableTotp: (code: string) =>
    request<{ enabled: boolean; recovery_codes: string[] }>('/api/v1/auth/totp/enable', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
  disableTotp: () => request<SecurityState>('/api/v1/auth/totp', { method: 'DELETE' }),
  regenerateRecoveryCodes: () =>
    request<{ codes: string[]; remaining: number }>('/api/v1/auth/recovery-codes', { method: 'POST' }),
  beginPasskeyAuthentication: () =>
    request<WebAuthnOptions>('/api/v1/auth/passkeys/authentication/begin', {
      method: 'POST',
      body: JSON.stringify({ origin: window.location.origin }),
    }),
  completePasskeyAuthentication: (challengeId: string, credential: unknown) =>
    request<AuthenticationState>('/api/v1/auth/passkeys/authentication/complete', {
      method: 'POST',
      body: JSON.stringify({ challenge_id: challengeId, credential }),
    }),
  beginPasskeyRegistration: () =>
    request<WebAuthnOptions>('/api/v1/auth/passkeys/registration/begin', {
      method: 'POST',
      body: JSON.stringify({ origin: window.location.origin }),
    }),
  completePasskeyRegistration: (challengeId: string, credential: unknown, name: string) =>
    request<Passkey>('/api/v1/auth/passkeys/registration/complete', {
      method: 'POST',
      body: JSON.stringify({ challenge_id: challengeId, credential, name }),
    }),
  deletePasskey: (credentialId: string) =>
    request<SecurityState>(`/api/v1/auth/passkeys/${encodeURIComponent(credentialId)}`, { method: 'DELETE' }),
  updateOwnerProfile: (displayName: string, email: string | null) =>
    request<AuthenticationState>('/api/v1/auth/profile', {
      method: 'PATCH',
      body: JSON.stringify({ display_name: displayName, email }),
    }),
  authSessions: () => request<AuthSession[]>('/api/v1/auth/sessions'),
  revokeAuthSession: (sessionId: string) =>
    request<{ revoked: number; authenticated: boolean }>(`/api/v1/auth/sessions/${sessionId}`, {
      method: 'DELETE',
    }),
  revokeOtherAuthSessions: () =>
    request<{ revoked: number; authenticated: boolean }>('/api/v1/auth/sessions/revoke-others', {
      method: 'POST',
    }),
  apiTokenScopes: () => request<ApiTokenScope[]>('/api/v1/auth/api-token-scopes'),
  apiTokens: () => request<ApiToken[]>('/api/v1/auth/api-tokens'),
  createApiToken: (name: string, scopes: ApiTokenScopeId[], expiresDays: number) =>
    request<ApiTokenCreated>('/api/v1/auth/api-tokens', {
      method: 'POST',
      body: JSON.stringify({ name, scopes, expires_days: expiresDays }),
    }),
  revokeApiToken: (tokenId: string) =>
    request<{ revoked: number; authenticated: boolean }>(`/api/v1/auth/api-tokens/${encodeURIComponent(tokenId)}`, {
      method: 'DELETE',
    }),
  householdMembers: () => request<HouseholdMember[]>('/api/v1/auth/members'),
  updateHouseholdMember: (userId: string, role: HouseholdMember['role'], active: boolean) =>
    request<HouseholdMember>(`/api/v1/auth/members/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({ role, active }),
    }),
  householdInvitations: () => request<HouseholdInvitation[]>('/api/v1/auth/invitations'),
  createHouseholdInvitation: (input: {
    display_name: string
    email: string
    role: Exclude<HouseholdMember['role'], 'owner'>
    expires_hours: number
  }) => request<HouseholdInvitation>('/api/v1/auth/invitations', {
    method: 'POST',
    body: JSON.stringify(input),
  }),
  revokeHouseholdInvitation: (invitationId: string) =>
    request<{ revoked: number }>(`/api/v1/auth/invitations/${invitationId}`, {
      method: 'DELETE',
    }),
  householdInvitation: (token: string) =>
    request<HouseholdInvitationPublic>(`/api/v1/auth/invitations/${encodeURIComponent(token)}`),
  acceptHouseholdInvitation: (token: string, password: string) =>
    request<AuthenticationState>(`/api/v1/auth/invitations/${encodeURIComponent(token)}/accept`, {
      method: 'POST',
      body: JSON.stringify({ password }),
    }),
  logout: () => request('/api/v1/auth/logout', { method: 'POST' }),
  experience: () => request<ExperienceState>('/api/v1/experience'),
  updateExperience: (input: { complete_onboarding?: boolean; acknowledge_current_version?: boolean }) =>
    request<ExperienceState>('/api/v1/experience', {
      method: 'PUT',
      body: JSON.stringify(input),
    }),
  status: () => request<AppStatus>('/api/v1/status'),
  settings: () => request<SettingsData>('/api/v1/settings'),
  saveSettings: (settings: SettingsData) =>
    request<SettingsData>('/api/v1/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
  exportPreview: () => request<ExportPreview>('/api/v1/privacy/export/preview'),
  downloadHouseholdExport: (includeReceiptFiles = true) =>
    download(`/api/v1/privacy/export?include_receipt_files=${includeReceiptFiles}`),
  retentionPreview: () => request<RetentionPreview>('/api/v1/privacy/retention'),
  runRetention: () => request<RetentionRunResult>('/api/v1/privacy/retention/run', { method: 'POST' }),
  operationsOverview: () => request<OperationsOverview>('/api/v1/operations/overview'),
  eraseHousehold: (confirmation: string) =>
    request<{ deleted: boolean }>('/api/v1/privacy/household', {
      method: 'DELETE',
      body: JSON.stringify({ confirmation }),
    }),
  testGrocy: () => request<{ connected: boolean }>('/api/v1/settings/test-grocy', { method: 'POST' }),
  testProvider: () =>
    request<{ connected: boolean }>('/api/v1/settings/test-provider', { method: 'POST' }),
  receipts: () => request<Receipt[]>('/api/v1/receipts'),
  receipt: (id: string) => request<Receipt>(`/api/v1/receipts/${id}`),
  analyze: async (file: File) => {
    const form = new FormData()
    form.append('image', file)
    return request<Receipt>('/api/v1/receipts/analyze', { method: 'POST', body: form })
  },
  products: (query: string) =>
    request<CatalogProduct[]>(`/api/v1/catalog/products?q=${encodeURIComponent(query)}`),
  itemCandidates: (receiptId: string, itemId: string) =>
    request<ProductCandidateSearch>(
      `/api/v1/receipts/${receiptId}/items/${itemId}/candidates?limit=3`,
    ),
  confirmItemCandidate: (
    receiptId: string,
    itemId: string,
    input: ProductCandidateConfirmInput,
  ) => request<Receipt>(`/api/v1/receipts/${receiptId}/items/${itemId}/candidate`, {
    method: 'POST',
    body: JSON.stringify(input),
  }),
  catalogMasterData: () => request<GrocyMasterData>('/api/v1/catalog/master-data'),
  catalogProducts: (query = '') =>
    request<CatalogProduct[]>(`/api/v1/catalog/products?q=${encodeURIComponent(query)}`),
  createCatalogProduct: (input: CatalogProductCreateInput) =>
    request<CatalogProductDetail>('/api/v1/catalog/products', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  catalogProduct: (productId: string) =>
    request<CatalogProductDetail>(`/api/v1/catalog/products/${encodeURIComponent(productId)}`),
  catalogProductPriceHistory: (productId: string, limit = 100) =>
    request<CatalogPriceHistoryItem[]>(`/api/v1/catalog/products/${encodeURIComponent(productId)}/price-history?limit=${limit}`),
  priceInsights: (limit = 100) =>
    request<PriceInsightsResponse>(`/api/v1/insights/prices?limit=${limit}`),
  budgetOverview: (months = 6) =>
    request<BudgetOverviewResponse>(`/api/v1/insights/budget?months=${months}`),
  updateBudgetSettings: (monthlyLimit: number | null, warningPercent: number) =>
    request<BudgetSettings>('/api/v1/insights/budget/settings', {
      method: 'PUT',
      body: JSON.stringify({ monthly_limit: monthlyLimit, warning_percent: warningPercent }),
    }),
  updateCatalogProduct: (productId: string, input: CatalogProductUpdateInput) =>
    request<CatalogProductDetail>(`/api/v1/catalog/products/${encodeURIComponent(productId)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    }),
  uploadCatalogProductImage: (productId: string, image: File) => {
    const form = new FormData()
    form.append('image', image)
    return request<CatalogProductDetail>(`/api/v1/catalog/products/${encodeURIComponent(productId)}/image`, {
      method: 'POST',
      body: form,
    })
  },
  deleteCatalogProductImage: (productId: string) =>
    request<CatalogProductDetail>(`/api/v1/catalog/products/${encodeURIComponent(productId)}/image`, {
      method: 'DELETE',
    }),
  createCatalogVariant: (productId: string, input: CatalogVariantInput) =>
    request<CatalogProductDetail>(`/api/v1/catalog/products/${encodeURIComponent(productId)}/variants`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  updateCatalogVariant: (variantId: string, input: CatalogVariantInput & { expected_updated_at: string }) =>
    request<CatalogProductDetail>(`/api/v1/catalog/variants/${encodeURIComponent(variantId)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    }),
  deleteCatalogVariant: (variantId: string) =>
    request<CatalogProductDetail>(`/api/v1/catalog/variants/${encodeURIComponent(variantId)}`, {
      method: 'DELETE',
    }),
  createCatalogBarcode: (variantId: string, barcode: string) =>
    request<CatalogProductDetail>(`/api/v1/catalog/variants/${encodeURIComponent(variantId)}/barcodes`, {
      method: 'POST',
      body: JSON.stringify({ barcode }),
    }),
  deleteCatalogBarcode: (variantId: string, barcode: string) =>
    request<CatalogProductDetail>(`/api/v1/catalog/variants/${encodeURIComponent(variantId)}/barcodes/${encodeURIComponent(barcode)}`, {
      method: 'DELETE',
    }),
  createCatalogMaster: (kind: CatalogMasterKind, input: CatalogMasterInput) =>
    request<GrocyMasterItem>(`/api/v1/catalog/master-data/${kind}`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  updateCatalogMaster: (
    kind: CatalogMasterKind,
    itemId: number,
    input: CatalogMasterInput & { expected_updated_at: string },
  ) => request<GrocyMasterItem>(`/api/v1/catalog/master-data/${kind}/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  }),
  archiveCatalogMaster: (kind: CatalogMasterKind, itemId: number) =>
    request<GrocyMasterItem>(`/api/v1/catalog/master-data/${kind}/${itemId}`, {
      method: 'DELETE',
    }),
  stockCountProducts: (query = '') =>
    request<CatalogProductDetail[]>(`/api/v1/stock/count/products?q=${encodeURIComponent(query)}`),
  stockCounts: () => request<StockCountSession[]>('/api/v1/stock/counts'),
  createStockCount: (input: {
    client_mutation_id: string
    source: StockCountSource
    note: string
    lines: StockCountLineInput[]
  }) => request<StockCountSession>('/api/v1/stock/counts', {
    method: 'POST',
    body: JSON.stringify(input),
  }),
  grocyStockPreview: () =>
    request<GrocyStockPreview>('/api/v1/integrations/grocy/stock-preview'),
  shoppingList: () => request<ShoppingListItem[]>('/api/v1/shopping-list'),
  shoppingLowStock: () => request<ShoppingLowStockResponse>('/api/v1/shopping-list/low-stock'),
  generateShoppingList: (input: { client_mutation_id: string; product_ids: string[] }) =>
    request<ShoppingGeneration>('/api/v1/shopping-list/generate', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  updateShoppingItem: (
    itemId: string,
    input: { desired_quantity: number; checked: boolean; notes: string; expected_updated_at: string },
  ) => request<ShoppingListItem>(`/api/v1/shopping-list/${encodeURIComponent(itemId)}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  }),
  resolveScan: (barcode: string, mode: ScanMode, clientMutationId: string) =>
    request<ScanDraft>('/api/v1/scans/resolve', {
      method: 'POST',
      body: JSON.stringify({
        barcode,
        mode,
        client_mutation_id: clientMutationId,
      }),
    }),
  confirmScan: (scanId: string, input: ScanConfirmInput) =>
    request<ScanDraft>(`/api/v1/scans/${scanId}/confirm`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  updateScan: (
    scanId: string,
    input: { mode?: ScanMode; product_id?: string; name?: string; brand?: string; quantity_label?: string },
  ) =>
    request<ScanDraft>(`/api/v1/scans/${scanId}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    }),
  unresolvedScans: () => request<ScanDraft[]>('/api/v1/scans/unresolved'),
  discardScan: (scanId: string) =>
    request<ScanDraft>(`/api/v1/scans/${scanId}`, { method: 'DELETE' }),
  mapItem: (receiptId: string, itemId: string, product: Pick<CatalogProduct, 'id' | 'name'> | null) =>
    request<Receipt>(`/api/v1/receipts/${receiptId}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        product_id: product?.id ?? null,
        remember: true,
      }),
    }),
  createAndMapProduct: (
    receiptId: string,
    itemId: string,
    product: CatalogProductCreateInput,
  ) =>
    request<Receipt>(`/api/v1/receipts/${receiptId}/items/${itemId}/catalog-product`, {
      method: 'POST',
      body: JSON.stringify(product),
    }),
  importGrocyCatalog: () =>
    request<{
      imported: { locations: number; quantity_units: number; product_groups: number; products: number }
      catalog: AppStatus['catalog']
    }>('/api/v1/integrations/grocy/import-catalog', { method: 'POST' }),
  importReceipt: (receiptId: string) =>
    request<{ imported: number; failed: number; grocy_exported: number; grocy_failed: number; receipt: Receipt }>(
      `/api/v1/receipts/${receiptId}/import`,
      { method: 'POST', body: JSON.stringify({ item_ids: null }) },
    ),
}
