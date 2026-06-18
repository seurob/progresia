import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BriefcaseBusiness, Plus } from "lucide-react";
import { Link } from "react-router";
import { useAuth } from "../features/auth/auth-context";
import { api } from "../lib/api";
import { Project, Workspace } from "../types/api";

export function DashboardPage() {
  const auth = useAuth();
  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => (await api.get<Workspace[]>("/workspaces")).data
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: async () => (await api.get<Project[]>("/projects")).data
  });

  const projects = projectsQuery.data ?? [];
  const workspaces = workspacesQuery.data ?? [];

  return (
    <div className="grid gap-6">
      <section className="flex flex-col justify-between gap-5 border-b border-white/10 pb-6 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold uppercase text-emerald-300">Dashboard</p>
          <h1 className="mt-2 text-3xl font-semibold md:text-4xl">Proyectos de {auth.user?.name ?? "tu workspace"}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400">
            Crea el contenedor de producto, captura la idea y guarda la primera especificacion para alimentar los agentes.
          </p>
        </div>
        <Link className="primary-button w-full justify-center md:w-auto" to="/projects/new">
          <Plus size={18} />
          Nuevo proyecto
        </Link>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Metric label="Workspaces" value={workspaces.length} />
        <Metric label="Proyectos" value={projects.length} />
        <Metric label="Con idea" value={projects.filter((project) => project.idea).length} />
      </section>

      <section className="grid gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Proyectos recientes</h2>
          {projectsQuery.isLoading ? <span className="text-sm text-zinc-500">Cargando</span> : null}
        </div>

        {projects.length === 0 ? (
          <div className="rounded-md border border-dashed border-white/15 p-8 text-center">
            <BriefcaseBusiness className="mx-auto mb-4 text-zinc-500" />
            <p className="font-medium">Aun no hay proyectos.</p>
            <p className="mt-2 text-sm text-zinc-400">Crea el primero para empezar el flujo de idea a OpenSpec.</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {projects.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="row-link">
                <div>
                  <p className="font-medium text-zinc-100">{project.name}</p>
                  <p className="mt-1 text-sm text-zinc-400">
                    {project.sector} · {project.productType}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="status-pill">{project.status}</span>
                  <ArrowRight size={18} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-5">
      <p className="text-sm text-zinc-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </div>
  );
}
