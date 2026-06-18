import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot, Check, Code2, Download, ExternalLink, FileText, Package, Save, Upload } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router";
import { z } from "zod";
import { FormField } from "../components/FormField";
import { api, getErrorMessage } from "../lib/api";
import { getAccessToken } from "../lib/auth-token";
import { useJobPoller } from "../hooks/useJobPoller";
import { ArtifactBundle, Project, PushToGithubResult, RequirementsContent } from "../types/api";

const ideaSchema = z.object({
  problem: z.string().min(10),
  targetUsers: z.string().min(2),
  coreFeatures: z.string().min(2),
  complexity: z.string().min(2),
  needsAi: z.boolean(),
  needsAuth: z.boolean(),
  needsAdminPanel: z.boolean(),
  constraints: z.string().optional()
});

type IdeaForm = z.infer<typeof ideaSchema>;

const STATUS_STEPS: Project["status"][] = [
  "DRAFT",
  "SPEC_READY",
  "GENERATING",
  "GENERATED",
  "REVIEW",
  "DEPLOYED"
];

const STATUS_LABELS: Record<Project["status"], string> = {
  DRAFT: "Borrador",
  SPEC_READY: "Spec lista",
  GENERATING: "Generando",
  GENERATED: "Generado",
  REVIEW: "Revision",
  DEPLOYED: "Desplegado"
};

function stepClass(isDone: boolean, isCurrent: boolean): string {
  if (isDone) return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  if (isCurrent) return "border-emerald-300/70 bg-emerald-300/15 text-emerald-100";
  return "border-white/10 bg-white/[0.03] text-zinc-500";
}

function RequirementsView({ content }: { readonly content: RequirementsContent }) {
  if (!content) return null;
  const functional = content.functional_requirements ?? [];
  const nonFunctional = content.non_functional_requirements ?? [];
  const stories = content.user_stories ?? [];

  return (
    <div className="mt-3 grid gap-3">
      {functional.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500">Funcionales</p>
          <ul className="grid gap-1.5">
            {functional.map((r) => (
              <li key={r.id} className="rounded-md border border-white/8 bg-black/20 px-3 py-2 text-xs leading-5">
                <span className="mr-1.5 font-mono text-zinc-500">{r.id}</span>
                <span className="font-medium text-zinc-200">{r.title}</span>
                {r.description && <span className="block mt-0.5 text-zinc-400">{r.description}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {nonFunctional.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500">No Funcionales</p>
          <ul className="grid gap-1.5">
            {nonFunctional.map((r) => (
              <li key={r.id} className="rounded-md border border-white/8 bg-black/20 px-3 py-2 text-xs leading-5">
                <span className="mr-1.5 font-mono text-zinc-500">{r.id}</span>
                <span className="font-medium text-zinc-200">{r.title}</span>
                {r.description && <span className="block mt-0.5 text-zinc-400">{r.description}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {stories.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500">User Stories</p>
          <ul className="grid gap-1.5">
            {stories.map((s) => (
              <li key={s.id} className="rounded-md border border-white/8 bg-black/20 px-3 py-2 text-xs leading-5">
                <span className="font-medium text-zinc-200">Como {s.actor}</span>
                <span className="text-zinc-400"> quiero {s.goal} para {s.benefit}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

interface ProjectActionsProps {
  readonly hasIdea: boolean;
  readonly hasOpenSpec: boolean;
  readonly hasRequirements: boolean;
  readonly onGenerateRequirements: () => void;
  readonly onGenerateOpenSpec: () => void;
  readonly onGenerateBundle: () => void;
  readonly onGenerateCode: () => void;
  readonly requirementsPending: boolean;
  readonly requirementsPolling: boolean;
  readonly openSpecPending: boolean;
  readonly openSpecPolling: boolean;
  readonly bundlePending: boolean;
  readonly codePending: boolean;
  readonly codePolling: boolean;
}

function jobLabel(base: string, isPending: boolean, isPolling: boolean): string {
  if (isPolling) return "En cola...";
  if (isPending) return "Enviando...";
  return base;
}

function ProjectActions({
  hasIdea, hasOpenSpec, hasRequirements,
  onGenerateRequirements, onGenerateOpenSpec, onGenerateBundle, onGenerateCode,
  requirementsPending, requirementsPolling,
  openSpecPending, openSpecPolling,
  bundlePending,
  codePending, codePolling
}: ProjectActionsProps) {
  const requirementsLabel = jobLabel(
    hasRequirements ? "Regenerar requisitos" : "Generar requisitos",
    requirementsPending, requirementsPolling
  );
  const openSpecLabel = jobLabel("Generar OpenSpec IA", openSpecPending, openSpecPolling);
  const codeLabel = jobLabel("Generar codigo", codePending, codePolling);

  return (
    <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
      <button
        className="secondary-button"
        onClick={onGenerateRequirements}
        disabled={requirementsPending || requirementsPolling || !hasIdea}
        aria-label={requirementsPolling ? "Requisitos en cola" : "Generar requisitos con IA"}
        title={hasIdea ? undefined : "Guarda la idea primero"}
      >
        <FileText size={18} aria-hidden="true" />
        {requirementsLabel}
      </button>
      <button
        className="secondary-button"
        onClick={onGenerateOpenSpec}
        disabled={openSpecPending || openSpecPolling || !hasIdea}
        aria-label={openSpecPolling ? "OpenSpec en cola" : "Generar OpenSpec con IA"}
        title={hasIdea ? undefined : "Guarda la idea primero"}
      >
        <Bot size={18} aria-hidden="true" />
        {openSpecLabel}
      </button>
      <button
        className="secondary-button"
        onClick={onGenerateBundle}
        disabled={bundlePending || !hasOpenSpec}
        aria-label={bundlePending ? "Preparando kit de artefactos" : "Generar kit de artefactos"}
        title={hasOpenSpec ? undefined : "Genera un OpenSpec primero"}
      >
        <Package size={18} aria-hidden="true" />
        {bundlePending ? "Preparando..." : "Generar kit"}
      </button>
      <button
        className="secondary-button"
        onClick={onGenerateCode}
        disabled={codePending || codePolling || !hasOpenSpec}
        aria-label={codePolling ? "Codigo en cola" : "Generar codigo scaffold"}
        title={hasOpenSpec ? undefined : "Genera un OpenSpec primero"}
      >
        <Code2 size={18} aria-hidden="true" />
        {codeLabel}
      </button>
    </div>
  );
}

function BundleCard({ bundle }: { readonly bundle: ArtifactBundle }) {
  const apiBase = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:3000/api";
  const manifestFiles = Array.isArray(bundle.manifest.files) ? bundle.manifest.files : [];
  const codeFiles = bundle.generatedContent?.files ?? [];
  const hasCode = codeFiles.length > 0;

  const [showGitHub, setShowGitHub] = useState(false);
  const [githubToken, setGithubToken] = useState("");
  const [repoName, setRepoName] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [pushResult, setPushResult] = useState<PushToGithubResult | null>(null);
  const [pushError, setPushError] = useState<string | null>(null);

  const pushMutation = useMutation({
    mutationFn: () =>
      api.post<PushToGithubResult>(`/artifacts/${bundle.id}/push-to-github`, {
        githubToken,
        repoName,
        isPrivate
      }).then((r) => r.data),
    onSuccess: (data) => { setPushResult(data); setPushError(null); },
    onError: (err) => setPushError(getErrorMessage(err))
  });

  const exportUrlMutation = useMutation({
    mutationFn: () =>
      api.get<{ url: string; expiresIn: number }>(`/artifacts/${bundle.id}/export-url`).then((r) => r.data),
    onSuccess: ({ url }) => window.open(url, "_blank", "noopener,noreferrer"),
    onError: (err) => setPushError(getErrorMessage(err))
  });

  return (
    <article className="min-w-0 rounded-md border border-white/10 bg-zinc-950/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="font-medium">Kit MVP</p>
        <span className="status-pill" aria-label={`Estado: ${bundle.status}`}>
          {bundle.status}
        </span>
      </div>
      {hasCode && (
        <p className="mt-1 text-xs text-emerald-400">
          <Code2 size={10} className="mr-1 inline" aria-hidden="true" />
          {codeFiles.length} archivos generados
        </p>
      )}
      <p className="mt-2 text-xs text-zinc-500">
        Spec: <span className="font-mono">{bundle.specificationId}</span>
      </p>

      <div className="mt-3 flex gap-2">
        <a
          href={`${apiBase}/artifacts/${bundle.id}/export`}
          download={`progresia-artifact-${bundle.id}.zip`}
          className="secondary-button flex-1 justify-center text-sm"
          aria-label="Descargar kit como ZIP"
          onClick={(e) => {
            const token = getAccessToken();
            if (!token) { e.preventDefault(); return; }
            e.preventDefault();
            void fetch(`${apiBase}/artifacts/${bundle.id}/export`, {
              headers: { Authorization: `Bearer ${token}` }
            })
              .then((r) => r.blob())
              .then((blob) => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `progresia-artifact-${bundle.id}.zip`;
                a.click();
                URL.revokeObjectURL(url);
              });
          }}
        >
          <Download size={15} aria-hidden="true" />
          ZIP
        </a>
        <button
          className="secondary-button text-sm"
          onClick={() => exportUrlMutation.mutate()}
          disabled={exportUrlMutation.isPending}
          aria-label="Obtener enlace de descarga desde MinIO"
          title="Sube el ZIP a MinIO y abre la URL firmada"
        >
          <Download size={15} aria-hidden="true" />
          {exportUrlMutation.isPending ? "Subiendo..." : "Enlace"}
        </button>
        {hasCode && (
          <button
            className="secondary-button flex-1 justify-center text-sm"
            onClick={() => setShowGitHub((v) => !v)}
            aria-expanded={showGitHub}
            aria-label="Publicar en GitHub"
          >
            <Upload size={15} aria-hidden="true" />
            GitHub
          </button>
        )}
      </div>

      {showGitHub && !pushResult && (
        <form
          className="mt-3 grid gap-2 rounded-md border border-white/10 bg-black/20 p-3"
          onSubmit={(e) => { e.preventDefault(); pushMutation.mutate(); }}
          aria-label="Formulario de publicacion en GitHub"
        >
          <p className="text-xs text-zinc-400">
            El token se usa en transit y nunca se persiste.
          </p>
          <input
            className="input text-sm"
            type="password"
            placeholder="GitHub token (ghp_...)"
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            required
            aria-label="GitHub personal access token"
          />
          <input
            className="input text-sm"
            type="text"
            placeholder="Nombre del repositorio"
            value={repoName}
            onChange={(e) => setRepoName(e.target.value)}
            required
            aria-label="Nombre del repositorio"
          />
          <label className="check-row text-sm">
            <input
              type="checkbox"
              checked={isPrivate}
              onChange={(e) => setIsPrivate(e.target.checked)}
            />
            <span>Repositorio privado</span>
          </label>
          {pushError && (
            <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-2 text-xs text-rose-300" role="alert">
              {pushError}
            </p>
          )}
          <button
            className="primary-button justify-center text-sm"
            type="submit"
            disabled={pushMutation.isPending || !githubToken || !repoName}
          >
            <Upload size={14} aria-hidden="true" />
            {pushMutation.isPending ? "Publicando..." : "Publicar en GitHub"}
          </button>
        </form>
      )}

      {pushResult && (
        <div className="mt-3 rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3">
          <p className="text-xs font-semibold text-emerald-300">Repositorio creado</p>
          <a
            href={pushResult.repoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 flex items-center gap-1 break-all text-xs text-emerald-200 underline"
          >
            {pushResult.repoUrl}
            <ExternalLink size={10} aria-hidden="true" className="shrink-0" />
          </a>
        </div>
      )}

      <ul className="mt-4 grid gap-2 text-sm text-zinc-300" aria-label="Archivos del kit">
        {(hasCode ? codeFiles : manifestFiles).map((file, index) => {
          const entry = file as { path?: string; description?: string; language?: string };
          return (
            <li key={`${bundle.id}-${index}`} className="rounded-md bg-black/25 p-3">
              <span className="block font-mono text-xs text-emerald-200">{entry.path}</span>
              {entry.language && (
                <span className="mt-0.5 block text-xs text-zinc-600">{entry.language}</span>
              )}
              {entry.description && (
                <span className="mt-1 block text-xs text-zinc-500">{entry.description}</span>
              )}
            </li>
          );
        })}
      </ul>
    </article>
  );
}

function StatusTimeline({ status }: { readonly status: Project["status"] }) {
  const currentIndex = STATUS_STEPS.indexOf(status);

  return (
    <nav aria-label="Estado del proyecto" className="mt-4">
      <ol className="flex flex-wrap items-center gap-1">
        {STATUS_STEPS.map((step, index) => {
          const isDone = index < currentIndex;
          const isCurrent = index === currentIndex;

          return (
            <li key={step} className="flex items-center gap-1">
              <span
                aria-current={isCurrent ? "step" : undefined}
                className={`rounded-md border px-2.5 py-1 text-xs font-semibold transition-colors ${stepClass(isDone, isCurrent)}`}
              >
                {isDone && <Check size={10} className="mr-1 inline" aria-hidden="true" />}
                {STATUS_LABELS[step]}
              </span>
              {index < STATUS_STEPS.length - 1 && (
                <span className="text-zinc-700" aria-hidden="true">›</span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);
  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: async () => (await api.get<Project>(`/projects/${projectId}`)).data,
    enabled: Boolean(projectId)
  });
  const form = useForm<IdeaForm>({
    resolver: zodResolver(ideaSchema),
    values: {
      problem: projectQuery.data?.idea?.problem ?? "",
      targetUsers: projectQuery.data?.idea?.targetUsers ?? "",
      coreFeatures: projectQuery.data?.idea?.coreFeatures?.join("\n") ?? "",
      complexity: projectQuery.data?.idea?.complexity ?? "standard",
      needsAi: projectQuery.data?.idea?.needsAi ?? false,
      needsAuth: projectQuery.data?.idea?.needsAuth ?? true,
      needsAdminPanel: projectQuery.data?.idea?.needsAdminPanel ?? true,
      constraints: projectQuery.data?.idea?.constraints ?? ""
    }
  });
  const saveIdea = useMutation({
    mutationFn: async (values: IdeaForm) =>
      api.post("/ideas", {
        projectId,
        problem: values.problem,
        targetUsers: values.targetUsers,
        coreFeatures: values.coreFeatures
          .split("\n")
          .map((feature) => feature.trim())
          .filter(Boolean),
        complexity: values.complexity,
        needsAi: values.needsAi,
        needsAuth: values.needsAuth,
        needsAdminPanel: values.needsAdminPanel,
        constraints: values.constraints
      }),
    onSuccess: async () => {
      setServerError(null);
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (error) => setServerError(getErrorMessage(error))
  });
  const refetchProject = async () => {
    setServerError(null);
    await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
  };

  const requirementsPoller = useJobPoller(refetchProject);
  const openSpecPoller = useJobPoller(refetchProject);
  const codePoller = useJobPoller(refetchProject);

  const generateRequirements = useMutation({
    mutationFn: async () => {
      const res = await api.post<{ jobId: string }>("/jobs/generate-requirements", { projectId });
      return res.data;
    },
    onSuccess: ({ jobId }) => requirementsPoller.startPolling(jobId),
    onError: (error) => setServerError(getErrorMessage(error))
  });
  const generateOpenSpec = useMutation({
    mutationFn: async () => {
      const res = await api.post<{ jobId: string }>("/jobs/generate-openspec", { projectId });
      return res.data;
    },
    onSuccess: ({ jobId }) => openSpecPoller.startPolling(jobId),
    onError: (error) => setServerError(getErrorMessage(error))
  });
  const generateArtifactBundle = useMutation({
    mutationFn: async () =>
      (await api.post<ArtifactBundle>(`/artifacts/project/${projectId}/generate`)).data,
    onSuccess: async () => {
      setServerError(null);
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (error) => setServerError(getErrorMessage(error))
  });
  const generateCode = useMutation({
    mutationFn: async () => {
      const res = await api.post<{ jobId: string }>("/jobs/generate-code", { projectId });
      return res.data;
    },
    onSuccess: ({ jobId }) => codePoller.startPolling(jobId),
    onError: (error) => setServerError(getErrorMessage(error))
  });

  const project = projectQuery.data;

  if (projectQuery.isLoading) {
    return (
      <div className="grid gap-6" aria-busy="true" aria-label="Cargando proyecto">
        <div className="h-8 w-24 animate-pulse rounded-md bg-white/10" />
        <div className="h-32 animate-pulse rounded-md bg-white/4" />
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="h-96 animate-pulse rounded-md bg-white/4" />
          <div className="h-64 animate-pulse rounded-md bg-white/4" />
        </div>
      </div>
    );
  }

  if (projectQuery.isError || !project) {
    return (
      <div className="grid gap-4">
        <Link className="subtle-link inline-flex w-fit" to="/">
          <ArrowLeft size={16} aria-hidden="true" />
          Volver
        </Link>
        <p
          className="rounded-md border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200"
          role="alert"
        >
          No se pudo cargar el proyecto. Comprueba que tienes acceso o recarga la pagina.
        </p>
      </div>
    );
  }

  const hasOpenSpec = (project.specifications ?? []).some(
    (s) => s.type === "OPENSPEC" && s.status === "GENERATED"
  );
  const hasRequirements = (project.specifications ?? []).some(
    (s) => s.type === "REQUIREMENTS" && s.status === "GENERATED"
  );

  return (
    <div className="grid gap-6">
      <Link className="subtle-link inline-flex w-fit" to="/" aria-label="Volver al dashboard">
        <ArrowLeft size={16} aria-hidden="true" />
        Volver
      </Link>

      <section className="border-b border-white/10 pb-6" aria-label="Cabecera del proyecto">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
          <div className="min-w-0">
            <h1 className="text-3xl font-semibold md:text-4xl">{project.name}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-400">{project.description}</p>
            <StatusTimeline status={project.status} />
          </div>
          <ProjectActions
            hasIdea={Boolean(project.idea)}
            hasOpenSpec={hasOpenSpec}
            hasRequirements={hasRequirements}
            onGenerateRequirements={() => generateRequirements.mutate()}
            onGenerateOpenSpec={() => generateOpenSpec.mutate()}
            onGenerateBundle={() => generateArtifactBundle.mutate()}
            onGenerateCode={() => generateCode.mutate()}
            requirementsPending={generateRequirements.isPending}
            requirementsPolling={requirementsPoller.isPolling}
            openSpecPending={generateOpenSpec.isPending}
            openSpecPolling={openSpecPoller.isPolling}
            bundlePending={generateArtifactBundle.isPending}
            codePending={generateCode.isPending}
            codePolling={codePoller.isPolling}
          />
        </div>

        {serverError && (
          <p
            className="mt-4 rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-200"
            role="alert"
          >
            {serverError}
          </p>
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section
          className="min-w-0 rounded-md border border-white/10 bg-white/4 p-5"
          aria-label="Idea wizard"
        >
          <h2 className="text-lg font-semibold">Idea wizard</h2>
          {project.idea ? null : (
            <p className="mt-2 text-sm text-zinc-400">
              Guarda la idea antes de generar OpenSpec con el servicio IA.
            </p>
          )}
          <form
            className="mt-5 grid gap-4"
            onSubmit={form.handleSubmit((values) => saveIdea.mutate(values))}
            aria-label="Formulario de idea de producto"
          >
            <FormField label="Problema" error={form.formState.errors.problem?.message}>
              <textarea
                className="input min-h-24"
                aria-required="true"
                {...form.register("problem")}
              />
            </FormField>
            <FormField label="Usuarios objetivo" error={form.formState.errors.targetUsers?.message}>
              <input
                className="input"
                aria-required="true"
                {...form.register("targetUsers")}
              />
            </FormField>
            <FormField
              label="Funcionalidades principales, una por linea"
              error={form.formState.errors.coreFeatures?.message}
            >
              <textarea
                className="input min-h-28"
                aria-required="true"
                {...form.register("coreFeatures")}
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="Complejidad" error={form.formState.errors.complexity?.message}>
                <select className="input" {...form.register("complexity")}>
                  <option value="simple">Simple</option>
                  <option value="standard">Standard</option>
                  <option value="advanced">Advanced</option>
                </select>
              </FormField>
              <FormField label="Restricciones" error={form.formState.errors.constraints?.message}>
                <input className="input" {...form.register("constraints")} />
              </FormField>
            </div>
            <fieldset>
              <legend className="mb-2 text-sm text-zinc-400">Modulos requeridos</legend>
              <div className="grid gap-3 md:grid-cols-3">
                <label className="check-row">
                  <input type="checkbox" {...form.register("needsAuth")} />
                  <span>Auth</span>
                </label>
                <label className="check-row">
                  <input type="checkbox" {...form.register("needsAdminPanel")} />
                  <span>Admin</span>
                </label>
                <label className="check-row">
                  <input type="checkbox" {...form.register("needsAi")} />
                  <span>IA</span>
                </label>
              </div>
            </fieldset>

            <button
              className="primary-button justify-center"
              type="submit"
              disabled={saveIdea.isPending}
              aria-label={saveIdea.isPending ? "Guardando idea..." : "Guardar idea"}
            >
              <Save size={18} aria-hidden="true" />
              {saveIdea.isPending ? "Guardando..." : "Guardar idea"}
            </button>
          </form>
        </section>

        <section
          className="min-w-0 rounded-md border border-white/10 bg-white/4 p-5"
          aria-label="Especificaciones generadas"
        >
          <h2 className="text-lg font-semibold">Specifications</h2>
          <ul className="mt-5 grid gap-3" aria-label="Lista de especificaciones">
            {(project.specifications ?? []).length === 0 ? (
              <li>
                <p className="rounded-md border border-dashed border-white/15 p-5 text-sm text-zinc-400">
                  Aun no hay specifications guardadas para este proyecto.
                </p>
              </li>
            ) : (
              project.specifications?.map((specification) => (
                <li key={specification.id}>
                  <article className="min-w-0 rounded-md border border-white/10 bg-zinc-950/70 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium">{specification.type}</p>
                      <span className="status-pill" aria-label={`Estado: ${specification.status}`}>
                        {specification.status}
                      </span>
                    </div>
                    {specification.type === "REQUIREMENTS" ? (
                      <RequirementsView content={specification.content as unknown as RequirementsContent} />
                    ) : (
                      <pre className="mt-3 max-h-72 max-w-full overflow-auto rounded-md bg-black/30 p-3 text-xs leading-5 text-zinc-300">
                        {JSON.stringify(specification.content, null, 2)}
                      </pre>
                    )}
                  </article>
                </li>
              ))
            )}
          </ul>
        </section>

        <section
          className="min-w-0 rounded-md border border-white/10 bg-white/4 p-5 xl:col-span-2"
          aria-label="Kits de artefactos generados"
        >
          <h2 className="text-lg font-semibold">Artifact bundles</h2>
          <ul
            className="mt-5 grid gap-3 md:grid-cols-2"
            aria-label="Lista de kits de artefactos"
          >
            {(project.artifactBundles ?? []).length === 0 ? (
              <li className="md:col-span-2">
                <p className="rounded-md border border-dashed border-white/15 p-5 text-sm text-zinc-400">
                  Todavia no hay kits generados. Crea uno desde una OpenSpec generada.
                </p>
              </li>
            ) : (
              project.artifactBundles?.map((bundle) => (
                <li key={bundle.id}>
                  <BundleCard bundle={bundle} />
                </li>
              ))
            )}
          </ul>
        </section>
      </div>
    </div>
  );
}
