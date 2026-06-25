import * as Sentry from "@sentry/nestjs";
import { configureExceptionCapture } from "./common/monitoring/exception-capture";
import { sanitizeSentryEvent } from "./common/monitoring/sentry-sanitize";

const dsn = process.env.SENTRY_DSN?.trim();

function sampleRate(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 && parsed <= 1 ? parsed : fallback;
}

export const sentryEnabled = Boolean(dsn);

if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.SENTRY_ENVIRONMENT || process.env.NODE_ENV || "development",
    release: process.env.SENTRY_RELEASE || undefined,
    sendDefaultPii: false,
    tracesSampleRate: sampleRate(process.env.SENTRY_TRACES_SAMPLE_RATE, 0.1),
    beforeSend: sanitizeSentryEvent
  });
  configureExceptionCapture(Sentry.captureException);
}
