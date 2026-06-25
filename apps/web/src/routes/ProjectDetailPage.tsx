import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle, ArrowLeft, BookOpen, Check, ChevronDown, ChevronUp,
  Code2, Cpu, Database, Download, ExternalLink, FileText, GitBranch, Layers,
  Loader2, PackageCheck, RefreshCw, Rocket, Terminal, Trash2, Upload, X, Zap
} from "lucide-react";
import { useCallback, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api, getErrorMessage } from "../lib/api";
import { getAccessToken } from "../lib/auth-token";
import {
  PIPELINE_STEPS, PipelineStage,
  stageToStepIndex, useGeneratePipeline
} from "../hooks/useGeneratePipeline";
import { ArtifactBundle, Project, PushToGithubResult, Specification, TechProposal, TechProposalContent } from "../types/api";
import { STATUS_LABELS } from "../constants/status";

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

      <div className="flex justify-end gap-2">
        <button className="secondary-button gap-2 text-sm" onClick={() => downloadSpecification(spec, "md")}>
          <Download size={15} />
          Descargar MD
        </button>
        <button className="secondary-button gap-2 text-sm" onClick={() => downloadSpecification(spec, "pdf")}>
          <Download size={15} />
          Descargar PDF
        </button>
      </div>

      {/* When to upgrade — kept inline as architecture context */}
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

function downloadSpecification(spec: Specification, format: "pdf" | "md") {
  const token = getAccessToken();
  if (!token) return;
  const apiBase = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:3000/api";
  void fetch(`${apiBase}/specifications/${spec.id}/export-${format}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(response => {
      if (!response.ok) throw new Error(`No se pudo generar el ${format.toUpperCase()}`);
      return response.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `progresia-spec-${spec.id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    });
}

function LearningItineraryCard({ spec }: { readonly spec: Specification }) {
  const [open, setOpen] = useState(false);
  const arch = spec.content as ArchContent;
  const resources = arch.learning_path ?? [];

  if (resources.length === 0) return null;

  const byLevel: Record<string, typeof resources> = {};
  for (const r of resources) {
    const key = r.level ?? "OTHER";
    if (!byLevel[key]) byLevel[key] = [];
    byLevel[key].push(r);
  }

  const levelOrder = ["BEGINNER", "INTERMEDIATE", "ADVANCED"];
  const levelLabel: Record<string, string> = {
    BEGINNER: "Básico", INTERMEDIATE: "Intermedio", ADVANCED: "Avanzado",
  };
  const levelClass: Record<string, string> = {
    BEGINNER: "text-emerald-400 border-emerald-800",
    INTERMEDIATE: "text-amber-400 border-amber-800",
    ADVANCED: "text-rose-400 border-rose-800",
  };
  const typeLabel: Record<string, string> = {
    docs: "Docs", course: "Curso", book: "Libro", video: "Video", article: "Artículo",
  };

  return (
    <SpecAccordion
      icon={<BookOpen size={16} />}
      label="Itinerario formativo"
      summary={`${resources.length} recursos de aprendizaje personalizados`}
      open={open}
      onToggle={() => setOpen(v => !v)}
    >
      {levelOrder.filter(l => byLevel[l]).map(level => (
        <div key={level}>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">
            Nivel {levelLabel[level] ?? level}
          </p>
          <div className="grid gap-1.5 mb-3">
            {byLevel[level].map((res, i) => (
              <a key={i} href={res.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center justify-between gap-3 rounded-md border border-[var(--c-border-subtle)] px-3 py-2 text-xs hover:border-[var(--c-border-med)] transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium ${levelClass[level] ?? ""}`}>
                    {levelLabel[level] ?? level}
                  </span>
                  <span className="truncate text-[var(--c-text-muted)]">{res.title}</span>
                </div>
                <div className="flex shrink-0 items-center gap-1.5 text-[var(--c-text-faint)]">
                  <span>{typeLabel[res.type] ?? res.type}</span>
                  <ExternalLink size={11} />
                </div>
              </a>
            ))}
          </div>
        </div>
      ))}
    </SpecAccordion>
  );
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
      <div className="flex justify-end">
        <button className="secondary-button gap-2 text-sm" onClick={() => downloadSpecification(spec, "pdf")}>
          <Download size={15} />
          Descargar PDF
        </button>
      </div>

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
      <div className="flex justify-end gap-2">
        <button className="secondary-button gap-2 text-sm" onClick={() => downloadSpecification(spec, "md")}>
          <Download size={15} />
          Descargar MD
        </button>
        <button className="secondary-button gap-2 text-sm" onClick={() => downloadSpecification(spec, "pdf")}>
          <Download size={15} />
          Descargar PDF
        </button>
      </div>

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
      <div className="flex justify-end gap-2">
        <button className="secondary-button gap-2 text-sm" onClick={() => downloadSpecification(spec, "md")}>
          <Download size={15} />
          Descargar MD
        </button>
        <button className="secondary-button gap-2 text-sm" onClick={() => downloadSpecification(spec, "pdf")}>
          <Download size={15} />
          Descargar PDF
        </button>
      </div>

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

/* ─── Data Model card ────────────────────────────────────────────────────── */

interface DataModelContent {
  data_model?: {
    storage_type?: string;
    technology?: string;
    justification?: string;
    orm?: string;
    orm_rationale?: string;
    relationships?: { from_entity: string; to_entity: string; type: string; label?: string; cascade_delete?: boolean; optional?: boolean }[];
    indexes?: string[];
    mermaid_diagram?: string;
    seed_needed?: boolean;
    seed_instructions?: string[];
    security_notes?: string[];
    mvp_scope?: string[];
    future_scope?: string[];
  };
  data_entities?: { name: string; description?: string; fields?: string[]; relations?: string[] }[];
}

const REL_TYPE_LABEL: Record<string, string> = {
  one_to_one: "1:1", one_to_many: "1:N", many_to_many: "N:M"
};

function DataModelCard({ spec }: { readonly spec: Specification }) {
  const [open, setOpen]         = useState(false);
  const [entityOpen, setEntityOpen] = useState<number | null>(null);
  const doc = spec.content as DataModelContent;
  const dm  = doc.data_model ?? {};
  const entities     = doc.data_entities ?? [];
  const relationships = dm.relationships ?? [];
  const indexes       = dm.indexes ?? [];
  const security      = dm.security_notes ?? [];
  const seedInstr     = dm.seed_instructions ?? [];
  const mvpScope      = dm.mvp_scope ?? [];
  const futureScope   = dm.future_scope ?? [];

  const summary = [
    dm.technology ?? "PostgreSQL",
    dm.orm ? `· ${dm.orm}` : "",
    entities.length > 0 ? `· ${entities.length} entidades` : "",
  ].filter(Boolean).join(" ");

  return (
    <SpecAccordion
      icon={<Database size={16} />}
      label="Modelo de datos y base de datos"
      summary={summary}
      open={open}
      onToggle={() => setOpen(v => !v)}
    >
      {/* Technology + ORM pills */}
      <div className="flex flex-wrap gap-2">
        {dm.technology && (
          <span className="rounded-full border border-[var(--c-border-med)] px-3 py-1 font-mono text-xs text-[var(--c-text-muted)]">
            {dm.storage_type === "relational" ? "🗄️" : dm.storage_type === "document" ? "📄" : "🔮"} {dm.technology}
          </span>
        )}
        {dm.orm && (
          <span className="rounded-full border border-[var(--c-border-med)] px-3 py-1 font-mono text-xs text-[var(--c-text-muted)]">
            ORM: {dm.orm}
          </span>
        )}
      </div>

      {/* Justification */}
      {dm.justification && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Por qué esta base de datos</p>
          <p className="text-sm text-[var(--c-text-muted)] leading-relaxed">{dm.justification}</p>
        </div>
      )}
      {dm.orm_rationale && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Por qué este ORM</p>
          <p className="text-sm text-[var(--c-text-muted)] leading-relaxed">{dm.orm_rationale}</p>
        </div>
      )}

      {/* Entities */}
      {entities.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">
            Entidades principales ({entities.length})
          </p>
          <div className="grid gap-2">
            {entities.map((entity, i) => (
              <div key={i} className="rounded-lg border border-[var(--c-border-subtle)] bg-[var(--c-surface-2)]">
                <button
                  className="flex w-full items-center justify-between gap-2 p-3 text-left"
                  onClick={() => setEntityOpen(entityOpen === i ? null : i)}
                >
                  <span className="font-mono text-sm font-semibold text-[var(--c-text)]">{entity.name}</span>
                  <div className="flex items-center gap-2">
                    {entity.fields && (
                      <span className="text-xs text-[var(--c-text-faint)]">{entity.fields.length} campos</span>
                    )}
                    {entityOpen === i
                      ? <ChevronUp size={13} className="shrink-0 text-[var(--c-text-faint)]" />
                      : <ChevronDown size={13} className="shrink-0 text-[var(--c-text-faint)]" />}
                  </div>
                </button>
                {entityOpen === i && (
                  <div className="border-t border-[var(--c-border-subtle)] p-3 grid gap-2">
                    {entity.description && (
                      <p className="text-xs text-[var(--c-text-muted)]">{entity.description}</p>
                    )}
                    {(entity.fields ?? []).length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-left text-[var(--c-text-faint)]">
                              <th className="pb-1 pr-4 font-semibold">Campo</th>
                              <th className="pb-1 font-semibold">Definición</th>
                            </tr>
                          </thead>
                          <tbody>
                            {entity.fields!.map((field, j) => {
                              const [name, ...rest] = field.split(":");
                              return (
                                <tr key={j} className="border-t border-[var(--c-border-subtle)]">
                                  <td className="py-1 pr-4 font-mono text-[var(--c-accent)]">{name.trim()}</td>
                                  <td className="py-1 text-[var(--c-text-faint)]">{rest.join(":").trim()}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                    {(entity.relations ?? []).filter(Boolean).length > 0 && (
                      <p className="text-xs text-[var(--c-text-faint)]">
                        <span className="font-semibold">Relaciones:</span>{" "}
                        {entity.relations!.filter(Boolean).join(" · ")}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relationships */}
      {relationships.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Relaciones</p>
          <div className="grid gap-1.5">
            {relationships.map((r, i) => (
              <div key={i} className="flex items-center gap-2 rounded-md bg-[var(--c-surface-2)] px-3 py-2 text-xs">
                <span className="font-mono font-semibold text-[var(--c-accent)]">{r.from_entity}</span>
                <span className="rounded border border-[var(--c-border-med)] px-1.5 py-0.5 text-[var(--c-text-faint)]">
                  {REL_TYPE_LABEL[r.type] ?? r.type}
                </span>
                <span className="font-mono font-semibold text-[var(--c-accent)]">{r.to_entity}</span>
                {r.label && <span className="text-[var(--c-text-faint)]">"{r.label}"</span>}
                {r.cascade_delete && <span className="ml-auto text-amber-400">CASCADE</span>}
                {r.optional && <span className="ml-auto text-zinc-500">opcional</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mermaid diagram */}
      {dm.mermaid_diagram && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Diagrama ER</p>
          <pre className="overflow-x-auto rounded-lg bg-zinc-900 p-4 font-mono text-xs text-emerald-300 leading-relaxed whitespace-pre">
            {dm.mermaid_diagram}
          </pre>
          <p className="mt-1 text-[10px] text-[var(--c-text-faint)]">
            Copia este bloque en{" "}
            <a href="https://mermaid.live" target="_blank" rel="noopener noreferrer" className="underline">
              mermaid.live
            </a>{" "}
            para visualizarlo.
          </p>
        </div>
      )}

      {/* Indexes */}
      {indexes.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Índices recomendados</p>
          <pre className="overflow-x-auto rounded-lg bg-zinc-900 p-3 font-mono text-xs text-sky-300">
            {indexes.join("\n")}
          </pre>
        </div>
      )}

      {/* MVP scope */}
      {(mvpScope.length > 0 || futureScope.length > 0) && (
        <div className="grid gap-2 sm:grid-cols-2">
          {mvpScope.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-emerald-400">MVP</p>
              <div className="flex flex-wrap gap-1">
                {mvpScope.map((e, i) => (
                  <span key={i} className="rounded border border-emerald-800 px-2 py-0.5 font-mono text-xs text-emerald-400">{e}</span>
                ))}
              </div>
            </div>
          )}
          {futureScope.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-500">Fase futura</p>
              <div className="flex flex-wrap gap-1">
                {futureScope.map((e, i) => (
                  <span key={i} className="rounded border border-zinc-700 px-2 py-0.5 font-mono text-xs text-zinc-500">{e}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Seed instructions */}
      {seedInstr.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--c-text-faint)]">Seeds y migraciones</p>
          <ul className="grid gap-1">
            {seedInstr.map((s, i) => (
              <li key={i} className="rounded-md bg-[var(--c-surface-2)] px-3 py-2 font-mono text-xs text-[var(--c-text-muted)]">
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Security notes */}
      {security.length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
          <p className="mb-2 text-xs font-semibold text-amber-400">🔒 Seguridad y privacidad</p>
          <ul className="grid gap-1">
            {security.map((n, i) => (
              <li key={i} className="text-xs text-[var(--c-text-muted)]">· {n}</li>
            ))}
          </ul>
        </div>
      )}
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
  const [validation, setValidation] = useState<{
    valid: boolean; canDownload: boolean; fileCount: number; hasCode: boolean; hasSdd: boolean; hasReadme: boolean;
    hasEnvExample?: boolean; hasDockerCompose?: boolean; hasDocs?: boolean;
    issues: Array<{ message: string; severity: "error" | "warning" }>;
  } | null>(null);

  const summaryQuery = useQuery({
    queryKey: ["artifact-summary", bundle.id],
    queryFn: () => api.get<{
      projectName: string;
      stack: string[];
      modules: string[];
      services: Array<{ name: string; port: number; url: string }>;
      costs: Record<string, string>;
      prerequisites: string[];
      quickstart: string[];
      nextSteps: string[];
      fileCount: number;
    }>(`/artifacts/${bundle.id}/summary`).then(r => r.data),
  });

  const pushMutation = useMutation({
    mutationFn: () =>
      api.post<PushToGithubResult>(`/artifacts/${bundle.id}/push-to-github`, { githubToken, repoName, isPrivate }).then(r => r.data),
    onSuccess: (data) => { setPushResult(data); setPushError(null); },
    onError:   (err)  => setPushError(getErrorMessage(err)),
  });

  const validateMutation = useMutation({
    mutationFn: () => api.get<typeof validation>(`/artifacts/${bundle.id}/validate`).then(r => r.data),
    onSuccess: (data) => setValidation(data),
  });

  const [downloadError, setDownloadError] = useState<string | null>(null);

  function downloadZip() {
    if (validation && !validation.canDownload) return;
    const token = getAccessToken();
    if (!token) return;
    setDownloadError(null);
    void fetch(`${apiBase}/artifacts/${bundle.id}/export`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async r => {
        if (!r.ok) {
          const err = await r.json().catch(() => ({ message: "Error desconocido al generar el ZIP" })) as { message?: string };
          throw new Error(err.message ?? "No se pudo descargar el ZIP");
        }
        return r.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a   = document.createElement("a");
        a.href     = url;
        a.download = `proyecto-mvp-${bundle.id}.zip`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 100);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Error al descargar el ZIP";
        setDownloadError(msg);
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

      {/* Validation result */}
      {validation && (
        <div className={`rounded-xl border p-4 text-sm ${
          validation.valid
            ? "border-emerald-500/30 bg-emerald-500/10"
            : "border-amber-500/30 bg-amber-500/10"
        }`}>
          <div className="flex items-center gap-2 font-semibold">
            {validation.valid
              ? <><Check size={15} className="text-emerald-400" /> <span className="text-emerald-300">Bundle válido — {validation.fileCount} archivos</span></>
              : <><AlertTriangle size={15} className="text-amber-400" /> <span className="text-amber-300">Se encontraron advertencias</span></>}
          </div>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {validation.hasCode    && <span className="rounded border border-emerald-700 px-2 py-0.5 text-emerald-400">✓ Código</span>}
            {validation.hasSdd     && <span className="rounded border border-emerald-700 px-2 py-0.5 text-emerald-400">✓ SDD</span>}
            {validation.hasReadme  && <span className="rounded border border-emerald-700 px-2 py-0.5 text-emerald-400">✓ README</span>}
          </div>
          {validation.issues.length > 0 && (
            <ul className="mt-2 grid gap-1">
              {validation.issues.map((issue, i) => (
                <li key={i} className={`flex items-start gap-1.5 text-xs ${issue.severity === "error" ? "text-red-300" : "text-amber-300"}`}>
                  <AlertTriangle size={11} className="mt-0.5 shrink-0" />{issue.message}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {summaryQuery.data && (
        <div className="rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-text-faint)]">Resumen antes de descargar</p>
              <p className="mt-1 font-semibold">{summaryQuery.data.projectName}</p>
              <p className="mt-1 text-xs text-[var(--c-text-muted)]">
                {summaryQuery.data.fileCount} archivos · {summaryQuery.data.stack.slice(0, 4).join(" · ") || "Stack pendiente"}
              </p>
            </div>
            <span className="rounded border border-[var(--c-border-med)] px-2 py-1 text-xs text-[var(--c-text-faint)]">
              {summaryQuery.data.services.length} servicios
            </span>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold text-[var(--c-text-muted)]">Servicios</p>
              <ul className="mt-1 grid gap-1 text-xs text-[var(--c-text-faint)]">
                {summaryQuery.data.services.slice(0, 5).map(service => (
                  <li key={`${service.name}-${service.port}`}>{service.name}: {service.url}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold text-[var(--c-text-muted)]">Siguiente paso</p>
              <ul className="mt-1 grid gap-1 text-xs text-[var(--c-text-faint)]">
                {summaryQuery.data.nextSteps.slice(0, 3).map(step => <li key={step}>{step}</li>)}
              </ul>
            </div>
          </div>
          <details className="mt-3">
            <summary className="cursor-pointer text-xs font-semibold text-[var(--c-accent)]">Ver comandos y costes</summary>
            <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-[var(--c-surface-2)] p-3 text-xs text-[var(--c-text-muted)]">
{summaryQuery.data.quickstart.join("\n")}
            </pre>
            <ul className="mt-2 grid gap-1 text-xs text-[var(--c-text-faint)]">
              {Object.entries(summaryQuery.data.costs).map(([key, value]) => <li key={key}>{key}: {value}</li>)}
            </ul>
          </details>
        </div>
      )}

      <div className="flex gap-2">
        <button className="primary-button flex-1 justify-center py-4 text-base" onClick={downloadZip} disabled={validation?.canDownload === false}>
          <Download size={20} />
          {validation?.canDownload === false ? "Corrige errores antes de descargar" : "Descargar ZIP"}
        </button>
        <button
          className="secondary-button px-4"
          onClick={() => validateMutation.mutate()}
          disabled={validateMutation.isPending}
          title="Validar coherencia del bundle antes de descargar"
        >
          {validateMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
        </button>
      </div>

      {downloadError && (
        <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

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

/* ─── Tech Proposal Section ──────────────────────────────────────────────── */

function TechProposalSection({
  projectId,
  existingSpec,
  mandatoryTechs,
  onProposed,
}: {
  readonly projectId: string;
  readonly existingSpec: Specification | undefined;
  readonly mandatoryTechs?: string | null;
  readonly onProposed: () => void;
}) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  const proposeMutation = useMutation({
    mutationFn: () => api.post<TechProposalContent>(`/specifications/project/${projectId}/propose-tech`),
    onSuccess: () => { onProposed(); },
  });

  const content = existingSpec
    ? (existingSpec.content as unknown as TechProposalContent)
    : proposeMutation.data?.data ?? null;

  if (!content && !proposeMutation.isPending) {
    return (
      <div className="rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-5">
        <div className="flex items-start gap-3">
          <Cpu size={18} className="mt-0.5 shrink-0 text-[var(--c-accent)]" />
          <div className="min-w-0 flex-1">
            <p className="font-semibold">Propuestas de tecnología</p>
            <p className="mt-1 text-sm text-[var(--c-text-muted)]">
              Antes de generar el MVP, obtén 3 propuestas de stack adaptadas a tu proyecto y nivel técnico.
            </p>
            {mandatoryTechs && (
              <p className="mt-2 flex items-center gap-1.5 text-xs text-[var(--c-text-faint)]">
                <span className="rounded border border-[var(--c-border-med)] bg-[var(--c-surface-2)] px-1.5 py-0.5 font-mono text-[10px]">
                  {mandatoryTechs}
                </span>
                <span>— tecnologías que has indicado como obligatorias</span>
              </p>
            )}
          </div>
        </div>
        {proposeMutation.isError && (
          <p className="mt-3 rounded-lg bg-amber-400/10 p-3 text-xs text-amber-300">
            {getErrorMessage(proposeMutation.error)} — se continuará con la arquitectura por defecto.
          </p>
        )}
        <button
          className="secondary-button mt-4 gap-2 text-sm"
          onClick={() => proposeMutation.mutate()}
        >
          <Cpu size={15} /> Ver propuestas de tecnología
        </button>
      </div>
    );
  }

  if (proposeMutation.isPending) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] p-5 text-sm text-[var(--c-text-muted)]">
        <Loader2 size={16} className="animate-spin text-[var(--c-accent)]" />
        Analizando tu proyecto y preparando propuestas de stack...
      </div>
    );
  }

  if (!content) return null;

  return (
    <div className="grid gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-text-faint)]">
          Propuestas de tecnología
        </p>
        {selectedId !== null && (
          <span className="rounded-full border border-[var(--c-accent)] px-2 py-0.5 text-xs text-[var(--c-accent)]">
            Stack seleccionado ✓
          </span>
        )}
      </div>

      <div className="rounded-xl border border-[var(--c-border-subtle)] bg-[var(--c-surface)] px-4 py-3 text-sm">
        <span className="text-[var(--c-accent)]">💡 </span>
        <span className="text-[var(--c-text-muted)]">{content.recommendation_reason}</span>
      </div>

      <div className="grid gap-2">
        {content.proposals.map((p: TechProposal) => {
          const isSelected = selectedId === p.id;
          const isRecommended = p.id === content.recommended_id;
          const isExpanded = expanded === p.id;
          return (
            <div key={p.id} className={`rounded-xl border transition-colors ${
              isSelected
                ? "border-[var(--c-accent)] ring-1 ring-[var(--c-accent)] bg-[var(--c-active-bg)]"
                : "border-[var(--c-border-subtle)] bg-[var(--c-surface)]"
            }`}>
              <button
                className="flex w-full items-start gap-3 p-4 text-left"
                onClick={() => { setSelectedId(p.id); setExpanded(isExpanded ? null : p.id); }}
              >
                <span className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-full border-2 ${
                  isSelected ? "border-[var(--c-accent)] bg-[var(--c-accent)]" : "border-[var(--c-border-med)]"
                }`}>
                  {isSelected && <span className="size-2 rounded-full bg-[var(--c-accent-on)]" />}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold">{p.name}</p>
                    {isRecommended && (
                      <span className="rounded-full bg-[var(--c-accent)]/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--c-accent)]">
                        Recomendado
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-xs text-[var(--c-text-muted)]">{p.tagline}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {p.stack.map(t => (
                      <span key={t} className="rounded border border-[var(--c-border-med)] bg-[var(--c-surface-2)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--c-text-muted)]">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <span className="mt-1 shrink-0 text-[var(--c-text-faint)]">
                  {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                </span>
              </button>

              {isExpanded && (
                <div className="grid gap-3 border-t border-[var(--c-border-subtle)] p-4 text-sm">
                  <p className="text-[var(--c-text-muted)]">{p.description}</p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-400">Ventajas</p>
                      <ul className="grid gap-1">
                        {p.advantages.map((a, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-[var(--c-text-muted)]">
                            <Check size={11} className="mt-0.5 shrink-0 text-emerald-400" />{a}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-amber-400">Limitaciones</p>
                      <ul className="grid gap-1">
                        {p.limitations.map((l, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-[var(--c-text-muted)]">
                            <AlertTriangle size={11} className="mt-0.5 shrink-0 text-amber-400" />{l}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  {p.learning_outcomes.length > 0 && (
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--c-text-faint)]">Aprenderás</p>
                      <div className="flex flex-wrap gap-1.5">
                        {p.learning_outcomes.map((lo, i) => (
                          <span key={i} className="rounded-full border border-[var(--c-border-med)] px-2 py-0.5 text-xs text-[var(--c-text-faint)]">
                            {lo}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="flex flex-wrap gap-3 text-xs text-[var(--c-text-faint)]">
                    <span className={`rounded border px-2 py-0.5 ${
                      p.difficulty === "Principiante"
                        ? "border-emerald-800 text-emerald-400"
                        : "border-amber-800 text-amber-400"
                    }`}>{p.difficulty}</span>
                    {p.docker_ready && <span className="rounded border border-[var(--c-border-med)] px-2 py-0.5">🐳 Docker-ready</span>}
                    {p.ai_ready    && <span className="rounded border border-[var(--c-border-med)] px-2 py-0.5">🤖 IA integrable</span>}
                    <span className="rounded border border-[var(--c-border-med)] px-2 py-0.5">⏱ ~{p.estimated_setup_minutes} min setup</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
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
      queryClient.removeQueries({ queryKey: ["project", projectId] });
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

  const archSpec          = specs.find(s => s.type === "ARCHITECTURE"  && s.status === "GENERATED");
  const openSpec          = specs.find(s => s.type === "OPENSPEC"       && s.status === "GENERATED");
  const issuesSpec        = specs.find(s => s.type === "ISSUES"         && s.status === "GENERATED"
    && Array.isArray((s.content as IssuesContent).issues));
  const tutorialSpec      = specs.find(s => s.type === "TUTORIAL"       && s.status === "GENERATED");
  const techProposalSpec  = specs.find(s => s.type === "TECH_PROPOSAL"  && s.status === "GENERATED");

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
          {project.idea && (
            <TechProposalSection
              projectId={projectId!}
              existingSpec={techProposalSpec}
              mandatoryTechs={project.idea?.mandatoryTechs}
              onProposed={refetch}
            />
          )}
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
            <div className="flex items-center gap-3">
              <Loader2 size={22} className="shrink-0 animate-spin text-[var(--c-accent)]" />
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-accent)]">
                  {isGenerated ? "Regenerando tu proyecto" : "Generando tu MVP"}
                </p>
                <p className="mt-1 text-sm text-[var(--c-text-muted)]">
                  {isGenerated
                    ? "El proyecto anterior no está disponible durante la regeneración. Esto puede tardar entre 2 y 5 minutos."
                    : "Esto puede tardar entre 2 y 5 minutos. No cierres esta página."}
                </p>
              </div>
            </div>
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
      {isGenerated && !pipeline.isRunning && latestBundle && <BundleCard bundle={latestBundle} />}

      {isGenerated && !pipeline.isRunning && (archSpec || openSpec || issuesSpec || tutorialSpec) && (
        <div className="grid gap-3">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--c-text-faint)]">
            Especificaciones generadas
          </p>
          {archSpec     && <ArchitectureCard        spec={archSpec} />}
          {archSpec     && <LearningItineraryCard  spec={archSpec} />}
          {openSpec     && <OpenSpecCard            spec={openSpec} />}
          {openSpec     && <DataModelCard    spec={openSpec} />}
          {issuesSpec   && <IssuesCard       spec={issuesSpec} />}
          {tutorialSpec && <TutorialCard     spec={tutorialSpec} />}
        </div>
      )}

      {/* ── Regenerate ────────────────────────────────────────── */}
      {isGenerated && !pipeline.isRunning && (
        <div className="border-t border-[var(--c-border-subtle)] pt-4">
          <button className="secondary-button text-sm" onClick={pipeline.start}>
            <RefreshCw size={14} /> Regenerar proyecto
          </button>
          <p className="mt-2 text-xs text-[var(--c-text-faint)]">
            Regenerar reemplazará el kit actual con una nueva versión.
          </p>
        </div>
      )}

      {/* ── Previous bundles ──────────────────────────────────── */}
      {isGenerated && !pipeline.isRunning && (project.artifactBundles ?? []).length > 1 && (
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
