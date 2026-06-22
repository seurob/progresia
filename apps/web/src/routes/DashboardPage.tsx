import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, BriefcaseBusiness, CheckCircle2, Circle, Clock, Plus, Trash2, UserPlus, Users, Zap } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { useAuth } from "../features/auth/auth-context";
import { api, getErrorMessage } from "../lib/api";
import { Project, Role, Workspace, WorkspaceMember } from "../types/api";

type ProjectStatus = Project["status"];

const STATUS_LABELS: Record<ProjectStatus, string> = {
  DRAFT: "Borrador",
  REQUIREMENTS_READY: "Requisitos listos",
  SPEC_READY: "Arquitectura lista",
  GENERATING: "Generando...",
  GENERATED: "MVP generado",
  REVIEW: "En revision",
  DEPLOYED: "Publicado"
};

const STATUS_COLOR: Record<ProjectStatus, string> = {
  DRAFT: "text-zinc-400 border-zinc-700",
  REQUIREMENTS_READY: "text-sky-400 border-sky-800",
  SPEC_READY: "text-violet-400 border-violet-800",
  GENERATING: "text-amber-400 border-amber-800",
  GENERATED: "text-emerald-400 border-emerald-800",
  REVIEW: "text-blue-400 border-blue-800",
  DEPLOYED: "text-green-400 border-green-800"
};

const PIPELINE_STEPS: ProjectStatus[] = [
  "DRAFT", "REQUIREMENTS_READY", "SPEC_READY", "GENERATED"
];

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-ES", {
    day: "numeric", month: "short", year: "numeric"
  });
}

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
  const isLoading = projectsQuery.isLoading || workspacesQuery.isLoading;

  return (
    <div className="grid gap-6">
      <section className="flex flex-col justify-between gap-5 border-b border-zinc-800 pb-8 md:flex-row md:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-emerald-400">Dashboard</p>
          <h1 className="mt-3 text-4xl font-bold md:text-5xl">
            Proyectos de {auth.user?.name ?? "tu workspace"}
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-zinc-400">
            Crea el contenedor de producto, captura la idea y guarda la primera especificacion para alimentar los agentes.
          </p>
        </div>
        <Link
          className="primary-button w-full justify-center md:w-auto"
          to="/projects/new"
          aria-label="Crear nuevo proyecto"
        >
          <Plus size={18} aria-hidden="true" />
          Nuevo proyecto
        </Link>
      </section>

      <section className="grid gap-4 md:grid-cols-3" aria-label="Resumen del workspace">
        <Metric label="Workspaces" value={workspaces.length} loading={workspacesQuery.isLoading} />
        <Metric label="Proyectos" value={projects.length} loading={projectsQuery.isLoading} />
        <Metric
          label="Con idea"
          value={projects.filter((project) => project.idea).length}
          loading={projectsQuery.isLoading}
        />
      </section>

      <section className="grid gap-3" aria-label="Lista de proyectos">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Proyectos recientes</h2>
          {isLoading && (
            <span className="text-sm text-zinc-500" role="status" aria-live="polite">
              Cargando...
            </span>
          )}
        </div>

        {projectsQuery.isError && (
          <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200" role="alert">
            No se pudieron cargar los proyectos. Intenta recargar la pagina.
          </p>
        )}

        {projectsQuery.isLoading ? (
          <div className="grid gap-3" aria-busy="true" aria-label="Cargando proyectos">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-16 animate-pulse rounded-md border border-white/10 bg-white/4"
              />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-md border border-dashed border-white/15 p-8 text-center">
            <BriefcaseBusiness className="mx-auto mb-4 text-zinc-500" aria-hidden="true" />
            <p className="font-medium">Aun no hay proyectos.</p>
            <p className="mt-2 text-sm text-zinc-400">
              Crea el primero para empezar el flujo de idea a OpenSpec.
            </p>
            <Link className="primary-button mt-5 justify-center" to="/projects/new">
              <Plus size={18} aria-hidden="true" />
              Crear proyecto
            </Link>
          </div>
        ) : (
          <div className="grid gap-3">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </section>

      {workspaces.length > 0 && (() => {
        const ws = workspaces.find((w) => w.ownerId === auth.user?.id) ?? workspaces[0];
        return (
          <TeamSection
            workspaceId={ws.id}
            ownerId={ws.ownerId}
            currentUserId={auth.user?.id ?? ""}
          />
        );
      })()}
    </div>
  );
}

function ProjectCard({ project }: { readonly project: Project }) {
  const stepIndex = PIPELINE_STEPS.indexOf(
    PIPELINE_STEPS.find(s => s === project.status) ?? "DRAFT"
  );
  const isGenerated = ["GENERATED", "REVIEW", "DEPLOYED"].includes(project.status);
  const colorClass = STATUS_COLOR[project.status] ?? "text-zinc-400 border-zinc-700";

  return (
    <Link
      to={`/projects/${project.slug}`}
      className="group flex flex-col gap-3 rounded-lg border border-white/10 bg-white/4 p-4 transition-colors hover:border-white/20 hover:bg-white/6"
      aria-label={`Proyecto: ${project.name}`}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-semibold text-zinc-100 group-hover:text-white">
            {project.name}
          </p>
          <p className="mt-0.5 truncate text-sm text-zinc-500">
            {project.sector}
            {project.productType ? ` · ${project.productType}` : ""}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${colorClass}`}
            aria-label={`Estado: ${STATUS_LABELS[project.status]}`}
          >
            {STATUS_LABELS[project.status]}
          </span>
          <ArrowRight size={16} className="text-zinc-600 group-hover:text-zinc-400 transition-colors" aria-hidden="true" />
        </div>
      </div>

      {/* Pipeline progress dots */}
      {!isGenerated && (
        <div className="flex items-center gap-1.5" aria-label="Progreso del pipeline" role="list">
          {PIPELINE_STEPS.map((step, i) => {
            const done = i < stepIndex || isGenerated;
            const active = i === stepIndex;
            return (
              <div key={step} role="listitem" aria-label={STATUS_LABELS[step]}>
                {done ? (
                  <CheckCircle2 size={13} className="text-emerald-400" />
                ) : active ? (
                  <Zap size={13} className="text-amber-400" />
                ) : (
                  <Circle size={13} className="text-zinc-700" />
                )}
              </div>
            );
          })}
          <span className="ml-1 text-xs text-zinc-600">
            {stepIndex}/{PIPELINE_STEPS.length - 1} pasos
          </span>
        </div>
      )}

      {isGenerated && (
        <div className="flex items-center gap-1.5 text-xs text-emerald-400">
          <CheckCircle2 size={13} />
          Pipeline completo · ZIP disponible
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center gap-3 text-xs text-zinc-600">
        <span className="flex items-center gap-1">
          <Clock size={11} aria-hidden="true" />
          {formatDate(project.createdAt)}
        </span>
        {project.idea && (
          <span className="text-sky-600">· Idea capturada</span>
        )}
        {(project.specifications?.length ?? 0) > 0 && (
          <span className="text-violet-600">· Spec generada</span>
        )}
      </div>
    </Link>
  );
}

function TeamSection({
  workspaceId,
  ownerId,
  currentUserId
}: {
  readonly workspaceId: string;
  readonly ownerId: string;
  readonly currentUserId: string;
}) {
  const [showInvite, setShowInvite] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"COLLABORATOR" | "REVIEWER">("COLLABORATOR");
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [removeError, setRemoveError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const isOwner = currentUserId === ownerId;

  const membersQuery = useQuery({
    queryKey: ["workspace-members", workspaceId],
    queryFn: async () =>
      (await api.get<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`)).data
  });

  const inviteMutation = useMutation({
    mutationFn: () =>
      api.post(`/workspaces/${workspaceId}/members`, { email, role }).then((r) => r.data),
    onSuccess: () => {
      setEmail("");
      setInviteError(null);
      setShowInvite(false);
      void queryClient.invalidateQueries({ queryKey: ["workspace-members", workspaceId] });
    },
    onError: (err) => setInviteError(getErrorMessage(err))
  });

  const removeMutation = useMutation({
    mutationFn: (userId: string) =>
      api.delete(`/workspaces/${workspaceId}/members/${userId}`),
    onSuccess: () => {
      setRemoveError(null);
      void queryClient.invalidateQueries({ queryKey: ["workspace-members", workspaceId] });
    },
    onError: (err) => setRemoveError(getErrorMessage(err))
  });

  const members = membersQuery.data ?? [];

  return (
    <section
      className="rounded-md border border-white/10 bg-white/4 p-5"
      aria-label="Equipo del workspace"
    >
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <Users size={18} aria-hidden="true" />
          Equipo
          <span className="text-sm font-normal text-zinc-400">({members.length})</span>
        </h2>
        {isOwner && (
          <button
            className="secondary-button text-sm"
            onClick={() => setShowInvite((v) => !v)}
            aria-expanded={showInvite}
          >
            <UserPlus size={15} aria-hidden="true" />
            Invitar
          </button>
        )}
      </div>

      {showInvite && isOwner && (
        <form
          className="mt-4 grid gap-2 rounded-md border border-white/10 bg-black/20 p-3"
          onSubmit={(e) => { e.preventDefault(); inviteMutation.mutate(); }}
          aria-label="Formulario de invitacion"
        >
          <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto]">
            <input
              className="input text-sm"
              type="email"
              placeholder="email@ejemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              aria-label="Email del colaborador"
            />
            <select
              className="input text-sm"
              value={role}
              onChange={(e) => setRole(e.target.value as "COLLABORATOR" | "REVIEWER")}
              aria-label="Rol"
            >
              <option value="COLLABORATOR">Colaborador</option>
              <option value="REVIEWER">Revisor</option>
            </select>
            <button
              className="primary-button text-sm"
              type="submit"
              disabled={inviteMutation.isPending || !email}
            >
              {inviteMutation.isPending ? "Invitando..." : "Invitar"}
            </button>
          </div>
          {inviteError && (
            <p className="text-xs text-rose-300" role="alert">{inviteError}</p>
          )}
        </form>
      )}

      {removeError && (
        <p className="mt-3 text-xs text-rose-300" role="alert">{removeError}</p>
      )}

      <div className="mt-4 grid gap-2">
        {membersQuery.isLoading ? (
          [1, 2].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded-md bg-white/4" />
          ))
        ) : members.length === 0 ? (
          <p className="text-sm text-zinc-500">Solo tu por ahora. Invita a colaboradores.</p>
        ) : (
          members.map((m) => (
            <MemberRow
              key={m.id}
              member={m}
              canRemove={isOwner && m.userId !== currentUserId}
              onRemove={() => removeMutation.mutate(m.userId)}
              isRemoving={removeMutation.isPending}
            />
          ))
        )}
      </div>
    </section>
  );
}

function MemberRow({
  member,
  canRemove,
  onRemove,
  isRemoving
}: {
  readonly member: WorkspaceMember;
  readonly canRemove: boolean;
  readonly onRemove: () => void;
  readonly isRemoving: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-md border border-white/10 bg-white/2 px-3 py-2">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{member.user.name}</p>
        <p className="truncate text-xs text-zinc-500">{member.user.email}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <RolePill role={member.role} />
        {canRemove && (
          <button
            className="icon-button text-zinc-500 hover:text-rose-400"
            onClick={onRemove}
            disabled={isRemoving}
            aria-label={`Eliminar a ${member.user.name} del workspace`}
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );
}

const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Admin",
  OWNER: "Propietario",
  COLLABORATOR: "Colaborador",
  REVIEWER: "Revisor"
};

function RolePill({ role }: { readonly role: Role }) {
  return (
    <span className="status-pill text-xs">
      {ROLE_LABELS[role] ?? role}
    </span>
  );
}

function Metric({ label, value, loading }: { label: string; value: number; loading: boolean }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/4 p-5">
      <p className="text-sm text-zinc-400">{label}</p>
      {loading ? (
        <div className="mt-2 h-9 w-16 animate-pulse rounded-md bg-white/10" aria-hidden="true" />
      ) : (
        <p className="mt-2 text-3xl font-semibold" aria-label={`${label}: ${value}`}>
          {value}
        </p>
      )}
    </div>
  );
}
