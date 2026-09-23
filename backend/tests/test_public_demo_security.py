import pytest
from pydantic import ValidationError

from backend.models.api_models import QueryRequest
from backend.security.public_demo import (
    InMemoryDemoRateLimiter,
    PublicDemoConfig,
)


def make_config(
    short_requests: int = 2,
    daily_client: int = 5,
    global_daily: int = 20,
) -> PublicDemoConfig:
    return PublicDemoConfig(
        enabled=True,
        short_window_seconds=60,
        short_window_requests=short_requests,
        daily_requests_per_client=daily_client,
        global_daily_requests=global_daily,
        max_content_length_bytes=16384,
        trust_proxy_headers=False,
        session_cookie_secure=False,
        admin_api_key="",
    )


def test_query_accepts_1000_chars():
    request = QueryRequest(
        user_id="sarah",
        repository_id="demo-engineering-repository",
        query="x" * 1000,
    )

    assert len(request.query) == 1000


def test_query_rejects_over_1000_chars():
    with pytest.raises(ValidationError):
        QueryRequest(
            user_id="sarah",
            repository_id="demo-engineering-repository",
            query="x" * 1001,
        )


def test_query_rejects_extra_fields():
    with pytest.raises(ValidationError):
        QueryRequest(
            user_id="sarah",
            repository_id="demo-engineering-repository",
            query="Valid question",
            unexpected="not allowed",
        )


def test_short_window_limit():
    limiter = InMemoryDemoRateLimiter(
        make_config()
    )

    assert limiter.check(
        "client-a",
        now=1000,
    ).allowed

    assert limiter.check(
        "client-a",
        now=1001,
    ).allowed

    blocked = limiter.check(
        "client-a",
        now=1002,
    )

    assert not blocked.allowed
    assert blocked.scope == "short_window"


def test_daily_client_limit():
    limiter = InMemoryDemoRateLimiter(
        make_config(
            short_requests=10,
            daily_client=2,
        )
    )

    assert limiter.check(
        "client-a",
        now=1000,
    ).allowed

    assert limiter.check(
        "client-a",
        now=1001,
    ).allowed

    blocked = limiter.check(
        "client-a",
        now=1002,
    )

    assert not blocked.allowed
    assert blocked.scope == "client_daily"


def test_global_daily_limit():
    limiter = InMemoryDemoRateLimiter(
        make_config(
            short_requests=10,
            daily_client=10,
            global_daily=2,
        )
    )

    assert limiter.check(
        "client-a",
        now=1000,
    ).allowed

    assert limiter.check(
        "client-b",
        now=1001,
    ).allowed

    blocked = limiter.check(
        "client-c",
        now=1002,
    )

    assert not blocked.allowed
    assert blocked.scope == "global_daily"
