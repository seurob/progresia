import { ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import { Prisma, ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import * as JSZip from "jszip";
import { AiServiceClient } from "../ai-service/ai-service.client";
import { GithubService } from "../github/github.service";
import { StorageService } from "../storage/storage.service";
import { PrismaService } from "../../database/prisma.service";
import { ProjectsService } from "../projects/projects.service";
import { slugify } from "../../common/utils/string";
import { PushToGithubDto, PushToGithubResult } from "./dto/push-to-github.dto";

interface ManifestFile {
  path: string;
  kind: "document" | "specification";
  description: string;
  source: string;
}

interface Manifest {
  version: string;
  project: string;
  sourceSpecificationId: string;
  generatedAt: string;
  files: ManifestFile[];
  sourceSummary?: Record<string, unknown>;
}

@Injectable()
export class ArtifactsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly projectsService: ProjectsService,
    private readonly aiServiceClient: AiServiceClient,
    private readonly githubService: GithubService,
    private readonly storageService: StorageService
  ) {}

  async listByProject(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);

    return this.prisma.artifactBundle.findMany({
      where: { projectId: project.id },
      orderBy: { createdAt: "desc" }
    });
  }

  async generateBundle(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;
    const specification = await this.prisma.specification.findFirst({
      where: {
        projectId: id,
        type: SpecificationType.OPENSPEC,
        status: SpecificationStatus.GENERATED
      },
      orderBy: { createdAt: "desc" }
    });

    if (!specification) {
      throw new ConflictException("Generated OpenSpec is required before creating artifact bundle");
    }

    const manifest = this.createManifest({
      projectName: project.name,
      sourceSpecificationId: specification.id,
      source: specification.content
    });

    // If generateCode() already created a bundle for this spec, update its manifest
    // rather than creating a new empty bundle — otherwise the user would download
    // a bundle with no code files.
    const existing = await this.prisma.artifactBundle.findFirst({
      where: { projectId: id, specificationId: specification.id },
      orderBy: { createdAt: "desc" }
    });

    if (existing) {
      return this.prisma.artifactBundle.update({
        where: { id: existing.id },
        data: { manifest: manifest as unknown as Prisma.InputJsonValue }
      });
    }

    return this.prisma.artifactBundle.create({
      data: {
        projectId: id,
        specificationId: specification.id,
        manifest: manifest as unknown as Prisma.InputJsonValue
      }
    });
  }

  async generateCode(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const id = project.id;
    const specification = await this.prisma.specification.findFirst({
      where: { projectId: id, type: SpecificationType.OPENSPEC, status: SpecificationStatus.GENERATED },
      orderBy: { createdAt: "desc" }
    });

    if (!specification) {
      throw new ConflictException("Generated OpenSpec is required before generating code");
    }

    const spec = specification.content as Record<string, unknown>;
    const modules = Array.isArray(spec.modules) ? (spec.modules as string[]) : [];
    const requirements = Array.isArray(spec.requirements)
      ? (spec.requirements as Array<{ id: string; title: string; description: string }>)
      : [];
    const constraints = (spec.constraints ?? {}) as Record<string, unknown>;
    const stack = Array.isArray(constraints.stack) ? (constraints.stack as string[]) : [];

    const idea = await this.prisma.idea.findUnique({ where: { projectId: id } });

    const archSpec = await this.prisma.specification.findFirst({
      where: { projectId: id, type: SpecificationType.ARCHITECTURE, status: SpecificationStatus.GENERATED },
      orderBy: { createdAt: "desc" }
    });
    const architectureType = (archSpec?.content as Record<string, unknown>)?.architecture_type as string | undefined;

    const generated = await this.aiServiceClient.generateCode({
      project_name: project.name,
      sector: project.sector,
      modules,
      requirements,
      needs_auth: idea?.needsAuth ?? true,
      needs_admin_panel: idea?.needsAdminPanel ?? true,
      needs_ai: idea?.needsAi ?? false,
      stack,
      architecture_type: architectureType
    });

    const existingBundle = await this.prisma.artifactBundle.findFirst({
      where: { projectId: id, specificationId: specification.id },
      orderBy: { createdAt: "desc" }
    });

    if (existingBundle) {
      const [bundle] = await this.prisma.$transaction([
        this.prisma.artifactBundle.update({
          where: { id: existingBundle.id },
          data: {
            status: "GENERATED",
            generatedContent: generated as unknown as Prisma.InputJsonValue
          }
        }),
        this.prisma.project.update({
          where: { id },
          data: { status: ProjectStatus.GENERATED }
        })
      ]);
      return bundle;
    }

    const manifest = this.createManifest({
      projectName: project.name,
      sourceSpecificationId: specification.id,
      source: specification.content
    });

    const [bundle] = await this.prisma.$transaction([
      this.prisma.artifactBundle.create({
        data: {
          projectId: id,
          specificationId: specification.id,
          manifest: manifest as unknown as Prisma.InputJsonValue,
          generatedContent: generated as unknown as Prisma.InputJsonValue
        }
      }),
      this.prisma.project.update({
        where: { id },
        data: { status: ProjectStatus.GENERATED }
      })
    ]);
    return bundle;
  }

  async pushToGithub(
    userId: string,
    bundleId: string,
    dto: PushToGithubDto
  ): Promise<PushToGithubResult> {
    const bundle = await this.prisma.artifactBundle.findUnique({
      where: { id: bundleId },
      include: { project: true }
    });

    if (!bundle) {
      throw new NotFoundException("Artifact bundle not found");
    }

    await this.projectsService.ensureProjectAccess(bundle.projectId, userId);

    const generated = bundle.generatedContent as unknown as {
      files?: Array<{ path: string; content: string }>;
    } | null;

    if (!generated?.files?.length) {
      throw new ConflictException(
        "Generate code first before pushing to GitHub (use POST /generate-code)"
      );
    }

    const result = await this.githubService.pushFiles(
      dto.githubToken,
      dto.repoName,
      dto.description ?? bundle.project.name,
      dto.isPrivate ?? false,
      generated.files,
      `feat: initial scaffold generated by ProgresIA Studio\n\nBundle: ${bundleId}`
    );

    await this.prisma.project.update({
      where: { id: bundle.projectId },
      data: { status: ProjectStatus.DEPLOYED }
    });

    return result;
  }

  async exportZip(userId: string, bundleId: string): Promise<Buffer> {
    const bundle = await this.prisma.artifactBundle.findUnique({
      where: { id: bundleId },
      include: { project: true }
    });

    if (!bundle) {
      throw new NotFoundException("Artifact bundle not found");
    }

    await this.projectsService.ensureProjectAccess(bundle.projectId, userId);

    const manifest = bundle.manifest as unknown as Manifest;
    const zip = new JSZip();

    const generated = bundle.generatedContent as unknown as {
      files?: Array<{ path: string; content: string }>;
    } | null;

    if (generated?.files?.length) {
      for (const file of generated.files) {
        zip.file(file.path, file.content);
      }
    } else {
      for (const file of manifest.files ?? []) {
        zip.file(file.path, this.renderFileContent(file, manifest));
      }
    }

    return zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  }

  async validateBundle(userId: string, bundleId: string): Promise<{
    valid: boolean;
    fileCount: number;
    hasCode: boolean;
    hasSdd: boolean;
    hasReadme: boolean;
    issues: string[];
  }> {
    const bundle = await this.prisma.artifactBundle.findUnique({
      where: { id: bundleId },
      include: { project: true }
    });

    if (!bundle) throw new NotFoundException("Artifact bundle not found");
    await this.projectsService.ensureProjectAccess(bundle.projectId, userId);

    const generated = bundle.generatedContent as unknown as {
      files?: Array<{ path: string; content: string }>;
    } | null;
    const manifest = bundle.manifest as unknown as Manifest;

    const files = this.mergeBundleFiles(manifest.files ?? [], generated?.files ?? []);

    const issues: string[] = [];
    const paths = files.map(f => f.path);

    if (paths.length === 0) issues.push("El bundle no contiene archivos.");

    const dupes = paths.filter((p, i) => paths.indexOf(p) !== i);
    if (dupes.length > 0) issues.push(`Rutas duplicadas: ${dupes.slice(0, 3).join(", ")}`);

    const dangerous = paths.filter(p => p.includes("..") || p.startsWith("/"));
    if (dangerous.length > 0) issues.push(`Rutas peligrosas detectadas: ${dangerous[0]}`);

    const hasCode = paths.some(p =>
      /\.(ts|tsx|js|jsx|py|php|rb|go|rs|java|cs)$/.test(p) ||
      p.includes("package.json") || p.includes("composer.json")
    );
    const hasSdd = paths.some(p => p.includes("sdd/"));
    const hasReadme = paths.some(p => p.endsWith("README.md"));

    if (!hasCode && !hasSdd) issues.push("El bundle no contiene archivos de codigo ni especificaciones SDD.");
    if (!hasReadme) issues.push("Falta README.md.");

    return {
      valid: issues.length === 0,
      fileCount: paths.length,
      hasCode,
      hasSdd,
      hasReadme,
      issues,
    };
  }

  private mergeBundleFiles(
    manifestFiles: Array<{ path: string }>,
    generatedFiles: Array<{ path: string }>
  ): Array<{ path: string }> {
    const seen = new Set<string>();
    const files: Array<{ path: string }> = [];

    for (const file of [...manifestFiles, ...generatedFiles]) {
      if (!file.path || seen.has(file.path)) continue;
      seen.add(file.path);
      files.push(file);
    }

    return files;
  }

  async exportZipUrl(userId: string, bundleId: string): Promise<{ url: string; expiresIn: number }> {
    const buffer = await this.exportZip(userId, bundleId);
    const objectName = `bundles/${bundleId}/artifact.zip`;
    await this.storageService.uploadBuffer(objectName, buffer, "application/zip");
    const url = await this.storageService.getSignedUrl(objectName, 3600);
    return { url, expiresIn: 3600 };
  }

  createManifest(input: {
    projectName: string;
    sourceSpecificationId: string;
    source: Prisma.JsonValue;
  }) {
    const basePath = this.slugify(input.projectName);
    const files: ManifestFile[] = [
      // ── Root ─────────────────────────────────────────────────────────────
      {
        path: `${basePath}/README.md`,
        kind: "document",
        description: "Guia de inicio: descripcion, setup multi-plataforma e instrucciones de arranque.",
        source: "openspec"
      },
      {
        path: `${basePath}/docker-compose.yml`,
        kind: "specification",
        description: "Infraestructura de desarrollo lista para usar con Docker Compose.",
        source: "openspec"
      },
      {
        path: `${basePath}/.env.example`,
        kind: "specification",
        description: "Variables de entorno requeridas para arrancar los servicios.",
        source: "openspec"
      },
      // ── SDD ──────────────────────────────────────────────────────────────
      {
        path: `${basePath}/sdd/constitution.md`,
        kind: "document",
        description: "Constitucion del proyecto: stack, decisiones de arquitectura y principios de desarrollo.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/requirements/requirements.md`,
        kind: "document",
        description: "Requisitos funcionales y no funcionales completos del sistema.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/requirements/user-stories.md`,
        kind: "document",
        description: "User stories por actor con criterios de aceptacion.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/specifications/openspec.md`,
        kind: "specification",
        description: "Resumen del OpenSpec tecnico con endpoints y entidades principales.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/plans/milestones.md`,
        kind: "document",
        description: "Milestones del proyecto con tareas organizadas por fase.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/project-context.md`,
        kind: "document",
        description: "Instrucciones para IA: contexto completo del proyecto para Claude, Copilot, etc.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/resume-session.md`,
        kind: "document",
        description: "Prompt para retomar el trabajo en una nueva sesion de IA.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/add-feature.md`,
        kind: "document",
        description: "Prompt para anadir nuevas funcionalidades con ayuda de IA.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/fix-bug.md`,
        kind: "document",
        description: "Prompt para resolver bugs con ayuda de IA.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/setup/environment.md`,
        kind: "document",
        description: "Configuracion del entorno de desarrollo con comandos para Windows, Linux y macOS.",
        source: "openspec"
      },
      // ── Docs ─────────────────────────────────────────────────────────────
      {
        path: `${basePath}/docs/architecture/overview.md`,
        kind: "document",
        description: "Diagrama de componentes y stack tecnologico seleccionado.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/adr/adr-001-tech-stack.md`,
        kind: "document",
        description: "Architecture Decision Record: seleccion del stack tecnologico.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/development/contributing.md`,
        kind: "document",
        description: "Guia de contribucion: flujo Git, convenciones de commits y checklist de PR.",
        source: "openspec"
      },
      // ── Data model ───────────────────────────────────────────────────────
      {
        path: `${basePath}/sdd/requirements/data-model.md`,
        kind: "document",
        description: "Modelo de datos: entidades, relaciones, ORM recomendado e instrucciones de migracion.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/architecture/entity-relation-diagram.md`,
        kind: "document",
        description: "Diagrama ER en formato Mermaid: entidades, campos clave y relaciones.",
        source: "openspec"
      },
      // ── OpenSpec JSON ─────────────────────────────────────────────────────
      {
        path: `${basePath}/sdd/specifications/openspec.json`,
        kind: "specification",
        description: "Especificacion tecnica completa generada por IA (OpenSpec JSON).",
        source: "openspec"
      }
    ];

    return {
      version: "0.3.0",
      project: input.projectName,
      sourceSpecificationId: input.sourceSpecificationId,
      generatedAt: new Date().toISOString(),
      files,
      sourceSummary: this.extractSourceSummary(input.source)
    };
  }

  private renderFileContent(file: ManifestFile, manifest: Manifest): string {
    const projectName = manifest.project ?? "Project";
    const summary = manifest.sourceSummary ?? {};
    const requirements = Array.isArray(summary.requirements) ? (summary.requirements as Array<Record<string, unknown>>) : [];
    const modules = Array.isArray(summary.modules) ? (summary.modules as string[]) : [];
    const constraints = (typeof summary.constraints === "object" && summary.constraints)
      ? (summary.constraints as Record<string, unknown>)
      : {};
    const stack = Array.isArray(constraints.stack) ? (constraints.stack as string[]) : [];
    const nonFunctional = Array.isArray(summary.non_functional_requirements)
      ? (summary.non_functional_requirements as Array<Record<string, unknown>>)
      : [];
    const userStories = Array.isArray(summary.user_stories)
      ? (summary.user_stories as Array<Record<string, unknown>>)
      : [];

    const p = file.path;

    if (p.endsWith("README.md")) {
      return this.renderReadme(projectName, manifest, modules, stack);
    }

    if (p.endsWith("docker-compose.yml")) {
      return this.renderDockerCompose(projectName, stack, modules);
    }

    if (p.endsWith(".env.example")) {
      return this.renderEnvExample(projectName, stack);
    }

    if (p.endsWith("requirements.md")) {
      return this.renderRequirements(projectName, requirements, nonFunctional, userStories);
    }

    if (p.endsWith("user-stories.md")) {
      return this.renderUserStories(projectName, userStories, modules);
    }

    if (p.endsWith("constitution.md")) {
      return this.renderConstitution(projectName, stack, modules);
    }

    if (p.endsWith("milestones.md")) {
      return this.renderImplementationSteps(projectName, modules);
    }

    if (p.includes("sdd/prompts/project-context.md")) {
      return this.renderProjectContextPrompt(projectName, stack, modules);
    }

    if (p.endsWith("overview.md")) {
      return this.renderArchOverview(projectName, stack, modules);
    }

    if (p.endsWith("adr-001-tech-stack.md")) {
      return this.renderAdr001(projectName, stack);
    }

    if (p.endsWith("contributing.md")) {
      return this.renderContributing(projectName);
    }

    if (p.endsWith("data-model.md")) {
      return this.renderDataModel(projectName, summary);
    }

    if (p.endsWith("entity-relation-diagram.md")) {
      return this.renderErDiagram(projectName, summary);
    }

    if (p.endsWith(".json")) {
      return JSON.stringify(summary, null, 2);
    }

    // Generic markdown stub for remaining SDD files
    return `# ${p.split("/").pop()?.replace(".md", "").replace(/-/g, " ")}\n\n> Parte del proyecto **${projectName}**.\n\n${file.description}\n`;
  }

  private renderReadme(
    projectName: string,
    manifest: Manifest,
    modules: string[],
    stack: string[]
  ): string {
    const slug = this.slugify(projectName);
    const generatedDate = new Date(manifest.generatedAt).toLocaleDateString("es-ES", {
      year: "numeric", month: "long", day: "numeric"
    });
    const stackLine = stack.length > 0 ? stack.slice(0, 4).join(" · ") : "React · NestJS · PostgreSQL";

    return [
      `# ${projectName}`,
      "",
      `> MVP generado con **ProgresIA Studio** el ${generatedDate}.`,
      `> Stack: ${stackLine}`,
      "",
      "---",
      "",
      "## Inicio rapido",
      "",
      "### Linux / macOS",
      "",
      "```bash",
      "cp .env.example .env",
      "docker compose up -d",
      "npm install && npm run db:migrate",
      "npm run dev",
      "```",
      "",
      "### Windows (PowerShell)",
      "",
      "```powershell",
      "Copy-Item .env.example .env",
      "docker compose up -d",
      "npm install; npm run db:migrate",
      "npm run dev",
      "```",
      "",
      "---",
      "",
      "## Estructura del proyecto",
      "",
      "```",
      `${slug}/`,
      "├── apps/",
      "│   ├── web/              # Frontend",
      "│   └── api/              # Backend API",
      "├── sdd/                  # Especificaciones SDD",
      "│   ├── constitution.md   # Arquitectura y decisiones",
      "│   ├── requirements/     # Requisitos funcionales y user stories",
      "│   ├── specifications/   # OpenSpec tecnico",
      "│   ├── plans/            # Milestones y sprints",
      "│   ├── prompts/          # Instrucciones para IA (Claude, Copilot...)",
      "│   └── setup/            # Guia de configuracion del entorno",
      "├── docs/",
      "│   ├── architecture/     # Diagramas y overview del sistema",
      "│   ├── development/      # Guia de contribucion",
      "│   └── adr/              # Architecture Decision Records",
      "├── docker-compose.yml",
      "├── .env.example",
      "└── README.md             # Este archivo",
      "```",
      "",
      ...(modules.length > 0 ? ["## Modulos del sistema", "", ...modules.map(m => `- ${m}`), ""] : []),
      ...(stack.length > 0 ? ["## Stack tecnologico", "", ...stack.map(s => `- ${s}`), ""] : []),
      "## Continuar con IA",
      "",
      "Este proyecto incluye instrucciones para IA en `sdd/prompts/`:",
      "",
      "- `project-context.md` — Contexto completo para abrir una nueva sesion",
      "- `resume-session.md` — Para retomar el trabajo donde lo dejaste",
      "- `add-feature.md` — Para anadir nuevas funcionalidades",
      "- `fix-bug.md` — Para resolver errores con ayuda de IA",
      "",
      "---",
      "",
      "_Generado con [ProgresIA Studio](https://progresia.studio)_"
    ].join("\n");
  }

  private renderUserStories(
    projectName: string,
    userStories: Array<Record<string, unknown>>,
    modules: string[]
  ): string {
    const lines = [`# User Stories — ${projectName}`, ""];

    if (userStories.length > 0) {
      lines.push("## Por actor", "");
      for (const s of userStories) {
        const actor = s.actor ?? "Usuario";
        const goal = s.goal ?? "";
        const benefit = s.benefit ?? "";
        const id = s.id ?? "";
        lines.push(`### ${id}`, "", `**Como** ${actor} **quiero** ${goal} **para** ${benefit}`, "");
      }
    } else if (modules.length > 0) {
      lines.push("## Actor principal: Usuario final", "");
      modules.slice(0, 6).forEach((m, i) => {
        lines.push(
          `### US-${String(i + 1).padStart(3, "0")}`,
          "",
          `**Como** usuario final **quiero** ${m.toLowerCase()} **para** mejorar mi flujo de trabajo.`,
          ""
        );
      });
    } else {
      lines.push("_Las user stories se generaran durante la especificacion._", "");
    }

    return lines.join("\n");
  }

  private renderConstitution(
    projectName: string,
    stack: string[],
    modules: string[]
  ): string {
    return [
      `# Constitucion del Proyecto — ${projectName}`,
      "",
      "> Este documento es la fuente de verdad del proyecto.",
      "> Cualquier IA o desarrollador debe leer este archivo antes de trabajar en el codigo.",
      "",
      "## Stack tecnologico",
      "",
      ...(stack.length > 0 ? stack.map(s => `- ${s}`) : ["- React + NestJS + PostgreSQL"]),
      "",
      "## Modulos principales",
      "",
      ...(modules.length > 0 ? modules.map(m => `- ${m}`) : ["- (por definir)"]),
      "",
      "## Principios de desarrollo",
      "",
      "- **SDD-first**: cada cambio empieza con una especificacion, no con codigo",
      "- **Convenciones sobre configuracion**: seguir las convenciones del framework",
      "- **Tests antes de refactorizar**: no refactorizar sin cobertura",
      "- **Seguridad por defecto**: API keys solo en `.env`, nunca en el codigo",
      "",
      "## Cambios a este documento",
      "",
      "Cualquier cambio de stack o arquitectura debe actualizarse aqui y en `sdd/specifications/openspec.md`.",
    ].join("\n");
  }

  private renderProjectContextPrompt(
    projectName: string,
    stack: string[],
    modules: string[]
  ): string {
    return [
      `# Contexto del proyecto para IA — ${projectName}`,
      "",
      "> Copia y pega este archivo al inicio de cualquier sesion con Claude, Copilot o ChatGPT.",
      "",
      "---",
      "",
      `Estoy trabajando en **${projectName}**.`,
      "",
      "## Stack tecnologico",
      "",
      ...(stack.length > 0 ? stack.map(s => `- ${s}`) : ["- React + NestJS + PostgreSQL"]),
      "",
      "## Modulos implementados",
      "",
      ...(modules.length > 0 ? modules.map(m => `- ${m}`) : ["- (ver sdd/requirements/requirements.md)"]),
      "",
      "## Convenciones",
      "",
      "- TypeScript estricto en todo el codigo",
      "- Nombres de variables y funciones: camelCase",
      "- Nombres de archivos: kebab-case",
      "- Commits: Conventional Commits (feat:, fix:, docs:, refactor:)",
      "",
      "Lee `sdd/constitution.md` y `sdd/requirements/requirements.md` antes de hacer cambios.",
    ].join("\n");
  }

  private renderArchOverview(
    projectName: string,
    stack: string[],
    modules: string[]
  ): string {
    const hasAi = stack.some(s => /fastapi|python|langchain|ai/i.test(s));
    return [
      `# Arquitectura — ${projectName}`,
      "",
      "## Diagrama de componentes",
      "",
      "```",
      "┌─────────────────────────────────────────────────────┐",
      "│                  Docker Compose                      │",
      "│                                                      │",
      "│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │",
      "│  │  Frontend  │  │    API     │  │   Database   │  │",
      `│  │  ${(stack[0] ?? "React").slice(0, 8).padEnd(8)}  │──▶│  ${(stack[1] ?? "NestJS").slice(0, 8).padEnd(8)}  │──▶│  PostgreSQL  │  │`,
      "│  │   :5173    │  │   :3000    │  │    :5432     │  │",
      "│  └────────────┘  └────────────┘  └──────────────┘  │",
      ...(hasAi ? [
        "│                      ┌────────────┐                 │",
        "│                      │ AI Service │                 │",
        "│                      │  FastAPI   │                 │",
        "│                      │   :8003    │                 │",
        "│                      └────────────┘                 │",
      ] : []),
      "└─────────────────────────────────────────────────────┘",
      "```",
      "",
      "## Modulos del sistema",
      "",
      ...(modules.length > 0 ? modules.map(m => `- **${m}**`) : ["- (ver sdd/requirements/requirements.md)"]),
      "",
      "## Decisiones de arquitectura",
      "",
      "Ver `docs/adr/` para las Architecture Decision Records.",
    ].join("\n");
  }

  private renderAdr001(projectName: string, stack: string[]): string {
    return [
      "# ADR-001: Seleccion del stack tecnologico",
      "",
      "**Estado**: Aceptado",
      `**Proyecto**: ${projectName}`,
      "",
      "## Contexto",
      "",
      `Se necesita seleccionar el stack para el MVP de ${projectName}.`,
      "",
      "## Decision",
      "",
      `Stack seleccionado: **${stack.slice(0, 4).join(", ") || "React + NestJS + PostgreSQL"}**`,
      "",
      "## Justificacion",
      "",
      "- Ecosistema maduro con amplia documentacion",
      "- Buena integracion entre los componentes del stack",
      "- Preparado para escalar cuando el MVP valide la propuesta de valor",
      "",
      "## Consecuencias",
      "",
      "- **Positivas**: Velocidad de desarrollo, comunidad activa",
      "- **Negativas**: Requiere conocimiento previo del stack",
    ].join("\n");
  }

  private renderContributing(projectName: string): string {
    return [
      `# Guia de contribucion — ${projectName}`,
      "",
      "## Flujo de trabajo Git",
      "",
      "```bash",
      "# 1. Crea una rama",
      "git checkout -b feat/nombre-de-la-funcionalidad",
      "",
      "# 2. Commit con Conventional Commits",
      'git commit -m "feat: anadir gestion de reservas"',
      "",
      "# 3. Push y Pull Request",
      "git push origin feat/nombre-de-la-funcionalidad",
      "```",
      "",
      "## Prefijos de commit",
      "",
      "| Prefijo | Cuando usarlo |",
      "|---------|---------------|",
      "| `feat:` | Nueva funcionalidad |",
      "| `fix:` | Correccion de bug |",
      "| `docs:` | Documentacion |",
      "| `refactor:` | Refactorizacion sin cambio de comportamiento |",
      "| `test:` | Anadir o corregir tests |",
      "",
      "## Antes de un PR",
      "",
      "- [ ] Tests pasan: `npm test`",
      "- [ ] Sin errores TypeScript: `npx tsc --noEmit`",
      "- [ ] Linting pasa: `npm run lint`",
    ].join("\n");
  }

  private renderRequirements(
    projectName: string,
    functional: Array<Record<string, unknown>>,
    nonFunctional: Array<Record<string, unknown>>,
    userStories: Array<Record<string, unknown>>
  ): string {
    const lines = [
      `# Requisitos — ${projectName}`,
      "",
      "> Extraidos del OpenSpec generado por IA. Revision y validacion recomendadas antes de implementar.",
      ""
    ];

    if (functional.length > 0) {
      lines.push("## Requisitos funcionales", "");
      for (const r of functional) {
        lines.push(`### ${r.id ?? ""} — ${r.title ?? "Requisito"}`);
        if (r.description) lines.push("", String(r.description));
        lines.push("");
      }
    } else {
      lines.push("## Requisitos funcionales", "", "_No se extrajeron requisitos funcionales._", "");
    }

    if (nonFunctional.length > 0) {
      lines.push("## Requisitos no funcionales", "");
      for (const r of nonFunctional) {
        lines.push(`### ${r.id ?? ""} — ${r.title ?? "Requisito"}`);
        if (r.description) lines.push("", String(r.description));
        lines.push("");
      }
    }

    if (userStories.length > 0) {
      lines.push("## User Stories", "");
      for (const s of userStories) {
        const actor = s.actor ?? "Usuario";
        const goal = s.goal ?? "";
        const benefit = s.benefit ?? "";
        lines.push(`- **Como** ${actor} **quiero** ${goal} **para** ${benefit}`);
      }
      lines.push("");
    }

    return lines.join("\n");
  }

  private renderImplementationSteps(projectName: string, modules: string[]): string {
    const lines = [
      `# Plan de implementacion — ${projectName}`,
      "",
      "> Guia paso a paso para construir el MVP. Marca cada tarea conforme la completes.",
      "",
      "## Fase 0: Preparacion del entorno (Dia 1)",
      "",
      "- [ ] Clonar el repositorio o crear uno nuevo en GitHub",
      "- [ ] Copiar variables: `cp docker/.env.example docker/.env`",
      "- [ ] Ajustar contrasenas y secretos en `docker/.env`",
      "- [ ] Arrancar la infraestructura: `docker compose -f docker/docker-compose.yml up -d`",
      "- [ ] Verificar que todos los servicios arrancan correctamente",
      "- [ ] Configurar el IDE (ESLint, Prettier, extensiones recomendadas)",
      "",
      "## Fase 1: Backend — Modelo de datos (Dias 2-3)",
      "",
      "- [ ] Definir el esquema de base de datos (ERD)",
      "- [ ] Crear las migraciones de base de datos",
      "- [ ] Verificar relaciones y constraints",
      "- [ ] Crear datos de prueba (seed)",
      ""
    ];

    if (modules.length > 0) {
      lines.push("## Fase 2: Backend — Implementacion de modulos (Dias 4-8)", "");
      for (const mod of modules) {
        lines.push(
          `### ${mod}`,
          "",
          `- [ ] Crear el modelo/entidad \`${mod}\``,
          `- [ ] Implementar endpoints CRUD`,
          `- [ ] Añadir validaciones de entrada`,
          `- [ ] Escribir tests unitarios`,
          `- [ ] Documentar los endpoints (Swagger/OpenAPI)`,
          ""
        );
      }
    } else {
      lines.push(
        "## Fase 2: Backend — Implementacion de modulos (Dias 4-8)",
        "",
        "- [ ] Identificar y crear los modulos del sistema",
        "- [ ] Implementar endpoints CRUD para cada modulo",
        "- [ ] Añadir validaciones y manejo de errores",
        "- [ ] Escribir tests unitarios",
        ""
      );
    }

    lines.push(
      "## Fase 3: Frontend (Dias 9-13)",
      "",
      "- [ ] Configurar el proyecto frontend (React + Vite)",
      "- [ ] Implementar el sistema de autenticacion (login/registro)",
      "- [ ] Crear los componentes base (Layout, Navigation, Forms)",
      "- [ ] Conectar cada pantalla con la API",
      "- [ ] Implementar validaciones de formularios",
      "- [ ] Añadir estados de carga y manejo de errores",
      "",
      "## Fase 4: Integracion y testing (Dias 14-15)",
      "",
      "- [ ] Tests de integracion frontend-backend",
      "- [ ] Tests E2E de los flujos principales",
      "- [ ] Revision de accesibilidad",
      "- [ ] Optimizacion de rendimiento",
      "- [ ] Revision de seguridad basica",
      "",
      "## Fase 5: Despliegue (Dia 16)",
      "",
      "- [ ] Configurar CI/CD (GitHub Actions)",
      "- [ ] Preparar entorno de produccion",
      "- [ ] Configurar variables de entorno de produccion",
      "- [ ] Desplegar y verificar en produccion",
      "- [ ] Configurar monitoreo y alertas",
      "",
      "---",
      "",
      "_Adapta esta guia a tu equipo y contexto. Los tiempos son estimados para un desarrollador._"
    );

    return lines.join("\n");
  }

  private renderDockerCompose(projectName: string, stack: string[], modules: string[]): string {
    const slug = this.slugify(projectName);
    const hasRedis = stack.some(s => /redis|bull|queue/i.test(s)) || modules.length > 3;
    const hasMinio = stack.some(s => /minio|s3|storage/i.test(s));

    const services: string[] = [];

    // Postgres (always)
    services.push(`  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: \${DB_USER:-${slug}}
      POSTGRES_PASSWORD: \${DB_PASSWORD:-changeme}
      POSTGRES_DB: \${DB_NAME:-${slug}_db}
    ports:
      - "\${DB_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${DB_USER:-${slug}}"]
      interval: 10s
      timeout: 5s
      retries: 5`);

    // Redis (conditional)
    if (hasRedis) {
      services.push(`  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "\${REDIS_PORT:-6379}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5`);
    }

    // MinIO (conditional)
    if (hasMinio) {
      services.push(`  minio:
    image: minio/minio:latest
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: \${MINIO_USER:-admin}
      MINIO_ROOT_PASSWORD: \${MINIO_PASSWORD:-changeme}
    ports:
      - "\${MINIO_PORT:-9000}:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data`);
    }

    const volumeNames = ["postgres_data"];
    if (hasMinio) volumeNames.push("minio_data");

    const lines = [
      `# Docker Compose — ${projectName}`,
      `# Generado por ProgresIA Studio`,
      `#`,
      `# Uso:`,
      `#   cp .env.example .env`,
      `#   docker compose up -d`,
      "",
      "version: '3.9'",
      "",
      "services:",
      services.join("\n\n"),
      "",
      "volumes:",
      ...volumeNames.map(v => `  ${v}:`),
      "",
      "networks:",
      "  default:",
      `    name: ${slug}_network`
    ];

    return lines.join("\n");
  }

  private renderEnvExample(projectName: string, stack: string[]): string {
    const slug = this.slugify(projectName);
    const hasRedis = stack.some(s => /redis|bull|queue/i.test(s));
    const hasMinio = stack.some(s => /minio|s3|storage/i.test(s));

    const lines = [
      `# Entorno de desarrollo — ${projectName}`,
      `# Copia este fichero a .env y ajusta los valores`,
      `# NUNCA subas .env a git (ya esta en .gitignore)`,
      "",
      "# ── Base de datos ────────────────────────────────────",
      `DB_USER=${slug}`,
      "DB_PASSWORD=changeme_en_produccion",
      `DB_NAME=${slug}_db`,
      "DB_PORT=5432",
      `DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@localhost:\${DB_PORT}/\${DB_NAME}`,
      "",
      "# ── Autenticacion ────────────────────────────────────",
      "JWT_SECRET=cambia_esto_por_un_secreto_largo_y_aleatorio",
      "JWT_EXPIRES_IN=1d",
      "",
      "# ── Aplicacion ───────────────────────────────────────",
      "NODE_ENV=development",
      "PORT=3000",
      `APP_URL=http://localhost:3000`
    ];

    if (hasRedis) {
      lines.push(
        "",
        "# ── Redis / Cola de trabajos ─────────────────────────",
        "REDIS_HOST=localhost",
        "REDIS_PORT=6379"
      );
    }

    if (hasMinio) {
      lines.push(
        "",
        "# ── Almacenamiento de objetos (MinIO / S3) ───────────",
        "MINIO_ENDPOINT=localhost",
        "MINIO_PORT=9000",
        "MINIO_USER=admin",
        "MINIO_PASSWORD=changeme_en_produccion",
        `MINIO_BUCKET=${slug}-files`
      );
    }

    return lines.join("\n");
  }

  private extractSourceSummary(source: Prisma.JsonValue) {
    if (!source || typeof source !== "object" || Array.isArray(source)) {
      return {};
    }

    const record = source as Record<string, unknown>;
    return {
      project: record.project,
      modules: record.modules,
      requirements: record.requirements,
      non_functional_requirements: record.non_functional_requirements,
      user_stories: record.user_stories,
      constraints: record.constraints,
      description: record.description,
      target_users: record.target_users
    };
  }

  private renderDataModel(projectName: string, summary: Record<string, unknown>): string {
    const dm = (typeof summary.data_model === "object" && summary.data_model)
      ? (summary.data_model as Record<string, unknown>)
      : {};
    const entities = Array.isArray(summary.data_entities)
      ? (summary.data_entities as Array<Record<string, unknown>>)
      : [];
    const technology   = (dm.technology   as string) || "PostgreSQL";
    const orm          = (dm.orm          as string) || "";
    const justification = (dm.justification as string) || "";
    const ormRationale  = (dm.orm_rationale as string) || "";
    const indexes      = Array.isArray(dm.indexes)       ? (dm.indexes as string[])          : [];
    const seedInstr    = Array.isArray(dm.seed_instructions) ? (dm.seed_instructions as string[]) : [];
    const secNotes     = Array.isArray(dm.security_notes) ? (dm.security_notes as string[])   : [];
    const mvpScope     = Array.isArray(dm.mvp_scope)     ? (dm.mvp_scope as string[])        : [];
    const futureScope  = Array.isArray(dm.future_scope)  ? (dm.future_scope as string[])     : [];
    const relationships = Array.isArray(dm.relationships) ? (dm.relationships as Array<Record<string, unknown>>) : [];

    const lines: string[] = [
      `# Modelo de datos — ${projectName}`,
      "",
      `## Base de datos principal: ${technology}`,
      orm ? `## ORM: ${orm}` : "",
      "",
      justification  ? `**Justificación:** ${justification}` : "",
      ormRationale   ? `**ORM — por qué:** ${ormRationale}`  : "",
      "",
    ];

    if (entities.length > 0) {
      lines.push("## Entidades principales", "");
      for (const entity of entities) {
        const fields = Array.isArray(entity.fields) ? (entity.fields as string[]) : [];
        const rels   = Array.isArray(entity.relations) ? (entity.relations as string[]) : [];
        lines.push(`### ${entity.name as string}`, "");
        if (entity.description) lines.push(`${entity.description as string}`, "");
        if (fields.length > 0) {
          lines.push("| Campo | Definición |", "| --- | --- |");
          for (const f of fields) {
            const [name, ...rest] = f.split(":");
            lines.push(`| \`${name.trim()}\` | ${rest.join(":").trim()} |`);
          }
          lines.push("");
        }
        if (rels.length > 0) {
          lines.push(`**Relaciones:** ${rels.filter(Boolean).join(" · ")}`, "");
        }
      }
    }

    if (relationships.length > 0) {
      lines.push("## Relaciones entre entidades", "");
      for (const r of relationships) {
        const cascade = r.cascade_delete ? " (CASCADE DELETE)" : "";
        const optional = r.optional ? " [opcional]" : "";
        lines.push(`- **${r.from_entity} → ${r.to_entity}** (${r.type})${cascade}${optional}`);
      }
      lines.push("");
    }

    if (indexes.length > 0) {
      lines.push("## Índices recomendados", "", "```sql");
      lines.push(...indexes);
      lines.push("```", "");
    }

    if (mvpScope.length > 0) {
      lines.push(`## Alcance MVP`, "", `Entidades incluidas en el MVP: ${mvpScope.join(", ")}`, "");
    }
    if (futureScope.length > 0) {
      lines.push(`**Previsto para fases posteriores:** ${futureScope.join(", ")}`, "");
    }

    if (seedInstr.length > 0) {
      lines.push("## Seeds y datos iniciales", "");
      for (const instr of seedInstr) lines.push(`- ${instr}`);
      lines.push("");
    }

    if (secNotes.length > 0) {
      lines.push("## Seguridad y privacidad", "");
      for (const note of secNotes) lines.push(`- ${note}`);
      lines.push("");
    }

    return lines.filter(l => l !== undefined).join("\n");
  }

  private renderErDiagram(projectName: string, summary: Record<string, unknown>): string {
    const dm = (typeof summary.data_model === "object" && summary.data_model)
      ? (summary.data_model as Record<string, unknown>)
      : {};
    const diagram = (dm.mermaid_diagram as string) || "";

    const lines = [
      `# Diagrama Entidad-Relación — ${projectName}`,
      "",
      "> Generado automáticamente por ProgresIA Studio. Puedes editarlo en [Mermaid Live Editor](https://mermaid.live).",
      "",
    ];

    if (diagram) {
      lines.push("```mermaid", diagram, "```");
    } else {
      lines.push("_Diagrama no disponible — regenera el OpenSpec para obtenerlo._");
    }

    return lines.join("\n");
  }

  private slugify(value: string): string {
    return slugify(value, "progresia-project");
  }
}
