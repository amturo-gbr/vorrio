from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from .services.outbound_urls import normalize_connector_url


ProviderType = Literal[
    "cortecs", "openai", "openrouter", "ollama", "openai-compatible", "anthropic"
]
ScanMode = Literal["identify", "add", "consume", "open", "shopping"]
ScanStatus = Literal["resolved", "unresolved", "confirmed", "discarded"]
ScanResolutionSource = Literal["local", "cache", "open_facts", "unresolved"]
StockCountSource = Literal["manual", "grocy_review"]
HouseholdRole = Literal["owner", "admin", "member", "viewer"]
ApiTokenScope = Literal[
    "status:read",
    "catalog:read",
    "stock:read",
    "shopping:read",
    "shopping:write",
    "scans:read",
    "scans:write",
]


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=512)
    identifier: str | None = Field(default=None, max_length=320)


class SetupRequest(BaseModel):
    password: str = Field(min_length=10, max_length=512)
    display_name: str | None = Field(default=None, min_length=2, max_length=100)


class OwnerProfileUpdateInput(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(
        default=None,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class HouseholdInvitationCreateInput(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    email: str = Field(
        min_length=5,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    role: Literal["admin", "member", "viewer"] = "member"
    expires_hours: int = Field(default=72, ge=1, le=168)


class HouseholdInvitationAcceptInput(BaseModel):
    password: str = Field(min_length=10, max_length=512)


class HouseholdMemberUpdateInput(BaseModel):
    role: Literal["admin", "member", "viewer"]
    active: bool = True


class GrocySettingsInput(BaseModel):
    enabled: bool = False
    url: str = Field(default="http://grocy:80", min_length=4, max_length=500)
    api_key: str | None = Field(default=None, max_length=1000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return normalize_connector_url(value)


class ProviderSettingsInput(BaseModel):
    type: ProviderType = "cortecs"
    base_url: str = Field(default="https://api.cortecs.ai/v1", min_length=4, max_length=500)
    model: str = Field(default="", max_length=300)
    api_key: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_base_url(self) -> "ProviderSettingsInput":
        cloud_provider = self.type in {
            "cortecs", "openai", "openrouter", "anthropic"
        }
        self.base_url = normalize_connector_url(
            self.base_url, require_https=cloud_provider
        )
        return self


class PrivacySettingsInput(BaseModel):
    delete_image_after_analysis: bool = False
    retention_days: int = Field(default=7, ge=0, le=365)


class SettingsInput(BaseModel):
    grocy: GrocySettingsInput
    provider: ProviderSettingsInput
    privacy: PrivacySettingsInput


class ItemMappingInput(BaseModel):
    grocy_product_id: int | None = Field(default=None, ge=1)
    grocy_product_name: str | None = Field(default=None, max_length=300)
    remember: bool = True


class CatalogItemMappingInput(BaseModel):
    product_id: str | None = Field(default=None, max_length=100)
    remember: bool = True


class CatalogProductCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    location_id: int | None = Field(default=None, ge=1)
    new_location_name: str | None = Field(default=None, max_length=150)
    new_location_is_freezer: bool = False
    quantity_unit_id: int | None = Field(default=None, ge=1)
    new_quantity_unit_name: str | None = Field(default=None, max_length=150)
    product_group_id: int | None = Field(default=None, ge=1)
    new_product_group_name: str | None = Field(default=None, max_length=150)
    default_best_before_days: int = Field(default=0, ge=0, le=3650)
    minimum_stock_quantity: float = Field(default=0, ge=0, le=1_000_000)
    shopping_target_quantity: float = Field(default=0, ge=0, le=1_000_000)
    brand: str | None = Field(default=None, max_length=200)
    barcode: str | None = Field(default=None, max_length=100)
    remember: bool = True

    @model_validator(mode="after")
    def validate_reorder_rule(self):
        if (
            self.shopping_target_quantity > 0
            and self.shopping_target_quantity <= self.minimum_stock_quantity
        ):
            raise ValueError("Das Auffüllziel muss größer als der Mindestbestand sein")
        return self


class ProductCandidateConfirmInput(BaseModel):
    source: Literal["open_facts"] = "open_facts"
    external_id: str = Field(min_length=4, max_length=100)
    product_id: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=300)
    location_id: int | None = Field(default=None, ge=1)
    new_location_name: str | None = Field(default=None, max_length=150)
    new_location_is_freezer: bool = False
    quantity_unit_id: int | None = Field(default=None, ge=1)
    new_quantity_unit_name: str | None = Field(default=None, max_length=150)
    product_group_id: int | None = Field(default=None, ge=1)
    new_product_group_name: str | None = Field(default=None, max_length=150)
    default_best_before_days: int = Field(default=0, ge=0, le=3650)
    remember: bool = True


class GrocyProductCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    location_id: int | None = Field(default=None, ge=1)
    new_location_name: str | None = Field(default=None, max_length=150)
    new_location_is_freezer: bool = False
    quantity_unit_id: int | None = Field(default=None, ge=1)
    new_quantity_unit_name: str | None = Field(default=None, max_length=150)
    product_group_id: int | None = Field(default=None, ge=1)
    new_product_group_name: str | None = Field(default=None, max_length=150)
    default_best_before_days: int = Field(default=0, ge=0, le=3650)
    remember: bool = True


class ImportRequest(BaseModel):
    item_ids: list[str] | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessCheckResponse(BaseModel):
    id: str
    status: Literal["pass", "warn", "fail"]
    message: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded", "blocked"]
    profile: Literal["lan", "private_https", "public_https"]
    checks: list[ReadinessCheckResponse]


class AuthenticatedUserResponse(BaseModel):
    id: str
    display_name: str
    email: str | None = None
    role: HouseholdRole
    household_id: str
    household_name: str
    owner_setup_complete: bool


class AuthenticationResponse(BaseModel):
    authenticated: bool
    needs_setup: bool | None = None
    needs_owner_setup: bool | None = None
    identifier_required: bool | None = None
    mfa_required: bool | None = None
    mfa_challenge: str | None = None
    mfa_methods: list[Literal["totp", "recovery_code"]] | None = None
    user: AuthenticatedUserResponse | None = None


class AuthSessionResponse(BaseModel):
    id: str
    device_name: str
    created_at: str
    last_seen_at: str
    expires_at: str
    authenticated_at: str
    authentication_method: str
    current: bool


class ApiTokenCreateInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    scopes: list[ApiTokenScope] = Field(min_length=1, max_length=7)
    expires_days: int = Field(default=90, ge=1, le=365)


class ApiTokenResponse(BaseModel):
    id: str
    name: str
    token_prefix: str
    scopes: list[ApiTokenScope]
    expires_at: str
    created_at: str
    last_used_at: str | None = None


class ApiTokenCreatedResponse(ApiTokenResponse):
    token: str


class ApiTokenScopeResponse(BaseModel):
    id: ApiTokenScope
    label: str
    description: str


class MfaVerifyInput(BaseModel):
    challenge: str = Field(min_length=20, max_length=500)
    code: str = Field(min_length=6, max_length=64)


class RecoveryLoginInput(BaseModel):
    identifier: str = Field(min_length=2, max_length=320)
    code: str = Field(min_length=10, max_length=64)


class ReauthenticateInput(BaseModel):
    password: str = Field(min_length=1, max_length=512)
    code: str | None = Field(default=None, max_length=64)


class PasswordChangeInput(BaseModel):
    password: str = Field(min_length=10, max_length=512)


class WebAuthnBeginInput(BaseModel):
    origin: str = Field(min_length=8, max_length=500)


class WebAuthnRegistrationBeginInput(WebAuthnBeginInput):
    name: str = Field(default="Passkey", min_length=1, max_length=100)


class WebAuthnCompleteInput(BaseModel):
    challenge_id: str = Field(min_length=20, max_length=100)
    credential: dict[str, Any]
    name: str | None = Field(default=None, max_length=100)


class WebAuthnOptionsResponse(BaseModel):
    challenge_id: str
    options: dict[str, Any]


class PasskeyResponse(BaseModel):
    id: str
    name: str
    device_type: str
    backed_up: bool
    transports: list[str]
    created_at: str
    last_used_at: str | None = None


class SecurityStateResponse(BaseModel):
    passkeys: list[PasskeyResponse]
    totp_enabled: bool
    recovery_codes_remaining: int
    recent_authentication: bool
    recent_authentication_until: str | None = None
    secure_context_required: bool = True


class PushSubscriptionKeysInput(BaseModel):
    p256dh: str = Field(min_length=20, max_length=500)
    auth: str = Field(min_length=8, max_length=200)


class PushSubscriptionCreateInput(BaseModel):
    endpoint: HttpUrl
    keys: PushSubscriptionKeysInput
    device_name: str = Field(default="Vorrio-Gerät", min_length=1, max_length=100)


class PushSubscriptionResponse(BaseModel):
    id: str
    endpoint_fingerprint: str
    device_name: str
    active: bool
    failure_count: int
    created_at: str
    updated_at: str
    last_success_at: str | None = None
    last_failure_at: str | None = None


class NotificationPreferencesInput(BaseModel):
    push_enabled: bool = False
    low_stock_enabled: bool = True
    expiry_enabled: bool = True
    expiry_days_before: int = Field(default=7, ge=0, le=90)


class NotificationPreferencesResponse(NotificationPreferencesInput):
    pass


class NotificationStateResponse(BaseModel):
    public_key: str
    secure_context_required: bool = True
    preferences: NotificationPreferencesResponse
    subscriptions: list[PushSubscriptionResponse]
    active_low_stock_events: int = 0
    active_expiry_events: int = 0
    last_checked_at: str | None = None


class NotificationTestInput(BaseModel):
    subscription_id: str = Field(min_length=20, max_length=100)


class NotificationDeliveryResponse(BaseModel):
    delivered: int
    failed: int


class TotpSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_data_uri: str


class TotpVerifyInput(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class TotpEnableResponse(BaseModel):
    enabled: bool
    recovery_codes: list[str] = Field(default_factory=list)


class RecoveryCodesResponse(BaseModel):
    codes: list[str]
    remaining: int


class SessionRevocationResponse(BaseModel):
    revoked: int
    authenticated: bool = True


class HouseholdMemberResponse(BaseModel):
    id: str
    display_name: str
    email: str | None = None
    role: HouseholdRole
    active: bool
    active_session_count: int
    created_at: str
    updated_at: str


class HouseholdInvitationResponse(BaseModel):
    id: str
    display_name: str
    email: str
    role: Literal["admin", "member", "viewer"]
    expires_at: str
    created_at: str
    invite_token: str | None = None


class HouseholdInvitationPublicResponse(BaseModel):
    valid: bool
    household_name: str
    display_name: str
    email: str
    role: Literal["admin", "member", "viewer"]
    expires_at: str


class CatalogSummaryResponse(BaseModel):
    products: int
    variants: int
    barcodes: int
    stock_lots: int


class StatusResponse(BaseModel):
    grocy_configured: bool
    grocy_enabled: bool
    grocy_connected: bool
    provider_configured: bool
    provider: str
    catalog: CatalogSummaryResponse
    version: str


class PublicGrocySettings(BaseModel):
    enabled: bool
    url: str
    api_key_configured: bool


class PublicProviderSettings(BaseModel):
    type: ProviderType
    base_url: str
    model: str
    api_key_configured: bool


class PublicPrivacySettings(BaseModel):
    delete_image_after_analysis: bool
    retention_days: int


class PublicSettingsResponse(BaseModel):
    grocy: PublicGrocySettings
    provider: PublicProviderSettings
    privacy: PublicPrivacySettings


class RetentionPreviewResponse(BaseModel):
    delete_after_analysis: bool
    retention_days: int
    retained_file_count: int
    retained_bytes: int
    expired_file_count: int
    expired_bytes: int
    cutoff: str


class RetentionRunResponse(BaseModel):
    deleted_file_count: int
    deleted_bytes: int
    cleared_receipt_count: int
    rejected_path_count: int
    completed_at: str


class ExportPreviewResponse(BaseModel):
    household_name: str
    counts: dict[str, int]
    receipt_file_count: int
    receipt_file_bytes: int
    excluded_secret_categories: list[str]


class OperationsCountResponse(BaseModel):
    active_users: int
    active_sessions: int
    active_api_tokens: int
    active_push_devices: int
    pending_receipts: int
    products: int
    stock_lots: int
    failures_24h: int


class OperationsAuditEventResponse(BaseModel):
    id: str
    category: str
    action: str
    outcome: str
    created_at: str
    actor_label: str


class OperationsOverviewResponse(BaseModel):
    database_integrity: str
    database_bytes: int
    counts: OperationsCountResponse
    retention: RetentionPreviewResponse
    recent_events: list[OperationsAuditEventResponse]
    generated_at: str


class HouseholdEraseInput(BaseModel):
    confirmation: Literal["HAUSHALT ENDGÜLTIG LÖSCHEN"]


class HouseholdEraseResponse(BaseModel):
    deleted: bool
    deleted_receipt_files: int
    deleted_receipt_bytes: int
    completed_at: str


class MatchEvidenceResponse(BaseModel):
    source: str
    label: str
    confidence: float = Field(ge=0, le=1)
    automatic: bool


class ProductCandidateEvidenceResponse(BaseModel):
    source: str
    label: str


class ProductCandidateResponse(BaseModel):
    external_id: str
    barcode: str
    name: str
    brand: str | None = None
    quantity: str | None = None
    image_url: str | None = None
    stores: list[str] = Field(default_factory=list)
    source: Literal["open_facts"]
    source_label: str
    source_url: str | None = None
    database_license: str | None = None
    image_license: str | None = None
    attribution: str | None = None
    score: float = Field(ge=0, le=100)
    ai_confidence: float | None = Field(default=None, ge=0, le=100)
    ai_reason: str | None = None
    store_match: bool
    local_product_id: str | None = None
    local_product_name: str | None = None
    evidence: list[ProductCandidateEvidenceResponse] = Field(default_factory=list)


class ProductCandidateSearchResponse(BaseModel):
    query: str
    store_name: str | None = None
    receipt_unit_price: float | None = None
    currency: str
    source: Literal["open_facts"]
    cached: bool
    ai_ranked: bool
    candidates: list[ProductCandidateResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReceiptItemResponse(BaseModel):
    id: str
    receipt_id: str
    position: int
    raw_name: str
    normalized_name: str | None = None
    quantity: float
    unit_price: float | None = None
    total_price: float | None = None
    barcode: str | None = None
    brand: str | None = None
    best_before_date: str | None = None
    suggested_location: str | None = None
    suggested_unit: str | None = None
    suggested_product_group: str | None = None
    suggested_best_before_days: int | None = None
    suggestion_confidence: float | None = None
    catalog_product_id: str | None = None
    catalog_product_name: str | None = None
    catalog_variant_id: str | None = None
    catalog_product_image_url: str | None = None
    catalog_variant_name: str | None = None
    catalog_variant_brand: str | None = None
    catalog_variant_package_amount: float | None = None
    catalog_variant_package_unit: str | None = None
    suggested_catalog_product_id: str | None = None
    suggested_catalog_product_name: str | None = None
    suggested_catalog_product_score: float | None = None
    grocy_product_id: int | None = None
    grocy_product_name: str | None = None
    grocy_exported: int = 0
    match_status: str
    match_score: float | None = None
    match_reason: str
    match_evidence: list[MatchEvidenceResponse] = Field(default_factory=list)
    imported: int
    import_error: str | None = None


class ReceiptResponse(BaseModel):
    id: str
    store_name: str | None = None
    purchase_date: str | None = None
    currency: str
    total: float | None = None
    status: str
    retailer: str | None = None
    store_number: str | None = None
    store_address: str | None = None
    item_count: int | None = None
    imported_count: int | None = None
    ready_count: int | None = None
    review_count: int
    created_at: str
    updated_at: str
    items: list[ReceiptItemResponse] | None = None
    duplicate: bool | None = None


class CatalogProductResponse(BaseModel):
    id: str
    name: str
    normalized_name: str
    product_group_id: int | None = None
    product_group_name: str | None = None
    default_location_id: int | None = None
    default_location_name: str | None = None
    default_quantity_unit_id: int | None = None
    default_quantity_unit_name: str | None = None
    default_best_before_days: int
    minimum_stock_quantity: float = 0
    shopping_target_quantity: float = 0
    image_url: str | None = None
    variant_count: int
    barcode_count: int
    stock_quantity: float
    grocy_product_id: int | None = None


class CatalogProductUpdateInput(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    product_group_id: int | None = Field(default=None, ge=1)
    default_location_id: int | None = Field(default=None, ge=1)
    default_quantity_unit_id: int | None = Field(default=None, ge=1)
    default_best_before_days: int = Field(default=0, ge=0, le=3650)
    minimum_stock_quantity: float = Field(default=0, ge=0, le=1_000_000)
    shopping_target_quantity: float = Field(default=0, ge=0, le=1_000_000)
    image_url: HttpUrl | None = None
    notes: str = Field(default="", max_length=2000)
    expected_updated_at: str = Field(min_length=10, max_length=80)

    @model_validator(mode="after")
    def validate_reorder_rule(self):
        if (
            self.shopping_target_quantity > 0
            and self.shopping_target_quantity <= self.minimum_stock_quantity
        ):
            raise ValueError("Das Auffüllziel muss größer als der Mindestbestand sein")
        return self


class CatalogBarcodeCreateInput(BaseModel):
    barcode: str = Field(min_length=4, max_length=100)


class CatalogBarcodeResponse(BaseModel):
    barcode: str
    symbology: str | None = None
    is_primary: int = 1
    created_at: str
    updated_at: str


class CatalogVariantCreateInput(BaseModel):
    name: str | None = Field(default=None, max_length=300)
    brand: str | None = Field(default=None, max_length=200)
    package_amount: float | None = Field(default=None, gt=0, le=1_000_000)
    package_unit: str | None = Field(default=None, max_length=100)
    image_url: HttpUrl | None = None


class CatalogVariantUpdateInput(CatalogVariantCreateInput):
    expected_updated_at: str = Field(min_length=10, max_length=80)


class CatalogVariantResponse(BaseModel):
    id: str
    product_id: str
    name: str | None = None
    brand: str | None = None
    package_amount: float | None = None
    package_unit: str | None = None
    image_url: str | None = None
    created_at: str
    updated_at: str
    barcodes: list[CatalogBarcodeResponse]
    receipt_count: int = 0
    stock_lot_count: int = 0


class CatalogProductDetailResponse(CatalogProductResponse):
    notes: str
    active: int
    created_at: str
    updated_at: str
    variants: list[CatalogVariantResponse]


class StockCountLineInput(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    variant_id: str | None = Field(default=None, max_length=100)
    location_id: int | None = Field(default=None, ge=1)
    counted_quantity: float = Field(ge=0, le=1_000_000)
    best_before_date: date | None = None
    unit_price: float | None = Field(default=None, ge=0, le=1_000_000)
    note: str = Field(default="", max_length=500)


class StockCountCreateInput(BaseModel):
    client_mutation_id: str = Field(
        min_length=8,
        max_length=100,
        description="Idempotency key generated once for the reviewed count.",
        examples=["count_018f3f1c8c1a"],
    )
    source: StockCountSource = "manual"
    note: str = Field(default="", max_length=1000)
    lines: list[StockCountLineInput] = Field(min_length=1, max_length=1000)


class StockCountLineResponse(BaseModel):
    id: str
    session_id: str
    product_id: str
    product_name: str
    variant_id: str | None = None
    variant_name: str | None = None
    variant_brand: str | None = None
    location_id: int | None = None
    location_name: str | None = None
    quantity_unit_name: str | None = None
    previous_quantity: float
    counted_quantity: float
    quantity_delta: float
    best_before_date: str | None = None
    unit_price: float | None = None
    note: str
    movement_count: int
    created_at: str


class StockCountSessionResponse(BaseModel):
    id: str
    client_mutation_id: str
    source: StockCountSource
    note: str
    status: Literal["confirmed"]
    line_count: int
    changed_count: int
    created_at: str
    lines: list[StockCountLineResponse]


class GrocyStockPreviewItemResponse(BaseModel):
    product_id: str
    product_name: str
    grocy_product_id: int
    current_quantity: float
    proposed_quantity: float
    quantity_delta: float
    default_location_id: int | None = None
    default_location_name: str | None = None
    quantity_unit_name: str | None = None
    best_before_date: str | None = None


class GrocyUnmappedStockResponse(BaseModel):
    grocy_product_id: int
    product_name: str | None = None
    quantity: float


class GrocyStockPreviewResponse(BaseModel):
    items: list[GrocyStockPreviewItemResponse]
    unmapped: list[GrocyUnmappedStockResponse]
    generated_at: str


class CatalogPriceHistoryItemResponse(BaseModel):
    receipt_item_id: str
    receipt_id: str
    purchase_date: str | None = None
    store_name: str | None = None
    retailer: str | None = None
    currency: str
    quantity: float
    unit_price: float | None = None
    total_price: float | None = None
    barcode: str | None = None
    catalog_variant_id: str | None = None
    variant_name: str | None = None
    brand: str | None = None
    package_amount: float | None = None
    package_unit: str | None = None


class PriceStoreSummaryResponse(BaseModel):
    store_key: str
    store_name: str
    latest_price: float
    latest_date: str | None = None
    lowest_price: float
    average_price: float
    observation_count: int


class PriceProductSummaryResponse(BaseModel):
    product_id: str
    product_name: str
    image_url: str | None = None
    quantity_unit_name: str | None = None
    currency: str
    observation_count: int
    store_count: int
    latest_price: float
    latest_date: str | None = None
    latest_store: str
    previous_price: float | None = None
    lowest_price: float
    highest_price: float
    change_amount: float | None = None
    change_percent: float | None = None
    stores: list[PriceStoreSummaryResponse]


class PriceInsightsResponse(BaseModel):
    products: list[PriceProductSummaryResponse]
    product_count: int
    store_count: int
    observation_count: int
    generated_at: str


class BudgetSettingsInput(BaseModel):
    monthly_limit: float | None = Field(default=None, ge=1, le=1_000_000)
    warning_percent: int = Field(default=80, ge=50, le=100)


class BudgetSettingsResponse(BaseModel):
    configured: bool
    monthly_limit: float | None = None
    currency: Literal["EUR"] = "EUR"
    warning_percent: int
    updated_at: str | None = None


class BudgetCurrentPeriodResponse(BaseModel):
    month: str
    start_date: str
    as_of_date: str
    spent: float
    receipt_count: int
    average_receipt: float
    remaining: float | None = None
    percent_used: float | None = None
    forecast: float
    days_elapsed: int
    days_total: int
    days_remaining: int
    daily_available: float | None = None
    status: Literal["unconfigured", "on_track", "watch", "over"]
    latest_purchase_date: str | None = None


class BudgetComparisonResponse(BaseModel):
    start_date: str
    end_date: str
    spent: float
    receipt_count: int
    change_amount: float
    change_percent: float | None = None


class BudgetMonthResponse(BaseModel):
    month: str
    spent: float
    receipt_count: int
    is_current: bool


class BudgetStoreResponse(BaseModel):
    store_key: str
    store_name: str
    spent: float
    receipt_count: int
    share_percent: float


class BudgetDataQualityResponse(BaseModel):
    confirmed_receipt_count: int
    counted_receipt_count: int
    pending_receipt_count: int
    missing_total_count: int
    other_currency_receipt_count: int
    coverage_percent: float


class BudgetOverviewResponse(BaseModel):
    settings: BudgetSettingsResponse
    current_period: BudgetCurrentPeriodResponse
    comparison: BudgetComparisonResponse
    months: list[BudgetMonthResponse]
    stores: list[BudgetStoreResponse]
    data_quality: BudgetDataQualityResponse
    generated_at: str


class ReconcileResponse(BaseModel):
    scanned: int
    resolved: int
    suggested: int


class GrocyProductResponse(BaseModel):
    id: int
    name: str


class MasterDataItemResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    active: int = 1
    grocy_id: int | None = None
    is_freezer: int | None = None
    name_plural: str | None = None
    usage_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class MasterDataCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=500)
    is_freezer: bool = False
    name_plural: str | None = Field(default=None, max_length=150)


class MasterDataUpdateInput(MasterDataCreateInput):
    expected_updated_at: str = Field(min_length=10, max_length=80)


class MasterDataResponse(BaseModel):
    locations: list[MasterDataItemResponse]
    quantity_units: list[MasterDataItemResponse]
    product_groups: list[MasterDataItemResponse]


class BarcodeLookupResponse(BaseModel):
    found: bool
    local: bool
    product: dict[str, Any] | None = None


class ScanResolveInput(BaseModel):
    barcode: str = Field(
        min_length=4,
        max_length=100,
        description="EAN, UPC or GTIN as decoded by the camera or scanner.",
        examples=["4000000000016"],
    )
    mode: ScanMode = Field(default="identify", examples=["identify"])
    client_mutation_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
        description="Optional idempotency key generated once per resolve attempt.",
        examples=["scan_018f3f1c8c1a"],
    )


class ScanUpdateInput(BaseModel):
    mode: ScanMode | None = None
    product_id: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=300)
    brand: str | None = Field(default=None, max_length=200)
    quantity_label: str | None = Field(default=None, max_length=100)
    image_url: HttpUrl | None = None


class ScanConfirmInput(BaseModel):
    client_mutation_id: str = Field(
        min_length=8,
        max_length=100,
        description="Idempotency key generated once for the confirmation action.",
        examples=["confirm_018f3f1c8c1a"],
    )
    product_id: str | None = Field(
        default=None,
        max_length=100,
        description="Existing local product to map before confirming.",
    )
    name: str | None = Field(
        default=None,
        max_length=300,
        description="Product name used only when a local product must be created.",
    )
    brand: str | None = Field(default=None, max_length=200)
    variant_name: str | None = Field(default=None, max_length=300)
    package_amount: float | None = Field(default=None, gt=0, le=100000)
    package_unit: str | None = Field(default=None, max_length=50)
    image_url: HttpUrl | None = None
    location_id: int | None = Field(default=None, ge=1)
    quantity_unit_id: int | None = Field(default=None, ge=1)
    product_group_id: int | None = Field(default=None, ge=1)
    default_best_before_days: int = Field(default=0, ge=0, le=3650)
    quantity: float = Field(default=1, gt=0, le=10000)
    best_before_date: date | None = None
    unit_price: float | None = Field(default=None, ge=0, le=1000000)


class ScanResponse(BaseModel):
    id: str
    barcode_raw: str
    barcode_normalized: str
    symbology: str | None = None
    mode: ScanMode
    status: ScanStatus
    resolution_source: ScanResolutionSource
    product_id: str | None = None
    variant_id: str | None = None
    product_name: str | None = None
    product_image_url: str | None = None
    default_location_id: int | None = None
    default_location_name: str | None = None
    default_quantity_unit_id: int | None = None
    default_quantity_unit_name: str | None = None
    brand: str | None = None
    variant_name: str | None = None
    package_amount: float | None = None
    package_unit: str | None = None
    stock_quantity: float = 0
    suggestion: dict[str, Any] | None = None
    upstream_error: str | None = None
    action_result: dict[str, Any] | None = None
    created_at: str
    updated_at: str


class ShoppingListItemResponse(BaseModel):
    id: str
    product_id: str | None = None
    product_name: str | None = None
    product_image_url: str | None = None
    label: str
    desired_quantity: float
    checked: int
    notes: str
    quantity_unit_name: str | None = None
    stock_quantity: float = 0
    minimum_stock_quantity: float = 0
    shopping_target_quantity: float = 0
    created_at: str
    updated_at: str


class ShoppingLowStockItemResponse(BaseModel):
    product_id: str
    product_name: str
    product_image_url: str | None = None
    current_quantity: float
    minimum_quantity: float
    target_quantity: float
    suggested_quantity: float
    quantity_unit_name: str | None = None
    existing_item_id: str | None = None
    existing_desired_quantity: float | None = None


class ShoppingLowStockResponse(BaseModel):
    items: list[ShoppingLowStockItemResponse]
    generated_at: str


class ShoppingGenerateInput(BaseModel):
    client_mutation_id: str = Field(min_length=8, max_length=100)
    product_ids: list[str] = Field(min_length=1, max_length=1000)


class ShoppingGenerationItemResponse(BaseModel):
    id: str
    run_id: str
    product_id: str
    product_name: str
    shopping_item_id: str | None = None
    current_quantity: float
    minimum_quantity: float
    target_quantity: float
    suggested_quantity: float
    quantity_unit_name: str | None = None
    action: Literal["created", "updated", "unchanged", "skipped"]
    created_at: str


class ShoppingGenerationResponse(BaseModel):
    id: str
    client_mutation_id: str
    requested_count: int
    created_count: int
    updated_count: int
    unchanged_count: int
    skipped_count: int
    created_at: str
    items: list[ShoppingGenerationItemResponse]


class ShoppingListItemUpdateInput(BaseModel):
    desired_quantity: float = Field(gt=0, le=1_000_000)
    checked: bool = False
    notes: str = Field(default="", max_length=500)
    expected_updated_at: str = Field(min_length=10, max_length=80)


class GrocyImportCounts(BaseModel):
    locations: int
    quantity_units: int
    product_groups: int
    products: int


class GrocyCatalogImportResponse(BaseModel):
    imported: GrocyImportCounts
    catalog: CatalogSummaryResponse


class ReceiptImportResponse(BaseModel):
    run_id: str
    requested: int
    imported: int
    failed: int
    grocy_exported: int
    grocy_failed: int
    details: list[dict[str, Any]]
    receipt: ReceiptResponse


class ConnectionTestResponse(BaseModel):
    connected: bool
    info: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    detail: str
