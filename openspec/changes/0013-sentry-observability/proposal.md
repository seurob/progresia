# Proposal: Sentry Observability

## Why

Production failures currently depend on local logs and user reports. The
platform needs centralized error monitoring and performance traces across the
React frontend, NestJS API and FastAPI AI service without collecting secrets or
personal data by default.

## What Changes

- Add optional Sentry SDK initialization to all three applications.
- Capture uncaught frontend errors, NestJS exceptions and FastAPI 5xx failures.
- Enable configurable trace sampling and release/environment tagging.
- Remove authorization, cookies, tokens and request bodies before transmission.
- Expose only an enabled/disabled observability flag in API health output.
- Document local and production configuration.

## Non-Goals

- Enabling Session Replay.
- Sending default PII.
- Uploading source maps without deployment credentials.
- Replacing application security controls with monitoring.
