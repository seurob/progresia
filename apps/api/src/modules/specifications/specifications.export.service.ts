import { Injectable } from "@nestjs/common";
import { SpecificationType } from "@prisma/client";
import { slugify } from "../../common/utils/string";

export interface ExportInput {
  projectName: string;
  type: SpecificationType;
  createdAt: Date;
  content: Record<string, unknown>;
}

/**
 * Pure rendering service: converts Specification content to Markdown or PDF.
 * No database access — receives pre-fetched data from SpecificationsService.
 */
@Injectable()
export class SpecificationExportService {
  buildFilename(projectName: string, type: SpecificationType, ext: "md" | "pdf"): string {
    return `${slugify(projectName, "specification")}-${type.toLowerCase()}.${ext}`;
  }

  toMarkdown(input: ExportInput): string {
    if (input.type === SpecificationType.TUTORIAL) return this.tutorialToMarkdown(input);
    if (input.type === SpecificationType.ISSUES)   return this.issuesToMarkdown(input);
    return this.genericToMarkdown(input);
  }

  toPdf(input: ExportInput): Buffer {
    const lines = this.toPdfLines(input);
    return this.createSimplePdf(lines);
  }

  // ── Markdown renderers ─────────────────────────────────────────────────────

  private tutorialToMarkdown(input: ExportInput): string {
    const c = input.content;
    const phases = Array.isArray(c.phases) ? (c.phases as Array<Record<string, unknown>>) : [];
    const archType = String(c.architecture_type ?? "");
    const totalSteps = Number(c.total_steps ?? phases.reduce((acc, p) => {
      return acc + (Array.isArray(p.steps) ? p.steps.length : 0);
    }, 0));

    const lines: string[] = [
      `# ${input.projectName} — Tutorial de implementación`,
      "",
      `> **Arquitectura:** ${archType || "personalizada"}  `,
      `> **Total:** ${phases.length} fases · ${totalSteps} pasos  `,
      `> **Generado por ProgresIA Studio** · ${input.createdAt.toISOString().slice(0, 10)}`,
      "",
      "---",
      "",
      "Este tutorial te guía desde cero hasta tener tu proyecto funcionando en local.",
      "Sigue cada fase en orden. Al final de cada fase habrás completado un bloque",
      "funcional del sistema.",
      "",
      "---",
      ""
    ];

    phases.forEach((phase, pi) => {
      const title = String(phase.title ?? `Fase ${pi + 1}`);
      const desc  = String(phase.description ?? "");
      const steps = Array.isArray(phase.steps) ? (phase.steps as Array<Record<string, unknown>>) : [];

      lines.push(`## ${title}`, "");
      if (desc) lines.push(`**Objetivo:** ${desc}`, "");

      steps.forEach((step, si) => {
        const action  = String(step.action ?? "");
        const command = step.command ? String(step.command) : null;
        const notes   = step.notes  ? String(step.notes)   : null;

        lines.push(`### Paso ${si + 1}: ${action}`, "");
        if (command) lines.push("```bash", command, "```", "");
        if (notes)   lines.push(`> **Nota:** ${notes}`, "");
      });

      lines.push("---", "");
    });

    lines.push(
      "## Lista de verificación final", "",
      "Antes de dar por finalizado el proyecto, comprueba:", "",
      "- [ ] Todos los servicios arrancan con `docker compose up -d`",
      "- [ ] Los tests pasan sin errores",
      "- [ ] Las variables de entorno están configuradas en `.env`",
      "- [ ] El README explica cómo levantar el proyecto desde cero",
      "- [ ] No hay claves o contraseñas hardcodeadas en el código"
    );

    return lines.join("\n");
  }

  private issuesToMarkdown(input: ExportInput): string {
    const c = input.content;
    const issues = Array.isArray(c.issues) ? (c.issues as Array<Record<string, unknown>>) : [];
    const milestones = Array.isArray(c.milestones) ? (c.milestones as string[]) : [];
    const priorityLabel: Record<string, string> = { critical: "Crítico", high: "Alto", medium: "Medio", low: "Bajo" };
    const priorityEmoji: Record<string, string> = { critical: "🔴", high: "🟠", medium: "🟡", low: "🟢" };

    const lines: string[] = [
      `# ${input.projectName} — Issues de GitHub`,
      "",
      `> **${issues.length} issues** · **${milestones.length} milestones**  `,
      `> Generado por ProgresIA Studio · ${input.createdAt.toISOString().slice(0, 10)}`,
      "",
      "---",
      ""
    ];

    const groups = milestones.length > 0
      ? milestones.map(ms => ({ ms, group: issues.filter(i => i.milestone === ms) }))
      : [{ ms: "Sin milestone", group: issues }];

    const ungrouped = milestones.length > 0
      ? issues.filter(i => !milestones.includes(String(i.milestone ?? "")))
      : [];
    if (ungrouped.length > 0) groups.push({ ms: "Sin milestone", group: ungrouped });

    for (const { ms, group } of groups) {
      if (group.length === 0) continue;
      lines.push(`## ${ms}`, "");
      for (const issue of group) {
        const p = String(issue.priority ?? "low");
        const labels = Array.isArray(issue.labels) ? (issue.labels as string[]) : [];
        lines.push(`### ${priorityEmoji[p] ?? "⚪"} ${String(issue.title ?? "Issue")}`, "");
        lines.push(`**Prioridad:** ${priorityLabel[p] ?? p}  `);
        if (labels.length > 0) lines.push(`**Labels:** ${labels.join(", ")}  `);
        if (issue.milestone)    lines.push(`**Milestone:** ${String(issue.milestone)}  `);
        lines.push("");
        if (issue.body) lines.push(String(issue.body), "");
      }
    }

    return lines.join("\n");
  }

  private genericToMarkdown(input: ExportInput): string {
    const c = input.content;
    const project      = (typeof c.project === "object" && c.project) ? (c.project as Record<string, unknown>) : {};
    const architecture = (typeof c.architecture === "object" && c.architecture) ? (c.architecture as Record<string, unknown>) : {};
    const requirements = Array.isArray(c.requirements) ? (c.requirements as Array<Record<string, unknown>>) : [];
    const stories      = Array.isArray(c.user_stories) ? (c.user_stories as Array<Record<string, unknown>>) : [];
    const modules      = Array.isArray(c.modules) ? (c.modules as string[]) : [];
    const stack        = Array.isArray(architecture.stack) ? (architecture.stack as string[]) : [];
    const milestones   = Array.isArray(c.milestones) ? (c.milestones as string[]) : [];

    const typeLabel: Record<string, string> = {
      REQUIREMENTS: "Requisitos", ARCHITECTURE: "Arquitectura",
      OPENSPEC: "OpenSpec", CODE: "Código generado"
    };

    const lines: string[] = [
      `# ${input.projectName} — ${typeLabel[input.type] ?? input.type}`,
      `> Generado por ProgresIA Studio · ${input.createdAt.toISOString().slice(0, 10)}`,
      ""
    ];

    const desc = String(project.description ?? c.description ?? "");
    if (desc) lines.push("## Resumen", "", desc, "");

    if (stack.length > 0) {
      lines.push("## Stack tecnológico", "");
      stack.forEach(s => lines.push(`- ${s}`));
      lines.push("");
    }

    if (modules.length > 0) {
      lines.push("## Módulos", "");
      modules.forEach(m => lines.push(`- ${m}`));
      lines.push("");
    }

    if (milestones.length > 0) {
      lines.push("## Milestones", "");
      milestones.forEach((ms, i) => lines.push(`${i + 1}. ${ms}`));
      lines.push("");
    }

    if (requirements.length > 0) {
      lines.push("## Requisitos", "");
      requirements.forEach(r => {
        lines.push(`### ${r.id ?? ""} ${r.title ?? "Requisito"}`);
        if (r.description) lines.push("", String(r.description));
        const ac = Array.isArray(r.acceptance_criteria) ? (r.acceptance_criteria as string[]) : [];
        if (ac.length > 0) {
          lines.push("", "**Criterios de aceptación:**", "");
          ac.forEach(a => lines.push(`- [ ] ${a}`));
        }
        lines.push("");
      });
    }

    if (stories.length > 0) {
      lines.push("## User Stories", "");
      stories.forEach(s => {
        lines.push(`- **${s.id ?? ""}** Como *${s.actor ?? "usuario"}* quiero **${s.goal ?? ""}** para ${s.benefit ?? ""}`);
      });
      lines.push("");
    }

    return lines.join("\n");
  }

  // ── PDF renderers ──────────────────────────────────────────────────────────

  private toPdfLines(input: ExportInput): string[] {
    if (input.type === SpecificationType.TUTORIAL) return this.tutorialToPdfLines(input);
    if (input.type === SpecificationType.ISSUES)   return this.issuesToPdfLines(input);
    return this.genericToPdfLines(input);
  }

  private tutorialToPdfLines(input: ExportInput): string[] {
    const c = input.content;
    const phases = Array.isArray(c.phases) ? (c.phases as Array<Record<string, unknown>>) : [];
    const archType = String(c.architecture_type ?? "");
    const totalSteps = Number(c.total_steps ?? phases.reduce((acc, p) => {
      return acc + (Array.isArray(p.steps) ? p.steps.length : 0);
    }, 0));

    const sep = "------------------------------------------------------------";
    const lines: string[] = [
      "ProgresIA Studio  |  Tutorial de implementacion",
      input.projectName + (archType ? `  (${archType})` : ""),
      `Generado: ${input.createdAt.toISOString().slice(0, 10)}`,
      "",
      sep,
      `GUIA PASO A PASO  |  ${phases.length} fases  |  ${totalSteps} pasos`,
      sep,
      "",
      "Esta guia acompana al estudiante desde cero hasta tener el proyecto",
      "funcionando en local. Sigue cada fase en orden; no saltes pasos.",
      ""
    ];

    phases.forEach((phase, pi) => {
      const title = String(phase.title ?? `Fase ${pi + 1}`);
      const desc  = String(phase.description ?? "");
      const steps = Array.isArray(phase.steps) ? (phase.steps as Array<Record<string, unknown>>) : [];

      lines.push(sep, title.toUpperCase(), sep);
      if (desc) lines.push("", ...this.wrapText(`Objetivo: ${desc}`, 80));
      lines.push("");

      steps.forEach((step, si) => {
        const action  = String(step.action ?? "");
        const command = step.command ? String(step.command) : null;
        const notes   = step.notes  ? String(step.notes)   : null;

        lines.push(`  [${si + 1}] ${action}`);
        if (command) lines.push(`       $ ${command}`);
        if (notes)   lines.push(...this.wrapText(`       * ${notes}`, 80));
        lines.push("");
      });
    });

    lines.push(
      sep, "SIGUIENTES PASOS", sep,
      "[ ] Escribe tests para cada modulo implementado.",
      "[ ] Revisa las variables de entorno antes de desplegar.",
      "[ ] Lee el README del proyecto para comandos de produccion."
    );

    return lines;
  }

  private issuesToPdfLines(input: ExportInput): string[] {
    const c = input.content;
    const issues     = Array.isArray(c.issues)     ? (c.issues     as Array<Record<string, unknown>>) : [];
    const milestones = Array.isArray(c.milestones) ? (c.milestones as string[]) : [];
    const sep = "------------------------------------------------------------";
    const priorityLabel: Record<string, string> = { critical: "CRITICO", high: "ALTO", medium: "MEDIO", low: "BAJO" };

    const lines: string[] = [
      "ProgresIA Studio  |  Issues de GitHub",
      input.projectName,
      `Generado: ${input.createdAt.toISOString().slice(0, 10)}`,
      "",
      sep,
      `${issues.length} ISSUES  |  ${milestones.length} MILESTONES`,
      sep,
      ""
    ];

    const groups = milestones.length > 0 ? milestones : ["Sin milestone"];
    for (const ms of groups) {
      const group = milestones.length > 0 ? issues.filter(i => i.milestone === ms) : issues;
      if (group.length === 0) continue;
      lines.push(`--- ${ms} (${group.length} issues) ---`, "");
      for (const issue of group) {
        const priority = priorityLabel[String(issue.priority ?? "low")] ?? String(issue.priority ?? "low").toUpperCase();
        lines.push(`  [${priority}] ${String(issue.title ?? "Issue")}`);
        if (issue.body) {
          lines.push(...this.wrapText(`    ${String(issue.body)}`, 78).slice(0, 6));
        }
        lines.push("");
      }
    }

    return lines;
  }

  private genericToPdfLines(input: ExportInput): string[] {
    const c = input.content;
    const project      = (typeof c.project === "object" && c.project) ? (c.project as Record<string, unknown>) : {};
    const architecture = (typeof c.architecture === "object" && c.architecture) ? (c.architecture as Record<string, unknown>) : {};
    const requirements = Array.isArray(c.requirements) ? (c.requirements as Array<Record<string, unknown>>) : [];
    const stories      = Array.isArray(c.user_stories) ? (c.user_stories as Array<Record<string, unknown>>) : [];
    const modules      = Array.isArray(c.modules) ? (c.modules as string[]) : [];
    const stack        = Array.isArray(architecture.stack) ? (architecture.stack as string[]) : [];

    const lines = [
      "ProgresIA Studio",
      `${input.type} - ${input.projectName}`,
      `Generado: ${input.createdAt.toISOString().slice(0, 10)}`,
      "",
      "Resumen",
      String(project.description ?? c.description ?? "Especificacion generada por ProgresIA Studio."),
      "",
      "Stack recomendado",
      ...(stack.length > 0 ? stack.map(item => `- ${item}`) : ["- Pendiente de definir"]),
      "",
      "Modulos",
      ...(modules.length > 0 ? modules.map(item => `- ${item}`) : ["- Pendiente de definir"]),
      "",
      "Requisitos principales",
    ];

    if (requirements.length > 0) {
      for (const req of requirements.slice(0, 12)) {
        lines.push(`- ${req.id ?? ""} ${req.title ?? "Requisito"}: ${req.description ?? ""}`);
      }
    } else {
      lines.push("- No hay requisitos estructurados en esta especificacion.");
    }

    lines.push("", "User stories");
    if (stories.length > 0) {
      for (const story of stories.slice(0, 10)) {
        lines.push(`- Como ${story.actor ?? "usuario"} quiero ${story.goal ?? ""} para ${story.benefit ?? ""}`);
      }
    } else {
      lines.push("- No hay user stories estructuradas en esta especificacion.");
    }

    return lines;
  }

  // ── PDF byte builder ───────────────────────────────────────────────────────

  private createSimplePdf(lines: string[]): Buffer {
    const pageLineLimit = 44;
    const pages: string[][] = [];
    for (let i = 0; i < lines.length; i += pageLineLimit) {
      pages.push(lines.slice(i, i + pageLineLimit));
    }
    if (pages.length === 0) pages.push(["ProgresIA Studio"]);

    const objects: string[] = [];
    const addObject = (body: string) => { objects.push(body); return objects.length; };

    const catalogId = addObject("<< /Type /Catalog /Pages 2 0 R >>");
    const pagesId   = addObject("");
    const fontId    = addObject("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
    const pageIds: number[] = [];

    for (const pageLines of pages) {
      const stream = [
        "BT", "/F1 11 Tf", "14 TL", "50 790 Td",
        ...pageLines.flatMap(line => this.wrapText(line, 92).map(w => `(${this.escapePdfText(w)}) Tj T*`)),
        "ET"
      ].join("\n");
      const contentId = addObject(`<< /Length ${Buffer.byteLength(stream, "latin1")} >>\nstream\n${stream}\nendstream`);
      const pageId    = addObject(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`);
      pageIds.push(pageId);
    }

    objects[pagesId - 1] = `<< /Type /Pages /Kids [${pageIds.map(id => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`;

    let pdf = "%PDF-1.4\n";
    const offsets = [0];
    objects.forEach((body, index) => {
      offsets.push(Buffer.byteLength(pdf, "latin1"));
      pdf += `${index + 1} 0 obj\n${body}\nendobj\n`;
    });
    const xrefOffset = Buffer.byteLength(pdf, "latin1");
    pdf += `xref\n0 ${objects.length + 1}\n`;
    pdf += "0000000000 65535 f \n";
    for (let i = 1; i < offsets.length; i += 1) {
      pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
    }
    pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;

    return Buffer.from(pdf, "latin1");
  }

  // ── Text helpers ───────────────────────────────────────────────────────────

  private wrapText(text: string, width: number): string[] {
    const wrapped: string[] = [];
    for (const rawLine of this.toPdfSafeText(text).split(/\r?\n/)) {
      const words = rawLine.trim().split(/\s+/).filter(Boolean);
      if (words.length === 0) { wrapped.push(""); continue; }
      let line = "";
      for (const word of words) {
        line = `${line} ${word}`.trim().length > width && line
          ? (wrapped.push(line), word)
          : `${line} ${word}`.trim();
      }
      if (line) wrapped.push(line);
    }
    return wrapped;
  }

  private escapePdfText(text: string): string {
    return this.toPdfSafeText(text).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
  }

  private toPdfSafeText(text: string): string {
    return Array.from(text.normalize("NFD").replace(/[\u0300-\u036f]/g, ""))
      .map(char => { const c = char.charCodeAt(0); return c >= 32 && c <= 126 ? char : "-"; })
      .join("");
  }
}
