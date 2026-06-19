"""
RRHH template — sistema de gestión de recursos humanos.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: empleados, departamentos, solicitudes de ausencia, nóminas.
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
        _f("apps/api/src/lib/auth.ts",             "typescript", _LIB_AUTH),
        _f("apps/api/prisma/schema.prisma",        "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",              "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",           "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/employees/employee.router.ts",  "typescript", _EMPLOYEE_ROUTER),
        _f("apps/api/src/modules/departments/department.router.ts", "typescript", _DEPT_ROUTER),
        _f("apps/api/src/modules/leaves/leave.router.ts",        "typescript", _LEAVE_ROUTER),
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
        _f("apps/web/src/app/empleados/page.tsx",  "typescript", _EMPLOYEES_PAGE),
        _f("apps/web/src/app/ausencias/page.tsx",  "typescript", _LEAVES_PAGE),
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
console.log(`🚀 __NAME__ API running on port ${port}`);"""

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
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN') throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter } from './modules/auth/auth.router';
import { employeeRouter } from './modules/employees/employee.router';
import { departmentRouter } from './modules/departments/department.router';
import { leaveRouter } from './modules/leaves/leave.router';

export const appRouter = router({
  auth:       authRouter,
  employees:  employeeRouter,
  departments: departmentRouter,
  leaves:     leaveRouter,
});

export type AppRouter = typeof appRouter;"""

_LIB_AUTH = """import { TRPCError } from '@trpc/server';
import { prisma } from '../trpc';

export async function hashPassword(password: string): Promise<string> {
  const bcrypt = await import('bcryptjs');
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  const bcrypt = await import('bcryptjs');
  return bcrypt.compare(password, hash);
}

export async function findUserByEmail(email: string) {
  return prisma.user.findUnique({ where: { email } });
}"""

_PRISMA_SCHEMA = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum Role {
  ADMIN
  HR_MANAGER
  EMPLOYEE
}

enum LeaveType {
  VACATION
  SICK
  PERSONAL
  MATERNITY_PATERNITY
}

enum LeaveStatus {
  PENDING
  APPROVED
  REJECTED
}

model User {
  id           String   @id @default(cuid())
  email        String   @unique
  name         String
  passwordHash String
  role         Role     @default(EMPLOYEE)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  employee     Employee?
}

model Department {
  id          String     @id @default(cuid())
  name        String     @unique
  description String?
  managerId   String?
  createdAt   DateTime   @default(now())
  employees   Employee[]
}

model Employee {
  id           String      @id @default(cuid())
  userId       String      @unique
  user         User        @relation(fields: [userId], references: [id])
  departmentId String?
  department   Department? @relation(fields: [departmentId], references: [id])
  position     String
  startDate    DateTime
  salary       Decimal?    @db.Decimal(10, 2)
  phone        String?
  address      String?
  createdAt    DateTime    @default(now())
  updatedAt    DateTime    @updatedAt
  leaves       LeaveRequest[]
}

model LeaveRequest {
  id         String      @id @default(cuid())
  employeeId String
  employee   Employee    @relation(fields: [employeeId], references: [id])
  type       LeaveType
  status     LeaveStatus @default(PENDING)
  startDate  DateTime
  endDate    DateTime
  reason     String?
  reviewedBy String?
  reviewedAt DateTime?
  createdAt  DateTime    @default(now())
  updatedAt  DateTime    @updatedAt
}"""

_SEED = """import { PrismaClient, Role, LeaveType, LeaveStatus } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ RRHH...');

  const engineering = await prisma.department.upsert({
    where:  { name: 'Ingeniería' },
    update: {},
    create: { name: 'Ingeniería', description: 'Desarrollo de producto y tecnología' },
  });

  const marketing = await prisma.department.upsert({
    where:  { name: 'Marketing' },
    update: {},
    create: { name: 'Marketing', description: 'Marketing, comunicación y crecimiento' },
  });

  const hash = await bcrypt.hash('password123', 10);

  const adminUser = await prisma.user.upsert({
    where:  { email: 'admin@empresa.com' },
    update: {},
    create: { email: 'admin@empresa.com', name: 'Admin RRHH', passwordHash: hash, role: Role.ADMIN },
  });

  await prisma.employee.upsert({
    where:  { userId: adminUser.id },
    update: {},
    create: { userId: adminUser.id, departmentId: engineering.id, position: 'CTO', startDate: new Date('2022-01-10') },
  });

  const emp1 = await prisma.user.upsert({
    where:  { email: 'ana@empresa.com' },
    update: {},
    create: { email: 'ana@empresa.com', name: 'Ana García', passwordHash: hash, role: Role.EMPLOYEE },
  });

  const emp1Employee = await prisma.employee.upsert({
    where:  { userId: emp1.id },
    update: {},
    create: { userId: emp1.id, departmentId: engineering.id, position: 'Frontend Developer', startDate: new Date('2023-03-01'), salary: 45000 },
  });

  await prisma.leaveRequest.create({
    data: {
      employeeId: emp1Employee.id,
      type:       LeaveType.VACATION,
      status:     LeaveStatus.APPROVED,
      startDate:  new Date('2025-08-04'),
      endDate:    new Date('2025-08-15'),
      reason:     'Vacaciones de verano',
    },
  });

  console.log('✅ Seed completado. Admin: admin@empresa.com / password123');
}

main().catch(console.error).finally(() => prisma.$disconnect());"""

_AUTH_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../../trpc';
import { findUserByEmail, verifyPassword } from '../../lib/auth';

export const authRouter = router({
  login: publicProcedure
    .input(z.object({ email: z.string().email(), password: z.string().min(6) }))
    .mutation(async ({ input, ctx }) => {
      const user = await findUserByEmail(input.email);
      if (!user || !(await verifyPassword(input.password, user.passwordHash))) {
        throw new Error('Credenciales incorrectas');
      }
      const token = await ctx.req.server.jwt.sign({ sub: user.id, role: user.role }, { expiresIn: '7d' });
      return { token, user: { id: user.id, name: user.name, email: user.email, role: user.role } };
    }),

  me: protectedProcedure
    .query(async ({ ctx }) => {
      const { prisma } = await import('../../trpc');
      return prisma.user.findUnique({
        where:  { id: ctx.userId },
        select: { id: true, name: true, email: true, role: true, employee: { include: { department: true } } },
      });
    }),
});"""

_EMPLOYEE_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const employeeRouter = router({
  list: protectedProcedure.query(() =>
    prisma.employee.findMany({ include: { user: { select: { id: true, name: true, email: true, role: true } }, department: true }, orderBy: { user: { name: 'asc' } } })
  ),

  getById: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.employee.findUnique({ where: { id: input }, include: { user: true, department: true, leaves: { orderBy: { createdAt: 'desc' }, take: 10 } } })
    ),

  update: adminProcedure
    .input(z.object({
      id:           z.string(),
      position:     z.string().optional(),
      departmentId: z.string().optional(),
      salary:       z.number().optional(),
      phone:        z.string().optional(),
    }))
    .mutation(({ input: { id, ...data } }) =>
      prisma.employee.update({ where: { id }, data })
    ),
});"""

_DEPT_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const departmentRouter = router({
  list: protectedProcedure.query(() =>
    prisma.department.findMany({ include: { _count: { select: { employees: true } } }, orderBy: { name: 'asc' } })
  ),

  create: adminProcedure
    .input(z.object({ name: z.string().min(2), description: z.string().optional() }))
    .mutation(({ input }) => prisma.department.create({ data: input })),

  update: adminProcedure
    .input(z.object({ id: z.string(), name: z.string().optional(), description: z.string().optional() }))
    .mutation(({ input: { id, ...data } }) => prisma.department.update({ where: { id }, data })),

  delete: adminProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.department.delete({ where: { id: input } })),
});"""

_LEAVE_ROUTER = """import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, protectedProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const leaveRouter = router({
  myLeaves: protectedProcedure.query(async ({ ctx }) => {
    const emp = await prisma.employee.findUnique({ where: { userId: ctx.userId } });
    if (!emp) throw new TRPCError({ code: 'NOT_FOUND' });
    return prisma.leaveRequest.findMany({ where: { employeeId: emp.id }, orderBy: { createdAt: 'desc' } });
  }),

  allLeaves: adminProcedure.query(() =>
    prisma.leaveRequest.findMany({ include: { employee: { include: { user: { select: { name: true } } } } }, orderBy: { createdAt: 'desc' } })
  ),

  request: protectedProcedure
    .input(z.object({
      type:      z.enum(['VACATION', 'SICK', 'PERSONAL', 'MATERNITY_PATERNITY']),
      startDate: z.string(),
      endDate:   z.string(),
      reason:    z.string().optional(),
    }))
    .mutation(async ({ input, ctx }) => {
      const emp = await prisma.employee.findUnique({ where: { userId: ctx.userId } });
      if (!emp) throw new TRPCError({ code: 'NOT_FOUND' });
      return prisma.leaveRequest.create({
        data: { ...input, employeeId: emp.id, startDate: new Date(input.startDate), endDate: new Date(input.endDate) },
      });
    }),

  review: adminProcedure
    .input(z.object({ id: z.string(), status: z.enum(['APPROVED', 'REJECTED']) }))
    .mutation(async ({ input, ctx }) =>
      prisma.leaveRequest.update({ where: { id: input.id }, data: { status: input.status, reviewedBy: ctx.userId, reviewedAt: new Date() } })
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
const nextConfig = {
  reactStrictMode: true,
};
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

export const metadata: Metadata = { title: '__NAME__', description: 'Sistema de Gestión de RRHH' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-gray-50 text-gray-900">
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
  const { data: employees } = trpc.employees.list.useQuery(undefined, { enabled: !!user });

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-2 text-3xl font-bold text-blue-700">__NAME__</h1>
      <p className="mb-8 text-gray-500">Portal de Recursos Humanos</p>

      {!user ? (
        <div className="flex gap-4">
          <Link href="/login" className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700">
            Iniciar sesión
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Empleados activos</p>
            <p className="mt-1 text-4xl font-bold text-blue-600">{employees?.length ?? '—'}</p>
          </div>
          <Link href="/empleados" className="rounded-xl border bg-white p-6 shadow-sm hover:shadow-md">
            <p className="font-semibold text-gray-800">Gestionar empleados →</p>
          </Link>
          <Link href="/ausencias" className="rounded-xl border bg-white p-6 shadow-sm hover:shadow-md">
            <p className="font-semibold text-gray-800">Solicitudes de ausencia →</p>
          </Link>
        </div>
      )}
    </main>
  );
}"""

_EMPLOYEES_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

export default function EmpleadosPage() {
  const { data, isLoading } = trpc.employees.list.useQuery();

  if (isLoading) return <p className="p-8 text-gray-400">Cargando empleados...</p>;

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Empleados</h1>
      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Departamento</th>
              <th className="px-4 py-3">Cargo</th>
              <th className="px-4 py-3">Inicio</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.map(e => (
              <tr key={e.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{e.user.name}</td>
                <td className="px-4 py-3 text-gray-500">{e.user.email}</td>
                <td className="px-4 py-3">{e.department?.name ?? '—'}</td>
                <td className="px-4 py-3">{e.position}</td>
                <td className="px-4 py-3 text-gray-500">{new Date(e.startDate).toLocaleDateString('es-ES')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}"""

_LEAVES_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const LEAVE_TYPES = ['VACATION', 'SICK', 'PERSONAL', 'MATERNITY_PATERNITY'] as const;
const LEAVE_LABELS: Record<string, string> = {
  VACATION: 'Vacaciones', SICK: 'Baja médica', PERSONAL: 'Asunto personal', MATERNITY_PATERNITY: 'Maternidad/Paternidad'
};

export default function AusenciasPage() {
  const user = useAuthStore(s => s.user);
  const { data, refetch } = trpc.leaves.myLeaves.useQuery(undefined, { enabled: !!user });
  const requestLeave = trpc.leaves.request.useMutation({ onSuccess: () => refetch() });
  const [form, setForm] = useState({ type: 'VACATION' as typeof LEAVE_TYPES[number], startDate: '', endDate: '', reason: '' });

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Mis solicitudes de ausencia</h1>

      <form onSubmit={e => { e.preventDefault(); requestLeave.mutate(form); }}
        className="mb-8 rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-semibold">Nueva solicitud</h2>
        <div className="grid gap-4">
          <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value as typeof LEAVE_TYPES[number] }))}
            className="rounded-lg border px-3 py-2 text-sm">
            {LEAVE_TYPES.map(t => <option key={t} value={t}>{LEAVE_LABELS[t]}</option>)}
          </select>
          <div className="grid grid-cols-2 gap-3">
            <input type="date" value={form.startDate} onChange={e => setForm(f => ({ ...f, startDate: e.target.value }))}
              className="rounded-lg border px-3 py-2 text-sm" />
            <input type="date" value={form.endDate} onChange={e => setForm(f => ({ ...f, endDate: e.target.value }))}
              className="rounded-lg border px-3 py-2 text-sm" />
          </div>
          <textarea value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
            placeholder="Motivo (opcional)" className="rounded-lg border px-3 py-2 text-sm" rows={2} />
          <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
            Enviar solicitud
          </button>
        </div>
      </form>

      <div className="space-y-3">
        {data?.map(l => (
          <div key={l.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm">
            <div>
              <p className="font-medium">{LEAVE_LABELS[l.type]}</p>
              <p className="text-xs text-gray-500">
                {new Date(l.startDate).toLocaleDateString('es-ES')} — {new Date(l.endDate).toLocaleDateString('es-ES')}
              </p>
            </div>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
              l.status === 'APPROVED' ? 'bg-green-100 text-green-700' :
              l.status === 'REJECTED' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
            }`}>
              {l.status === 'APPROVED' ? 'Aprobada' : l.status === 'REJECTED' ? 'Rechazada' : 'Pendiente'}
            </span>
          </div>
        ))}
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
      POSTGRES_USER: rrhh
      POSTGRES_PASSWORD: rrhh_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://rrhh:rrhh_pass@postgres:5432/__SLUG___db
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
DATABASE_URL="postgresql://rrhh:rrhh_pass@localhost:5432/__SLUG___db"

# Auth
JWT_SECRET="change-me-in-production-use-a-long-random-string"

# API
PORT=4000
CORS_ORIGIN="http://localhost:3000"

# Web
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Sistema de Gestión de RRHH

Portal completo para gestión de empleados, departamentos y solicitudes de ausencia.

## Stack

- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, HR_MANAGER, EMPLOYEE)
- **Infra:** Docker Compose · nginx

## Módulos incluidos

| Módulo | Funcionalidad |
|--------|---------------|
| Empleados | Listado, perfiles, cargo, departamento, salario |
| Departamentos | CRUD con conteo de empleados |
| Ausencias | Solicitud, revisión y aprobación de vacaciones/bajas |
| Auth | Login JWT con roles diferenciados |

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

**Admin demo:** admin@empresa.com / password123
"""
