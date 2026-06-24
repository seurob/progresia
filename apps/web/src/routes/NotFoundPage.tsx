import { AlertTriangle } from "lucide-react";
import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-5 text-zinc-50">
      <div className="text-center">
        <AlertTriangle
          size={48}
          className="mx-auto mb-6 text-zinc-700"
          aria-hidden="true"
        />
        <p className="page-label mb-3">Error 404</p>
        <h1 className="text-5xl font-bold tracking-tight">Página no encontrada</h1>
        <p className="mt-4 text-base text-zinc-400">
          La ruta que buscas no existe en ProgresIA Studio.
        </p>
        <Link className="primary-button mt-8 inline-flex" to="/">
          Volver al dashboard
        </Link>
      </div>
    </div>
  );
}
