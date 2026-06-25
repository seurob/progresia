# ProgresIA Studio Delta

## ADDED Requirements

### Requirement: Cross-service error monitoring

The platform SHALL optionally report uncaught errors from the web, API and AI
service to independently configured Sentry projects.

### Requirement: Privacy-safe telemetry

Telemetry SHALL exclude authorization credentials, cookies, tokens and request
bodies, and SHALL NOT enable default PII or Session Replay.

### Requirement: Configurable tracing

Each service SHALL support environment, release and trace-sampling configuration
without requiring source changes.
