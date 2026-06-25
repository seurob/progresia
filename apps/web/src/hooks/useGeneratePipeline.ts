import { useCallback, useEffect, useRef, useState } from "react";
import { api, getErrorMessage } from "../lib/api";
import { JobStatus } from "../types/api";

export type PipelineStage =
  | "idle" | "req" | "arch" | "spec" | "issues" | "tutorial" | "code" | "bundle"
  | "done" | "error";

export const JOB_STAGES: PipelineStage[] = ["req", "arch", "spec", "issues", "tutorial", "code"];

export const PIPELINE_STEPS = [
  { key: "req",      label: "Análisis de requisitos",     hint: "La IA extrae los requisitos funcionales de tu idea." },
  { key: "arch",     label: "Arquitectura tecnológica",   hint: "Se selecciona el stack más adecuado y se explica por qué." },
  { key: "spec",     label: "OpenSpec técnico",           hint: "Se genera la especificación completa: requisitos, user stories, módulos y milestones." },
  { key: "issues",   label: "Issues de GitHub",           hint: "Se crean las tareas del proyecto listas para importar a GitHub." },
  { key: "tutorial", label: "Tutorial de implementación", hint: "Se genera una guía paso a paso con comandos específicos del stack." },
  { key: "code",     label: "Generación de código",       hint: "Se genera el código base estructurado del proyecto." },
  { key: "bundle",   label: "Empaquetado",                hint: "Se empaqueta todo en un ZIP listo para descargar." },
] as const;

export function stageToStepIndex(stage: PipelineStage): number {
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

/**
 * Manages the 7-stage SDD generation pipeline: req → arch → spec → issues → tutorial → code → bundle.
 * Each stage launches a background job, polls until completion, then advances automatically.
 * The bundle stage is a direct API call (no job queue).
 */
export function useGeneratePipeline(projectId: string | undefined, onDone: () => void) {
  const [stage, setStage] = useState<PipelineStage>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
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
