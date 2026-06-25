from __future__ import annotations

from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.settings import settings

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


def sanitize_sentry_event(
    event: dict[str, Any],
    hint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del hint
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("cookies", None)
        request.pop("data", None)
        headers = request.get("headers")
        if isinstance(headers, dict):
            request["headers"] = {
                key: value
                for key, value in headers.items()
                if key.lower() not in SENSITIVE_HEADERS
            }
    event.pop("user", None)
    return event


def init_sentry() -> bool:
    dsn = (settings.ai_sentry_dsn or "").strip()
    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.ai_sentry_environment,
        release=settings.ai_sentry_release or None,
        send_default_pii=False,
        traces_sample_rate=settings.ai_sentry_traces_sample_rate,
        enable_logs=settings.ai_sentry_enable_logs,
        before_send=sanitize_sentry_event,
        integrations=[
            StarletteIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={*range(500, 600)},
                http_methods_to_capture=("CONNECT", "DELETE", "GET", "PATCH", "POST", "PUT"),
            ),
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={*range(500, 600)},
            ),
        ],
        max_request_body_size="never",
    )
    return True
