"""
GYM template — gestión de gimnasio: planes de membresía, clases grupales, reservas y check-in.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",                                "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",                                "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",                                 "typescript", _API_INDEX.replace("__NAME__", name)),
        _f("apps/api/src/trpc.ts",                                  "typescript", _TRPC),
        _f("apps/api/src/router.ts",                                "typescript", _ROUTER),
        _f("apps/api/prisma/schema.prisma",                         "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",                               "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",              "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/membership/membership.router.ts",  "typescript", _MEMBERSHIP_ROUTER),
        _f("apps/api/src/modules/classes/class.router.ts",          "typescript", _CLASS_ROUTER),
        _f("apps/api/src/modules/sessions/session.router.ts",       "typescript", _SESSION_ROUTER),
        _f("apps/api/src/modules/bookings/booking.router.ts",       "typescript", _BOOKING_ROUTER),
        _f("apps/api/Dockerfile",                                   "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",                                 "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",                                "json",       _WEB_TSCONFIG),
        _f("apps/web/next.config.js",                               "javascript", _NEXT_CONFIG),
        _f("apps/web/tailwind.config.ts",                           "typescript", _TAILWIND),
        _f("apps/web/postcss.config.js",                            "javascript", _POSTCSS),
        _f("apps/web/src/app/globals.css",                          "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",                              "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",                         "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts",                        "typescript", _AUTH_STORE),
        _f("apps/web/src/app/layout.tsx",                           "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",                             "typescript", _DASHBOARD.replace("__NAME__", name)),
        _f("apps/web/src/app/clases/page.tsx",                      "typescript", _CLASSES_PAGE),
        _f("apps/web/src/app/reservas/page.tsx",                    "typescript", _BOOKINGS_PAGE),
        _f("apps/web/src/app/membresia/page.tsx",                   "typescript", _MEMBERSHIP_PAGE),
        _f("apps/web/Dockerfile",                                   "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",                                      "nginx",      _NGINX),
        _f("docker-compose.yml",                                    "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                                          "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                                             "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
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
console.log(`💪 __NAME__ API running on port ${port}`);"""

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
export const trainerProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'TRAINER'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN')
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }       from './modules/auth/auth.router';
import { membershipRouter } from './modules/membership/membership.router';
import { classRouter }      from './modules/classes/class.router';
import { sessionRouter }    from './modules/sessions/session.router';
import { bookingRouter }    from './modules/bookings/booking.router';

export const appRouter = router({
  auth:        authRouter,
  memberships: membershipRouter,
  classes:     classRouter,
  sessions:    sessionRouter,
  bookings:    bookingRouter,
});

export type AppRouter = typeof appRouter;"""

_PRISMA_SCHEMA = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum GymRole {
  ADMIN
  TRAINER
  MEMBER
}

enum MembershipStatus {
  ACTIVE
  EXPIRED
  CANCELLED
  PENDING
}

enum ClassType {
  YOGA
  PILATES
  CROSSFIT
  SPINNING
  BOXING
  ZUMBA
  STRENGTH
  CARDIO
  SWIMMING
  STRETCHING
}

enum DayOfWeek {
  MONDAY
  TUESDAY
  WEDNESDAY
  THURSDAY
  FRIDAY
  SATURDAY
  SUNDAY
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         GymRole   @default(MEMBER)
  phone        String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  trainer      Trainer?
  membership   Membership?
  bookings     ClassBooking[]
}

model Trainer {
  id          String    @id @default(cuid())
  userId      String    @unique
  user        User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  bio         String?
  specialties String[]
  classes     GymClass[]
}

model MembershipPlan {
  id          String       @id @default(cuid())
  name        String
  description String?
  durationDays Int
  price       Decimal      @db.Decimal(8, 2)
  maxClasses  Int?
  isActive    Boolean      @default(true)
  createdAt   DateTime     @default(now())
  memberships Membership[]
}

model Membership {
  id        String           @id @default(cuid())
  userId    String           @unique
  user      User             @relation(fields: [userId], references: [id], onDelete: Cascade)
  planId    String
  plan      MembershipPlan   @relation(fields: [planId], references: [id])
  status    MembershipStatus @default(PENDING)
  startDate DateTime
  endDate   DateTime
  createdAt DateTime         @default(now())
  updatedAt DateTime         @updatedAt
}

model GymClass {
  id          String     @id @default(cuid())
  trainerId   String
  trainer     Trainer    @relation(fields: [trainerId], references: [id])
  name        String
  description String?
  type        ClassType
  maxCapacity Int
  durationMin Int        @default(60)
  dayOfWeek   DayOfWeek
  startTime   String
  room        String?
  isActive    Boolean    @default(true)
  createdAt   DateTime   @default(now())
  sessions    ClassSession[]
}

model ClassSession {
  id          String         @id @default(cuid())
  gymClassId  String
  gymClass    GymClass       @relation(fields: [gymClassId], references: [id])
  date        DateTime
  cancelled   Boolean        @default(false)
  cancelReason String?
  createdAt   DateTime       @default(now())
  bookings    ClassBooking[]
}

model ClassBooking {
  id          String       @id @default(cuid())
  sessionId   String
  session     ClassSession @relation(fields: [sessionId], references: [id], onDelete: Cascade)
  userId      String
  user        User         @relation(fields: [userId], references: [id])
  attendedAt  DateTime?
  cancelledAt DateTime?
  createdAt   DateTime     @default(now())

  @@unique([sessionId, userId])
}"""

_SEED = """import { PrismaClient, GymRole, ClassType, DayOfWeek } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Gym...');

  const hash = await bcrypt.hash('password123', 10);

  const admin = await prisma.user.upsert({
    where: { email: 'admin@gym.com' },
    update: {},
    create: { email: 'admin@gym.com', name: 'Admin Gym', passwordHash: hash, role: GymRole.ADMIN },
  });

  const trainer1User = await prisma.user.upsert({
    where: { email: 'carlos@gym.com' },
    update: {},
    create: { email: 'carlos@gym.com', name: 'Carlos Trainer', passwordHash: hash, role: GymRole.TRAINER, phone: '600123456' },
  });

  const trainer2User = await prisma.user.upsert({
    where: { email: 'sofia@gym.com' },
    update: {},
    create: { email: 'sofia@gym.com', name: 'Sofía Trainer', passwordHash: hash, role: GymRole.TRAINER, phone: '600789012' },
  });

  const member1User = await prisma.user.upsert({
    where: { email: 'miembro@gym.com' },
    update: {},
    create: { email: 'miembro@gym.com', name: 'Juan Miembro', passwordHash: hash, role: GymRole.MEMBER, phone: '677001122' },
  });

  // Trainers
  const trainer1 = await prisma.trainer.upsert({
    where: { userId: trainer1User.id },
    update: {},
    create: { userId: trainer1User.id, bio: 'Especialista en fuerza y CrossFit con 8 años de experiencia.', specialties: ['CROSSFIT', 'STRENGTH', 'CARDIO'] },
  });

  const trainer2 = await prisma.trainer.upsert({
    where: { userId: trainer2User.id },
    update: {},
    create: { userId: trainer2User.id, bio: 'Instructora certificada en Yoga y Pilates.', specialties: ['YOGA', 'PILATES', 'STRETCHING'] },
  });

  // Membership plans
  const planBasic = await prisma.membershipPlan.create({
    data: { name: 'Básica', description: 'Acceso a sala de pesas y cardio', durationDays: 30, price: 29.99 },
  });
  const planPro = await prisma.membershipPlan.create({
    data: { name: 'Pro', description: 'Acceso completo + clases grupales ilimitadas', durationDays: 30, price: 49.99, maxClasses: null },
  });
  const planAnual = await prisma.membershipPlan.create({
    data: { name: 'Anual Pro', description: '12 meses + 2 meses gratis', durationDays: 365, price: 399.00 },
  });

  // Active membership for member
  const now = new Date();
  const end = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
  await prisma.membership.create({
    data: { userId: member1User.id, planId: planPro.id, status: 'ACTIVE', startDate: now, endDate: end },
  });

  // Classes
  const crossfit = await prisma.gymClass.create({
    data: { trainerId: trainer1.id, name: 'CrossFit Matutino', type: ClassType.CROSSFIT, maxCapacity: 15, durationMin: 60, dayOfWeek: DayOfWeek.MONDAY, startTime: '07:00', room: 'Sala A', description: 'Entrenamiento funcional de alta intensidad.' },
  });
  const yoga = await prisma.gymClass.create({
    data: { trainerId: trainer2.id, name: 'Yoga Hatha', type: ClassType.YOGA, maxCapacity: 20, durationMin: 75, dayOfWeek: DayOfWeek.TUESDAY, startTime: '09:30', room: 'Sala B', description: 'Yoga para todos los niveles.' },
  });
  const spinning = await prisma.gymClass.create({
    data: { trainerId: trainer1.id, name: 'Spinning Power', type: ClassType.SPINNING, maxCapacity: 18, durationMin: 45, dayOfWeek: DayOfWeek.WEDNESDAY, startTime: '18:00', room: 'Sala Cycling', description: 'Ciclismo indoor de alta energía.' },
  });
  const pilates = await prisma.gymClass.create({
    data: { trainerId: trainer2.id, name: 'Pilates Core', type: ClassType.PILATES, maxCapacity: 12, durationMin: 60, dayOfWeek: DayOfWeek.THURSDAY, startTime: '10:00', room: 'Sala B', description: 'Trabajo de core y flexibilidad.' },
  });
  const zumba = await prisma.gymClass.create({
    data: { trainerId: trainer2.id, name: 'Zumba Fitness', type: ClassType.ZUMBA, maxCapacity: 25, durationMin: 60, dayOfWeek: DayOfWeek.FRIDAY, startTime: '19:00', room: 'Sala Principal', description: 'Baile y fitness combinados.' },
  });

  // Sessions for this week
  const monday    = new Date(); monday.setDate(monday.getDate() + (1 - monday.getDay() + 7) % 7); monday.setHours(7, 0, 0, 0);
  const tuesday   = new Date(monday); tuesday.setDate(tuesday.getDate() + 1); tuesday.setHours(9, 30, 0, 0);
  const wednesday = new Date(monday); wednesday.setDate(wednesday.getDate() + 2); wednesday.setHours(18, 0, 0, 0);

  const session1 = await prisma.classSession.create({ data: { gymClassId: crossfit.id,  date: monday } });
  const session2 = await prisma.classSession.create({ data: { gymClassId: yoga.id,      date: tuesday } });
  await prisma.classSession.create({ data: { gymClassId: spinning.id, date: wednesday } });

  // Member books CrossFit and Yoga
  await prisma.classBooking.createMany({
    data: [
      { sessionId: session1.id, userId: member1User.id },
      { sessionId: session2.id, userId: member1User.id },
    ],
  });

  console.log('✅ Seed completado.');
  console.log('   Admin:    admin@gym.com / password123');
  console.log('   Trainers: carlos@gym.com / sofia@gym.com / password123');
  console.log('   Member:   miembro@gym.com / password123');
}

main().catch(console.error).finally(() => prisma.$disconnect());"""

_AUTH_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';
import bcrypt from 'bcryptjs';

export const authRouter = router({
  register: publicProcedure
    .input(z.object({ email: z.string().email(), name: z.string().min(2), password: z.string().min(8), phone: z.string().optional() }))
    .mutation(async ({ input }) => {
      if (await prisma.user.findUnique({ where: { email: input.email } })) throw new Error('Email ya registrado');
      const passwordHash = await bcrypt.hash(input.password, 10);
      return prisma.user.create({ data: { email: input.email, name: input.name, passwordHash, phone: input.phone }, select: { id: true, email: true, name: true, role: true } });
    }),

  login: publicProcedure
    .input(z.object({ email: z.string().email(), password: z.string() }))
    .mutation(async ({ input, ctx }) => {
      const user = await prisma.user.findUnique({ where: { email: input.email } });
      if (!user || !(await bcrypt.compare(input.password, user.passwordHash)))
        throw new Error('Credenciales incorrectas');
      const token = await ctx.req.server.jwt.sign({ sub: user.id, role: user.role }, { expiresIn: '7d' });
      return { token, user: { id: user.id, name: user.name, email: user.email, role: user.role } };
    }),

  me: protectedProcedure.query(({ ctx }) =>
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true } })
  ),
});"""

_MEMBERSHIP_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const membershipRouter = router({
  plans: publicProcedure.query(() =>
    prisma.membershipPlan.findMany({ where: { isActive: true }, orderBy: { price: 'asc' } })
  ),

  mine: protectedProcedure.query(({ ctx }) =>
    prisma.membership.findUnique({
      where: { userId: ctx.userId },
      include: { plan: true },
    })
  ),

  subscribe: protectedProcedure
    .input(z.object({ planId: z.string() }))
    .mutation(async ({ input, ctx }) => {
      const plan  = await prisma.membershipPlan.findUniqueOrThrow({ where: { id: input.planId } });
      const start = new Date();
      const end   = new Date(start.getTime() + plan.durationDays * 24 * 60 * 60 * 1000);
      return prisma.membership.upsert({
        where: { userId: ctx.userId },
        update: { planId: input.planId, status: 'ACTIVE', startDate: start, endDate: end },
        create: { userId: ctx.userId, planId: input.planId, status: 'ACTIVE', startDate: start, endDate: end },
        include: { plan: true },
      });
    }),

  cancel: protectedProcedure.mutation(({ ctx }) =>
    prisma.membership.update({ where: { userId: ctx.userId }, data: { status: 'CANCELLED' } })
  ),

  all: adminProcedure.query(() =>
    prisma.membership.findMany({ include: { user: { select: { name: true, email: true } }, plan: true }, orderBy: { createdAt: 'desc' } })
  ),
});"""

_CLASS_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, trainerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const classRouter = router({
  list: publicProcedure
    .input(z.object({ type: z.enum(['YOGA','PILATES','CROSSFIT','SPINNING','BOXING','ZUMBA','STRENGTH','CARDIO','SWIMMING','STRETCHING']).optional(), dayOfWeek: z.enum(['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY']).optional() }).optional())
    .query(({ input }) =>
      prisma.gymClass.findMany({
        where: {
          isActive: true,
          ...(input?.type      && { type: input.type }),
          ...(input?.dayOfWeek && { dayOfWeek: input.dayOfWeek }),
        },
        include: { trainer: { include: { user: { select: { name: true } } } }, _count: { select: { sessions: true } } },
        orderBy: [{ dayOfWeek: 'asc' }, { startTime: 'asc' }],
      })
    ),

  create: trainerProcedure
    .input(z.object({
      name:        z.string().min(3),
      type:        z.enum(['YOGA','PILATES','CROSSFIT','SPINNING','BOXING','ZUMBA','STRENGTH','CARDIO','SWIMMING','STRETCHING']),
      maxCapacity: z.number().int().min(1),
      durationMin: z.number().int().default(60),
      dayOfWeek:   z.enum(['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY']),
      startTime:   z.string().regex(/^\\d{2}:\\d{2}$/),
      description: z.string().optional(),
      room:        z.string().optional(),
    }))
    .mutation(async ({ input, ctx }) => {
      const trainer = await prisma.trainer.findUnique({ where: { userId: ctx.userId } });
      if (!trainer) throw new Error('Perfil de entrenador no encontrado');
      return prisma.gymClass.create({ data: { ...input, trainerId: trainer.id } });
    }),

  toggleActive: trainerProcedure
    .input(z.string())
    .mutation(async ({ input }) => {
      const c = await prisma.gymClass.findUniqueOrThrow({ where: { id: input } });
      return prisma.gymClass.update({ where: { id: input }, data: { isActive: !c.isActive } });
    }),
});"""

_SESSION_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, trainerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const sessionRouter = router({
  upcoming: protectedProcedure
    .input(z.object({ days: z.number().int().min(1).max(14).default(7) }).optional())
    .query(({ input }) => {
      const from = new Date();
      const to   = new Date(from.getTime() + (input?.days ?? 7) * 24 * 60 * 60 * 1000);
      return prisma.classSession.findMany({
        where: { date: { gte: from, lte: to }, cancelled: false },
        include: {
          gymClass: { include: { trainer: { include: { user: { select: { name: true } } } } } },
          _count: { select: { bookings: true } },
        },
        orderBy: { date: 'asc' },
      });
    }),

  byClass: protectedProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.classSession.findMany({
        where: { gymClassId: input, date: { gte: new Date() }, cancelled: false },
        include: { _count: { select: { bookings: true } } },
        orderBy: { date: 'asc' },
      })
    ),

  create: trainerProcedure
    .input(z.object({ gymClassId: z.string(), date: z.string() }))
    .mutation(({ input }) =>
      prisma.classSession.create({ data: { gymClassId: input.gymClassId, date: new Date(input.date) } })
    ),

  cancel: trainerProcedure
    .input(z.object({ id: z.string(), cancelReason: z.string().optional() }))
    .mutation(({ input }) =>
      prisma.classSession.update({ where: { id: input.id }, data: { cancelled: true, cancelReason: input.cancelReason } })
    ),
});"""

_BOOKING_ROUTER = """import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, protectedProcedure, trainerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const bookingRouter = router({
  myBookings: protectedProcedure
    .input(z.object({ upcoming: z.boolean().default(true) }).optional())
    .query(({ ctx, input }) =>
      prisma.classBooking.findMany({
        where: {
          userId: ctx.userId,
          cancelledAt: null,
          session: input?.upcoming !== false ? { date: { gte: new Date() }, cancelled: false } : undefined,
        },
        include: { session: { include: { gymClass: { include: { trainer: { include: { user: { select: { name: true } } } } } } } } },
        orderBy: { session: { date: 'asc' } },
      })
    ),

  book: protectedProcedure
    .input(z.string())
    .mutation(async ({ input: sessionId, ctx }) => {
      // Verify active membership
      const membership = await prisma.membership.findUnique({ where: { userId: ctx.userId } });
      if (!membership || membership.status !== 'ACTIVE' || membership.endDate < new Date())
        throw new TRPCError({ code: 'FORBIDDEN', message: 'Necesitas una membresía activa para reservar clases' });

      const session = await prisma.classSession.findUniqueOrThrow({
        where: { id: sessionId },
        include: { gymClass: true, _count: { select: { bookings: true } } },
      });

      if (session.cancelled)
        throw new TRPCError({ code: 'BAD_REQUEST', message: 'Esta sesión ha sido cancelada' });

      if (session._count.bookings >= session.gymClass.maxCapacity)
        throw new TRPCError({ code: 'BAD_REQUEST', message: 'Clase completa' });

      return prisma.classBooking.create({
        data: { sessionId, userId: ctx.userId },
        include: { session: { include: { gymClass: true } } },
      });
    }),

  cancel: protectedProcedure
    .input(z.string())
    .mutation(({ input, ctx }) =>
      prisma.classBooking.update({
        where: { sessionId_userId: { sessionId: input, userId: ctx.userId } },
        data: { cancelledAt: new Date() },
      })
    ),

  markAttended: trainerProcedure
    .input(z.object({ sessionId: z.string(), userId: z.string() }))
    .mutation(({ input }) =>
      prisma.classBooking.update({
        where: { sessionId_userId: { sessionId: input.sessionId, userId: input.userId } },
        data: { attendedAt: new Date() },
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
export const metadata: Metadata = { title: '__NAME__', description: 'Gestión de gimnasio' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">
        <TRPCProvider>
          <nav className="bg-zinc-900 border-b border-zinc-800 px-6 py-3 flex items-center gap-6">
            <span className="font-bold text-orange-500">💪 __NAME__</span>
            <a href="/"          className="text-sm text-zinc-400 hover:text-orange-400">Dashboard</a>
            <a href="/clases"    className="text-sm text-zinc-400 hover:text-orange-400">Clases</a>
            <a href="/reservas"  className="text-sm text-zinc-400 hover:text-orange-400">Mis reservas</a>
            <a href="/membresia" className="text-sm text-zinc-400 hover:text-orange-400">Membresía</a>
          </nav>
          {children}
        </TRPCProvider>
      </body>
    </html>
  );
}"""

_DASHBOARD = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';
import Link from 'next/link';

const CLASS_TYPE_EMOJI: Record<string, string> = { YOGA: '🧘', PILATES: '🏋️', CROSSFIT: '🔥', SPINNING: '🚴', BOXING: '🥊', ZUMBA: '💃', STRENGTH: '💪', CARDIO: '❤️', SWIMMING: '🏊', STRETCHING: '🤸' };
const DAY_ES: Record<string, string> = { MONDAY: 'Lunes', TUESDAY: 'Martes', WEDNESDAY: 'Miércoles', THURSDAY: 'Jueves', FRIDAY: 'Viernes', SATURDAY: 'Sábado', SUNDAY: 'Domingo' };

export default function DashboardPage() {
  const user = useAuthStore(s => s.user);
  const { data: membership } = trpc.memberships.mine.useQuery(undefined, { enabled: !!user });
  const { data: bookings }   = trpc.bookings.myBookings.useQuery({ upcoming: true }, { enabled: !!user });
  const { data: sessions }   = trpc.sessions.upcoming.useQuery({ days: 7 }, { enabled: !!user });

  if (!user) return (
    <main className="flex min-h-[80vh] flex-col items-center justify-center gap-6">
      <h1 className="text-4xl font-bold text-orange-500">💪 __NAME__</h1>
      <p className="text-zinc-400">Tu gimnasio, a un click de distancia</p>
      <Link href="/login" className="rounded-xl bg-orange-500 px-8 py-3 font-bold text-white hover:bg-orange-600">Acceder</Link>
    </main>
  );

  const daysLeft = membership?.endDate ? Math.ceil((new Date(membership.endDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : null;

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h2 className="mb-6 text-xl font-semibold text-zinc-300">Hola, {user.name.split(' ')[0]} 👋</h2>

      {/* Membership card */}
      <div className={`mb-6 rounded-2xl p-5 ${membership?.status === 'ACTIVE' ? 'bg-gradient-to-r from-orange-600 to-amber-500' : 'bg-zinc-800 border border-zinc-700'}`}>
        {membership?.status === 'ACTIVE' ? (
          <>
            <p className="text-sm text-orange-100">Membresía activa</p>
            <p className="text-2xl font-bold">{membership.plan.name}</p>
            <p className="text-sm text-orange-100 mt-1">Vence en {daysLeft} días — {new Date(membership.endDate).toLocaleDateString('es-ES')}</p>
          </>
        ) : (
          <>
            <p className="text-zinc-400 text-sm">Sin membresía activa</p>
            <Link href="/membresia" className="mt-2 inline-block rounded-lg bg-orange-500 px-4 py-2 text-sm font-bold text-white">Suscribirse</Link>
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Upcoming bookings */}
        <div className="rounded-2xl bg-zinc-900 p-5">
          <p className="mb-3 font-semibold text-zinc-300">Mis próximas clases</p>
          <div className="space-y-3">
            {bookings?.slice(0, 4).map(b => (
              <div key={b.id} className="flex items-center gap-3 rounded-xl bg-zinc-800 p-3">
                <span className="text-2xl">{CLASS_TYPE_EMOJI[b.session.gymClass.type] ?? '💪'}</span>
                <div className="flex-1">
                  <p className="font-medium text-sm">{b.session.gymClass.name}</p>
                  <p className="text-xs text-zinc-400">{new Date(b.session.date).toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric', month: 'short' })} · {b.session.gymClass.startTime}</p>
                </div>
              </div>
            ))}
            {!bookings?.length && <p className="text-zinc-500 text-sm">Sin reservas. <Link href="/clases" className="text-orange-400 hover:underline">Reservar clase</Link></p>}
          </div>
        </div>

        {/* Upcoming sessions this week */}
        <div className="rounded-2xl bg-zinc-900 p-5">
          <p className="mb-3 font-semibold text-zinc-300">Clases esta semana</p>
          <div className="space-y-2">
            {sessions?.slice(0, 5).map(s => (
              <div key={s.id} className="flex items-center justify-between rounded-xl bg-zinc-800 px-3 py-2">
                <div className="flex items-center gap-2">
                  <span>{CLASS_TYPE_EMOJI[s.gymClass.type] ?? '💪'}</span>
                  <div>
                    <p className="text-sm font-medium">{s.gymClass.name}</p>
                    <p className="text-xs text-zinc-500">{new Date(s.date).toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric' })} · {s.gymClass.startTime}</p>
                  </div>
                </div>
                <span className="text-xs text-zinc-400">{s._count.bookings}/{s.gymClass.maxCapacity}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}"""

_CLASSES_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const CLASS_TYPE_EMOJI: Record<string, string> = { YOGA: '🧘', PILATES: '🏋️', CROSSFIT: '🔥', SPINNING: '🚴', BOXING: '🥊', ZUMBA: '💃', STRENGTH: '💪', CARDIO: '❤️', SWIMMING: '🏊', STRETCHING: '🤸' };
const DAY_ORDER = ['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY'];
const DAY_ES: Record<string, string> = { MONDAY: 'Lunes', TUESDAY: 'Martes', WEDNESDAY: 'Miércoles', THURSDAY: 'Jueves', FRIDAY: 'Viernes', SATURDAY: 'Sábado', SUNDAY: 'Domingo' };

export default function ClasesPage() {
  const user = useAuthStore(s => s.user);
  const [filter, setFilter] = useState<string>('');
  const { data: classes } = trpc.classes.list.useQuery();
  const { data: sessions, refetch } = trpc.sessions.upcoming.useQuery({ days: 7 });
  const book = trpc.bookings.book.useMutation({ onSuccess: () => refetch() });

  const grouped = DAY_ORDER.reduce((acc, day) => {
    const dayClasses = classes?.filter(c => c.dayOfWeek === day && (!filter || c.type === filter)) ?? [];
    if (dayClasses.length > 0) acc[day] = dayClasses;
    return acc;
  }, {} as Record<string, typeof classes>);

  const getNextSession = (gymClassId: string) => sessions?.find(s => s.gymClass.id === gymClassId);

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Horario de clases</h1>
        <select value={filter} onChange={e => setFilter(e.target.value)}
          className="ml-auto rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-300">
          <option value="">Todas las actividades</option>
          {['YOGA','PILATES','CROSSFIT','SPINNING','BOXING','ZUMBA','STRENGTH','CARDIO','SWIMMING','STRETCHING'].map(t => (
            <option key={t} value={t}>{CLASS_TYPE_EMOJI[t]} {t}</option>
          ))}
        </select>
      </div>

      <div className="space-y-6">
        {Object.entries(grouped).map(([day, dayClasses]) => (
          <div key={day}>
            <p className="mb-3 text-sm font-bold uppercase tracking-wide text-orange-500">{DAY_ES[day]}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {dayClasses?.map(c => {
                const next = getNextSession(c.id);
                const spots = next ? c.maxCapacity - next._count.bookings : c.maxCapacity;
                return (
                  <div key={c.id} className="rounded-xl border border-zinc-700 bg-zinc-900 p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-bold">{CLASS_TYPE_EMOJI[c.type]} {c.name}</p>
                        <p className="text-xs text-zinc-400">{c.startTime} · {c.durationMin} min · {c.room ?? 'Sala'}</p>
                        <p className="text-xs text-zinc-500 mt-0.5">👤 {c.trainer.user.name}</p>
                      </div>
                      <span className={`text-xs rounded-full px-2 py-0.5 ${spots > 0 ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                        {spots > 0 ? `${spots} plazas` : 'Completo'}
                      </span>
                    </div>
                    {c.description && <p className="mt-2 text-xs text-zinc-500 line-clamp-2">{c.description}</p>}
                    {user && next && spots > 0 && (
                      <button onClick={() => book.mutate(next.id)} disabled={book.isPending}
                        className="mt-3 w-full rounded-lg bg-orange-500 py-2 text-sm font-bold text-white hover:bg-orange-600 disabled:opacity-50">
                        Reservar próxima sesión
                      </button>
                    )}
                    {!user && <p className="mt-2 text-xs text-zinc-500">Inicia sesión para reservar</p>}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_BOOKINGS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const CLASS_TYPE_EMOJI: Record<string, string> = { YOGA: '🧘', PILATES: '🏋️', CROSSFIT: '🔥', SPINNING: '🚴', BOXING: '🥊', ZUMBA: '💃', STRENGTH: '💪', CARDIO: '❤️', SWIMMING: '🏊', STRETCHING: '🤸' };

export default function ReservasPage() {
  const user = useAuthStore(s => s.user);
  const { data, refetch } = trpc.bookings.myBookings.useQuery({ upcoming: true }, { enabled: !!user });
  const cancel = trpc.bookings.cancel.useMutation({ onSuccess: () => refetch() });

  if (!user) return <main className="p-8 text-center text-zinc-400">Inicia sesión para ver tus reservas.</main>;

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Mis reservas</h1>
      {data?.length === 0 && (
        <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-8 text-center">
          <p className="text-zinc-400">Sin reservas próximas.</p>
          <a href="/clases" className="mt-3 inline-block text-orange-400 hover:underline">Ver horario de clases →</a>
        </div>
      )}
      <div className="space-y-3">
        {data?.map(b => {
          const cls     = b.session.gymClass;
          const session = b.session;
          const isPast  = new Date(session.date) < new Date();
          return (
            <div key={b.id} className="flex items-center gap-4 rounded-xl border border-zinc-700 bg-zinc-900 p-4">
              <span className="text-3xl">{CLASS_TYPE_EMOJI[cls.type] ?? '💪'}</span>
              <div className="flex-1">
                <p className="font-bold">{cls.name}</p>
                <p className="text-sm text-zinc-400">{new Date(session.date).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })} · {cls.startTime}</p>
                <p className="text-xs text-zinc-500">{cls.room ?? ''} · {cls.durationMin} min</p>
              </div>
              {!isPast && (
                <button onClick={() => cancel.mutate(session.id)} disabled={cancel.isPending}
                  className="rounded-lg border border-red-800 px-3 py-1.5 text-xs text-red-400 hover:bg-red-900/30 disabled:opacity-50">
                  Cancelar
                </button>
              )}
              {isPast && b.attendedAt && <span className="text-xs text-green-400">✓ Asistido</span>}
              {isPast && !b.attendedAt && <span className="text-xs text-zinc-500">No asistido</span>}
            </div>
          );
        })}
      </div>
    </main>
  );
}"""

_MEMBERSHIP_PAGE = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

export default function MembresiaPage() {
  const user = useAuthStore(s => s.user);
  const { data: current, refetch } = trpc.memberships.mine.useQuery(undefined, { enabled: !!user });
  const { data: plans }             = trpc.memberships.plans.useQuery();
  const subscribe = trpc.memberships.subscribe.useMutation({ onSuccess: () => refetch() });
  const cancel    = trpc.memberships.cancel.useMutation({ onSuccess: () => refetch() });

  if (!user) return <main className="p-8 text-center text-zinc-400">Inicia sesión para gestionar tu membresía.</main>;

  const daysLeft = current?.endDate ? Math.ceil((new Date(current.endDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : null;

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Membresía</h1>

      {/* Current status */}
      {current?.status === 'ACTIVE' && (
        <div className="mb-6 rounded-2xl bg-gradient-to-r from-orange-600 to-amber-500 p-5">
          <p className="text-sm text-orange-100">Plan activo</p>
          <p className="text-2xl font-bold">{current.plan.name}</p>
          <p className="text-sm text-orange-100 mt-1">{daysLeft} días restantes · vence el {new Date(current.endDate).toLocaleDateString('es-ES')}</p>
          <button onClick={() => cancel.mutate()} disabled={cancel.isPending}
            className="mt-3 rounded-lg border border-orange-200 px-4 py-1.5 text-sm text-orange-100 hover:bg-orange-700/50">
            Cancelar membresía
          </button>
        </div>
      )}
      {(!current || current.status !== 'ACTIVE') && (
        <div className="mb-6 rounded-2xl border border-zinc-700 bg-zinc-900 p-5 text-center">
          <p className="text-zinc-400">Sin membresía activa</p>
          <p className="text-xs text-zinc-500 mt-1">Elige un plan para empezar</p>
        </div>
      )}

      {/* Plans */}
      <h2 className="mb-4 font-semibold text-zinc-300">Planes disponibles</h2>
      <div className="grid gap-4">
        {plans?.map(p => (
          <div key={p.id} className={`rounded-xl border p-4 ${p.durationDays >= 365 ? 'border-orange-500 bg-orange-950/30' : 'border-zinc-700 bg-zinc-900'}`}>
            <div className="flex items-start justify-between">
              <div>
                <p className="font-bold text-lg">{p.name}</p>
                {p.description && <p className="text-sm text-zinc-400">{p.description}</p>}
                <p className="text-xs text-zinc-500 mt-1">{p.durationDays >= 365 ? `${p.durationDays / 365} año` : `${p.durationDays} días`}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-orange-400">{Number(p.price).toFixed(2)} €</p>
                <p className="text-xs text-zinc-500">{p.durationDays >= 365 ? '/año' : '/mes'}</p>
              </div>
            </div>
            <button onClick={() => subscribe.mutate({ planId: p.id })} disabled={subscribe.isPending}
              className="mt-3 w-full rounded-lg bg-orange-500 py-2 text-sm font-bold text-white hover:bg-orange-600 disabled:opacity-50">
              {current?.planId === p.id && current.status === 'ACTIVE' ? 'Renovar' : 'Suscribirse'}
            </button>
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
      POSTGRES_USER: gymapp
      POSTGRES_PASSWORD: gym_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://gymapp:gym_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://gymapp:gym_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Gestión de Gimnasio

Sistema completo para gimnasios: membresías, clases grupales, reservas y check-in de asistentes.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS (dark theme)
- **Auth:** JWT con roles (ADMIN, TRAINER, MEMBER)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Membresías | Planes configurables por días + suscripción/cancelación; membresía requerida para reservar |
| Clases | Horario semanal por tipo (Yoga, CrossFit, Spinning, etc.) con capacidad y entrenador |
| Sesiones | Instancias semanales de cada clase con conteo de plazas disponibles |
| Reservas | Book/cancel inline; check-in de asistencia por entrenador |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin:   admin@gym.com / password123
Trainer: carlos@gym.com / sofia@gym.com / password123
Member:  miembro@gym.com / password123
"""
