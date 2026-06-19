"""
INMOBILIARIA template — sistema de gestión inmobiliaria.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: propiedades, clientes/leads, visitas, contratos.
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
        _f("apps/api/src/modules/properties/property.router.ts",    "typescript", _PROPERTY_ROUTER),
        _f("apps/api/src/modules/clients/client.router.ts",         "typescript", _CLIENT_ROUTER),
        _f("apps/api/src/modules/visits/visit.router.ts",           "typescript", _VISIT_ROUTER),
        _f("apps/api/src/modules/contracts/contract.router.ts",     "typescript", _CONTRACT_ROUTER),
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
        _f("apps/web/src/app/propiedades/page.tsx",   "typescript", _PROPERTIES_PAGE),
        _f("apps/web/src/app/clientes/page.tsx",      "typescript", _CLIENTS_PAGE),
        _f("apps/web/src/app/visitas/page.tsx",       "typescript", _VISITS_PAGE),
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
console.log(`🏠 __NAME__ API running on port ${port}`);"""

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
export const publicProcedure  = t.procedure;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId) throw new TRPCError({ code: 'UNAUTHORIZED' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const agentProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'AGENT'].includes(ctx.userRole ?? ''))
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
import { propertyRouter } from './modules/properties/property.router';
import { clientRouter }   from './modules/clients/client.router';
import { visitRouter }    from './modules/visits/visit.router';
import { contractRouter } from './modules/contracts/contract.router';

export const appRouter = router({
  auth:      authRouter,
  properties: propertyRouter,
  clients:   clientRouter,
  visits:    visitRouter,
  contracts: contractRouter,
});

export type AppRouter = typeof appRouter;"""

_PRISMA_SCHEMA = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum AgentRole {
  ADMIN
  AGENT
  SUPPORT
}

enum PropertyType {
  APARTMENT
  HOUSE
  STUDIO
  OFFICE
  COMMERCIAL
  LAND
  GARAGE
}

enum PropertyStatus {
  AVAILABLE
  RESERVED
  SOLD
  RENTED
  WITHDRAWN
}

enum PropertyOperation {
  SALE
  RENT
  BOTH
}

enum LeadStatus {
  NEW
  CONTACTED
  QUALIFIED
  PROPOSAL
  WON
  LOST
}

enum VisitStatus {
  SCHEDULED
  COMPLETED
  CANCELLED
  NO_SHOW
}

enum ContractType {
  SALE
  RENT
  OPTION_TO_BUY
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         AgentRole @default(AGENT)
  phone        String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  properties   Property[]
  clients      Client[]
  visits       Visit[]
  contracts    Contract[]
}

model Property {
  id          String            @id @default(cuid())
  agentId     String
  agent       User              @relation(fields: [agentId], references: [id])
  reference   String            @unique
  title       String
  description String?
  type        PropertyType
  operation   PropertyOperation
  status      PropertyStatus    @default(AVAILABLE)
  price       Decimal           @db.Decimal(12, 2)
  area        Decimal?          @db.Decimal(8, 2)
  bedrooms    Int?
  bathrooms   Int?
  floor       Int?
  address     String
  city        String
  postalCode  String?
  latitude    Decimal?          @db.Decimal(9, 6)
  longitude   Decimal?          @db.Decimal(9, 6)
  features    String[]
  imageUrls   String[]
  yearBuilt   Int?
  createdAt   DateTime          @default(now())
  updatedAt   DateTime          @updatedAt
  visits      Visit[]
  contracts   Contract[]
}

model Client {
  id        String     @id @default(cuid())
  agentId   String
  agent     User       @relation(fields: [agentId], references: [id])
  name      String
  email     String?
  phone     String
  status    LeadStatus @default(NEW)
  budget    Decimal?   @db.Decimal(12, 2)
  notes     String?
  lookingFor String?
  source    String?
  createdAt DateTime   @default(now())
  updatedAt DateTime   @updatedAt
  visits    Visit[]
  contracts Contract[]
}

model Visit {
  id          String      @id @default(cuid())
  propertyId  String
  property    Property    @relation(fields: [propertyId], references: [id])
  clientId    String
  client      Client      @relation(fields: [clientId], references: [id])
  agentId     String
  agent       User        @relation(fields: [agentId], references: [id])
  scheduledAt DateTime
  status      VisitStatus @default(SCHEDULED)
  feedback    String?
  interest    Int?        // 1-5 rating
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
}

model Contract {
  id          String       @id @default(cuid())
  propertyId  String
  property    Property     @relation(fields: [propertyId], references: [id])
  clientId    String
  client      Client       @relation(fields: [clientId], references: [id])
  agentId     String
  agent       User         @relation(fields: [agentId], references: [id])
  type        ContractType
  price       Decimal      @db.Decimal(12, 2)
  commission  Decimal?     @db.Decimal(10, 2)
  signedAt    DateTime?
  startDate   DateTime?
  endDate     DateTime?
  notes       String?
  createdAt   DateTime     @default(now())
  updatedAt   DateTime     @updatedAt
}"""

_SEED = """import { PrismaClient, AgentRole, PropertyType, PropertyOperation, PropertyStatus, LeadStatus } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Inmobiliaria...');

  const hash = await bcrypt.hash('password123', 10);

  const admin = await prisma.user.upsert({
    where:  { email: 'admin@inmobiliaria.com' },
    update: {},
    create: { email: 'admin@inmobiliaria.com', name: 'Admin', passwordHash: hash, role: AgentRole.ADMIN, phone: '600 000 001' },
  });

  const agent = await prisma.user.upsert({
    where:  { email: 'agente@inmobiliaria.com' },
    update: {},
    create: { email: 'agente@inmobiliaria.com', name: 'María Agente', passwordHash: hash, role: AgentRole.AGENT, phone: '600 000 002' },
  });

  await prisma.property.createMany({
    skipDuplicates: true,
    data: [
      { agentId: agent.id, reference: 'INM-001', title: 'Piso luminoso en el centro', type: PropertyType.APARTMENT, operation: PropertyOperation.SALE, price: 285000, area: 85, bedrooms: 3, bathrooms: 2, address: 'Calle Mayor 10, 3ºA', city: 'Madrid', postalCode: '28001', features: ['Ascensor', 'Reformado', 'Terraza'] },
      { agentId: agent.id, reference: 'INM-002', title: 'Estudio moderno zona universitaria', type: PropertyType.STUDIO, operation: PropertyOperation.RENT, price: 850, area: 35, bedrooms: 0, bathrooms: 1, address: 'Calle Universidad 5, 1ºB', city: 'Madrid', postalCode: '28004', features: ['Amueblado', 'Internet incluido'] },
      { agentId: admin.id, reference: 'INM-003', title: 'Chalet con jardín y piscina', type: PropertyType.HOUSE, operation: PropertyOperation.SALE, price: 680000, area: 280, bedrooms: 5, bathrooms: 3, address: 'Urbanización Las Palomas 7', city: 'Pozuelo de Alarcón', postalCode: '28224', features: ['Piscina', 'Jardín', 'Garaje doble', 'Trastero'] },
    ],
  });

  await prisma.client.createMany({
    skipDuplicates: true,
    data: [
      { agentId: agent.id, name: 'Juan García', email: 'juan@email.com', phone: '611 222 333', status: LeadStatus.QUALIFIED, budget: 300000, lookingFor: 'Piso 3 habitaciones centro Madrid', source: 'Portal inmobiliario' },
      { agentId: agent.id, name: 'Laura Martínez', phone: '622 333 444', status: LeadStatus.NEW, lookingFor: 'Alquiler estudio Madrid', source: 'Referido' },
    ],
  });

  console.log('✅ Seed completado.');
  console.log('   Admin: admin@inmobiliaria.com / password123');
  console.log('   Agente: agente@inmobiliaria.com / password123');
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
      const token = await ctx.req.server.jwt.sign({ sub: user.id, role: user.role }, { expiresIn: '8h' });
      return { token, user: { id: user.id, name: user.name, email: user.email, role: user.role } };
    }),

  me: protectedProcedure.query(({ ctx }) =>
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true, phone: true } })
  ),
});"""

_PROPERTY_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, agentProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const propertyInput = z.object({
  title:       z.string().min(5),
  description: z.string().optional(),
  type:        z.enum(['APARTMENT', 'HOUSE', 'STUDIO', 'OFFICE', 'COMMERCIAL', 'LAND', 'GARAGE']),
  operation:   z.enum(['SALE', 'RENT', 'BOTH']),
  price:       z.number().positive(),
  area:        z.number().positive().optional(),
  bedrooms:    z.number().int().min(0).optional(),
  bathrooms:   z.number().int().min(0).optional(),
  floor:       z.number().int().optional(),
  address:     z.string().min(5),
  city:        z.string().min(2),
  postalCode:  z.string().optional(),
  features:    z.string().array().default([]),
  imageUrls:   z.string().array().default([]),
  yearBuilt:   z.number().int().optional(),
});

export const propertyRouter = router({
  list: publicProcedure
    .input(z.object({
      city:      z.string().optional(),
      type:      z.enum(['APARTMENT', 'HOUSE', 'STUDIO', 'OFFICE', 'COMMERCIAL', 'LAND', 'GARAGE']).optional(),
      operation: z.enum(['SALE', 'RENT', 'BOTH']).optional(),
      minPrice:  z.number().optional(),
      maxPrice:  z.number().optional(),
      minBedrooms: z.number().int().optional(),
    }).optional())
    .query(({ input }) =>
      prisma.property.findMany({
        where: {
          status: 'AVAILABLE',
          ...(input?.city      && { city: { contains: input.city, mode: 'insensitive' } }),
          ...(input?.type      && { type: input.type }),
          ...(input?.operation && { operation: { in: [input.operation, 'BOTH'] } }),
          ...(input?.minPrice  && { price: { gte: input.minPrice } }),
          ...(input?.maxPrice  && { price: { lte: input.maxPrice } }),
          ...(input?.minBedrooms && { bedrooms: { gte: input.minBedrooms } }),
        },
        include: { agent: { select: { name: true, phone: true, email: true } } },
        orderBy: { createdAt: 'desc' },
      })
    ),

  getById: publicProcedure
    .input(z.string())
    .query(({ input }) =>
      prisma.property.findUnique({ where: { id: input }, include: { agent: { select: { name: true, phone: true, email: true } }, _count: { select: { visits: true } } } })
    ),

  myProperties: agentProcedure
    .query(({ ctx }) =>
      prisma.property.findMany({ where: { agentId: ctx.userId }, include: { _count: { select: { visits: true, contracts: true } } }, orderBy: { createdAt: 'desc' } })
    ),

  create: agentProcedure
    .input(propertyInput)
    .mutation(async ({ input, ctx }) => {
      const count = await prisma.property.count({ where: { agentId: ctx.userId } });
      const reference = `INM-${String(count + 1).padStart(4, '0')}`;
      return prisma.property.create({ data: { ...input, agentId: ctx.userId, reference } });
    }),

  update: agentProcedure
    .input(propertyInput.partial().extend({ id: z.string() }))
    .mutation(({ input: { id, ...data } }) => prisma.property.update({ where: { id }, data })),

  updateStatus: agentProcedure
    .input(z.object({ id: z.string(), status: z.enum(['AVAILABLE', 'RESERVED', 'SOLD', 'RENTED', 'WITHDRAWN']) }))
    .mutation(({ input }) => prisma.property.update({ where: { id: input.id }, data: { status: input.status } })),
});"""

_CLIENT_ROUTER = """import { z } from 'zod';
import { router, agentProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const clientInput = z.object({
  name:       z.string().min(2),
  email:      z.string().email().optional(),
  phone:      z.string().min(9),
  budget:     z.number().positive().optional(),
  lookingFor: z.string().optional(),
  notes:      z.string().optional(),
  source:     z.string().optional(),
});

export const clientRouter = router({
  list: agentProcedure
    .input(z.object({ status: z.enum(['NEW', 'CONTACTED', 'QUALIFIED', 'PROPOSAL', 'WON', 'LOST']).optional() }).optional())
    .query(({ ctx, input }) =>
      prisma.client.findMany({
        where: { agentId: ctx.userId, ...(input?.status && { status: input.status }) },
        include: { _count: { select: { visits: true, contracts: true } } },
        orderBy: { createdAt: 'desc' },
      })
    ),

  create: agentProcedure
    .input(clientInput)
    .mutation(({ input, ctx }) => prisma.client.create({ data: { ...input, agentId: ctx.userId } })),

  update: agentProcedure
    .input(clientInput.partial().extend({ id: z.string() }))
    .mutation(({ input: { id, ...data } }) => prisma.client.update({ where: { id }, data })),

  updateStatus: agentProcedure
    .input(z.object({ id: z.string(), status: z.enum(['NEW', 'CONTACTED', 'QUALIFIED', 'PROPOSAL', 'WON', 'LOST']) }))
    .mutation(({ input }) => prisma.client.update({ where: { id: input.id }, data: { status: input.status } })),
});"""

_VISIT_ROUTER = """import { z } from 'zod';
import { router, agentProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const visitRouter = router({
  list: agentProcedure
    .input(z.object({ propertyId: z.string().optional(), clientId: z.string().optional() }).optional())
    .query(({ ctx, input }) =>
      prisma.visit.findMany({
        where: { agentId: ctx.userId, ...(input?.propertyId && { propertyId: input.propertyId }), ...(input?.clientId && { clientId: input.clientId }) },
        include: { property: { select: { reference: true, title: true, address: true } }, client: { select: { name: true, phone: true } } },
        orderBy: { scheduledAt: 'desc' },
      })
    ),

  schedule: agentProcedure
    .input(z.object({
      propertyId:  z.string(),
      clientId:    z.string(),
      scheduledAt: z.string(),
    }))
    .mutation(({ input, ctx }) =>
      prisma.visit.create({ data: { ...input, agentId: ctx.userId, scheduledAt: new Date(input.scheduledAt) } })
    ),

  complete: agentProcedure
    .input(z.object({ id: z.string(), feedback: z.string().optional(), interest: z.number().int().min(1).max(5).optional() }))
    .mutation(({ input: { id, ...data } }) =>
      prisma.visit.update({ where: { id }, data: { ...data, status: 'COMPLETED' } })
    ),

  cancel: agentProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.visit.update({ where: { id: input }, data: { status: 'CANCELLED' } })),
});"""

_CONTRACT_ROUTER = """import { z } from 'zod';
import { router, agentProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const contractRouter = router({
  list: agentProcedure
    .query(({ ctx }) =>
      prisma.contract.findMany({
        where: { agentId: ctx.userId },
        include: {
          property: { select: { reference: true, title: true } },
          client:   { select: { name: true } },
        },
        orderBy: { createdAt: 'desc' },
      })
    ),

  create: agentProcedure
    .input(z.object({
      propertyId: z.string(),
      clientId:   z.string(),
      type:       z.enum(['SALE', 'RENT', 'OPTION_TO_BUY']),
      price:      z.number().positive(),
      commission: z.number().nonnegative().optional(),
      signedAt:   z.string().optional(),
      startDate:  z.string().optional(),
      endDate:    z.string().optional(),
      notes:      z.string().optional(),
    }))
    .mutation(async ({ input, ctx }) => {
      const { signedAt, startDate, endDate, ...rest } = input;
      const contract = await prisma.contract.create({
        data: {
          ...rest,
          agentId:   ctx.userId,
          signedAt:  signedAt  ? new Date(signedAt)  : undefined,
          startDate: startDate ? new Date(startDate) : undefined,
          endDate:   endDate   ? new Date(endDate)   : undefined,
        },
      });
      // Auto-update property status
      const newStatus = input.type === 'RENT' ? 'RENTED' : 'SOLD';
      await prisma.property.update({ where: { id: input.propertyId }, data: { status: newStatus } });
      return contract;
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
export const metadata: Metadata = { title: '__NAME__', description: 'CRM Inmobiliario' };
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

const OP_LABELS: Record<string, string>     = { SALE: 'Venta', RENT: 'Alquiler', BOTH: 'Venta/Alquiler' };
const STATUS_COLOR: Record<string, string>  = { AVAILABLE: 'bg-green-100 text-green-700', RESERVED: 'bg-yellow-100 text-yellow-700', SOLD: 'bg-red-100 text-red-700', RENTED: 'bg-blue-100 text-blue-700', WITHDRAWN: 'bg-stone-100 text-stone-500' };
const STATUS_LABEL: Record<string, string>  = { AVAILABLE: 'Disponible', RESERVED: 'Reservada', SOLD: 'Vendida', RENTED: 'Alquilada', WITHDRAWN: 'Retirada' };

export default function HomePage() {
  const user = useAuthStore(s => s.user);
  const { data: properties } = trpc.properties.list.useQuery(undefined);

  return (
    <main className="mx-auto max-w-5xl p-6">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">__NAME__</h1>
          <p className="text-slate-500">Portal Inmobiliario</p>
        </div>
        <nav className="flex gap-2">
          {user ? (
            <>
              <Link href="/propiedades" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Mis propiedades</Link>
              <Link href="/clientes" className="rounded-lg border px-4 py-2 text-sm hover:bg-slate-100">Clientes</Link>
              <Link href="/visitas" className="rounded-lg border px-4 py-2 text-sm hover:bg-slate-100">Visitas</Link>
            </>
          ) : (
            <Link href="/login" className="rounded-lg bg-indigo-600 px-6 py-2 text-sm text-white hover:bg-indigo-700">Acceder</Link>
          )}
        </nav>
      </div>

      <h2 className="mb-4 text-lg font-semibold text-slate-700">Propiedades disponibles</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {properties?.map(p => (
          <div key={p.id} className="overflow-hidden rounded-xl border bg-white shadow-sm transition hover:shadow-md">
            <div className="h-40 bg-gradient-to-br from-indigo-100 to-slate-200 flex items-center justify-center text-4xl">🏠</div>
            <div className="p-4">
              <div className="mb-2 flex items-start justify-between gap-2">
                <p className="font-semibold leading-tight">{p.title}</p>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLOR[p.status]}`}>{STATUS_LABEL[p.status]}</span>
              </div>
              <p className="text-xs text-slate-400">{p.address}, {p.city}</p>
              {p.bedrooms !== null && <p className="mt-1 text-xs text-slate-500">{p.bedrooms} hab · {p.bathrooms} baños{p.area ? ` · ${p.area} m²` : ''}</p>}
              <div className="mt-3 flex items-center justify-between">
                <p className="font-bold text-indigo-700">{Number(p.price).toLocaleString('es-ES')} €{p.operation === 'RENT' ? '/mes' : ''}</p>
                <span className="text-xs text-slate-400">{OP_LABELS[p.operation]}</span>
              </div>
              <p className="mt-1 text-xs text-slate-400">Ref: {p.reference} · {p.agent.name}</p>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_PROPERTIES_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const STATUS_COLOR: Record<string, string> = {
  AVAILABLE: 'bg-green-100 text-green-700', RESERVED: 'bg-yellow-100 text-yellow-700',
  SOLD: 'bg-red-100 text-red-700', RENTED: 'bg-blue-100 text-blue-700', WITHDRAWN: 'bg-stone-100 text-stone-500'
};
const STATUS_LABELS: Record<string, string> = { AVAILABLE: 'Disponible', RESERVED: 'Reservada', SOLD: 'Vendida', RENTED: 'Alquilada', WITHDRAWN: 'Retirada' };

export default function PropiedadesPage() {
  const { data, isLoading, refetch } = trpc.properties.myProperties.useQuery();
  const updateStatus = trpc.properties.updateStatus.useMutation({ onSuccess: () => refetch() });

  if (isLoading) return <p className="p-8 text-slate-400">Cargando...</p>;

  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-slate-800">Mis propiedades</h1>
      <div className="space-y-3">
        {data?.map(p => (
          <div key={p.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400">{p.reference}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLOR[p.status]}`}>{STATUS_LABELS[p.status]}</span>
              </div>
              <p className="font-semibold">{p.title}</p>
              <p className="text-sm text-slate-500">{p.address}, {p.city}</p>
              <p className="text-xs text-slate-400 mt-1">{p._count.visits} visitas · {p._count.contracts} contratos</p>
            </div>
            <div className="text-right">
              <p className="font-bold text-indigo-700">{Number(p.price).toLocaleString('es-ES')} €</p>
              {p.status === 'AVAILABLE' && (
                <button onClick={() => updateStatus.mutate({ id: p.id, status: 'RESERVED' })}
                  className="mt-2 rounded-lg border px-3 py-1 text-xs hover:bg-slate-50">
                  Marcar reservada
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_CLIENTS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

const STATUS_COLORS: Record<string, string> = {
  NEW: 'bg-slate-100 text-slate-600', CONTACTED: 'bg-blue-100 text-blue-700',
  QUALIFIED: 'bg-purple-100 text-purple-700', PROPOSAL: 'bg-yellow-100 text-yellow-700',
  WON: 'bg-green-100 text-green-700', LOST: 'bg-red-100 text-red-700',
};
const STATUS_LABELS: Record<string, string> = {
  NEW: 'Nuevo', CONTACTED: 'Contactado', QUALIFIED: 'Cualificado',
  PROPOSAL: 'Propuesta', WON: 'Ganado', LOST: 'Perdido',
};

export default function ClientesPage() {
  const { data, isLoading, refetch } = trpc.clients.list.useQuery();
  const updateStatus = trpc.clients.updateStatus.useMutation({ onSuccess: () => refetch() });

  if (isLoading) return <p className="p-8 text-slate-400">Cargando...</p>;

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-slate-800">Clientes y leads</h1>
      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3">Contacto</th>
              <th className="px-4 py-3">Presupuesto</th>
              <th className="px-4 py-3">Busca</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Visitas</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.map(c => (
              <tr key={c.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium">{c.name}</td>
                <td className="px-4 py-3 text-slate-500">{c.phone}{c.email ? <><br /><span className="text-xs">{c.email}</span></> : ''}</td>
                <td className="px-4 py-3">{c.budget ? `${Number(c.budget).toLocaleString('es-ES')} €` : '—'}</td>
                <td className="px-4 py-3 text-slate-500 max-w-[160px] truncate">{c.lookingFor ?? '—'}</td>
                <td className="px-4 py-3">
                  <select value={c.status} onChange={e => updateStatus.mutate({ id: c.id, status: e.target.value as any })}
                    className={`rounded-full px-2 py-0.5 text-xs font-medium border-0 cursor-pointer ${STATUS_COLORS[c.status]}`}>
                    {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </td>
                <td className="px-4 py-3 text-center text-slate-400">{c._count.visits}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}"""

_VISITS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

const STATUS_COLORS: Record<string, string> = {
  SCHEDULED: 'bg-yellow-100 text-yellow-700', COMPLETED: 'bg-green-100 text-green-700',
  CANCELLED: 'bg-red-100 text-red-700', NO_SHOW: 'bg-stone-100 text-stone-500',
};
const STATUS_LABELS: Record<string, string> = { SCHEDULED: 'Programada', COMPLETED: 'Realizada', CANCELLED: 'Cancelada', NO_SHOW: 'No presentado' };

export default function VisitasPage() {
  const { data, isLoading, refetch } = trpc.visits.list.useQuery();
  const cancel   = trpc.visits.cancel.useMutation({ onSuccess: () => refetch() });
  const complete = trpc.visits.complete.useMutation({ onSuccess: () => refetch() });

  if (isLoading) return <p className="p-8 text-slate-400">Cargando...</p>;

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-slate-800">Visitas</h1>
      <div className="space-y-3">
        {data?.map(v => (
          <div key={v.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm">
            <div>
              <p className="font-semibold">{v.property.title}</p>
              <p className="text-xs text-slate-400">{v.property.reference} · {v.property.address}</p>
              <p className="mt-1 text-sm text-slate-600">{v.client.name} · {v.client.phone}</p>
              <p className="text-xs text-slate-400">
                {new Date(v.scheduledAt).toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' })}
              </p>
              {v.feedback && <p className="mt-1 text-xs italic text-slate-400">"{v.feedback}"</p>}
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[v.status]}`}>
                {STATUS_LABELS[v.status]}
              </span>
              {v.status === 'SCHEDULED' && (
                <div className="flex gap-1.5">
                  <button onClick={() => complete.mutate({ id: v.id })}
                    className="rounded-lg bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700">
                    Realizada
                  </button>
                  <button onClick={() => cancel.mutate(v.id)}
                    className="rounded-lg border px-3 py-1 text-xs hover:bg-slate-50 text-red-500">
                    Cancelar
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        {data?.length === 0 && <p className="text-slate-400">No hay visitas registradas.</p>}
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
      POSTGRES_USER: inmo
      POSTGRES_PASSWORD: inmo_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://inmo:inmo_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://inmo:inmo_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — CRM Inmobiliario

Plataforma de gestión para agencias inmobiliarias: propiedades, clientes, visitas y contratos.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, AGENT, SUPPORT)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Propiedades | Ficha completa con fotos, características, estado y referencia automática |
| Clientes/Leads | Pipeline CRM (Nuevo → Contactado → Cualificado → Propuesta → Ganado) |
| Visitas | Programar, confirmar asistencia y registrar feedback + interés 1-5 |
| Contratos | Venta, alquiler y opción a compra con comisión y actualización automática de estado |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin: admin@inmobiliaria.com / password123
Agente: agente@inmobiliaria.com / password123
"""
