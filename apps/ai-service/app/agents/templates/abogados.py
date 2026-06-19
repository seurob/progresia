"""
ABOGADOS template — despacho jurídico: clientes, expedientes, vistas, horas facturables y facturas.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",                             "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",                             "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",                              "typescript", _API_INDEX.replace("__NAME__", name)),
        _f("apps/api/src/trpc.ts",                               "typescript", _TRPC),
        _f("apps/api/src/router.ts",                             "typescript", _ROUTER),
        _f("apps/api/prisma/schema.prisma",                      "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",                            "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",           "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/clients/client.router.ts",      "typescript", _CLIENT_ROUTER),
        _f("apps/api/src/modules/matters/matter.router.ts",      "typescript", _MATTER_ROUTER),
        _f("apps/api/src/modules/hearings/hearing.router.ts",    "typescript", _HEARING_ROUTER),
        _f("apps/api/src/modules/time/time.router.ts",           "typescript", _TIME_ROUTER),
        _f("apps/api/src/modules/invoices/invoice.router.ts",    "typescript", _INVOICE_ROUTER),
        _f("apps/api/Dockerfile",                                "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",                              "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",                             "json",       _WEB_TSCONFIG),
        _f("apps/web/next.config.js",                            "javascript", _NEXT_CONFIG),
        _f("apps/web/tailwind.config.ts",                        "typescript", _TAILWIND),
        _f("apps/web/postcss.config.js",                         "javascript", _POSTCSS),
        _f("apps/web/src/app/globals.css",                       "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",                           "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",                      "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts",                     "typescript", _AUTH_STORE),
        _f("apps/web/src/app/layout.tsx",                        "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",                          "typescript", _DASHBOARD.replace("__NAME__", name)),
        _f("apps/web/src/app/expedientes/page.tsx",              "typescript", _MATTERS_PAGE),
        _f("apps/web/src/app/clientes/page.tsx",                 "typescript", _CLIENTS_PAGE),
        _f("apps/web/src/app/agenda/page.tsx",                   "typescript", _AGENDA_PAGE),
        _f("apps/web/src/app/facturacion/page.tsx",              "typescript", _BILLING_PAGE),
        _f("apps/web/Dockerfile",                                "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",                                   "nginx",      _NGINX),
        _f("docker-compose.yml",                                 "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                                       "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                                          "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
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
console.log(`⚖️ __NAME__ API running on port ${port}`);"""

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
export const lawyerProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'LAWYER'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN')
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }    from './modules/auth/auth.router';
import { clientRouter }  from './modules/clients/client.router';
import { matterRouter }  from './modules/matters/matter.router';
import { hearingRouter } from './modules/hearings/hearing.router';
import { timeRouter }    from './modules/time/time.router';
import { invoiceRouter } from './modules/invoices/invoice.router';

export const appRouter = router({
  auth:     authRouter,
  clients:  clientRouter,
  matters:  matterRouter,
  hearings: hearingRouter,
  time:     timeRouter,
  invoices: invoiceRouter,
});

export type AppRouter = typeof appRouter;"""

_PRISMA_SCHEMA = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum LegalRole {
  ADMIN
  LAWYER
  PARALEGAL
}

enum CaseType {
  CIVIL
  CRIMINAL
  LABOR
  ADMINISTRATIVE
  MERCANTIL
  FAMILY
  REAL_ESTATE
  OTHER
}

enum CaseStatus {
  OPEN
  IN_PROGRESS
  SUSPENDED
  CLOSED_WON
  CLOSED_LOST
  SETTLED
}

enum InvoiceStatus {
  DRAFT
  SENT
  PAID
  CANCELLED
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         LegalRole @default(PARALEGAL)
  barNumber    String?
  phone        String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  matters      Matter[]
  timeEntries  TimeEntry[]
}

model LegalClient {
  id          String   @id @default(cuid())
  name        String
  isCompany   Boolean  @default(false)
  nif         String?
  email       String?
  phone       String
  address     String?
  notes       String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  matters     Matter[]
}

model Matter {
  id          String     @id @default(cuid())
  clientId    String
  client      LegalClient @relation(fields: [clientId], references: [id])
  lawyerId    String
  lawyer      User        @relation(fields: [lawyerId], references: [id])
  reference   String      @unique @default(cuid())
  title       String
  description String?
  type        CaseType
  status      CaseStatus  @default(OPEN)
  court       String?
  opposingParty String?
  openedAt    DateTime    @default(now())
  closedAt    DateTime?
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
  hearings    Hearing[]
  timeEntries TimeEntry[]
  invoices    Invoice[]
}

model Hearing {
  id          String   @id @default(cuid())
  matterId    String
  matter      Matter   @relation(fields: [matterId], references: [id], onDelete: Cascade)
  scheduledAt DateTime
  court       String?
  judge       String?
  description String?
  result      String?
  notes       String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model TimeEntry {
  id          String   @id @default(cuid())
  matterId    String
  matter      Matter   @relation(fields: [matterId], references: [id], onDelete: Cascade)
  userId      String
  user        User     @relation(fields: [userId], references: [id])
  date        DateTime
  hours       Decimal  @db.Decimal(5, 2)
  description String
  isBillable  Boolean  @default(true)
  ratePerHour Decimal  @db.Decimal(8, 2) @default(150)
  invoiceId   String?
  invoice     Invoice? @relation(fields: [invoiceId], references: [id])
  createdAt   DateTime @default(now())
}

model Invoice {
  id          String        @id @default(cuid())
  matterId    String
  matter      Matter        @relation(fields: [matterId], references: [id])
  status      InvoiceStatus @default(DRAFT)
  number      String        @unique
  issuedAt    DateTime      @default(now())
  dueDate     DateTime?
  subtotal    Decimal       @db.Decimal(10, 2) @default(0)
  tax         Decimal       @db.Decimal(10, 2) @default(0)
  total       Decimal       @db.Decimal(10, 2) @default(0)
  notes       String?
  paidAt      DateTime?
  createdAt   DateTime      @default(now())
  updatedAt   DateTime      @updatedAt
  timeEntries TimeEntry[]
}"""

_SEED = """import { PrismaClient, LegalRole, CaseType, CaseStatus } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Abogados...');

  const hash = await bcrypt.hash('password123', 10);

  const admin = await prisma.user.upsert({
    where: { email: 'admin@despacho.com' },
    update: {},
    create: { email: 'admin@despacho.com', name: 'Admin', passwordHash: hash, role: LegalRole.ADMIN },
  });

  const lawyer1 = await prisma.user.upsert({
    where: { email: 'garcia@despacho.com' },
    update: {},
    create: { email: 'garcia@despacho.com', name: 'Dra. García Abogada', passwordHash: hash, role: LegalRole.LAWYER, barNumber: 'MAD-12345' },
  });

  const lawyer2 = await prisma.user.upsert({
    where: { email: 'ruiz@despacho.com' },
    update: {},
    create: { email: 'ruiz@despacho.com', name: 'D. Ruiz Abogado', passwordHash: hash, role: LegalRole.LAWYER, barNumber: 'MAD-67890' },
  });

  await prisma.user.upsert({
    where: { email: 'paralegal@despacho.com' },
    update: {},
    create: { email: 'paralegal@despacho.com', name: 'Paralegal', passwordHash: hash, role: LegalRole.PARALEGAL },
  });

  // Clients
  const client1 = await prisma.legalClient.create({
    data: { name: 'Carlos Sánchez', phone: '666111222', email: 'csanchez@email.com', nif: '12345678A' },
  });
  const client2 = await prisma.legalClient.create({
    data: { name: 'Construcciones López S.L.', isCompany: true, nif: 'B12345678', phone: '912345678', email: 'info@construcclopez.com' },
  });

  // Matters
  const now = new Date();
  const matter1 = await prisma.matter.create({
    data: {
      clientId: client1.id, lawyerId: lawyer1.id,
      title: 'Divorcio contencioso vs. Marta López',
      type: CaseType.FAMILY, status: CaseStatus.IN_PROGRESS,
      court: 'Juzgado de Primera Instancia nº3 de Madrid',
      opposingParty: 'Marta López Fernández',
    },
  });

  const matter2 = await prisma.matter.create({
    data: {
      clientId: client2.id, lawyerId: lawyer2.id,
      title: 'Reclamación impagos cliente Pérez Obras',
      type: CaseType.MERCANTIL, status: CaseStatus.OPEN,
      court: 'Juzgado Mercantil nº2 de Madrid',
      opposingParty: 'Pérez Obras S.A.',
      description: 'Reclamación de 45.000 € por obras ejecutadas y no pagadas.',
    },
  });

  // Hearings
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 15, 10, 0);
  await prisma.hearing.create({
    data: { matterId: matter1.id, scheduledAt: nextMonth, court: 'Juzgado de Primera Instancia nº3', judge: 'Ilmo. Sr. Martínez', description: 'Vista previa de medidas provisionales' },
  });

  // Time entries
  await prisma.timeEntry.createMany({
    data: [
      { matterId: matter1.id, userId: lawyer1.id, date: new Date(now.getFullYear(), now.getMonth(), 5), hours: 2.5, description: 'Revisión documentación matrimonial y elaboración demanda', isBillable: true, ratePerHour: 180 },
      { matterId: matter1.id, userId: lawyer1.id, date: new Date(now.getFullYear(), now.getMonth(), 8), hours: 1.0, description: 'Reunión con cliente', isBillable: true, ratePerHour: 180 },
      { matterId: matter2.id, userId: lawyer2.id, date: new Date(now.getFullYear(), now.getMonth(), 6), hours: 3.0, description: 'Análisis contratos y reclamación extrajudicial', isBillable: true, ratePerHour: 150 },
    ],
  });

  console.log('✅ Seed completado.');
  console.log('   Admin:      admin@despacho.com / password123');
  console.log('   Abogada:    garcia@despacho.com / password123');
  console.log('   Abogado:    ruiz@despacho.com / password123');
  console.log('   Paralegal:  paralegal@despacho.com / password123');
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
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true, barNumber: true } })
  ),

  lawyers: protectedProcedure.query(() =>
    prisma.user.findMany({ where: { role: { in: ['ADMIN', 'LAWYER'] } }, select: { id: true, name: true, role: true, barNumber: true }, orderBy: { name: 'asc' } })
  ),
});"""

_CLIENT_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const clientRouter = router({
  list: protectedProcedure
    .input(z.object({ search: z.string().optional() }).optional())
    .query(({ input }) =>
      prisma.legalClient.findMany({
        where: input?.search ? { OR: [{ name: { contains: input.search, mode: 'insensitive' } }, { nif: { contains: input.search } }, { email: { contains: input.search, mode: 'insensitive' } }] } : undefined,
        include: { _count: { select: { matters: true } } },
        orderBy: { name: 'asc' },
      })
    ),

  byId: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.legalClient.findUnique({ where: { id: input }, include: { matters: { include: { lawyer: { select: { name: true } } } } } })
    ),

  create: protectedProcedure
    .input(z.object({ name: z.string().min(2), isCompany: z.boolean().default(false), nif: z.string().optional(), email: z.string().email().optional(), phone: z.string().min(9), address: z.string().optional(), notes: z.string().optional() }))
    .mutation(({ input }) => prisma.legalClient.create({ data: input })),

  update: protectedProcedure
    .input(z.object({ id: z.string(), name: z.string().optional(), phone: z.string().optional(), email: z.string().email().optional(), address: z.string().optional(), notes: z.string().optional() }))
    .mutation(({ input: { id, ...data } }) => prisma.legalClient.update({ where: { id }, data })),
});"""

_MATTER_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const matterRouter = router({
  list: protectedProcedure
    .input(z.object({ status: z.enum(['OPEN','IN_PROGRESS','SUSPENDED','CLOSED_WON','CLOSED_LOST','SETTLED']).optional(), lawyerId: z.string().optional() }).optional())
    .query(({ input }) =>
      prisma.matter.findMany({
        where: {
          ...(input?.status   && { status: input.status }),
          ...(input?.lawyerId && { lawyerId: input.lawyerId }),
        },
        include: { client: { select: { name: true } }, lawyer: { select: { name: true } }, _count: { select: { hearings: true, timeEntries: true } } },
        orderBy: { createdAt: 'desc' },
      })
    ),

  byId: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.matter.findUnique({
        where: { id: input },
        include: { client: true, lawyer: { select: { name: true } }, hearings: { orderBy: { scheduledAt: 'asc' } }, timeEntries: { include: { user: { select: { name: true } } }, orderBy: { date: 'desc' } }, invoices: true },
      })
    ),

  create: protectedProcedure
    .input(z.object({ clientId: z.string(), lawyerId: z.string(), title: z.string().min(3), type: z.enum(['CIVIL','CRIMINAL','LABOR','ADMINISTRATIVE','MERCANTIL','FAMILY','REAL_ESTATE','OTHER']), description: z.string().optional(), court: z.string().optional(), opposingParty: z.string().optional() }))
    .mutation(({ input }) => prisma.matter.create({ data: input })),

  updateStatus: protectedProcedure
    .input(z.object({ id: z.string(), status: z.enum(['OPEN','IN_PROGRESS','SUSPENDED','CLOSED_WON','CLOSED_LOST','SETTLED']) }))
    .mutation(({ input }) =>
      prisma.matter.update({ where: { id: input.id }, data: { status: input.status, closedAt: ['CLOSED_WON','CLOSED_LOST','SETTLED'].includes(input.status) ? new Date() : undefined } })
    ),
});"""

_HEARING_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const hearingRouter = router({
  upcoming: protectedProcedure
    .input(z.object({ days: z.number().int().min(1).max(60).default(30) }).optional())
    .query(({ input }) => {
      const from = new Date();
      const to   = new Date(from.getTime() + (input?.days ?? 30) * 24 * 60 * 60 * 1000);
      return prisma.hearing.findMany({
        where: { scheduledAt: { gte: from, lte: to } },
        include: { matter: { include: { client: { select: { name: true } }, lawyer: { select: { name: true } } } } },
        orderBy: { scheduledAt: 'asc' },
      });
    }),

  byMatter: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.hearing.findMany({ where: { matterId: input }, orderBy: { scheduledAt: 'desc' } })
    ),

  create: protectedProcedure
    .input(z.object({ matterId: z.string(), scheduledAt: z.string(), court: z.string().optional(), judge: z.string().optional(), description: z.string().optional() }))
    .mutation(({ input }) =>
      prisma.hearing.create({ data: { ...input, scheduledAt: new Date(input.scheduledAt) } })
    ),

  updateResult: protectedProcedure
    .input(z.object({ id: z.string(), result: z.string(), notes: z.string().optional() }))
    .mutation(({ input }) =>
      prisma.hearing.update({ where: { id: input.id }, data: { result: input.result, notes: input.notes } })
    ),
});"""

_TIME_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const timeRouter = router({
  byMatter: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.timeEntry.findMany({
        where: { matterId: input },
        include: { user: { select: { name: true } } },
        orderBy: { date: 'desc' },
      })
    ),

  summary: protectedProcedure
    .input(z.string())
    .query(async ({ input: matterId }) => {
      const entries = await prisma.timeEntry.findMany({ where: { matterId, isBillable: true, invoiceId: null } });
      const totalHours   = entries.reduce((s, e) => s + Number(e.hours), 0);
      const totalAmount  = entries.reduce((s, e) => s + Number(e.hours) * Number(e.ratePerHour), 0);
      return { totalHours, totalAmount, entries };
    }),

  log: protectedProcedure
    .input(z.object({ matterId: z.string(), date: z.string(), hours: z.number().positive().max(24), description: z.string().min(5), isBillable: z.boolean().default(true), ratePerHour: z.number().positive().default(150) }))
    .mutation(({ input, ctx }) =>
      prisma.timeEntry.create({ data: { ...input, date: new Date(input.date), userId: ctx.userId } })
    ),
});"""

_INVOICE_ROUTER = """import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, protectedProcedure, lawyerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

let invoiceCounter = 1000;

export const invoiceRouter = router({
  byMatter: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.invoice.findMany({ where: { matterId: input }, include: { timeEntries: { include: { user: { select: { name: true } } } } }, orderBy: { issuedAt: 'desc' } })
    ),

  create: lawyerProcedure
    .input(z.object({ matterId: z.string(), taxRate: z.number().min(0).max(100).default(21), dueDate: z.string().optional(), notes: z.string().optional() }))
    .mutation(async ({ input }) => {
      // Gather unbilled entries
      const entries = await prisma.timeEntry.findMany({ where: { matterId: input.matterId, isBillable: true, invoiceId: null } });
      if (!entries.length) throw new TRPCError({ code: 'BAD_REQUEST', message: 'No hay horas facturables pendientes' });

      const subtotal = entries.reduce((s, e) => s + Number(e.hours) * Number(e.ratePerHour), 0);
      const tax      = subtotal * (input.taxRate / 100);
      const total    = subtotal + tax;
      const number   = `INV-${new Date().getFullYear()}-${String(++invoiceCounter).padStart(4, '0')}`;

      const invoice = await prisma.invoice.create({
        data: {
          matterId: input.matterId, number, subtotal, tax, total,
          dueDate: input.dueDate ? new Date(input.dueDate) : undefined,
          notes:   input.notes,
          timeEntries: { connect: entries.map(e => ({ id: e.id })) },
        },
        include: { timeEntries: true },
      });
      return invoice;
    }),

  updateStatus: lawyerProcedure
    .input(z.object({ id: z.string(), status: z.enum(['DRAFT', 'SENT', 'PAID', 'CANCELLED']) }))
    .mutation(({ input }) =>
      prisma.invoice.update({ where: { id: input.id }, data: { status: input.status, paidAt: input.status === 'PAID' ? new Date() : undefined } })
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
  "scripts": { "dev": "next dev", "build": "next build", "start": "next start" },
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
    "target": "ES2022", "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true, "skipLibCheck": true, "strict": true, "noEmit": true,
    "esModuleInterop": true, "module": "esnext", "moduleResolution": "bundler",
    "resolveJsonModule": true, "isolatedModules": true, "jsx": "preserve",
    "incremental": true, "plugins": [{ "name": "next" }],
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
_GLOBALS_CSS = """@tailwind base;\n@tailwind components;\n@tailwind utilities;"""
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
export const metadata: Metadata = { title: '__NAME__', description: 'Gestión jurídica' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <TRPCProvider>
          <nav className="bg-slate-800 text-white px-6 py-3 flex items-center gap-6 shadow">
            <span className="font-bold text-amber-400">⚖️ __NAME__</span>
            <a href="/"             className="text-sm hover:text-amber-300">Dashboard</a>
            <a href="/expedientes"  className="text-sm hover:text-amber-300">Expedientes</a>
            <a href="/clientes"     className="text-sm hover:text-amber-300">Clientes</a>
            <a href="/agenda"       className="text-sm hover:text-amber-300">Agenda</a>
            <a href="/facturacion"  className="text-sm hover:text-amber-300">Facturación</a>
          </nav>
          {children}
        </TRPCProvider>
      </body>
    </html>
  );
}"""

_DASHBOARD = """'use client';
import { trpc } from '@/lib/trpc';

const STATUS_COLORS: Record<string, string> = { OPEN: 'bg-blue-100 text-blue-700', IN_PROGRESS: 'bg-amber-100 text-amber-700', SUSPENDED: 'bg-slate-100 text-slate-500', CLOSED_WON: 'bg-green-100 text-green-700', CLOSED_LOST: 'bg-red-100 text-red-600', SETTLED: 'bg-purple-100 text-purple-700' };
const TYPE_LABELS: Record<string, string> = { CIVIL: 'Civil', CRIMINAL: 'Penal', LABOR: 'Laboral', ADMINISTRATIVE: 'Administrativo', MERCANTIL: 'Mercantil', FAMILY: 'Familia', REAL_ESTATE: 'Inmobiliario', OTHER: 'Otro' };

export default function DashboardPage() {
  const { data: matters }  = trpc.matters.list.useQuery();
  const { data: hearings } = trpc.hearings.upcoming.useQuery({ days: 14 });

  const active   = matters?.filter(m => ['OPEN', 'IN_PROGRESS'].includes(m.status)) ?? [];
  const byStatus = matters?.reduce((acc: Record<string, number>, m) => { acc[m.status] = (acc[m.status] ?? 0) + 1; return acc; }, {}) ?? {};

  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-2xl font-bold">⚖️ Dashboard</h1>

      {/* Stats */}
      <div className="mb-6 grid grid-cols-4 gap-4">
        {[['Activos', active.length, 'text-blue-600'], ['Total', matters?.length ?? 0, 'text-slate-700'], ['Vistas (14d)', hearings?.length ?? 0, 'text-amber-600'], ['Cerrados', (byStatus['CLOSED_WON'] ?? 0) + (byStatus['CLOSED_LOST'] ?? 0), 'text-slate-500']].map(([label, val, cls]) => (
          <div key={label as string} className="rounded-xl border bg-white p-4 shadow-sm text-center">
            <p className={`text-3xl font-bold ${cls}`}>{val}</p>
            <p className="text-xs text-slate-400 mt-1">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Active matters */}
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <p className="mb-3 font-semibold text-slate-700">Expedientes activos</p>
          <div className="space-y-2">
            {active.slice(0, 5).map(m => (
              <div key={m.id} className="rounded-lg border p-3">
                <div className="flex items-start justify-between">
                  <p className="font-medium text-sm leading-tight">{m.title}</p>
                  <span className={`ml-2 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[m.status]}`}>{m.status}</span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{m.client.name} · {TYPE_LABELS[m.type]}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming hearings */}
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <p className="mb-3 font-semibold text-slate-700">Próximas vistas (14 días)</p>
          <div className="space-y-2">
            {hearings?.map(h => (
              <div key={h.id} className="flex gap-3 items-start rounded-lg border p-3">
                <div className="shrink-0 text-center w-12">
                  <p className="text-lg font-bold text-amber-600">{new Date(h.scheduledAt).getDate()}</p>
                  <p className="text-xs text-slate-400">{new Date(h.scheduledAt).toLocaleString('es-ES', { month: 'short' })}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">{h.matter.title}</p>
                  <p className="text-xs text-slate-400">{h.description ?? h.court ?? ''}</p>
                  <p className="text-xs text-slate-300">{h.matter.client.name} · {h.matter.lawyer.name}</p>
                </div>
              </div>
            ))}
            {!hearings?.length && <p className="text-slate-400 text-sm">Sin vistas próximas.</p>}
          </div>
        </div>
      </div>
    </main>
  );
}"""

_MATTERS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const STATUS_COLORS: Record<string, string> = { OPEN: 'bg-blue-100 text-blue-700', IN_PROGRESS: 'bg-amber-100 text-amber-700', SUSPENDED: 'bg-slate-100 text-slate-500', CLOSED_WON: 'bg-green-100 text-green-700', CLOSED_LOST: 'bg-red-100 text-red-600', SETTLED: 'bg-purple-100 text-purple-700' };
const TYPE_LABELS: Record<string, string> = { CIVIL: 'Civil', CRIMINAL: 'Penal', LABOR: 'Laboral', ADMINISTRATIVE: 'Administrativo', MERCANTIL: 'Mercantil', FAMILY: 'Familia', REAL_ESTATE: 'Inmobiliario', OTHER: 'Otro' };
const STATUSES = ['OPEN', 'IN_PROGRESS', 'SUSPENDED', 'CLOSED_WON', 'CLOSED_LOST', 'SETTLED'];

export default function ExpedientesPage() {
  const [status, setStatus] = useState('');
  const { data, refetch } = trpc.matters.list.useQuery(status ? { status: status as any } : undefined);
  const updateStatus = trpc.matters.updateStatus.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Expedientes</h1>
        <select value={status} onChange={e => setStatus(e.target.value)}
          className="ml-auto rounded-xl border px-3 py-2 text-sm bg-white">
          <option value="">Todos</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <div className="space-y-3">
        {data?.map(m => (
          <div key={m.id} className="rounded-xl border bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between mb-1">
              <div className="flex-1">
                <p className="font-semibold">{m.title}</p>
                <p className="text-sm text-slate-500">{m.client.name} · {m.lawyer.name} · {TYPE_LABELS[m.type]}</p>
              </div>
              <span className={`ml-3 shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[m.status]}`}>{m.status}</span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
              <span>📅 {new Date(m.createdAt).toLocaleDateString('es-ES')}</span>
              <span>· ⏱️ {m._count.timeEntries} entradas</span>
              <span>· 📋 {m._count.hearings} vistas</span>
              <select value={m.status} onChange={e => updateStatus.mutate({ id: m.id, status: e.target.value as any })}
                className="ml-auto rounded border border-slate-200 px-2 py-0.5 text-xs bg-white">
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_CLIENTS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

export default function ClientesPage() {
  const [search, setSearch] = useState('');
  const { data } = trpc.clients.list.useQuery(search ? { search } : undefined);

  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Clientes</h1>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por nombre, NIF o email..."
          className="ml-auto w-64 rounded-xl border px-4 py-2 text-sm bg-white" />
      </div>
      <div className="space-y-2">
        {data?.map(c => (
          <div key={c.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm">
            <div>
              <p className="font-semibold">{c.isCompany ? '🏢' : '👤'} {c.name}</p>
              <p className="text-sm text-slate-400">{c.nif ?? '—'} · {c.email ?? '—'}</p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-0.5">{c._count.matters} exp.</span>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_AGENDA_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

export default function AgendaPage() {
  const { data } = trpc.hearings.upcoming.useQuery({ days: 30 });

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Agenda — próximas vistas</h1>
      <div className="space-y-3">
        {data?.map(h => (
          <div key={h.id} className="flex gap-4 rounded-xl border bg-white p-4 shadow-sm">
            <div className="shrink-0 w-14 text-center rounded-xl bg-amber-50 py-2">
              <p className="text-2xl font-bold text-amber-600">{new Date(h.scheduledAt).getDate()}</p>
              <p className="text-xs text-slate-400">{new Date(h.scheduledAt).toLocaleString('es-ES', { month: 'short' })}</p>
              <p className="text-xs text-slate-400">{new Date(h.scheduledAt).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
            <div className="flex-1">
              <p className="font-semibold">{h.matter.title}</p>
              <p className="text-sm text-slate-500">{h.description ?? '—'}</p>
              <p className="text-xs text-slate-400 mt-1">{h.court ?? ''} · {h.judge ? `Juzgado: ${h.judge}` : ''}</p>
              <p className="text-xs text-slate-300">{h.matter.client.name} · {h.matter.lawyer.name}</p>
            </div>
            {h.result && <div className="text-xs text-green-600 bg-green-50 rounded-lg px-2 py-1">✓ {h.result}</div>}
          </div>
        ))}
        {data?.length === 0 && <p className="text-slate-400">Sin vistas en los próximos 30 días.</p>}
      </div>
    </main>
  );
}"""

_BILLING_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const INV_STATUS_COLORS: Record<string, string> = { DRAFT: 'bg-slate-100 text-slate-600', SENT: 'bg-blue-100 text-blue-700', PAID: 'bg-green-100 text-green-700', CANCELLED: 'bg-red-100 text-red-500' };

export default function FacturacionPage() {
  const { data: matters } = trpc.matters.list.useQuery();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: timeSummary, refetch: refetchTime } = trpc.time.summary.useQuery(selectedId!, { enabled: !!selectedId });
  const { data: invoices,    refetch: refetchInv }  = trpc.invoices.byMatter.useQuery(selectedId!, { enabled: !!selectedId });
  const createInvoice  = trpc.invoices.create.useMutation({ onSuccess: () => { refetchTime(); refetchInv(); } });
  const updateInvoice  = trpc.invoices.updateStatus.useMutation({ onSuccess: () => refetchInv() });

  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Facturación</h1>
      <div className="grid grid-cols-3 gap-6">
        {/* Matter list */}
        <div className="col-span-1 space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">Expedientes</p>
          {matters?.filter(m => ['OPEN','IN_PROGRESS','SETTLED'].includes(m.status)).map(m => (
            <button key={m.id} onClick={() => setSelectedId(m.id)}
              className={`w-full text-left rounded-xl border p-3 transition text-sm ${selectedId === m.id ? 'border-amber-400 bg-amber-50' : 'bg-white hover:bg-slate-50'}`}>
              <p className="font-medium leading-tight">{m.title}</p>
              <p className="text-xs text-slate-400">{m.client.name}</p>
            </button>
          ))}
        </div>

        {/* Billing detail */}
        <div className="col-span-2">
          {!selectedId && <p className="text-slate-400 py-8 text-center">Selecciona un expediente</p>}
          {selectedId && (
            <>
              {/* Unbilled hours summary */}
              {timeSummary && (
                <div className="mb-4 rounded-xl border bg-amber-50 p-4">
                  <p className="text-sm font-semibold text-amber-800">Horas facturables pendientes</p>
                  <p className="text-2xl font-bold text-amber-700 mt-1">{timeSummary.totalHours.toFixed(1)}h — {timeSummary.totalAmount.toFixed(2)} €</p>
                  <button onClick={() => createInvoice.mutate({ matterId: selectedId })} disabled={timeSummary.totalHours === 0 || createInvoice.isPending}
                    className="mt-2 rounded-lg bg-amber-600 px-4 py-1.5 text-xs text-white hover:bg-amber-700 disabled:opacity-50">
                    Generar factura
                  </button>
                </div>
              )}
              {/* Invoices */}
              <div className="space-y-3">
                {invoices?.map(inv => (
                  <div key={inv.id} className="rounded-xl border bg-white p-4 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-mono font-bold text-sm">{inv.number}</p>
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${INV_STATUS_COLORS[inv.status]}`}>{inv.status}</span>
                    </div>
                    <div className="flex gap-4 text-sm text-slate-600">
                      <span>Base: {Number(inv.subtotal).toFixed(2)} €</span>
                      <span>IVA: {Number(inv.tax).toFixed(2)} €</span>
                      <span className="font-bold">Total: {Number(inv.total).toFixed(2)} €</span>
                    </div>
                    <div className="mt-2 flex gap-2">
                      {inv.status === 'DRAFT' && <button onClick={() => updateInvoice.mutate({ id: inv.id, status: 'SENT' })} className="rounded-lg bg-blue-600 px-3 py-1 text-xs text-white">Enviar</button>}
                      {inv.status === 'SENT'  && <button onClick={() => updateInvoice.mutate({ id: inv.id, status: 'PAID' })} className="rounded-lg bg-green-600 px-3 py-1 text-xs text-white">Marcar pagada</button>}
                    </div>
                  </div>
                ))}
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
      POSTGRES_USER: despacho
      POSTGRES_PASSWORD: legal_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://despacho:legal_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://despacho:legal_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Despacho de Abogados

Sistema de gestión jurídica: clientes, expedientes, vistas, horas facturables y facturación.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, LAWYER, PARALEGAL)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Dashboard | Expedientes activos + próximas vistas en los próximos 14 días |
| Expedientes | CRUD + cambio de estado (OPEN → IN_PROGRESS → CLOSED_WON / SETTLED) |
| Clientes | Personas físicas y jurídicas con número de expedientes |
| Agenda | Vistas de los próximos 30 días con tribunal y juez |
| Facturación | Horas imputadas → generar factura → DRAFT → SENT → PAID |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin:     admin@despacho.com / password123
Abogada:   garcia@despacho.com / password123
Abogado:   ruiz@despacho.com / password123
"""
