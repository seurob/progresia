"""
VETERINARIA template — clínica veterinaria: propietarios, mascotas, citas, historia clínica y vacunas.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",                              "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",                              "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",                               "typescript", _API_INDEX.replace("__NAME__", name)),
        _f("apps/api/src/trpc.ts",                                "typescript", _TRPC),
        _f("apps/api/src/router.ts",                              "typescript", _ROUTER),
        _f("apps/api/prisma/schema.prisma",                       "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",                             "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",            "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/owners/owner.router.ts",         "typescript", _OWNER_ROUTER),
        _f("apps/api/src/modules/pets/pet.router.ts",             "typescript", _PET_ROUTER),
        _f("apps/api/src/modules/appointments/appointment.router.ts", "typescript", _APPOINTMENT_ROUTER),
        _f("apps/api/src/modules/records/record.router.ts",       "typescript", _RECORD_ROUTER),
        _f("apps/api/Dockerfile",                                 "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",                               "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",                              "json",       _WEB_TSCONFIG),
        _f("apps/web/next.config.js",                             "javascript", _NEXT_CONFIG),
        _f("apps/web/tailwind.config.ts",                         "typescript", _TAILWIND),
        _f("apps/web/postcss.config.js",                          "javascript", _POSTCSS),
        _f("apps/web/src/app/globals.css",                        "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",                            "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",                       "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts",                      "typescript", _AUTH_STORE),
        _f("apps/web/src/app/layout.tsx",                         "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",                           "typescript", _RECEPTION_PAGE.replace("__NAME__", name)),
        _f("apps/web/src/app/mascotas/page.tsx",                  "typescript", _PETS_PAGE),
        _f("apps/web/src/app/citas/page.tsx",                     "typescript", _APPOINTMENTS_PAGE),
        _f("apps/web/src/app/historia/page.tsx",                  "typescript", _HISTORY_PAGE),
        _f("apps/web/Dockerfile",                                 "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",                                    "nginx",      _NGINX),
        _f("docker-compose.yml",                                  "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                                        "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                                           "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
    ]
    return CodeGenerationResponse(project_name=name, files=files)


def _slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _f(path: str, lang: str, content: str) -> GeneratedFile:
    return GeneratedFile(path=path, language=lang, content=content)


_API_PKG = """{
  "name": "__SLUG__-api",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "db:push": "prisma db push",
    "db:migrate": "prisma migrate dev",
    "db:seed": "tsx prisma/seed.ts"
  },
  "dependencies": {
    "@fastify/cors": "^9.0.1",
    "@fastify/jwt": "^8.0.1",
    "@prisma/client": "^6.0.0",
    "@trpc/server": "^11.0.0",
    "bcryptjs": "^2.4.3",
    "fastify": "^5.0.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/bcryptjs": "^2.4.6",
    "@types/node": "^22.0.0",
    "prisma": "^6.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.6.0"
  }
}"""

_API_TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}"""

_API_INDEX = """import Fastify from 'fastify';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import { fastifyTRPCPlugin } from '@trpc/server/adapters/fastify';
import { appRouter } from './router';
import { createContext } from './trpc';

const server = Fastify({ logger: process.env.NODE_ENV !== 'production' });

await server.register(cors, { origin: process.env.CORS_ORIGIN ?? 'http://localhost:3000' });
await server.register(jwt, { secret: process.env.JWT_SECRET ?? 'dev-secret-change-me' });
await server.register(fastifyTRPCPlugin, {
  prefix: '/trpc',
  trpcOptions: { router: appRouter, createContext },
});

server.get('/health', async () => ({ status: 'ok', service: '__NAME__-api' }));

const port = Number(process.env.PORT ?? 4000);
await server.listen({ port, host: '0.0.0.0' });
console.log(`🐾 __NAME__ API running on port ${port}`);"""

_TRPC = """import { initTRPC, TRPCError } from '@trpc/server';
import type { FastifyRequest } from 'fastify';
import { PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient();

type Context = { req: FastifyRequest; userId?: string; userRole?: string };
export const createContext = async ({ req }: { req: FastifyRequest }): Promise<Context> => {
  const ctx: Context = { req };
  const auth = req.headers.authorization;
  if (auth?.startsWith('Bearer ')) {
    try {
      const payload = req.server.jwt.verify<{ sub: string; role: string }>(auth.slice(7));
      ctx.userId   = payload.sub;
      ctx.userRole = payload.role;
    } catch { /* invalid token */ }
  }
  return ctx;
};

const t = initTRPC.context<Context>().create();
export const router             = t.router;
export const publicProcedure    = t.procedure;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId) throw new TRPCError({ code: 'UNAUTHORIZED' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const vetProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'VET'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN')
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }        from './modules/auth/auth.router';
import { ownerRouter }       from './modules/owners/owner.router';
import { petRouter }         from './modules/pets/pet.router';
import { appointmentRouter } from './modules/appointments/appointment.router';
import { recordRouter }      from './modules/records/record.router';

export const appRouter = router({
  auth:         authRouter,
  owners:       ownerRouter,
  pets:         petRouter,
  appointments: appointmentRouter,
  records:      recordRouter,
});

export type AppRouter = typeof appRouter;"""

_PRISMA_SCHEMA = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum VetRole {
  ADMIN
  VET
  RECEPTIONIST
}

enum Species {
  DOG
  CAT
  RABBIT
  BIRD
  REPTILE
  OTHER
}

enum AppointmentType {
  CONSULTATION
  VACCINATION
  SURGERY
  GROOMING
  CHECKUP
  EMERGENCY
}

enum AppointmentStatus {
  SCHEDULED
  IN_PROGRESS
  COMPLETED
  CANCELLED
  NO_SHOW
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         VetRole   @default(RECEPTIONIST)
  phone        String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  appointments Appointment[]
  records      MedicalRecord[]
}

model Owner {
  id        String   @id @default(cuid())
  name      String
  email     String   @unique
  phone     String
  address   String?
  notes     String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  pets      Pet[]
}

model Pet {
  id         String    @id @default(cuid())
  ownerId    String
  owner      Owner     @relation(fields: [ownerId], references: [id], onDelete: Cascade)
  name       String
  species    Species
  breed      String?
  color      String?
  birthDate  DateTime?
  microchip  String?   @unique
  weight     Float?
  isActive   Boolean   @default(true)
  notes      String?
  createdAt  DateTime  @default(now())
  updatedAt  DateTime  @updatedAt
  appointments Appointment[]
  records    MedicalRecord[]
  vaccines   Vaccine[]
}

model Appointment {
  id          String            @id @default(cuid())
  petId       String
  pet         Pet               @relation(fields: [petId], references: [id])
  vetId       String
  vet         User              @relation(fields: [vetId], references: [id])
  type        AppointmentType
  status      AppointmentStatus @default(SCHEDULED)
  scheduledAt DateTime
  duration    Int               @default(30)
  reason      String?
  notes       String?
  createdAt   DateTime          @default(now())
  updatedAt   DateTime          @updatedAt
  record      MedicalRecord?
}

model MedicalRecord {
  id             String      @id @default(cuid())
  petId          String
  pet            Pet         @relation(fields: [petId], references: [id])
  vetId          String
  vet            User        @relation(fields: [vetId], references: [id])
  appointmentId  String?     @unique
  appointment    Appointment? @relation(fields: [appointmentId], references: [id])
  diagnosis      String
  treatment      String?
  prescription   String?
  weight         Float?
  temperature    Float?
  notes          String?
  followUpDate   DateTime?
  createdAt      DateTime    @default(now())
}

model Vaccine {
  id          String   @id @default(cuid())
  petId       String
  pet         Pet      @relation(fields: [petId], references: [id])
  name        String
  batch       String?
  administeredAt DateTime
  nextDueAt   DateTime?
  notes       String?
  createdAt   DateTime @default(now())
}"""

_SEED = """import { PrismaClient, VetRole, Species, AppointmentType } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Veterinaria...');

  const hash = await bcrypt.hash('password123', 10);

  const admin = await prisma.user.upsert({
    where: { email: 'admin@vetclinica.com' },
    update: {},
    create: { email: 'admin@vetclinica.com', name: 'Admin', passwordHash: hash, role: VetRole.ADMIN },
  });

  const vet1 = await prisma.user.upsert({
    where: { email: 'drlopez@vetclinica.com' },
    update: {},
    create: { email: 'drlopez@vetclinica.com', name: 'Dr. López', passwordHash: hash, role: VetRole.VET, phone: '600111222' },
  });

  const vet2 = await prisma.user.upsert({
    where: { email: 'drmartinez@vetclinica.com' },
    update: {},
    create: { email: 'drmartinez@vetclinica.com', name: 'Dra. Martínez', passwordHash: hash, role: VetRole.VET, phone: '600333444' },
  });

  await prisma.user.upsert({
    where: { email: 'recepcion@vetclinica.com' },
    update: {},
    create: { email: 'recepcion@vetclinica.com', name: 'Recepción', passwordHash: hash, role: VetRole.RECEPTIONIST },
  });

  // Owners
  const owner1 = await prisma.owner.create({
    data: { name: 'Ana García', email: 'ana@email.com', phone: '666111222', address: 'Calle Mayor 10' },
  });
  const owner2 = await prisma.owner.create({
    data: { name: 'Carlos Ruiz', email: 'carlos@email.com', phone: '677333444' },
  });

  // Pets
  const pet1 = await prisma.pet.create({
    data: { ownerId: owner1.id, name: 'Toby', species: Species.DOG, breed: 'Labrador', color: 'Dorado', birthDate: new Date('2020-03-15'), weight: 28.5, microchip: '941000024123456' },
  });
  const pet2 = await prisma.pet.create({
    data: { ownerId: owner1.id, name: 'Luna', species: Species.CAT, breed: 'Persa', color: 'Blanco', birthDate: new Date('2021-07-01'), weight: 4.2 },
  });
  const pet3 = await prisma.pet.create({
    data: { ownerId: owner2.id, name: 'Coco', species: Species.RABBIT, breed: 'Enano holandés', color: 'Gris', weight: 1.8 },
  });

  // Appointments
  const now = new Date();
  const todayAm = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 10, 0);
  const todayPm = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 16, 30);

  const appt1 = await prisma.appointment.create({
    data: { petId: pet1.id, vetId: vet1.id, type: AppointmentType.CHECKUP, scheduledAt: todayAm, reason: 'Revisión anual' },
  });
  await prisma.appointment.create({
    data: { petId: pet2.id, vetId: vet2.id, type: AppointmentType.VACCINATION, scheduledAt: todayPm, reason: 'Vacuna triple felina' },
  });

  // Medical record for pet1
  await prisma.medicalRecord.create({
    data: {
      petId: pet1.id, vetId: vet1.id, appointmentId: appt1.id,
      diagnosis: 'Animal sano. Sin hallazgos significativos.',
      treatment: 'Desparasitación interna y externa preventiva.',
      weight: 28.5, temperature: 38.5,
    },
  });

  // Vaccines
  await prisma.vaccine.createMany({
    data: [
      { petId: pet1.id, name: 'Rabia', administeredAt: new Date('2025-01-10'), nextDueAt: new Date('2026-01-10') },
      { petId: pet1.id, name: 'Polivalente canina (DHPP)', administeredAt: new Date('2025-01-10'), nextDueAt: new Date('2026-01-10') },
      { petId: pet2.id, name: 'Triple felina (RCP)', administeredAt: new Date('2025-06-01'), nextDueAt: new Date('2026-06-01') },
    ],
  });

  console.log('✅ Seed completado.');
  console.log('   Admin:      admin@vetclinica.com / password123');
  console.log('   Dr. López:  drlopez@vetclinica.com / password123');
  console.log('   Dra. Martínez: drmartinez@vetclinica.com / password123');
  console.log('   Recepción:  recepcion@vetclinica.com / password123');
}

main().catch(console.error).finally(() => prisma.$disconnect());"""

_AUTH_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';
import bcrypt from 'bcryptjs';

export const authRouter = router({
  login: publicProcedure
    .input(z.object({ email: z.string().email(), password: z.string() }))
    .mutation(async ({ input, ctx }) => {
      const user = await prisma.user.findUnique({ where: { email: input.email } });
      if (!user || !(await bcrypt.compare(input.password, user.passwordHash)))
        throw new Error('Credenciales incorrectas');
      const token = await ctx.req.server.jwt.sign({ sub: user.id, role: user.role }, { expiresIn: '12h' });
      return { token, user: { id: user.id, name: user.name, email: user.email, role: user.role } };
    }),

  me: protectedProcedure.query(({ ctx }) =>
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true } })
  ),

  staff: protectedProcedure.query(() =>
    prisma.user.findMany({ select: { id: true, name: true, role: true }, orderBy: { name: 'asc' } })
  ),
});"""

_OWNER_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const ownerRouter = router({
  list: protectedProcedure
    .input(z.object({ search: z.string().optional() }).optional())
    .query(({ input }) =>
      prisma.owner.findMany({
        where: input?.search ? { OR: [{ name: { contains: input.search, mode: 'insensitive' } }, { email: { contains: input.search, mode: 'insensitive' } }, { phone: { contains: input.search } }] } : undefined,
        include: { _count: { select: { pets: true } } },
        orderBy: { name: 'asc' },
      })
    ),

  byId: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.owner.findUnique({ where: { id: input }, include: { pets: { include: { _count: { select: { appointments: true } } } } } })
    ),

  create: protectedProcedure
    .input(z.object({ name: z.string().min(2), email: z.string().email(), phone: z.string().min(9), address: z.string().optional(), notes: z.string().optional() }))
    .mutation(({ input }) => prisma.owner.create({ data: input })),

  update: protectedProcedure
    .input(z.object({ id: z.string(), name: z.string().optional(), phone: z.string().optional(), address: z.string().optional(), notes: z.string().optional() }))
    .mutation(({ input: { id, ...data } }) => prisma.owner.update({ where: { id }, data })),
});"""

_PET_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const petRouter = router({
  list: protectedProcedure
    .input(z.object({ species: z.enum(['DOG', 'CAT', 'RABBIT', 'BIRD', 'REPTILE', 'OTHER']).optional() }).optional())
    .query(({ input }) =>
      prisma.pet.findMany({
        where: { isActive: true, ...(input?.species && { species: input.species }) },
        include: { owner: { select: { name: true, phone: true } }, _count: { select: { appointments: true } } },
        orderBy: { name: 'asc' },
      })
    ),

  byOwner: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.pet.findMany({ where: { ownerId: input, isActive: true }, include: { vaccines: { orderBy: { administeredAt: 'desc' } } } })
    ),

  byId: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.pet.findUnique({
        where: { id: input },
        include: { owner: true, vaccines: { orderBy: { administeredAt: 'desc' } }, records: { include: { vet: { select: { name: true } } }, orderBy: { createdAt: 'desc' } } },
      })
    ),

  create: protectedProcedure
    .input(z.object({
      ownerId:   z.string(),
      name:      z.string().min(1),
      species:   z.enum(['DOG', 'CAT', 'RABBIT', 'BIRD', 'REPTILE', 'OTHER']),
      breed:     z.string().optional(),
      color:     z.string().optional(),
      birthDate: z.string().optional(),
      microchip: z.string().optional(),
      weight:    z.number().positive().optional(),
      notes:     z.string().optional(),
    }))
    .mutation(({ input }) =>
      prisma.pet.create({ data: { ...input, birthDate: input.birthDate ? new Date(input.birthDate) : undefined } })
    ),

  addVaccine: protectedProcedure
    .input(z.object({ petId: z.string(), name: z.string().min(2), batch: z.string().optional(), administeredAt: z.string(), nextDueAt: z.string().optional(), notes: z.string().optional() }))
    .mutation(({ input }) =>
      prisma.vaccine.create({
        data: { ...input, administeredAt: new Date(input.administeredAt), nextDueAt: input.nextDueAt ? new Date(input.nextDueAt) : undefined },
      })
    ),
});"""

_APPOINTMENT_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const appointmentRouter = router({
  today: protectedProcedure.query(() => {
    const start = new Date(); start.setHours(0, 0, 0, 0);
    const end   = new Date(); end.setHours(23, 59, 59, 999);
    return prisma.appointment.findMany({
      where: { scheduledAt: { gte: start, lte: end } },
      include: { pet: { include: { owner: { select: { name: true, phone: true } } } }, vet: { select: { name: true } } },
      orderBy: { scheduledAt: 'asc' },
    });
  }),

  byDate: protectedProcedure
    .input(z.string())
    .query(({ input }) => {
      const date  = new Date(input);
      const start = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0);
      const end   = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59);
      return prisma.appointment.findMany({
        where: { scheduledAt: { gte: start, lte: end } },
        include: { pet: { include: { owner: { select: { name: true, phone: true } } } }, vet: { select: { name: true } } },
        orderBy: { scheduledAt: 'asc' },
      });
    }),

  byPet: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.appointment.findMany({
        where: { petId: input },
        include: { vet: { select: { name: true } }, record: true },
        orderBy: { scheduledAt: 'desc' },
      })
    ),

  create: protectedProcedure
    .input(z.object({
      petId:       z.string(),
      vetId:       z.string(),
      type:        z.enum(['CONSULTATION', 'VACCINATION', 'SURGERY', 'GROOMING', 'CHECKUP', 'EMERGENCY']),
      scheduledAt: z.string(),
      duration:    z.number().int().default(30),
      reason:      z.string().optional(),
    }))
    .mutation(({ input }) =>
      prisma.appointment.create({ data: { ...input, scheduledAt: new Date(input.scheduledAt) } })
    ),

  updateStatus: protectedProcedure
    .input(z.object({ id: z.string(), status: z.enum(['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW']) }))
    .mutation(({ input }) => prisma.appointment.update({ where: { id: input.id }, data: { status: input.status } })),
});"""

_RECORD_ROUTER = """import { z } from 'zod';
import { router, vetProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const recordRouter = router({
  byPet: vetProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.medicalRecord.findMany({
        where: { petId: input },
        include: { vet: { select: { name: true } }, appointment: { select: { type: true, scheduledAt: true } } },
        orderBy: { createdAt: 'desc' },
      })
    ),

  create: vetProcedure
    .input(z.object({
      petId:         z.string(),
      appointmentId: z.string().optional(),
      diagnosis:     z.string().min(5),
      treatment:     z.string().optional(),
      prescription:  z.string().optional(),
      weight:        z.number().positive().optional(),
      temperature:   z.number().optional(),
      notes:         z.string().optional(),
      followUpDate:  z.string().optional(),
    }))
    .mutation(({ input, ctx }) =>
      prisma.medicalRecord.create({
        data: { ...input, vetId: ctx.userId, followUpDate: input.followUpDate ? new Date(input.followUpDate) : undefined },
      })
    ),
});"""

_API_DOCKERFILE = """FROM node:22-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM base AS builder
COPY tsconfig.json ./
COPY src ./src
RUN npx tsc

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=base /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY prisma ./prisma
EXPOSE 4000
CMD ["node", "dist/index.js"]"""

_WEB_PKG = """{
  "name": "__SLUG__-web",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.56.2",
    "@trpc/client": "^11.0.0",
    "@trpc/next": "^11.0.0",
    "@trpc/react-query": "^11.0.0",
    "@trpc/server": "^11.0.0",
    "next": "^14.2.15",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "superjson": "^2.2.1",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3"
  }
}"""

_WEB_TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}"""

_NEXT_CONFIG = """/** @type {import('next').NextConfig} */
module.exports = { reactStrictMode: true };"""

_TAILWIND = """import type { Config } from 'tailwindcss';
const config: Config = { content: ['./src/**/*.{ts,tsx}'], theme: { extend: {} }, plugins: [] };
export default config;"""

_POSTCSS = """module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };"""

_GLOBALS_CSS = """@tailwind base;
@tailwind components;
@tailwind utilities;"""

_WEB_TRPC = """import { createTRPCReact } from '@trpc/react-query';
import type { AppRouter } from '../../apps/api/src/router';
export const trpc = createTRPCReact<AppRouter>();"""

_PROVIDER = """'use client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import { useState } from 'react';
import superjson from 'superjson';
import { trpc } from './trpc';
import { useAuthStore } from './auth-store';

export function TRPCProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token);
  const [queryClient] = useState(() => new QueryClient());
  const [trpcClient] = useState(() =>
    trpc.createClient({ links: [httpBatchLink({ url: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000/trpc', headers: () => token ? { Authorization: `Bearer ${token}` } : {}, transformer: superjson })] })
  );
  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </trpc.Provider>
  );
}"""

_AUTH_STORE = """import { create } from 'zustand';
import { persist } from 'zustand/middleware';
interface AuthState { token: string | null; user: { id: string; name: string; email: string; role: string } | null; login: (token: string, user: AuthState['user']) => void; logout: () => void; }
export const useAuthStore = create<AuthState>()(persist((set) => ({ token: null, user: null, login: (token, user) => set({ token, user }), logout: () => set({ token: null, user: null }) }), { name: 'auth-store' }));"""

_LAYOUT = """import type { Metadata } from 'next';
import { TRPCProvider } from '@/lib/provider';
import './globals.css';
export const metadata: Metadata = { title: '__NAME__', description: 'Clínica veterinaria' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-teal-50 text-stone-900">
        <TRPCProvider>
          <nav className="bg-white border-b px-6 py-3 flex items-center gap-6 shadow-sm">
            <span className="font-bold text-teal-700">🐾 __NAME__</span>
            <a href="/"         className="text-sm text-stone-600 hover:text-teal-700">Recepción</a>
            <a href="/mascotas" className="text-sm text-stone-600 hover:text-teal-700">Mascotas</a>
            <a href="/citas"    className="text-sm text-stone-600 hover:text-teal-700">Citas</a>
            <a href="/historia" className="text-sm text-stone-600 hover:text-teal-700">Historia clínica</a>
          </nav>
          {children}
        </TRPCProvider>
      </body>
    </html>
  );
}"""

_RECEPTION_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

const TYPE_LABELS: Record<string, string>  = { CONSULTATION: 'Consulta', VACCINATION: 'Vacuna', SURGERY: 'Cirugía', GROOMING: 'Peluquería', CHECKUP: 'Revisión', EMERGENCY: '🚨 Urgencia' };
const STATUS_COLORS: Record<string, string> = { SCHEDULED: 'bg-blue-100 text-blue-700', IN_PROGRESS: 'bg-amber-100 text-amber-700', COMPLETED: 'bg-green-100 text-green-700', CANCELLED: 'bg-red-100 text-red-700', NO_SHOW: 'bg-stone-100 text-stone-500' };
const STATUS_NEXT: Record<string, string>   = { SCHEDULED: 'IN_PROGRESS', IN_PROGRESS: 'COMPLETED' };
const STATUS_BTN: Record<string, string>    = { SCHEDULED: 'Iniciar', IN_PROGRESS: 'Completar' };

export default function RecepcionPage() {
  const { data, refetch } = trpc.appointments.today.useQuery();
  const update = trpc.appointments.updateStatus.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">🐾 Recepción — {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}</h1>
        <span className="rounded-full bg-teal-100 px-3 py-1 text-sm font-medium text-teal-700">{data?.length ?? 0} citas hoy</span>
      </div>

      <div className="space-y-3">
        {data?.map(a => (
          <div key={a.id} className="flex items-center gap-4 rounded-xl border bg-white p-4 shadow-sm">
            <div className="w-14 text-center">
              <p className="text-lg font-bold text-teal-700">{new Date(a.scheduledAt).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}</p>
              <p className="text-xs text-stone-400">{a.duration} min</p>
            </div>
            <div className="flex-1">
              <p className="font-semibold">{a.pet.name} <span className="text-sm font-normal text-stone-400">({a.pet.owner.name})</span></p>
              <p className="text-sm text-stone-500">{TYPE_LABELS[a.type]} · {a.vet.name}</p>
              {a.reason && <p className="text-xs text-stone-400 italic mt-0.5">{a.reason}</p>}
            </div>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[a.status]}`}>{a.status}</span>
            {STATUS_NEXT[a.status] && (
              <button onClick={() => update.mutate({ id: a.id, status: STATUS_NEXT[a.status] as any })}
                className="rounded-lg bg-teal-600 px-3 py-1.5 text-xs text-white hover:bg-teal-700">
                {STATUS_BTN[a.status]}
              </button>
            )}
          </div>
        ))}
        {data?.length === 0 && <p className="py-8 text-center text-stone-400">Sin citas para hoy.</p>}
      </div>
    </main>
  );
}"""

_PETS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const SPECIES_EMOJI: Record<string, string> = { DOG: '🐕', CAT: '🐈', RABBIT: '🐇', BIRD: '🦜', REPTILE: '🦎', OTHER: '🐾' };

export default function MascotasPage() {
  const [search, setSearch] = useState('');
  const { data } = trpc.pets.list.useQuery();

  const filtered = data?.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.owner.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Mascotas</h1>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por nombre o propietario..."
          className="ml-auto w-64 rounded-xl border px-4 py-2 text-sm" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered?.map(p => (
          <div key={p.id} className="rounded-xl border bg-white p-4 shadow-sm hover:shadow-md transition">
            <div className="mb-3 flex items-center gap-3">
              <span className="text-4xl">{SPECIES_EMOJI[p.species]}</span>
              <div>
                <p className="font-bold text-lg">{p.name}</p>
                <p className="text-xs text-stone-400">{p.species}{p.breed ? ` · ${p.breed}` : ''}</p>
              </div>
            </div>
            <div className="space-y-1 text-sm">
              <p className="text-stone-600">👤 {p.owner.name}</p>
              <p className="text-stone-400">📞 {p.owner.phone}</p>
              {p.weight && <p className="text-stone-500">⚖️ {p.weight} kg</p>}
              {p.birthDate && <p className="text-stone-500">🎂 {new Date(p.birthDate).toLocaleDateString('es-ES')}</p>}
            </div>
            <div className="mt-3 pt-3 border-t flex justify-between text-xs text-stone-400">
              <span>{p._count.appointments} visitas</span>
              {p.microchip && <span title="Microchip">🔖 {p.microchip.slice(-6)}</span>}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_APPOINTMENTS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const TYPE_LABELS: Record<string, string> = { CONSULTATION: 'Consulta', VACCINATION: 'Vacuna', SURGERY: 'Cirugía', GROOMING: 'Peluquería', CHECKUP: 'Revisión', EMERGENCY: 'Urgencia' };
const TYPE_COLORS: Record<string, string> = { CONSULTATION: 'bg-blue-50 text-blue-700', VACCINATION: 'bg-green-50 text-green-700', SURGERY: 'bg-red-50 text-red-700', GROOMING: 'bg-purple-50 text-purple-700', CHECKUP: 'bg-teal-50 text-teal-700', EMERGENCY: 'bg-red-100 text-red-800 font-bold' };
const STATUS_COLORS: Record<string, string> = { SCHEDULED: 'text-blue-600', IN_PROGRESS: 'text-amber-600', COMPLETED: 'text-green-600', CANCELLED: 'text-red-500', NO_SHOW: 'text-stone-400' };

export default function CitasPage() {
  const today = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(today);
  const { data, refetch } = trpc.appointments.byDate.useQuery(date);
  const update = trpc.appointments.updateStatus.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Agenda de citas</h1>
        <input type="date" value={date} onChange={e => setDate(e.target.value)}
          className="ml-auto rounded-xl border px-4 py-2 text-sm" />
      </div>

      <div className="space-y-3">
        {data?.map(a => (
          <div key={a.id} className="grid grid-cols-[5rem_1fr_auto] items-center gap-4 rounded-xl border bg-white p-4 shadow-sm">
            <div className="text-center">
              <p className="text-xl font-bold text-teal-700">{new Date(a.scheduledAt).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}</p>
              <p className="text-xs text-stone-400">{a.duration}min</p>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold">{a.pet.name}</p>
                <span className={`rounded-full px-2 py-0.5 text-xs ${TYPE_COLORS[a.type]}`}>{TYPE_LABELS[a.type]}</span>
              </div>
              <p className="text-sm text-stone-500">{a.pet.owner.name} · {a.vet.name}</p>
              {a.reason && <p className="text-xs text-stone-400 italic">{a.reason}</p>}
            </div>
            <div className="text-right">
              <p className={`text-xs font-semibold mb-1 ${STATUS_COLORS[a.status]}`}>{a.status}</p>
              {a.status === 'SCHEDULED' && (
                <button onClick={() => update.mutate({ id: a.id, status: 'IN_PROGRESS' })}
                  className="rounded-lg bg-amber-500 px-2 py-1 text-xs text-white hover:bg-amber-600">Iniciar</button>
              )}
              {a.status === 'IN_PROGRESS' && (
                <button onClick={() => update.mutate({ id: a.id, status: 'COMPLETED' })}
                  className="rounded-lg bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700">Completar</button>
              )}
            </div>
          </div>
        ))}
        {data?.length === 0 && <p className="py-8 text-center text-stone-400">Sin citas para este día.</p>}
      </div>
    </main>
  );
}"""

_HISTORY_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const SPECIES_EMOJI: Record<string, string> = { DOG: '🐕', CAT: '🐈', RABBIT: '🐇', BIRD: '🦜', REPTILE: '🦎', OTHER: '🐾' };

export default function HistoriaPage() {
  const { data: pets } = trpc.pets.list.useQuery();
  const [selectedPetId, setSelectedPetId] = useState<string | null>(null);
  const { data: records }  = trpc.records.byPet.useQuery(selectedPetId!, { enabled: !!selectedPetId });
  const { data: petDetail } = trpc.pets.byId.useQuery(selectedPetId!, { enabled: !!selectedPetId });

  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Historia clínica</h1>
      <div className="grid grid-cols-3 gap-6">
        {/* Pet selector */}
        <div className="col-span-1 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2">Mascotas</p>
          {pets?.map(p => (
            <button key={p.id} onClick={() => setSelectedPetId(p.id)}
              className={`w-full text-left rounded-xl border p-3 transition ${selectedPetId === p.id ? 'border-teal-500 bg-teal-50' : 'bg-white hover:bg-stone-50'}`}>
              <span className="mr-2">{SPECIES_EMOJI[p.species]}</span>
              <span className="font-medium">{p.name}</span>
              <p className="text-xs text-stone-400">{p.owner.name}</p>
            </button>
          ))}
        </div>

        {/* Records */}
        <div className="col-span-2">
          {!selectedPetId && <p className="text-stone-400 py-8 text-center">Selecciona una mascota</p>}
          {selectedPetId && (
            <>
              {/* Vaccines */}
              {petDetail?.vaccines && petDetail.vaccines.length > 0 && (
                <div className="mb-4 rounded-xl border bg-white p-4 shadow-sm">
                  <p className="mb-3 font-semibold text-teal-700">💉 Vacunas</p>
                  <div className="space-y-2">
                    {petDetail.vaccines.map(v => (
                      <div key={v.id} className="flex items-center justify-between text-sm">
                        <span className="font-medium">{v.name}</span>
                        <div className="text-right text-xs text-stone-400">
                          <p>Administrada: {new Date(v.administeredAt).toLocaleDateString('es-ES')}</p>
                          {v.nextDueAt && <p className="text-amber-600">Próxima: {new Date(v.nextDueAt).toLocaleDateString('es-ES')}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {/* Medical records */}
              <div className="space-y-3">
                {records?.map(r => (
                  <div key={r.id} className="rounded-xl border bg-white p-4 shadow-sm">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-xs text-stone-400">{new Date(r.createdAt).toLocaleDateString('es-ES', { dateStyle: 'medium' })} · {r.vet.name}</p>
                      {r.appointment && <span className="text-xs bg-stone-100 text-stone-600 rounded-full px-2 py-0.5">{r.appointment.type}</span>}
                    </div>
                    <p className="font-semibold text-stone-800">{r.diagnosis}</p>
                    {r.treatment    && <p className="text-sm text-stone-600 mt-1">Tratamiento: {r.treatment}</p>}
                    {r.prescription && <p className="text-sm text-teal-700 mt-1">💊 {r.prescription}</p>}
                    <div className="mt-2 flex gap-4 text-xs text-stone-400">
                      {r.weight      && <span>⚖️ {r.weight} kg</span>}
                      {r.temperature && <span>🌡️ {r.temperature}°C</span>}
                    </div>
                  </div>
                ))}
                {records?.length === 0 && <p className="text-stone-400 py-4 text-center">Sin registros médicos.</p>}
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}"""

_WEB_DOCKERFILE = """FROM node:22-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM base AS builder
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]"""

_NGINX = """events { worker_connections 1024; }
http {
  upstream api { server api:4000; }
  upstream web { server web:3000; }
  server {
    listen 80;
    location /trpc { proxy_pass http://api; }
    location /health { proxy_pass http://api; }
    location / { proxy_pass http://web; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection 'upgrade'; }
  }
}"""

_DOCKER_COMPOSE = """services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: vetclinica
      POSTGRES_PASSWORD: vet_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://vetclinica:vet_pass@postgres:5432/__SLUG___db
      JWT_SECRET: change-me-in-production
      CORS_ORIGIN: http://localhost:3000
    ports: ["4000:4000"]

  web:
    build: ./apps/web
    depends_on: [api]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:4000/trpc
    ports: ["3000:3000"]

  nginx:
    image: nginx:alpine
    depends_on: [api, web]
    ports: ["80:80"]
    volumes: [./nginx/nginx.conf:/etc/nginx/nginx.conf:ro]

volumes:
  postgres_data:"""

_ENV = """DATABASE_URL="postgresql://vetclinica:vet_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Clínica Veterinaria

Sistema de gestión de clínica veterinaria: propietarios, mascotas, citas, historia clínica y vacunas.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, VET, RECEPTIONIST)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Recepción | Agenda diaria con flujo de estados: SCHEDULED → IN_PROGRESS → COMPLETED |
| Mascotas | Registro con especie, raza, microchip, peso y propietario asociado |
| Citas | Vista por fecha con cambio de estado inline |
| Historia clínica | Registros médicos por mascota + calendario de vacunas con próxima dosis |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin:   admin@vetclinica.com / password123
Vets:    drlopez@vetclinica.com / drmartinez@vetclinica.com / password123
"""
