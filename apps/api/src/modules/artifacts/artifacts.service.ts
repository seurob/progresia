import { ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import { Prisma, ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import JSZip from "jszip";
import { AiServiceClient } from "../ai-service/ai-service.client";
import { GithubService } from "../github/github.service";
import { StorageService } from "../storage/storage.service";
import { PrismaService } from "../../database/prisma.service";
import { ProjectsService } from "../projects/projects.service";
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
    await this.projectsService.ensureProjectAccess(projectId, userId);

    return this.prisma.artifactBundle.findMany({
      where: { projectId },
      orderBy: { createdAt: "desc" }
    });
  }

  async generateBundle(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const specification = await this.prisma.specification.findFirst({
      where: {
        projectId,
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

    return this.prisma.artifactBundle.create({
      data: {
        projectId,
        specificationId: specification.id,
        manifest: manifest as unknown as Prisma.InputJsonValue
      }
    });
  }

  async generateCode(userId: string, projectId: string) {
    const project = await this.projectsService.ensureProjectAccess(projectId, userId);
    const specification = await this.prisma.specification.findFirst({
      where: { projectId, type: SpecificationType.OPENSPEC, status: SpecificationStatus.GENERATED },
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

    const generated = await this.aiServiceClient.generateCode({
      project_name: project.name,
      sector: project.sector,
      modules,
      requirements,
      needs_auth: true,
      needs_admin_panel: true,
      needs_ai: false,
      stack
    });

    const existingBundle = await this.prisma.artifactBundle.findFirst({
      where: { projectId, specificationId: specification.id },
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
          where: { id: projectId },
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
          projectId,
          specificationId: specification.id,
          manifest: manifest as unknown as Prisma.InputJsonValue,
          generatedContent: generated as unknown as Prisma.InputJsonValue
        }
      }),
      this.prisma.project.update({
        where: { id: projectId },
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
      {
        path: `${basePath}/README.md`,
        kind: "document",
        description: "Resumen del MVP, alcance funcional y puesta en marcha.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/requirements.md`,
        kind: "document",
        description: "Requisitos funcionales y criterios de aceptacion extraidos de OpenSpec.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/architecture.md`,
        kind: "document",
        description: "Arquitectura tecnica propuesta para frontend, backend, datos e IA.",
        source: "openspec"
      },
      {
        path: `${basePath}/openspec/spec.md`,
        kind: "specification",
        description: "Contrato OpenSpec generado para gobernar el desarrollo.",
        source: "openspec"
      }
    ];

    return {
      version: "0.1.0",
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
    const requirements = Array.isArray(summary.requirements) ? summary.requirements : [];

    if (file.path.endsWith("README.md")) {
      return [
        `# ${projectName}`,
        "",
        `> Generated by ProgresIA Studio · ${manifest.generatedAt}`,
        "",
        "## Descripcion",
        "",
        `Proyecto generado a partir de OpenSpec \`${manifest.sourceSpecificationId}\`.`,
        "",
        "## Puesta en marcha",
        "",
        "```bash",
        "docker compose up -d",
        "npm install",
        "npm run dev",
        "```",
        "",
        "## Archivos incluidos",
        "",
        ...(manifest.files ?? []).map((f) => `- \`${f.path}\` — ${f.description}`)
      ].join("\n");
    }

    if (file.path.endsWith("requirements.md")) {
      const reqLines = requirements.map((r: unknown) => {
        if (typeof r === "object" && r !== null) {
          const req = r as { id?: string; title?: string; description?: string };
          return `### ${req.id ?? ""} — ${req.title ?? ""}\n\n${req.description ?? ""}`;
        }
        return String(r);
      });

      return [
        `# Requisitos funcionales — ${projectName}`,
        "",
        "> Extraidos del OpenSpec generado por IA.",
        "",
        ...(reqLines.length > 0 ? reqLines : ["_No se encontraron requisitos en la especificacion._"])
      ].join("\n\n");
    }

    if (file.path.endsWith("architecture.md")) {
      return [
        `# Arquitectura tecnica — ${projectName}`,
        "",
        "## Stack propuesto",
        "",
        "| Capa | Tecnologia |",
        "|------|-----------|",
        "| Frontend | React 19, Vite, Tailwind CSS |",
        "| Backend | NestJS, TypeScript, PostgreSQL, Prisma |",
        "| IA | FastAPI, Python, LangChain |",
        "| Infraestructura | Docker Compose |",
        "",
        "## Contextos acotados",
        "",
        "- **Auth** — registro, login, JWT",
        "- **Projects** — ciclo de vida del proyecto",
        "- **Specifications** — generacion y gestion de specs",
        "- **Artifacts** — bundles y exportacion"
      ].join("\n");
    }

    if (file.path.endsWith("spec.md")) {
      return [
        `# OpenSpec — ${projectName}`,
        "",
        `> Generado el ${manifest.generatedAt}`,
        "",
        "```json",
        JSON.stringify(summary, null, 2),
        "```"
      ].join("\n");
    }

    return `# ${file.path}\n\n${file.description}`;
  }

  private extractSourceSummary(source: Prisma.JsonValue) {
    if (!source || typeof source !== "object" || Array.isArray(source)) {
      return {};
    }

    const record = source as Record<string, unknown>;
    return {
      project: record.project,
      modules: record.modules,
      requirements: record.requirements
    };
  }

  private slugify(value: string) {
    return (
      value
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "") || "progresia-project"
    );
  }
}
