from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any, Awaitable, Callable
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send


UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
access_logger = logging.getLogger("vorrio.access")
SECURITY_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-frame-options", b"DENY"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"permissions-policy", b"camera=(self), microphone=(), geolocation=()"),
    (
        b"content-security-policy",
        b"default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
        b"form-action 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        b"img-src 'self' data: blob: https:; connect-src 'self'; worker-src 'self' blob:; "
        b"manifest-src 'self'",
    ),
)


def source_fingerprint(source: str, secret_key: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"),
        source.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def request_source_fingerprint(request: Request, secret_key: str) -> str:
    source = request.client.host if request.client else "unknown"
    return source_fingerprint(source, secret_key)


def _normalize_origin(value: str) -> str | None:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


class LegacyApiCompatibilityMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = str(scope.get("path", ""))
            if (
                path.startswith("/api/")
                and not path.startswith("/api/v1/")
                and path not in {"/api/health", "/api/readiness"}
            ):
                scope["path"] = "/api/v1" + path[4:]
        await self.app(scope, receive, send)


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                declared_length = int(content_length)
                if declared_length < 0:
                    raise ValueError
                if declared_length > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                await JSONResponse(
                    status_code=400,
                    content={"detail": "Ungültige Content-Length-Angabe"},
                )(scope, receive, send)
                return

        method = str(scope.get("method", "GET")).upper()
        if method not in UNSAFE_METHODS:
            await self.app(scope, receive, send)
            return

        messages: list[Message] = []
        received = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.disconnect":
                break
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break

        position = 0

        async def replay_receive() -> Message:
            nonlocal position
            if position >= len(messages):
                return {"type": "http.disconnect"}
            message = messages[position]
            position += 1
            return message

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        await JSONResponse(
            status_code=413,
            content={"detail": "Die Anfrage ist zu groß"},
        )(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        scheme = str(scope.get("scheme", "http"))

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                existing = {key.lower() for key, _ in headers}
                for key, value in SECURITY_HEADERS:
                    if key not in existing:
                        headers.append((key, value))
                if scheme == "https" and b"strict-transport-security" not in existing:
                    headers.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


class PrivacySafeAccessLogMiddleware(BaseHTTPMiddleware):
    """Log request health without retaining IP addresses, query strings or identifiers."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request_id)
        route = request.scope.get("route")
        route_template = str(getattr(route, "path", "unmatched"))
        if route_template not in {"/api/health", "/api/readiness"}:
            access_logger.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": request.method,
                        "route": route_template,
                        "status_code": response.status_code,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    },
                    separators=(",", ":"),
                )
            )
        return response


class PublicExposureGateMiddleware:
    """Refuse application traffic when an internet profile is incomplete."""

    def __init__(self, app: ASGIApp, *, blocked_reasons: tuple[str, ...]) -> None:
        self.app = app
        self.blocked_reasons = blocked_reasons

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and self.blocked_reasons
            and str(scope.get("path", "")) not in {"/api/health", "/api/readiness"}
        ):
            await JSONResponse(
                status_code=503,
                content={
                    "detail": "Das öffentliche Bereitstellungsprofil ist noch nicht sicher freigegeben"
                },
                headers={"Cache-Control": "no-store"},
            )(scope, receive, send)
            return
        await self.app(scope, receive, send)


class RequestSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        database: Any,
        secret_key: str,
        public_url: str,
        allowed_origins: tuple[str, ...],
        require_session_origin: bool,
    ) -> None:
        super().__init__(app)
        self.database = database
        self.secret_key = secret_key
        self.public_url = public_url
        self.allowed_origins = set(allowed_origins)
        self.require_session_origin = require_session_origin

    def _request_origins(self, request: Request) -> set[str]:
        origins = set(self.allowed_origins)
        request_origin = _normalize_origin(f"{request.url.scheme}://{request.url.netloc}")
        if request_origin:
            origins.add(request_origin)
        if self.public_url:
            origins.add(self.public_url)
        return origins

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in UNSAFE_METHODS:
            origin = request.headers.get("origin")
            fetch_site = request.headers.get("sec-fetch-site", "").lower()
            normalized_origin = _normalize_origin(origin) if origin else None
            cookie_session = "session" in request.cookies and not request.headers.get(
                "authorization"
            )
            if (
                (origin and normalized_origin not in self._request_origins(request))
                or (not origin and fetch_site == "cross-site")
                or (
                    not origin
                    and cookie_session
                    and self.require_session_origin
                )
            ):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Die Anfrage stammt nicht von einer erlaubten Herkunft"},
                )

        response = await call_next(request)
        route = request.scope.get("route")
        path = str(getattr(route, "path", request.scope.get("path", "")))
        if (
            request.method in UNSAFE_METHODS
            and str(path).startswith("/api/v1/")
            and not str(path).startswith("/api/v1/auth/")
            and str(path) != "/api/v1/privacy/household"
            and (
                request.session.get("authenticated") is True
                or getattr(request.state, "api_token_id", None)
            )
        ):
            try:
                details = {"status_code": response.status_code}
                api_token_id = getattr(request.state, "api_token_id", None)
                if api_token_id:
                    details["authentication"] = "api_token"
                    details["api_token_id"] = api_token_id
                self.database.add_audit_event(
                    category="api",
                    action=f"{request.method} {path}",
                    outcome="success" if response.status_code < 400 else "failure",
                    source_hash=request_source_fingerprint(request, self.secret_key),
                    details=details,
                )
            except Exception:
                access_logger.exception(
                    json.dumps(
                        {
                            "event": "audit_write_failure",
                            "method": request.method,
                            "route": path,
                            "status_code": response.status_code,
                        },
                        separators=(",", ":"),
                    )
                )
        if str(path).startswith("/api/v1/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response
