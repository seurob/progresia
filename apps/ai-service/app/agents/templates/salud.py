"""
SALUD template — sistema de gestión de clínica/consulta médica.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: pacientes, doctores, citas, historial médico.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",               "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",               "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",                "typescript", _API_INDEX.replace("__NAME__", name)),
        _f("apps/api/src/trpc.ts",                 "typescript", _TRPC),
        _f("apps/api/src/router.ts",               "typescript", _ROUTER),
        _f("apps/api/prisma/schema.prisma",        "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",              "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",              "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/patients/patient.router.ts",       "typescript", _PATIENT_ROUTER),
        _f("apps/api/src/modules/doctors/doctor.router.ts",         "typescript", _DOCTOR_ROUTER),
        _f("apps/api/src/modules/appointments/appointment.router.ts", "typescript", _APPT_ROUTER),
        _f("apps/api/src/modules/records/record.router.ts",         "typescript", _RECORD_ROUTER),
        _f("apps/api/Dockerfile",                  "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",                "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",               "json",       _WEB_TSCONFIG),
        _f("apps/web/next.config.js",              "javascript", _NEXT_CONFIG),
        _f("apps/web/tailwind.config.ts",          "typescript", _TAILWIND),
        _f("apps/web/postcss.config.js",           "javascript", _POSTCSS_CONFIG),
        _f("apps/web/src/app/globals.css",         "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",             "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",        "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts",       "typescript", _AUTH_STORE),
        _f("apps/web/src/app/layout.tsx",          "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",            "typescript", _LANDING.replace("__NAME__", name)),
        _f("apps/web/src/app/pacientes/page.tsx",  "typescript", _PATIENTS_PAGE),
        _f("apps/web/src/app/citas/page.tsx",      "typescript", _APPTS_PAGE),
        _f("apps/web/Dockerfile",                  "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",                     "nginx",      _NGINX),
        _f("docker-compose.yml",                   "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                         "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                            "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
    ]
    return CodeGenerationResponse(project_name=name, files=files)


def _slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _f(path: str, lang: str, content: str) -> GeneratedFile:
    return GeneratedFile(path=path, language=lang, content=content)


# ── API package.json ──────────────────────────────────────────────────────────

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
    "db:seed": "tsx prisma/seed.ts",
    "db:studio": "prisma studio"
  },
  "dependencies": {
    "@fastify/cors": "^9.0.1",
    "@fastify/jwt": "^8.0.1",
    "@prisma/client": "^6.0.0",
    "@trpc/server": "^11.0.0",
    "fastify": "^5.0.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
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
console.log(`🏥 __NAME__ API running on port ${port}`);"""

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
export const router = t.router;
export const publicProcedure = t.procedure;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId) throw new TRPCError({ code: 'UNAUTHORIZED' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const doctorProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['DOCTOR', 'ADMIN'].includes(ctx.userRole ?? '')) throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter } from './modules/auth/auth.router';
import { patientRouter } from './modules/patients/patient.router';
import { doctorRouter } from './modules/doctors/doctor.router';
import { appointmentRouter } from './modules/appointments/appointment.router';
import { recordRouter } from './modules/records/record.router';

export const appRouter = router({
  auth:         authRouter,
  patients:     patientRouter,
  doctors:      doctorRouter,
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

enum UserRole {
  ADMIN
  DOCTOR
  RECEPTIONIST
  PATIENT
}

enum AppointmentStatus {
  SCHEDULED
  CONFIRMED
  COMPLETED
  CANCELLED
  NO_SHOW
}

enum Specialty {
  GENERAL
  PEDIATRICS
  CARDIOLOGY
  DERMATOLOGY
  NEUROLOGY
  ORTHOPEDICS
  PSYCHIATRY
}

model User {
  id           String   @id @default(cuid())
  email        String   @unique
  name         String
  passwordHash String
  role         UserRole @default(PATIENT)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  doctor       Doctor?
  patient      Patient?
}

model Doctor {
  id           String       @id @default(cuid())
  userId       String       @unique
  user         User         @relation(fields: [userId], references: [id])
  specialty    Specialty
  licenseNumber String      @unique
  bio          String?
  phone        String?
  createdAt    DateTime     @default(now())
  appointments Appointment[]
  records      MedicalRecord[]
}

model Patient {
  id           String      @id @default(cuid())
  userId       String      @unique
  user         User        @relation(fields: [userId], references: [id])
  birthDate    DateTime
  gender       String?
  phone        String?
  address      String?
  allergies    String[]
  bloodType    String?
  createdAt    DateTime    @default(now())
  updatedAt    DateTime    @updatedAt
  appointments Appointment[]
  records      MedicalRecord[]
}

model Appointment {
  id          String            @id @default(cuid())
  patientId   String
  patient     Patient           @relation(fields: [patientId], references: [id])
  doctorId    String
  doctor      Doctor            @relation(fields: [doctorId], references: [id])
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
  id            String      @id @default(cuid())
  patientId     String
  patient       Patient     @relation(fields: [patientId], references: [id])
  doctorId      String
  doctor        Doctor      @relation(fields: [doctorId], references: [id])
  appointmentId String?     @unique
  appointment   Appointment? @relation(fields: [appointmentId], references: [id])
  diagnosis     String
  treatment     String?
  prescription  String?
  observations  String?
  createdAt     DateTime    @default(now())
  updatedAt     DateTime    @updatedAt
}"""

_SEED = """import { PrismaClient, UserRole, Specialty, AppointmentStatus } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Salud...');

  const hash = await bcrypt.hash('password123', 10);

  const adminUser = await prisma.user.upsert({
    where:  { email: 'admin@clinica.com' },
    update: {},
    create: { email: 'admin@clinica.com', name: 'Administrador', passwordHash: hash, role: UserRole.ADMIN },
  });

  const drUser = await prisma.user.upsert({
    where:  { email: 'dr.garcia@clinica.com' },
    update: {},
    create: { email: 'dr.garcia@clinica.com', name: 'Dr. Carlos García', passwordHash: hash, role: UserRole.DOCTOR },
  });

  const doctor = await prisma.doctor.upsert({
    where:  { userId: drUser.id },
    update: {},
    create: { userId: drUser.id, specialty: Specialty.GENERAL, licenseNumber: 'COL-1234', bio: 'Médico de familia con 15 años de experiencia.' },
  });

  const patUser = await prisma.user.upsert({
    where:  { email: 'paciente@example.com' },
    update: {},
    create: { email: 'paciente@example.com', name: 'María López', passwordHash: hash, role: UserRole.PATIENT },
  });

  const patient = await prisma.patient.upsert({
    where:  { userId: patUser.id },
    update: {},
    create: { userId: patUser.id, birthDate: new Date('1990-05-15'), gender: 'Femenino', bloodType: 'A+', allergies: ['Penicilina'] },
  });

  const appt = await prisma.appointment.create({
    data: {
      patientId:   patient.id,
      doctorId:    doctor.id,
      scheduledAt: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
      reason:      'Revisión anual',
      status:      AppointmentStatus.CONFIRMED,
    },
  });

  console.log('✅ Seed completado. Admin: admin@clinica.com / password123');
  console.log(`   Doctor: dr.garcia@clinica.com | Paciente: paciente@example.com`);
  console.log(`   Cita programada ID: ${appt.id}`);
}

main().catch(console.error).finally(() => prisma.$disconnect());"""

_AUTH_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';
import bcrypt from 'bcryptjs';

export const authRouter = router({
  login: publicProcedure
    .input(z.object({ email: z.string().email(), password: z.string().min(6) }))
    .mutation(async ({ input, ctx }) => {
      const user = await prisma.user.findUnique({ where: { email: input.email } });
      if (!user || !(await bcrypt.compare(input.password, user.passwordHash))) {
        throw new Error('Credenciales incorrectas');
      }
      const token = await ctx.req.server.jwt.sign({ sub: user.id, role: user.role }, { expiresIn: '7d' });
      return { token, user: { id: user.id, name: user.name, email: user.email, role: user.role } };
    }),

  me: protectedProcedure.query(async ({ ctx }) =>
    prisma.user.findUnique({
      where:  { id: ctx.userId },
      select: { id: true, name: true, email: true, role: true, doctor: { include: { _count: { select: { appointments: true } } } }, patient: true },
    })
  ),
});"""

_PATIENT_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, doctorProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const patientRouter = router({
  list: doctorProcedure.query(() =>
    prisma.patient.findMany({ include: { user: { select: { name: true, email: true } } }, orderBy: { user: { name: 'asc' } } })
  ),

  getById: doctorProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.patient.findUnique({
        where:   { id: input },
        include: { user: { select: { name: true, email: true } }, appointments: { orderBy: { scheduledAt: 'desc' }, take: 5 }, records: { orderBy: { createdAt: 'desc' }, take: 10 } },
      })
    ),

  myProfile: protectedProcedure.query(async ({ ctx }) =>
    prisma.patient.findUnique({
      where:   { userId: ctx.userId },
      include: { user: { select: { name: true, email: true } }, appointments: { orderBy: { scheduledAt: 'desc' }, take: 10, include: { doctor: { include: { user: { select: { name: true } } } } } } },
    })
  ),

  update: doctorProcedure
    .input(z.object({
      id:        z.string(),
      allergies: z.string().array().optional(),
      bloodType: z.string().optional(),
      phone:     z.string().optional(),
      address:   z.string().optional(),
    }))
    .mutation(({ input: { id, ...data } }) => prisma.patient.update({ where: { id }, data })),
});"""

_DOCTOR_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const doctorRouter = router({
  list: publicProcedure.query(() =>
    prisma.doctor.findMany({
      include: { user: { select: { name: true } }, _count: { select: { appointments: true } } },
      orderBy: { user: { name: 'asc' } },
    })
  ),

  getBySpecialty: publicProcedure
    .input(z.enum(['GENERAL', 'PEDIATRICS', 'CARDIOLOGY', 'DERMATOLOGY', 'NEUROLOGY', 'ORTHOPEDICS', 'PSYCHIATRY']))
    .query(({ input }) =>
      prisma.doctor.findMany({
        where:   { specialty: input },
        include: { user: { select: { name: true } } },
      })
    ),
});"""

_APPT_ROUTER = """import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, protectedProcedure, doctorProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const appointmentRouter = router({
  book: protectedProcedure
    .input(z.object({
      doctorId:    z.string(),
      scheduledAt: z.string(),
      reason:      z.string().optional(),
    }))
    .mutation(async ({ input, ctx }) => {
      const patient = await prisma.patient.findUnique({ where: { userId: ctx.userId } });
      if (!patient) throw new TRPCError({ code: 'NOT_FOUND', message: 'Perfil de paciente no encontrado' });
      return prisma.appointment.create({
        data: { ...input, patientId: patient.id, scheduledAt: new Date(input.scheduledAt) },
      });
    }),

  myAppointments: protectedProcedure.query(async ({ ctx }) => {
    const patient = await prisma.patient.findUnique({ where: { userId: ctx.userId } });
    if (!patient) return [];
    return prisma.appointment.findMany({
      where:   { patientId: patient.id },
      include: { doctor: { include: { user: { select: { name: true } } } } },
      orderBy: { scheduledAt: 'desc' },
    });
  }),

  doctorAgenda: doctorProcedure.query(async ({ ctx }) => {
    const doctor = await prisma.doctor.findUnique({ where: { userId: ctx.userId } });
    if (!doctor) return [];
    return prisma.appointment.findMany({
      where:   { doctorId: doctor.id, scheduledAt: { gte: new Date() } },
      include: { patient: { include: { user: { select: { name: true } } } } },
      orderBy: { scheduledAt: 'asc' },
    });
  }),

  updateStatus: doctorProcedure
    .input(z.object({
      id:     z.string(),
      status: z.enum(['CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW']),
      notes:  z.string().optional(),
    }))
    .mutation(({ input: { id, ...data } }) =>
      prisma.appointment.update({ where: { id }, data })
    ),
});"""

_RECORD_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, doctorProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const recordRouter = router({
  create: doctorProcedure
    .input(z.object({
      patientId:     z.string(),
      appointmentId: z.string().optional(),
      diagnosis:     z.string().min(3),
      treatment:     z.string().optional(),
      prescription:  z.string().optional(),
      observations:  z.string().optional(),
    }))
    .mutation(async ({ input, ctx }) => {
      const doctor = await prisma.doctor.findUnique({ where: { userId: ctx.userId } });
      if (!doctor) throw new Error('Doctor no encontrado');
      return prisma.medicalRecord.create({ data: { ...input, doctorId: doctor.id } });
    }),

  patientHistory: doctorProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.medicalRecord.findMany({
        where:   { patientId: input },
        include: { doctor: { include: { user: { select: { name: true } } } }, appointment: true },
        orderBy: { createdAt: 'desc' },
      })
    ),

  myHistory: protectedProcedure.query(async ({ ctx }) => {
    const patient = await prisma.patient.findUnique({ where: { userId: ctx.userId } });
    if (!patient) return [];
    return prisma.medicalRecord.findMany({
      where:   { patientId: patient.id },
      include: { doctor: { include: { user: { select: { name: true } } } } },
      orderBy: { createdAt: 'desc' },
    });
  }),
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
const nextConfig = { reactStrictMode: true };
module.exports = nextConfig;"""

_TAILWIND = """import type { Config } from 'tailwindcss';
const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
};
export default config;"""

_POSTCSS_CONFIG = """module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };"""

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
    trpc.createClient({
      links: [httpBatchLink({
        url: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000/trpc',
        headers: () => token ? { Authorization: `Bearer ${token}` } : {},
        transformer: superjson,
      })],
    })
  );
  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </trpc.Provider>
  );
}"""

_AUTH_STORE = """import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user:  { id: string; name: string; email: string; role: string } | null;
  login:  (token: string, user: AuthState['user']) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token:  null,
      user:   null,
      login:  (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-store' }
  )
);"""

_LAYOUT = """import type { Metadata } from 'next';
import { TRPCProvider } from '@/lib/provider';
import './globals.css';

export const metadata: Metadata = { title: '__NAME__', description: 'Sistema de Gestión Clínica' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <TRPCProvider>{children}</TRPCProvider>
      </body>
    </html>
  );
}"""

_LANDING = """'use client';
import { useAuthStore } from '@/lib/auth-store';
import { trpc } from '@/lib/trpc';
import Link from 'next/link';

export default function HomePage() {
  const user = useAuthStore(s => s.user);
  const { data: doctors } = trpc.doctors.list.useQuery();

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-2 text-3xl font-bold text-teal-700">__NAME__</h1>
      <p className="mb-8 text-slate-500">Portal de Gestión Clínica</p>

      {!user ? (
        <div className="flex gap-4">
          <Link href="/login" className="rounded-lg bg-teal-600 px-6 py-3 text-white hover:bg-teal-700">
            Iniciar sesión
          </Link>
          <Link href="/citas/nueva" className="rounded-lg border px-6 py-3 hover:bg-slate-100">
            Pedir cita
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <p className="text-sm text-slate-500">Médicos disponibles</p>
            <p className="mt-1 text-4xl font-bold text-teal-600">{doctors?.length ?? '—'}</p>
          </div>
          <Link href="/pacientes" className="rounded-xl border bg-white p-6 shadow-sm hover:shadow-md">
            <p className="font-semibold">Gestionar pacientes →</p>
          </Link>
          <Link href="/citas" className="rounded-xl border bg-white p-6 shadow-sm hover:shadow-md">
            <p className="font-semibold">Agenda de citas →</p>
          </Link>
        </div>
      )}

      <section className="mt-12">
        <h2 className="mb-4 text-lg font-semibold">Nuestro equipo médico</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {doctors?.map(d => (
            <div key={d.id} className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="font-medium">{d.user.name}</p>
              <p className="text-sm text-slate-500">{d.specialty}</p>
              <p className="mt-1 text-xs text-slate-400">{d._count.appointments} citas realizadas</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}"""

_PATIENTS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

export default function PacientesPage() {
  const { data, isLoading } = trpc.patients.list.useQuery();

  if (isLoading) return <p className="p-8 text-slate-400">Cargando pacientes...</p>;

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Pacientes</h1>
      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Tipo sanguíneo</th>
              <th className="px-4 py-3">Alergias</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.map(p => (
              <tr key={p.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium">{p.user.name}</td>
                <td className="px-4 py-3 text-slate-500">{p.user.email}</td>
                <td className="px-4 py-3">{p.bloodType ?? '—'}</td>
                <td className="px-4 py-3">
                  {p.allergies.length > 0
                    ? p.allergies.map(a => <span key={a} className="mr-1 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">{a}</span>)
                    : <span className="text-slate-400">Ninguna</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}"""

_APPTS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const STATUS_LABELS: Record<string, string> = {
  SCHEDULED: 'Programada', CONFIRMED: 'Confirmada', COMPLETED: 'Completada',
  CANCELLED: 'Cancelada', NO_SHOW: 'No presentado',
};
const STATUS_COLOR: Record<string, string> = {
  SCHEDULED: 'bg-yellow-100 text-yellow-700', CONFIRMED: 'bg-teal-100 text-teal-700',
  COMPLETED: 'bg-green-100 text-green-700', CANCELLED: 'bg-red-100 text-red-700',
  NO_SHOW: 'bg-slate-100 text-slate-600',
};

export default function CitasPage() {
  const user = useAuthStore(s => s.user);
  const isDoctor = user?.role === 'DOCTOR' || user?.role === 'ADMIN';
  const { data: doctorAppts } = trpc.appointments.doctorAgenda.useQuery(undefined, { enabled: isDoctor });
  const { data: myAppts }     = trpc.appointments.myAppointments.useQuery(undefined, { enabled: !isDoctor });

  const appts = isDoctor ? doctorAppts : myAppts;

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="mb-6 text-2xl font-bold">{isDoctor ? 'Mi agenda' : 'Mis citas'}</h1>
      <div className="space-y-3">
        {appts?.map(a => (
          <div key={a.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm">
            <div>
              <p className="font-medium">
                {isDoctor
                  ? (a as any).patient?.user?.name
                  : (a as any).doctor?.user?.name}
              </p>
              <p className="text-xs text-slate-500">
                {new Date(a.scheduledAt).toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' })}
                {a.reason ? ` · ${a.reason}` : ''}
              </p>
            </div>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLOR[a.status] ?? ''}`}>
              {STATUS_LABELS[a.status] ?? a.status}
            </span>
          </div>
        ))}
        {(!appts || appts.length === 0) && <p className="text-slate-400">No hay citas programadas.</p>}
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
      POSTGRES_USER: salud
      POSTGRES_PASSWORD: salud_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://salud:salud_pass@postgres:5432/__SLUG___db
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

_ENV = """# Base de datos
DATABASE_URL="postgresql://salud:salud_pass@localhost:5432/__SLUG___db"

# Auth
JWT_SECRET="change-me-in-production-use-a-long-random-string"

# API
PORT=4000
CORS_ORIGIN="http://localhost:3000"

# Web
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Sistema de Gestión Clínica

Portal para gestión de pacientes, doctores, citas médicas e historiales clínicos.

## Stack

- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, DOCTOR, RECEPTIONIST, PATIENT)
- **Infra:** Docker Compose · nginx

## Módulos incluidos

| Módulo | Funcionalidad |
|--------|---------------|
| Pacientes | Perfil, alergias, tipo sanguíneo, historial |
| Doctores | Especialidad, número de colegiado, agenda |
| Citas | Programar, confirmar, cancelar, marcar completada |
| Historial médico | Diagnóstico, tratamiento, receta, observaciones |

## Inicio rápido

```bash
# 1. Clonar e instalar
git clone <url> __SLUG__ && cd __SLUG__
npm install

# 2. Variables de entorno
cp .env.example .env

# 3. Base de datos y seed
docker compose up -d postgres
npx prisma migrate dev
npx prisma db seed

# 4. Arrancar todo
docker compose up --build
```

Accede en `http://localhost`.

**Admin demo:** admin@clinica.com / password123
**Doctor demo:** dr.garcia@clinica.com / password123
**Paciente demo:** paciente@example.com / password123
"""
