from unittest.mock import patch

from app.core.monitoring import init_sentry, sanitize_sentry_event
from app.core.settings import settings


def test_sanitize_sentry_event_removes_sensitive_request_data() -> None:
    event = sanitize_sentry_event({
        "user": {"id": "user-1", "email": "private@example.com"},
        "request": {
            "data": {"password": "secret"},
            "cookies": {"session": "secret"},
            "headers": {
                "Authorization": "Bearer secret",
                "X-Api-Key": "secret",
                "Content-Type": "application/json",
            },
        },
    })

    assert "user" not in event
    assert "data" not in event["request"]
    assert "cookies" not in event["request"]
    assert event["request"]["headers"] == {"Content-Type": "application/json"}


def test_init_sentry_is_disabled_without_dsn() -> None:
    with patch.object(settings, "ai_sentry_dsn", None), patch(
        "app.core.monitoring.sentry_sdk.init"
    ) as init:
        assert init_sentry() is False
        init.assert_not_called()


def test_init_sentry_uses_privacy_safe_defaults() -> None:
    with (
        patch.object(settings, "ai_sentry_dsn", "https://public@example.ingest.sentry.io/1"),
        patch("app.core.monitoring.sentry_sdk.init") as init,
    ):
        assert init_sentry() is True

    kwargs = init.call_args.kwargs
    assert kwargs["send_default_pii"] is False
    assert kwargs["max_request_body_size"] == "never"
    assert kwargs["before_send"] is sanitize_sentry_event
