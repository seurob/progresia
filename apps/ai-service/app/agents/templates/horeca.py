"""
HORECA template — sistema de gestión para restaurante/hostelería.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: carta (menú), mesas, reservas, comandas, personal.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",                  "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",                  "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",                   "typescript", _API_INDEX.replace("__NAME__", name)),
        _f("apps/api/src/trpc.ts",                    "typescript", _TRPC),
        _f("apps/api/src/router.ts",                  "typescript", _ROUTER),
        _f("apps/api/prisma/schema.prisma",           "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",                 "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",              "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/menu/menu.router.ts",              "typescript", _MENU_ROUTER),
        _f("apps/api/src/modules/tables/table.router.ts",           "typescript", _TABLE_ROUTER),
        _f("apps/api/src/modules/reservations/reservation.router.ts", "typescript", _RESERVATION_ROUTER),
        _f("apps/api/src/modules/orders/order.router.ts",           "typescript", _ORDER_ROUTER),
        _f("apps/api/Dockerfile",                     "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",                   "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",                  "json",       _WEB_TSCONFIG),
        _f("apps/web/next.config.js",                 "javascript", _NEXT_CONFIG),
        _f("apps/web/tailwind.config.ts",             "typescript", _TAILWIND),
        _f("apps/web/postcss.config.js",              "javascript", _POSTCSS_CONFIG),
        _f("apps/web/src/app/globals.css",            "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",                "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",           "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts",          "typescript", _AUTH_STORE),
        _f("apps/web/src/app/layout.tsx",             "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",               "typescript", _LANDING.replace("__NAME__", name)),
        _f("apps/web/src/app/carta/page.tsx",         "typescript", _MENU_PAGE),
        _f("apps/web/src/app/reservas/page.tsx",      "typescript", _RESERVATIONS_PAGE),
        _f("apps/web/src/app/comandas/page.tsx",      "typescript", _ORDERS_PAGE),
        _f("apps/web/Dockerfile",                     "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",                        "nginx",      _NGINX),
        _f("docker-compose.yml",                      "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                            "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                               "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
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
console.log(`🍽️ __NAME__ API running on port ${port}`);"""

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
export const staffProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'MANAGER', 'WAITER'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const managerProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'MANAGER'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }        from './modules/auth/auth.router';
import { menuRouter }        from './modules/menu/menu.router';
import { tableRouter }       from './modules/tables/table.router';
import { reservationRouter } from './modules/reservations/reservation.router';
import { orderRouter }       from './modules/orders/order.router';

export const appRouter = router({
  auth:         authRouter,
  menu:         menuRouter,
  tables:       tableRouter,
  reservations: reservationRouter,
  orders:       orderRouter,
});

export type AppRouter = typeof appRouter;"""

_PRISMA_SCHEMA = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum StaffRole {
  ADMIN
  MANAGER
  WAITER
  KITCHEN
}

enum TableStatus {
  FREE
  OCCUPIED
  RESERVED
  CLEANING
}

enum ReservationStatus {
  PENDING
  CONFIRMED
  SEATED
  COMPLETED
  CANCELLED
  NO_SHOW
}

enum OrderStatus {
  OPEN
  IN_KITCHEN
  READY
  SERVED
  PAID
  CANCELLED
}

enum MenuCategory {
  STARTER
  MAIN
  DESSERT
  BEVERAGE
  SPECIAL
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         StaffRole @default(WAITER)
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  orders       Order[]
}

model MenuItem {
  id          String       @id @default(cuid())
  name        String
  description String?
  price       Decimal      @db.Decimal(8, 2)
  category    MenuCategory
  available   Boolean      @default(true)
  imageUrl    String?
  allergens   String[]
  createdAt   DateTime     @default(now())
  updatedAt   DateTime     @updatedAt
  orderLines  OrderLine[]
}

model Table {
  id           String      @id @default(cuid())
  number       Int         @unique
  capacity     Int
  status       TableStatus @default(FREE)
  zone         String?
  createdAt    DateTime    @default(now())
  updatedAt    DateTime    @updatedAt
  reservations Reservation[]
  orders       Order[]
}

model Reservation {
  id          String            @id @default(cuid())
  tableId     String?
  table       Table?            @relation(fields: [tableId], references: [id])
  guestName   String
  guestPhone  String
  guestEmail  String?
  partySize   Int
  scheduledAt DateTime
  status      ReservationStatus @default(PENDING)
  notes       String?
  createdAt   DateTime          @default(now())
  updatedAt   DateTime          @updatedAt
}

model Order {
  id         String      @id @default(cuid())
  tableId    String
  table      Table       @relation(fields: [tableId], references: [id])
  waiterId   String
  waiter     User        @relation(fields: [waiterId], references: [id])
  status     OrderStatus @default(OPEN)
  notes      String?
  total      Decimal?    @db.Decimal(8, 2)
  openedAt   DateTime    @default(now())
  closedAt   DateTime?
  updatedAt  DateTime    @updatedAt
  lines      OrderLine[]
}

model OrderLine {
  id         String   @id @default(cuid())
  orderId    String
  order      Order    @relation(fields: [orderId], references: [id], onDelete: Cascade)
  menuItemId String
  menuItem   MenuItem @relation(fields: [menuItemId], references: [id])
  quantity   Int      @default(1)
  unitPrice  Decimal  @db.Decimal(8, 2)
  notes      String?
  createdAt  DateTime @default(now())
}"""

_SEED = """import { PrismaClient, StaffRole, MenuCategory, TableStatus } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ HORECA...');

  const hash = await bcrypt.hash('password123', 10);

  await prisma.user.upsert({
    where: { email: 'admin@restaurante.com' },
    update: {},
    create: { email: 'admin@restaurante.com', name: 'Admin', passwordHash: hash, role: StaffRole.ADMIN },
  });
  await prisma.user.upsert({
    where: { email: 'manager@restaurante.com' },
    update: {},
    create: { email: 'manager@restaurante.com', name: 'Carlos (Manager)', passwordHash: hash, role: StaffRole.MANAGER },
  });
  await prisma.user.upsert({
    where: { email: 'camarero@restaurante.com' },
    update: {},
    create: { email: 'camarero@restaurante.com', name: 'Ana (Camarera)', passwordHash: hash, role: StaffRole.WAITER },
  });

  // Tables
  for (let i = 1; i <= 10; i++) {
    await prisma.table.upsert({
      where: { number: i },
      update: {},
      create: { number: i, capacity: i <= 5 ? 2 : 4, zone: i <= 5 ? 'Terraza' : 'Interior' },
    });
  }

  // Menu
  const menuItems = [
    { name: 'Ensalada César', description: 'Lechuga romana, pollo, parmesano y croutons', price: 9.50, category: MenuCategory.STARTER, allergens: ['Gluten', 'Lácteos'] },
    { name: 'Croquetas caseras', description: 'Croquetas de jamón ibérico (6 uds)', price: 8.00, category: MenuCategory.STARTER, allergens: ['Gluten', 'Lácteos'] },
    { name: 'Entrecot a la brasa', description: '300g con guarnición', price: 22.50, category: MenuCategory.MAIN, allergens: [] },
    { name: 'Merluza al horno', description: 'Con patatas y verduras de temporada', price: 18.00, category: MenuCategory.MAIN, allergens: ['Pescado'] },
    { name: 'Pasta carbonara', description: 'Pasta fresca, panceta y huevo', price: 13.50, category: MenuCategory.MAIN, allergens: ['Gluten', 'Huevo', 'Lácteos'] },
    { name: 'Tiramisú', description: 'Receta clásica italiana', price: 6.50, category: MenuCategory.DESSERT, allergens: ['Huevo', 'Lácteos', 'Gluten'] },
    { name: 'Agua mineral 0,5L', description: null, price: 2.00, category: MenuCategory.BEVERAGE, allergens: [] },
    { name: 'Vino tinto Rioja (copa)', description: 'DOC Rioja', price: 4.00, category: MenuCategory.BEVERAGE, allergens: ['Sulfitos'] },
  ];

  for (const item of menuItems) {
    await prisma.menuItem.upsert({
      where:  { id: item.name.toLowerCase().replace(/ /g, '-') },
      update: {},
      create: { id: item.name.toLowerCase().replace(/ /g, '-'), ...item },
    });
  }

  console.log('✅ Seed completado.');
  console.log('   Admin: admin@restaurante.com / password123');
  console.log('   Manager: manager@restaurante.com / password123');
  console.log('   Camarero: camarero@restaurante.com / password123');
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
      if (!user || !(await bcrypt.compare(input.password, user.passwordHash)))
        throw new Error('Credenciales incorrectas');
      const token = await ctx.req.server.jwt.sign({ sub: user.id, role: user.role }, { expiresIn: '12h' });
      return { token, user: { id: user.id, name: user.name, email: user.email, role: user.role } };
    }),

  me: protectedProcedure.query(({ ctx }) =>
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true } })
  ),
});"""

_MENU_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, managerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const menuItemInput = z.object({
  name:        z.string().min(2),
  description: z.string().optional(),
  price:       z.number().positive(),
  category:    z.enum(['STARTER', 'MAIN', 'DESSERT', 'BEVERAGE', 'SPECIAL']),
  allergens:   z.string().array().default([]),
  imageUrl:    z.string().url().optional(),
});

export const menuRouter = router({
  list: publicProcedure
    .input(z.object({ category: z.enum(['STARTER', 'MAIN', 'DESSERT', 'BEVERAGE', 'SPECIAL']).optional(), availableOnly: z.boolean().default(true) }).optional())
    .query(({ input }) =>
      prisma.menuItem.findMany({
        where: { ...(input?.availableOnly !== false && { available: true }), ...(input?.category && { category: input.category }) },
        orderBy: [{ category: 'asc' }, { name: 'asc' }],
      })
    ),

  create: managerProcedure
    .input(menuItemInput)
    .mutation(({ input }) => prisma.menuItem.create({ data: input })),

  update: managerProcedure
    .input(menuItemInput.partial().extend({ id: z.string() }))
    .mutation(({ input: { id, ...data } }) => prisma.menuItem.update({ where: { id }, data })),

  toggleAvailability: managerProcedure
    .input(z.string())
    .mutation(async ({ input }) => {
      const item = await prisma.menuItem.findUniqueOrThrow({ where: { id: input } });
      return prisma.menuItem.update({ where: { id: input }, data: { available: !item.available } });
    }),

  delete: managerProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.menuItem.delete({ where: { id: input } })),
});"""

_TABLE_ROUTER = """import { z } from 'zod';
import { router, staffProcedure, managerProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const tableRouter = router({
  list: staffProcedure.query(() =>
    prisma.table.findMany({ orderBy: { number: 'asc' }, include: { _count: { select: { orders: { where: { status: { in: ['OPEN', 'IN_KITCHEN', 'READY'] } } } } } } })
  ),

  updateStatus: staffProcedure
    .input(z.object({ id: z.string(), status: z.enum(['FREE', 'OCCUPIED', 'RESERVED', 'CLEANING']) }))
    .mutation(({ input }) => prisma.table.update({ where: { id: input.id }, data: { status: input.status } })),

  create: managerProcedure
    .input(z.object({ number: z.number().int().positive(), capacity: z.number().int().positive(), zone: z.string().optional() }))
    .mutation(({ input }) => prisma.table.create({ data: input })),
});"""

_RESERVATION_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, staffProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const reservationInput = z.object({
  guestName:   z.string().min(2),
  guestPhone:  z.string().min(9),
  guestEmail:  z.string().email().optional(),
  partySize:   z.number().int().min(1).max(20),
  scheduledAt: z.string(),
  notes:       z.string().optional(),
  tableId:     z.string().optional(),
});

export const reservationRouter = router({
  list: staffProcedure
    .input(z.object({ date: z.string().optional() }).optional())
    .query(({ input }) => {
      const start = input?.date ? new Date(input.date) : new Date();
      start.setHours(0, 0, 0, 0);
      const end = new Date(start);
      end.setDate(end.getDate() + 1);
      return prisma.reservation.findMany({
        where: { scheduledAt: { gte: start, lt: end } },
        include: { table: true },
        orderBy: { scheduledAt: 'asc' },
      });
    }),

  create: publicProcedure
    .input(reservationInput)
    .mutation(({ input }) =>
      prisma.reservation.create({ data: { ...input, scheduledAt: new Date(input.scheduledAt) } })
    ),

  updateStatus: staffProcedure
    .input(z.object({ id: z.string(), status: z.enum(['PENDING', 'CONFIRMED', 'SEATED', 'COMPLETED', 'CANCELLED', 'NO_SHOW']) }))
    .mutation(({ input }) => prisma.reservation.update({ where: { id: input.id }, data: { status: input.status } })),

  assignTable: staffProcedure
    .input(z.object({ id: z.string(), tableId: z.string() }))
    .mutation(({ input }) => prisma.reservation.update({ where: { id: input.id }, data: { tableId: input.tableId } })),
});"""

_ORDER_ROUTER = """import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, staffProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const orderRouter = router({
  openOrder: staffProcedure
    .input(z.object({ tableId: z.string(), notes: z.string().optional() }))
    .mutation(async ({ input, ctx }) => {
      const existing = await prisma.order.findFirst({ where: { tableId: input.tableId, status: { in: ['OPEN', 'IN_KITCHEN', 'READY'] } } });
      if (existing) throw new TRPCError({ code: 'CONFLICT', message: 'La mesa ya tiene una comanda abierta' });
      const [order] = await prisma.$transaction([
        prisma.order.create({ data: { tableId: input.tableId, waiterId: ctx.userId, notes: input.notes } }),
        prisma.table.update({ where: { id: input.tableId }, data: { status: 'OCCUPIED' } }),
      ]);
      return order;
    }),

  addLine: staffProcedure
    .input(z.object({ orderId: z.string(), menuItemId: z.string(), quantity: z.number().int().min(1).default(1), notes: z.string().optional() }))
    .mutation(async ({ input }) => {
      const item = await prisma.menuItem.findUniqueOrThrow({ where: { id: input.menuItemId } });
      return prisma.orderLine.create({ data: { orderId: input.orderId, menuItemId: input.menuItemId, quantity: input.quantity, unitPrice: item.price, notes: input.notes } });
    }),

  removeLine: staffProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.orderLine.delete({ where: { id: input } })),

  updateStatus: staffProcedure
    .input(z.object({ id: z.string(), status: z.enum(['OPEN', 'IN_KITCHEN', 'READY', 'SERVED', 'PAID', 'CANCELLED']) }))
    .mutation(async ({ input }) => {
      const data: Record<string, unknown> = { status: input.status };
      if (['PAID', 'CANCELLED'].includes(input.status)) data['closedAt'] = new Date();
      const order = await prisma.order.update({ where: { id: input.id }, data });
      if (['PAID', 'CANCELLED'].includes(input.status))
        await prisma.table.update({ where: { id: order.tableId }, data: { status: 'FREE' } });
      return order;
    }),

  getByTable: staffProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.order.findFirst({
        where: { tableId: input, status: { in: ['OPEN', 'IN_KITCHEN', 'READY', 'SERVED'] } },
        include: { lines: { include: { menuItem: true } }, waiter: { select: { name: true } } },
      })
    ),

  closeAndCalculate: staffProcedure
    .input(z.string())
    .mutation(async ({ input }) => {
      const order = await prisma.order.findUniqueOrThrow({ where: { id: input }, include: { lines: true } });
      const total = order.lines.reduce((acc, l) => acc + Number(l.unitPrice) * l.quantity, 0);
      return prisma.order.update({ where: { id: input }, data: { total, status: 'SERVED' } });
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
export const metadata: Metadata = { title: '__NAME__', description: 'Gestión HORECA' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-amber-50 text-stone-900">
        <TRPCProvider>{children}</TRPCProvider>
      </body>
    </html>
  );
}"""

_LANDING = """'use client';
import { useAuthStore } from '@/lib/auth-store';
import { trpc } from '@/lib/trpc';
import Link from 'next/link';

const TABLE_STATUS_COLOR: Record<string, string> = {
  FREE: 'bg-green-100 text-green-700 border-green-200',
  OCCUPIED: 'bg-red-100 text-red-700 border-red-200',
  RESERVED: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  CLEANING: 'bg-blue-100 text-blue-700 border-blue-200',
};
const TABLE_STATUS_LABEL: Record<string, string> = { FREE: 'Libre', OCCUPIED: 'Ocupada', RESERVED: 'Reservada', CLEANING: 'Limpieza' };

export default function HomePage() {
  const user = useAuthStore(s => s.user);
  const { data: tables } = trpc.tables.list.useQuery(undefined, { enabled: !!user });

  if (!user) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
        <h1 className="text-4xl font-bold text-amber-800">__NAME__</h1>
        <p className="text-stone-500">Sistema de gestión de restaurante</p>
        <Link href="/login" className="mt-4 rounded-lg bg-amber-600 px-8 py-3 font-semibold text-white hover:bg-amber-700">
          Acceder
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-800">__NAME__</h1>
          <p className="text-sm text-stone-500">Bienvenido, {user.name}</p>
        </div>
        <nav className="flex gap-2">
          <Link href="/carta" className="rounded-lg border border-amber-200 bg-white px-4 py-2 text-sm hover:bg-amber-50">Carta</Link>
          <Link href="/reservas" className="rounded-lg border border-amber-200 bg-white px-4 py-2 text-sm hover:bg-amber-50">Reservas</Link>
          <Link href="/comandas" className="rounded-lg border border-amber-200 bg-white px-4 py-2 text-sm hover:bg-amber-50">Comandas</Link>
        </nav>
      </div>

      <h2 className="mb-4 font-semibold text-stone-700">Estado de mesas</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {tables?.map(t => (
          <div key={t.id} className={`rounded-xl border p-4 text-center shadow-sm ${TABLE_STATUS_COLOR[t.status] ?? 'bg-white'}`}>
            <p className="text-2xl font-bold">Mesa {t.number}</p>
            <p className="text-xs">{t.zone ?? ''}</p>
            <p className="mt-1 text-xs font-medium">{TABLE_STATUS_LABEL[t.status]}</p>
            <p className="text-xs text-stone-400">{t.capacity} pax</p>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_MENU_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const CATEGORY_LABELS: Record<string, string> = {
  STARTER: 'Entrantes', MAIN: 'Principales', DESSERT: 'Postres', BEVERAGE: 'Bebidas', SPECIAL: 'Especiales del día'
};
const CATEGORIES = ['STARTER', 'MAIN', 'DESSERT', 'BEVERAGE', 'SPECIAL'] as const;

export default function CartaPage() {
  const [active, setActive] = useState<typeof CATEGORIES[number]>('MAIN');
  const { data } = trpc.menu.list.useQuery({ category: active, availableOnly: false });
  const user = useAuthStore(s => s.user);
  const isManager = user?.role === 'ADMIN' || user?.role === 'MANAGER';
  const utils = trpc.useUtils();
  const toggle = trpc.menu.toggleAvailability.useMutation({ onSuccess: () => utils.menu.list.invalidate() });

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h1 className="mb-4 text-2xl font-bold text-amber-800">Carta</h1>
      <div className="mb-6 flex flex-wrap gap-2">
        {CATEGORIES.map(c => (
          <button key={c} onClick={() => setActive(c)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${active === c ? 'bg-amber-600 text-white' : 'border border-amber-200 bg-white hover:bg-amber-50'}`}>
            {CATEGORY_LABELS[c]}
          </button>
        ))}
      </div>
      <div className="grid gap-3">
        {data?.map(item => (
          <div key={item.id} className={`flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm ${!item.available ? 'opacity-50' : ''}`}>
            <div>
              <p className="font-semibold">{item.name}</p>
              {item.description && <p className="text-sm text-stone-500">{item.description}</p>}
              {item.allergens.length > 0 && (
                <p className="mt-1 text-xs text-amber-700">Alérgenos: {item.allergens.join(', ')}</p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold text-amber-700">{Number(item.price).toFixed(2)} €</span>
              {isManager && (
                <button onClick={() => toggle.mutate(item.id)}
                  className={`rounded-lg px-3 py-1 text-xs font-medium ${item.available ? 'bg-red-100 text-red-700 hover:bg-red-200' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}>
                  {item.available ? 'Deshabilitar' : 'Habilitar'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_RESERVATIONS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pendiente', CONFIRMED: 'Confirmada', SEATED: 'En mesa', COMPLETED: 'Completada', CANCELLED: 'Cancelada', NO_SHOW: 'No presentado'
};
const STATUS_COLOR: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700', CONFIRMED: 'bg-green-100 text-green-700',
  SEATED: 'bg-blue-100 text-blue-700', COMPLETED: 'bg-stone-100 text-stone-600',
  CANCELLED: 'bg-red-100 text-red-700', NO_SHOW: 'bg-stone-100 text-stone-500',
};

export default function ReservasPage() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const { data, refetch } = trpc.reservations.list.useQuery({ date });
  const updateStatus = trpc.reservations.updateStatus.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-amber-800">Reservas</h1>
        <input type="date" value={date} onChange={e => setDate(e.target.value)}
          className="rounded-lg border border-amber-200 px-3 py-2 text-sm" />
      </div>
      <div className="space-y-3">
        {data?.length === 0 && <p className="text-stone-400">No hay reservas para este día.</p>}
        {data?.map(r => (
          <div key={r.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm">
            <div>
              <p className="font-semibold">{r.guestName}</p>
              <p className="text-sm text-stone-500">
                {new Date(r.scheduledAt).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                {' · '}{r.partySize} personas{r.table ? ` · Mesa ${r.table.number}` : ''}
              </p>
              {r.notes && <p className="text-xs italic text-stone-400">{r.notes}</p>}
            </div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLOR[r.status]}`}>{STATUS_LABELS[r.status]}</span>
              {r.status === 'PENDING' && (
                <button onClick={() => updateStatus.mutate({ id: r.id, status: 'CONFIRMED' })}
                  className="rounded-lg bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700">
                  Confirmar
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_ORDERS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const STATUS_LABELS: Record<string, string> = {
  OPEN: 'Abierta', IN_KITCHEN: 'En cocina', READY: 'Lista', SERVED: 'Servida', PAID: 'Pagada', CANCELLED: 'Cancelada'
};
const STATUS_COLOR: Record<string, string> = {
  OPEN: 'bg-yellow-100 text-yellow-700', IN_KITCHEN: 'bg-orange-100 text-orange-700',
  READY: 'bg-green-100 text-green-700', SERVED: 'bg-blue-100 text-blue-700',
  PAID: 'bg-stone-100 text-stone-500', CANCELLED: 'bg-red-100 text-red-700',
};

export default function ComandasPage() {
  const user = useAuthStore(s => s.user);
  const { data: tables } = trpc.tables.list.useQuery(undefined, { enabled: !!user });

  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-amber-800">Comandas activas</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tables?.filter(t => t.status === 'OCCUPIED').map(table => (
          <TableOrderCard key={table.id} tableId={table.id} tableNumber={table.number} />
        ))}
        {tables?.filter(t => t.status === 'OCCUPIED').length === 0 && (
          <p className="col-span-full text-stone-400">No hay mesas ocupadas en este momento.</p>
        )}
      </div>
    </main>
  );
}

function TableOrderCard({ tableId, tableNumber }: { tableId: string; tableNumber: number }) {
  const { data: order, refetch } = trpc.orders.getByTable.useQuery(tableId);
  const updateStatus = trpc.orders.updateStatus.useMutation({ onSuccess: () => refetch() });
  const closeAndCalc = trpc.orders.closeAndCalculate.useMutation({ onSuccess: () => refetch() });

  if (!order) return null;

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-bold">Mesa {tableNumber}</h2>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLOR[order.status]}`}>
          {STATUS_LABELS[order.status]}
        </span>
      </div>
      <ul className="mb-3 space-y-1 text-sm">
        {order.lines.map(l => (
          <li key={l.id} className="flex justify-between">
            <span>{l.quantity}× {l.menuItem.name}</span>
            <span className="text-stone-500">{(Number(l.unitPrice) * l.quantity).toFixed(2)} €</span>
          </li>
        ))}
      </ul>
      {order.total && (
        <p className="mb-3 border-t pt-2 text-right font-bold text-amber-700">Total: {Number(order.total).toFixed(2)} €</p>
      )}
      <div className="flex flex-wrap gap-1.5">
        {order.status === 'OPEN' && (
          <button onClick={() => updateStatus.mutate({ id: order.id, status: 'IN_KITCHEN' })}
            className="rounded-lg bg-orange-500 px-3 py-1 text-xs text-white hover:bg-orange-600">
            Enviar a cocina
          </button>
        )}
        {order.status === 'IN_KITCHEN' && (
          <button onClick={() => updateStatus.mutate({ id: order.id, status: 'READY' })}
            className="rounded-lg bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700">
            Lista para servir
          </button>
        )}
        {order.status === 'READY' && (
          <button onClick={() => closeAndCalc.mutate(order.id)}
            className="rounded-lg bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700">
            Calcular cuenta
          </button>
        )}
        {order.status === 'SERVED' && (
          <button onClick={() => updateStatus.mutate({ id: order.id, status: 'PAID' })}
            className="rounded-lg bg-amber-600 px-3 py-1 text-xs text-white hover:bg-amber-700">
            Cobrar
          </button>
        )}
      </div>
    </div>
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
      POSTGRES_USER: horeca
      POSTGRES_PASSWORD: horeca_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://horeca:horeca_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://horeca:horeca_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Sistema de Gestión HORECA

Plataforma para gestión de restaurante: carta, mesas, reservas y comandas.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, MANAGER, WAITER, KITCHEN)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Carta | Gestión de menú por categorías con disponibilidad |
| Mesas | Estado en tiempo real (Libre/Ocupada/Reservada) |
| Reservas | Agenda diaria con confirmación y asignación de mesa |
| Comandas | Flujo completo: abrir → cocina → listo → cobrar |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin: admin@restaurante.com / password123
"""
