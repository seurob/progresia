import * as Sentry from "@sentry/react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { ReactNode } from "react";

function ErrorFallback() {
  return (
    <main className="grid min-h-screen place-items-center bg-[var(--bg)] px-6 text-[var(--text)]">
      <section className="max-w-lg text-center">
        <AlertTriangle className="mx-auto mb-5 size-10 text-[var(--accent)]" aria-hidden="true" />
        <h1 className="text-2xl font-semibold">No hemos podido mostrar esta pantalla</h1>
        <p className="mt-3 text-[var(--muted)]">
          El error ha quedado registrado. Recarga la aplicación para continuar.
        </p>
        <button
          type="button"
          className="mt-6 inline-flex items-center gap-2 bg-[var(--accent)] px-4 py-2 font-medium text-white"
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="size-4" aria-hidden="true" />
          Recargar
        </button>
      </section>
    </main>
  );
}

export function AppErrorBoundary({ children }: Readonly<{ children: ReactNode }>) {
  return <Sentry.ErrorBoundary fallback={<ErrorFallback />}>{children}</Sentry.ErrorBoundary>;
}
