import { PrismaClient, Role, ProjectStatus, SpecificationType, SpecificationStatus } from "@prisma/client";
import * as bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  // ── Admin user ──────────────────────────────────────────────────────────
  // DEVELOPMENT CREDENTIALS ONLY — change via env vars before deploying to production
  const adminEmail = process.env.ADMIN_EMAIL ?? "admin@progresia.local";
  const adminName = process.env.ADMIN_USERNAME ?? "seurobman";
  const adminPassword = process.env.ADMIN_PASSWORD ?? "$eurobman2026";

  await prisma.user.upsert({
    where: { email: adminEmail },
    update: { role: Role.ADMIN },
    create: {
      email: adminEmail,
      name: adminName,
      passwordHash: await bcrypt.hash(adminPassword, 12),
      role: Role.ADMIN
    }
  });

  // ── Demo user ───────────────────────────────────────────────────────────
  const demoPasswordHash = await bcrypt.hash("change_me_123", 12);

  const demoUser = await prisma.user.upsert({
    where: { email: "demo@progresia.local" },
    update: {},
    create: {
      email: "demo@progresia.local",
      name: "Demo User",
      passwordHash: demoPasswordHash,
      role: Role.OWNER
    }
  });

  // ── Demo workspace ──────────────────────────────────────────────────────
  const workspace = await prisma.workspace.upsert({
    where: { id: "10000000-0000-0000-0000-000000000001" },
    update: {},
    create: {
      id: "10000000-0000-0000-0000-000000000001",
      name: "Demo Workspace",
      ownerId: demoUser.id,
      members: { create: { userId: demoUser.id, role: Role.OWNER } }
    }
  });

  // ── Demo project ────────────────────────────────────────────────────────
  const project = await prisma.project.upsert({
    where: { id: "10000000-0000-0000-0000-000000000002" },
    update: { slug: "sistema-de-reservas" },
    create: {
      id: "10000000-0000-0000-0000-000000000002",
      workspaceId: workspace.id,
      name: "Sistema de Reservas",
      slug: "sistema-de-reservas",
      sector: "Educación",
      productType: "Web App",
      description: "Plataforma para gestionar reservas de aulas y recursos del centro.",
      status: ProjectStatus.SPEC_READY
    }
  });

  // ── Demo idea ───────────────────────────────────────────────────────────
  await prisma.idea.upsert({
    where: { projectId: project.id },
    update: {},
    create: {
      projectId: project.id,
      problem: "Gestionar reservas de aulas de forma manual consume demasiado tiempo y genera errores.",
      targetUsers: "Profesores y personal administrativo del centro educativo.",
      coreFeatures: [
        "Calendario de disponibilidad",
        "Reserva de aulas y recursos",
        "Notificaciones por email",
        "Panel de administración",
        "Historial de reservas"
      ],
      complexity: "standard",
      needsAi: false,
      needsAuth: true,
      needsAdminPanel: true,
      constraints: "Debe integrarse con el sistema de calendario existente del centro.",
      mainObjective: "mvp",
      techPreference: "ai_recommends",
      architectureStyle: "frontend_api",
      dataNeeds: ["relational"],
      aiNeeds: "none",
      deploymentTarget: "docker_local",
      expectedResults: ["zip", "docker", "github"]
    }
  });

  // ── Demo specification ──────────────────────────────────────────────────
  await prisma.specification.upsert({
    where: { id: "10000000-0000-0000-0000-000000000003" },
    update: {},
    create: {
      id: "10000000-0000-0000-0000-000000000003",
      projectId: project.id,
      type: SpecificationType.OPENSPEC,
      status: SpecificationStatus.GENERATED,
      content: {
        project: {
          name: "Sistema de Reservas",
          sector: "Educación",
          description: "Plataforma de gestión de reservas de aulas y recursos."
        },
        requirements: [
          { id: "RF-001", title: "Autenticación de usuarios", description: "Los usuarios deben poder registrarse e iniciar sesión." },
          { id: "RF-002", title: "Calendario de disponibilidad", description: "Visualizar disponibilidad de aulas en tiempo real." },
          { id: "RF-003", title: "Crear y cancelar reservas", description: "Usuarios pueden reservar y cancelar sus reservas." },
          { id: "RF-004", title: "Panel de administración", description: "Administradores gestionan aulas, usuarios y reservas." }
        ],
        constraints: {
          stack: ["React", "NestJS", "PostgreSQL", "Docker"],
          delivery: ["MVP en 8 semanas", "Docker Compose para desarrollo local"]
        },
        generatedBy: "seed",
        projectName: "Sistema de Reservas"
      }
    }
  });

  console.log("Seed completed.");
  console.log(`  Admin:    ${adminEmail} / ${adminPassword}`);
  console.log(`  Demo:     demo@progresia.local / change_me_123`);
  console.log("");
  console.log("  ⚠  DEVELOPMENT ONLY — change admin credentials before deploying to production.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
