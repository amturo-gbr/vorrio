from __future__ import annotations

import asyncio
import hashlib
import json
import mimetypes
import secrets
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.exceptions import (
    InvalidAuthenticationResponse,
    InvalidRegistrationResponse,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .config import config
from .database import Database, now_iso
from .deployment_security import is_safe_secret_key, public_exposure_failures
from .schemas import (
    CatalogItemMappingInput,
    CatalogBarcodeCreateInput,
    CatalogPriceHistoryItemResponse,
    PriceInsightsResponse,
    BudgetOverviewResponse,
    BudgetSettingsInput,
    BudgetSettingsResponse,
    CatalogProductCreateInput,
    CatalogProductDetailResponse,
    ProductCandidateConfirmInput,
    ProductCandidateSearchResponse,
    CatalogProductUpdateInput,
    AuthenticationResponse,
    ApiTokenCreateInput,
    ApiTokenCreatedResponse,
    ApiTokenResponse,
    ApiTokenScopeResponse,
    AuthSessionResponse,
    MfaVerifyInput,
    NotificationDeliveryResponse,
    NotificationPreferencesInput,
    NotificationStateResponse,
    NotificationTestInput,
    PasswordChangeInput,
    PasskeyResponse,
    ReauthenticateInput,
    RecoveryCodesResponse,
    RecoveryLoginInput,
    SecurityStateResponse,
    PushSubscriptionCreateInput,
    PushSubscriptionResponse,
    TotpEnableResponse,
    TotpSetupResponse,
    TotpVerifyInput,
    WebAuthnBeginInput,
    WebAuthnCompleteInput,
    WebAuthnOptionsResponse,
    HouseholdInvitationAcceptInput,
    HouseholdInvitationCreateInput,
    HouseholdInvitationPublicResponse,
    HouseholdInvitationResponse,
    HouseholdMemberResponse,
    HouseholdMemberUpdateInput,
    OwnerProfileUpdateInput,
    UserPreferencesUpdateInput,
    SessionRevocationResponse,
    BarcodeLookupResponse,
    CatalogProductResponse,
    ConnectionTestResponse,
    ErrorResponse,
    ExperienceStateResponse,
    ExperienceUpdateInput,
    GrocyCatalogImportResponse,
    GrocyProductResponse,
    GrocyProductCreateInput,
    HealthResponse,
    ImportRequest,
    ItemMappingInput,
    LoginRequest,
    MasterDataCreateInput,
    MasterDataResponse,
    MasterDataItemResponse,
    MasterDataUpdateInput,
    PublicSettingsResponse,
    ExportPreviewResponse,
    HouseholdEraseInput,
    HouseholdEraseResponse,
    OperationsOverviewResponse,
    RetentionPreviewResponse,
    RetentionRunResponse,
    ReadinessResponse,
    ReceiptImportResponse,
    ReceiptResponse,
    ReconcileResponse,
    ScanConfirmInput,
    ScanResolveInput,
    ScanResponse,
    ScanUpdateInput,
    SettingsInput,
    ShoppingGenerateInput,
    ShoppingGenerationResponse,
    ShoppingListItemUpdateInput,
    ShoppingListItemResponse,
    ShoppingLowStockResponse,
    StockCountCreateInput,
    StockCountSessionResponse,
    GrocyStockPreviewResponse,
    StatusResponse,
    SetupRequest,
    CatalogVariantCreateInput,
    CatalogVariantUpdateInput,
)
from .middleware import (
    LegacyApiCompatibilityMiddleware,
    RequestBodyLimitMiddleware,
    RequestSecurityMiddleware,
    PublicExposureGateMiddleware,
    PrivacySafeAccessLogMiddleware,
    SecurityHeadersMiddleware,
    request_source_fingerprint,
)
from .security import SecretStore, browser_device_name, hash_password, verify_password
from .services.grocy import GrocyClient, GrocyError
from .services.authentication import (
    WebAuthnContextError,
    generate_recovery_codes,
    generate_totp_secret,
    recovery_code_hash,
    totp_provisioning_uri,
    totp_qr_data_uri,
    verify_totp_step,
    webauthn_context,
)
from .services.matching import match_items, reconcile_unresolved_items
from .services.notifications import NotificationService
from .services.outbound_urls import OutboundUrlError, validate_public_push_url
from .services.media import MediaValidationError, prepare_product_image, validate_image_upload
from .services.pdf_receipt import PdfReceiptError, prepare_pdf_receipt
from .services.providers import ProviderError, analyze_receipt, test_provider
from .services.receipt_identity import build_receipt_fingerprint
from .services.product_data import ProductDataError, lookup_open_facts
from .services.product_candidates import find_product_candidates
from .services.product_images import (
    ProductImageStore,
    is_managed_product_image_url,
    managed_product_image_url,
)
from .services.privacy import PrivacyService
from .services.scanning import (
    BarcodeValidationError,
    normalize_barcode,
    parse_package_quantity,
)
from .services.settings import SettingsService


config.data_dir.mkdir(parents=True, exist_ok=True)
(config.data_dir / "receipts").mkdir(parents=True, exist_ok=True)
database = Database(config.data_dir / "app.db")
product_image_store = ProductImageStore(config.data_dir)
secret_store = SecretStore(config.secret_key)
settings_service = SettingsService(database, secret_store)
notification_service = NotificationService(
    database,
    secret_store,
    vapid_subject=config.web_push_subject,
)
privacy_service = PrivacyService(database, config.data_dir)


async def _notification_loop() -> None:
    while True:
        await asyncio.sleep(config.notification_check_seconds)
        try:
            await asyncio.to_thread(notification_service.evaluate_and_send)
        except Exception as exc:  # pragma: no cover - scheduler resilience
            database.add_audit_event(
                category="notifications",
                action="scheduled_check",
                outcome="failure",
                details={"error": str(exc)[:300]},
            )


async def _privacy_retention_loop() -> None:
    await asyncio.sleep(300)
    while True:
        try:
            privacy = settings_service.get_private()["privacy"]
            result = await asyncio.to_thread(
                privacy_service.prune_receipt_files,
                delete_after_analysis=bool(privacy["delete_image_after_analysis"]),
                retention_days=int(privacy["retention_days"]),
            )
            if result["cleared_receipt_count"]:
                database.add_audit_event(
                    category="privacy",
                    action="scheduled_retention",
                    outcome="success",
                    details={
                        "cleared_receipt_count": result["cleared_receipt_count"],
                        "deleted_file_count": result["deleted_file_count"],
                    },
                )
        except Exception as exc:  # pragma: no cover - scheduler resilience
            database.add_audit_event(
                category="privacy",
                action="scheduled_retention",
                outcome="failure",
                details={"error": str(exc)[:300]},
            )
        await asyncio.sleep(60 * 60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    notification_task = asyncio.create_task(_notification_loop())
    privacy_task = asyncio.create_task(_privacy_retention_loop())
    try:
        yield
    finally:
        notification_task.cancel()
        privacy_task.cancel()
        try:
            await asyncio.gather(notification_task, privacy_task)
        except asyncio.CancelledError:
            pass


OPENAPI_TAGS = [
    {"name": "System", "description": "Health and instance status."},
    {"name": "Authentication", "description": "Household setup and session authentication."},
    {"name": "Notifications", "description": "Opt-in Web Push devices and state-based stock alerts."},
    {"name": "Settings", "description": "Provider, connector and privacy settings."},
    {"name": "Privacy & Operations", "description": "Owner-only export, retention, erasure and privacy-safe operations."},
    {"name": "Receipts", "description": "Receipt analysis, review and stock intake."},
    {"name": "Catalog", "description": "Products, master data, barcodes and stock metadata."},
    {"name": "Stock", "description": "Reviewed opening counts and auditable stock corrections."},
    {"name": "Shopping", "description": "Low-stock proposals and the reviewed household shopping list."},
    {"name": "Insights", "description": "Receipt-backed household budget and historic price knowledge."},
    {"name": "Scanning", "description": "Idempotent package identification and stock actions."},
    {"name": "Integrations", "description": "Optional external connectors."},
    {"name": "Legacy Grocy", "description": "Compatibility endpoints for the former Grocy-first workflow."},
]

app = FastAPI(
    title="Vorrio REST API",
    summary="Self-hosted household inventory and receipt API",
    description=(
        "The versioned API used by the Vorrio PWA and external household tools. "
        "All stock-changing operations require an authenticated household session."
    ),
    version="0.8.22",
    lifespan=lifespan,
    contact={"name": "Amturo UG"},
    license_info={
        "name": "GNU Affero General Public License v3.0 or later",
        "identifier": "AGPL-3.0-or-later",
    },
    openapi_tags=OPENAPI_TAGS,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        409: {"model": ErrorResponse, "description": "Instance or workflow conflict"},
        502: {"model": ErrorResponse, "description": "Configured upstream service failed"},
    },
)
import_locks: dict[str, asyncio.Lock] = {}
app.add_middleware(
    RequestSecurityMiddleware,
    database=database,
    secret_key=config.secret_key,
    public_url=config.public_url,
    allowed_origins=config.allowed_origins,
    require_session_origin=config.deployment_profile != "lan",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.secret_key,
    https_only=config.session_https_only,
    same_site="lax",
    max_age=60 * 60 * 24 * 30,
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(config.trusted_hosts),
    www_redirect=False,
)
app.add_middleware(RequestBodyLimitMiddleware, max_bytes=config.max_request_bytes)
app.add_middleware(LegacyApiCompatibilityMiddleware)
app.add_middleware(
    PublicExposureGateMiddleware,
    blocked_reasons=public_exposure_failures(config),
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PrivacySafeAccessLogMiddleware)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        summary=app.summary,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        contact=app.contact,
        license_info=app.license_info,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "householdSession"
    ] = {
        "type": "apiKey",
        "in": "cookie",
        "name": "session",
        "description": (
            "Signed HttpOnly cookie containing a random token whose hash is bound to a "
            "revocable server-side device session."
        ),
    }
    schema["components"]["securitySchemes"]["apiToken"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "Vorrio API token",
        "description": (
            "Scoped automation credential sent only through the Authorization header. "
            "The raw token is returned once; Vorrio stores only its SHA-256 hash."
        ),
    }
    public_operations = {
        ("/api/health", "get"),
        ("/api/readiness", "get"),
        ("/api/v1/auth/state", "get"),
        ("/api/v1/auth/setup", "post"),
        ("/api/v1/auth/login", "post"),
        ("/api/v1/auth/mfa/verify", "post"),
        ("/api/v1/auth/recovery", "post"),
        ("/api/v1/auth/passkeys/authentication/begin", "post"),
        ("/api/v1/auth/passkeys/authentication/complete", "post"),
        ("/api/v1/auth/invitations/{token}", "get"),
        ("/api/v1/auth/invitations/{token}/accept", "post"),
    }
    for path, methods in schema.get("paths", {}).items():
        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if (path, method.lower()) in public_operations:
                continue
            required_scope = _api_token_required_scope(path, method.upper())
            if required_scope:
                operation["security"] = [
                    {"householdSession": []},
                    {"apiToken": []},
                ]
                operation["x-vorrio-required-scope"] = required_scope
            else:
                operation["security"] = [{"householdSession": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
RECENT_AUTH_SECONDS = 10 * 60
API_TOKEN_SCOPES = {
    "de": {
        "status:read": ("Status lesen", "Instanz-, Katalog- und Connectorstatus lesen."),
        "catalog:read": ("Katalog lesen", "Produkte, Barcodes und Stammdaten lesen."),
        "stock:read": ("Vorrat lesen", "Aktuelle Mengen und Zählhistorie lesen."),
        "shopping:read": ("Einkaufsliste lesen", "Liste und Auffüllvorschläge lesen."),
        "shopping:write": ("Einkaufsliste ändern", "Einträge erzeugen, ändern und abhaken."),
        "scans:read": ("Scans lesen", "Scanentwürfe und unbekannte Codes lesen."),
        "scans:write": ("Scans ausführen", "Codes auflösen und bestätigte Scanaktionen ausführen."),
    },
    "en": {
        "status:read": ("Read status", "Read instance, catalog and connector status."),
        "catalog:read": ("Read catalog", "Read products, barcodes and master data."),
        "stock:read": ("Read stock", "Read current quantities and stock-count history."),
        "shopping:read": ("Read shopping list", "Read the list and replenishment suggestions."),
        "shopping:write": ("Change shopping list", "Create, change and check off entries."),
        "scans:read": ("Read scans", "Read scan drafts and unknown codes."),
        "scans:write": ("Execute scans", "Resolve codes and execute confirmed scan actions."),
    },
}

CURRENT_RELEASE = {
    "de": {
        "version": "0.8.22",
        "title": "Vorrio spricht Deutsch und Englisch",
        "summary": "Die gesamte PWA folgt jetzt deiner persönlichen Sprachwahl – einschließlich Login, Scanner, Einstellungen, Fehlermeldungen und Push-Mitteilungen.",
        "highlights": [
            "Deutsch und Englisch mit persönlicher, geräteübergreifender Sprachwahl",
            "Lokalisierte Zahlen, Datumsangaben, API-Fehler und Benachrichtigungen",
            "Automatische Vollständigkeitsprüfung schützt neue Funktionen vor fehlenden Übersetzungen",
        ],
    },
    "en": {
        "version": "0.8.22",
        "title": "Vorrio now speaks German and English",
        "summary": "The entire PWA now follows your personal language choice, including sign-in, scanner, settings, errors and push notifications.",
        "highlights": [
            "German and English with a personal language choice synced across devices",
            "Localized numbers, dates, API errors and notifications",
            "Automated completeness checks protect new features from missing translations",
        ],
    },
}


def _api_token_required_scope(path: str, method: str) -> str | None:
    if path == "/api/v1/status" and method == "GET":
        return "status:read"
    if path.startswith("/api/v1/catalog/") and method == "GET":
        return "catalog:read"
    if path.startswith("/api/v1/stock/") and method == "GET":
        return "stock:read"
    if path == "/api/v1/shopping-list" or path.startswith("/api/v1/shopping-list/"):
        return "shopping:read" if method == "GET" else "shopping:write"
    if path.startswith("/api/v1/scans/"):
        return "scans:read" if method == "GET" else "scans:write"
    return None


def _public_user(principal: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(principal["user_id"]),
        "display_name": str(principal["display_name"]),
        "email": principal.get("email"),
        "role": str(principal["role"]),
        "household_id": str(principal["household_id"]),
        "household_name": str(principal["household_name"]),
        "owner_setup_complete": bool(principal["owner_setup_complete"]),
        "preferred_locale": database.get_user_locale(str(principal["user_id"])),
    }


def _experience_state(user_id: str) -> dict[str, Any]:
    stored = database.get_user_experience(user_id)
    onboarding_completed = bool(stored["onboarding_completed_at"])
    last_acknowledged_version = stored["last_acknowledged_version"]
    return {
        "current_version": app.version,
        "onboarding_completed": onboarding_completed,
        "onboarding_required": not onboarding_completed,
        "last_acknowledged_version": last_acknowledged_version,
        "release_notes_pending": bool(
            onboarding_completed and last_acknowledged_version != app.version
        ),
        "release": {
            **CURRENT_RELEASE[database.get_user_locale(user_id)],
            "version": app.version,
        },
    }


def _issue_auth_session(
    request: Request,
    identity: dict[str, Any],
    source_hash: str,
    authentication_method: str = "password",
    authentication_is_recent: bool = True,
) -> dict[str, Any]:
    session, token = database.create_auth_session(
        user_id=str(identity["user_id"]),
        household_id=str(identity["household_id"]),
        device_name=browser_device_name(request.headers.get("user-agent")),
        source_hash=source_hash,
        max_age_seconds=SESSION_MAX_AGE_SECONDS,
        authentication_method=authentication_method,
    )
    request.session.clear()
    request.session["authenticated"] = True
    request.session["session_token"] = token
    principal = {**identity, "session_id": session["id"]}
    if not authentication_is_recent:
        database.mark_session_authentication_stale(session["id"], authentication_method)
        principal["authenticated_at"] = "1970-01-01T00:00:00+00:00"
        principal["authentication_method"] = authentication_method
    return principal


def _password_valid(identity: dict[str, Any], password: str) -> bool:
    identity_hash = str(identity.get("password_hash") or "")
    stored_hash = database.get_setting("auth.password_hash")
    return (
        bool(identity_hash and verify_password(password, identity_hash))
        or bool(
            identity.get("role") == "owner"
            and not identity_hash
            and config.app_password
            and secrets.compare_digest(password, config.app_password)
        )
        or bool(
            not identity_hash
            and stored_hash
            and verify_password(password, stored_hash)
        )
    )


def _totp_secret(record: dict[str, Any]) -> str:
    try:
        return str(secret_store.decrypt_json(str(record["secret_encrypted"]))["secret"])
    except (KeyError, TypeError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail="TOTP-Konfiguration kann nicht gelesen werden") from exc


def _verify_second_factor(user_id: str, code: str) -> str | None:
    record = database.get_totp_credential(user_id)
    if record and bool(record["enabled"]):
        step = verify_totp_step(
            _totp_secret(record), code, record.get("last_used_step")
        )
        if step is not None and database.record_totp_step(user_id, step):
            return "totp"
    if database.consume_recovery_code(user_id, recovery_code_hash(code)):
        return "recovery_code"
    return None


def _recent_authentication(principal: dict[str, Any]) -> tuple[bool, str | None]:
    authenticated_at = principal.get("authenticated_at")
    if not authenticated_at:
        return False, None
    try:
        timestamp = datetime.fromisoformat(str(authenticated_at))
    except ValueError:
        return False, None
    until = timestamp + timedelta(seconds=RECENT_AUTH_SECONDS)
    return datetime.now(UTC) < until, until.isoformat(timespec="seconds")


def _require_recent_auth(principal: dict[str, Any]) -> None:
    recent, _ = _recent_authentication(principal)
    if not recent:
        raise HTTPException(
            status_code=428,
            detail="Bitte bestätige zuerst noch einmal deine Identität",
        )


def _passkey_public(row: dict[str, Any]) -> dict[str, Any]:
    try:
        transports = json.loads(str(row.get("transports_json") or "[]"))
    except json.JSONDecodeError:
        transports = []
    return {
        "id": str(row["id"]),
        "name": str(row["name"]),
        "device_type": str(row["device_type"]),
        "backed_up": bool(row["backed_up"]),
        "transports": transports if isinstance(transports, list) else [],
        "created_at": str(row["created_at"]),
        "last_used_at": row.get("last_used_at"),
    }


def _security_state(principal: dict[str, Any]) -> dict[str, Any]:
    recent, recent_until = _recent_authentication(principal)
    totp = database.get_totp_credential(str(principal["user_id"]))
    return {
        "passkeys": [
            _passkey_public(row)
            for row in database.list_webauthn_credentials(str(principal["user_id"]))
        ],
        "totp_enabled": bool(totp and totp["enabled"]),
        "recovery_codes_remaining": database.recovery_code_count(str(principal["user_id"])),
        "recent_authentication": recent,
        "recent_authentication_until": recent_until if recent else None,
        "secure_context_required": True,
    }


def _request_webauthn_context(request: Request, supplied_origin: str) -> tuple[str, str]:
    try:
        return webauthn_context(
            supplied_origin=supplied_origin,
            request_origin=request.headers.get("origin"),
            allowed_origins=config.allowed_origins,
            public_url=config.public_url,
        )
    except WebAuthnContextError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _current_principal(request: Request) -> dict[str, Any] | None:
    authorization = request.headers.get("authorization")
    if authorization:
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip():
            return None
        principal = database.resolve_api_token(token.strip())
        if not principal:
            return None
        principal["auth_type"] = "api_token"
        request.state.authentication_kind = "api_token"
        request.state.api_token_id = principal["api_token_id"]
        return principal

    token = request.session.get("session_token")
    if isinstance(token, str) and token:
        principal = database.resolve_auth_session(token)
        if principal:
            request.session["authenticated"] = True
            principal["auth_type"] = "session"
            request.state.authentication_kind = "session"
            return principal
        request.session.clear()
        return None

    # Signed 0.8.8 cookies are upgraded in place. This keeps existing private
    # installations logged in while introducing server-side revocation.
    if request.session.get("authenticated") is True:
        identity = database.ensure_owner_identity(
            database.get_setting("auth.password_hash")
        )
        principal = _issue_auth_session(
            request,
            identity,
            request_source_fingerprint(request, config.secret_key),
            "legacy_session",
            False,
        )
        database.add_audit_event(
            category="authentication",
            action="legacy_session_upgrade",
            outcome="success",
            source_hash=request_source_fingerprint(request, config.secret_key),
            details={"user_id": identity["user_id"]},
        )
        principal["auth_type"] = "session"
        request.state.authentication_kind = "session"
        return principal
    return None


def _authorize_request(request: Request, principal: dict[str, Any]) -> None:
    role = str(principal["role"])
    route = request.scope.get("route")
    path = str(getattr(route, "path", request.url.path))
    method = request.method.upper()

    if principal.get("auth_type") == "api_token":
        required_scope = _api_token_required_scope(path, method)
        if not required_scope:
            raise HTTPException(
                status_code=403,
                detail="API-Tokens dürfen diesen Endpunkt nicht verwenden",
            )
        if required_scope not in set(principal.get("api_token_scopes") or []):
            raise HTTPException(
                status_code=403,
                detail=f"Dem API-Token fehlt die Berechtigung {required_scope}",
            )

    if role == "owner":
        return

    if path.startswith("/api/v1/auth/"):
        return
    if path.startswith("/api/v1/notifications/"):
        return
    if path.startswith("/api/v1/privacy/") or path.startswith("/api/v1/operations/"):
        raise HTTPException(status_code=403, detail="Nur der Owner darf Datenschutz- und Betriebsdaten verwalten")
    if path == "/api/v1/insights/budget/settings" and method == "PUT" and role != "admin":
        raise HTTPException(status_code=403, detail="Nur Owner und Admins dürfen das Haushaltsbudget ändern")
    if path.startswith("/api/v1/settings") or path.startswith("/api/v1/integrations/"):
        raise HTTPException(status_code=403, detail="Dafür fehlen dir die erforderlichen Rechte")
    if path.startswith("/api/v1/grocy/"):
        raise HTTPException(status_code=403, detail="Dafür fehlen dir die erforderlichen Rechte")
    if path.startswith("/api/v1/catalog/") and method != "GET" and role not in {"admin"}:
        raise HTTPException(status_code=403, detail="Dafür fehlen dir die erforderlichen Rechte")
    if role == "viewer" and method != "GET":
        raise HTTPException(status_code=403, detail="Dieser Zugang ist schreibgeschützt")


def require_auth(request: Request) -> dict[str, Any]:
    principal = _current_principal(request)
    if not principal:
        headers = {"WWW-Authenticate": "Bearer"} if request.headers.get("authorization") else None
        raise HTTPException(status_code=401, detail="Bitte anmelden", headers=headers)
    _authorize_request(request, principal)
    return principal


def get_grocy_client(*, require_enabled: bool = True) -> GrocyClient:
    settings = settings_service.get_private()["grocy"]
    if require_enabled and not settings.get("enabled"):
        raise HTTPException(status_code=409, detail="Der Grocy-Connector ist deaktiviert")
    if not settings.get("url") or not settings.get("api_key"):
        raise HTTPException(status_code=409, detail="Grocy ist noch nicht verbunden")
    return GrocyClient(settings["url"], settings["api_key"])


@app.get("/api/health", tags=["System"], summary="Check instance health", response_model=HealthResponse)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/readiness",
    tags=["System"],
    summary="Check deployment readiness",
    response_model=ReadinessResponse,
)
async def readiness() -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(check_id: str, state: str, message: str) -> None:
        checks.append({"id": check_id, "status": state, "message": message})

    database_ready = database.ping()
    add(
        "database",
        "pass" if database_ready else "fail",
        "Die lokale Datenbank ist erreichbar"
        if database_ready
        else "Die lokale Datenbank ist nicht erreichbar",
    )
    secret_is_safe = is_safe_secret_key(config.secret_key)
    add(
        "session_secret",
        "pass" if secret_is_safe else "fail",
        "Ein eigenes Session-Geheimnis ist gesetzt"
        if secret_is_safe
        else "APP_SECRET_KEY muss mindestens 32 Zeichen lang und individuell sein",
    )
    wildcard_hosts = "*" in config.trusted_hosts
    add(
        "trusted_hosts",
        "fail"
        if wildcard_hosts and config.deployment_profile == "public_https"
        else "warn"
        if wildcard_hosts
        else "pass",
        "Hostnamen sind explizit eingeschränkt"
        if not wildcard_hosts
        else "Im LAN sind alle Hostnamen erlaubt; vor externer Nutzung einschränken",
    )
    exposure_failures = public_exposure_failures(config)
    proxy_failure = any(
        reason.startswith("forwarded_proxy_") for reason in exposure_failures
    )
    wildcard_proxy = config.forwarded_allow_ips == "*"
    add(
        "forwarded_headers",
        "fail" if wildcard_proxy or proxy_failure else "pass",
        "Forwarded-Header werden nur von konfigurierten Proxys akzeptiert"
        if not wildcard_proxy and not proxy_failure
        else "FORWARDED_ALLOW_IPS muss konkrete Proxy-IP-Adressen oder -Netze enthalten",
    )
    needs_https = config.deployment_profile != "lan"
    add(
        "secure_cookie",
        "fail" if needs_https and not config.session_https_only else "pass",
        "Secure-Cookies sind für das HTTPS-Profil aktiv"
        if config.session_https_only
        else "HTTP-Cookies sind ausschließlich im privaten LAN-Profil vorgesehen",
    )
    has_https_url = config.public_url.startswith("https://")
    add(
        "canonical_url",
        "fail" if needs_https and not has_https_url else "pass",
        "Die kanonische HTTPS-URL ist gesetzt"
        if has_https_url
        else "Im LAN-Profil ist keine PUBLIC_URL erforderlich",
    )
    if config.deployment_profile == "public_https":
        add(
            "public_exposure",
            "fail" if exposure_failures else "pass",
            "Öffentlicher Betrieb ist explizit bestätigt und alle Laufzeitbedingungen sind erfüllt"
            if not exposure_failures
            else "Öffentlicher Betrieb ist gesperrt: " + ", ".join(exposure_failures),
        )
    else:
        add(
            "public_exposure",
            "pass",
            "Die Instanz ist als LAN- oder privater HTTPS-Dienst konfiguriert",
        )

    states = {check["status"] for check in checks}
    overall = "blocked" if "fail" in states else "degraded" if "warn" in states else "ready"
    return {
        "status": overall,
        "profile": config.deployment_profile,
        "checks": checks,
    }


@app.post("/api/v1/auth/login", tags=["Authentication"], summary="Create a household session", response_model=AuthenticationResponse)
async def login(payload: LoginRequest, request: Request) -> dict[str, Any]:
    source_hash = request_source_fingerprint(request, config.secret_key)
    failures = database.auth_failure_count(
        source_hash, config.login_window_seconds
    )
    if failures >= config.login_max_failures:
        database.add_audit_event(
            category="authentication",
            action="login",
            outcome="blocked",
            source_hash=source_hash,
            details={"reason": "rate_limit"},
        )
        raise HTTPException(
            status_code=429,
            detail="Zu viele Anmeldeversuche. Bitte später erneut versuchen",
            headers={"Retry-After": str(config.login_window_seconds)},
        )
    stored_hash = database.get_setting("auth.password_hash")
    if config.app_password or stored_hash:
        database.ensure_owner_identity(stored_hash)
    identity = database.get_login_identity(payload.identifier)
    valid = bool(identity) and _password_valid(identity, payload.password)
    if not valid:
        database.record_auth_failure(source_hash)
        database.add_audit_event(
            category="authentication",
            action="login",
            outcome="failure",
            source_hash=source_hash,
        )
        raise HTTPException(status_code=401, detail="Anmeldung nicht möglich")
    totp = database.get_totp_credential(str(identity["user_id"]))
    if totp and bool(totp["enabled"]):
        challenge = database.create_login_challenge(
            str(identity["user_id"]), source_hash
        )
        return {
            "authenticated": False,
            "needs_setup": False,
            "identifier_required": database.active_user_count() > 1,
            "mfa_required": True,
            "mfa_challenge": challenge,
            "mfa_methods": ["totp", "recovery_code"],
        }
    database.clear_auth_failures(source_hash)
    database.add_audit_event(
        category="authentication",
        action="login",
        outcome="success",
        source_hash=source_hash,
        details={"user_id": identity["user_id"]},
    )
    principal = _issue_auth_session(request, identity, source_hash)
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": not bool(principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal),
    }


@app.post(
    "/api/v1/auth/mfa/verify",
    tags=["Authentication"],
    summary="Finish a password login with a second factor",
    response_model=AuthenticationResponse,
)
async def verify_login_mfa(payload: MfaVerifyInput, request: Request) -> dict[str, Any]:
    source_hash = request_source_fingerprint(request, config.secret_key)
    if database.auth_failure_count(source_hash, config.login_window_seconds) >= config.login_max_failures:
        raise HTTPException(
            status_code=429,
            detail="Zu viele Anmeldeversuche. Bitte später erneut versuchen",
            headers={"Retry-After": str(config.login_window_seconds)},
        )
    identity = database.resolve_login_challenge(payload.challenge, source_hash)
    method = (
        _verify_second_factor(str(identity["user_id"]), payload.code)
        if identity
        else None
    )
    if not identity or not method:
        database.record_auth_failure(source_hash)
        database.add_audit_event(
            category="authentication",
            action="mfa_login",
            outcome="failure",
            source_hash=source_hash,
        )
        raise HTTPException(status_code=401, detail="Code ist ungültig oder bereits verwendet")
    if not database.consume_login_challenge(payload.challenge):
        raise HTTPException(status_code=401, detail="Anmeldung ist abgelaufen")
    database.clear_auth_failures(source_hash)
    principal = _issue_auth_session(request, identity, source_hash, method)
    database.add_audit_event(
        category="authentication",
        action="mfa_login",
        outcome="success",
        source_hash=source_hash,
        details={"user_id": principal["user_id"], "method": method},
    )
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": not bool(principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal),
    }


@app.post(
    "/api/v1/auth/recovery",
    tags=["Authentication"],
    summary="Recover an account with a single-use recovery code",
    response_model=AuthenticationResponse,
)
async def recovery_login(payload: RecoveryLoginInput, request: Request) -> dict[str, Any]:
    source_hash = request_source_fingerprint(request, config.secret_key)
    if database.auth_failure_count(source_hash, config.login_window_seconds) >= config.login_max_failures:
        raise HTTPException(status_code=429, detail="Zu viele Anmeldeversuche. Bitte später erneut versuchen")
    identity = database.get_login_identity(payload.identifier)
    valid = bool(identity) and database.consume_recovery_code(
        str(identity["user_id"]), recovery_code_hash(payload.code)
    )
    if not valid:
        database.record_auth_failure(source_hash)
        database.add_audit_event(
            category="authentication",
            action="recovery_login",
            outcome="failure",
            source_hash=source_hash,
        )
        raise HTTPException(status_code=401, detail="Wiederherstellung nicht möglich")
    database.clear_auth_failures(source_hash)
    principal = _issue_auth_session(request, identity, source_hash, "recovery_code")
    database.add_audit_event(
        category="authentication",
        action="recovery_login",
        outcome="success",
        source_hash=source_hash,
        details={"user_id": principal["user_id"]},
    )
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": not bool(principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal),
    }


@app.post(
    "/api/v1/auth/passkeys/authentication/begin",
    tags=["Authentication"],
    summary="Start passwordless passkey authentication",
    response_model=WebAuthnOptionsResponse,
)
async def begin_passkey_authentication(
    payload: WebAuthnBeginInput, request: Request
) -> dict[str, Any]:
    origin, rp_id = _request_webauthn_context(request, payload.origin)
    options = generate_authentication_options(
        rp_id=rp_id,
        user_verification=UserVerificationRequirement.REQUIRED,
        timeout=120_000,
    )
    challenge_id = database.create_webauthn_challenge(
        challenge=options.challenge,
        ceremony="authentication",
        purpose="login",
        rp_id=rp_id,
        origin=origin,
    )
    return {"challenge_id": challenge_id, "options": json.loads(options_to_json(options))}


@app.post(
    "/api/v1/auth/passkeys/authentication/complete",
    tags=["Authentication"],
    summary="Complete passwordless passkey authentication",
    response_model=AuthenticationResponse,
)
async def complete_passkey_authentication(
    payload: WebAuthnCompleteInput, request: Request
) -> dict[str, Any]:
    source_hash = request_source_fingerprint(request, config.secret_key)
    if database.auth_failure_count(source_hash, config.login_window_seconds) >= config.login_max_failures:
        raise HTTPException(status_code=429, detail="Zu viele Anmeldeversuche. Bitte später erneut versuchen")
    challenge = database.consume_webauthn_challenge(
        payload.challenge_id, ceremony="authentication", purpose="login"
    )
    try:
        encoded_id = str(payload.credential.get("rawId") or payload.credential["id"])
        credential_id = base64url_to_bytes(encoded_id)
        stored = database.get_webauthn_credential(credential_id)
        if not challenge or not stored:
            raise InvalidAuthenticationResponse("unknown credential or challenge")
        verification = verify_authentication_response(
            credential=payload.credential,
            expected_challenge=bytes(challenge["challenge"]),
            expected_rp_id=str(challenge["rp_id"]),
            expected_origin=str(challenge["origin"]),
            credential_public_key=bytes(stored["public_key"]),
            credential_current_sign_count=int(stored["sign_count"]),
            require_user_verification=True,
        )
    except (InvalidAuthenticationResponse, KeyError, TypeError, ValueError) as exc:
        database.record_auth_failure(source_hash)
        database.add_audit_event(
            category="authentication",
            action="passkey_login",
            outcome="failure",
            source_hash=source_hash,
        )
        raise HTTPException(status_code=401, detail="Passkey-Anmeldung nicht möglich") from exc
    database.update_webauthn_credential(
        str(stored["id"]),
        int(verification.new_sign_count),
        str(getattr(verification.credential_device_type, "value", verification.credential_device_type)),
        bool(verification.credential_backed_up),
    )
    database.clear_auth_failures(source_hash)
    principal = _issue_auth_session(request, stored, source_hash, "passkey")
    database.add_audit_event(
        category="authentication",
        action="passkey_login",
        outcome="success",
        source_hash=source_hash,
        details={"user_id": principal["user_id"], "credential_id": stored["id"]},
    )
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": not bool(principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal),
    }


@app.get("/api/v1/auth/state", tags=["Authentication"], summary="Read setup and session state", response_model=AuthenticationResponse)
async def auth_state(request: Request) -> dict[str, Any]:
    needs_setup = not config.app_password and not database.get_setting("auth.password_hash")
    principal = None if needs_setup else _current_principal(request)
    return {
        "authenticated": principal is not None,
        "needs_setup": needs_setup,
        "needs_owner_setup": bool(principal and not principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal) if principal else None,
    }


@app.post("/api/v1/auth/setup", tags=["Authentication"], summary="Complete first-run setup", response_model=AuthenticationResponse)
async def setup(payload: SetupRequest, request: Request) -> dict[str, Any]:
    if config.app_password or database.get_setting("auth.password_hash"):
        raise HTTPException(status_code=409, detail="Die Ersteinrichtung ist bereits abgeschlossen")
    password_hash = hash_password(payload.password)
    database.put_setting("auth.password_hash", password_hash)
    identity = database.ensure_owner_identity(password_hash)
    database.update_user_locale(str(identity["user_id"]), payload.preferred_locale)
    database.localize_seeded_master_data(payload.preferred_locale)
    if payload.display_name:
        identity = database.update_owner_profile(
            str(identity["user_id"]),
            display_name=payload.display_name,
            email=None,
        ) or identity
    source_hash = request_source_fingerprint(request, config.secret_key)
    database.add_audit_event(
        category="authentication",
        action="first_run_setup",
        outcome="success",
        source_hash=source_hash,
        details={"user_id": identity["user_id"]},
    )
    principal = _issue_auth_session(request, identity, source_hash)
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": not bool(principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal),
    }


@app.get("/api/v1/auth/me", tags=["Authentication"], summary="Validate the current session", response_model=AuthenticationResponse)
async def me(principal: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": not bool(principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal),
    }


@app.get(
    "/api/v1/experience",
    tags=["Experience"],
    summary="Read personal onboarding and release-note state",
    response_model=ExperienceStateResponse,
)
async def get_experience(
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    return _experience_state(str(principal["user_id"]))


@app.put(
    "/api/v1/experience",
    tags=["Experience"],
    summary="Complete onboarding or acknowledge the current release",
    response_model=ExperienceStateResponse,
)
async def update_experience(
    payload: ExperienceUpdateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    if not payload.complete_onboarding and not payload.acknowledge_current_version:
        raise HTTPException(status_code=422, detail="Keine Änderung ausgewählt")
    database.update_user_experience(
        str(principal["user_id"]),
        complete_onboarding=payload.complete_onboarding,
        acknowledged_version=(
            app.version if payload.acknowledge_current_version else None
        ),
    )
    database.add_audit_event(
        category="experience",
        action="experience_update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "user_id": principal["user_id"],
            "onboarding_completed": payload.complete_onboarding,
            "release_acknowledged": payload.acknowledge_current_version,
            "version": app.version if payload.acknowledge_current_version else None,
        },
    )
    return _experience_state(str(principal["user_id"]))


@app.get(
    "/api/v1/auth/security",
    tags=["Authentication"],
    summary="Read passkey, TOTP and recovery status",
    response_model=SecurityStateResponse,
)
async def auth_security(
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    return _security_state(principal)


@app.post(
    "/api/v1/auth/reauthenticate",
    tags=["Authentication"],
    summary="Confirm identity before a sensitive change",
    response_model=SecurityStateResponse,
)
async def reauthenticate(
    payload: ReauthenticateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    source_hash = request_source_fingerprint(request, config.secret_key)
    identity = database.get_identity_by_user_id(str(principal["user_id"]))
    if not identity or not _password_valid(identity, payload.password):
        database.record_auth_failure(source_hash)
        raise HTTPException(status_code=401, detail="Sicherheitsbestätigung fehlgeschlagen")
    totp = database.get_totp_credential(str(principal["user_id"]))
    method = "password"
    if totp and bool(totp["enabled"]):
        method = _verify_second_factor(str(principal["user_id"]), payload.code or "") or ""
        if not method:
            database.record_auth_failure(source_hash)
            raise HTTPException(status_code=401, detail="Zusätzlicher Code ist ungültig oder fehlt")
    if not database.mark_session_reauthenticated(str(principal["session_id"]), method):
        raise HTTPException(status_code=401, detail="Sitzung ist nicht mehr gültig")
    database.clear_auth_failures(source_hash)
    refreshed = {**principal, "authenticated_at": now_iso(), "authentication_method": method}
    database.add_audit_event(
        category="authentication",
        action="reauthenticate",
        outcome="success",
        source_hash=source_hash,
        details={"user_id": principal["user_id"], "method": method},
    )
    return _security_state(refreshed)


@app.put(
    "/api/v1/auth/password",
    tags=["Authentication"],
    summary="Change the current account password",
    response_model=SecurityStateResponse,
)
async def change_password(
    payload: PasswordChangeInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    if not database.update_password(
        str(principal["user_id"]), hash_password(payload.password), str(principal["session_id"])
    ):
        raise HTTPException(status_code=404, detail="Konto nicht gefunden")
    database.add_audit_event(
        category="authentication",
        action="password_change",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"], "other_sessions_revoked": True},
    )
    return _security_state(principal)


@app.post(
    "/api/v1/auth/totp/setup",
    tags=["Authentication"],
    summary="Create a pending authenticator-app secret",
    response_model=TotpSetupResponse,
)
async def setup_totp(
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    current = database.get_totp_credential(str(principal["user_id"]))
    if current and bool(current["enabled"]):
        raise HTTPException(status_code=409, detail="Authenticator-App ist bereits aktiv")
    secret = generate_totp_secret()
    database.put_pending_totp(
        str(principal["user_id"]), secret_store.encrypt_json({"secret": secret})
    )
    account_name = str(principal.get("email") or principal["display_name"])
    uri = totp_provisioning_uri(secret, account_name)
    return {"secret": secret, "provisioning_uri": uri, "qr_data_uri": totp_qr_data_uri(uri)}


@app.post(
    "/api/v1/auth/totp/enable",
    tags=["Authentication"],
    summary="Verify and enable an authenticator app",
    response_model=TotpEnableResponse,
)
async def enable_totp(
    payload: TotpVerifyInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    user_id = str(principal["user_id"])
    record = database.get_totp_credential(user_id)
    if not record or bool(record["enabled"]):
        raise HTTPException(status_code=409, detail="TOTP-Einrichtung wurde nicht begonnen")
    step = verify_totp_step(_totp_secret(record), payload.code, None)
    if step is None or not database.enable_totp(user_id, step):
        raise HTTPException(status_code=400, detail="Der sechsstellige Code ist nicht gültig")
    codes: list[str] = []
    if database.recovery_code_count(user_id) == 0:
        codes = generate_recovery_codes()
        database.replace_recovery_codes(user_id, [recovery_code_hash(code) for code in codes])
    database.add_audit_event(
        category="authentication",
        action="totp_enable",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": user_id},
    )
    return {"enabled": True, "recovery_codes": codes}


@app.delete(
    "/api/v1/auth/totp",
    tags=["Authentication"],
    summary="Disable authenticator-app verification",
    response_model=SecurityStateResponse,
)
async def disable_totp(
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    if not database.delete_totp(str(principal["user_id"])):
        raise HTTPException(status_code=404, detail="Authenticator-App ist nicht aktiv")
    database.add_audit_event(
        category="authentication",
        action="totp_disable",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"]},
    )
    return _security_state(principal)


@app.post(
    "/api/v1/auth/recovery-codes",
    tags=["Authentication"],
    summary="Replace all single-use recovery codes",
    response_model=RecoveryCodesResponse,
)
async def regenerate_recovery_codes(
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    codes = generate_recovery_codes()
    database.replace_recovery_codes(
        str(principal["user_id"]), [recovery_code_hash(code) for code in codes]
    )
    database.add_audit_event(
        category="authentication",
        action="recovery_codes_replace",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"], "count": len(codes)},
    )
    return {"codes": codes, "remaining": len(codes)}


@app.post(
    "/api/v1/auth/passkeys/registration/begin",
    tags=["Authentication"],
    summary="Start passkey registration",
    response_model=WebAuthnOptionsResponse,
)
async def begin_passkey_registration(
    payload: WebAuthnBeginInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    origin, rp_id = _request_webauthn_context(request, payload.origin)
    credentials = database.list_webauthn_credentials(str(principal["user_id"]))
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name="Vorrio",
        user_id=str(principal["user_id"]).encode("utf-8"),
        user_name=str(principal.get("email") or principal["display_name"]),
        user_display_name=str(principal["display_name"]),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=bytes(row["credential_id"]))
            for row in credentials
        ],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        timeout=120_000,
    )
    challenge_id = database.create_webauthn_challenge(
        challenge=options.challenge,
        ceremony="registration",
        purpose="registration",
        rp_id=rp_id,
        origin=origin,
        user_id=str(principal["user_id"]),
        session_id=str(principal["session_id"]),
    )
    return {"challenge_id": challenge_id, "options": json.loads(options_to_json(options))}


@app.post(
    "/api/v1/auth/passkeys/registration/complete",
    tags=["Authentication"],
    summary="Verify and save a passkey",
    response_model=PasskeyResponse,
)
async def complete_passkey_registration(
    payload: WebAuthnCompleteInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    challenge = database.consume_webauthn_challenge(
        payload.challenge_id,
        ceremony="registration",
        purpose="registration",
        session_id=str(principal["session_id"]),
    )
    if not challenge or challenge.get("user_id") != principal["user_id"]:
        raise HTTPException(status_code=400, detail="Passkey-Einrichtung ist abgelaufen")
    try:
        verification = verify_registration_response(
            credential=payload.credential,
            expected_challenge=bytes(challenge["challenge"]),
            expected_rp_id=str(challenge["rp_id"]),
            expected_origin=str(challenge["origin"]),
            require_user_verification=True,
        )
        response = payload.credential.get("response") or {}
        transports = response.get("transports") if isinstance(response, dict) else []
        if not isinstance(transports, list):
            transports = []
        stored = database.add_webauthn_credential(
            user_id=str(principal["user_id"]),
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=int(verification.sign_count),
            device_type=str(getattr(verification.credential_device_type, "value", verification.credential_device_type)),
            backed_up=bool(verification.credential_backed_up),
            transports=[str(item) for item in transports],
            name=payload.name or browser_device_name(request.headers.get("user-agent")),
        )
    except InvalidRegistrationResponse as exc:
        raise HTTPException(status_code=400, detail="Passkey konnte nicht bestätigt werden") from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Dieser Passkey ist bereits gespeichert") from exc
    database.add_audit_event(
        category="authentication",
        action="passkey_add",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"], "credential_id": stored["id"]},
    )
    return _passkey_public(stored)


@app.delete(
    "/api/v1/auth/passkeys/{credential_id}",
    tags=["Authentication"],
    summary="Delete one passkey",
    response_model=SecurityStateResponse,
)
async def delete_passkey(
    credential_id: str,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    if not database.delete_webauthn_credential(str(principal["user_id"]), credential_id):
        raise HTTPException(status_code=404, detail="Passkey nicht gefunden")
    database.add_audit_event(
        category="authentication",
        action="passkey_delete",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"], "credential_id": credential_id},
    )
    return _security_state(principal)


@app.patch(
    "/api/v1/auth/profile",
    tags=["Authentication"],
    summary="Complete or update the owner profile",
    description=(
        "Names the first owner created from the former household password. "
        "The optional email is stored locally and identifies the account during recovery-code login."
    ),
    response_model=AuthenticationResponse,
)
async def update_owner_profile(
    payload: OwnerProfileUpdateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    if principal["role"] != "owner":
        raise HTTPException(status_code=403, detail="Nur der Owner darf dieses Profil ändern")
    _require_recent_auth(principal)
    try:
        updated = database.update_owner_profile(
            str(principal["user_id"]),
            display_name=payload.display_name,
            email=payload.email,
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Diese E-Mail-Adresse wird bereits verwendet") from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Owner-Profil nicht gefunden")
    updated["session_id"] = principal["session_id"]
    database.add_audit_event(
        category="identity",
        action="owner_profile_update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"]},
    )
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": False,
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(updated),
    }


@app.patch(
    "/api/v1/auth/preferences",
    tags=["Authentication"],
    summary="Update personal interface preferences",
    description=(
        "Stores the signed-in user's supported BCP 47 interface locale. "
        "The preference is personal and does not alter household product data, "
        "currency or installation timezone."
    ),
    response_model=AuthenticationResponse,
)
async def update_user_preferences(
    payload: UserPreferencesUpdateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    if not database.update_user_locale(
        str(principal["user_id"]), payload.preferred_locale
    ):
        raise HTTPException(status_code=404, detail="Benutzerkonto nicht gefunden")
    database.add_audit_event(
        category="identity",
        action="user_locale_update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "user_id": principal["user_id"],
            "preferred_locale": payload.preferred_locale,
        },
    )
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": not bool(principal["owner_setup_complete"]),
        "identifier_required": database.active_user_count() > 1,
        "user": _public_user(principal),
    }


def _require_member_manager(principal: dict[str, Any]) -> None:
    if principal["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Nur Owner und Admins verwalten Mitglieder")


@app.get(
    "/api/v1/auth/members",
    tags=["Authentication"],
    summary="List household members",
    response_model=list[HouseholdMemberResponse],
)
async def household_members(
    principal: dict[str, Any] = Depends(require_auth),
) -> list[dict[str, Any]]:
    _require_member_manager(principal)
    return database.list_household_members(str(principal["household_id"]))


@app.patch(
    "/api/v1/auth/members/{user_id}",
    tags=["Authentication"],
    summary="Change a member role or access state",
    description=(
        "Owner membership cannot be changed through this endpoint. Admins may "
        "manage members and viewers but cannot grant or manage admin access."
    ),
    response_model=HouseholdMemberResponse,
)
async def update_household_member(
    user_id: str,
    payload: HouseholdMemberUpdateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_member_manager(principal)
    _require_recent_auth(principal)
    members = database.list_household_members(str(principal["household_id"]))
    target = next((member for member in members if member["id"] == user_id), None)
    if not target or target["role"] == "owner":
        raise HTTPException(status_code=404, detail="Mitglied nicht gefunden")
    if user_id == principal["user_id"]:
        raise HTTPException(status_code=409, detail="Den eigenen Zugang hier nicht ändern")
    if principal["role"] == "admin" and (
        target["role"] == "admin" or payload.role == "admin"
    ):
        raise HTTPException(status_code=403, detail="Nur der Owner verwaltet Admin-Rechte")
    updated = database.update_household_member(
        household_id=str(principal["household_id"]),
        user_id=user_id,
        role=payload.role,
        active=payload.active,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Mitglied nicht gefunden")
    database.add_audit_event(
        category="identity",
        action="member_update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "actor_user_id": principal["user_id"],
            "target_user_id": user_id,
            "role": payload.role,
            "active": payload.active,
        },
    )
    return updated


@app.get(
    "/api/v1/auth/invitations",
    tags=["Authentication"],
    summary="List active household invitations",
    response_model=list[HouseholdInvitationResponse],
)
async def household_invitations(
    principal: dict[str, Any] = Depends(require_auth),
) -> list[dict[str, Any]]:
    _require_member_manager(principal)
    return database.list_household_invitations(str(principal["household_id"]))


@app.post(
    "/api/v1/auth/invitations",
    tags=["Authentication"],
    summary="Create a single-use household invitation",
    description=(
        "Returns the raw invitation token exactly once. Only its SHA-256 hash is "
        "stored. The inviter shares the same-origin PWA link privately."
    ),
    response_model=HouseholdInvitationResponse,
)
async def create_household_invitation(
    payload: HouseholdInvitationCreateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_member_manager(principal)
    _require_recent_auth(principal)
    if not principal.get("email"):
        raise HTTPException(
            status_code=409,
            detail="Bitte zuerst deine eigene Login-E-Mail im Owner-Profil speichern",
        )
    if principal["role"] == "admin" and payload.role == "admin":
        raise HTTPException(status_code=403, detail="Nur der Owner darf Admins einladen")
    try:
        invitation, token = database.create_household_invitation(
            household_id=str(principal["household_id"]),
            invited_by_user_id=str(principal["user_id"]),
            display_name=payload.display_name,
            email=payload.email,
            role=payload.role,
            expires_hours=payload.expires_hours,
        )
    except ValueError as exc:
        detail = (
            "Für diese E-Mail besteht bereits ein Mitglied"
            if str(exc) == "member_exists"
            else "Für diese E-Mail ist bereits eine Einladung offen"
        )
        raise HTTPException(status_code=409, detail=detail) from exc
    database.add_audit_event(
        category="identity",
        action="invitation_create",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "actor_user_id": principal["user_id"],
            "invitation_id": invitation["id"],
            "role": invitation["role"],
        },
    )
    return {**invitation, "invite_token": token}


@app.delete(
    "/api/v1/auth/invitations/{invitation_id}",
    tags=["Authentication"],
    summary="Revoke an unused household invitation",
    response_model=SessionRevocationResponse,
)
async def revoke_household_invitation(
    invitation_id: str,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_member_manager(principal)
    _require_recent_auth(principal)
    if not database.revoke_household_invitation(
        str(principal["household_id"]), invitation_id
    ):
        raise HTTPException(status_code=404, detail="Einladung nicht gefunden")
    database.add_audit_event(
        category="identity",
        action="invitation_revoke",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"invitation_id": invitation_id},
    )
    return {"revoked": 1, "authenticated": True}


@app.get(
    "/api/v1/auth/invitations/{token}",
    tags=["Authentication"],
    summary="Read a single-use invitation",
    response_model=HouseholdInvitationPublicResponse,
)
async def household_invitation(token: str) -> dict[str, Any]:
    invitation = database.get_household_invitation(token)
    if not invitation or not invitation["valid"]:
        raise HTTPException(status_code=410, detail="Diese Einladung ist nicht mehr gültig")
    return {
        "valid": True,
        "household_name": invitation["household_name"],
        "display_name": invitation["display_name"],
        "email": invitation["email"],
        "role": invitation["role"],
        "expires_at": invitation["expires_at"],
    }


@app.post(
    "/api/v1/auth/invitations/{token}/accept",
    tags=["Authentication"],
    summary="Accept an invitation and create the member account",
    response_model=AuthenticationResponse,
)
async def accept_household_invitation(
    token: str,
    payload: HouseholdInvitationAcceptInput,
    request: Request,
) -> dict[str, Any]:
    identity = database.accept_household_invitation(
        token,
        password_hash=hash_password(payload.password),
        preferred_locale=payload.preferred_locale,
    )
    if not identity:
        raise HTTPException(status_code=410, detail="Diese Einladung ist nicht mehr gültig")
    source_hash = request_source_fingerprint(request, config.secret_key)
    principal = _issue_auth_session(request, identity, source_hash)
    database.add_audit_event(
        category="identity",
        action="invitation_accept",
        outcome="success",
        source_hash=source_hash,
        details={"user_id": principal["user_id"], "role": principal["role"]},
    )
    return {
        "authenticated": True,
        "needs_setup": False,
        "needs_owner_setup": False,
        "identifier_required": True,
        "user": _public_user(principal),
    }


@app.get(
    "/api/v1/auth/sessions",
    tags=["Authentication"],
    summary="List active browser sessions",
    response_model=list[AuthSessionResponse],
)
async def auth_sessions(
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> list[dict[str, Any]]:
    return database.list_auth_sessions(
        str(principal["user_id"]), str(request.session["session_token"])
    )


@app.delete(
    "/api/v1/auth/sessions/{session_id}",
    tags=["Authentication"],
    summary="Revoke one browser session",
    response_model=SessionRevocationResponse,
)
async def revoke_auth_session(
    session_id: str,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    current = secrets.compare_digest(str(principal["session_id"]), session_id)
    if not database.revoke_auth_session(str(principal["user_id"]), session_id):
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")
    database.add_audit_event(
        category="authentication",
        action="session_revoke",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"session_id": session_id, "current": current},
    )
    if current:
        request.session.clear()
    return {"revoked": 1, "authenticated": not current}


@app.post(
    "/api/v1/auth/sessions/revoke-others",
    tags=["Authentication"],
    summary="Revoke every other browser session",
    response_model=SessionRevocationResponse,
)
async def revoke_other_auth_sessions(
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    revoked = database.revoke_other_auth_sessions(
        str(principal["user_id"]), str(request.session["session_token"])
    )
    database.add_audit_event(
        category="authentication",
        action="session_revoke_others",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"revoked": revoked},
    )
    return {"revoked": revoked, "authenticated": True}


@app.get(
    "/api/v1/auth/api-token-scopes",
    tags=["Authentication"],
    summary="List available automation-token scopes",
    response_model=list[ApiTokenScopeResponse],
)
async def api_token_scopes(
    principal: dict[str, Any] = Depends(require_auth),
) -> list[dict[str, str]]:
    if principal["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Nur Owner und Admins verwalten API-Tokens")
    locale = database.get_user_locale(str(principal["user_id"]))
    return [
        {"id": scope, "label": label, "description": description}
        for scope, (label, description) in API_TOKEN_SCOPES[locale].items()
    ]


@app.get(
    "/api/v1/auth/api-tokens",
    tags=["Authentication"],
    summary="List the current account's automation tokens",
    response_model=list[ApiTokenResponse],
)
async def api_tokens(
    principal: dict[str, Any] = Depends(require_auth),
) -> list[dict[str, Any]]:
    if principal["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Nur Owner und Admins verwalten API-Tokens")
    return database.list_api_tokens(str(principal["user_id"]))


@app.post(
    "/api/v1/auth/api-tokens",
    tags=["Authentication"],
    summary="Create a scoped automation token",
    description=(
        "Returns the raw bearer token exactly once. Vorrio stores only its SHA-256 "
        "hash. The token is restricted to the selected scopes and expires after at "
        "most 365 days."
    ),
    response_model=ApiTokenCreatedResponse,
)
async def create_api_token(
    payload: ApiTokenCreateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    if principal["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Nur Owner und Admins verwalten API-Tokens")
    _require_recent_auth(principal)
    token_record, raw_token = database.create_api_token(
        user_id=str(principal["user_id"]),
        household_id=str(principal["household_id"]),
        name=payload.name,
        scopes=list(payload.scopes),
        expires_days=payload.expires_days,
    )
    database.add_audit_event(
        category="authentication",
        action="api_token_create",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "api_token_id": token_record["id"],
            "scopes": token_record["scopes"],
            "expires_at": token_record["expires_at"],
        },
    )
    return {**token_record, "token": raw_token}


@app.delete(
    "/api/v1/auth/api-tokens/{token_id}",
    tags=["Authentication"],
    summary="Revoke one automation token",
    response_model=SessionRevocationResponse,
)
async def revoke_api_token(
    token_id: str,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    if principal["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Nur Owner und Admins verwalten API-Tokens")
    _require_recent_auth(principal)
    if not database.revoke_api_token_for_user(str(principal["user_id"]), token_id):
        raise HTTPException(status_code=404, detail="API-Token nicht gefunden")
    database.add_audit_event(
        category="authentication",
        action="api_token_revoke",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"api_token_id": token_id},
    )
    return {"revoked": 1, "authenticated": True}


@app.post("/api/v1/auth/logout", tags=["Authentication"], summary="End the current session", response_model=AuthenticationResponse)
async def logout(request: Request) -> dict[str, Any]:
    principal = _current_principal(request)
    token = request.session.get("session_token")
    was_authenticated = principal is not None
    if isinstance(token, str) and token:
        database.revoke_auth_token(token)
    request.session.clear()
    if was_authenticated:
        database.add_audit_event(
            category="authentication",
            action="logout",
            outcome="success",
            source_hash=request_source_fingerprint(request, config.secret_key),
        )
    return {"authenticated": False, "needs_setup": False, "needs_owner_setup": False}


@app.get(
    "/api/v1/notifications/state",
    tags=["Notifications"],
    summary="Read personal Web Push settings and devices",
    response_model=NotificationStateResponse,
)
async def notification_state(
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    return notification_service.state(
        str(principal["user_id"]), str(principal["household_id"])
    )


@app.put(
    "/api/v1/notifications/preferences",
    tags=["Notifications"],
    summary="Update personal stock notification preferences",
    response_model=NotificationStateResponse,
)
async def update_notification_preferences(
    payload: NotificationPreferencesInput,
    background_tasks: BackgroundTasks,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    state = notification_service.save_preferences(
        str(principal["user_id"]),
        str(principal["household_id"]),
        push_enabled=payload.push_enabled,
        low_stock_enabled=payload.low_stock_enabled,
        expiry_enabled=payload.expiry_enabled,
        expiry_days_before=payload.expiry_days_before,
    )
    database.add_audit_event(
        category="notifications",
        action="preferences_update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "user_id": principal["user_id"],
            "push_enabled": payload.push_enabled,
            "low_stock_enabled": payload.low_stock_enabled,
            "expiry_enabled": payload.expiry_enabled,
            "expiry_days_before": payload.expiry_days_before,
        },
    )
    if payload.push_enabled:
        background_tasks.add_task(notification_service.evaluate_and_send)
    return state


@app.post(
    "/api/v1/notifications/subscriptions",
    tags=["Notifications"],
    summary="Register or refresh one browser push device",
    response_model=PushSubscriptionResponse,
)
async def register_push_subscription(
    payload: PushSubscriptionCreateInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    try:
        endpoint = validate_public_push_url(str(payload.endpoint))
    except OutboundUrlError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    device_name = payload.device_name
    if device_name == "Vorrio-Gerät":
        device_name = browser_device_name(request.headers.get("user-agent"))
    try:
        subscription = notification_service.save_subscription(
            str(principal["user_id"]),
            str(principal["household_id"]),
            subscription={
                "endpoint": endpoint,
                "keys": payload.keys.model_dump(),
            },
            device_name=device_name,
        )
    except OutboundUrlError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    database.add_audit_event(
        category="notifications",
        action="push_device_register",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"], "subscription_id": subscription["id"]},
    )
    return subscription


@app.delete(
    "/api/v1/notifications/subscriptions/{subscription_id}",
    tags=["Notifications"],
    summary="Revoke one personal push device",
    response_model=SessionRevocationResponse,
)
async def revoke_push_subscription(
    subscription_id: str,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    if not notification_service.revoke_subscription(
        str(principal["user_id"]), subscription_id
    ):
        raise HTTPException(status_code=404, detail="Push-Gerät nicht gefunden")
    database.add_audit_event(
        category="notifications",
        action="push_device_revoke",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"user_id": principal["user_id"], "subscription_id": subscription_id},
    )
    return {"revoked": 1, "authenticated": True}


@app.post(
    "/api/v1/notifications/test",
    tags=["Notifications"],
    summary="Send a visible test notification to one personal device",
    response_model=NotificationDeliveryResponse,
)
async def test_push_notification(
    payload: NotificationTestInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, int]:
    try:
        result = await asyncio.to_thread(
            notification_service.send_test,
            str(principal["user_id"]),
            payload.subscription_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    database.add_audit_event(
        category="notifications",
        action="push_test",
        outcome="success" if result["delivered"] else "failure",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "user_id": principal["user_id"],
            "subscription_id": payload.subscription_id,
        },
    )
    return result


@app.get("/api/v1/status", tags=["System"], summary="Read instance and connector status", response_model=StatusResponse)
async def status(_: None = Depends(require_auth)) -> dict[str, Any]:
    settings = settings_service.get_public()
    private = settings_service.get_private()
    grocy_enabled = bool(private["grocy"].get("enabled"))
    grocy_configured = bool(private["grocy"].get("api_key"))
    grocy_connected = False
    if grocy_enabled and grocy_configured:
        try:
            await GrocyClient(
                private["grocy"]["url"], private["grocy"]["api_key"], timeout=3
            ).test()
            grocy_connected = True
        except (GrocyError, OSError):
            grocy_connected = False
    return {
        "grocy_configured": grocy_configured,
        "grocy_enabled": grocy_enabled,
        "grocy_connected": grocy_connected,
        "provider_configured": bool(
            private["provider"].get("model")
            and (
                private["provider"].get("api_key")
                or private["provider"].get("type") == "ollama"
            )
        ),
        "provider": settings["provider"]["type"],
        "catalog": database.catalog_summary(),
        "version": app.version,
    }


@app.get("/api/v1/settings", tags=["Settings"], summary="Read public settings", response_model=PublicSettingsResponse)
async def get_settings(_: None = Depends(require_auth)) -> dict[str, Any]:
    return settings_service.get_public()


@app.put("/api/v1/settings", tags=["Settings"], summary="Replace instance settings", response_model=PublicSettingsResponse)
async def save_settings(
    payload: SettingsInput, principal: dict[str, Any] = Depends(require_auth)
) -> dict[str, Any]:
    _require_recent_auth(principal)
    return settings_service.save(payload.model_dump())


@app.post("/api/v1/settings/test-grocy", tags=["Settings"], summary="Test the Grocy connector", response_model=ConnectionTestResponse)
async def test_grocy(_: None = Depends(require_auth)) -> dict[str, Any]:
    try:
        result = await get_grocy_client(require_enabled=False).test()
    except GrocyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"connected": True, "info": result}


@app.post("/api/v1/settings/test-provider", tags=["Settings"], summary="Test the selected analysis provider", response_model=ConnectionTestResponse)
async def provider_test(_: None = Depends(require_auth)) -> dict[str, Any]:
    try:
        return await test_provider(settings_service.get_private()["provider"])
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get(
    "/api/v1/privacy/export/preview",
    tags=["Privacy & Operations"],
    summary="Preview the portable household export",
    response_model=ExportPreviewResponse,
)
async def privacy_export_preview(
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    return await asyncio.to_thread(
        privacy_service.export_preview,
        str(principal["household_id"]),
    )


@app.get(
    "/api/v1/privacy/export",
    tags=["Privacy & Operations"],
    summary="Download a secret-free portable household export",
    responses={200: {"content": {"application/zip": {}}}},
)
async def privacy_export(
    include_receipt_files: bool = Query(default=True),
    principal: dict[str, Any] = Depends(require_auth),
) -> StreamingResponse:
    _require_recent_auth(principal)
    archive, manifest = await asyncio.to_thread(
        privacy_service.build_export,
        household_id=str(principal["household_id"]),
        public_settings=settings_service.get_public(),
        include_receipt_files=include_receipt_files,
        version=app.version,
    )
    database.add_audit_event(
        category="privacy",
        action="portable_export",
        outcome="success",
        details={
            "actor_user_id": principal["user_id"],
            "receipt_files_included": manifest["receipt_files_included"],
        },
    )

    def stream_archive():
        try:
            while chunk := archive.read(1024 * 1024):
                yield chunk
        finally:
            archive.close()

    filename = f"vorrio-export-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.zip"
    return StreamingResponse(
        stream_archive(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get(
    "/api/v1/privacy/retention",
    tags=["Privacy & Operations"],
    summary="Preview receipt-file retention",
    response_model=RetentionPreviewResponse,
)
async def privacy_retention_preview(
    _: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    privacy = settings_service.get_private()["privacy"]
    return await asyncio.to_thread(
        privacy_service.retention_preview,
        delete_after_analysis=bool(privacy["delete_image_after_analysis"]),
        retention_days=int(privacy["retention_days"]),
    )


@app.post(
    "/api/v1/privacy/retention/run",
    tags=["Privacy & Operations"],
    summary="Apply receipt-file retention now",
    response_model=RetentionRunResponse,
)
async def privacy_retention_run(
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    _require_recent_auth(principal)
    privacy = settings_service.get_private()["privacy"]
    result = await asyncio.to_thread(
        privacy_service.prune_receipt_files,
        delete_after_analysis=bool(privacy["delete_image_after_analysis"]),
        retention_days=int(privacy["retention_days"]),
    )
    database.add_audit_event(
        category="privacy",
        action="manual_retention",
        outcome="success",
        details={
            "actor_user_id": principal["user_id"],
            "cleared_receipt_count": result["cleared_receipt_count"],
            "deleted_file_count": result["deleted_file_count"],
        },
    )
    return result


@app.get(
    "/api/v1/operations/overview",
    tags=["Privacy & Operations"],
    summary="Read the privacy-safe owner operations overview",
    response_model=OperationsOverviewResponse,
)
async def operations_overview(
    event_limit: int = Query(default=40, ge=1, le=100),
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    privacy = settings_service.get_private()["privacy"]
    return await asyncio.to_thread(
        privacy_service.operational_overview,
        household_id=str(principal["household_id"]),
        delete_after_analysis=bool(privacy["delete_image_after_analysis"]),
        retention_days=int(privacy["retention_days"]),
        event_limit=event_limit,
    )


@app.delete(
    "/api/v1/privacy/household",
    tags=["Privacy & Operations"],
    summary="Permanently erase this single-household installation",
    response_model=HouseholdEraseResponse,
)
async def privacy_erase_household(
    payload: HouseholdEraseInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> JSONResponse:
    _require_recent_auth(principal)
    request.session.clear()
    result = await asyncio.to_thread(privacy_service.erase_installation)
    response = JSONResponse(result)
    response.delete_cookie("session")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/v1/receipts", tags=["Receipts"], summary="List recent receipts", response_model=list[ReceiptResponse])
async def receipts(_: None = Depends(require_auth)) -> list[dict[str, Any]]:
    return database.list_receipts()


@app.get("/api/v1/receipts/{receipt_id}", tags=["Receipts"], summary="Get a receipt with all lines", response_model=ReceiptResponse)
async def receipt(receipt_id: str, _: None = Depends(require_auth)) -> dict[str, Any]:
    result = database.get_receipt(receipt_id)
    if not result:
        raise HTTPException(status_code=404, detail="Einkauf nicht gefunden")
    return result


@app.post("/api/v1/receipts/analyze", tags=["Receipts"], summary="Analyze an image or PDF receipt", response_model=ReceiptResponse)
async def analyze(
    image: UploadFile = File(...), _: None = Depends(require_auth)
) -> dict[str, Any]:
    declared_type = image.content_type or mimetypes.guess_type(image.filename or "")[0]
    raw = await image.read(config.max_upload_bytes + 1)
    if len(raw) > config.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Die Bondatei ist zu groß")
    if len(raw) < 100:
        raise HTTPException(status_code=400, detail="Die Bondatei ist leer oder beschädigt")

    filename_is_pdf = (image.filename or "").lower().endswith(".pdf")
    is_pdf = declared_type == "application/pdf" or filename_is_pdf or raw.startswith(b"%PDF-")
    allowed_images = {"image/jpeg", "image/png", "image/webp", "image/heic"}
    if not is_pdf and declared_type not in allowed_images:
        raise HTTPException(
            status_code=415,
            detail="Bitte ein JPG-, PNG-, WebP-, HEIC-Bild oder PDF verwenden",
        )

    if not is_pdf:
        try:
            validate_image_upload(raw, str(declared_type), config.max_image_pixels)
        except MediaValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    content_type = "application/pdf" if is_pdf else str(declared_type)
    source_sha256 = hashlib.sha256(raw).hexdigest()
    existing = database.get_receipt_by_hash(source_sha256, app.version)
    if existing:
        existing["duplicate"] = True
        return existing

    media: list[tuple[bytes, str]]
    source_text = ""
    if is_pdf:
        try:
            media, source_text = prepare_pdf_receipt(raw)
        except PdfReceiptError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        media = [(raw, content_type)]

    settings = settings_service.get_private()
    provider = settings["provider"]
    if not provider.get("model"):
        raise HTTPException(
            status_code=409, detail="Bitte zuerst unter Einstellungen ein KI-Modell auswählen"
        )

    grocy: GrocyClient | None = None
    master_data_context: dict[str, list[dict[str, Any]]] | None = None
    if settings["grocy"].get("enabled") and settings["grocy"].get("api_key"):
        grocy = GrocyClient(settings["grocy"]["url"], settings["grocy"]["api_key"])
        try:
            master_data_context = await grocy.master_data()
        except GrocyError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    receipt_id = str(uuid.uuid4())
    suffix = mimetypes.guess_extension(content_type) or ".img"
    upload_path = config.data_dir / "receipts" / f"{receipt_id}{suffix}"
    upload_path.write_bytes(raw)

    try:
        extracted = await analyze_receipt(
            provider, media, source_text, master_data_context
        )
    except ProviderError as exc:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not extracted.get("items"):
        upload_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail="Auf dem Bon wurden keine Artikel erkannt. Bitte ein schärferes Bild verwenden.",
        )

    items = [
        item
        for item in extracted.get("items", [])
        if item.get("category") != "adjustment"
        and not (
            isinstance(item.get("total_price"), (int, float))
            and float(item["total_price"]) < 0
        )
    ]
    if not items:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail="Es wurden keine sicheren Produktzeilen erkannt.",
        )
    receipt_fingerprint = build_receipt_fingerprint(
        {
            **extracted,
            "currency": extracted.get("currency") or "EUR",
        },
        items,
    )
    if receipt_fingerprint:
        semantic_duplicate = database.get_receipt_by_fingerprint(receipt_fingerprint)
        if semantic_duplicate:
            upload_path.unlink(missing_ok=True)
            semantic_duplicate["duplicate"] = True
            return semantic_duplicate
    try:
        items = await match_items(
            database=database,
            grocy=grocy,
            store_name=extracted.get("store_name"),
            items=items,
        )
    except GrocyError as exc:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    for item in items:
        item["id"] = str(uuid.uuid4())

    store_id: int | None = None
    if grocy and extracted.get("store_name"):
        stores = await grocy.stores()
        store_name = str(extracted["store_name"]).strip().lower()
        exact_store = next(
            (store for store in stores if str(store.get("name", "")).strip().lower() == store_name),
            None,
        )
        if exact_store:
            store_id = int(exact_store["id"])

    keep_path: str | None = str(upload_path)
    if settings["privacy"].get("delete_image_after_analysis"):
        upload_path.unlink(missing_ok=True)
        keep_path = None

    database.create_receipt(
        {
            "id": receipt_id,
            "store_name": extracted.get("store_name"),
            "purchase_date": extracted.get("purchase_date"),
            "currency": extracted.get("currency") or "EUR",
            "total": extracted.get("total"),
            "status": "review",
            "image_path": keep_path,
            "source_sha256": source_sha256,
            "receipt_fingerprint": receipt_fingerprint,
            "analysis_version": app.version,
            "retailer": extracted.get("retailer"),
            "store_number": extracted.get("store_number"),
            "store_address": extracted.get("store_address"),
            "grocy_store_id": store_id,
        },
        items,
    )
    return database.get_receipt(receipt_id) or {}


@app.patch("/api/v1/receipts/{receipt_id}/items/{item_id}", tags=["Receipts"], summary="Map a receipt line to a catalog product", response_model=ReceiptResponse)
async def map_item(
    receipt_id: str,
    item_id: str,
    payload: CatalogItemMappingInput,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    updated = database.update_catalog_item_mapping(
        receipt_id,
        item_id,
        payload.product_id,
        payload.remember,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Bonzeile nicht gefunden")
    reconcile_unresolved_items(database)
    return database.get_receipt(receipt_id) or {}


@app.get(
    "/api/v1/receipts/{receipt_id}/items/{item_id}/candidates",
    tags=["Receipts"],
    summary="Find real product candidates for a receipt line",
    description=(
        "Searches real Open Facts records only after an explicit review action, caches "
        "the result for 30 days and optionally lets the configured AI provider rank the "
        "returned records. Candidates are never assigned automatically."
    ),
    response_model=ProductCandidateSearchResponse,
)
async def receipt_item_candidates(
    receipt_id: str,
    item_id: str,
    limit: int = Query(default=3, ge=1, le=5),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    receipt = database.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Bon nicht gefunden")
    item = next(
        (row for row in receipt.get("items", []) if str(row.get("id")) == item_id),
        None,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Bonzeile nicht gefunden")
    provider = settings_service.get_private().get("provider") or {}
    return await find_product_candidates(
        database=database,
        provider_settings=provider,
        receipt=receipt,
        item=item,
        limit=limit,
    )


@app.post(
    "/api/v1/receipts/{receipt_id}/items/{item_id}/candidate",
    tags=["Receipts"],
    summary="Confirm and learn a real product candidate",
    description=(
        "Loads the selected candidate from the server-side cache, links its barcode, "
        "image and package variant to an existing or newly created local product, maps "
        "the receipt line and remembers the retailer wording."
    ),
    response_model=ReceiptResponse,
)
async def confirm_receipt_item_candidate(
    receipt_id: str,
    item_id: str,
    payload: ProductCandidateConfirmInput,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    receipt = database.get_receipt(receipt_id)
    item = next(
        (row for row in (receipt or {}).get("items", []) if str(row.get("id")) == item_id),
        None,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Bonzeile nicht gefunden")
    candidate = database.get_external_product(
        payload.source, payload.external_id, max_age_days=3650
    )
    if not candidate:
        raise HTTPException(
            status_code=409,
            detail="Der Produktvorschlag ist nicht mehr im lokalen Cache. Bitte neu suchen.",
        )
    barcode = str(candidate.get("barcode") or payload.external_id).strip()
    existing_barcode = database.catalog_product_by_barcode(barcode)
    product_id = payload.product_id or (
        str(existing_barcode["id"]) if existing_barcode else None
    )
    if product_id and not database.get_catalog_product(product_id):
        raise HTTPException(status_code=404, detail="Vorrio-Produkt nicht gefunden")
    if product_id is None:
        if not (payload.location_id or payload.new_location_name):
            raise HTTPException(status_code=422, detail="Bitte einen Lagerort wählen")
        if not (payload.quantity_unit_id or payload.new_quantity_unit_name):
            raise HTTPException(status_code=422, detail="Bitte eine Mengeneinheit wählen")
        name = str(payload.name or candidate.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Der Produktname fehlt")
        product = database.create_catalog_product(
            name=name,
            location_id=payload.location_id,
            new_location_name=payload.new_location_name,
            new_location_is_freezer=payload.new_location_is_freezer,
            quantity_unit_id=payload.quantity_unit_id,
            new_quantity_unit_name=payload.new_quantity_unit_name,
            product_group_id=payload.product_group_id,
            new_product_group_name=payload.new_product_group_name,
            default_best_before_days=payload.default_best_before_days,
            brand=str(candidate.get("brand") or "").strip() or None,
            barcode=barcode,
        )
        product_id = str(product["id"])
    package_amount, package_unit = parse_package_quantity(
        str(candidate.get("quantity") or "")
    )
    try:
        variant_id = database.attach_external_candidate(
            product_id=product_id,
            source=payload.source,
            external_id=payload.external_id,
            candidate=candidate,
            variant_name=str(candidate.get("name") or "").strip() or None,
            package_amount=package_amount,
            package_unit=package_unit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    database.update_catalog_item_mapping(
        receipt_id,
        item_id,
        product_id,
        payload.remember,
        variant_id,
    )
    reconcile_unresolved_items(database)
    return database.get_receipt(receipt_id) or {}


@app.get("/api/v1/catalog/products", tags=["Catalog"], summary="Search catalog products", response_model=list[CatalogProductResponse])
async def catalog_products(
    q: str = Query(default="", max_length=200),
    _: None = Depends(require_auth),
) -> list[dict[str, Any]]:
    return database.list_catalog_products(q, limit=100)


@app.post(
    "/api/v1/catalog/products",
    tags=["Catalog"],
    summary="Create a local catalog product",
    response_model=CatalogProductDetailResponse,
)
async def create_catalog_product(
    payload: CatalogProductCreateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    barcode: str | None = None
    if payload.barcode:
        try:
            barcode = normalize_barcode(payload.barcode).value
        except BarcodeValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        created = database.create_catalog_product(
            name=payload.name,
            location_id=payload.location_id,
            new_location_name=payload.new_location_name,
            new_location_is_freezer=payload.new_location_is_freezer,
            quantity_unit_id=payload.quantity_unit_id,
            new_quantity_unit_name=payload.new_quantity_unit_name,
            product_group_id=payload.product_group_id,
            new_product_group_name=payload.new_product_group_name,
            default_best_before_days=payload.default_best_before_days,
            minimum_stock_quantity=payload.minimum_stock_quantity,
            shopping_target_quantity=payload.shopping_target_quantity,
            brand=payload.brand,
            barcode=barcode,
        )
        product = database.get_catalog_product_detail(str(created["id"]))
        if not product:
            raise RuntimeError("Das Produkt konnte nicht geladen werden")
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="product.create",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"product_id": product["id"]},
    )
    return product


def raise_catalog_error(exc: Exception) -> None:
    detail = str(exc.args[0]) if exc.args else str(exc)
    raise HTTPException(
        status_code=404 if isinstance(exc, KeyError) else 409,
        detail=detail,
    ) from exc


@app.get(
    "/api/v1/catalog/products/{product_id}",
    tags=["Catalog"],
    summary="Read a product with variants and barcodes",
    response_model=CatalogProductDetailResponse,
)
async def catalog_product_detail(
    product_id: str,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    product = database.get_catalog_product_detail(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    return product


@app.patch(
    "/api/v1/catalog/products/{product_id}",
    tags=["Catalog"],
    summary="Edit a local catalog product",
    description=(
        "Updates confirmed household fields with optimistic concurrency. A renamed "
        "product keeps its old normalized name as an alias so earlier receipt wording "
        "continues to resolve."
    ),
    response_model=CatalogProductDetailResponse,
)
async def update_catalog_product(
    product_id: str,
    payload: CatalogProductUpdateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    previous = database.get_catalog_product_detail(product_id)
    if not previous:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    image_url = payload.image_url
    if image_url and image_url.startswith("/api/v1/catalog/products/") and not is_managed_product_image_url(
        image_url, product_id
    ):
        raise HTTPException(status_code=422, detail="Ungültige interne Produktbild-Adresse")
    try:
        product = database.update_catalog_product(
            product_id,
            name=payload.name,
            product_group_id=payload.product_group_id,
            default_location_id=payload.default_location_id,
            default_quantity_unit_id=payload.default_quantity_unit_id,
            default_best_before_days=payload.default_best_before_days,
            minimum_stock_quantity=payload.minimum_stock_quantity,
            shopping_target_quantity=payload.shopping_target_quantity,
            image_url=image_url,
            notes=payload.notes,
            expected_updated_at=payload.expected_updated_at,
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    if is_managed_product_image_url(previous.get("image_url"), product_id) and not is_managed_product_image_url(
        product.get("image_url"), product_id
    ):
        product_image_store.delete(product_id)
    database.add_audit_event(
        category="catalog",
        action="product.update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"product_id": product_id},
    )
    return product


@app.get(
    "/api/v1/catalog/products/{product_id}/image",
    tags=["Catalog"],
    summary="Read a locally managed product image",
)
async def catalog_product_image(
    product_id: str,
    _: None = Depends(require_auth),
) -> FileResponse:
    product = database.get_catalog_product_detail(product_id)
    if not product or not is_managed_product_image_url(product.get("image_url"), product_id):
        raise HTTPException(status_code=404, detail="Produktbild nicht gefunden")
    try:
        path = product_image_store.path(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Produktbild nicht gefunden") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Produktbild nicht gefunden")
    return FileResponse(
        path,
        media_type="image/webp",
        headers={"Cache-Control": "private, no-cache"},
    )


@app.post(
    "/api/v1/catalog/products/{product_id}/image",
    tags=["Catalog"],
    summary="Upload a private product image",
    description=(
        "Accepts JPEG, PNG or WebP, removes camera metadata and stores an optimized "
        "WebP in the local Vorrio data volume."
    ),
    response_model=CatalogProductDetailResponse,
)
async def upload_catalog_product_image(
    product_id: str,
    request: Request,
    image: UploadFile = File(...),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    previous = database.get_catalog_product_detail(product_id)
    if not previous:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    raw = await image.read(config.max_upload_bytes + 1)
    if len(raw) > config.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Das Produktbild ist zu groß")
    content_type = (image.content_type or "").split(";", 1)[0].strip().lower()
    try:
        body = await asyncio.to_thread(
            prepare_product_image,
            raw,
            content_type,
            config.max_image_pixels,
        )
    except MediaValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        staged = product_image_store.stage(product_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden") from exc
    previous_url = previous.get("image_url")
    try:
        updated = database.set_catalog_product_image(
            product_id, managed_product_image_url(product_id)
        )
        product_image_store.commit(product_id, staged)
    except Exception:
        product_image_store.discard(staged)
        database.set_catalog_product_image(product_id, previous_url)
        raise
    database.add_audit_event(
        category="catalog",
        action="product.image.upload",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"product_id": product_id, "bytes": len(body)},
    )
    return updated


@app.delete(
    "/api/v1/catalog/products/{product_id}/image",
    tags=["Catalog"],
    summary="Remove the current product image",
    response_model=CatalogProductDetailResponse,
)
async def delete_catalog_product_image(
    product_id: str,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        updated = database.set_catalog_product_image(product_id, None)
        product_image_store.delete(product_id)
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="product.image.delete",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"product_id": product_id},
    )
    return updated


@app.post(
    "/api/v1/catalog/products/{product_id}/variants",
    tags=["Catalog"],
    summary="Add a sellable product variant",
    response_model=CatalogProductDetailResponse,
)
async def create_catalog_variant(
    product_id: str,
    payload: CatalogVariantCreateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        product = database.create_catalog_variant(
            product_id,
            name=payload.name,
            brand=payload.brand,
            package_amount=payload.package_amount,
            package_unit=payload.package_unit,
            image_url=str(payload.image_url) if payload.image_url else None,
        )
    except (KeyError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="variant.create",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"product_id": product_id},
    )
    return product


@app.patch(
    "/api/v1/catalog/variants/{variant_id}",
    tags=["Catalog"],
    summary="Edit a product variant",
    response_model=CatalogProductDetailResponse,
)
async def update_catalog_variant(
    variant_id: str,
    payload: CatalogVariantUpdateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        product = database.update_catalog_variant(
            variant_id,
            name=payload.name,
            brand=payload.brand,
            package_amount=payload.package_amount,
            package_unit=payload.package_unit,
            image_url=str(payload.image_url) if payload.image_url else None,
            expected_updated_at=payload.expected_updated_at,
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="variant.update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"variant_id": variant_id},
    )
    return product


@app.delete(
    "/api/v1/catalog/variants/{variant_id}",
    tags=["Catalog"],
    summary="Delete an unused product variant",
    description="Deletion is blocked while a receipt, stock lot or scan still references the variant.",
    response_model=CatalogProductDetailResponse,
)
async def delete_catalog_variant(
    variant_id: str,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        product = database.delete_catalog_variant(variant_id)
    except (KeyError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="variant.delete",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"variant_id": variant_id},
    )
    return product


@app.post(
    "/api/v1/catalog/variants/{variant_id}/barcodes",
    tags=["Catalog"],
    summary="Attach a barcode to a product variant",
    response_model=CatalogProductDetailResponse,
)
async def create_catalog_barcode(
    variant_id: str,
    payload: CatalogBarcodeCreateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        normalized = normalize_barcode(payload.barcode)
        product = database.add_catalog_barcode(
            variant_id,
            barcode=normalized.value,
            symbology=normalized.symbology,
        )
    except BarcodeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="barcode.create",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"variant_id": variant_id, "symbology": normalized.symbology},
    )
    return product


@app.delete(
    "/api/v1/catalog/variants/{variant_id}/barcodes/{barcode}",
    tags=["Catalog"],
    summary="Detach a barcode from a product variant",
    response_model=CatalogProductDetailResponse,
)
async def delete_catalog_barcode(
    variant_id: str,
    barcode: str,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        normalized = normalize_barcode(barcode)
        product = database.delete_catalog_barcode(variant_id, normalized.value)
    except BarcodeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="barcode.delete",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"variant_id": variant_id},
    )
    return product


@app.get(
    "/api/v1/catalog/products/{product_id}/price-history",
    tags=["Catalog"],
    summary="List receipt prices for a catalog product",
    description=(
        "Returns receipt-derived prices with store and package variant context. "
        "No bank or payment data is stored."
    ),
    response_model=list[CatalogPriceHistoryItemResponse],
)
async def catalog_product_price_history(
    product_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    _: None = Depends(require_auth),
) -> list[dict[str, Any]]:
    if not database.get_catalog_product(product_id):
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    return database.catalog_price_history(product_id, limit)


@app.get(
    "/api/v1/insights/prices",
    tags=["Insights"],
    summary="Summarize confirmed receipt prices by product and store",
    description=(
        "Builds a read-only household price overview from confirmed receipt imports. "
        "Store values are historic observations, not live prices or availability."
    ),
    response_model=PriceInsightsResponse,
)
async def price_insights(
    limit: int = Query(default=100, ge=1, le=500),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    return database.price_insights(limit)


@app.get(
    "/api/v1/insights/budget",
    tags=["Insights"],
    summary="Summarize the household budget from confirmed receipts",
    description=(
        "Returns month-to-date spending, a pace-based forecast, a comparable prior "
        "period, monthly history, store shares and explicit coverage diagnostics. "
        "Only receipts with at least one confirmed stock import are counted; historic "
        "receipt values are never presented as live market prices."
    ),
    response_model=BudgetOverviewResponse,
)
async def budget_overview(
    months: int = Query(default=6, ge=1, le=24),
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    return database.budget_overview(str(principal["household_id"]), months)


@app.put(
    "/api/v1/insights/budget/settings",
    tags=["Insights"],
    summary="Set or clear the shared monthly household budget",
    description=(
        "Owner and admin sessions can set one EUR monthly limit and warning threshold "
        "for the household. A null limit removes the target without changing receipts."
    ),
    response_model=BudgetSettingsResponse,
)
async def update_budget_settings(
    payload: BudgetSettingsInput,
    request: Request,
    principal: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    try:
        updated = database.set_budget_settings(
            household_id=str(principal["household_id"]),
            user_id=str(principal["user_id"]),
            monthly_limit=payload.monthly_limit,
            warning_percent=payload.warning_percent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    database.add_audit_event(
        category="budget",
        action="settings.update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "household_id": str(principal["household_id"]),
            "configured": bool(updated["configured"]),
            "warning_percent": int(updated["warning_percent"]),
        },
    )
    return updated


@app.post(
    "/api/v1/catalog/reconcile",
    tags=["Catalog"],
    summary="Re-evaluate unresolved receipt lines",
    description=(
        "Uses only the local product catalog and learned mappings. Exact matches may "
        "be assigned automatically; fuzzy candidates always remain suggestions."
    ),
    response_model=ReconcileResponse,
)
async def reconcile_catalog_receipts(
    _: None = Depends(require_auth),
) -> dict[str, int]:
    return reconcile_unresolved_items(database)


@app.get("/api/v1/catalog/master-data", tags=["Catalog"], summary="List locations, units and product groups", response_model=MasterDataResponse)
async def catalog_master_data(_: None = Depends(require_auth)) -> dict[str, Any]:
    return database.catalog_master_data()


@app.post(
    "/api/v1/catalog/master-data/{kind}",
    tags=["Catalog"],
    summary="Create a catalog master-data entry",
    description="Supported kinds are locations, quantity-units and product-groups.",
    response_model=MasterDataItemResponse,
)
async def create_catalog_master_data(
    kind: str,
    payload: MasterDataCreateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        item = database.create_catalog_master_data(
            kind,
            name=payload.name,
            description=payload.description,
            is_freezer=payload.is_freezer,
            name_plural=payload.name_plural,
        )
    except (KeyError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="master_data.create",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"kind": kind, "item_id": item["id"]},
    )
    return item


@app.patch(
    "/api/v1/catalog/master-data/{kind}/{item_id}",
    tags=["Catalog"],
    summary="Rename or edit a catalog master-data entry",
    response_model=MasterDataItemResponse,
)
async def update_catalog_master_data(
    kind: str,
    item_id: int,
    payload: MasterDataUpdateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        item = database.update_catalog_master_data(
            kind,
            item_id,
            name=payload.name,
            description=payload.description,
            is_freezer=payload.is_freezer,
            name_plural=payload.name_plural,
            expected_updated_at=payload.expected_updated_at,
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="master_data.update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"kind": kind, "item_id": item_id},
    )
    return item


@app.delete(
    "/api/v1/catalog/master-data/{kind}/{item_id}",
    tags=["Catalog"],
    summary="Archive an unused catalog master-data entry",
    description=(
        "The entry is archived instead of physically deleted. Archiving is blocked "
        "while an active product still uses it."
    ),
    response_model=MasterDataItemResponse,
)
async def archive_catalog_master_data(
    kind: str,
    item_id: int,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        item = database.archive_catalog_master_data(kind, item_id)
    except (KeyError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="catalog",
        action="master_data.archive",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"kind": kind, "item_id": item_id},
    )
    return item


@app.get(
    "/api/v1/stock/count/products",
    tags=["Stock"],
    summary="List products for a reviewed stock count",
    description=(
        "Returns the complete active catalog including current totals, variants and "
        "default master data. Reading this endpoint never changes stock."
    ),
    response_model=list[CatalogProductDetailResponse],
)
async def stock_count_products(
    q: str = Query(default="", max_length=200),
    _: None = Depends(require_auth),
) -> list[dict[str, Any]]:
    return database.stock_count_products(q)


@app.get(
    "/api/v1/stock/counts",
    tags=["Stock"],
    summary="List completed stock counts",
    response_model=list[StockCountSessionResponse],
)
async def stock_counts(
    limit: int = Query(default=20, ge=1, le=100),
    _: None = Depends(require_auth),
) -> list[dict[str, Any]]:
    return database.list_stock_count_sessions(limit)


@app.post(
    "/api/v1/stock/counts",
    tags=["Stock"],
    summary="Apply a reviewed opening or correction count",
    description=(
        "Only explicitly submitted products are changed. Each line sets the counted "
        "total for one product; omitted products remain untouched. Positive and "
        "negative differences create append-only stock movements. Reusing the same "
        "client mutation id returns the original result."
    ),
    response_model=StockCountSessionResponse,
)
async def create_stock_count(
    payload: StockCountCreateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        result = database.apply_stock_count(
            client_mutation_id=payload.client_mutation_id,
            source=payload.source,
            note=payload.note,
            lines=[line.model_dump(mode="json") for line in payload.lines],
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="stock",
        action="count.confirm",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "session_id": result["id"],
            "source": result["source"],
            "line_count": result["line_count"],
            "changed_count": result["changed_count"],
        },
    )
    return result


@app.get("/api/v1/catalog/barcodes/{barcode}/lookup", tags=["Catalog"], summary="Resolve a barcode locally or through Open Facts", response_model=BarcodeLookupResponse)
async def catalog_barcode_lookup(
    barcode: str,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        normalized = normalize_barcode(barcode)
    except BarcodeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    local = database.catalog_product_by_barcode(normalized.value)
    if local:
        return {"found": True, "local": True, "product": local}
    if not normalized.supports_open_facts_lookup:
        return {"found": False, "local": False, "product": None}
    try:
        product = await lookup_open_facts(normalized.value)
    except ProductDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"found": product is not None, "local": False, "product": product}


@app.post(
    "/api/v1/scans/resolve",
    tags=["Scanning"],
    summary="Resolve a package code without changing stock",
    description=(
        "Normalizes the decoded code, checks the local catalog and fresh cache first, "
        "then queries Open Facts for EAN/UPC/GTIN codes. Internal codes never leave the "
        "installation. Unknown and upstream-failed codes are kept "
        "in the unresolved inbox. Reusing client_mutation_id returns the same draft."
    ),
    response_model=ScanResponse,
)
async def resolve_scan(
    payload: ScanResolveInput,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        barcode = normalize_barcode(payload.barcode)
    except BarcodeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    local = database.catalog_product_by_barcode(barcode.value)
    if local:
        return database.create_scan(
            barcode_raw=barcode.raw,
            barcode_normalized=barcode.value,
            symbology=barcode.symbology,
            mode=payload.mode,
            resolution_source="local",
            product_id=str(local["id"]),
            variant_id=str(local["variant_id"]),
            resolve_key=payload.client_mutation_id,
        )
    if not barcode.supports_open_facts_lookup:
        return database.create_scan(
            barcode_raw=barcode.raw,
            barcode_normalized=barcode.value,
            symbology=barcode.symbology,
            mode=payload.mode,
            resolution_source="unresolved",
            resolve_key=payload.client_mutation_id,
        )
    cached = database.get_external_product("open_facts", barcode.value)
    if cached:
        return database.create_scan(
            barcode_raw=barcode.raw,
            barcode_normalized=barcode.value,
            symbology=barcode.symbology,
            mode=payload.mode,
            resolution_source="cache",
            suggestion=cached,
            resolve_key=payload.client_mutation_id,
        )
    try:
        product = await lookup_open_facts(barcode.value)
    except ProductDataError as exc:
        return database.create_scan(
            barcode_raw=barcode.raw,
            barcode_normalized=barcode.value,
            symbology=barcode.symbology,
            mode=payload.mode,
            resolution_source="unresolved",
            upstream_error=str(exc),
            resolve_key=payload.client_mutation_id,
        )
    if product:
        database.put_external_product(
            "open_facts",
            barcode.value,
            product,
            source_url=product.get("source_url"),
            license_name=product.get("database_license"),
            attribution=product.get("attribution"),
        )
        return database.create_scan(
            barcode_raw=barcode.raw,
            barcode_normalized=barcode.value,
            symbology=barcode.symbology,
            mode=payload.mode,
            resolution_source="open_facts",
            suggestion=product,
            resolve_key=payload.client_mutation_id,
        )
    return database.create_scan(
        barcode_raw=barcode.raw,
        barcode_normalized=barcode.value,
        symbology=barcode.symbology,
        mode=payload.mode,
        resolution_source="unresolved",
        resolve_key=payload.client_mutation_id,
    )


@app.get(
    "/api/v1/scans/unresolved",
    tags=["Scanning"],
    summary="List unresolved package scans",
    response_model=list[ScanResponse],
)
async def unresolved_scans(_: None = Depends(require_auth)) -> list[dict[str, Any]]:
    return database.list_unresolved_scans()


@app.get(
    "/api/v1/scans/{scan_id}",
    tags=["Scanning"],
    summary="Read one scan draft",
    response_model=ScanResponse,
)
async def get_scan(scan_id: str, _: None = Depends(require_auth)) -> dict[str, Any]:
    scan = database.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    return scan


@app.patch(
    "/api/v1/scans/{scan_id}",
    tags=["Scanning"],
    summary="Edit or map an unresolved scan",
    description="Updates review suggestions or maps the code to an existing local product.",
    response_model=ScanResponse,
)
async def update_scan(
    scan_id: str,
    payload: ScanUpdateInput,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    updated = database.update_scan(
        scan_id,
        mode=payload.mode,
        product_id=payload.product_id,
        suggestion_updates={
            "name": payload.name,
            "brand": payload.brand,
            "quantity": payload.quantity_label,
            "image_url": str(payload.image_url) if payload.image_url else None,
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail="Scan kann nicht mehr geändert werden")
    return updated


@app.post(
    "/api/v1/scans/{scan_id}/confirm",
    tags=["Scanning"],
    summary="Confirm the selected package action",
    description=(
        "Optionally creates or maps the local product and then performs exactly one "
        "identify, add, consume, open or shopping-list action. The confirmation key "
        "makes retries safe."
    ),
    response_model=ScanResponse,
)
async def confirm_scan(
    scan_id: str,
    payload: ScanConfirmInput,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    scan = database.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    suggestion = scan.get("suggestion") or {}
    if payload.product_id or not scan.get("product_id"):
        product_name = payload.name or suggestion.get("name")
        if not payload.product_id and not product_name:
            raise HTTPException(
                status_code=422,
                detail="Bitte einen Produktnamen eingeben oder ein Produkt zuordnen",
            )
        package_amount, package_unit = parse_package_quantity(
            str(suggestion.get("quantity") or "")
        )
        try:
            scan = database.ensure_scan_product(
                scan_id,
                name=str(product_name or "Zugeordnetes Produkt"),
                product_id=payload.product_id,
                brand=payload.brand or suggestion.get("brand"),
                variant_name=payload.variant_name,
                package_amount=payload.package_amount or package_amount,
                package_unit=payload.package_unit or package_unit,
                image_url=str(payload.image_url) if payload.image_url else suggestion.get("image_url"),
                location_id=payload.location_id,
                quantity_unit_id=payload.quantity_unit_id,
                product_group_id=payload.product_group_id,
                default_best_before_days=payload.default_best_before_days,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    reconciled = reconcile_unresolved_items(database)
    try:
        return database.confirm_scan_action(
            scan_id,
            confirmation_key=payload.client_mutation_id,
            quantity=payload.quantity,
            location_id=payload.location_id,
            best_before_date=payload.best_before_date.isoformat()
            if payload.best_before_date
            else None,
            unit_price=payload.unit_price,
            result_metadata={
                "reconciled_receipt_items": reconciled["resolved"],
                "suggested_receipt_items": reconciled["suggested"],
            },
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.delete(
    "/api/v1/scans/{scan_id}",
    tags=["Scanning"],
    summary="Discard an unresolved scan",
    response_model=ScanResponse,
)
async def discard_scan(scan_id: str, _: None = Depends(require_auth)) -> dict[str, Any]:
    scan = database.discard_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=409, detail="Bestätigter oder unbekannter Scan")
    return scan


@app.get(
    "/api/v1/shopping-list",
    tags=["Shopping"],
    summary="List open household shopping items",
    response_model=list[ShoppingListItemResponse],
)
async def shopping_list(_: None = Depends(require_auth)) -> list[dict[str, Any]]:
    return database.list_shopping_items()


@app.get(
    "/api/v1/shopping-list/low-stock",
    tags=["Shopping"],
    summary="Preview products below their configured minimum stock",
    description=(
        "Returns a read-only proposal. Products without an active refill target are "
        "omitted, and no shopping-list item changes until generation is confirmed."
    ),
    response_model=ShoppingLowStockResponse,
)
async def shopping_low_stock(
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    return {"items": database.low_stock_preview(), "generated_at": now_iso()}


@app.post(
    "/api/v1/shopping-list/generate",
    tags=["Shopping"],
    summary="Generate reviewed shopping-list items from low stock",
    description=(
        "Re-checks every selected product transactionally. Existing open items are "
        "raised only when the calculated shortage is larger, and an idempotency key "
        "prevents network retries from adding twice."
    ),
    response_model=ShoppingGenerationResponse,
)
async def generate_shopping_list(
    payload: ShoppingGenerateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        result = database.generate_shopping_list(
            client_mutation_id=payload.client_mutation_id,
            product_ids=payload.product_ids,
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="shopping",
        action="minimum.generate",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={
            "run_id": result["id"],
            "requested_count": result["requested_count"],
            "created_count": result["created_count"],
            "updated_count": result["updated_count"],
        },
    )
    return result


@app.patch(
    "/api/v1/shopping-list/{item_id}",
    tags=["Shopping"],
    summary="Edit or complete a shopping-list item",
    response_model=ShoppingListItemResponse,
)
async def update_shopping_list_item(
    item_id: str,
    payload: ShoppingListItemUpdateInput,
    request: Request,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        item = database.update_shopping_item(
            item_id,
            desired_quantity=payload.desired_quantity,
            checked=payload.checked,
            notes=payload.notes,
            expected_updated_at=payload.expected_updated_at,
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise_catalog_error(exc)
    database.add_audit_event(
        category="shopping",
        action="item.complete" if payload.checked else "item.update",
        outcome="success",
        source_hash=request_source_fingerprint(request, config.secret_key),
        details={"item_id": item_id, "product_id": item.get("product_id")},
    )
    return item


@app.get(
    "/api/v1/integrations/grocy/stock-preview",
    tags=["Integrations"],
    summary="Preview mapped Grocy balances without changing Vorrio",
    description=(
        "Reads the configured Grocy stock and maps it to previously imported catalog "
        "products. The response is a review proposal only; stock changes require a "
        "separate confirmed POST to /api/v1/stock/counts."
    ),
    response_model=GrocyStockPreviewResponse,
)
async def grocy_stock_preview(
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        entries = await get_grocy_client().stock()
    except GrocyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return database.grocy_stock_preview(entries)


@app.post("/api/v1/integrations/grocy/import-catalog", tags=["Integrations"], summary="Import or update the local catalog from Grocy", response_model=GrocyCatalogImportResponse)
async def import_grocy_catalog(_: None = Depends(require_auth)) -> dict[str, Any]:
    client = get_grocy_client(require_enabled=False)
    try:
        master_data, products = await asyncio.gather(
            client.master_data(),
            client.products(),
        )
    except GrocyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "imported": database.import_grocy_catalog(master_data, products),
        "catalog": database.catalog_summary(),
    }


@app.post("/api/v1/receipts/{receipt_id}/items/{item_id}/catalog-product", tags=["Receipts"], summary="Create and map a local catalog product", response_model=ReceiptResponse)
async def create_and_map_catalog_product(
    receipt_id: str,
    item_id: str,
    payload: CatalogProductCreateInput,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    receipt_data = database.get_receipt(receipt_id)
    item = next(
        (row for row in (receipt_data or {}).get("items", []) if row["id"] == item_id),
        None,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Bonzeile nicht gefunden")
    product = database.create_catalog_product(
        name=payload.name,
        location_id=payload.location_id,
        new_location_name=payload.new_location_name,
        new_location_is_freezer=payload.new_location_is_freezer,
        quantity_unit_id=payload.quantity_unit_id,
        new_quantity_unit_name=payload.new_quantity_unit_name,
        product_group_id=payload.product_group_id,
        new_product_group_name=payload.new_product_group_name,
        default_best_before_days=payload.default_best_before_days,
        brand=payload.brand or item.get("brand"),
        barcode=payload.barcode or item.get("barcode"),
    )
    database.update_catalog_item_mapping(
        receipt_id,
        item_id,
        str(product["id"]),
        payload.remember,
    )
    reconcile_unresolved_items(database)
    return database.get_receipt(receipt_id) or {}


@app.get(
    "/api/v1/grocy/products",
    tags=["Legacy Grocy"],
    summary="Search Grocy products",
    deprecated=True,
    response_model=list[GrocyProductResponse],
)
async def search_products(
    q: str = Query(default="", max_length=200),
    _: None = Depends(require_auth),
) -> list[dict[str, Any]]:
    try:
        products = await get_grocy_client().products()
    except GrocyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    needle = q.strip().lower()
    filtered = [
        {"id": int(product["id"]), "name": str(product.get("name", ""))}
        for product in products
        if not needle or needle in str(product.get("name", "")).lower()
    ]
    return sorted(filtered, key=lambda product: product["name"].lower())[:50]


@app.get(
    "/api/v1/grocy/master-data",
    tags=["Legacy Grocy"],
    summary="Read Grocy master data",
    deprecated=True,
    response_model=MasterDataResponse,
)
async def grocy_master_data(_: None = Depends(require_auth)) -> dict[str, Any]:
    try:
        data = await get_grocy_client().master_data()
    except GrocyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "locations": [
            {"id": int(row["id"]), "name": str(row.get("name", ""))}
            for row in data["locations"]
            if int(row.get("active", 1)) == 1
        ],
        "quantity_units": [
            {"id": int(row["id"]), "name": str(row.get("name", ""))}
            for row in data["quantity_units"]
            if int(row.get("active", 1)) == 1
        ],
        "product_groups": [
            {"id": int(row["id"]), "name": str(row.get("name", ""))}
            for row in data["product_groups"]
            if int(row.get("active", 1)) == 1
        ],
    }


@app.post(
    "/api/v1/receipts/{receipt_id}/items/{item_id}/create-product",
    tags=["Legacy Grocy"],
    summary="Create and map a Grocy product",
    deprecated=True,
    response_model=ReceiptResponse,
)
async def create_and_map_product(
    receipt_id: str,
    item_id: str,
    payload: GrocyProductCreateInput,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    receipt_data = database.get_receipt(receipt_id)
    if not receipt_data or not any(item["id"] == item_id for item in receipt_data["items"]):
        raise HTTPException(status_code=404, detail="Bonzeile nicht gefunden")

    new_location_name = (payload.new_location_name or "").strip()
    new_quantity_unit_name = (payload.new_quantity_unit_name or "").strip()
    new_product_group_name = (payload.new_product_group_name or "").strip()
    if payload.location_id is None and not new_location_name:
        raise HTTPException(
            status_code=422,
            detail="Bitte einen vorhandenen Lagerort wählen oder die Neuanlage bestätigen",
        )
    if payload.location_id is not None and new_location_name:
        raise HTTPException(
            status_code=422,
            detail="Lagerort kann nicht gleichzeitig gewählt und neu angelegt werden",
        )
    if payload.quantity_unit_id is None and not new_quantity_unit_name:
        raise HTTPException(
            status_code=422,
            detail="Bitte eine vorhandene Einheit wählen oder die Neuanlage bestätigen",
        )
    if payload.quantity_unit_id is not None and new_quantity_unit_name:
        raise HTTPException(
            status_code=422,
            detail="Einheit kann nicht gleichzeitig gewählt und neu angelegt werden",
        )
    if payload.product_group_id is not None and new_product_group_name:
        raise HTTPException(
            status_code=422,
            detail="Produktgruppe kann nicht gleichzeitig gewählt und neu angelegt werden",
        )

    client = get_grocy_client()
    try:
        products = await client.products()
        exact = next(
            (
                product
                for product in products
                if str(product.get("name", "")).strip().casefold()
                == payload.name.strip().casefold()
            ),
            None,
        )
        if exact:
            product_id = int(exact["id"])
        else:
            location_id = payload.location_id
            if new_location_name:
                location_id = await client.ensure_location(
                    new_location_name,
                    is_freezer=payload.new_location_is_freezer,
                )
            quantity_unit_id = payload.quantity_unit_id
            if new_quantity_unit_name:
                quantity_unit_id = await client.ensure_quantity_unit(
                    new_quantity_unit_name
                )
            product_group_id = payload.product_group_id
            if new_product_group_name:
                product_group_id = await client.ensure_product_group(
                    new_product_group_name
                )
            product_id = await client.create_product(
                name=payload.name,
                location_id=int(location_id),
                quantity_unit_id=int(quantity_unit_id),
                product_group_id=product_group_id,
                default_best_before_days=payload.default_best_before_days,
            )
    except GrocyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    updated = database.update_item_mapping(
        receipt_id,
        item_id,
        product_id,
        payload.name.strip(),
        payload.remember,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Bonzeile nicht gefunden")
    return database.get_receipt(receipt_id) or {}


@app.post("/api/v1/receipts/{receipt_id}/import", tags=["Receipts"], summary="Commit reviewed lines to local stock", response_model=ReceiptImportResponse)
async def import_receipt(
    receipt_id: str,
    payload: ImportRequest,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    lock = import_locks.setdefault(receipt_id, asyncio.Lock())
    async with lock:
        receipt_data = database.get_receipt(receipt_id)
        if not receipt_data:
            raise HTTPException(status_code=404, detail="Einkauf nicht gefunden")
        selected = set(payload.item_ids or [])
        items = [
            item
            for item in receipt_data["items"]
            if item["catalog_product_id"] is not None
            and not item["imported"]
            and (not selected or item["id"] in selected)
        ]
        if not items:
            raise HTTPException(status_code=409, detail="Keine bestätigten Artikel zum Übernehmen")

        private_settings = settings_service.get_private()
        grocy_settings = private_settings["grocy"]
        client = None
        if grocy_settings.get("enabled") and grocy_settings.get("api_key"):
            client = GrocyClient(grocy_settings["url"], grocy_settings["api_key"])
        store_id = receipt_data.get("grocy_store_id")
        grocy_store_error: str | None = None
        if client and store_id is None and receipt_data.get("store_name"):
            try:
                store_id = await client.ensure_store(str(receipt_data["store_name"]))
            except GrocyError as exc:
                grocy_store_error = str(exc)
            else:
                database.update_receipt_store_id(receipt_id, store_id)
        details: list[dict[str, Any]] = []
        imported_count = 0
        failed_count = 0
        grocy_exported_count = 0
        grocy_failed_count = 0
        for item in items:
            quantity = float(item["quantity"] or 1)
            unit_price = item["unit_price"]
            if unit_price is None and item["total_price"] is not None and quantity:
                unit_price = float(item["total_price"]) / quantity
            if not database.record_catalog_purchase(receipt_id, item["id"]):
                failed_count += 1
                error = "Artikel konnte nicht in den Vorrio-Bestand übernommen werden"
                database.mark_item_failed(item["id"], error)
                details.append({"item_id": item["id"], "ok": False, "error": error})
                continue

            imported_count += 1
            detail: dict[str, Any] = {"item_id": item["id"], "ok": True, "grocy": "skipped"}
            if client and item.get("grocy_product_id") and not item.get("grocy_exported"):
                if grocy_store_error:
                    detail["grocy"] = "failed"
                    detail["grocy_error"] = grocy_store_error
                    grocy_failed_count += 1
                else:
                    try:
                        await client.add_purchase(
                            product_id=int(item["grocy_product_id"]),
                            amount=quantity,
                            unit_price=float(unit_price) if unit_price is not None else None,
                            purchased_date=receipt_data.get("purchase_date"),
                            best_before_date=item.get("best_before_date"),
                            store_id=int(store_id) if store_id is not None else None,
                        )
                    except GrocyError as exc:
                        detail["grocy"] = "failed"
                        detail["grocy_error"] = str(exc)
                        grocy_failed_count += 1
                    else:
                        database.mark_grocy_exported(item["id"])
                        detail["grocy"] = "exported"
                        grocy_exported_count += 1
            details.append(detail)

        run_id = str(uuid.uuid4())
        database.save_import_run(
            run_id,
            receipt_id,
            len(items),
            imported_count,
            failed_count,
            details,
        )
        return {
            "run_id": run_id,
            "requested": len(items),
            "imported": imported_count,
            "failed": failed_count,
            "grocy_exported": grocy_exported_count,
            "grocy_failed": grocy_failed_count,
            "details": details,
            "receipt": database.get_receipt(receipt_id),
        }


static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str) -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API-Endpunkt nicht gefunden")
    candidate = (static_dir / full_path).resolve()
    if candidate.is_file() and static_dir in candidate.parents:
        return FileResponse(candidate)
    index = static_dir / "index.html"
    if not index.exists():
        raise HTTPException(status_code=503, detail="Frontend wurde noch nicht gebaut")
    return FileResponse(index)
