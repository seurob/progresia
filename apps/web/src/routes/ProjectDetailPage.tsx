import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle, ArrowLeft, BookOpen, Check, ChevronDown, ChevronUp,
  Code2, Download, ExternalLink, FileText, GitBranch, Layers,
  Loader2, PackageCheck, RefreshCw, Rocket, Terminal, Trash2, Upload, X, Zap
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api, getErrorMessage } from "../lib/api";
import { getAccessToken } from "../lib/auth-token";
import { ArtifactBundle, JobStatus, Project, PushToGithubResult, Specification } from "../types/api";

/* ─── Pipeline ─────────────────────────────────────────────────────────── */

type PipelineStage =
  | "idle" | "req" | "arch" | "spec" | "issues" | "tutorial" | "code" | "bundle"
  | "done" | "error";

const JOB_STAGES: PipelineStage[] = ["req", "arch", "spec", "issues", "tutorial", "code"];

const PIPELINE_STEPS = [
  { key: "req",      label: "Análisis de requisitos",    hint: "La IA extrae los requisitos funcionales de tu idea." },
  { key: "arch",     label: "Arquitectura tecnológica",  hint: "Se selecciona el stack más adecuado y se explica por qué." },
  { key: "spec",     label: "OpenSpec técnico",          hint: "Se genera la especificación completa: requisitos, user stories, módulos y milestones." },
  { key: "issues",   label: "Issues de GitHub",          hint: "Se crean las tareas del proyecto listas para importar a GitHub." },
  { key: "tutorial", label: "Tutorial de implementación", hint: "Se genera una guía paso a paso con comandos específicos del stack." },
  { key: "code",     label: "Generación de código",      hint: "Se genera el código base estructurado del proyecto." },
  { key: "bundle",   label: "Empaquetado",               hint: "Se empaqueta todo en un ZIP listo para descargar." },
] as const;

function stageToStepIndex(stage: PipelineStage): number {
  const idx: Partial<Record<PipelineStage, number>> = {
    req: 0, arch: 1, spec: 2, issues: 3, tutorial: 4, code: 5, bundle: 6
  };
  return idx[stage] ?? -1;
}

function stageEndpoint(stage: PipelineStage): string {
  const map: Partial<Record<PipelineStage, string>> = {
    req:      "/jobs/generate-requirements",
    arch:     "/jobs/recommend-architecture",
    spec:     "/jobs/generate-openspec",
    issues:   "/jobs/generate-issues",
    tutorial: "/jobs/generate-tutorial",
    code:     "/jobs/generate-code",
  };
  return map[stage] ?? "";
}

function nextStage(stage: PipelineStage): PipelineStage {
  const map: Partial<Record<PipelineStage, PipelineStage>> = {
    req: "arch", arch: "spec", spec: "issues", issues: "tutorial", tutorial: "code", code: "bundle"
  };
  return map[stage] ?? "done";
}

function useGeneratePipeline(projectId: string | undefined, onDone: () => void) {
  const [stage, setStage]   = useState<PipelineStage>("idle");
  const [jobId, setJobId]   = useState<string | null>(null);
  const [error, setError]   = useState<string | null>(null);
  const onDoneRef = useRef(onDone);
  useEffect(() => { onDoneRef.current = onDone; }, [onDone]);

  // Launch jobs or fire bundle
  useEffect(() => {
    if (!projectId || stage === "idle" || stage === "done" || stage === "error") return;

    if (stage === "bundle") {
      api.post(`/artifacts/project/${projectId}/generate`)
        .then(() => { setStage("done"); onDoneRef.current(); })
        .catch(err => { setError(getErrorMessage(err)); setStage("error"); });
      return;
    }

    if (jobId) return; // already running — wait for polling

    const endpoint = stageEndpoint(stage);
    if (!endpoint) return;

    api.post<{ jobId: string }>(endpoint, { projectId })
      .then(r => setJobId(r.data.jobId))
      .catch(err => { setError(getErrorMessage(err)); setStage("error"); });
  }, [stage, jobId, projectId]);

  // Poll active job
  useEffect(() => {
    if (!jobId || !JOB_STAGES.includes(stage as typeof JOB_STAGES[number])) return;

    const interval = setInterval(async () => {
      try {
        const { data } = await api.get<JobStatus>(`/jobs/${jobId}`);
        if (data.status === "completed") {
          clearInterval(interval);
          setJobId(null);
          setStage(nextStage(stage));
        } else if (data.status === "failed") {
          clearInterval(interval);
          setJobId(null);
          setError(data.failReason ?? "El proceso ha fallado");
          setStage("error");
        }
      } catch {
        clearInterval(interval);
        setJobId(null);
        setError("Error de comunicación con el servidor");
        setStage("error");
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [jobId, stage]);

  const start = useCallback(() => { setError(null); setJobId(null); setStage("req"); }, []);
  const reset = useCallback(() => { setStage("idle"); setError(null); setJobId(null); }, []);
  const isRunning = !["idle", "done", "error"].includes(stage);

  return { stage, isRunning, error, start, reset };
}

/* ─── Pipeline progress UI ───────────────────────────────────────────────── */

function PipelineProgress({ stage }: { readonly stage: PipelineStage }) {
  const activeIndex = stageToStepIndex(stage);

  return (
    <div className="grid gap-3">
      {PIPELINE_STEPS.map((step, i) => {
        const isDone   = i < activeIndex || stage === "done";
        const isActive = i === activeIndex && stage !== "done";

        return (
          <div
            key={step.key}
            className={`flex items-start gap-3 rounded-lg border p-4 transition-colors ${
              isActive ? "border-[var(--c-border-strong)] bg-[var(--c-surface-2)]" :
              isDone   ? "border-[var(--c-border-subtle)] bg-[var(--c-active-bg)]"  :
                         "border-[var(--c-border-subtle)] opacity-40"
            }`}
          >
            <span className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-full ${
              isDone   ? "bg-[var(--c-accent)] text-[var(--c-accent-on)]" :
              isActive ? "border border-[var(--c-accent)] text-[var(--c-accent)]" :
                         "border border-[var(--c-border-med)] text-[var(--c-text-faint)]"
            }`}>
              {isDone   ? <Check size={13} /> :
               isActive ? <Loader2 size={13} className="animate-spin" /> :
               <span className="text-xs">{i + 1}</span>}
            </span>
            <div className="min-w-0">
              <p className={`text-sm font-semibold ${
                isActive ? "text-[var(--c-text)]" :
                isDone   ? "text-[var(--c-text-muted)]" :
                           "text-[var(--c-text-faint)]"
              }`}>
                {step.label}
              </p>
              {isActive && (
                <p className="mt-0.5 text-xs text-[var(--c-text-muted)]">{step.hint}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Idea summary ───────────────────────────────────────────────────────── */

function IdeaSummary({
  idea, open, onToggle
}: {
  readonly idea: NonNullable<Project["idea"]>;
  readonly open: boolean;
  readonly onToggle: () => void;
}) {
  return (
    <div className="rounded-lg border border-[var(--c-border-subtle)] bg-[var(--c-surface)]">
      <button
        className="flex w-full items-center justify-between p-4 text-left"
        onClick={onToggle}
        aria-expanded={open}
      >
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-accent)]">Tu idea</p>
          <p className="mt-0.5 text-sm text-[var(--c-text-muted)] line-clamp-1">{idea.problem}</p>
        </div>
        {open ? <ChevronUp size={16} className="shrink-0 text-[var(--c-text-faint)]" /> : <ChevronDown size={16} className="shrink-0 text-[var(--c-text-faint)]" />}
      </button>

      {open && (
        <div className="grid gap-3 border-t border-[var(--c-border-subtle)] p-4 text-sm">
          <Field label="Problema"  value={idea.problem} />
          <Field label="Usuarios"  value={idea.targetUsers} />
          {(idea.coreFeatures ?? []).length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Funcionalidades</p>
              <ul className="grid gap-1">
                {idea.coreFeatures.map((f, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-[var(--c-text-muted)]">
                    <span className="mt-0.5 text-[var(--c-accent)]">—</span>{f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            {idea.needsAuth       && <Tag>Login / Auth</Tag>}
            {idea.needsAdminPanel && <Tag>Panel Admin</Tag>}
            {idea.needsAi         && <Tag>Inteligencia Artificial</Tag>}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Architecture card ──────────────────────────────────────────────────── */

interface ArchContent {
  architecture_type?: string;
  name?: string;
  justification?: string;
  tech_stack?: { name: string; version: string; purpose: string }[];
  alternatives?: string[];
  difficulty?: string;
  risks?: string[];
  first_steps?: string[];
  educational_notes?: string[];
  learning_path?: { title: string; url: string; type: string; level: string }[];
  when_to_upgrade?: { signal: string; reason: string; next_step: string }[];
}

const DIFFICULTY_LABEL: Record<string, string> = {
  BEGINNER: "Principiante", INTERMEDIATE: "Intermedio", ADVANCED: "Avanzado"
};
const DIFFICULTY_CLASS: Record<string, string> = {
  BEGINNER: "text-emerald-400 border-emerald-800",
  INTERMEDIATE: "text-amber-400 border-amber-800",
  ADVANCED: "text-rose-400 border-rose-800",
};

function ArchitectureCard({ spec }: { readonly spec: Specification }) {
  const [open, setOpen] = useState(false);
  const [notesOpen, setNotesOpen] = useState(false);
  const arch = spec.content as ArchContent;
  const difficulty = arch.difficulty ?? "";
  const stack = arch.tech_stack ?? [];

  return (
    <SpecAccordion
      icon={<Layers size={16} />}
      label="Arquitectura tecnológica"
      summary={arch.name ?? arch.architecture_type ?? "Sin nombre"}
      badge={difficulty ? (
        <span className={`rounded border px-2 py-0.5 text-xs font-medium ${DIFFICULTY_CLASS[difficulty] ?? "text-zinc-400 border-zinc-700"}`}>
          {DIFFICULTY_LABEL[difficulty] ?? difficulty}
        </span>
      ) : null}
      open={open}
      onToggle={() => setOpen(v => !v)}
    >
      {/* Stack pills */}
      {stack.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {stack.map((t, i) => (
            <span key={i} className="rounded-full border border-[var(--c-border-med)] px-2.5 py-0.5 text-xs font-mono text-[var(--c-text-muted)]">
              {t.name} {t.version}
            </span>
          ))}
        </div>
      )}

      {/* Justification */}
      {arch.justification && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Por qué este stack</p>
          <p className="text-sm text-[var(--c-text-muted)] leading-relaxed">{arch.justification}</p>
        </div>
      )}

      {/* First steps */}
      {(arch.first_steps ?? []).length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Primeros pasos</p>
          <ol className="grid gap-1.5">
            {arch.first_steps!.map((step, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[var(--c-text-muted)]">
                <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-[var(--c-surface-2)] text-xs font-bold text-[var(--c-accent)]">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Alternatives */}
      {(arch.alternatives ?? []).length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Alternativas consideradas</p>
          <div className="flex flex-wrap gap-1.5">
            {arch.alternatives!.map((a, i) => (
              <span key={i} className="rounded border border-[var(--c-border-subtle)] px-2 py-0.5 text-xs text-[var(--c-text-faint)]">{a}</span>
            ))}
          </div>
        </div>
      )}

      {/* Risks */}
      {(arch.risks ?? []).length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-amber-400">
            <AlertTriangle size={12} /> Riesgos a tener en cuenta
          </p>
          <ul className="grid gap-1">
            {arch.risks!.map((r, i) => (
              <li key={i} className="text-xs text-[var(--c-text-muted)]">· {r}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Educational notes */}
      {(arch.educational_notes ?? []).length > 0 && (
        <div>
          <button
            className="flex items-center gap-1.5 text-xs font-semibold text-[var(--c-accent)]"
            onClick={() => setNotesOpen(v => !v)}
          >
            <BookOpen size={12} />
            {notesOpen ? "Ocultar notas educativas" : "Ver notas educativas"}
            {notesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {notesOpen && (
            <ul className="mt-2 grid gap-1.5">
              {arch.educational_notes!.map((n, i) => (
                <li key={i} className="rounded-md bg-[var(--c-surface-2)] px-3 py-2 text-xs text-[var(--c-text-muted)]">
                  📚 {n}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Learning path */}
      {(arch.learning_path ?? []).length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">
            Ruta de aprendizaje
          </p>
          <div className="grid gap-1.5">
            {arch.learning_path!.map((res, i) => {
              const levelClass =
                res.level === "BEGINNER"     ? "text-emerald-400 border-emerald-800" :
                res.level === "INTERMEDIATE" ? "text-amber-400 border-amber-800"    :
                                               "text-rose-400 border-rose-800";
              const typeLabel: Record<string, string> = {
                docs: "Docs", course: "Curso", book: "Libro", video: "Video", article: "Artículo"
              };
              return (
                <a
                  key={i}
                  href={res.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between gap-3 rounded-md border border-[var(--c-border-subtle)] px-3 py-2 text-xs hover:border-[var(--c-border-med)] transition-colors"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium ${levelClass}`}>
                      {res.level === "BEGINNER" ? "Básico" : res.level === "INTERMEDIATE" ? "Medio" : "Avanzado"}
                    </span>
                    <span className="truncate text-[var(--c-text-muted)]">{res.title}</span>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5 text-[var(--c-text-faint)]">
                    <span>{typeLabel[res.type] ?? res.type}</span>
                    <ExternalLink size={11} />
                  </div>
                </a>
              );
            })}
          </div>
        </div>
      )}

      {/* When to upgrade */}
      {(arch.when_to_upgrade ?? []).length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">
            Cuándo escalar o migrar
          </p>
          <div className="grid gap-2">
            {arch.when_to_upgrade!.map((sig, i) => (
              <div key={i} className="rounded-md border border-[var(--c-border-subtle)] p-3">
                <p className="text-xs font-semibold text-[var(--c-text)]">
                  <Zap size={11} className="mr-1 inline text-amber-400" />
                  {sig.signal}
                </p>
                <p className="mt-0.5 text-xs text-[var(--c-text-muted)]">{sig.reason}</p>
                <p className="mt-1 text-[11px] font-medium text-[var(--c-accent)]">→ {sig.next_step}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </SpecAccordion>
  );
}

/* ─── OpenSpec card ─────────────────────────────────────────────────────── */

interface OpenSpecContent {
  project?: { name: string; sector: string; target_users: string; problem: string; description: string };
  architecture?: { type: string; name: string; stack: string[]; difficulty: string };
  requirements?: { id: string; title: string; description: string; acceptance_criteria?: string[] }[];
  user_stories?: { id: string; actor: string; goal: string; benefit: string }[];
  modules?: string[];
  milestones?: string[];
  constraints?: { delivery: string; environments: string[] };
}

function OpenSpecCard({ spec }: { readonly spec: Specification }) {
  const [open, setOpen]     = useState(false);
  const [reqOpen, setReqOpen] = useState<number | null>(null);
  const doc = spec.content as OpenSpecContent;
  const reqs = doc.requirements ?? [];
  const stories = doc.user_stories ?? [];
  const modules = doc.modules ?? [];
  const milestones = doc.milestones ?? [];

  return (
    <SpecAccordion
      icon={<FileText size={16} />}
      label="Especificación OpenSpec"
      summary={`${reqs.length} requisitos · ${stories.length} user stories · ${modules.length} módulos`}
      open={open}
      onToggle={() => setOpen(v => !v)}
    >
      {/* Project description */}
      {doc.project?.description && (
        <p className="text-sm text-[var(--c-text-muted)] leading-relaxed">{doc.project.description}</p>
      )}

      {/* Modules + Milestones row */}
      <div className="grid gap-4 sm:grid-cols-2">
        {modules.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Módulos</p>
            <div className="flex flex-wrap gap-1.5">
              {modules.map((m, i) => (
                <span key={i} className="rounded-full bg-[var(--c-surface-2)] px-3 py-1 text-xs font-medium text-[var(--c-text-muted)]">{m}</span>
              ))}
            </div>
          </div>
        )}
        {milestones.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Milestones</p>
            <ol className="grid gap-1">
              {milestones.map((ms, i) => (
                <li key={i} className="text-xs text-[var(--c-text-muted)]">{ms}</li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Requirements */}
      {reqs.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">
            Requisitos funcionales ({reqs.length})
          </p>
          <div className="grid gap-2">
            {reqs.map((r, i) => (
              <div key={i} className="rounded-lg border border-[var(--c-border-subtle)] bg-[var(--c-surface-2)]">
                <button
                  className="flex w-full items-start justify-between gap-2 p-3 text-left"
                  onClick={() => setReqOpen(reqOpen === i ? null : i)}
                >
                  <div className="min-w-0">
                    <span className="mr-2 font-mono text-xs text-[var(--c-accent)]">{r.id}</span>
                    <span className="text-sm text-[var(--c-text)]">{r.title}</span>
                  </div>
                  {reqOpen === i ? <ChevronUp size={13} className="mt-0.5 shrink-0 text-[var(--c-text-faint)]" /> : <ChevronDown size={13} className="mt-0.5 shrink-0 text-[var(--c-text-faint)]" />}
                </button>
                {reqOpen === i && (
                  <div className="border-t border-[var(--c-border-subtle)] p-3">
                    <p className="text-xs text-[var(--c-text-muted)]">{r.description}</p>
                    {(r.acceptance_criteria ?? []).length > 0 && (
                      <ul className="mt-2 grid gap-1">
                        {r.acceptance_criteria!.map((c, j) => (
                          <li key={j} className="flex items-start gap-1.5 text-xs text-[var(--c-text-faint)]">
                            <Check size={11} className="mt-0.5 shrink-0 text-[var(--c-accent)]" />
                            {c}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* User stories */}
      {stories.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">
            User stories ({stories.length})
          </p>
          <div className="grid gap-2">
            {stories.map((s, i) => (
              <div key={i} className="rounded-lg bg-[var(--c-surface-2)] px-3 py-2 text-xs text-[var(--c-text-muted)]">
                <span className="mr-2 font-mono text-[var(--c-accent)]">{s.id}</span>
                <span className="font-medium">Como {s.actor}</span>, quiero {s.goal}
                {s.benefit && <span className="text-[var(--c-text-faint)]"> para {s.benefit}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Delivery constraint */}
      {doc.constraints?.delivery && (
        <p className="text-xs text-[var(--c-text-faint)]">
          <span className="font-semibold">Entrega:</span> {doc.constraints.delivery}
          {doc.constraints.environments?.length ? ` · Entornos: ${doc.constraints.environments.join(", ")}` : ""}
        </p>
      )}
    </SpecAccordion>
  );
}

/* ─── Issues card ───────────────────────────────────────────────────────── */

interface IssueItem {
  title: string;
  body?: string;
  labels: string[];
  priority: string;
  milestone?: string | null;
}
interface IssuesContent {
  project_name?: string;
  milestones?: string[];
  issues?: IssueItem[];
  total?: number;
}

const PRIORITY_CLASS: Record<string, string> = {
  high:   "text-rose-400 bg-rose-900/30 border-rose-800",
  medium: "text-amber-400 bg-amber-900/30 border-amber-800",
  low:    "text-zinc-400 bg-zinc-800/50 border-zinc-700",
};
const PRIORITY_LABEL: Record<string, string> = {
  high: "Alta", medium: "Media", low: "Baja"
};

function IssuesCard({ spec }: { readonly spec: Specification }) {
  const [open, setOpen] = useState(false);
  const [expandedIssue, setExpandedIssue] = useState<number | null>(null);
  const data = spec.content as IssuesContent;
  const issues = data.issues ?? [];
  const milestones = data.milestones ?? [];

  // Group issues by milestone
  const grouped = milestones.reduce<Record<string, IssueItem[]>>((acc, ms) => {
    acc[ms] = issues.filter(i => i.milestone === ms);
    return acc;
  }, {});
  const ungrouped = issues.filter(i => !i.milestone || !milestones.includes(i.milestone));
  if (ungrouped.length > 0) grouped["Sin milestone"] = ungrouped;

  return (
    <SpecAccordion
      icon={<GitBranch size={16} />}
      label="Issues de GitHub"
      summary={`${issues.length} issues · ${milestones.length} milestones`}
      open={open}
      onToggle={() => setOpen(v => !v)}
    >
      {Object.entries(grouped).map(([ms, msIssues]) => msIssues.length > 0 && (
        <div key={ms}>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">
            {ms} <span className="normal-case font-normal">({msIssues.length})</span>
          </p>
          <div className="grid gap-2">
            {msIssues.map((issue, i) => {
              const globalIdx = issues.indexOf(issue);
              const isExpanded = expandedIssue === globalIdx;
              return (
                <div key={i} className="rounded-lg border border-[var(--c-border-subtle)] bg-[var(--c-surface-2)]">
                  <button
                    className="flex w-full items-start gap-2 p-3 text-left"
                    onClick={() => setExpandedIssue(isExpanded ? null : globalIdx)}
                  >
                    <span className={`mt-0.5 shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-semibold ${PRIORITY_CLASS[issue.priority] ?? PRIORITY_CLASS.low}`}>
                      {PRIORITY_LABEL[issue.priority] ?? issue.priority}
                    </span>
                    <span className="flex-1 text-sm text-[var(--c-text)]">{issue.title}</span>
                    {isExpanded
                      ? <ChevronUp size={13} className="mt-0.5 shrink-0 text-[var(--c-text-faint)]" />
                      : <ChevronDown size={13} className="mt-0.5 shrink-0 text-[var(--c-text-faint)]" />}
                  </button>
                  {issue.labels.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 px-3 pb-2">
                      {issue.labels.map((l, j) => (
                        <span key={j} className="rounded-full bg-[var(--c-surface)] px-2 py-0.5 text-[10px] text-[var(--c-text-faint)]">
                          {l}
                        </span>
                      ))}
                    </div>
                  )}
                  {isExpanded && issue.body && (
                    <div className="border-t border-[var(--c-border-subtle)] p-3">
                      <pre className="whitespace-pre-wrap text-xs text-[var(--c-text-faint)] font-sans leading-relaxed">
                        {issue.body}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </SpecAccordion>
  );
}

/* ─── Tutorial card ─────────────────────────────────────────────────────── */

interface TutorialStep {
  action: string;
  command?: string | null;
  notes?: string | null;
}
interface TutorialPhase {
  title: string;
  description: string;
  steps: TutorialStep[];
}
interface TutorialContent {
  project_name?: string;
  architecture_type?: string;
  phases?: TutorialPhase[];
  total_steps?: number;
}

function TutorialCard({ spec }: { readonly spec: Specification }) {
  const [open, setOpen]             = useState(false);
  const [activePhase, setActivePhase] = useState<number | null>(null);
  const data = spec.content as TutorialContent;
  const phases = data.phases ?? [];

  return (
    <SpecAccordion
      icon={<Terminal size={16} />}
      label="Tutorial de implementación"
      summary={`${phases.length} fases · ${data.total_steps ?? 0} pasos con comandos reales`}
      open={open}
      onToggle={() => setOpen(v => !v)}
    >
      {phases.map((phase, pi) => (
        <div key={pi} className="rounded-lg border border-[var(--c-border-subtle)]">
          <button
            className="flex w-full items-start gap-3 p-3 text-left"
            onClick={() => setActivePhase(activePhase === pi ? null : pi)}
          >
            <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-[var(--c-surface-2)] text-xs font-bold text-[var(--c-accent)]">
              {pi}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-[var(--c-text)]">{phase.title}</p>
              <p className="mt-0.5 text-xs text-[var(--c-text-muted)]">{phase.description}</p>
            </div>
            <span className="mt-0.5 shrink-0 text-xs text-[var(--c-text-faint)]">{phase.steps.length} pasos</span>
            {activePhase === pi
              ? <ChevronUp size={13} className="mt-0.5 shrink-0 text-[var(--c-text-faint)]" />
              : <ChevronDown size={13} className="mt-0.5 shrink-0 text-[var(--c-text-faint)]" />}
          </button>

          {activePhase === pi && (
            <div className="grid gap-3 border-t border-[var(--c-border-subtle)] p-3">
              {phase.steps.map((step, si) => (
                <div key={si} className="flex items-start gap-2.5">
                  <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded bg-[var(--c-surface-2)] text-[10px] font-bold text-[var(--c-text-faint)]">
                    {si + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-[var(--c-text)]">{step.action}</p>
                    {step.command && (
                      <pre className="mt-1.5 overflow-x-auto rounded-md bg-zinc-900 px-3 py-2 font-mono text-xs text-emerald-300">
                        {step.command}
                      </pre>
                    )}
                    {step.notes && (
                      <p className="mt-1 text-xs text-[var(--c-text-faint)] italic">{step.notes}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </SpecAccordion>
  );
}

/* ─── SpecAccordion wrapper ──────────────────────────────────────────────── */

function SpecAccordion({
  icon, label, summary, badge, open, onToggle, children
}: {
  readonly icon: React.ReactNode;
  readonly label: string;
  readonly summary: string;
  readonly badge?: React.ReactNode;
  readonly open: boolean;
  readonly onToggle: () => void;
  readonly children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-[var(--c-border-subtle)] bg-[var(--c-surface)]">
      <button
        className="flex w-full items-start gap-3 p-4 text-left"
        onClick={onToggle}
        aria-expanded={open}
      >
        <span className="mt-0.5 shrink-0 text-[var(--c-accent)]">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-accent)]">{label}</p>
            {badge}
          </div>
          <p className="mt-0.5 text-sm text-[var(--c-text-muted)] truncate">{summary}</p>
        </div>
        {open
          ? <ChevronUp size={16} className="mt-1 shrink-0 text-[var(--c-text-faint)]" />
          : <ChevronDown size={16} className="mt-1 shrink-0 text-[var(--c-text-faint)]" />}
      </button>
      {open && (
        <div className="grid gap-4 border-t border-[var(--c-border-subtle)] p-4">
          {children}
        </div>
      )}
    </div>
  );
}

/* ─── What's included ───────────────────────────────────────────────────── */

function WhatIsIncluded() {
  const steps = [
    { icon: <Check size={13} />, text: "Análisis de requisitos funcionales y no funcionales" },
    { icon: <Check size={13} />, text: "Recomendación de arquitectura con notas educativas" },
    { icon: <Check size={13} />, text: "OpenSpec técnico: requisitos, user stories, módulos, milestones" },
    { icon: <Check size={13} />, text: "Issues de GitHub listos para importar al repositorio" },
    { icon: <Check size={13} />, text: "Tutorial de implementación paso a paso con comandos reales" },
    { icon: <Check size={13} />, text: "Código base estructurado del proyecto" },
    { icon: <Check size={13} />, text: "ZIP con todo el proyecto listo para descargar" },
  ];

  return (
    <div className="rounded-lg border border-[var(--c-border-subtle)] p-4">
      <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-accent)]">Qué genera el pipeline</p>
      <ul className="mt-3 grid gap-2">
        {steps.map((item, i) => (
          <li key={i} className="flex items-center gap-2 text-sm text-[var(--c-text-muted)]">
            <span className="shrink-0 text-[var(--c-accent)]">{item.icon}</span>
            {item.text}
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ─── Bundle / download card ─────────────────────────────────────────────── */

function BundleCard({ bundle }: { readonly bundle: ArtifactBundle }) {
  const apiBase = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:3000/api";
  const codeFiles    = bundle.generatedContent?.files ?? [];
  const manifestFiles = Array.isArray(bundle.manifest?.files)
    ? (bundle.manifest.files as { path: string; description?: string }[])
    : [];
  const hasCode = codeFiles.length > 0;
  const fileList = hasCode ? codeFiles : manifestFiles;

  const [showGitHub, setShowGitHub] = useState(false);
  const [githubToken, setGithubToken] = useState("");
  const [repoName, setRepoName] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [pushResult, setPushResult] = useState<PushToGithubResult | null>(null);
  const [pushError, setPushError]   = useState<string | null>(null);
  const [showFiles, setShowFiles]   = useState(false);

  const pushMutation = useMutation({
    mutationFn: () =>
      api.post<PushToGithubResult>(`/artifacts/${bundle.id}/push-to-github`, { githubToken, repoName, isPrivate }).then(r => r.data),
    onSuccess: (data) => { setPushResult(data); setPushError(null); },
    onError:   (err)  => setPushError(getErrorMessage(err)),
  });

  function downloadZip() {
    const token = getAccessToken();
    if (!token) return;
    void fetch(`${apiBase}/artifacts/${bundle.id}/export`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a   = document.createElement("a");
        a.href     = url;
        a.download = `proyecto-mvp-${bundle.id}.zip`;
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  return (
    <div className="grid gap-4">
      <div className="flex items-center gap-3 rounded-xl border border-[var(--c-border-strong)] bg-[var(--c-surface)] p-5">
        <span className="grid size-12 shrink-0 place-items-center rounded-full bg-[var(--c-accent)] text-[var(--c-accent-on)]">
          <PackageCheck size={24} />
        </span>
        <div>
          <p className="font-bold">¡Tu proyecto MVP está listo!</p>
          <p className="mt-0.5 text-sm text-[var(--c-text-muted)]">
            {hasCode ? `${codeFiles.length} archivos generados` : `${manifestFiles.length} documentos incluidos`}
            {" · "}Listo para descargar
          </p>
        </div>
      </div>

      <button className="primary-button justify-center py-4 text-base" onClick={downloadZip}>
        <Download size={20} />
        Descargar ZIP del proyecto
      </button>

      {hasCode && !pushResult && (
        <button className="secondary-button justify-center" onClick={() => setShowGitHub(v => !v)} aria-expanded={showGitHub}>
          <Upload size={16} />
          {showGitHub ? "Cancelar" : "Publicar en GitHub"}
        </button>
      )}

      {showGitHub && !pushResult && (
        <form
          className="grid gap-3 rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-4"
          onSubmit={e => { e.preventDefault(); pushMutation.mutate(); }}
        >
          <p className="text-xs text-[var(--c-text-faint)]">El token se usa solo en esta operación y nunca se almacena.</p>
          <input className="input text-sm" type="password" placeholder="GitHub personal access token (ghp_...)" value={githubToken} onChange={e => setGithubToken(e.target.value)} required />
          <input className="input text-sm" placeholder="Nombre del repositorio" value={repoName} onChange={e => setRepoName(e.target.value)} required />
          <label className="check-row text-sm">
            <input type="checkbox" checked={isPrivate} onChange={e => setIsPrivate(e.target.checked)} />
            <span>Repositorio privado</span>
          </label>
          {pushError && <p className="rounded-md bg-rose-400/10 p-2 text-xs text-rose-300">{pushError}</p>}
          <button className="primary-button justify-center" type="submit" disabled={pushMutation.isPending || !githubToken || !repoName}>
            <Upload size={15} />
            {pushMutation.isPending ? "Publicando..." : "Publicar en GitHub"}
          </button>
        </form>
      )}

      {pushResult && (
        <div className="rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-4">
          <p className="text-sm font-semibold text-[var(--c-accent)]">Repositorio creado</p>
          <a href={pushResult.repoUrl} target="_blank" rel="noopener noreferrer" className="mt-1 flex items-center gap-1 break-all text-xs text-[var(--c-text-muted)] underline">
            {pushResult.repoUrl}<ExternalLink size={10} className="shrink-0" />
          </a>
        </div>
      )}

      {fileList.length > 0 && (
        <div className="rounded-xl border border-[var(--c-border-subtle)]">
          <button className="flex w-full items-center justify-between p-3 text-left" onClick={() => setShowFiles(v => !v)}>
            <span className="text-xs font-semibold text-[var(--c-text-muted)]">Ver {fileList.length} archivos incluidos</span>
            {showFiles ? <ChevronUp size={15} className="text-[var(--c-text-faint)]" /> : <ChevronDown size={15} className="text-[var(--c-text-faint)]" />}
          </button>
          {showFiles && (
            <ul className="grid gap-1.5 border-t border-[var(--c-border-subtle)] p-3">
              {fileList.map((file, i) => {
                const entry = file as { path?: string; description?: string };
                return (
                  <li key={i} className="rounded-md bg-[var(--c-surface-2)] px-3 py-2">
                    <span className="block font-mono text-xs text-[var(--c-accent)]">{entry.path}</span>
                    {entry.description && <span className="mt-0.5 block text-xs text-[var(--c-text-faint)]">{entry.description}</span>}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Helpers ────────────────────────────────────────────────────────────── */

function Field({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div>
      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">{label}</p>
      <p className="text-[var(--c-text-muted)]">{value}</p>
    </div>
  );
}

function Tag({ children }: { readonly children: React.ReactNode }) {
  return (
    <span className="rounded border border-[var(--c-border-med)] px-2 py-0.5 text-xs text-[var(--c-text-faint)]">
      {children}
    </span>
  );
}

/* ─── Status labels ──────────────────────────────────────────────────────── */

const STATUS_LABELS: Record<Project["status"], string> = {
  DRAFT: "Borrador",
  REQUIREMENTS_READY: "Requisitos listos",
  SPEC_READY: "OpenSpec listo",
  GENERATING: "Generando...",
  GENERATED: "MVP generado",
  REVIEW: "En revisión",
  DEPLOYED: "Publicado"
};

/* ─── Main page ─────────────────────────────────────────────────────────── */

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate      = useNavigate();
  const queryClient   = useQueryClient();
  const [ideaOpen, setIdeaOpen]         = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/projects/${projectId}`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      void navigate("/");
    }
  });

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn:  async () => (await api.get<Project>(`/projects/${projectId}`)).data,
    enabled:  Boolean(projectId),
  });

  const refetch = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
  }, [queryClient, projectId]);

  const pipeline = useGeneratePipeline(projectId, refetch);

  const project      = projectQuery.data;
  const specs        = project?.specifications ?? [];
  const latestBundle = project?.artifactBundles?.[0];
  const isGenerated  = ["GENERATED", "REVIEW", "DEPLOYED"].includes(project?.status ?? "");

  const archSpec     = specs.find(s => s.type === "ARCHITECTURE" && s.status === "GENERATED");
  const openSpec     = specs.find(s => s.type === "OPENSPEC"      && s.status === "GENERATED");
  const issuesSpec   = specs.find(s => s.type === "ISSUES"        && s.status === "GENERATED"
    && Array.isArray((s.content as IssuesContent).issues));
  const tutorialSpec = specs.find(s => s.type === "TUTORIAL"      && s.status === "GENERATED");

  if (projectQuery.isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <div className="h-8 w-24 animate-pulse rounded bg-[var(--c-surface-2)]" />
        <div className="h-24 animate-pulse rounded-xl bg-[var(--c-surface-2)]" />
        <div className="h-48 animate-pulse rounded-xl bg-[var(--c-surface-2)]" />
      </div>
    );
  }

  if (projectQuery.isError || !project) {
    return (
      <div className="mx-auto max-w-2xl grid gap-4">
        <Link className="subtle-link inline-flex w-fit items-center gap-1.5 text-sm" to="/">
          <ArrowLeft size={15} /> Volver
        </Link>
        <p className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">
          No se pudo cargar el proyecto. Comprueba tu acceso o recarga la página.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl grid gap-6">
      {/* Back */}
      <Link className="subtle-link inline-flex w-fit items-center gap-1.5 text-sm" to="/">
        <ArrowLeft size={15} /> Todos los proyectos
      </Link>

      {/* Header */}
      <div>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-accent)]">{project.sector}</p>
            <h1 className="mt-1 text-3xl font-bold">{project.name}</h1>
            {project.description && (
              <p className="mt-2 text-sm text-[var(--c-text-muted)]">{project.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="status-pill">{STATUS_LABELS[project.status]}</span>
            <button
              onClick={() => setConfirmDelete(true)}
              disabled={pipeline.isRunning}
              title="Eliminar proyecto"
              className="icon-button text-[var(--c-text-faint)] hover:border-rose-500/40 hover:bg-rose-500/10 hover:text-rose-400 disabled:opacity-40"
            >
              <Trash2 size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Confirm delete dialog */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-sm rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-bg)] p-6 shadow-2xl">
            <h2 className="font-bold text-lg">¿Eliminar proyecto?</h2>
            <p className="mt-2 text-sm text-[var(--c-text-muted)]">
              Se borrarán permanentemente <strong className="text-[var(--c-text)]">{project.name}</strong> y todos
              sus datos. Esta acción no se puede deshacer.
            </p>
            {deleteMutation.isError && (
              <p className="mt-3 rounded-lg bg-rose-500/10 border border-rose-500/30 px-3 py-2 text-sm text-rose-400">
                {getErrorMessage(deleteMutation.error)}
              </p>
            )}
            <div className="mt-5 flex gap-3 justify-end">
              <button className="secondary-button" onClick={() => setConfirmDelete(false)} disabled={deleteMutation.isPending}>
                Cancelar
              </button>
              <button
                className="flex items-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700 transition disabled:opacity-60"
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                {deleteMutation.isPending ? "Eliminando..." : "Eliminar proyecto"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Idea summary */}
      {project.idea && (
        <IdeaSummary idea={project.idea} open={ideaOpen} onToggle={() => setIdeaOpen(v => !v)} />
      )}

      {/* ── Pre-generation ─────────────────────────────────────── */}
      {!isGenerated && !pipeline.isRunning && pipeline.stage !== "done" && (
        <div className="grid gap-4">
          <WhatIsIncluded />
          <button
            className="primary-button justify-center py-4 text-base"
            onClick={pipeline.start}
            disabled={!project.idea}
            title={project.idea ? undefined : "Necesitas añadir una idea primero"}
          >
            <Zap size={20} />
            Generar mi MVP completo con IA
          </button>
          {!project.idea && (
            <p className="text-center text-sm text-[var(--c-text-muted)]">
              Este proyecto no tiene idea definida.{" "}
              <Link className="subtle-link underline" to="/projects/new">Crea uno nuevo</Link> con el asistente guiado.
            </p>
          )}
        </div>
      )}

      {/* ── Pipeline running ──────────────────────────────────── */}
      {pipeline.isRunning && (
        <div className="grid gap-4">
          <div className="rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-accent)]">Generando tu MVP</p>
            <p className="mt-1 text-sm text-[var(--c-text-muted)]">
              Esto puede tardar entre 2 y 5 minutos. No cierres esta página.
            </p>
          </div>
          <PipelineProgress stage={pipeline.stage} />
        </div>
      )}

      {/* ── Error state ───────────────────────────────────────── */}
      {pipeline.stage === "error" && pipeline.error && (
        <div className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-rose-300">Ha ocurrido un error</p>
              <p className="mt-1 text-sm text-rose-300/80">{pipeline.error}</p>
            </div>
            <button onClick={pipeline.reset} className="shrink-0 text-rose-300 hover:text-rose-100">
              <X size={18} />
            </button>
          </div>
          <button className="secondary-button mt-4 gap-2" onClick={pipeline.start}>
            <RefreshCw size={15} /> Reintentar
          </button>
        </div>
      )}

      {/* ── Pipeline just finished ───────────────────────────── */}
      {pipeline.stage === "done" && (
        <div className="rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Rocket size={16} className="text-[var(--c-accent)]" />
            Generación completada — recargando datos...
          </div>
        </div>
      )}

      {/* ── Generated: bundle + spec cards ───────────────────── */}
      {isGenerated && latestBundle && <BundleCard bundle={latestBundle} />}

      {isGenerated && (archSpec || openSpec || issuesSpec || tutorialSpec) && (
        <div className="grid gap-3">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-text-faint)]">
            Especificaciones generadas
          </p>
          {archSpec     && <ArchitectureCard spec={archSpec} />}
          {openSpec     && <OpenSpecCard     spec={openSpec} />}
          {issuesSpec   && <IssuesCard       spec={issuesSpec} />}
          {tutorialSpec && <TutorialCard     spec={tutorialSpec} />}
        </div>
      )}

      {/* ── Regenerate ────────────────────────────────────────── */}
      {isGenerated && !pipeline.isRunning && (
        <div className="border-t border-[var(--c-border-subtle)] pt-4">
          <button className="secondary-button text-sm" onClick={pipeline.reset}>
            <RefreshCw size={14} /> Regenerar proyecto
          </button>
          <p className="mt-2 text-xs text-[var(--c-text-faint)]">
            Regenerar reemplazará el kit actual con una nueva versión.
          </p>
        </div>
      )}

      {/* ── Previous bundles ──────────────────────────────────── */}
      {isGenerated && (project.artifactBundles ?? []).length > 1 && (
        <details className="rounded-xl border border-[var(--c-border-subtle)]">
          <summary className="cursor-pointer p-4 text-sm text-[var(--c-text-muted)]">
            Ver versiones anteriores ({project.artifactBundles!.length - 1} más)
          </summary>
          <ul className="grid gap-3 border-t border-[var(--c-border-subtle)] p-4">
            {project.artifactBundles!.slice(1).map(bundle => (
              <li key={bundle.id}>
                <div className="flex items-center justify-between gap-3 rounded-lg border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-3 text-sm">
                  <div>
                    <p className="font-mono text-xs text-[var(--c-text-faint)]">{bundle.id}</p>
                    <p className="mt-0.5 text-xs text-[var(--c-text-faint)]">{new Date(bundle.createdAt).toLocaleDateString("es-ES")}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {(bundle.generatedContent?.files ?? []).length > 0 && (
                      <span className="text-xs text-[var(--c-text-faint)]">
                        <Code2 size={11} className="mr-1 inline" />
                        {bundle.generatedContent!.files.length} archivos
                      </span>
                    )}
                    <span className="status-pill">{bundle.status}</span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
