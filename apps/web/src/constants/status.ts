import { Project } from "../types/api";

export type ProjectStatus = Project["status"];

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  DRAFT: "Borrador",
  REQUIREMENTS_READY: "Requisitos listos",
  SPEC_READY: "OpenSpec listo",
  GENERATING: "Generando...",
  GENERATED: "MVP generado",
  REVIEW: "En revisión",
  DEPLOYED: "Publicado"
};

export const STATUS_COLOR: Record<ProjectStatus, string> = {
  DRAFT: "text-zinc-400 border-zinc-700",
  REQUIREMENTS_READY: "text-sky-400 border-sky-800",
  SPEC_READY: "text-violet-400 border-violet-800",
  GENERATING: "text-amber-400 border-amber-800",
  GENERATED: "text-emerald-400 border-emerald-800",
  REVIEW: "text-blue-400 border-blue-800",
  DEPLOYED: "text-green-400 border-green-800"
};
