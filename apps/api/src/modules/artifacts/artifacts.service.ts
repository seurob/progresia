import { ConflictException, Injectable, NotFoundException, UnprocessableEntityException } from "@nestjs/common";
import { Prisma, ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import * as JSZip from "jszip";
import { AiServiceClient } from "../ai-service/ai-service.client";
import { GithubService } from "../github/github.service";
import { StorageService } from "../storage/storage.service";
import { PrismaService } from "../../database/prisma.service";
import { ProjectsService } from "../projects/projects.service";
import { slugify } from "../../common/utils/string";
import { complexityToLevel } from "../../common/utils/project";
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
    const archSection = (typeof spec.architecture === "object" && spec.architecture)
      ? (spec.architecture as Record<string, unknown>)
      : {};
    const stack = this.extractStack(constraints, archSection);

    const dataEntities = Array.isArray(spec.data_entities)
      ? (spec.data_entities as Array<{ name: string; description?: string; fields?: string[]; relations?: string[] }>)
      : [];
    const apiEndpoints = Array.isArray(spec.api_endpoints)
      ? (spec.api_endpoints as Array<{ method: string; path: string; description: string; auth_required?: boolean }>)
      : [];

    const idea = await this.prisma.idea.findUnique({ where: { projectId: id } });

    const archSpec = await this.prisma.specification.findFirst({
      where: { projectId: id, type: SpecificationType.ARCHITECTURE, status: SpecificationStatus.GENERATED },
      orderBy: { createdAt: "desc" }
    });
    const architectureType =
      ((archSpec?.content as Record<string, unknown> | undefined)?.architecture_type as string | undefined)
      ?? (archSection.type as string | undefined);

    const technicalLevel = complexityToLevel(idea?.complexity);

    const generated = await this.aiServiceClient.generateCode({
      project_name: project.name,
      sector: project.sector,
      modules,
      requirements,
      needs_auth: idea?.needsAuth ?? true,
      needs_admin_panel: idea?.needsAdminPanel ?? true,
      needs_ai: idea?.needsAi ?? false,
      stack,
      architecture_type: architectureType,
      technical_level: technicalLevel,
      data_entities: dataEntities,
      api_endpoints: apiEndpoints
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

  private extractStack(
    constraints: Record<string, unknown>,
    architecture: Record<string, unknown>
  ): string[] {
    const architectureStack = Array.isArray(architecture.stack)
      ? (architecture.stack as string[])
      : [];
    const constraintsStack = Array.isArray(constraints.stack)
      ? (constraints.stack as string[])
      : [];

    return architectureStack.length > 0 ? architectureStack : constraintsStack;
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

    const manifest = bundle.manifest as unknown as Manifest;
    const generatedUsesRoot = generated.files.some(file => file.path === "README.md");
    const basePath = slugify(bundle.project.name);
    const filesByPath = new Map<string, string>();

    for (const file of manifest.files ?? []) {
      const path = generatedUsesRoot && file.path.startsWith(`${basePath}/`)
        ? file.path.slice(basePath.length + 1)
        : file.path;
      filesByPath.set(path, this.renderFileContent(file, manifest));
    }
    for (const file of generated.files) {
      filesByPath.set(file.path, file.content);
    }

    const result = await this.githubService.pushFiles(
      dto.githubToken,
      dto.repoName,
      dto.description ?? bundle.project.name,
      dto.isPrivate ?? false,
      Array.from(filesByPath.entries()).map(([path, content]) => ({ path, content })),
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

    const validation = await this.validateBundle(userId, bundleId);
    const blockers = validation.issues.filter(i => i.severity === "error");
    if (blockers.length > 0) {
      throw new UnprocessableEntityException({
        message: "El bundle tiene errores críticos que deben resolverse antes de descargar.",
        issues: blockers.map(i => i.message)
      });
    }

    const manifest = bundle.manifest as unknown as Manifest;
    const zip = new JSZip();

    const generated = bundle.generatedContent as unknown as {
      files?: Array<{ path: string; content: string }>;
    } | null;

    const generatedFiles = generated?.files ?? [];
    const basePath = slugify(bundle.project.name);
    const addedPaths = new Set<string>();

    // Manifest files already carry the basePath/ prefix (e.g. "bobhoy/sdd/...")
    for (const file of manifest.files ?? []) {
      if (!file.path || addedPaths.has(file.path)) continue;
      addedPaths.add(file.path);
      zip.file(file.path, this.renderFileContent(file, manifest));
    }

    // Generated files may arrive without the project prefix (e.g. "apps/web/..." or "README.md").
    // Prefix them so everything ends up inside one folder; generated content overrides manifest.
    for (const file of generatedFiles) {
      if (!file.path) continue;
      const zipPath = file.path.startsWith(`${basePath}/`)
        ? file.path
        : `${basePath}/${file.path}`;
      addedPaths.add(zipPath);
      zip.file(zipPath, file.content);
    }

    return zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  }

  async validateBundle(userId: string, bundleId: string): Promise<{
    valid: boolean;
    canDownload: boolean;
    fileCount: number;
    hasCode: boolean;
    hasSdd: boolean;
    hasReadme: boolean;
    hasEnvExample: boolean;
    hasDockerCompose: boolean;
    hasDocs: boolean;
    secretsFound: string[];
    issues: Array<{ message: string; severity: "error" | "warning" }>;
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
    const contentFiles = generated?.files ?? [];

    const issues: Array<{ message: string; severity: "error" | "warning" }> = [];
    const paths = files.map(f => f.path);

    // ── Critical checks (severity: error) ───────────────────────────────────

    if (paths.length === 0) {
      issues.push({ message: "El bundle no contiene archivos.", severity: "error" });
    }

    const dangerous = paths.filter(p => p.includes("..") || p.startsWith("/"));
    if (dangerous.length > 0) {
      issues.push({ message: `Rutas peligrosas detectadas: ${dangerous[0]}`, severity: "error" });
    }

    const dupes = paths.filter((p, i) => paths.indexOf(p) !== i);
    if (dupes.length > 0) {
      issues.push({ message: `Rutas duplicadas: ${dupes.slice(0, 3).join(", ")}`, severity: "warning" });
    }

    // ── Secrets scan in generated content files ──────────────────────────────
    // Pattern: KEY=VALUE where value is non-placeholder and ≥8 chars
    // Exclude placeholder prefixes common in scaffold code (change, cambia, replace, insecure, example…)
    const secretPattern = /(?:PASSWORD|SECRET|API_KEY|PRIVATE_KEY|ACCESS_TOKEN|AUTH_TOKEN)\s*=\s*(?!\$\{)(?!your-)(?!<)(?!change)(?!cambia)(?!replace)(?!insecure)(?!example)(?!sample)(?!dummy)(?!placeholder)(?!dev-)(?!test-)(?!fake)[^\s'"]{8,}/gi;
    const secretsFound: string[] = [];
    for (const f of contentFiles) {
      const basename = f.path.split("/").pop() ?? f.path;
      if (basename.endsWith(".example") || basename.endsWith(".md") || basename === ".env") continue;
      for (const match of (f.content ?? "").matchAll(secretPattern)) {
        const key = match[0].split("=")[0].trim();
        secretsFound.push(`${f.path}: ${key}`);
      }
    }
    if (secretsFound.length > 0) {
      issues.push({
        message: `Cambia los valores de prueba antes de desplegar: ${secretsFound.slice(0, 2).join(", ")}`,
        severity: "warning"
      });
    }

    // ── Structural checks (severity: warning) ────────────────────────────────

    const hasCode = paths.some(p =>
      /\.(ts|tsx|js|jsx|py|php|rb|go|rs|java|cs)$/.test(p) ||
      p.includes("package.json") || p.includes("composer.json") || p.includes("pyproject.toml")
    );
    const hasSdd = paths.some(p => p.includes("sdd/"));
    const hasReadme = paths.some(p => p.endsWith("README.md"));
    const hasEnvExample = paths.some(p => p.endsWith(".env.example"));
    const hasDockerCompose = paths.some(p => p.endsWith("docker-compose.yml") || p.endsWith("Dockerfile"));
    const hasDocs = paths.some(p => p.includes("docs/"));

    if (!hasCode && !hasSdd) {
      issues.push({ message: "El bundle no contiene archivos de código ni especificaciones SDD.", severity: "warning" });
    }
    if (!hasReadme) {
      issues.push({ message: "Falta README.md.", severity: "warning" });
    }
    if (!hasEnvExample) {
      issues.push({ message: "Falta .env.example (variables de entorno requeridas).", severity: "warning" });
    }
    if (!hasDockerCompose) {
      issues.push({ message: "Falta docker-compose.yml o Dockerfile para el entorno de desarrollo.", severity: "warning" });
    }
    if (!hasDocs) {
      issues.push({ message: "Falta carpeta docs/ con documentación técnica.", severity: "warning" });
    }

    const readme = contentFiles.find(f => f.path.endsWith("README.md"));
    const constraints = (manifest.sourceSummary?.constraints && typeof manifest.sourceSummary.constraints === "object")
      ? (manifest.sourceSummary.constraints as Record<string, unknown>)
      : {};
    const summaryStack = Array.isArray(constraints.stack) ? (constraints.stack as string[]) : [];
    if (readme && summaryStack.length > 0) {
      const missingStack = summaryStack.filter(tech => {
        const token = tech.toLowerCase().split(/\s+/)[0];
        return token.length > 1 && !readme.content.toLowerCase().includes(token);
      });
      if (missingStack.length > 0) {
        issues.push({
          message: `README no menciona tecnologias del stack: ${missingStack.slice(0, 3).join(", ")}`,
          severity: "warning"
        });
      }
    }

    const officialLinkFiles = contentFiles.filter(f => f.path.endsWith("README.md") || f.path.includes("docs/"));
    const hasOfficialLinks = officialLinkFiles.some(f =>
      /https?:\/\/(nodejs\.org|docs\.|developer\.mozilla\.org|react\.dev|nextjs\.org|nestjs\.com|fastapi\.tiangolo\.com|laravel\.com|djangoproject\.com|postgresql\.org|docker\.com|qdrant\.tech)/i.test(f.content)
    );
    if (officialLinkFiles.length > 0 && !hasOfficialLinks) {
      issues.push({ message: "No se detectaron enlaces claros a documentacion oficial en README/docs.", severity: "warning" });
    }

    const emptyDirEntries = paths.filter(path => path.endsWith("/"));
    if (emptyDirEntries.length > 0) {
      issues.push({ message: `Carpetas vacias detectadas: ${emptyDirEntries.slice(0, 3).join(", ")}`, severity: "warning" });
    }

    const hasErrors = issues.some(i => i.severity === "error");

    return {
      valid: !hasErrors,
      canDownload: !hasErrors,
      fileCount: paths.length,
      hasCode,
      hasSdd,
      hasReadme,
      hasEnvExample,
      hasDockerCompose,
      hasDocs,
      secretsFound,
      issues,
    };
  }

  async bundleSummary(userId: string, bundleId: string) {
    const bundle = await this.prisma.artifactBundle.findUnique({
      where: { id: bundleId },
      include: { project: true }
    });

    if (!bundle) throw new NotFoundException("Artifact bundle not found");
    await this.projectsService.ensureProjectAccess(bundle.projectId, userId);

    const manifest = bundle.manifest as unknown as Manifest;
    const summary = manifest.sourceSummary ?? {};
    const constraints = (typeof summary.constraints === "object" && summary.constraints)
      ? (summary.constraints as Record<string, unknown>)
      : {};
    const stack: string[] = Array.isArray(constraints.stack) ? (constraints.stack as string[]) : [];
    const modules: string[] = Array.isArray(summary.modules) ? (summary.modules as string[]) : [];

    const generated = bundle.generatedContent as unknown as {
      files?: Array<{ path: string; content: string }>;
    } | null;
    const allPaths = this.mergeBundleFiles(manifest.files ?? [], generated?.files ?? []).map(f => f.path);

    const hasPython = stack.some(s => /python|fastapi|django|flask/i.test(s));
    const hasLaravel = stack.some(s => /laravel|php/i.test(s));

    const services = this.deriveServices(stack, hasPython, hasLaravel);
    const prerequisites = this.derivePrerequisites(stack, hasPython, hasLaravel);

    const quickstart = [
      "# 1. Clonar el repositorio",
      `git clone <repo-url> ${slugify(bundle.project.name)}`,
      "",
      "# 2. Variables de entorno",
      "cp .env.example .env   # Linux/macOS",
      "# Copy-Item .env.example .env  # Windows PowerShell",
      "",
      "# 3. Infraestructura",
      "docker compose up -d",
      "",
      "# 4. Dependencias y migraciones",
      hasLaravel
        ? "composer install && php artisan migrate --seed"
        : "npm install && npm run db:migrate",
      ...(hasPython ? ["pip install -r apps/ai-service/requirements.txt"] : []),
      "",
      "# 5. Arrancar en desarrollo",
      hasLaravel ? "php artisan serve" : "npm run dev"
    ];

    const costs = {
      development: "0 €/mes (Docker local, sin coste)",
      staging: "~5–15 €/mes (Render free / Railway hobby)",
      production: "~20–50 €/mes (Fly.io + Supabase / Railway pro)",
      database: "~0–25 €/mes (Supabase free → Pro / Railway PostgreSQL)",
      notes: "Escala con el volumen de usuarios. Ver docs/deployment/ para guías detalladas."
    };

    const nextSteps = [
      "Edita .env con tus credenciales reales",
      "Lee sdd/constitution.md para entender la arquitectura",
      "Sigue M1 en sdd/plans/milestones.md para el primer sprint",
      "Usa sdd/prompts/project-context.md al abrir una sesión con Claude o Copilot",
      ...(allPaths.some(p => p.includes("sdd/acceptance-criteria")) ? ["Revisa sdd/acceptance-criteria.md para los criterios de 'hecho'"] : []),
    ];

    return {
      projectName: bundle.project.name,
      stack,
      modules,
      services,
      costs,
      prerequisites,
      quickstart,
      nextSteps,
      fileCount: allPaths.length,
      generatedAt: manifest.generatedAt,
      validation: {
        hasCode: allPaths.some(p => /\.(ts|tsx|js|jsx|py|php)$/.test(p)),
        hasSdd: allPaths.some(p => p.includes("sdd/")),
        hasReadme: allPaths.some(p => p.endsWith("README.md")),
        hasDockerCompose: allPaths.some(p => p.endsWith("docker-compose.yml"))
      }
    };
  }

  private deriveServices(stack: string[], hasPython: boolean, hasLaravel: boolean) {
    const services: Array<{ name: string; port: number; url: string }> = [];
    if (stack.some(s => /react|vue|next|angular|svelte/i.test(s))) {
      services.push({ name: "Frontend", port: 5173, url: "http://localhost:5173" });
    }
    if (!hasLaravel && stack.some(s => /node|nest|express/i.test(s))) {
      services.push({ name: "API", port: 3000, url: "http://localhost:3000" });
    }
    if (hasLaravel) {
      services.push({ name: "API (Laravel)", port: 8000, url: "http://localhost:8000" });
    }
    if (hasPython) {
      services.push({ name: "AI Service", port: 8003, url: "http://localhost:8003" });
    }
    services.push({ name: "PostgreSQL", port: 5432, url: "postgresql://localhost:5432" });
    return services;
  }

  private derivePrerequisites(stack: string[], hasPython: boolean, hasLaravel: boolean) {
    const prerequisites: string[] = [];
    if (hasLaravel) {
      prerequisites.push("PHP 8.2+ — https://php.net", "Composer 2.x — https://getcomposer.org");
    }
    if (stack.some(s => /node|nest|express|next|react|vue|angular/i.test(s))) {
      prerequisites.push("Node.js 20 LTS — https://nodejs.org");
    }
    prerequisites.push("Git 2.x — https://git-scm.com");
    if (hasPython) prerequisites.push("Python 3.12+ — https://python.org");
    prerequisites.push("Docker Desktop 4.x — https://docker.com/products/docker-desktop");
    return prerequisites;
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

  private createManifest(input: {
    projectName: string;
    sourceSpecificationId: string;
    source: Prisma.JsonValue;
  }) {
    const basePath = slugify(input.projectName);
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
      // ── Extended SDD ─────────────────────────────────────────────────────
      {
        path: `${basePath}/sdd/technology-decisions.md`,
        kind: "document",
        description: "Decisiones tecnológicas: tabla comparativa de alternativas, motivos de elección y deuda técnica aceptada.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/non-functional-requirements.md`,
        kind: "document",
        description: "Requisitos no funcionales: rendimiento, seguridad, fiabilidad, escalabilidad y observabilidad con objetivos medibles.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/acceptance-criteria.md`,
        kind: "document",
        description: "Criterios de aceptación por módulo: condiciones para considerar una feature terminada.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/ai-development-instructions.md`,
        kind: "document",
        description: "Instrucciones para IA: cómo usar Claude Code, Copilot y ChatGPT eficazmente en este proyecto.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/ai-testing-instructions.md`,
        kind: "document",
        description: "Estrategia de testing con IA: convenciones, prompts útiles y casos obligatorios por módulo.",
        source: "openspec"
      },
      // ── OpenSpec JSON ─────────────────────────────────────────────────────
      {
        path: `${basePath}/sdd/specifications/openspec.json`,
        kind: "specification",
        description: "Especificacion tecnica completa generada por IA (OpenSpec JSON).",
        source: "openspec"
      },
      // ── Root extras ───────────────────────────────────────────────────────
      {
        path: `${basePath}/.gitignore`,
        kind: "specification",
        description: "Patrones de exclusion de git: protege secretos, artefactos de build y dependencias.",
        source: "openspec"
      },
      {
        path: `${basePath}/.editorconfig`,
        kind: "specification",
        description: "Configuracion de editor: indentacion, charset y fin de linea uniformes para todo el equipo.",
        source: "openspec"
      },
      {
        path: `${basePath}/docker-compose.dev.yml`,
        kind: "specification",
        description: "Docker Compose de desarrollo con puertos debug, volúmenes y health checks.",
        source: "openspec"
      },
      // ── GitHub CI ─────────────────────────────────────────────────────────
      {
        path: `${basePath}/.github/workflows/ci.yml`,
        kind: "specification",
        description: "GitHub Actions CI: lint, type-check y tests en cada push y pull request.",
        source: "openspec"
      },
      // ── Docs extra ────────────────────────────────────────────────────────
      {
        path: `${basePath}/docs/api/api-reference.md`,
        kind: "document",
        description: "Referencia de la API REST: endpoints, autenticacion, ejemplos de request y response.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/deployment/deployment-guide.md`,
        kind: "document",
        description: "Guia de despliegue: Railway, Render, VPS con Docker y variables de entorno de produccion.",
        source: "openspec"
      },
      // ── SDD extras ────────────────────────────────────────────────────────
      {
        path: `${basePath}/sdd/tasks/backlog.md`,
        kind: "document",
        description: "Backlog inicial de tareas organizado por modulo y prioridad.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/plans/learning-plan.md`,
        kind: "document",
        description: "Plan de aprendizaje personalizado: recursos, orden de estudio e hitos de conocimiento.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/product/idea-negocio.md`,
        kind: "document",
        description: "Idea de negocio, problema, publico objetivo y oportunidad del MVP.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/product/problema-a-resolver.md`,
        kind: "document",
        description: "Dolor principal del usuario y alcance del problema que resuelve el producto.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/product/publico-objetivo.md`,
        kind: "document",
        description: "Perfiles de usuario, necesidades y contexto de uso.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/product/propuesta-valor.md`,
        kind: "document",
        description: "Valor diferencial, beneficios y riesgos de adopcion.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/product/mvp.md`,
        kind: "document",
        description: "Alcance del MVP, fuera de alcance y metricas de validacion.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/development/environment-setup.md`,
        kind: "document",
        description: "Setup completo del entorno con herramientas requeridas y comandos por sistema operativo.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/development/windows-setup.md`,
        kind: "document",
        description: "Instalacion en Windows con PowerShell, Docker Desktop y herramientas del stack.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/development/linux-setup.md`,
        kind: "document",
        description: "Instalacion en Linux con Docker Engine y herramientas del stack.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/development/macos-setup.md`,
        kind: "document",
        description: "Instalacion en macOS con Homebrew, Docker Desktop y herramientas del stack.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/development/development-workflow.md`,
        kind: "document",
        description: "Flujo diario con ramas, commits, specs, tests y actualizacion SDD.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/development/testing-guide.md`,
        kind: "document",
        description: "Guia de pruebas unitarias, integracion, E2E y checks antes de publicar.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/architecture/modelo-datos.md`,
        kind: "document",
        description: "Modelo de datos explicado para estudiantes: entidades, relaciones, indices y seeds.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/architecture/decisiones-arquitectura.md`,
        kind: "document",
        description: "Resumen pedagogico de decisiones de arquitectura y alternativas descartadas.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/api/endpoints.md`,
        kind: "document",
        description: "Lista de endpoints REST previstos con metodo, ruta, auth y objetivo.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/api/contrato-api.md`,
        kind: "document",
        description: "Contrato de API: request, response, errores y versionado.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/api/autenticacion-autorizacion.md`,
        kind: "document",
        description: "Flujo de autenticacion, autorizacion, roles y proteccion de endpoints.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/ai/estrategia-ia.md`,
        kind: "document",
        description: "Estrategia de IA: cuando usar online, local, hibrida, RAG o agentes.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/ai/rag.md`,
        kind: "document",
        description: "Guia RAG: documentos, embeddings, base vectorial y casos en los que no compensa.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/ai/embeddings.md`,
        kind: "document",
        description: "Embeddings: criterios de modelo, coste, privacidad y evaluacion.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/ai/agentes.md`,
        kind: "document",
        description: "Agentes IA: responsabilidades, limites, herramientas y evaluacion.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/deployment/desarrollo-local.md`,
        kind: "document",
        description: "Despliegue local con Docker Compose y comandos de verificacion.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/deployment/docker.md`,
        kind: "document",
        description: "Docker: servicios, imagenes, volumenes, logs, rebuild y troubleshooting.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/deployment/produccion.md`,
        kind: "document",
        description: "Primer despliegue en VPS, Railway, Render, Fly.io, Vercel o Netlify segun stack.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/deployment/variables-entorno.md`,
        kind: "document",
        description: "Variables de entorno requeridas por entorno y reglas para secretos.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/deployment/costes-y-servicios-externos.md`,
        kind: "document",
        description: "Costes estimados de hosting, base de datos, email, almacenamiento e IA.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/requirements/functional-requirements.md`,
        kind: "document",
        description: "Requisitos funcionales separados por modulo con prioridad y criterios de aceptacion.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/requirements/non-functional-requirements.md`,
        kind: "document",
        description: "Requisitos no funcionales dentro de la carpeta de requisitos.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/requirements/acceptance-criteria.md`,
        kind: "document",
        description: "Criterios de aceptacion por historia y modulo dentro de requisitos.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/specifications/feature-001-main-module.md`,
        kind: "specification",
        description: "Primera especificacion de funcionalidad basada en el modulo principal del MVP.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/plans/implementation-plan.md`,
        kind: "document",
        description: "Plan de implementacion paso a paso con dependencias y orden recomendado.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/plans/release-plan.md`,
        kind: "document",
        description: "Plan de releases: MVP, beta, hardening y primera version publica.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/tasks/initial-tasks.md`,
        kind: "document",
        description: "Primeras tareas recomendadas para levantar el MVP sin perder el contexto SDD.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/tasks/task-status.md`,
        kind: "document",
        description: "Estado inicial de tareas para seguimiento manual o importacion a GitHub Issues.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/ai-development-instructions.md`,
        kind: "document",
        description: "Workflow obligatorio para asistentes IA: leer contexto, implementar alcance y actualizar SDD.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/ai-code-review-instructions.md`,
        kind: "document",
        description: "Checklist para que una IA revise bugs, riesgos, tests y seguridad.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/ai-testing-instructions.md`,
        kind: "document",
        description: "Prompts y reglas para crear tests con IA sin inventar comportamiento.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/prompts/ai-documentation-instructions.md`,
        kind: "document",
        description: "Reglas para actualizar README, docs, ADR y SDD tras cada cambio.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/setup/windows.md`,
        kind: "document",
        description: "Setup Windows con PowerShell, Docker Desktop, Git y herramientas del stack.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/setup/linux.md`,
        kind: "document",
        description: "Setup Linux con gestor de paquetes, Docker Engine y herramientas del stack.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/setup/macos.md`,
        kind: "document",
        description: "Setup macOS con Homebrew, Docker Desktop y herramientas del stack.",
        source: "openspec"
      },
      {
        path: `${basePath}/sdd/setup/required-tools.md`,
        kind: "document",
        description: "Herramientas requeridas y opcionales para desarrollo, testing y despliegue.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/docker/frontend.Dockerfile`,
        kind: "specification",
        description: "Dockerfile de frontend preparado para build estatico o servidor dev.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/docker/backend.Dockerfile`,
        kind: "specification",
        description: "Dockerfile de backend/API con instalacion reproducible.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/docker/ai-service.Dockerfile`,
        kind: "specification",
        description: "Dockerfile opcional del servicio IA cuando el proyecto incluye IA.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/docker/nginx.Dockerfile`,
        kind: "specification",
        description: "Dockerfile de nginx para proxy inverso y assets estaticos.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/nginx/default.conf`,
        kind: "specification",
        description: "Configuracion base de nginx para enrutar frontend, API y servicio IA.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/scripts/start-dev.sh`,
        kind: "specification",
        description: "Script para levantar el entorno local.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/scripts/stop-dev.sh`,
        kind: "specification",
        description: "Script para parar contenedores locales.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/scripts/reset-db.sh`,
        kind: "specification",
        description: "Script para resetear base de datos y seeds.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/scripts/test.sh`,
        kind: "specification",
        description: "Script para ejecutar validaciones locales.",
        source: "openspec"
      },
      {
        path: `${basePath}/infrastructure/scripts/deploy.sh`,
        kind: "specification",
        description: "Script inicial de despliegue para VPS o entorno Docker.",
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

    if (p.includes("docs/product/")) {
      return this.renderProductDoc(projectName, summary, p);
    }

    if (p.includes("docs/development/") && !p.endsWith("contributing.md")) {
      return this.renderDevelopmentDoc(projectName, stack, p);
    }

    if (p.includes("docs/api/")) {
      return this.renderApiDoc(projectName, summary, modules, p);
    }

    if (p.includes("docs/ai/")) {
      return this.renderAiDoc(projectName, stack, p);
    }

    if (p.includes("docs/deployment/") && !p.endsWith("deployment-guide.md")) {
      return this.renderDeploymentDoc(projectName, stack, p);
    }

    if (p.endsWith("modelo-datos.md")) {
      return this.renderDataModel(projectName, summary);
    }

    if (p.endsWith("decisiones-arquitectura.md")) {
      return this.renderArchitectureDecisions(projectName, stack, modules);
    }

    if (p.endsWith("functional-requirements.md")) {
      return this.renderFunctionalRequirements(projectName, requirements, modules);
    }

    if (p.endsWith("non-functional-requirements.md")) {
      return this.renderNFR(projectName, nonFunctional);
    }

    if (p.endsWith("acceptance-criteria.md")) {
      return this.renderAcceptanceCriteria(projectName, modules);
    }

    if (p.endsWith("feature-001-main-module.md")) {
      return this.renderFeatureSpec(projectName, modules);
    }

    if (p.endsWith("implementation-plan.md")) {
      return this.renderImplementationSteps(projectName, modules);
    }

    if (p.endsWith("release-plan.md")) {
      return this.renderReleasePlan(projectName, modules);
    }

    if (p.endsWith("initial-tasks.md")) {
      return this.renderInitialTasks(projectName, modules);
    }

    if (p.endsWith("task-status.md")) {
      return this.renderTaskStatus(projectName, modules);
    }

    if (p.includes("sdd/setup/") && !p.endsWith("environment.md")) {
      return this.renderSetupDoc(projectName, stack, p);
    }

    if (p.includes("infrastructure/docker/") && p.endsWith("Dockerfile")) {
      return this.renderDockerfile(p);
    }

    if (p.endsWith("infrastructure/nginx/default.conf")) {
      return this.renderNginxConf(stack);
    }

    if (p.includes("infrastructure/scripts/") && p.endsWith(".sh")) {
      return this.renderInfrastructureScript(p);
    }

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

    if (p.endsWith("openspec.md")) {
      return this.renderOpenSpecMd(projectName, summary);
    }

    if (p.endsWith("resume-session.md")) {
      return this.renderResumeSession(projectName, stack, modules);
    }

    if (p.endsWith("add-feature.md")) {
      return this.renderAddFeaturePrompt(projectName, stack, modules);
    }

    if (p.endsWith("fix-bug.md")) {
      return this.renderFixBugPrompt(projectName, stack);
    }

    if (p.includes("sdd/setup/environment.md")) {
      return this.renderEnvironmentSetup(projectName, stack);
    }

    if (p.endsWith("technology-decisions.md")) {
      return this.renderTechDecisions(projectName, stack);
    }

    if (p.endsWith("ai-development-instructions.md")) {
      return this.renderAiDevInstructions(projectName, stack, modules);
    }

    if (p.endsWith("ai-testing-instructions.md")) {
      return this.renderAiTestingInstructions(projectName, modules);
    }

    if (p.endsWith(".gitignore")) {
      return this.renderGitignore(stack);
    }

    if (p.endsWith(".editorconfig")) {
      return this.renderEditorConfig();
    }

    if (p.endsWith("docker-compose.dev.yml")) {
      return this.renderDevDockerCompose(projectName, stack);
    }

    if (p.endsWith("ci.yml")) {
      return this.renderCiYaml(projectName, stack);
    }

    if (p.endsWith("api-reference.md")) {
      return this.renderApiReference(projectName, summary, modules);
    }

    if (p.endsWith("deployment-guide.md")) {
      return this.renderDeploymentGuide(projectName, stack);
    }

    if (p.endsWith("backlog.md")) {
      return this.renderBacklog(projectName, modules);
    }

    if (p.endsWith("learning-plan.md")) {
      return this.renderLearningPlan(projectName, stack, modules);
    }

    // Generic markdown stub for remaining SDD files
    return `# ${p.split("/").pop()?.replace(".md", "").replace(/-/g, " ")}\n\n> Parte del proyecto **${projectName}**.\n\n${file.description}\n`;
  }

  private renderProjectGuideReadme(
    projectName: string,
    manifest: Manifest,
    modules: string[],
    stack: string[]
  ): string {
    const slug = slugify(projectName);
    const summary = manifest.sourceSummary ?? {};
    const description = String(
      summary.description
        ?? summary.summary
        ?? `${projectName} es un MVP generado desde una especificacion SDD.`
    );
    const targetUsers = String(summary.target_users ?? "Usuarios objetivo definidos durante el intake.");
    const requirements = Array.isArray(summary.requirements)
      ? (summary.requirements as Array<Record<string, unknown>>)
      : [];
    const hasPython = stack.some(s => /python|fastapi|django|flask|ai/i.test(s));
    const hasLaravel = stack.some(s => /laravel|php/i.test(s));
    const hasNode = stack.some(s => /node|nest|express|next|react|vue|angular|svelte/i.test(s));
    const hasRedis = stack.some(s => /redis/i.test(s));
    const hasQdrant = stack.some(s => /qdrant|vector/i.test(s));
    const hasMinio = stack.some(s => /minio|s3|storage/i.test(s));
    const services = this.deriveServices(stack, hasPython, hasLaravel);
    if (hasRedis) services.push({ name: "Redis", port: 6379, url: "redis://localhost:6379" });
    if (hasQdrant) services.push({ name: "Qdrant", port: 6333, url: "http://localhost:6333" });
    if (hasMinio) services.push({ name: "MinIO", port: 9000, url: "http://localhost:9000" });
    const prerequisites = this.derivePrerequisites(stack, hasPython, hasLaravel);
    const generatedDate = new Date(manifest.generatedAt).toLocaleDateString("es-ES", {
      year: "numeric", month: "long", day: "numeric"
    });
    const stackLine = stack.length > 0 ? stack.slice(0, 6).join(" - ") : "React - NestJS - PostgreSQL";
    const moduleLines = modules.length > 0
      ? modules.map(m => `- ${m}`)
      : ["- Core MVP: flujo principal definido en la especificacion SDD."];
    const requirementLines = requirements.length > 0
      ? requirements.slice(0, 8).map((r, index) => `- ${String(r.title ?? r.id ?? `REQ-${index + 1}`)}: ${String(r.description ?? "Requisito definido en OpenSpec.")}`)
      : ["- Consultar `sdd/specifications/` y `sdd/requirements/` para el detalle funcional."];
    const pythonInstall = hasPython
      ? [
          "",
          "### 5. Servicio de IA / Python",
          "",
          "```bash",
          "cd apps/ai-service",
          "python -m venv .venv",
          "# Linux / macOS: source .venv/bin/activate",
          "# Windows: .\\.venv\\Scripts\\Activate.ps1",
          "pip install -r requirements.txt",
          "cd ../..",
          "```",
          ""
        ]
      : [];
    const runStepNumber = hasPython ? 6 : 5;
    const docsLinks = this.renderReadmeOfficialLinks(stack, { hasPython, hasLaravel, hasRedis, hasQdrant, hasMinio });
    const dockerRows = this.renderReadmeDockerRows({ hasPython, hasLaravel, hasRedis, hasQdrant, hasMinio });
    const commandBlocks = this.renderReadmeCommandBlocks({ hasPython, hasLaravel, hasNode });
    const deploymentLines = this.renderReadmeDeploymentLines({ hasPython, hasLaravel });
    const costLines = this.renderReadmeCostLines({ hasPython, hasRedis, hasQdrant, hasMinio });

    return [
      `# ${projectName}`,
      "",
      `> Proyecto generado con **ProgresIA Studio** el ${generatedDate}.`,
      "> Este README resume el proyecto completo y explica como levantarlo en local.",
      `> Stack: ${stackLine}`,
      "",
      "---",
      "",
      "## Resumen del proyecto",
      "",
      description,
      "",
      `**Sector / contexto:** ${String(summary.sector ?? "Definido durante el intake")}`,
      `**Usuarios objetivo:** ${targetUsers}`,
      "",
      "### Alcance MVP",
      "",
      ...moduleLines,
      "",
      "### Requisitos principales",
      "",
      ...requirementLines,
      "",
      "---",
      "",
      "## Que incluye este ZIP",
      "",
      "- Codigo base del frontend y backend generado para el MVP.",
      "- Documentacion SDD en `sdd/`: requisitos, especificaciones, planes, tareas y prompts para continuar con IA.",
      "- Documentacion tecnica en `docs/`: arquitectura, API, desarrollo, despliegue y decisiones ADR.",
      "- Infraestructura local con `docker-compose.yml`, `docker-compose.dev.yml` y `.env.example`.",
      "- Automatizacion inicial de calidad en `.github/workflows/ci.yml`.",
      "",
      "---",
      "",
      "## Stack y servicios locales",
      "",
      "| Servicio | URL | Puerto |",
      "|----------|-----|--------|",
      ...services.map(service => `| ${service.name} | ${service.url} | ${service.port} |`),
      "",
      ...(stack.length > 0 ? ["### Tecnologias", "", ...stack.map(s => `- ${s}`), ""] : []),
      "### Documentacion oficial",
      "",
      ...docsLinks,
      "",
      "---",
      "",
      "## Requisitos previos",
      "",
      ...prerequisites.map(item => `- ${item}`),
      "",
      "---",
      "",
      "## Servicios Docker",
      "",
      "| Servicio | Para que sirve | Puerto local | Persistencia |",
      "|----------|----------------|--------------|--------------|",
      ...dockerRows,
      "",
      "Comandos utiles para infraestructura:",
      "",
      "```bash",
      "docker compose ps",
      "docker compose logs -f",
      "docker compose down",
      "docker compose down -v  # borra tambien volumenes/datos locales",
      "```",
      "",
      "---",
      "",
      "## Como levantar el proyecto",
      "",
      "### 1. Entrar en la carpeta",
      "",
      "```bash",
      `cd ${slug}`,
      "```",
      "",
      "### 2. Configurar variables de entorno",
      "",
      "```bash",
      "# Linux / macOS",
      "cp .env.example .env",
      "",
      "# Windows (PowerShell)",
      "Copy-Item .env.example .env",
      "```",
      "",
      "Edita `.env` antes de arrancar si necesitas cambiar credenciales, puertos o claves externas.",
      "",
      "### 3. Levantar infraestructura local",
      "",
      "```bash",
      "docker compose up -d",
      "```",
      "",
      "### 4. Instalar dependencias y preparar la base de datos",
      "",
      ...(hasLaravel
        ? ["```bash", "composer install", "php artisan migrate --seed", "```"]
        : hasNode
          ? ["```bash", "npm install", "npm run db:migrate", "```"]
          : ["```bash", "# Instala las dependencias indicadas por el stack generado.", "```"]),
      ...pythonInstall,
      `### ${runStepNumber}. Arrancar en desarrollo`,
      "",
      "#### Linux / macOS",
      "",
      "```bash",
      hasLaravel ? "php artisan serve" : "npm run dev",
      "```",
      "",
      "#### Windows (PowerShell)",
      "",
      "```powershell",
      ...(hasLaravel
        ? ["php artisan serve"]
        : [
            "# Terminal 1 - API",
            "cd apps/api; npm run dev",
            "",
            "# Terminal 2 - Frontend",
            "cd apps/web; npm run dev",
            ...(hasPython ? ["", "# Terminal 3 - AI Service", "cd apps/ai-service; python -m uvicorn app.main:app --port 8003 --reload"] : [])
          ]),
      "```",
      "",
      `### ${runStepNumber + 1}. Verificar que funciona`,
      "",
      "- Abre el frontend en `http://localhost:5173` si el proyecto incluye web.",
      "- Revisa la API en `http://localhost:3000` o en el puerto indicado arriba.",
      "- Si hay servicio de IA, prueba `http://localhost:8003/health`.",
      "- Si algo falla, mira logs con `docker compose logs -f` y revisa `.env`.",
      "",
      "---",
      "",
      "## Comandos utiles",
      "",
      ...commandBlocks,
      "",
      "---",
      "",
      "## Despliegue inicial",
      "",
      ...deploymentLines,
      "",
      "---",
      "",
      "## Costes estimados",
      "",
      ...costLines,
      "",
      "---",
      "",
      "## Estructura del proyecto",
      "",
      "```text",
      `${slug}/`,
      "+-- apps/",
      "|   +-- web/              # Frontend",
      "|   +-- api/              # Backend API",
      ...(hasPython ? ["|   +-- ai-service/       # Servicio de IA / agentes"] : []),
      "+-- sdd/                  # Especificaciones SDD",
      "|   +-- constitution.md    # Arquitectura y decisiones",
      "|   +-- requirements/      # Requisitos, user stories y modelo de datos",
      "|   +-- specifications/    # OpenSpec completo",
      "|   +-- plans/             # Milestones y plan de aprendizaje",
      "|   +-- tasks/             # Backlog de tareas por modulo",
      "|   +-- prompts/           # Instrucciones para continuar con IA",
      "|   +-- setup/             # Guia de entorno local",
      "+-- docs/",
      "|   +-- architecture/      # Diagramas y overview del sistema",
      "|   +-- api/               # Referencia de la API",
      "|   +-- deployment/        # Guia de despliegue",
      "|   +-- development/       # Guia de contribucion",
      "|   +-- adr/               # Architecture Decision Records",
      "+-- .github/workflows/     # GitHub Actions CI",
      "+-- docker-compose.yml",
      "+-- docker-compose.dev.yml",
      "+-- .env.example",
      "+-- README.md",
      "```",
      "",
      "---",
      "",
      "## Documentacion generada",
      "",
      "- `docs/product/project-brief.md`: resumen de producto y alcance.",
      "- `docs/architecture/system-overview.md`: arquitectura recomendada.",
      "- `docs/api/api-reference.md`: endpoints previstos.",
      "- `docs/deployment/deployment-guide.md`: pasos de despliegue.",
      "- `sdd/specifications/`: OpenSpec en formato tecnico.",
      "- `sdd/prompts/`: prompts para seguir desarrollando con IA.",
      "",
      "---",
      "",
      "## Continuar con IA",
      "",
      "Este proyecto incluye instrucciones para IA en `sdd/prompts/`:",
      "",
      "- `project-context.md` - Contexto completo para abrir una nueva sesion",
      "- `resume-session.md` - Para retomar el trabajo donde lo dejaste",
      "- `add-feature.md` - Para anadir nuevas funcionalidades",
      "- `fix-bug.md` - Para resolver errores con ayuda de IA",
      "",
      "Antes de pedir nuevas features, comparte con la IA este README, `sdd/constitution.md` y el OpenSpec generado.",
      "",
      "---",
      "",
      "## Troubleshooting rapido",
      "",
      "- **Docker no arranca:** abre Docker Desktop y ejecuta otra vez `docker compose up -d`.",
      "- **Puerto ocupado:** cambia el puerto en `.env` o detiene el proceso que lo usa.",
      "- **Error de migraciones:** revisa `DATABASE_URL` y que PostgreSQL este levantado.",
      "- **Frontend no conecta con API:** confirma la URL publica de API en `.env` del frontend.",
      "- **Servicio de IA no responde:** activa el entorno virtual e instala `requirements.txt`.",
      "",
      "---",
      "",
      "_Generado con [ProgresIA Studio](https://progresia.studio)_"
    ].join("\n");
  }

  private renderReadme(
    projectName: string,
    manifest: Manifest,
    modules: string[],
    stack: string[]
  ): string {
    return this.renderProjectGuideReadme(projectName, manifest, modules, stack);
  }

  private renderReadmeOfficialLinks(
    stack: string[],
    flags: { hasPython: boolean; hasLaravel: boolean; hasRedis: boolean; hasQdrant: boolean; hasMinio: boolean }
  ): string[] {
    const text = stack.join(" ").toLowerCase();
    const links = new Map<string, string>();
    links.set("Node.js", "https://nodejs.org/en/docs");
    links.set("Docker Compose", "https://docs.docker.com/compose/");
    if (/react/i.test(text)) links.set("React", "https://react.dev/learn");
    if (/next/i.test(text)) links.set("Next.js", "https://nextjs.org/docs");
    if (/nestjs|nest/i.test(text)) links.set("NestJS", "https://docs.nestjs.com/");
    if (/express/i.test(text)) links.set("Express", "https://expressjs.com/");
    if (/postgres/i.test(text)) links.set("PostgreSQL", "https://www.postgresql.org/docs/");
    if (/prisma/i.test(text)) links.set("Prisma", "https://www.prisma.io/docs");
    if (flags.hasPython) {
      links.set("Python", "https://docs.python.org/3/");
      links.set("FastAPI", "https://fastapi.tiangolo.com/");
    }
    if (flags.hasLaravel) links.set("Laravel", "https://laravel.com/docs");
    if (flags.hasRedis) links.set("Redis", "https://redis.io/docs/latest/");
    if (flags.hasQdrant) links.set("Qdrant", "https://qdrant.tech/documentation/");
    if (flags.hasMinio) links.set("MinIO", "https://min.io/docs/minio/container/index.html");
    return Array.from(links.entries()).map(([name, url]) => `- [${name}](${url})`);
  }

  private renderReadmeDockerRows(flags: {
    hasPython: boolean;
    hasLaravel: boolean;
    hasRedis: boolean;
    hasQdrant: boolean;
    hasMinio: boolean;
  }): string[] {
    const rows = [
      "| PostgreSQL | Base de datos principal del MVP | `5432` | volumen Docker `postgres_data` |"
    ];
    if (flags.hasRedis) rows.push("| Redis | Cache, sesiones o cola de trabajos | `6379` | sin persistencia critica por defecto |");
    if (flags.hasQdrant) rows.push("| Qdrant | Base vectorial para busqueda semantica/RAG | `6333` | volumen Docker `qdrant_data` |");
    if (flags.hasMinio) rows.push("| MinIO | Almacenamiento local compatible con S3 | `9000` / `9001` | volumen Docker `minio_data` |");
    if (flags.hasPython) rows.push("| AI Service | Servicio Python/FastAPI para agentes o IA | `8003` | sin volumen por defecto |");
    if (flags.hasLaravel) rows.push("| App Laravel | Backend monolitico PHP | `8000` | usa PostgreSQL |");
    return rows;
  }

  private renderReadmeCommandBlocks(flags: { hasPython: boolean; hasLaravel: boolean; hasNode: boolean }): string[] {
    if (flags.hasLaravel) {
      return [
        "```bash",
        "# Dependencias PHP",
        "composer install",
        "",
        "# Base de datos",
        "php artisan migrate --seed",
        "",
        "# Desarrollo",
        "php artisan serve",
        "",
        "# Calidad",
        "php artisan test",
        "vendor/bin/pint",
        "```"
      ];
    }

    const lines = [
      "```bash",
      "# Dependencias",
      flags.hasNode ? "npm install" : "# Instala dependencias segun el stack generado",
      "",
      "# Base de datos",
      flags.hasNode ? "npm run db:migrate" : "# Ejecuta las migraciones del framework generado",
      flags.hasNode ? "npm run db:seed --if-present" : "",
      "",
      "# Desarrollo",
      flags.hasNode ? "npm run dev" : "# Arranca el servidor de desarrollo",
      "",
      "# Calidad",
      flags.hasNode ? "npm run lint --if-present" : "",
      flags.hasNode ? "npm test" : "",
      flags.hasNode ? "npm run build" : ""
    ].filter(Boolean);
    if (flags.hasPython) {
      lines.push(
        "",
        "# Servicio de IA / Python",
        "cd apps/ai-service",
        "pip install -r requirements.txt",
        "python -m pytest",
        "ruff check .",
        "cd ../.."
      );
    }
    lines.push("```");
    return lines;
  }

  private renderReadmeDeploymentLines(flags: { hasPython: boolean; hasLaravel: boolean }): string[] {
    return [
      "1. Crea un repositorio GitHub y sube el contenido del ZIP.",
      "2. Configura variables de entorno de produccion: `DATABASE_URL`, secretos JWT y URLs publicas.",
      flags.hasLaravel
        ? "3. Despliega la app en Railway/Render como servicio PHP o en VPS con Docker Compose."
        : "3. Despliega `apps/api` como servicio backend y `apps/web` como frontend estatico/Vite.",
      flags.hasPython
        ? "4. Despliega `apps/ai-service` como servicio Python separado y configura `AI_SERVICE_URL` en la API."
        : "4. Ejecuta migraciones de produccion antes de abrir el servicio al publico.",
      "5. Revisa `docs/deployment/deployment-guide.md` para el despliegue detallado."
    ];
  }

  private renderReadmeCostLines(flags: {
    hasPython: boolean;
    hasRedis: boolean;
    hasQdrant: boolean;
    hasMinio: boolean;
  }): string[] {
    return [
      "- **Local:** 0 EUR/mes usando Docker Desktop.",
      "- **MVP en hosting gestionado:** 5-25 EUR/mes para API + frontend + PostgreSQL pequeno.",
      flags.hasPython ? "- **Servicio de IA:** 0 EUR/mes si usas modelos locales; coste variable si conectas OpenAI/Groq/Anthropic." : "- **IA externa:** no incluida por defecto; coste 0 EUR hasta configurar un proveedor.",
      flags.hasRedis ? "- **Redis gestionado:** 0-10 EUR/mes en planes pequenos." : "- **Redis:** no requerido por defecto.",
      flags.hasQdrant ? "- **Qdrant/vector DB:** local gratis; gestionado desde planes gratuitos o hobby segun proveedor." : "- **Vector DB:** no requerida por defecto.",
      flags.hasMinio ? "- **Almacenamiento S3/MinIO:** local gratis; S3 compatible suele empezar en centimos/GB." : "- **Storage externo:** no requerido por defecto.",
      "- **Produccion inicial razonable:** 20-50 EUR/mes cuando necesites dominio, backups y recursos dedicados."
    ];
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
      `│  │  ${(stack[0] ?? "React").slice(0, 8).padEnd(8)}  │──►│  ${(stack[1] ?? "NestJS").slice(0, 8).padEnd(8)}  │──►│  PostgreSQL  │  │`,
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
    const slug = slugify(projectName);
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
    const slug = slugify(projectName);
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

  private renderProductDoc(projectName: string, summary: Record<string, unknown>, path: string): string {
    const description = String(summary.description ?? "Describe aqui la idea validada durante el intake.");
    const targetUsers = String(summary.target_users ?? "Usuarios objetivo definidos durante la fase de descubrimiento.");
    const modules = Array.isArray(summary.modules) ? (summary.modules as string[]) : [];
    const title = path.split("/").pop()?.replace(".md", "").replace(/-/g, " ") ?? "producto";

    return [
      `# ${title} - ${projectName}`,
      "",
      "## Idea base",
      "",
      description,
      "",
      "## Publico objetivo",
      "",
      targetUsers,
      "",
      "## Alcance MVP",
      "",
      ...(modules.length > 0 ? modules.slice(0, 6).map(m => `- ${m}`) : ["- Definir el primer flujo de valor antes de ampliar funcionalidades."]),
      "",
      "## Validacion recomendada",
      "",
      "- Confirmar que el problema existe con 3-5 usuarios reales.",
      "- Medir una accion principal del MVP, no todas las funcionalidades.",
      "- Registrar riesgos y supuestos en `sdd/technology-decisions.md`.",
    ].join("\n");
  }

  private renderDevelopmentDoc(projectName: string, stack: string[], path: string): string {
    const isWindows = path.endsWith("windows-setup.md");
    const isLinux = path.endsWith("linux-setup.md");
    const isMac = path.endsWith("macos-setup.md");
    const isEnvironment = path.endsWith("environment-setup.md") || path.endsWith("environment.md");
    const title = path.split("/").pop()?.replace(".md", "").replace(/-/g, " ") ?? "desarrollo";
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));
    const hasPhp = stack.some(s => /php|laravel/i.test(s));
    const installCommands = isWindows
      ? this.readmeWindowsInstallCommands({ hasPython, hasPhp })
      : isMac
        ? this.readmeMacInstallCommands({ hasPython, hasPhp })
        : this.readmeLinuxInstallCommands({ hasPython, hasPhp });
    const sections = isEnvironment
      ? [
          { heading: "Windows (PowerShell)", language: "powershell", commands: this.readmeWindowsInstallCommands({ hasPython, hasPhp }) },
          { heading: "Linux (Ubuntu/Debian)", language: "bash", commands: this.readmeLinuxInstallCommands({ hasPython, hasPhp }) },
          { heading: "macOS", language: "bash", commands: this.readmeMacInstallCommands({ hasPython, hasPhp }) },
        ]
      : [
          {
            heading: isWindows ? "Windows (PowerShell)" : isMac ? "macOS" : isLinux ? "Linux (Ubuntu/Debian)" : "Sistema operativo",
            language: isWindows ? "powershell" : "bash",
            commands: installCommands
          }
        ];

    return [
      `# ${title} - ${projectName}`,
      "",
      "## Objetivo",
      "",
      "Instalar las herramientas necesarias, verificar versiones y levantar el proyecto de forma reproducible.",
      "",
      "## Herramientas requeridas",
      "",
      "- Git 2.x",
      "- Docker Desktop o Docker Engine con Compose",
      "- Node.js 20 LTS",
      ...(hasPython ? ["- Python 3.12 con `venv` y `pip`"] : []),
      ...(hasPhp ? ["- PHP 8.2+ y Composer 2.x"] : []),
      "",
      "## Instalacion de herramientas",
      "",
      ...sections.flatMap(section => [
        `### ${section.heading}`,
        "",
        `\`\`\`${section.language}`,
        ...section.commands,
        "```",
        ""
      ]),
      "## Verificar versiones",
      "",
      "```bash",
      "git --version",
      "node --version",
      "npm --version",
      "docker --version",
      "docker compose version",
      ...(hasPython ? ["python --version", "pip --version"] : []),
      ...(hasPhp ? ["php --version", "composer --version"] : []),
      "```",
      "",
      "## Levantar el proyecto",
      "",
      "```bash",
      "cp .env.example .env",
      "docker compose up -d",
      "npm install",
      "npm run db:migrate",
      "npm run db:seed --if-present",
      "npm run dev",
      "```",
      "",
      "## Validar instalacion",
      "",
      "```bash",
      "docker compose ps",
      "npm test",
      "npm run lint --if-present",
      "npm run build",
      "```",
      ...(hasPython ? [
        "",
        "## Servicio Python / IA",
        "",
        "```bash",
        "cd apps/ai-service",
        "python -m venv .venv",
        "# Linux/macOS: source .venv/bin/activate",
        "# Windows: .\\.venv\\Scripts\\Activate.ps1",
        "pip install -r requirements.txt",
        "python -m pytest",
        "cd ../..",
        "```"
      ] : []),
      "",
      "## Checklist",
      "",
      "- [ ] Git, Node, Docker y Docker Compose responden en terminal.",
      ...(hasPython ? ["- [ ] Python y pip responden en terminal."] : []),
      ...(hasPhp ? ["- [ ] PHP y Composer responden en terminal."] : []),
      "- [ ] Variables `.env` configuradas.",
      "- [ ] Base de datos levantada.",
      "- [ ] Migraciones aplicadas.",
      "- [ ] Tests iniciales ejecutados.",
    ].join("\n");
  }

  private readmeWindowsInstallCommands(flags: { hasPython: boolean; hasPhp: boolean }): string[] {
    return [
      "winget install --id Git.Git -e",
      "winget install --id OpenJS.NodeJS.LTS -e",
      "winget install --id Docker.DockerDesktop -e",
      ...(flags.hasPython ? ["winget install --id Python.Python.3.12 -e"] : []),
      ...(flags.hasPhp ? ["winget install --id PHP.PHP -e", "winget install --id Composer.Composer -e"] : []),
      "# Reinicia PowerShell despues de instalar Docker Desktop.",
    ];
  }

  private readmeLinuxInstallCommands(flags: { hasPython: boolean; hasPhp: boolean }): string[] {
    return [
      "sudo apt update",
      "sudo apt install -y git curl ca-certificates gnupg",
      "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -",
      "sudo apt install -y nodejs docker.io docker-compose-plugin",
      "sudo usermod -aG docker $USER",
      ...(flags.hasPython ? ["sudo apt install -y python3 python3-venv python3-pip"] : []),
      ...(flags.hasPhp ? ["sudo apt install -y php-cli php-mbstring php-xml php-curl unzip", "curl -sS https://getcomposer.org/installer | php", "sudo mv composer.phar /usr/local/bin/composer"] : []),
      "# Cierra sesion y vuelve a entrar para aplicar el grupo docker.",
    ];
  }

  private readmeMacInstallCommands(flags: { hasPython: boolean; hasPhp: boolean }): string[] {
    return [
      "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
      "brew install git node",
      "brew install --cask docker",
      ...(flags.hasPython ? ["brew install python@3.12"] : []),
      ...(flags.hasPhp ? ["brew install php composer"] : []),
      "# Abre Docker Desktop una vez antes de ejecutar docker compose.",
    ];
  }

  private renderApiDoc(projectName: string, summary: Record<string, unknown>, modules: string[], path: string): string {
    const endpoints = Array.isArray(summary.api_endpoints)
      ? (summary.api_endpoints as Array<Record<string, unknown>>)
      : [];
    const title = path.split("/").pop()?.replace(".md", "").replace(/-/g, " ") ?? "api";
    const lines = [`# ${title} - ${projectName}`, ""];

    lines.push("## Convenciones", "", "- Base URL local: `http://localhost:3000/api`", "- Formato: JSON", "- Errores: `{ message, code, details? }`", "");
    lines.push("## Endpoints", "");
    if (endpoints.length > 0) {
      lines.push("| Metodo | Ruta | Auth | Descripcion |", "| --- | --- | --- | --- |");
      for (const e of endpoints) {
        lines.push(`| ${e.method ?? "GET"} | \`${e.path ?? "/api"}\` | ${e.auth_required ? "Si" : "No"} | ${e.description ?? ""} |`);
      }
    } else {
      for (const mod of modules.slice(0, 6)) {
        const slug = slugify(mod);
        lines.push(`- \`GET /api/${slug}\`: listar ${mod}.`, `- \`POST /api/${slug}\`: crear ${mod}.`);
      }
    }
    lines.push("", "## Autenticacion", "", "Usa Bearer token para endpoints privados. Nunca guardes tokens en el repositorio.");
    return lines.join("\n");
  }

  private renderAiDoc(projectName: string, stack: string[], path: string): string {
    const hasVector = stack.some(s => /qdrant|pgvector|chroma|weaviate/i.test(s));
    const title = path.split("/").pop()?.replace(".md", "").replace(/-/g, " ") ?? "ia";
    return [
      `# ${title} - ${projectName}`,
      "",
      "## Criterio de uso",
      "",
      "- IA online: util para MVPs rapidos, menor operacion, coste variable por uso.",
      "- IA local: util si hay privacidad o coste predecible, exige hardware y mantenimiento.",
      "- RAG: solo si el usuario necesita consultar documentos o conocimiento cambiante.",
      "- Agentes: solo si hay procesos con varios pasos, herramientas o supervision humana.",
      "",
      "## Estado recomendado para este proyecto",
      "",
      hasVector
        ? "El stack incluye busqueda vectorial. Mantener un pipeline explicito: ingesta, chunking, embeddings, indexacion, retrieval y evaluacion."
        : "No anadas base vectorial hasta tener una necesidad real de busqueda semantica o documentos.",
      "",
      "## Evaluacion",
      "",
      "- Medir calidad con preguntas de prueba.",
      "- Registrar coste aproximado por usuario.",
      "- Probar latencia p95 antes de produccion.",
    ].join("\n");
  }

  private renderDeploymentDoc(projectName: string, stack: string[], path: string): string {
    const title = path.split("/").pop()?.replace(".md", "").replace(/-/g, " ") ?? "despliegue";
    const hasNext = stack.some(s => /next/i.test(s));
    return [
      `# ${title} - ${projectName}`,
      "",
      "## Local con Docker",
      "",
      "```bash",
      "cp .env.example .env",
      "docker compose up -d --build",
      "docker compose logs -f",
      "```",
      "",
      "## Primer despliegue recomendado",
      "",
      hasNext ? "- Frontend/fullstack: Vercel o Railway." : "- Frontend: Netlify/Vercel. API: Railway/Render/Fly.io.",
      "- Base de datos: Supabase, Railway PostgreSQL o Postgres en VPS.",
      "- VPS: usar nginx/Caddy/Traefik como proxy inverso.",
      "",
      "## Costes orientativos",
      "",
      "- Desarrollo local: 0 EUR/mes.",
      "- Staging pequeno: 5-15 EUR/mes.",
      "- Produccion inicial: 20-50 EUR/mes.",
      "- IA/API externas: coste variable por uso; documentar proveedor y limites.",
    ].join("\n");
  }

  private renderArchitectureDecisions(projectName: string, stack: string[], modules: string[]): string {
    return [
      `# Decisiones de arquitectura - ${projectName}`,
      "",
      "## Stack aprobado",
      "",
      ...(stack.length > 0 ? stack.map(s => `- ${s}`) : ["- Definir stack antes de implementar."]),
      "",
      "## Modulos",
      "",
      ...(modules.length > 0 ? modules.map(m => `- ${m}`) : ["- Definir modulos desde requisitos."]),
      "",
      "## Reglas",
      "",
      "- No cambiar framework, ORM o base de datos sin ADR.",
      "- No crear microservicios si el proyecto fue definido como monolito modular.",
      "- No anadir RAG si no hay busqueda semantica real.",
    ].join("\n");
  }

  private renderFunctionalRequirements(projectName: string, requirements: Array<Record<string, unknown>>, modules: string[]): string {
    const lines = [`# Requisitos funcionales - ${projectName}`, ""];
    if (requirements.length > 0) {
      for (const r of requirements) lines.push(`## ${r.id ?? ""} ${r.title ?? "Requisito"}`, "", String(r.description ?? ""), "");
    } else {
      for (const mod of modules) lines.push(`## ${mod}`, "", `- El usuario puede gestionar ${mod.toLowerCase()} con validacion y errores claros.`, "");
    }
    return lines.join("\n");
  }

  private renderFeatureSpec(projectName: string, modules: string[]): string {
    const feature = modules[0] ?? "Modulo principal";
    return [
      `# Feature 001 - ${feature}`,
      "",
      `Proyecto: ${projectName}`,
      "",
      "## Objetivo",
      "",
      `Implementar el flujo principal de ${feature} con API, validaciones, UI basica y tests.`,
      "",
      "## Criterios de aceptacion",
      "",
      "- [ ] El usuario puede crear, consultar, actualizar y eliminar registros si aplica.",
      "- [ ] Los errores se muestran con mensajes accionables.",
      "- [ ] Hay tests unitarios o de integracion para el flujo principal.",
      "- [ ] README y SDD quedan actualizados.",
    ].join("\n");
  }

  private renderReleasePlan(projectName: string, modules: string[]): string {
    return [
      `# Release plan - ${projectName}`,
      "",
      "## v0.1 MVP local",
      "",
      "- Entorno Docker funcionando.",
      "- Autenticacion y modulo principal.",
      "- README y SDD completos.",
      "",
      "## v0.2 Beta",
      "",
      ...(modules.slice(0, 4).map(m => `- Completar ${m}.`)),
      "",
      "## v1.0 Primera version publica",
      "",
      "- CI verde.",
      "- Despliegue documentado.",
      "- Seguridad y backups revisados.",
    ].join("\n");
  }

  private renderInitialTasks(projectName: string, modules: string[]): string {
    return [
      `# Initial tasks - ${projectName}`,
      "",
      "- [ ] Copiar `.env.example` a `.env`.",
      "- [ ] Levantar Docker Compose.",
      "- [ ] Ejecutar migraciones y seeds.",
      "- [ ] Revisar `sdd/specifications/feature-001-main-module.md`.",
      ...(modules.slice(0, 5).map(m => `- [ ] Implementar/revisar ${m}.`)),
    ].join("\n");
  }

  private renderTaskStatus(projectName: string, modules: string[]): string {
    return [
      `# Task status - ${projectName}`,
      "",
      "| Tarea | Estado | Notas |",
      "| --- | --- | --- |",
      "| Setup local | Pendiente | Ver `docs/development/environment-setup.md` |",
      "| CI | Pendiente | Ver `.github/workflows/ci.yml` |",
      ...modules.slice(0, 6).map(m => `| ${m} | Pendiente | Crear issue desde backlog |`),
    ].join("\n");
  }

  private renderSetupDoc(projectName: string, stack: string[], path: string): string {
    if (path.endsWith("required-tools.md")) return this.renderRequiredToolsDoc(projectName, stack);
    return this.renderDevelopmentDoc(projectName, stack, path);
  }

  private renderRequiredToolsDoc(projectName: string, stack: string[]): string {
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));
    const hasPhp = stack.some(s => /php|laravel/i.test(s));
    return [
      `# Herramientas requeridas - ${projectName}`,
      "",
      "| Herramienta | Version recomendada | Uso | Documentacion |",
      "| --- | --- | --- | --- |",
      "| Git | 2.x | Control de versiones | https://git-scm.com/doc |",
      "| Node.js | 20 LTS | Frontend, backend Node y scripts npm | https://nodejs.org/en/docs |",
      "| Docker | 24+ | Servicios locales reproducibles | https://docs.docker.com/ |",
      "| Docker Compose | v2 | PostgreSQL, Redis, MinIO y otros servicios | https://docs.docker.com/compose/ |",
      ...(hasPython ? ["| Python | 3.12+ | Servicio FastAPI/IA y tooling Python | https://docs.python.org/3/ |"] : []),
      ...(hasPhp ? ["| PHP | 8.2+ | Backend Laravel/PHP | https://www.php.net/docs.php |", "| Composer | 2.x | Dependencias PHP | https://getcomposer.org/doc/ |"] : []),
      "",
      "## Guias por sistema operativo",
      "",
      "- `sdd/setup/windows.md`",
      "- `sdd/setup/linux.md`",
      "- `sdd/setup/macos.md`",
      "- `docs/development/environment-setup.md`",
    ].join("\n");
  }

  private renderDockerfile(path: string): string {
    if (path.endsWith("ai-service.Dockerfile")) {
      return ["FROM python:3.12-slim", "WORKDIR /app", "COPY apps/ai-service/requirements.txt ./requirements.txt", "RUN pip install --no-cache-dir -r requirements.txt", "COPY apps/ai-service ./", "CMD [\"python\", \"-m\", \"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8003\"]"].join("\n");
    }
    if (path.endsWith("nginx.Dockerfile")) return ["FROM nginx:1.27-alpine", "COPY infrastructure/nginx/default.conf /etc/nginx/conf.d/default.conf"].join("\n");
    const isBackend = path.endsWith("backend.Dockerfile");
    const workdir = isBackend ? "/app/apps/api" : "/app/apps/web";
    return ["FROM node:20-alpine", "WORKDIR /app", "COPY package*.json ./", "RUN npm ci", "COPY . .", `WORKDIR ${workdir}`, "RUN npm run build", isBackend ? "CMD [\"npm\", \"run\", \"start\"]" : "CMD [\"npm\", \"run\", \"preview\", \"--\", \"--host\", \"0.0.0.0\"]"].join("\n");
  }

  private renderNginxConf(stack: string[]): string {
    const hasAi = stack.some(s => /fastapi|python|ai|langchain/i.test(s));
    return [
      "server {",
      "  listen 80;",
      "  server_name _;",
      "  location / { proxy_pass http://frontend:5173; }",
      "  location /api/ { proxy_pass http://backend:3000/api/; }",
      ...(hasAi ? ["  location /ai/ { proxy_pass http://ai-service:8003/; }"] : []),
      "}",
    ].join("\n");
  }

  private renderInfrastructureScript(path: string): string {
    const name = path.split("/").pop() ?? "script.sh";
    const command = name === "stop-dev.sh"
      ? "docker compose down"
      : name === "reset-db.sh"
        ? "docker compose down -v && docker compose up -d && npm run db:migrate"
        : name === "test.sh"
          ? "npm test && npm run lint"
          : name === "deploy.sh"
            ? "docker compose -f docker-compose.yml up -d --build"
            : "docker compose up -d";
    return ["#!/usr/bin/env bash", "set -euo pipefail", "", command, ""].join("\n");
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
      target_users: record.target_users,
      api_endpoints: record.api_endpoints,
      data_entities: record.data_entities,
      data_model: record.data_model
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
        lines.push(`- **${r.from_entity} -> ${r.to_entity}** (${r.type})${cascade}${optional}`);
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

  private renderOpenSpecMd(projectName: string, summary: Record<string, unknown>): string {
    const desc = (summary.description as string) || "";
    const modules = Array.isArray(summary.modules) ? (summary.modules as string[]) : [];
    const constraints = (typeof summary.constraints === "object" && summary.constraints)
      ? (summary.constraints as Record<string, unknown>) : {};
    const stack = Array.isArray(constraints.stack) ? (constraints.stack as string[]) : [];
    const reqs = Array.isArray(summary.requirements)
      ? (summary.requirements as Array<Record<string, unknown>>) : [];
    const apiEndpoints = Array.isArray(summary.api_endpoints)
      ? (summary.api_endpoints as Array<Record<string, unknown>>) : [];

    const lines = [
      `# OpenSpec — ${projectName}`,
      "",
      "> Resumen del documento de especificacion tecnica completo.",
      "> El JSON original se encuentra en `sdd/specifications/openspec.json`.",
      "",
    ];

    if (desc) lines.push(`## Descripcion`, "", desc, "");

    if (stack.length > 0) {
      lines.push("## Stack tecnologico", "");
      lines.push(...stack.map(s => `- ${s}`), "");
    }

    if (modules.length > 0) {
      lines.push("## Modulos del sistema", "");
      lines.push(...modules.map(m => `- **${m}**`), "");
    }

    if (reqs.length > 0) {
      lines.push("## Requisitos funcionales principales", "");
      for (const r of reqs.slice(0, 8)) {
        lines.push(`- **${r.id ?? ""}** ${r.title ?? ""}`);
      }
      if (reqs.length > 8) lines.push(`- _...y ${reqs.length - 8} más (ver openspec.json)_`);
      lines.push("");
    }

    if (apiEndpoints.length > 0) {
      lines.push("## Endpoints API", "");
      lines.push("| Metodo | Ruta | Descripcion |", "| --- | --- | --- |");
      for (const ep of apiEndpoints.slice(0, 15)) {
        const method = ((ep.method as string) ?? "GET").toUpperCase();
        const path = (ep.path as string) ?? "";
        const epDesc = (ep.description as string) ?? "";
        lines.push(`| \`${method}\` | \`${path}\` | ${epDesc} |`);
      }
      if (apiEndpoints.length > 15) lines.push(``, `_...y ${apiEndpoints.length - 15} endpoints más (ver openspec.json)_`);
      lines.push("");
    }

    lines.push(
      "---",
      "",
      "_Para editar la especificacion, modifica `openspec.json` y regenera los artefactos._"
    );

    return lines.join("\n");
  }

  private renderResumeSession(projectName: string, stack: string[], modules: string[]): string {
    return [
      `# Prompt: Reanudar sesion — ${projectName}`,
      "",
      "> Copia y pega este bloque al inicio de una nueva sesion con Claude Code, Copilot Chat o ChatGPT.",
      "",
      "---",
      "",
      "```",
      `Estoy trabajando en el proyecto **${projectName}**.`,
      "",
      `Stack: ${stack.length > 0 ? stack.slice(0, 5).join(", ") : "React + NestJS + PostgreSQL"}`,
      `Modulos: ${modules.length > 0 ? modules.slice(0, 5).join(", ") : "(ver sdd/requirements/requirements.md)"}`,
      "",
      "Documentos de contexto que debes leer antes de continuar:",
      "1. sdd/constitution.md — decisiones de arquitectura y principios",
      "2. sdd/requirements/requirements.md — requisitos funcionales",
      "3. sdd/specifications/openspec.md — resumen tecnico del proyecto",
      "",
      "Mi objetivo en esta sesion es: [DESCRIBE TU TAREA AQUI]",
      "```",
      "",
      "---",
      "",
      "## Preguntas utiles para orientar la IA",
      "",
      "- ¿Qué ficheros debo modificar para implementar [funcionalidad]?",
      "- ¿Cómo encaja [modulo] con el resto de la arquitectura?",
      "- Revisa `[fichero]` y sugiere mejoras manteniendo las convenciones del proyecto.",
      "- Genera los tests unitarios para `[fichero]` siguiendo las convenciones del proyecto.",
    ].join("\n");
  }

  private renderAddFeaturePrompt(projectName: string, stack: string[], modules: string[]): string {
    return [
      `# Prompt: Añadir funcionalidad — ${projectName}`,
      "",
      "> Usa este template cuando quieras añadir una nueva feature con ayuda de IA.",
      "",
      "---",
      "",
      "```",
      `Proyecto: **${projectName}**`,
      `Stack: ${stack.length > 0 ? stack.slice(0, 4).join(", ") : "React + NestJS + PostgreSQL"}`,
      `Modulos existentes: ${modules.length > 0 ? modules.slice(0, 4).join(", ") : "(ver requirements.md)"}`,
      "",
      "Quiero añadir la siguiente funcionalidad:",
      "[DESCRIBE LA FUNCIONALIDAD]",
      "",
      "Restricciones:",
      "- Mantener la arquitectura por modulos definida en sdd/constitution.md",
      "- TypeScript estricto, sin any implícito",
      "- Seguir las convenciones de commits (feat:, fix:, etc.)",
      "- Añadir tests unitarios para la nueva logica",
      "",
      "¿Qué ficheros necesito crear o modificar? Dame una lista con los cambios necesarios",
      "en orden de implementacion, empezando por el modelo de datos.",
      "```",
      "",
      "---",
      "",
      "## Checklist pre-implementacion",
      "",
      "- [ ] ¿Esta funcionalidad ya existe en otro modulo?",
      "- [ ] ¿Requiere cambios en el esquema de base de datos?",
      "- [ ] ¿Afecta a la autenticacion o permisos?",
      "- [ ] ¿Hay user stories relacionadas en sdd/requirements/user-stories.md?",
    ].join("\n");
  }

  private renderFixBugPrompt(projectName: string, stack: string[]): string {
    return [
      `# Prompt: Resolver bug — ${projectName}`,
      "",
      "> Usa este template cuando encuentres un bug y quieras resolverlo con ayuda de IA.",
      "",
      "---",
      "",
      "```",
      `Proyecto: **${projectName}**`,
      `Stack: ${stack.length > 0 ? stack.slice(0, 4).join(", ") : "React + NestJS + PostgreSQL"}`,
      "",
      "Descripcion del bug:",
      "[DESCRIBE EL COMPORTAMIENTO INCORRECTO]",
      "",
      "Comportamiento esperado:",
      "[DESCRIBE LO QUE DEBERIA OCURRIR]",
      "",
      "Pasos para reproducir:",
      "1. [PASO 1]",
      "2. [PASO 2]",
      "",
      "Error en consola / logs:",
      "```",
      "[PEGA EL ERROR AQUI]",
      "```",
      "",
      "Ficheros que creo que estan implicados:",
      "[LISTA DE FICHEROS O MODULOS RELACIONADOS]",
      "```",
      "",
      "---",
      "",
      "## Debugging rapido",
      "",
      "```bash",
      "# Ver logs del backend",
      "npm run start:dev 2>&1 | grep -i error",
      "",
      "# Tests del modulo afectado",
      "npm test -- --testPathPattern=[modulo]",
      "",
      "# TypeScript errors",
      "npx tsc --noEmit",
      "```",
    ].join("\n");
  }

  private renderEnvironmentSetup(projectName: string, stack: string[]): string {
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));
    const hasNode = !stack.every(s => /python|ruby|go/i.test(s));

    const lines = [
      `# Configuracion del entorno — ${projectName}`,
      "",
      "> Sigue estos pasos en orden. Tiempo estimado: 15-30 minutos.",
      "",
      "## Requisitos previos",
      "",
      "| Herramienta | Version minima | Verificar |",
      "| --- | --- | --- |",
      ...(hasNode ? ["| Node.js | 20.x | `node --version` |"] : []),
      ...(hasPython ? ["| Python | 3.11+ | `python --version` |"] : []),
      "| Docker Desktop | 4.x | `docker --version` |",
      "| Git | 2.40+ | `git --version` |",
      "",
      "## Linux / macOS",
      "",
      "```bash",
      "# 1. Clonar el repositorio",
      `git clone <repo-url> ${slugify(projectName)}`,
      `cd ${slugify(projectName)}`,
      "",
      "# 2. Copiar variables de entorno",
      "cp .env.example .env",
      "# Edita .env con tus valores reales",
      "",
      "# 3. Levantar servicios (base de datos, etc.)",
      "docker compose up -d",
      "",
      ...(hasNode ? [
        "# 4. Instalar dependencias",
        "npm install",
        "",
        "# 5. Ejecutar migraciones",
        "npm run db:migrate",
        "",
        "# 6. Arrancar en modo desarrollo",
        "npm run dev",
        "",
      ] : []),
      ...(hasPython ? [
        "# Instalar dependencias Python",
        "python -m venv .venv && source .venv/bin/activate",
        "pip install -r requirements.txt",
        "",
      ] : []),
      "# Verificar que todo funciona",
      "curl http://localhost:3000/health",
      "```",
      "",
      "## Windows (PowerShell)",
      "",
      "```powershell",
      `git clone <repo-url> ${slugify(projectName)}`,
      `cd ${slugify(projectName)}`,
      "Copy-Item .env.example .env",
      "docker compose up -d",
      ...(hasNode ? ["npm install", "npm run db:migrate", "npm run dev"] : []),
      "```",
      "",
      "## Puertos por defecto",
      "",
      "| Servicio | Puerto |",
      "| --- | --- |",
      "| Frontend | http://localhost:5173 |",
      "| API | http://localhost:3000 |",
      "| PostgreSQL | localhost:5432 |",
      ...(stack.some(s => /redis/i.test(s)) ? ["| Redis | localhost:6379 |"] : []),
      ...(hasPython ? ["| AI Service | http://localhost:8003 |"] : []),
      "",
      "## Solucionar problemas comunes",
      "",
      "**Puerto ya en uso**: `docker compose down && docker compose up -d`",
      "",
      "**Error de migracion**: verifica que el contenedor de PostgreSQL este healthy: `docker compose ps`",
      "",
      "**Modulos no encontrados**: borra `node_modules` y ejecuta `npm install` de nuevo.",
    ];

    return lines.join("\n");
  }

  private renderTechDecisions(projectName: string, stack: string[]): string {
    const lines = [
      `# Decisiones tecnologicas — ${projectName}`,
      "",
      "> Tabla de decisiones de arquitectura y tecnología.",
      "> Actualizar cuando el equipo adopte o descarte una tecnología.",
      "",
      "## Stack adoptado",
      "",
      "| Capa | Tecnologia | Alternativas consideradas | Motivo de eleccion |",
      "| --- | --- | --- | --- |",
    ];

    if (stack.length > 0) {
      const layers = ["Frontend", "Backend", "Base de datos", "Infraestructura", "Testing"];
      stack.slice(0, 5).forEach((tech, i) => {
        lines.push(`| ${layers[i] ?? "Otro"} | ${tech} | _ver ADR_ | Equilibrio entre curva de aprendizaje y productividad |`);
      });
    } else {
      lines.push(
        "| Frontend | React 19 + Vite | Angular, Vue | Ecosistema más demandado en el mercado |",
        "| Backend | NestJS + TypeScript | Express, Fastify | Arquitectura modular + DI + decorators |",
        "| Base de datos | PostgreSQL | MySQL, MongoDB | ACID, JSON nativo, extensiones |",
        "| ORM | Prisma | TypeORM, Drizzle | Type-safety, migraciones, DX superior |",
        "| Infraestructura | Docker Compose | K8s | Suficiente para MVP, menor complejidad |",
      );
    }

    lines.push(
      "",
      "## Deuda tecnica aceptada",
      "",
      "| Decisión | Deuda generada | Plan de revision |",
      "| --- | --- | --- |",
      "| Monolito inicial | Refactor a microservicios si escala | >1000 usuarios activos |",
      "| Sin cache (Redis) | Posibles bottlenecks en queries frecuentes | Sprint 3 |",
      "| Sin CDN | Latencia alta para usuarios globales | Post-validacion MVP |",
      "",
      "## Principios no negociables",
      "",
      "- API keys y secretos **nunca** en el codigo fuente",
      "- TypeScript estricto (`strict: true`) — sin `any` implícito",
      "- Tests antes de refactorizar",
      "- Migraciones de DB con herramienta del ORM, nunca SQL manual en produccion",
    );

    return lines.join("\n");
  }

  private renderNFR(projectName: string, nonFunctional: Array<Record<string, unknown>>): string {
    const lines = [
      `# Requisitos no funcionales — ${projectName}`,
      "",
      "> Objetivos medibles de calidad del sistema.",
      "",
    ];

    if (nonFunctional.length > 0) {
      lines.push("## Listado de requisitos", "");
      lines.push("| ID | Requisito | Objetivo |", "| --- | --- | --- |");
      for (const r of nonFunctional) {
        lines.push(`| ${r.id ?? "NFR"} | ${r.title ?? ""} | ${r.description ?? ""} |`);
      }
      lines.push("");
    }

    lines.push(
      "## Rendimiento",
      "",
      "| Metrica | Objetivo | Herramienta de medicion |",
      "| --- | --- | --- |",
      "| Tiempo de respuesta API (p95) | < 200 ms | Prometheus + Grafana |",
      "| Time to First Byte (TTFB) | < 500 ms | Lighthouse |",
      "| Disponibilidad | > 99.5% | Uptime Robot |",
      "",
      "## Seguridad",
      "",
      "- Autenticacion mediante JWT con rotacion de refresh token",
      "- Passwords hasheadas con bcrypt (salt rounds >= 10)",
      "- Rate limiting en endpoints de autenticacion",
      "- Headers de seguridad: HSTS, CSP, X-Frame-Options",
      "- Variables secretas solo en `.env`, nunca en el codigo fuente",
      "",
      "## Escalabilidad",
      "",
      "- La API debe soportar escala horizontal (stateless, sin sesiones en memoria)",
      "- Base de datos con connection pooling configurado",
      "- Uploads de ficheros a almacenamiento externo (S3/MinIO), no al servidor",
      "",
      "## Observabilidad",
      "",
      "- Logs estructurados (JSON) con nivel configurable por entorno",
      "- Health check endpoint: `GET /health`",
      "- Errores de produccion enviados a Sentry o similar",
    );

    return lines.join("\n");
  }

  private renderAcceptanceCriteria(projectName: string, modules: string[]): string {
    const lines = [
      `# Criterios de aceptacion — ${projectName}`,
      "",
      "> Una feature se considera **Done** cuando cumple TODOS los criterios de su modulo.",
      "",
    ];

    const defaultModules = modules.length > 0 ? modules : ["Autenticacion", "CRUD Principal", "API REST"];
    for (const mod of defaultModules.slice(0, 8)) {
      lines.push(
        `## ${mod}`,
        "",
        `- [ ] Los endpoints de ${mod} responden con el codigo HTTP correcto`,
        `- [ ] Los datos de entrada se validan con DTOs/schemas`,
        `- [ ] Los errores devuelven mensajes descriptivos (no stack traces)`,
        `- [ ] Hay al menos un test unitario por metodo de servicio`,
        `- [ ] La funcionalidad esta documentada en \`docs/api/api-reference.md\``,
        "",
      );
    }

    lines.push(
      "## Criterios globales (todos los modulos)",
      "",
      "- [ ] Sin errores de TypeScript: `npx tsc --noEmit`",
      "- [ ] Todos los tests pasan: `npm test`",
      "- [ ] Sin secrets en el codigo fuente (revisado con `git grep -i 'password\\|secret\\|api_key'`)",
      "- [ ] El README describe como arrancar y probar la funcionalidad",
    );

    return lines.join("\n");
  }

  private renderAiDevInstructions(projectName: string, stack: string[], modules: string[]): string {
    const stackLine = stack.length > 0 ? stack.join(", ") : "stack definido en OpenSpec";
    const moduleLine = modules.length > 0 ? modules.join(", ") : "modulos definidos en sdd/requirements";

    return [
      `# Instrucciones obligatorias para asistentes IA - ${projectName}`,
      "",
      "> Este archivo es el protocolo de trabajo para Claude Code, GitHub Copilot, ChatGPT u otros agentes.",
      "> No es una sugerencia: cualquier cambio de codigo debe seguir este flujo SDD.",
      "",
      "## Contexto fijo del proyecto",
      "",
      `- Proyecto: ${projectName}`,
      `- Stack: ${stackLine}`,
      `- Modulos principales: ${moduleLine}`,
      "- Fuente de verdad: `sdd/constitution.md`, `sdd/specifications/openspec.md` y `sdd/tasks/backlog.md`.",
      "",
      "## Workflow obligatorio de 10 pasos",
      "",
      "1. Leer `README.md` para entender como levantar y verificar el proyecto.",
      "2. Leer `sdd/constitution.md` para respetar arquitectura, stack y limites.",
      "3. Leer `sdd/specifications/openspec.md` y la spec `sdd/specifications/feature-*.md` relacionada.",
      "4. Leer `sdd/tasks/task-status.md` y `sdd/tasks/backlog.md` para ubicar la tarea.",
      "5. Resumir el objetivo, alcance y archivos previstos antes de modificar codigo.",
      "6. Pedir confirmacion si la tarea cambia schema, migraciones, dependencias, autenticacion, despliegue o datos existentes.",
      "7. Implementar el cambio minimo, respetando convenciones del framework y patrones existentes.",
      "8. Crear o actualizar tests proporcionales al riesgo del cambio.",
      "9. Ejecutar o indicar los checks: lint, typecheck, tests, build y migraciones si aplica.",
      "10. Actualizar documentacion SDD/docs/README afectada y registrar tareas pendientes.",
      "",
      "## Restricciones obligatorias",
      "",
      "- No eliminar archivos, migraciones, datos o configuracion sin confirmacion explicita.",
      "- No introducir dependencias nuevas sin justificar coste, mantenimiento y alternativa sin dependencia.",
      "- No cambiar el stack aprobado en `sdd/technology-decisions.md` sin ADR o decision registrada.",
      "- No hardcodear secretos, tokens, passwords, URLs privadas ni claves de proveedores.",
      "- No crear modulos huerfanos fuera de la estructura existente.",
      "- No usar `any` o desactivar validaciones/lint para hacer pasar checks.",
      "- No mockear logica de dominio propia en tests; mockear solo I/O externo.",
      "- No modificar codigo no relacionado con la tarea salvo que se explique y se confirme.",
      "- No marcar una tarea como completa si no hay forma de verificarla.",
      "- No inventar comportamiento: si falta informacion, documentar supuesto o preguntar.",
      "",
      "## Prompt base para iniciar una sesion",
      "",
      "```text",
      `Estoy trabajando en ${projectName}.`,
      "Antes de tocar codigo, lee y resume estos archivos:",
      "1. README.md",
      "2. sdd/constitution.md",
      "3. sdd/specifications/openspec.md",
      "4. sdd/tasks/backlog.md",
      "5. sdd/tasks/task-status.md",
      "Despues dime: objetivo del proyecto, stack, modulos principales, riesgos y siguiente tarea recomendada.",
      "No modifiques archivos hasta que confirme el alcance.",
      "```",
      "",
      "## Prompt para implementar una feature",
      "",
      "```text",
      "Implementa la feature [NOMBRE] siguiendo SDD.",
      "Primero revisa la spec relacionada en sdd/specifications/.",
      "Devuelve un plan con archivos a tocar, cambios de datos/API, tests necesarios y riesgos.",
      "Espera confirmacion antes de editar si hay migraciones, dependencias o cambios de auth.",
      "Al terminar, indica comandos ejecutados y docs actualizadas.",
      "```",
      "",
      "## Prompt para corregir un bug",
      "",
      "```text",
      "Corrige este bug con el cambio minimo posible.",
      "Error: [pegar error]",
      "Contexto: [que estaba haciendo]",
      "Primero identifica causa raiz, archivos implicados y test que evitaria regresion.",
      "No refactorices codigo no relacionado.",
      "```",
      "",
      "## Checklist de cierre para IA",
      "",
      "- [ ] Alcance confirmado o supuesto documentado.",
      "- [ ] Codigo implementado con el cambio minimo.",
      "- [ ] Tests creados o razon explicita si no aplica.",
      "- [ ] Lint/typecheck/tests/build ejecutados o limitacion explicada.",
      "- [ ] README/docs/SDD actualizados si cambia comportamiento, setup o API.",
      "- [ ] `sdd/tasks/task-status.md` refleja el estado real.",
    ].join("\n");
  }

  private renderAiTestingInstructions(projectName: string, modules: string[]): string {
    return [
      `# Estrategia de testing con IA — ${projectName}`,
      "",
      "> Convenciones de testing del proyecto y prompts para generar tests eficazmente.",
      "",
      "## Que testar (y que no)",
      "",
      "| Testar | No testar |",
      "| --- | --- |",
      "| Logica de negocio en Services | Constructores simples |",
      "| Validacion de DTOs/schemas | Getters/setters triviales |",
      "| Transformaciones de datos | Codigo del framework (NestJS/Django) |",
      "| Casos de error y bordes | Queries directas a la BD (usar repositorio mock) |",
      "",
      "## Prompt para generar tests",
      "",
      "```",
      "Genera tests unitarios para el siguiente [Service/Function/Agent].",
      "Contexto del proyecto:",
      `- Stack: ${modules.length > 0 ? modules[0] : "NestJS + Jest"}`,
      "- Convenciones: Arrange-Act-Assert, nombres descriptivos en espanol",
      "- Mocks: usa jest.fn() para dependencias externas, no implementaciones reales",
      "",
      "Casos que DEBEN estar cubiertos:",
      "1. Happy path — entrada valida, resultado esperado",
      "2. Entrada invalida — error descriptivo",
      "3. Dependencia falla — manejo de error correcto",
      "",
      "[PEGA EL CODIGO A TESTAR]",
      "```",
      "",
      "## Casos obligatorios por modulo",
      "",
      ...(modules.length > 0 ? modules.slice(0, 5).flatMap(m => [
        `### ${m}`,
        "",
        `- [ ] Crear ${m.toLowerCase()} con datos validos devuelve 201`,
        `- [ ] Crear ${m.toLowerCase()} sin campos requeridos devuelve 400`,
        `- [ ] Obtener ${m.toLowerCase()} inexistente devuelve 404`,
        `- [ ] Usuario sin permisos recibe 403`,
        "",
      ]) : ["- [ ] Tests por definir — ver sdd/requirements/requirements.md"]),
      "",
      "## Ejecutar tests",
      "",
      "```bash",
      "npm test                    # todos los tests",
      "npm test -- --watch         # modo watch",
      "npm test -- --coverage      # con cobertura",
      "npm test -- [nombre-modulo] # solo un modulo",
      "```",
    ].join("\n");
  }

  private renderGitignore(stack: string[]): string {
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));
    const hasNode = !stack.every(s => /^python|^ruby|^go/i.test(s));

    const lines = [
      "# ── Dependencies ─────────────────────────────────────────────────────",
    ];

    if (hasNode) {
      lines.push("node_modules/", ".pnp", ".pnp.js", "");
    }

    if (hasPython) {
      lines.push(
        "# Python",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".venv/",
        "venv/",
        ".pytest_cache/",
        "*.egg-info/",
        "dist/",
        "build/",
        "",
      );
    }

    lines.push(
      "# ── Build outputs ────────────────────────────────────────────────────",
      "dist/",
      "build/",
      ".next/",
      "out/",
      ".nuxt/",
      "",
      "# ── Environment & secrets ────────────────────────────────────────────",
      ".env",
      ".env.local",
      ".env.*.local",
      "!.env.example",
      "",
      "# ── IDE ──────────────────────────────────────────────────────────────",
      ".idea/",
      ".vscode/",
      "*.suo",
      "*.sw?",
      "*.swp",
      "",
      "# ── OS ───────────────────────────────────────────────────────────────",
      ".DS_Store",
      "Thumbs.db",
      "desktop.ini",
      "",
      "# ── Logs ─────────────────────────────────────────────────────────────",
      "*.log",
      "npm-debug.log*",
      "yarn-debug.log*",
      "yarn-error.log*",
      "pnpm-debug.log*",
      "",
      "# ── Testing & coverage ───────────────────────────────────────────────",
      "coverage/",
      ".nyc_output/",
      "",
      "# ── Database ─────────────────────────────────────────────────────────",
      "*.db",
      "*.db-journal",
      "*.sqlite",
    );

    return lines.join("\n");
  }

  private renderEditorConfig(): string {
    return [
      "root = true",
      "",
      "[*]",
      "charset = utf-8",
      "indent_style = space",
      "indent_size = 2",
      "end_of_line = lf",
      "trim_trailing_whitespace = true",
      "insert_final_newline = true",
      "",
      "[*.py]",
      "indent_size = 4",
      "",
      "[*.md]",
      "trim_trailing_whitespace = false",
      "",
      "[*.yml]",
      "indent_size = 2",
      "",
      "[Makefile]",
      "indent_style = tab",
    ].join("\n");
  }

  private renderDevDockerCompose(projectName: string, stack: string[]): string {
    const slug = slugify(projectName);
    const hasRedis = stack.some(s => /redis|bull|queue/i.test(s));
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));
    const hasMinio = stack.some(s => /minio|s3|storage/i.test(s));

    const lines = [
      `# Docker Compose — Entorno de desarrollo (${projectName})`,
      "# Expone todos los puertos y monta volumenes para hot-reload.",
      "# NO usar en produccion.",
      "",
      'version: "3.9"',
      "",
      "services:",
      `  postgres:`,
      `    image: postgres:16-alpine`,
      `    environment:`,
      `      POSTGRES_USER: \${DB_USER:-${slug}}`,
      `      POSTGRES_PASSWORD: \${DB_PASSWORD:-devpassword}`,
      `      POSTGRES_DB: \${DB_NAME:-${slug}_dev}`,
      `    ports:`,
      `      - "5432:5432"`,
      `    volumes:`,
      `      - postgres_dev_data:/var/lib/postgresql/data`,
      `    healthcheck:`,
      `      test: ["CMD-SHELL", "pg_isready -U \${DB_USER:-${slug}}"]`,
      `      interval: 5s`,
      `      timeout: 3s`,
      `      retries: 10`,
    ];

    if (hasRedis) {
      lines.push(
        "",
        "  redis:",
        "    image: redis:7-alpine",
        "    ports:",
        '      - "6379:6379"',
        "    command: redis-server --loglevel debug",
      );
    }

    if (hasMinio) {
      lines.push(
        "",
        "  minio:",
        "    image: minio/minio:latest",
        "    command: server /data --console-address ':9001'",
        "    environment:",
        "      MINIO_ROOT_USER: admin",
        "      MINIO_ROOT_PASSWORD: devpassword",
        "    ports:",
        '      - "9000:9000"',
        '      - "9001:9001"',
        "    volumes:",
        "      - minio_dev_data:/data",
      );
    }

    if (hasPython) {
      lines.push(
        "",
        "  ai-service:",
        "    build: ./apps/ai-service",
        "    ports:",
        '      - "8003:8003"',
        "    volumes:",
        "      - ./apps/ai-service:/app",
        "    environment:",
        '      - PYTHONUNBUFFERED=1',
        "    command: uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload",
        "    depends_on:",
        "      postgres:",
        "        condition: service_healthy",
      );
    }

    lines.push(
      "",
      "volumes:",
      "  postgres_dev_data:",
      ...(hasRedis ? [] : []),
      ...(hasMinio ? ["  minio_dev_data:"] : []),
      "",
      "networks:",
      "  default:",
      `    name: ${slug}_dev_network`,
    );

    return lines.join("\n");
  }

  private renderCiYaml(projectName: string, stack: string[]): string {
    const hasNode = stack.some(s => /typescript|react|nestjs|node/i.test(s)) || true;
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));

    const lines = [
      `# GitHub Actions CI — ${projectName}`,
      "# Se ejecuta en cada push y pull request.",
      "",
      "name: CI",
      "",
      "on:",
      "  push:",
      "    branches: [main, develop]",
      "  pull_request:",
      "    branches: [main]",
      "",
      "jobs:",
    ];

    if (hasNode) {
      lines.push(
        "  api:",
        `    name: API (Node.js)`,
        "    runs-on: ubuntu-latest",
        "",
        "    services:",
        "      postgres:",
        "        image: postgres:16-alpine",
        "        env:",
        "          POSTGRES_USER: testuser",
        "          POSTGRES_PASSWORD: testpass",
        "          POSTGRES_DB: testdb",
        "        ports:",
        "          - 5432:5432",
        "        options: >-",
        "          --health-cmd pg_isready",
        "          --health-interval 10s",
        "          --health-timeout 5s",
        "          --health-retries 5",
        "",
        "    steps:",
        "      - uses: actions/checkout@v4",
        "",
        "      - name: Setup Node.js",
        "        uses: actions/setup-node@v4",
        "        with:",
        "          node-version: '20'",
        "          cache: 'npm'",
        "",
        "      - name: Install dependencies",
        "        run: npm ci",
        "",
        "      - name: Type check",
        "        run: npx tsc --noEmit",
        "        working-directory: apps/api",
        "",
        "      - name: Lint",
        "        run: npm run lint",
        "        working-directory: apps/api",
        "",
        "      - name: Run tests",
        "        run: npm test -- --passWithNoTests",
        "        working-directory: apps/api",
        "        env:",
        "          DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb",
        "          JWT_SECRET: test_secret_for_ci",
        "",
      );
    }

    if (hasPython) {
      lines.push(
        "  ai-service:",
        "    name: AI Service (Python)",
        "    runs-on: ubuntu-latest",
        "",
        "    steps:",
        "      - uses: actions/checkout@v4",
        "",
        "      - name: Setup Python",
        "        uses: actions/setup-python@v5",
        "        with:",
        "          python-version: '3.12'",
        "",
        "      - name: Install dependencies",
        "        run: pip install -e '.[dev]'",
        "        working-directory: apps/ai-service",
        "",
        "      - name: Type check",
        "        run: mypy app/ --ignore-missing-imports",
        "        working-directory: apps/ai-service",
        "",
        "      - name: Run tests",
        "        run: pytest tests/ -q",
        "        working-directory: apps/ai-service",
        "",
      );
    }

    return lines.join("\n");
  }

  private renderApiReference(
    projectName: string,
    summary: Record<string, unknown>,
    modules: string[]
  ): string {
    const apiEndpoints = Array.isArray(summary.api_endpoints)
      ? (summary.api_endpoints as Array<Record<string, unknown>>) : [];
    const constraints = (typeof summary.constraints === "object" && summary.constraints)
      ? (summary.constraints as Record<string, unknown>) : {};
    const stack = Array.isArray(constraints.stack) ? (constraints.stack as string[]) : [];
    const hasAuth = stack.some(s => /jwt|auth/i.test(s)) || modules.some(m => /auth/i.test(m));

    const lines = [
      `# API Reference — ${projectName}`,
      "",
      "> Base URL: `http://localhost:3000`",
      "> Formato: JSON. Todos los endpoints de escritura requieren `Content-Type: application/json`.",
      "",
    ];

    if (hasAuth) {
      lines.push(
        "## Autenticacion",
        "",
        "La API usa **JWT Bearer tokens**. Incluye el token en el header:",
        "",
        "```",
        "Authorization: Bearer <token>",
        "```",
        "",
        "### Endpoints de autenticacion",
        "",
        "| Metodo | Ruta | Descripcion |",
        "| --- | --- | --- |",
        "| `POST` | `/auth/register` | Registrar nuevo usuario |",
        "| `POST` | `/auth/login` | Iniciar sesion, devuelve access + refresh token |",
        "| `POST` | `/auth/refresh` | Renovar access token |",
        "| `POST` | `/auth/logout` | Invalidar refresh token |",
        "",
      );
    }

    if (apiEndpoints.length > 0) {
      const byModule = new Map<string, Array<Record<string, unknown>>>();
      for (const ep of apiEndpoints) {
        const mod = (ep.module as string) || "General";
        if (!byModule.has(mod)) byModule.set(mod, []);
        byModule.get(mod)!.push(ep);
      }
      for (const [mod, endpoints] of byModule) {
        lines.push(`## ${mod}`, "", "| Metodo | Ruta | Auth | Descripcion |", "| --- | --- | --- | --- |");
        for (const ep of endpoints) {
          const method = ((ep.method as string) ?? "GET").toUpperCase();
          const path = (ep.path as string) ?? "";
          const epDesc = (ep.description as string) ?? "";
          const auth = ep.requires_auth ? "Si" : "No";
          lines.push(`| \`${method}\` | \`${path}\` | ${auth} | ${epDesc} |`);
        }
        lines.push("");
      }
    } else {
      for (const mod of modules.slice(0, 6)) {
        const slug = mod.toLowerCase().replace(/\s+/g, "-");
        lines.push(
          `## ${mod}`,
          "",
          "| Metodo | Ruta | Descripcion |",
          "| --- | --- | --- |",
          `| \`GET\` | \`/${slug}\` | Listar todos los registros |`,
          `| \`GET\` | \`/${slug}/:id\` | Obtener uno por ID |`,
          `| \`POST\` | \`/${slug}\` | Crear nuevo registro |`,
          `| \`PATCH\` | \`/${slug}/:id\` | Actualizar parcialmente |`,
          `| \`DELETE\` | \`/${slug}/:id\` | Eliminar |`,
          "",
        );
      }
    }

    lines.push(
      "## Codigos de respuesta",
      "",
      "| Codigo | Significado |",
      "| --- | --- |",
      "| `200` | OK — operacion exitosa |",
      "| `201` | Created — recurso creado |",
      "| `400` | Bad Request — datos de entrada invalidos |",
      "| `401` | Unauthorized — token ausente o expirado |",
      "| `403` | Forbidden — sin permisos |",
      "| `404` | Not Found — recurso inexistente |",
      "| `409` | Conflict — duplicado |",
      "| `500` | Internal Server Error — error inesperado |",
    );

    return lines.join("\n");
  }

  private renderDeploymentGuide(projectName: string, stack: string[]): string {
    const slug = slugify(projectName);
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));

    return [
      `# Guia de despliegue — ${projectName}`,
      "",
      "> Esta guia cubre los tres escenarios mas comunes: Railway, Render y VPS propio.",
      "",
      "## Variables de entorno de produccion",
      "",
      "Configura estas variables en tu plataforma de despliegue:",
      "",
      "```",
      "NODE_ENV=production",
      `DATABASE_URL=postgresql://user:password@host:5432/${slug}_prod`,
      "JWT_SECRET=<secreto-largo-y-aleatorio-minimo-64-caracteres>",
      "JWT_REFRESH_SECRET=<otro-secreto-diferente>",
      ...(hasPython ? ["AI_SERVICE_URL=<url-del-servicio-ai>"] : []),
      "```",
      "",
      "## Opcion 1: Railway (recomendado para MVPs)",
      "",
      "```bash",
      "# Instalar CLI",
      "npm install -g @railway/cli",
      "",
      "# Login y crear proyecto",
      "railway login",
      "railway init",
      "",
      "# Añadir PostgreSQL",
      "railway add --plugin postgresql",
      "",
      "# Desplegar",
      "railway up",
      "```",
      "",
      "> Railway detecta automaticamente Node.js y ejecuta `npm run build && npm start`.",
      "",
      "## Opcion 2: Render",
      "",
      "1. Conecta tu repositorio GitHub en render.com",
      "2. Crea un **Web Service** con:",
      "   - Build command: `npm ci && npm run build`",
      "   - Start command: `npm run start:prod`",
      "3. Crea una **PostgreSQL** database y copia la URL de conexion",
      "4. Añade las variables de entorno en la seccion Environment",
      "",
      "## Opcion 3: VPS con Docker",
      "",
      "```bash",
      "# En el servidor",
      `git clone <repo> /opt/${slug}`,
      `cd /opt/${slug}`,
      "",
      "# Configurar entorno",
      "cp .env.example .env",
      "nano .env  # ajusta con los valores reales",
      "",
      "# Arrancar en produccion",
      "docker compose up -d --build",
      "",
      "# Ejecutar migraciones",
      "docker compose exec api npm run db:migrate:deploy",
      "```",
      "",
      "## Checklist pre-despliegue",
      "",
      "- [ ] Variables de entorno configuradas (sin valores de development)",
      "- [ ] `NODE_ENV=production`",
      "- [ ] JWT secrets cambiados (minimo 64 caracteres aleatorios)",
      "- [ ] Base de datos de produccion accesible",
      "- [ ] Migraciones ejecutadas",
      "- [ ] Health check responde: `curl https://tu-dominio/health`",
      "- [ ] HTTPS habilitado (certificado SSL activo)",
    ].join("\n");
  }

  private renderBacklog(projectName: string, modules: string[]): string {
    const lines = [
      `# Backlog — ${projectName}`,
      "",
      "> Tareas organizadas por modulo y prioridad. Actualiza este archivo al iniciar cada sprint.",
      "",
      "## Leyenda de prioridad",
      "",
      "- 🔴 **Critico** — bloquea el MVP",
      "- 🟡 **Alto** — necesario para el lanzamiento",
      "- 🟢 **Medio** — mejora la experiencia",
      "- ⚪ **Bajo** — nice-to-have",
      "",
    ];

    const defaultModules = modules.length > 0 ? modules : ["Backend", "Frontend", "Infraestructura"];
    for (const mod of defaultModules.slice(0, 8)) {
      lines.push(
        `## ${mod}`,
        "",
        "| # | Tarea | Prioridad | Estado | Estimacion |",
        "| --- | --- | --- | --- | --- |",
        `| 1 | Definir modelo de datos de ${mod} | 🔴 | Por hacer | 2h |`,
        `| 2 | Implementar endpoints CRUD de ${mod} | 🔴 | Por hacer | 4h |`,
        `| 3 | Tests unitarios de ${mod} | 🟡 | Por hacer | 2h |`,
        `| 4 | Documentar endpoints de ${mod} en api-reference.md | 🟢 | Por hacer | 1h |`,
        "",
      );
    }

    lines.push(
      "## Tareas de infraestructura",
      "",
      "| # | Tarea | Prioridad | Estado |",
      "| --- | --- | --- | --- |",
      "| 1 | Configurar CI/CD en GitHub Actions | 🔴 | Por hacer |",
      "| 2 | Configurar entorno de produccion | 🟡 | Por hacer |",
      "| 3 | Configurar monitoreo (Sentry / Uptime Robot) | 🟢 | Por hacer |",
    );

    return lines.join("\n");
  }

  private renderLearningPlan(projectName: string, stack: string[], modules: string[]): string {
    const hasPython = stack.some(s => /python|fastapi|django/i.test(s));
    const hasTypeScript = stack.some(s => /typescript|nestjs|react|next/i.test(s));
    const hasDocker = true;

    const lines = [
      `# Plan de aprendizaje — ${projectName}`,
      "",
      "> Ruta de aprendizaje personalizada para implementar este proyecto paso a paso.",
      "> Cada seccion incluye recursos gratuitos y el objetivo de aprendizaje concreto.",
      "",
      "## Nivel actual recomendado",
      "",
      "Este plan asume conocimientos basicos de programacion.",
      "Si eres principiante, completa primero los recursos marcados con ⭐.",
      "",
    ];

    let week = 1;

    if (hasTypeScript) {
      lines.push(
        `## Semana ${week}: TypeScript fundamentals`,
        "",
        "**Objetivo**: Escribir TypeScript con tipos, interfaces y genericos basicos.",
        "",
        "| Recurso | Tipo | Tiempo |",
        "| --- | --- | --- |",
        "| [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html) ⭐ | Documentacion | 4h |",
        "| [Execute Program — TypeScript](https://www.executeprogram.com/courses/typescript) | Curso interactivo | 6h |",
        "| [Total TypeScript](https://www.totaltypescript.com/tutorials) | Tutoriales | 3h |",
        "",
        "**Tarea practica**: Reescribe una funcion de JavaScript puro a TypeScript tipado en este proyecto.",
        "",
      );
      week++;
    }

    if (hasDocker) {
      lines.push(
        `## Semana ${week}: Docker y entornos de desarrollo`,
        "",
        "**Objetivo**: Levantar y gestionar los servicios del proyecto con Docker Compose.",
        "",
        "| Recurso | Tipo | Tiempo |",
        "| --- | --- | --- |",
        "| [Docker Getting Started](https://docs.docker.com/get-started/) ⭐ | Documentacion | 3h |",
        "| [Docker Compose tutorial](https://docs.docker.com/compose/gettingstarted/) | Tutorial | 2h |",
        "",
        `**Tarea practica**: Arranca todos los servicios de ${projectName} con \`docker compose up -d\` sin errores.`,
        "",
      );
      week++;
    }

    if (stack.some(s => /nestjs/i.test(s))) {
      lines.push(
        `## Semana ${week}: NestJS — arquitectura por modulos`,
        "",
        "**Objetivo**: Crear un modulo NestJS con Service, Controller y DTOs.",
        "",
        "| Recurso | Tipo | Tiempo |",
        "| --- | --- | --- |",
        "| [NestJS Fundamentals](https://docs.nestjs.com/first-steps) ⭐ | Documentacion | 5h |",
        "| [NestJS Crash Course — Traversy](https://www.youtube.com/watch?v=0M8AYU_hPas) | Video | 2h |",
        "",
        `**Tarea practica**: Crea el modulo \`${modules[0] ?? "usuarios"}\` con endpoints CRUD completos.`,
        "",
      );
      week++;
    }

    if (hasPython) {
      lines.push(
        `## Semana ${week}: FastAPI y agentes IA`,
        "",
        "**Objetivo**: Crear un endpoint FastAPI que llame a un LLM y devuelva respuesta estructurada.",
        "",
        "| Recurso | Tipo | Tiempo |",
        "| --- | --- | --- |",
        "| [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) ⭐ | Documentacion | 4h |",
        "| [LangChain Quickstart](https://python.langchain.com/docs/get_started/quickstart) | Tutorial | 2h |",
        "",
        "**Tarea practica**: Crea un endpoint `/summarize` que reciba texto y devuelva un resumen con el LLM.",
        "",
      );
      week++;
    }

    if (modules.length > 0) {
      lines.push(
        `## Semanas ${week}-${week + 1}: Implementacion del MVP`,
        "",
        "**Objetivo**: Implementar los modulos principales del proyecto.",
        "",
        "Orden recomendado:",
        "",
        ...modules.slice(0, 6).map((m, i) => `${i + 1}. **${m}** — backend primero, luego frontend`),
        "",
        "**Recursos por modulo**: ver `sdd/requirements/requirements.md` para los criterios de aceptacion.",
        "",
      );
    }

    lines.push(
      "## Hitos de conocimiento",
      "",
      "- [ ] Puedo arrancar todos los servicios del proyecto sin ayuda",
      "- [ ] Puedo crear un endpoint REST nuevo de principio a fin",
      "- [ ] Puedo escribir un test unitario para cualquier Service",
      "- [ ] Puedo desplegar el proyecto en Railway o Render",
      "- [ ] Puedo usar la IA (Claude Code) para añadir funcionalidades manteniendo la arquitectura",
      "",
      "---",
      "",
      "_Este plan es una guia — adaptatalo a tu ritmo. Lo importante es completar tareas practicas, no los videos._",
    );

    return lines.join("\n");
  }

}
