import { PrismaClient, Role, ProjectStatus, SpecificationType, SpecificationStatus } from "@prisma/client";
import * as bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const passwordHash = await bcrypt.hash("change_me_123", 12);

  const user = await prisma.user.upsert({
    where: { email: "demo@progresia.local" },
    update: {},
    create: {
      email: "demo@progresia.local",
      name: "Demo User",
      passwordHash,
      role: Role.OWNER
    }
  });

  const workspace = await prisma.workspace.upsert({
    where: { id: "10000000-0000-0000-0000-000000000001" },
    update: {},
    create: {
      id: "10000000-0000-0000-0000-000000000001",
      name: "Demo Workspace",
      ownerId: user.id,
      members: {
        create: { userId: user.id, role: Role.OWNER }
      }
    }
  });

  const project = await prisma.project.upsert({
    where: { id: "10000000-0000-0000-0000-000000000002" },
    update: {},
    create: {
      id: "10000000-0000-0000-0000-000000000002",
      workspaceId: workspace.id,
      name: "Sistema de Reservas",
      sector: "Educación",
      productType: "Web App",
      description: "Plataforma para gestionar reservas de aulas y recursos del centro.",
      status: ProjectStatus.SPEC_READY
    }
  });

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
      constraints: "Debe integrarse con el sistema de calendario existente del centro."
    }
  });

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

  console.log(`Seed completed. Demo user: demo@progresia.local / change_me_123`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());