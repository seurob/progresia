import { ConflictException, Injectable } from "@nestjs/common";
import { Prisma, SpecificationStatus, SpecificationType } from "@prisma/client";
import { PrismaService } from "../../database/prisma.service";
import { ProjectsService } from "../projects/projects.service";

interface ManifestFile {
  path: string;
  kind: "document" | "specification";
  description: string;
  source: string;
}

@Injectable()
export class ArtifactsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly projectsService: ProjectsService
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
    return value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "") || "progresia-project";
  }
}
