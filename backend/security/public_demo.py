from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hmac
import math
import os
from threading import Lock
import time

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def _env_bool(
    name: str,
    default: bool,
) -> bool:
    raw = os.getenv(name)

    if raw is None:
        return default

    return raw.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_positive_int(
    name: str,
    default: int,
) -> int:
    raw = os.getenv(name, "").strip()

    if not raw:
        return default

    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be an integer."
        ) from exc

    if value <= 0:
        raise RuntimeError(
            f"{name} must be greater than zero."
        )

    return value


@dataclass(frozen=True)
class PublicDemoConfig:
    enabled: bool

    short_window_seconds: int
    short_window_requests: int

    daily_requests_per_client: int
    global_daily_requests: int

    max_content_length_bytes: int

    trust_proxy_headers: bool
    session_cookie_secure: bool

    admin_api_key: str

    @classmethod
    def from_env(
        cls,
    ) -> "PublicDemoConfig":
        return cls(
            enabled=_env_bool(
                "PUBLIC_DEMO_MODE",
                False,
            ),
            short_window_seconds=(
                _env_positive_int(
                    "PUBLIC_DEMO_SHORT_WINDOW_SECONDS",
                    300,
                )
            ),
            short_window_requests=(
                _env_positive_int(
                    "PUBLIC_DEMO_SHORT_WINDOW_REQUESTS",
                    8,
                )
            ),
            daily_requests_per_client=(
                _env_positive_int(
                    "PUBLIC_DEMO_DAILY_REQUESTS_PER_CLIENT",
                    30,
                )
            ),
            global_daily_requests=(
                _env_positive_int(
                    "PUBLIC_DEMO_GLOBAL_DAILY_REQUESTS",
                    200,
                )
            ),
            max_content_length_bytes=(
                _env_positive_int(
                    "PUBLIC_DEMO_MAX_CONTENT_LENGTH_BYTES",
                    16384,
                )
            ),
            trust_proxy_headers=_env_bool(
                "TRUST_PROXY_HEADERS",
                False,
            ),
            session_cookie_secure=_env_bool(
                "SESSION_COOKIE_SECURE",
                False,
            ),
            admin_api_key=os.getenv(
                "PUBLIC_DEMO_ADMIN_KEY",
                "",
            ).strip(),
        )


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0
    scope: str | None = None


class InMemoryDemoRateLimiter:
    """
    Single-instance portfolio-demo limiter.

    This is deliberately simple and transparent.
    A distributed deployment should use shared
    storage or gateway-level rate limiting.
    """

    def __init__(
        self,
        config: PublicDemoConfig,
    ) -> None:
        self.config = config

        self._recent: dict[
            str,
            deque[float],
        ] = defaultdict(deque)

        self._daily: dict[
            tuple[str, str],
            int,
        ] = defaultdict(int)

        self._global_day: str | None = None
        self._global_count = 0

        self._lock = Lock()

    @staticmethod
    def _utc_day(
        timestamp: float,
    ) -> str:
        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        ).date().isoformat()

    @staticmethod
    def _seconds_until_next_utc_day(
        timestamp: float,
    ) -> int:
        now = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

        tomorrow = datetime.combine(
            now.date() + timedelta(days=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        return max(
            1,
            math.ceil(
                (
                    tomorrow - now
                ).total_seconds()
            ),
        )

    def check(
        self,
        client_key: str,
        *,
        now: float | None = None,
    ) -> RateLimitDecision:
        current = (
            time.time()
            if now is None
            else now
        )

        today = self._utc_day(
            current
        )

        with self._lock:
            if (
                self._global_day
                != today
            ):
                self._global_day = today
                self._global_count = 0
                self._daily.clear()

            window_start = (
                current
                - self.config.short_window_seconds
            )

            recent = self._recent[
                client_key
            ]

            while (
                recent
                and recent[0]
                <= window_start
            ):
                recent.popleft()

            if (
                len(recent)
                >= self.config.short_window_requests
            ):
                retry_after = max(
                    1,
                    math.ceil(
                        recent[0]
                        + self.config.short_window_seconds
                        - current
                    ),
                )

                return RateLimitDecision(
                    allowed=False,
                    retry_after_seconds=retry_after,
                    scope="short_window",
                )

            daily_key = (
                today,
                client_key,
            )

            if (
                self._daily[daily_key]
                >= self.config.daily_requests_per_client
            ):
                return RateLimitDecision(
                    allowed=False,
                    retry_after_seconds=(
                        self._seconds_until_next_utc_day(
                            current
                        )
                    ),
                    scope="client_daily",
                )

            if (
                self._global_count
                >= self.config.global_daily_requests
            ):
                return RateLimitDecision(
                    allowed=False,
                    retry_after_seconds=(
                        self._seconds_until_next_utc_day(
                            current
                        )
                    ),
                    scope="global_daily",
                )

            recent.append(
                current
            )

            self._daily[
                daily_key
            ] += 1

            self._global_count += 1

            return RateLimitDecision(
                allowed=True
            )


class PublicDemoProtectionMiddleware:
    ADMIN_EXACT_PATHS = {
        "/api/google-drive/files",
        "/api/google-drive/sync",
    }

    ADMIN_PREFIXES = (
        "/api/google-auth",
    )

    def __init__(
        self,
        app: ASGIApp,
        config: PublicDemoConfig,
    ) -> None:
        self.app = app
        self.config = config
        self.rate_limiter = (
            InMemoryDemoRateLimiter(
                config
            )
        )

    def _client_key(
        self,
        request: Request,
    ) -> str:
        if (
            self.config.trust_proxy_headers
        ):
            forwarded = (
                request.headers.get(
                    "x-forwarded-for"
                )
            )

            if forwarded:
                first = (
                    forwarded
                    .split(",", 1)[0]
                    .strip()
                )

                if first:
                    return first

        if request.client:
            return request.client.host

        return "unknown-client"

    def _is_admin_path(
        self,
        path: str,
    ) -> bool:
        if (
            path
            in self.ADMIN_EXACT_PATHS
        ):
            return True

        return any(
            path.startswith(prefix)
            for prefix
            in self.ADMIN_PREFIXES
        )

    def _admin_authorized(
        self,
        request: Request,
    ) -> bool:
        configured = (
            self.config.admin_api_key
        )

        if not configured:
            return False

        supplied = (
            request.headers.get(
                "x-admin-key",
                "",
            )
        )

        return hmac.compare_digest(
            supplied,
            configured,
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if (
            scope["type"] != "http"
            or not self.config.enabled
        ):
            await self.app(
                scope,
                receive,
                send,
            )
            return

        request = Request(
            scope,
            receive=receive,
        )

        path = request.url.path
        method = request.method.upper()

        if self._is_admin_path(
            path
        ):
            if not self._admin_authorized(
                request
            ):
                response = JSONResponse(
                    status_code=403,
                    content={
                        "detail": (
                            "Administrative operation "
                            "is unavailable in the "
                            "public demo."
                        ),
                        "code": (
                            "public_demo_admin_blocked"
                        ),
                    },
                    headers={
                        "Cache-Control": "no-store",
                    },
                )

                await response(
                    scope,
                    receive,
                    send,
                )
                return

        if method in {
            "POST",
            "PUT",
            "PATCH",
        }:
            raw_length = (
                request.headers.get(
                    "content-length"
                )
            )

            if raw_length:
                try:
                    content_length = int(
                        raw_length
                    )
                except ValueError:
                    response = JSONResponse(
                        status_code=400,
                        content={
                            "detail": (
                                "Invalid Content-Length."
                            ),
                            "code": (
                                "invalid_content_length"
                            ),
                        },
                    )

                    await response(
                        scope,
                        receive,
                        send,
                    )
                    return

                if (
                    content_length
                    > self.config.max_content_length_bytes
                ):
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "detail": (
                                "Request body exceeds "
                                "the public demo limit."
                            ),
                            "code": (
                                "request_too_large"
                            ),
                        },
                        headers={
                            "Cache-Control": "no-store",
                        },
                    )

                    await response(
                        scope,
                        receive,
                        send,
                    )
                    return

        if (
            method == "POST"
            and path == "/api/query"
        ):
            decision = (
                self.rate_limiter.check(
                    self._client_key(
                        request
                    )
                )
            )

            if not decision.allowed:
                response = JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Public demo query limit "
                            "reached. Please try again "
                            "later."
                        ),
                        "code": (
                            "demo_rate_limited"
                        ),
                        "scope": (
                            decision.scope
                        ),
                    },
                    headers={
                        "Retry-After": str(
                            decision.retry_after_seconds
                        ),
                        "Cache-Control": "no-store",
                    },
                )

                await response(
                    scope,
                    receive,
                    send,
                )
                return

        await self.app(
            scope,
            receive,
            send,
        )
