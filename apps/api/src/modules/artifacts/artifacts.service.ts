import { ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import { Prisma, ProjectStatus, SpecificationStatus, SpecificationType } from "@prisma/client";
import * as JSZip from "jszip";
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

    const idea = await this.prisma.idea.findUnique({ where: { projectId } });

    // Use the stored architecture recommendation to drive template dispatch,
    // so the code generation matches what was recommended to the user.
    const archSpec = await this.prisma.specification.findFirst({
      where: { projectId, type: SpecificationType.ARCHITECTURE, status: SpecificationStatus.GENERATED },
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
        description: "Guia de inicio: descripcion del proyecto, setup e instrucciones de arranque.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/requisitos.md`,
        kind: "document",
        description: "Requisitos funcionales y no funcionales completos del sistema.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/sdd.md`,
        kind: "document",
        description: "Software Design Document: arquitectura tecnica, modulos y diseno del sistema.",
        source: "openspec"
      },
      {
        path: `${basePath}/docs/pasos-implementacion.md`,
        kind: "document",
        description: "Plan de implementacion paso a paso con checklist accionable.",
        source: "openspec"
      },
      {
        path: `${basePath}/docker/docker-compose.yml`,
        kind: "specification",
        description: "Infraestructura de desarrollo lista para usar con Docker Compose.",
        source: "openspec"
      },
      {
        path: `${basePath}/docker/.env.example`,
        kind: "specification",
        description: "Variables de entorno requeridas para arrancar los servicios.",
        source: "openspec"
      },
      {
        path: `${basePath}/openspec/spec.json`,
        kind: "specification",
        description: "Especificacion tecnica completa generada por IA (OpenSpec JSON).",
        source: "openspec"
      }
    ];

    return {
      version: "0.2.0",
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

    if (file.path.endsWith("README.md")) {
      return this.renderReadme(projectName, manifest, modules, stack);
    }

    if (file.path.includes("requisitos.md") || file.path.includes("requirements.md")) {
      return this.renderRequirements(projectName, requirements, nonFunctional, userStories);
    }

    if (file.path.endsWith("sdd.md")) {
      return this.renderSDD(projectName, modules, stack, requirements, constraints);
    }

    if (file.path.endsWith("pasos-implementacion.md")) {
      return this.renderImplementationSteps(projectName, modules);
    }

    if (file.path.endsWith("docker-compose.yml")) {
      return this.renderDockerCompose(projectName, stack, modules);
    }

    if (file.path.endsWith(".env.example")) {
      return this.renderEnvExample(projectName, stack);
    }

    if (file.path.endsWith("spec.json")) {
      return JSON.stringify(summary, null, 2);
    }

    return `# ${file.path}\n\n${file.description}`;
  }

  private renderReadme(
    projectName: string,
    manifest: Manifest,
    modules: string[],
    stack: string[]
  ): string {
    const lines = [
      `# ${projectName}`,
      "",
      `> Generado por **ProgresIA Studio** el ${new Date(manifest.generatedAt).toLocaleDateString("es-ES", { year: "numeric", month: "long", day: "numeric" })}`,
      "",
      "## Inicio rapido",
      "",
      "```bash",
      "# 1. Copia las variables de entorno",
      "cp docker/.env.example docker/.env",
      "",
      "# 2. Edita las variables con tus valores",
      "#    (cambia contrasenas y secretos)",
      "nano docker/.env",
      "",
      "# 3. Arranca todos los servicios",
      "docker compose -f docker/docker-compose.yml up -d",
      "",
      "# 4. Comprueba que todo arranca",
      "docker compose -f docker/docker-compose.yml ps",
      "```",
      "",
      "## Estructura del proyecto",
      "",
      "```",
      `${this.slugify(projectName)}/`,
      "├── docs/                    # Documentacion del proyecto",
      "│   ├── requisitos.md        # Requisitos funcionales y no funcionales",
      "│   ├── sdd.md               # Software Design Document",
      "│   └── pasos-implementacion.md  # Guia de implementacion",
      "├── docker/                  # Configuracion Docker",
      "│   ├── docker-compose.yml   # Servicios de infraestructura",
      "│   └── .env.example         # Variables de entorno de ejemplo",
      "└── openspec/",
      "    └── spec.json            # Especificacion tecnica completa",
      "```"
    ];

    if (modules.length > 0) {
      lines.push("", "## Modulos del sistema", "");
      for (const mod of modules) {
        lines.push(`- ${mod}`);
      }
    }

    if (stack.length > 0) {
      lines.push("", "## Stack tecnologico", "");
      for (const s of stack) {
        lines.push(`- ${s}`);
      }
    }

    lines.push(
      "",
      "## Archivos incluidos",
      "",
      ...(manifest.files ?? []).map((f) => `- \`${f.path}\` — ${f.description}`),
      "",
      "---",
      "",
      "_Generado con [ProgresIA Studio](https://github.com/progresia)_"
    );

    return lines.join("\n");
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

  private renderSDD(
    projectName: string,
    modules: string[],
    stack: string[],
    requirements: Array<Record<string, unknown>>,
    constraints: Record<string, unknown>
  ): string {
    const timeline = constraints.timeline ? String(constraints.timeline) : "A definir";
    const lines = [
      `# Software Design Document — ${projectName}`,
      "",
      "## 1. Resumen ejecutivo",
      "",
      `Este documento describe el diseño tecnico del sistema **${projectName}**.`,
      "Define la arquitectura, los modulos del sistema y los criterios de diseno.",
      "",
      "## 2. Alcance",
      "",
      ...(requirements.slice(0, 5).map(r => `- ${r.title ?? r.id ?? "Requisito"}`)),
      requirements.length > 5 ? `- _...y ${requirements.length - 5} requisitos mas (ver docs/requisitos.md)_` : "",
      "",
      "## 3. Arquitectura del sistema",
      "",
      "### 3.1 Diagrama de componentes",
      "",
      "```",
      "┌─────────────┐     HTTP/REST     ┌──────────────┐",
      "│  Frontend   │ ◄──────────────► │  API Backend │",
      "│  (Web App)  │                  │  (REST API)  │",
      "└─────────────┘                  └──────┬───────┘",
      "                                        │",
      "                               ┌────────▼────────┐",
      "                               │   Base de datos  │",
      "                               │  (PostgreSQL)    │",
      "                               └─────────────────┘",
      "```",
      "",
      "### 3.2 Stack tecnologico",
      ""
    ];

    if (stack.length > 0) {
      for (const s of stack) {
        lines.push(`- ${s}`);
      }
    } else {
      lines.push(
        "| Capa | Tecnologia |",
        "|------|-----------|",
        "| Frontend | React, Vite, TypeScript |",
        "| Backend | NestJS / FastAPI |",
        "| Base de datos | PostgreSQL |",
        "| Infraestructura | Docker Compose |"
      );
    }

    lines.push(
      "",
      "## 4. Modulos del sistema",
      ""
    );

    if (modules.length > 0) {
      for (let i = 0; i < modules.length; i++) {
        lines.push(
          `### 4.${i + 1} ${modules[i]}`,
          "",
          "**Responsabilidad:** Gestiona las operaciones relacionadas con este modulo.",
          "",
          "**Endpoints principales:**",
          `- \`GET /${this.slugify(modules[i])}\` — Listar`,
          `- \`POST /${this.slugify(modules[i])}\` — Crear`,
          `- \`PUT /${this.slugify(modules[i])}/:id\` — Actualizar`,
          `- \`DELETE /${this.slugify(modules[i])}/:id\` — Eliminar`,
          ""
        );
      }
    } else {
      lines.push("_Los modulos se definiran durante la implementacion._", "");
    }

    lines.push(
      "## 5. Modelo de datos",
      "",
      "_Diagrama ERD a completar durante la implementacion._",
      "",
      "## 6. Seguridad",
      "",
      "- Autenticacion: JWT (access token + refresh token)",
      "- Autorizacion: RBAC por rol de usuario",
      "- Comunicacion: HTTPS obligatorio en produccion",
      "- Datos sensibles: variables de entorno, nunca en codigo",
      "",
      "## 7. Estimacion",
      "",
      `- Timeline estimado: ${timeline}`,
      `- Modulos: ${modules.length > 0 ? modules.length : "Por definir"}`,
      `- Requisitos funcionales: ${requirements.length > 0 ? requirements.length : "Por definir"}`,
      ""
    );

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
