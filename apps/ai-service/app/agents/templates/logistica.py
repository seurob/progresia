"""
LOGISTICA template — sistema de gestión de envíos y logística.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: envíos, paquetes, rutas, vehículos, conductores, tracking público.
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
        _f("apps/api/src/modules/shipments/shipment.router.ts", "typescript", _SHIPMENT_ROUTER),
        _f("apps/api/src/modules/vehicles/vehicle.router.ts", "typescript", _VEHICLE_ROUTER),
        _f("apps/api/src/modules/drivers/driver.router.ts",   "typescript", _DRIVER_ROUTER),
        _f("apps/api/src/modules/routes/route.router.ts",     "typescript", _ROUTE_ROUTER),
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
        _f("apps/web/src/app/tracking/page.tsx",              "typescript", _TRACKING_PAGE),
        _f("apps/web/src/app/envios/page.tsx",                "typescript", _SHIPMENTS_PAGE),
        _f("apps/web/src/app/flota/page.tsx",                 "typescript", _FLEET_PAGE),
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
console.log(`🚚 __NAME__ API running on port ${port}`);"""

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
export const dispatcherProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'DISPATCHER'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const driverProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'DISPATCHER', 'DRIVER'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN')
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }     from './modules/auth/auth.router';
import { shipmentRouter } from './modules/shipments/shipment.router';
import { vehicleRouter }  from './modules/vehicles/vehicle.router';
import { driverRouter }   from './modules/drivers/driver.router';
import { routeRouter }    from './modules/routes/route.router';

export const appRouter = router({
  auth:      authRouter,
  shipments: shipmentRouter,
  vehicles:  vehicleRouter,
  drivers:   driverRouter,
  routes:    routeRouter,
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
  DISPATCHER
  DRIVER
}

enum ShipmentStatus {
  PENDING
  PICKED_UP
  IN_TRANSIT
  OUT_FOR_DELIVERY
  DELIVERED
  FAILED
  RETURNED
  CANCELLED
}

enum VehicleType {
  VAN
  TRUCK
  MOTORCYCLE
  BICYCLE
}

enum VehicleStatus {
  AVAILABLE
  ON_ROUTE
  MAINTENANCE
  RETIRED
}

enum RouteStatus {
  PLANNED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         StaffRole @default(DRIVER)
  phone        String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  driver       Driver?
}

model Driver {
  id            String    @id @default(cuid())
  userId        String    @unique
  user          User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  licenseNumber String    @unique
  licenseExpiry DateTime
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  routes        Route[]
}

model Vehicle {
  id           String        @id @default(cuid())
  plate        String        @unique
  type         VehicleType
  brand        String
  model        String
  year         Int
  capacity     Decimal?      @db.Decimal(6, 2)
  status       VehicleStatus @default(AVAILABLE)
  lastService  DateTime?
  notes        String?
  createdAt    DateTime      @default(now())
  updatedAt    DateTime      @updatedAt
  routes       Route[]
}

model Shipment {
  id              String         @id @default(cuid())
  trackingCode    String         @unique @default(cuid())
  status          ShipmentStatus @default(PENDING)
  senderName      String
  senderAddress   String
  senderCity      String
  receiverName    String
  receiverPhone   String
  receiverAddress String
  receiverCity    String
  receiverEmail   String?
  weight          Decimal        @db.Decimal(6, 3)
  dimensions      String?
  description     String?
  declaredValue   Decimal?       @db.Decimal(10, 2)
  notes           String?
  scheduledAt     DateTime?
  deliveredAt     DateTime?
  createdAt       DateTime       @default(now())
  updatedAt       DateTime       @updatedAt
  routeItems      RouteItem[]
  events          TrackingEvent[]
}

model Route {
  id          String      @id @default(cuid())
  driverId    String
  driver      Driver      @relation(fields: [driverId], references: [id])
  vehicleId   String
  vehicle     Vehicle     @relation(fields: [vehicleId], references: [id])
  status      RouteStatus @default(PLANNED)
  scheduledAt DateTime
  startedAt   DateTime?
  completedAt DateTime?
  notes       String?
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
  items       RouteItem[]
}

model RouteItem {
  id         String   @id @default(cuid())
  routeId    String
  route      Route    @relation(fields: [routeId], references: [id], onDelete: Cascade)
  shipmentId String
  shipment   Shipment @relation(fields: [shipmentId], references: [id])
  order      Int
  deliveredAt DateTime?
}

model TrackingEvent {
  id         String   @id @default(cuid())
  shipmentId String
  shipment   Shipment @relation(fields: [shipmentId], references: [id], onDelete: Cascade)
  status     ShipmentStatus
  location   String?
  notes      String?
  createdAt  DateTime @default(now())
}"""

_SEED = """import { PrismaClient, StaffRole, VehicleType, VehicleStatus } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Logística...');

  const hash = await bcrypt.hash('password123', 10);

  await prisma.user.upsert({
    where: { email: 'admin@logistica.com' },
    update: {},
    create: { email: 'admin@logistica.com', name: 'Admin', passwordHash: hash, role: StaffRole.ADMIN, phone: '900 100 200' },
  });

  const dispatcher = await prisma.user.upsert({
    where: { email: 'central@logistica.com' },
    update: {},
    create: { email: 'central@logistica.com', name: 'Central (Dispatcher)', passwordHash: hash, role: StaffRole.DISPATCHER, phone: '900 100 201' },
  });

  const driverUser = await prisma.user.upsert({
    where: { email: 'conductor@logistica.com' },
    update: {},
    create: { email: 'conductor@logistica.com', name: 'Juan Conductor', passwordHash: hash, role: StaffRole.DRIVER, phone: '611 001 002' },
  });

  const driver = await prisma.driver.upsert({
    where: { userId: driverUser.id },
    update: {},
    create: { userId: driverUser.id, licenseNumber: 'B-1234567', licenseExpiry: new Date('2027-06-30') },
  });

  const van = await prisma.vehicle.upsert({
    where: { plate: '1234 ABC' },
    update: {},
    create: { plate: '1234 ABC', type: VehicleType.VAN, brand: 'Furgoneta', model: 'Transit Custom', year: 2022, capacity: 1000, status: VehicleStatus.AVAILABLE },
  });

  // Sample shipments
  const s1 = await prisma.shipment.create({
    data: {
      senderName: 'Tienda Online SL', senderAddress: 'Polígono Industrial 5', senderCity: 'Madrid',
      receiverName: 'María López', receiverPhone: '612 111 222', receiverAddress: 'Calle Mayor 10, 2ºA', receiverCity: 'Alcalá de Henares',
      weight: 2.5, description: 'Electrónica - Auriculares',
      events: { create: [{ status: 'PENDING', location: 'Almacén origen', notes: 'Recibido en almacén' }] },
    },
  });
  const s2 = await prisma.shipment.create({
    data: {
      senderName: 'Tienda Online SL', senderAddress: 'Polígono Industrial 5', senderCity: 'Madrid',
      receiverName: 'Carlos García', receiverPhone: '622 333 444', receiverAddress: 'Avenida España 45, 1ºB', receiverCity: 'Torrejón de Ardoz',
      weight: 0.8, description: 'Ropa - Camiseta',
      events: { create: [{ status: 'PENDING', location: 'Almacén origen' }] },
    },
  });

  // Sample route
  await prisma.route.create({
    data: {
      driverId: driver.id, vehicleId: van.id, scheduledAt: new Date(),
      items: { create: [{ shipmentId: s1.id, order: 1 }, { shipmentId: s2.id, order: 2 }] },
    },
  });

  console.log('✅ Seed completado.');
  console.log('   Admin: admin@logistica.com / password123');
  console.log('   Dispatcher: central@logistica.com / password123');
  console.log('   Conductor: conductor@logistica.com / password123');
  console.log(`   Tracking S1: ${s1.trackingCode}`);
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
      const token = await ctx.req.server.jwt.sign({ sub: user.id, role: user.role }, { expiresIn: '8h' });
      return { token, user: { id: user.id, name: user.name, email: user.email, role: user.role } };
    }),

  me: protectedProcedure.query(({ ctx }) =>
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true, phone: true } })
  ),
});"""

_SHIPMENT_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, dispatcherProcedure, driverProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const shipmentInput = z.object({
  senderName:      z.string().min(2),
  senderAddress:   z.string().min(5),
  senderCity:      z.string().min(2),
  receiverName:    z.string().min(2),
  receiverPhone:   z.string().min(9),
  receiverAddress: z.string().min(5),
  receiverCity:    z.string().min(2),
  receiverEmail:   z.string().email().optional(),
  weight:          z.number().positive(),
  dimensions:      z.string().optional(),
  description:     z.string().optional(),
  declaredValue:   z.number().nonnegative().optional(),
  notes:           z.string().optional(),
  scheduledAt:     z.string().optional(),
});

export const shipmentRouter = router({
  track: publicProcedure
    .input(z.string())
    .query(async ({ input }) => {
      const shipment = await prisma.shipment.findUnique({
        where: { trackingCode: input },
        include: { events: { orderBy: { createdAt: 'desc' } } },
      });
      if (!shipment) throw new Error('Código de seguimiento no encontrado');
      return shipment;
    }),

  list: dispatcherProcedure
    .input(z.object({ status: z.enum(['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'RETURNED', 'CANCELLED']).optional() }).optional())
    .query(({ input }) =>
      prisma.shipment.findMany({
        where: input?.status ? { status: input.status } : {},
        include: { events: { orderBy: { createdAt: 'desc' }, take: 1 }, _count: { select: { routeItems: true } } },
        orderBy: { createdAt: 'desc' },
        take: 100,
      })
    ),

  create: dispatcherProcedure
    .input(shipmentInput)
    .mutation(async ({ input }) => {
      const { scheduledAt, ...rest } = input;
      const shipment = await prisma.shipment.create({
        data: { ...rest, ...(scheduledAt && { scheduledAt: new Date(scheduledAt) }), events: { create: [{ status: 'PENDING', location: 'Almacén origen', notes: 'Registrado en sistema' }] } },
      });
      return shipment;
    }),

  updateStatus: driverProcedure
    .input(z.object({ id: z.string(), status: z.enum(['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'RETURNED', 'CANCELLED']), location: z.string().optional(), notes: z.string().optional() }))
    .mutation(async ({ input: { id, status, location, notes } }) => {
      const [shipment] = await prisma.$transaction([
        prisma.shipment.update({
          where: { id },
          data: { status, ...(status === 'DELIVERED' && { deliveredAt: new Date() }) },
        }),
        prisma.trackingEvent.create({ data: { shipmentId: id, status, location, notes } }),
      ]);
      return shipment;
    }),
});"""

_VEHICLE_ROUTER = """import { z } from 'zod';
import { router, dispatcherProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const vehicleRouter = router({
  list: dispatcherProcedure.query(() =>
    prisma.vehicle.findMany({ include: { _count: { select: { routes: true } } }, orderBy: { plate: 'asc' } })
  ),

  create: adminProcedure
    .input(z.object({
      plate:    z.string().min(6),
      type:     z.enum(['VAN', 'TRUCK', 'MOTORCYCLE', 'BICYCLE']),
      brand:    z.string().min(2),
      model:    z.string().min(1),
      year:     z.number().int().min(1990).max(2030),
      capacity: z.number().positive().optional(),
    }))
    .mutation(({ input }) => prisma.vehicle.create({ data: input })),

  updateStatus: dispatcherProcedure
    .input(z.object({ id: z.string(), status: z.enum(['AVAILABLE', 'ON_ROUTE', 'MAINTENANCE', 'RETIRED']) }))
    .mutation(({ input }) => prisma.vehicle.update({ where: { id: input.id }, data: { status: input.status } })),
});"""

_DRIVER_ROUTER = """import { z } from 'zod';
import { router, dispatcherProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const driverRouter = router({
  list: dispatcherProcedure.query(() =>
    prisma.driver.findMany({
      include: { user: { select: { name: true, email: true, phone: true } }, _count: { select: { routes: true } } },
      orderBy: { createdAt: 'desc' },
    })
  ),

  myRoute: dispatcherProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.route.findFirst({
        where: { driver: { userId: input }, status: { in: ['PLANNED', 'IN_PROGRESS'] } },
        include: { items: { include: { shipment: true }, orderBy: { order: 'asc' } }, vehicle: true },
      })
    ),
});"""

_ROUTE_ROUTER = """import { z } from 'zod';
import { router, dispatcherProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const routeRouter = router({
  list: dispatcherProcedure
    .input(z.object({ date: z.string().optional() }).optional())
    .query(({ input }) => {
      const start = input?.date ? new Date(input.date) : new Date();
      start.setHours(0, 0, 0, 0);
      const end = new Date(start);
      end.setDate(end.getDate() + 1);
      return prisma.route.findMany({
        where: { scheduledAt: { gte: start, lt: end } },
        include: {
          driver: { include: { user: { select: { name: true } } } },
          vehicle: true,
          items: { include: { shipment: true }, orderBy: { order: 'asc' } },
        },
        orderBy: { scheduledAt: 'asc' },
      });
    }),

  create: dispatcherProcedure
    .input(z.object({
      driverId:    z.string(),
      vehicleId:   z.string(),
      scheduledAt: z.string(),
      shipmentIds: z.string().array().min(1),
      notes:       z.string().optional(),
    }))
    .mutation(async ({ input }) => {
      const { shipmentIds, scheduledAt, ...rest } = input;
      return prisma.route.create({
        data: {
          ...rest,
          scheduledAt: new Date(scheduledAt),
          items: { create: shipmentIds.map((id, i) => ({ shipmentId: id, order: i + 1 })) },
        },
        include: { items: { include: { shipment: true } } },
      });
    }),

  updateStatus: dispatcherProcedure
    .input(z.object({ id: z.string(), status: z.enum(['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']) }))
    .mutation(async ({ input }) => {
      const data: Record<string, unknown> = { status: input.status };
      if (input.status === 'IN_PROGRESS') data['startedAt'] = new Date();
      if (input.status === 'COMPLETED')   data['completedAt'] = new Date();
      return prisma.route.update({ where: { id: input.id }, data });
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
export const metadata: Metadata = { title: '__NAME__', description: 'Sistema de logística y envíos' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-100 text-slate-900">
        <TRPCProvider>{children}</TRPCProvider>
      </body>
    </html>
  );
}"""

_LANDING = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import Link from 'next/link';
import { useAuthStore } from '@/lib/auth-store';

const STATUS_ICONS: Record<string, string> = {
  PENDING: '📦', PICKED_UP: '🏭', IN_TRANSIT: '🚚', OUT_FOR_DELIVERY: '🛵',
  DELIVERED: '✅', FAILED: '❌', RETURNED: '↩️', CANCELLED: '🚫',
};
const STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pendiente', PICKED_UP: 'Recogido', IN_TRANSIT: 'En tránsito',
  OUT_FOR_DELIVERY: 'En reparto', DELIVERED: 'Entregado', FAILED: 'Fallido',
  RETURNED: 'Devuelto', CANCELLED: 'Cancelado',
};

export default function HomePage() {
  const user = useAuthStore(s => s.user);
  const [code, setCode] = useState('');
  const [query, setQuery] = useState('');
  const { data: tracking, error, isLoading } = trpc.shipments.track.useQuery(query, { enabled: query.length > 10 });

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-slate-800">🚚 __NAME__</h1>
        <p className="mt-2 text-slate-500">Sistema de gestión logística y seguimiento de envíos</p>
      </div>

      {/* Public tracking */}
      <div className="mb-8 rounded-2xl bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-semibold text-slate-700">Seguimiento de envío</h2>
        <div className="flex gap-3">
          <input value={code} onChange={e => setCode(e.target.value)}
            placeholder="Introduce tu código de seguimiento..."
            className="flex-1 rounded-xl border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400" />
          <button onClick={() => setQuery(code)} disabled={code.length < 5}
            className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            Rastrear
          </button>
        </div>
        {isLoading && <p className="mt-3 text-sm text-slate-400">Buscando...</p>}
        {error && <p className="mt-3 text-sm text-red-500">Código no encontrado.</p>}
        {tracking && (
          <div className="mt-4 rounded-xl bg-slate-50 p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{STATUS_ICONS[tracking.status]}</span>
              <div>
                <p className="font-semibold">{STATUS_LABELS[tracking.status]}</p>
                <p className="text-xs text-slate-400">Para: {tracking.receiverName} · {tracking.receiverCity}</p>
              </div>
            </div>
            <ol className="space-y-2 border-l-2 border-blue-200 pl-4">
              {tracking.events.map(e => (
                <li key={e.id} className="relative">
                  <span className="absolute -left-[21px] top-1 h-3 w-3 rounded-full border-2 border-blue-400 bg-white" />
                  <p className="text-sm font-medium">{STATUS_LABELS[e.status]}</p>
                  {e.location && <p className="text-xs text-slate-500">{e.location}</p>}
                  <p className="text-xs text-slate-400">{new Date(e.createdAt).toLocaleString('es-ES')}</p>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Staff links */}
      {user ? (
        <nav className="flex gap-3 justify-center">
          <Link href="/envios" className="rounded-xl bg-slate-800 px-6 py-3 text-white font-medium hover:bg-slate-700">Gestión de envíos</Link>
          <Link href="/flota" className="rounded-xl border border-slate-300 bg-white px-6 py-3 font-medium hover:bg-slate-50">Flota y rutas</Link>
        </nav>
      ) : (
        <div className="text-center">
          <Link href="/login" className="rounded-xl bg-slate-800 px-8 py-3 text-white font-medium hover:bg-slate-700">Acceso staff</Link>
        </div>
      )}
    </main>
  );
}"""

_TRACKING_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pendiente', PICKED_UP: 'Recogido', IN_TRANSIT: 'En tránsito',
  OUT_FOR_DELIVERY: 'En reparto', DELIVERED: 'Entregado', FAILED: 'Fallido',
  RETURNED: 'Devuelto', CANCELLED: 'Cancelado',
};
const STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700', PICKED_UP: 'bg-blue-100 text-blue-700',
  IN_TRANSIT: 'bg-indigo-100 text-indigo-700', OUT_FOR_DELIVERY: 'bg-purple-100 text-purple-700',
  DELIVERED: 'bg-green-100 text-green-700', FAILED: 'bg-red-100 text-red-700',
  RETURNED: 'bg-orange-100 text-orange-700', CANCELLED: 'bg-stone-100 text-stone-600',
};

export default function TrackingPage() {
  const [code, setCode] = useState('');
  const [query, setQuery] = useState('');
  const { data, error, isLoading } = trpc.shipments.track.useQuery(query, { enabled: query.length > 5 });

  return (
    <main className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold">Seguimiento de envío</h1>
      <div className="mb-6 flex gap-3">
        <input value={code} onChange={e => setCode(e.target.value)}
          placeholder="Código de seguimiento..."
          className="flex-1 rounded-xl border px-4 py-2.5 text-sm" />
        <button onClick={() => setQuery(code)}
          className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm text-white hover:bg-blue-700">
          Rastrear
        </button>
      </div>
      {isLoading && <p className="text-slate-400">Buscando...</p>}
      {error && <p className="text-red-500">Código no encontrado.</p>}
      {data && (
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-bold">Envío #{data.trackingCode.slice(-8).toUpperCase()}</h2>
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${STATUS_COLORS[data.status]}`}>{STATUS_LABELS[data.status]}</span>
          </div>
          <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
            <div><p className="text-slate-400">Remitente</p><p className="font-medium">{data.senderName}</p><p className="text-slate-500">{data.senderCity}</p></div>
            <div><p className="text-slate-400">Destinatario</p><p className="font-medium">{data.receiverName}</p><p className="text-slate-500">{data.receiverCity}</p></div>
          </div>
          <h3 className="mb-3 font-semibold text-slate-700">Historial</h3>
          <ol className="space-y-3 border-l-2 border-blue-200 pl-4">
            {data.events.map(e => (
              <li key={e.id} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-3 w-3 rounded-full border-2 border-blue-400 bg-white" />
                <p className="font-medium text-sm">{STATUS_LABELS[e.status]}</p>
                {e.location && <p className="text-xs text-slate-500">{e.location}</p>}
                {e.notes && <p className="text-xs italic text-slate-400">{e.notes}</p>}
                <p className="text-xs text-slate-400">{new Date(e.createdAt).toLocaleString('es-ES')}</p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </main>
  );
}"""

_SHIPMENTS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700', PICKED_UP: 'bg-blue-100 text-blue-700',
  IN_TRANSIT: 'bg-indigo-100 text-indigo-700', OUT_FOR_DELIVERY: 'bg-purple-100 text-purple-700',
  DELIVERED: 'bg-green-100 text-green-700', FAILED: 'bg-red-100 text-red-700',
  RETURNED: 'bg-orange-100 text-orange-700', CANCELLED: 'bg-stone-100 text-stone-600',
};
const STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pendiente', PICKED_UP: 'Recogido', IN_TRANSIT: 'En tránsito',
  OUT_FOR_DELIVERY: 'En reparto', DELIVERED: 'Entregado', FAILED: 'Fallido',
  RETURNED: 'Devuelto', CANCELLED: 'Cancelado',
};
type ShipmentStatus = keyof typeof STATUS_LABELS;

export default function EnviosPage() {
  const [filterStatus, setFilterStatus] = useState<ShipmentStatus | undefined>();
  const { data, isLoading, refetch } = trpc.shipments.list.useQuery(filterStatus ? { status: filterStatus } : undefined);
  const updateStatus = trpc.shipments.updateStatus.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Gestión de envíos</h1>
        <select value={filterStatus ?? ''} onChange={e => setFilterStatus((e.target.value as ShipmentStatus) || undefined)}
          className="ml-auto rounded-lg border px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      {isLoading && <p className="text-slate-400">Cargando...</p>}
      <div className="space-y-3">
        {data?.map(s => (
          <div key={s.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm">
            <div>
              <p className="font-mono text-xs text-slate-400">{s.trackingCode.slice(-8).toUpperCase()}</p>
              <p className="font-semibold">{s.receiverName}</p>
              <p className="text-sm text-slate-500">{s.receiverAddress}, {s.receiverCity}</p>
              <p className="text-xs text-slate-400">{Number(s.weight)} kg · {new Date(s.createdAt).toLocaleDateString('es-ES')}</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[s.status]}`}>{STATUS_LABELS[s.status]}</span>
              {s.status === 'PENDING' && (
                <button onClick={() => updateStatus.mutate({ id: s.id, status: 'PICKED_UP', location: 'Almacén' })}
                  className="rounded-lg bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700">
                  Recoger
                </button>
              )}
              {s.status === 'PICKED_UP' && (
                <button onClick={() => updateStatus.mutate({ id: s.id, status: 'IN_TRANSIT' })}
                  className="rounded-lg bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">
                  En tránsito
                </button>
              )}
              {s.status === 'IN_TRANSIT' && (
                <button onClick={() => updateStatus.mutate({ id: s.id, status: 'OUT_FOR_DELIVERY' })}
                  className="rounded-lg bg-purple-600 px-3 py-1 text-xs text-white hover:bg-purple-700">
                  En reparto
                </button>
              )}
              {s.status === 'OUT_FOR_DELIVERY' && (
                <button onClick={() => updateStatus.mutate({ id: s.id, status: 'DELIVERED', notes: 'Entregado al destinatario' })}
                  className="rounded-lg bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700">
                  Entregado
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_FLEET_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

const VEHICLE_ICONS: Record<string, string> = { VAN: '🚐', TRUCK: '🚛', MOTORCYCLE: '🏍️', BICYCLE: '🚲' };
const VEHICLE_STATUS_COLORS: Record<string, string> = {
  AVAILABLE: 'bg-green-100 text-green-700', ON_ROUTE: 'bg-blue-100 text-blue-700',
  MAINTENANCE: 'bg-yellow-100 text-yellow-700', RETIRED: 'bg-stone-100 text-stone-500',
};
const VEHICLE_STATUS_LABELS: Record<string, string> = { AVAILABLE: 'Disponible', ON_ROUTE: 'En ruta', MAINTENANCE: 'Mantenimiento', RETIRED: 'Retirado' };
const ROUTE_STATUS_COLORS: Record<string, string> = {
  PLANNED: 'bg-yellow-100 text-yellow-700', IN_PROGRESS: 'bg-blue-100 text-blue-700',
  COMPLETED: 'bg-green-100 text-green-700', CANCELLED: 'bg-red-100 text-red-700',
};
const ROUTE_STATUS_LABELS: Record<string, string> = { PLANNED: 'Planificada', IN_PROGRESS: 'En curso', COMPLETED: 'Completada', CANCELLED: 'Cancelada' };

export default function FlotaPage() {
  const today = new Date().toISOString().slice(0, 10);
  const { data: vehicles } = trpc.vehicles.list.useQuery();
  const { data: routes, refetch } = trpc.routes.list.useQuery({ date: today });
  const updateRoute = trpc.routes.updateStatus.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold">Flota y rutas</h1>

      {/* Vehicles */}
      <h2 className="mb-3 font-semibold text-slate-700">Vehículos</h2>
      <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {vehicles?.map(v => (
          <div key={v.id} className="rounded-xl border bg-white p-4 shadow-sm text-center">
            <p className="text-3xl">{VEHICLE_ICONS[v.type]}</p>
            <p className="font-semibold text-sm mt-1">{v.plate}</p>
            <p className="text-xs text-slate-400">{v.brand} {v.model}</p>
            <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${VEHICLE_STATUS_COLORS[v.status]}`}>{VEHICLE_STATUS_LABELS[v.status]}</span>
            <p className="text-xs text-slate-400 mt-1">{v._count.routes} rutas</p>
          </div>
        ))}
      </div>

      {/* Today routes */}
      <h2 className="mb-3 font-semibold text-slate-700">Rutas de hoy</h2>
      <div className="space-y-4">
        {routes?.map(r => (
          <div key={r.id} className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <p className="font-semibold">{r.driver.user.name}</p>
                <p className="text-xs text-slate-400">{r.vehicle.plate} · {r.items.length} paradas</p>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-sm font-medium ${ROUTE_STATUS_COLORS[r.status]}`}>{ROUTE_STATUS_LABELS[r.status]}</span>
            </div>
            <ol className="mb-3 space-y-1.5">
              {r.items.map((item, i) => (
                <li key={item.id} className="flex items-center gap-3 text-sm">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-medium shrink-0">{i + 1}</span>
                  <span className="flex-1">{item.shipment.receiverName} — {item.shipment.receiverAddress}, {item.shipment.receiverCity}</span>
                  {item.deliveredAt && <span className="text-xs text-green-600">✓ Entregado</span>}
                </li>
              ))}
            </ol>
            <div className="flex gap-2">
              {r.status === 'PLANNED' && (
                <button onClick={() => updateRoute.mutate({ id: r.id, status: 'IN_PROGRESS' })}
                  className="rounded-lg bg-blue-600 px-4 py-1.5 text-xs text-white hover:bg-blue-700">
                  Iniciar ruta
                </button>
              )}
              {r.status === 'IN_PROGRESS' && (
                <button onClick={() => updateRoute.mutate({ id: r.id, status: 'COMPLETED' })}
                  className="rounded-lg bg-green-600 px-4 py-1.5 text-xs text-white hover:bg-green-700">
                  Completar ruta
                </button>
              )}
            </div>
          </div>
        ))}
        {routes?.length === 0 && <p className="text-slate-400">No hay rutas programadas para hoy.</p>}
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
      POSTGRES_USER: logis
      POSTGRES_PASSWORD: logis_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://logis:logis_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://logis:logis_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Sistema de Logística

Plataforma para gestión de envíos, flota de vehículos y rutas de reparto.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, DISPATCHER, DRIVER)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Tracking público | Seguimiento de envío por código sin necesidad de login |
| Envíos | CRUD completo con flujo de estados + historial de eventos |
| Flota | Gestión de vehículos y conductores |
| Rutas | Planificación de rutas diarias, asignación conductor+vehículo, control de paradas |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin: admin@logistica.com / password123
Dispatcher: central@logistica.com / password123
Conductor: conductor@logistica.com / password123
"""
