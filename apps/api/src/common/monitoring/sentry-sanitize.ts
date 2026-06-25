import type { ErrorEvent } from "@sentry/nestjs";

export function sanitizeSentryEvent(event: ErrorEvent): ErrorEvent {
  if (event.request) {
    delete event.request.cookies;
    delete event.request.data;
    if (event.request.headers) {
      const headers = { ...event.request.headers };
      for (const key of Object.keys(headers)) {
        if (["authorization", "cookie", "set-cookie", "x-api-key"].includes(key.toLowerCase())) {
          delete headers[key];
        }
      }
      event.request.headers = headers;
    }
  }
  delete event.user;
  return event;
}
