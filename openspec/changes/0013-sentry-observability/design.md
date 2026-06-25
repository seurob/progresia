# Design

## Privacy Defaults

- `sendDefaultPii` / `send_default_pii` stays disabled.
- Authorization, cookie and token values are removed in `beforeSend`.
- Request bodies are removed from server events.
- Session Replay is not enabled.

## Activation

Each application is disabled when its DSN is empty. Trace sampling defaults to
`0.1` in production-oriented configuration and can be independently overridden.

## Deployment

Frontend configuration uses `VITE_SENTRY_*` build-time variables. Server
services use `SENTRY_*` runtime variables. Releases should use the deployed Git
commit SHA when available.
