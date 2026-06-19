"""
EVENTOS template — plataforma de gestión de eventos y venta de entradas.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: eventos, entradas (ticket types), órdenes, check-in, asistentes.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",                          "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",                          "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",                           "typescript", _API_INDEX.replace("__NAME__", name)),
        _f("apps/api/src/trpc.ts",                            "typescript", _TRPC),
        _f("apps/api/src/router.ts",                          "typescript", _ROUTER),
        _f("apps/api/prisma/schema.prisma",                   "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",                         "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",        "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/events/event.router.ts",     "typescript", _EVENT_ROUTER),
        _f("apps/api/src/modules/tickets/ticket.router.ts",   "typescript", _TICKET_ROUTER),
        _f("apps/api/src/modules/orders/order.router.ts",     "typescript", _ORDER_ROUTER),
        _f("apps/api/src/modules/checkin/checkin.router.ts",  "typescript", _CHECKIN_ROUTER),
        _f("apps/api/Dockerfile",                             "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",                           "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",                          "json",       _WEB_TSCONFIG),
        _f("apps/web/next.config.js",                         "javascript", _NEXT_CONFIG),
        _f("apps/web/tailwind.config.ts",                     "typescript", _TAILWIND),
        _f("apps/web/postcss.config.js",                      "javascript", _POSTCSS),
        _f("apps/web/src/app/globals.css",                    "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",                        "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",                   "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts",                  "typescript", _AUTH_STORE),
        _f("apps/web/src/app/layout.tsx",                     "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",                       "typescript", _LANDING.replace("__NAME__", name)),
        _f("apps/web/src/app/eventos/page.tsx",               "typescript", _EVENTS_PAGE),
        _f("apps/web/src/app/mis-entradas/page.tsx",          "typescript", _MY_TICKETS_PAGE),
        _f("apps/web/src/app/checkin/page.tsx",               "typescript", _CHECKIN_PAGE),
        _f("apps/web/Dockerfile",                             "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",                                "nginx",      _NGINX),
        _f("docker-compose.yml",                              "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                                    "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                                       "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
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
console.log(`🎪 __NAME__ API running on port ${port}`);"""

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
export const organizerProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'ORGANIZER'].includes(ctx.userRole ?? ''))
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
import { eventRouter }   from './modules/events/event.router';
import { ticketRouter }  from './modules/tickets/ticket.router';
import { orderRouter }   from './modules/orders/order.router';
import { checkinRouter } from './modules/checkin/checkin.router';

export const appRouter = router({
  auth:    authRouter,
  events:  eventRouter,
  tickets: ticketRouter,
  orders:  orderRouter,
  checkin: checkinRouter,
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
  ORGANIZER
  ATTENDEE
}

enum EventStatus {
  DRAFT
  PUBLISHED
  CANCELLED
  COMPLETED
}

enum TicketTier {
  GENERAL
  VIP
  BACKSTAGE
  EARLY_BIRD
  STUDENT
}

enum OrderStatus {
  PENDING
  CONFIRMED
  CANCELLED
  REFUNDED
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         UserRole  @default(ATTENDEE)
  phone        String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  events       Event[]
  orders       Order[]
}

model Venue {
  id       String  @id @default(cuid())
  name     String
  address  String
  city     String
  capacity Int?
  mapUrl   String?
  events   Event[]
}

model Event {
  id           String      @id @default(cuid())
  organizerId  String
  organizer    User        @relation(fields: [organizerId], references: [id])
  venueId      String?
  venue        Venue?      @relation(fields: [venueId], references: [id])
  title        String
  slug         String      @unique
  description  String?
  imageUrl     String?
  category     String?
  tags         String[]
  status       EventStatus @default(DRAFT)
  startsAt     DateTime
  endsAt       DateTime
  isOnline     Boolean     @default(false)
  onlineUrl    String?
  maxAttendees Int?
  createdAt    DateTime    @default(now())
  updatedAt    DateTime    @updatedAt
  ticketTypes  TicketType[]
  orders       Order[]
}

model TicketType {
  id          String     @id @default(cuid())
  eventId     String
  event       Event      @relation(fields: [eventId], references: [id], onDelete: Cascade)
  tier        TicketTier @default(GENERAL)
  name        String
  description String?
  price       Decimal    @db.Decimal(10, 2) @default(0)
  quantity    Int
  sold        Int        @default(0)
  saleStart   DateTime?
  saleEnd     DateTime?
  createdAt   DateTime   @default(now())
  orderItems  OrderItem[]
}

model Order {
  id          String      @id @default(cuid())
  userId      String
  user        User        @relation(fields: [userId], references: [id])
  eventId     String
  event       Event       @relation(fields: [eventId], references: [id])
  status      OrderStatus @default(PENDING)
  total       Decimal     @db.Decimal(10, 2)
  reference   String      @unique @default(cuid())
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
  items       OrderItem[]
  attendees   Attendee[]
}

model OrderItem {
  id           String     @id @default(cuid())
  orderId      String
  order        Order      @relation(fields: [orderId], references: [id], onDelete: Cascade)
  ticketTypeId String
  ticketType   TicketType @relation(fields: [ticketTypeId], references: [id])
  quantity     Int
  unitPrice    Decimal    @db.Decimal(10, 2)
  total        Decimal    @db.Decimal(10, 2)
}

model Attendee {
  id          String   @id @default(cuid())
  orderId     String
  order       Order    @relation(fields: [orderId], references: [id], onDelete: Cascade)
  name        String
  email       String
  ticketCode  String   @unique @default(cuid())
  checkedIn   Boolean  @default(false)
  checkedInAt DateTime?
  createdAt   DateTime @default(now())
}"""

_SEED = """import { PrismaClient, UserRole, TicketTier } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Eventos...');

  const hash = await bcrypt.hash('password123', 10);

  await prisma.user.upsert({
    where: { email: 'admin@eventos.com' },
    update: {},
    create: { email: 'admin@eventos.com', name: 'Admin', passwordHash: hash, role: UserRole.ADMIN },
  });

  const organizer = await prisma.user.upsert({
    where: { email: 'org@eventos.com' },
    update: {},
    create: { email: 'org@eventos.com', name: 'Productora EventosPro', passwordHash: hash, role: UserRole.ORGANIZER },
  });

  const attendee = await prisma.user.upsert({
    where: { email: 'asistente@email.com' },
    update: {},
    create: { email: 'asistente@email.com', name: 'Marta Asistente', passwordHash: hash, role: UserRole.ATTENDEE },
  });

  const venue = await prisma.venue.create({
    data: { name: 'Sala Gran Teatro', address: 'Calle Cultura 15', city: 'Madrid', capacity: 500 },
  });

  const futureDate = new Date();
  futureDate.setMonth(futureDate.getMonth() + 2);

  const event = await prisma.event.create({
    data: {
      organizerId: organizer.id,
      venueId: venue.id,
      title: 'Tech Summit Madrid 2026',
      slug: 'tech-summit-madrid-2026',
      description: 'La conferencia de tecnología más importante del año. Ponentes internacionales, talleres y networking.',
      category: 'Tecnología',
      tags: ['tech', 'IA', 'startup', 'networking'],
      status: 'PUBLISHED',
      startsAt: new Date(futureDate.getFullYear(), futureDate.getMonth(), futureDate.getDate(), 9, 0),
      endsAt:   new Date(futureDate.getFullYear(), futureDate.getMonth(), futureDate.getDate(), 19, 0),
      maxAttendees: 500,
    },
  });

  const generalTicket = await prisma.ticketType.create({
    data: { eventId: event.id, tier: TicketTier.GENERAL, name: 'Entrada General', price: 49.00, quantity: 400, sold: 12 },
  });
  await prisma.ticketType.create({
    data: { eventId: event.id, tier: TicketTier.VIP, name: 'VIP — Acceso total + afterparty', price: 149.00, quantity: 80, sold: 3 },
  });
  await prisma.ticketType.create({
    data: { eventId: event.id, tier: TicketTier.EARLY_BIRD, name: 'Early Bird (agotado)', price: 29.00, quantity: 50, sold: 50, saleEnd: new Date() },
  });

  // Sample order
  const order = await prisma.order.create({
    data: {
      userId: attendee.id, eventId: event.id, status: 'CONFIRMED', total: 98.00,
      items: { create: [{ ticketTypeId: generalTicket.id, quantity: 2, unitPrice: 49.00, total: 98.00 }] },
    },
  });
  await prisma.attendee.createMany({
    data: [
      { orderId: order.id, name: 'Marta Asistente', email: 'asistente@email.com' },
      { orderId: order.id, name: 'Pedro Acompañante', email: 'pedro@email.com' },
    ],
  });

  console.log('✅ Seed completado.');
  console.log('   Admin:     admin@eventos.com / password123');
  console.log('   Organizer: org@eventos.com / password123');
  console.log('   Attendee:  asistente@email.com / password123');
}

main().catch(console.error).finally(() => prisma.$disconnect());"""

_AUTH_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';
import bcrypt from 'bcryptjs';

export const authRouter = router({
  register: publicProcedure
    .input(z.object({ email: z.string().email(), name: z.string().min(2), password: z.string().min(8) }))
    .mutation(async ({ input }) => {
      if (await prisma.user.findUnique({ where: { email: input.email } })) throw new Error('Email ya registrado');
      const passwordHash = await bcrypt.hash(input.password, 10);
      return prisma.user.create({ data: { email: input.email, name: input.name, passwordHash }, select: { id: true, email: true, name: true, role: true } });
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
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true, phone: true } })
  ),
});"""

_EVENT_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, protectedProcedure, organizerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const eventInput = z.object({
  title:       z.string().min(3),
  slug:        z.string().min(3),
  description: z.string().optional(),
  category:    z.string().optional(),
  tags:        z.string().array().default([]),
  startsAt:    z.string(),
  endsAt:      z.string(),
  isOnline:    z.boolean().default(false),
  onlineUrl:   z.string().url().optional(),
  maxAttendees: z.number().int().positive().optional(),
  imageUrl:    z.string().url().optional(),
});

export const eventRouter = router({
  list: publicProcedure
    .input(z.object({ category: z.string().optional(), upcoming: z.boolean().default(true) }).optional())
    .query(({ input }) =>
      prisma.event.findMany({
        where: {
          status: 'PUBLISHED',
          ...(input?.category && { category: input.category }),
          ...(input?.upcoming !== false && { startsAt: { gte: new Date() } }),
        },
        include: { venue: true, organizer: { select: { name: true } }, ticketTypes: true, _count: { select: { orders: true } } },
        orderBy: { startsAt: 'asc' },
      })
    ),

  bySlug: publicProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.event.findUnique({
        where: { slug: input },
        include: { venue: true, organizer: { select: { name: true } }, ticketTypes: { orderBy: { price: 'asc' } } },
      })
    ),

  myEvents: organizerProcedure
    .query(({ ctx }) =>
      prisma.event.findMany({
        where: { organizerId: ctx.userId },
        include: { _count: { select: { orders: true } }, ticketTypes: true },
        orderBy: { startsAt: 'desc' },
      })
    ),

  create: organizerProcedure
    .input(eventInput)
    .mutation(({ input, ctx }) =>
      prisma.event.create({ data: { ...input, organizerId: ctx.userId, startsAt: new Date(input.startsAt), endsAt: new Date(input.endsAt) } })
    ),

  publish: organizerProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.event.update({ where: { id: input }, data: { status: 'PUBLISHED' } })),

  cancel: organizerProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.event.update({ where: { id: input }, data: { status: 'CANCELLED' } })),
});"""

_TICKET_ROUTER = """import { z } from 'zod';
import { router, organizerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const ticketRouter = router({
  create: organizerProcedure
    .input(z.object({
      eventId:     z.string(),
      tier:        z.enum(['GENERAL', 'VIP', 'BACKSTAGE', 'EARLY_BIRD', 'STUDENT']),
      name:        z.string().min(2),
      description: z.string().optional(),
      price:       z.number().min(0),
      quantity:    z.number().int().min(1),
      saleStart:   z.string().optional(),
      saleEnd:     z.string().optional(),
    }))
    .mutation(({ input }) =>
      prisma.ticketType.create({
        data: {
          ...input,
          saleStart: input.saleStart ? new Date(input.saleStart) : undefined,
          saleEnd:   input.saleEnd   ? new Date(input.saleEnd)   : undefined,
        },
      })
    ),

  update: organizerProcedure
    .input(z.object({ id: z.string(), quantity: z.number().int().positive().optional(), price: z.number().min(0).optional(), name: z.string().optional() }))
    .mutation(({ input: { id, ...data } }) => prisma.ticketType.update({ where: { id }, data })),
});"""

_ORDER_ROUTER = """import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const orderRouter = router({
  myOrders: protectedProcedure.query(({ ctx }) =>
    prisma.order.findMany({
      where: { userId: ctx.userId },
      include: { event: { select: { title: true, startsAt: true, venue: true } }, items: { include: { ticketType: true } }, attendees: true },
      orderBy: { createdAt: 'desc' },
    })
  ),

  purchase: protectedProcedure
    .input(z.array(z.object({ ticketTypeId: z.string(), quantity: z.number().int().min(1) })).min(1))
    .mutation(async ({ input, ctx }) => {
      // Validate availability
      const ticketTypes = await Promise.all(
        input.map(i => prisma.ticketType.findUniqueOrThrow({ where: { id: i.ticketTypeId } }))
      );

      for (let i = 0; i < input.length; i++) {
        const tt = ticketTypes[i];
        const remaining = tt.quantity - tt.sold;
        if (remaining < input[i].quantity)
          throw new TRPCError({ code: 'BAD_REQUEST', message: `Solo quedan ${remaining} entradas para "${tt.name}"` });
      }

      const eventId = ticketTypes[0].eventId;
      const total   = input.reduce((s, i, idx) => s + Number(ticketTypes[idx].price) * i.quantity, 0);
      const user    = await prisma.user.findUniqueOrThrow({ where: { id: ctx.userId } });

      const order = await prisma.order.create({
        data: {
          userId: ctx.userId, eventId, total, status: 'CONFIRMED',
          items: {
            create: input.map((i, idx) => ({
              ticketTypeId: i.ticketTypeId,
              quantity:     i.quantity,
              unitPrice:    ticketTypes[idx].price,
              total:        Number(ticketTypes[idx].price) * i.quantity,
            })),
          },
          attendees: {
            create: input.flatMap((i, idx) =>
              Array.from({ length: i.quantity }, (_, k) => ({
                name:  k === 0 ? user.name  : `Acompañante ${k + 1}`,
                email: k === 0 ? user.email : `acompanante${k + 1}@placeholder.com`,
              }))
            ),
          },
        },
        include: { attendees: true, items: { include: { ticketType: true } } },
      });

      // Update sold counts
      await Promise.all(input.map(i => prisma.ticketType.update({ where: { id: i.ticketTypeId }, data: { sold: { increment: i.quantity } } })));

      return order;
    }),
});"""

_CHECKIN_ROUTER = """import { z } from 'zod';
import { router, organizerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const checkinRouter = router({
  scan: organizerProcedure
    .input(z.string())
    .mutation(async ({ input }) => {
      const attendee = await prisma.attendee.findUnique({ where: { ticketCode: input }, include: { order: { include: { event: { select: { title: true, startsAt: true } } } } } });
      if (!attendee) throw new Error('Código de entrada no válido');
      if (attendee.checkedIn) throw new Error('Esta entrada ya fue utilizada');
      await prisma.attendee.update({ where: { id: attendee.id }, data: { checkedIn: true, checkedInAt: new Date() } });
      return { ok: true, attendee: { name: attendee.name, email: attendee.email, event: attendee.order.event.title } };
    }),

  listByEvent: organizerProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.attendee.findMany({
        where: { order: { eventId: input } },
        include: { order: { select: { status: true } } },
        orderBy: { checkedIn: 'desc' },
      })
    ),

  stats: organizerProcedure
    .input(z.string())
    .query(async ({ input }) => {
      const [total, checkedIn] = await prisma.$transaction([
        prisma.attendee.count({ where: { order: { eventId: input } } }),
        prisma.attendee.count({ where: { order: { eventId: input }, checkedIn: true } }),
      ]);
      return { total, checkedIn, pending: total - checkedIn, rate: total > 0 ? Math.round((checkedIn / total) * 100) : 0 };
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
export const metadata: Metadata = { title: '__NAME__', description: 'Plataforma de eventos' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-stone-50 text-stone-900">
        <TRPCProvider>{children}</TRPCProvider>
      </body>
    </html>
  );
}"""

_LANDING = """'use client';
import { trpc } from '@/lib/trpc';
import Link from 'next/link';
import { useAuthStore } from '@/lib/auth-store';

const TIER_COLORS: Record<string, string> = { GENERAL: 'bg-stone-100 text-stone-700', VIP: 'bg-amber-100 text-amber-700', BACKSTAGE: 'bg-purple-100 text-purple-700', EARLY_BIRD: 'bg-green-100 text-green-700', STUDENT: 'bg-blue-100 text-blue-700' };

export default function HomePage() {
  const user = useAuthStore(s => s.user);
  const { data: events } = trpc.events.list.useQuery({ upcoming: true });

  return (
    <main>
      {/* Hero */}
      <section className="bg-gradient-to-br from-rose-600 to-orange-500 px-6 py-20 text-center text-white">
        <h1 className="text-5xl font-bold mb-3">🎪 __NAME__</h1>
        <p className="text-xl opacity-90 mb-8">Descubre y reserva los mejores eventos</p>
        <div className="flex justify-center gap-3">
          <Link href="/eventos" className="rounded-full bg-white px-8 py-3 font-bold text-rose-600 hover:bg-rose-50">Ver eventos</Link>
          {user && <Link href="/mis-entradas" className="rounded-full border-2 border-white px-8 py-3 font-bold text-white hover:bg-white/20">Mis entradas</Link>}
        </div>
      </section>

      {/* Upcoming events */}
      <section className="mx-auto max-w-5xl px-6 py-12">
        <h2 className="mb-6 text-2xl font-bold">Próximos eventos</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {events?.map(e => (
            <Link key={e.id} href={`/eventos/${e.slug}`}
              className="overflow-hidden rounded-2xl border bg-white shadow-sm hover:shadow-md transition group">
              <div className="h-44 bg-gradient-to-br from-rose-100 to-orange-100 flex items-center justify-center text-5xl group-hover:scale-105 transition">🎪</div>
              <div className="p-4">
                {e.category && <span className="text-xs font-medium text-rose-600 bg-rose-50 rounded-full px-2 py-0.5">{e.category}</span>}
                <h3 className="mt-2 font-bold leading-tight">{e.title}</h3>
                <p className="mt-1 text-sm text-stone-500">
                  {new Date(e.startsAt).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                </p>
                {e.venue && <p className="text-xs text-stone-400">{e.venue.name}, {e.venue.city}</p>}
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-sm font-bold text-rose-600">
                    {e.ticketTypes.length > 0 ? `Desde ${Math.min(...e.ticketTypes.map(t => Number(t.price))).toFixed(2)} €` : 'Gratis'}
                  </span>
                  <span className="text-xs text-stone-400">{e._count.orders} órdenes</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}"""

_EVENTS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';
import { useRouter } from 'next/navigation';

const TIER_LABELS: Record<string, string> = { GENERAL: 'General', VIP: 'VIP', BACKSTAGE: 'Backstage', EARLY_BIRD: 'Early Bird', STUDENT: 'Estudiante' };

export default function EventosPage() {
  const user   = useAuthStore(s => s.user);
  const router = useRouter();
  const { data: events } = trpc.events.list.useQuery();
  const purchase = trpc.orders.purchase.useMutation({
    onSuccess: () => router.push('/mis-entradas'),
  });

  const [buying, setBuying] = useState<string | null>(null);

  const handleBuy = (ticketTypeId: string) => {
    if (!user) { alert('Inicia sesión para comprar entradas'); return; }
    purchase.mutate([{ ticketTypeId, quantity: 1 }]);
  };

  return (
    <main className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold">Todos los eventos</h1>
      <div className="space-y-6">
        {events?.map(e => (
          <div key={e.id} className="overflow-hidden rounded-2xl border bg-white shadow-sm">
            <div className="flex gap-4 p-5">
              <div className="h-24 w-24 shrink-0 rounded-xl bg-gradient-to-br from-rose-100 to-orange-100 flex items-center justify-center text-3xl">🎪</div>
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <h2 className="font-bold text-lg leading-tight">{e.title}</h2>
                  {e.category && <span className="ml-2 shrink-0 text-xs bg-rose-50 text-rose-600 rounded-full px-2 py-0.5">{e.category}</span>}
                </div>
                <p className="text-sm text-stone-500 mt-0.5">
                  {new Date(e.startsAt).toLocaleDateString('es-ES', { dateStyle: 'long' })} · {e.venue?.name ?? 'Online'}
                </p>
                {e.description && <p className="mt-1 text-sm text-stone-600 line-clamp-2">{e.description}</p>}
              </div>
            </div>
            {/* Ticket types */}
            <div className="border-t bg-stone-50 px-5 py-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">Entradas disponibles</p>
              <div className="flex flex-wrap gap-2">
                {e.ticketTypes.map(tt => {
                  const available = tt.quantity - tt.sold;
                  return (
                    <div key={tt.id} className="flex items-center gap-2 rounded-xl border bg-white px-3 py-2">
                      <div>
                        <p className="text-sm font-medium">{tt.name}</p>
                        <p className="text-xs text-stone-400">{available > 0 ? `${available} disponibles` : 'Agotado'}</p>
                      </div>
                      <div className="ml-2 text-right">
                        <p className="font-bold text-rose-600">{Number(tt.price) === 0 ? 'Gratis' : `${Number(tt.price).toFixed(2)} €`}</p>
                      </div>
                      {available > 0 && (
                        <button onClick={() => handleBuy(tt.id)} disabled={purchase.isPending}
                          className="ml-2 rounded-lg bg-rose-600 px-3 py-1 text-xs text-white hover:bg-rose-700 disabled:opacity-50">
                          Comprar
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_MY_TICKETS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const STATUS_COLORS: Record<string, string> = { CONFIRMED: 'bg-green-100 text-green-700', PENDING: 'bg-yellow-100 text-yellow-700', CANCELLED: 'bg-red-100 text-red-700', REFUNDED: 'bg-stone-100 text-stone-600' };
const STATUS_LABELS: Record<string, string> = { CONFIRMED: 'Confirmada', PENDING: 'Pendiente', CANCELLED: 'Cancelada', REFUNDED: 'Reembolsada' };

export default function MisEntradasPage() {
  const user = useAuthStore(s => s.user);
  const { data, isLoading } = trpc.orders.myOrders.useQuery(undefined, { enabled: !!user });

  if (!user) return <main className="mx-auto max-w-lg px-6 py-16 text-center"><p className="text-stone-500">Inicia sesión para ver tus entradas.</p></main>;
  if (isLoading) return <p className="p-8 text-stone-400">Cargando...</p>;

  return (
    <main className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold">Mis entradas</h1>
      {data?.length === 0 && <p className="text-stone-400">No tienes entradas todavía.</p>}
      <div className="space-y-4">
        {data?.map(order => (
          <div key={order.id} className="overflow-hidden rounded-2xl border bg-white shadow-sm">
            <div className="flex items-center justify-between border-b bg-stone-50 px-5 py-3">
              <div>
                <p className="font-bold">{order.event.title}</p>
                <p className="text-xs text-stone-400">{new Date(order.event.startsAt).toLocaleDateString('es-ES', { dateStyle: 'long' })}</p>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[order.status]}`}>{STATUS_LABELS[order.status]}</span>
            </div>
            <div className="p-5">
              <p className="mb-3 text-sm text-stone-500">Entradas ({order.attendees.length})</p>
              <div className="space-y-2">
                {order.attendees.map(a => (
                  <div key={a.id} className="flex items-center justify-between rounded-xl border p-3">
                    <div>
                      <p className="text-sm font-medium">{a.name}</p>
                      <p className="text-xs text-stone-400">{a.email}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-xs font-bold text-rose-600">{a.ticketCode.slice(-8).toUpperCase()}</p>
                      {a.checkedIn ? <p className="text-xs text-green-600">✓ Usado</p> : <p className="text-xs text-stone-400">No usado</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_CHECKIN_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

export default function CheckinPage() {
  const user = useAuthStore(s => s.user);
  const isOrganizer = user?.role === 'ADMIN' || user?.role === 'ORGANIZER';
  const [code, setCode] = useState('');
  const scan = trpc.checkin.scan.useMutation();

  if (!user || !isOrganizer) return (
    <main className="mx-auto max-w-lg px-6 py-16 text-center">
      <p className="text-stone-500">Acceso solo para organizadores.</p>
    </main>
  );

  return (
    <main className="mx-auto max-w-md px-6 py-12">
      <h1 className="mb-8 text-center text-2xl font-bold">Check-in de entradas</h1>
      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <label className="mb-2 block text-sm font-medium text-stone-700">Código de entrada</label>
        <div className="flex gap-2">
          <input value={code} onChange={e => setCode(e.target.value.toUpperCase())}
            placeholder="Ej: ABC12345"
            className="flex-1 rounded-xl border px-4 py-3 font-mono uppercase tracking-widest text-center text-lg" />
        </div>
        <button onClick={() => { scan.mutate(code); setCode(''); }} disabled={code.length < 3 || scan.isPending}
          className="mt-3 w-full rounded-xl bg-rose-600 py-3 font-bold text-white hover:bg-rose-700 disabled:opacity-50">
          {scan.isPending ? 'Verificando...' : 'Verificar entrada'}
        </button>

        {scan.isSuccess && scan.data.ok && (
          <div className="mt-4 rounded-xl bg-green-50 border border-green-200 p-4 text-center">
            <p className="text-2xl">✅</p>
            <p className="font-bold text-green-800">{scan.data.attendee.name}</p>
            <p className="text-sm text-green-700">{scan.data.attendee.event}</p>
          </div>
        )}
        {scan.isError && (
          <div className="mt-4 rounded-xl bg-red-50 border border-red-200 p-4 text-center">
            <p className="text-2xl">❌</p>
            <p className="text-sm text-red-700">{scan.error.message}</p>
          </div>
        )}
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
      POSTGRES_USER: eventos
      POSTGRES_PASSWORD: eventos_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://eventos:eventos_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://eventos:eventos_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Plataforma de Eventos

Sistema completo de gestión de eventos, venta de entradas y check-in.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, ORGANIZER, ATTENDEE)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Eventos | Creación con tiers de entradas, publicación y cancelación |
| Venta de entradas | Compra con validación de stock, órdenes confirmadas con asistentes |
| Mis entradas | Vista de órdenes con código único por asistente |
| Check-in | Verificación de código en puerta con feedback visual inmediato |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin:     admin@eventos.com / password123
Organizer: org@eventos.com / password123
Attendee:  asistente@email.com / password123
"""
