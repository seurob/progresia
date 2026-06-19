"""
FARMACIA template — gestión de farmacia/botica: productos, inventario, recetas y punto de venta.
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
        _f("apps/api/src/modules/products/product.router.ts",    "typescript", _PRODUCT_ROUTER),
        _f("apps/api/src/modules/sales/sale.router.ts",          "typescript", _SALE_ROUTER),
        _f("apps/api/src/modules/prescriptions/prescription.router.ts", "typescript", _PRESCRIPTION_ROUTER),
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
        _f("apps/web/src/app/page.tsx",                          "typescript", _DISPENSARIO_PAGE.replace("__NAME__", name)),
        _f("apps/web/src/app/inventario/page.tsx",               "typescript", _INVENTORY_PAGE),
        _f("apps/web/src/app/recetas/page.tsx",                  "typescript", _PRESCRIPTIONS_PAGE),
        _f("apps/web/src/app/ventas/page.tsx",                   "typescript", _SALES_PAGE),
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
console.log(`💊 __NAME__ API running on port ${port}`);"""

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
export const pharmacistProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || !['ADMIN', 'PHARMACIST'].includes(ctx.userRole ?? ''))
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN')
    throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }         from './modules/auth/auth.router';
import { productRouter }      from './modules/products/product.router';
import { saleRouter }         from './modules/sales/sale.router';
import { prescriptionRouter } from './modules/prescriptions/prescription.router';

export const appRouter = router({
  auth:          authRouter,
  products:      productRouter,
  sales:         saleRouter,
  prescriptions: prescriptionRouter,
});

export type AppRouter = typeof appRouter;"""

_PRISMA_SCHEMA = """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum PharmRole {
  ADMIN
  PHARMACIST
  TECHNICIAN
}

enum SaleStatus {
  OPEN
  COMPLETED
  CANCELLED
}

enum PrescriptionStatus {
  PENDING
  DISPENSED
  EXPIRED
  CANCELLED
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         PharmRole @default(TECHNICIAN)
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  sales        Sale[]
}

model Category {
  id       String    @id @default(cuid())
  name     String    @unique
  products Product[]
}

model Product {
  id                   String     @id @default(cuid())
  barcode              String?    @unique
  name                 String
  activeIngredient     String?
  format               String?
  categoryId           String?
  category             Category?  @relation(fields: [categoryId], references: [id])
  requiresPrescription Boolean    @default(false)
  stock                Int        @default(0)
  minStock             Int        @default(5)
  unitPrice            Decimal    @db.Decimal(8, 2)
  isActive             Boolean    @default(true)
  createdAt            DateTime   @default(now())
  updatedAt            DateTime   @updatedAt
  saleItems            SaleItem[]
  prescriptionItems    PrescriptionItem[]
}

model Sale {
  id          String     @id @default(cuid())
  userId      String
  user        User       @relation(fields: [userId], references: [id])
  status      SaleStatus @default(OPEN)
  total       Decimal    @db.Decimal(10, 2) @default(0)
  notes       String?
  createdAt   DateTime   @default(now())
  completedAt DateTime?
  items       SaleItem[]
  prescription Prescription?
}

model SaleItem {
  id         String  @id @default(cuid())
  saleId     String
  sale       Sale    @relation(fields: [saleId], references: [id], onDelete: Cascade)
  productId  String
  product    Product @relation(fields: [productId], references: [id])
  quantity   Int
  unitPrice  Decimal @db.Decimal(8, 2)
  total      Decimal @db.Decimal(10, 2)
}

model Prescription {
  id             String             @id @default(cuid())
  saleId         String?            @unique
  sale           Sale?              @relation(fields: [saleId], references: [id])
  patientName    String
  patientDni     String?
  doctorName     String
  doctorLicense  String?
  issuedAt       DateTime
  validUntil     DateTime?
  status         PrescriptionStatus @default(PENDING)
  notes          String?
  createdAt      DateTime           @default(now())
  updatedAt      DateTime           @updatedAt
  items          PrescriptionItem[]
}

model PrescriptionItem {
  id             String       @id @default(cuid())
  prescriptionId String
  prescription   Prescription @relation(fields: [prescriptionId], references: [id], onDelete: Cascade)
  productId      String
  product        Product      @relation(fields: [productId], references: [id])
  quantity       Int
  instructions   String?
}"""

_SEED = """import { PrismaClient, PharmRole } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Farmacia...');

  const hash = await bcrypt.hash('password123', 10);

  await prisma.user.upsert({
    where: { email: 'admin@farmacia.com' },
    update: {},
    create: { email: 'admin@farmacia.com', name: 'Admin', passwordHash: hash, role: PharmRole.ADMIN },
  });
  await prisma.user.upsert({
    where: { email: 'farm1@farmacia.com' },
    update: {},
    create: { email: 'farm1@farmacia.com', name: 'Dra. García', passwordHash: hash, role: PharmRole.PHARMACIST },
  });
  await prisma.user.upsert({
    where: { email: 'tec1@farmacia.com' },
    update: {},
    create: { email: 'tec1@farmacia.com', name: 'Técnico Ruiz', passwordHash: hash, role: PharmRole.TECHNICIAN },
  });

  const catAnalgesia = await prisma.category.upsert({ where: { name: 'Analgesia' }, update: {}, create: { name: 'Analgesia' } });
  const catAntibio   = await prisma.category.upsert({ where: { name: 'Antibióticos' }, update: {}, create: { name: 'Antibióticos' } });
  const catDigestivo = await prisma.category.upsert({ where: { name: 'Digestivo' }, update: {}, create: { name: 'Digestivo' } });

  await prisma.product.createMany({
    data: [
      { barcode: '8470001234561', name: 'Paracetamol 500mg', activeIngredient: 'Paracetamol', format: 'Comprimidos 500mg', categoryId: catAnalgesia.id, requiresPrescription: false, stock: 200, minStock: 30, unitPrice: 2.45 },
      { barcode: '8470001234562', name: 'Ibuprofeno 400mg', activeIngredient: 'Ibuprofeno', format: 'Comprimidos 400mg', categoryId: catAnalgesia.id, requiresPrescription: false, stock: 150, minStock: 20, unitPrice: 3.90 },
      { barcode: '8470001234563', name: 'Amoxicilina 500mg', activeIngredient: 'Amoxicilina', format: 'Cápsulas 500mg', categoryId: catAntibio.id, requiresPrescription: true, stock: 4, minStock: 10, unitPrice: 7.20 },
      { barcode: '8470001234564', name: 'Omeprazol 20mg', activeIngredient: 'Omeprazol', format: 'Cápsulas 20mg', categoryId: catDigestivo.id, requiresPrescription: false, stock: 80, minStock: 15, unitPrice: 4.10 },
      { barcode: '8470001234565', name: 'Metformina 850mg', activeIngredient: 'Metformina', format: 'Comprimidos 850mg', requiresPrescription: true, stock: 2, minStock: 10, unitPrice: 5.50 },
    ],
    skipDuplicates: true,
  });

  console.log('✅ Seed completado.');
  console.log('   Admin:        admin@farmacia.com / password123');
  console.log('   Farmacéutica: farm1@farmacia.com / password123');
  console.log('   Técnico:      tec1@farmacia.com / password123');
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
});"""

_PRODUCT_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const productRouter = router({
  list: protectedProcedure
    .input(z.object({
      search:              z.string().optional(),
      requiresPrescription: z.boolean().optional(),
      lowStock:            z.boolean().optional(),
      categoryId:          z.string().optional(),
    }).optional())
    .query(({ input }) =>
      prisma.product.findMany({
        where: {
          isActive: true,
          ...(input?.search && { OR: [{ name: { contains: input.search, mode: 'insensitive' } }, { barcode: { contains: input.search } }, { activeIngredient: { contains: input.search, mode: 'insensitive' } }] }),
          ...(input?.requiresPrescription !== undefined && { requiresPrescription: input.requiresPrescription }),
          ...(input?.lowStock && { stock: { lte: prisma.product.fields.minStock } }),
          ...(input?.categoryId && { categoryId: input.categoryId }),
        },
        include: { category: true },
        orderBy: { name: 'asc' },
      })
    ),

  lowStock: protectedProcedure.query(() =>
    prisma.$queryRaw<{ id: string; name: string; stock: number; minStock: number; unitPrice: string }[]>`
      SELECT id, name, stock, "minStock", "unitPrice"::text FROM "Product"
      WHERE "isActive" = true AND stock <= "minStock"
      ORDER BY stock ASC
    `
  ),

  categories: protectedProcedure.query(() => prisma.category.findMany({ orderBy: { name: 'asc' } })),

  byBarcode: protectedProcedure
    .input(z.string())
    .query(({ input }) => prisma.product.findUnique({ where: { barcode: input }, include: { category: true } })),

  create: adminProcedure
    .input(z.object({
      name:                z.string().min(2),
      activeIngredient:    z.string().optional(),
      format:              z.string().optional(),
      barcode:             z.string().optional(),
      categoryId:          z.string().optional(),
      requiresPrescription: z.boolean().default(false),
      stock:               z.number().int().min(0).default(0),
      minStock:            z.number().int().min(0).default(5),
      unitPrice:           z.number().positive(),
    }))
    .mutation(({ input }) => prisma.product.create({ data: input })),

  adjustStock: adminProcedure
    .input(z.object({ id: z.string(), delta: z.number().int() }))
    .mutation(({ input }) =>
      prisma.product.update({ where: { id: input.id }, data: { stock: { increment: input.delta } } })
    ),
});"""

_SALE_ROUTER = """import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const saleRouter = router({
  today: protectedProcedure.query(() => {
    const start = new Date(); start.setHours(0, 0, 0, 0);
    const end   = new Date(); end.setHours(23, 59, 59, 999);
    return prisma.sale.findMany({
      where: { createdAt: { gte: start, lte: end }, status: 'COMPLETED' },
      include: { user: { select: { name: true } }, items: { include: { product: true } } },
      orderBy: { completedAt: 'desc' },
    });
  }),

  open: protectedProcedure.query(({ ctx }) =>
    prisma.sale.findFirst({
      where: { userId: ctx.userId, status: 'OPEN' },
      include: { items: { include: { product: true } } },
    })
  ),

  create: protectedProcedure.mutation(({ ctx }) =>
    prisma.sale.create({ data: { userId: ctx.userId } })
  ),

  addItem: protectedProcedure
    .input(z.object({ saleId: z.string(), productId: z.string(), quantity: z.number().int().min(1) }))
    .mutation(async ({ input }) => {
      const product = await prisma.product.findUniqueOrThrow({ where: { id: input.productId } });
      if (product.stock < input.quantity)
        throw new TRPCError({ code: 'BAD_REQUEST', message: `Stock insuficiente: solo quedan ${product.stock} unidades` });

      const existing = await prisma.saleItem.findFirst({ where: { saleId: input.saleId, productId: input.productId } });
      const total = Number(product.unitPrice) * input.quantity;

      if (existing) {
        await prisma.saleItem.update({ where: { id: existing.id }, data: { quantity: { increment: input.quantity }, total: { increment: total } } });
      } else {
        await prisma.saleItem.create({ data: { saleId: input.saleId, productId: input.productId, quantity: input.quantity, unitPrice: product.unitPrice, total } });
      }
      // Recalculate sale total
      const items = await prisma.saleItem.findMany({ where: { saleId: input.saleId } });
      const saleTotal = items.reduce((s, i) => s + Number(i.total), 0);
      return prisma.sale.update({ where: { id: input.saleId }, data: { total: saleTotal }, include: { items: { include: { product: true } } } });
    }),

  removeItem: protectedProcedure
    .input(z.string())
    .mutation(async ({ input: itemId }) => {
      const item = await prisma.saleItem.findUniqueOrThrow({ where: { id: itemId } });
      await prisma.saleItem.delete({ where: { id: itemId } });
      const items = await prisma.saleItem.findMany({ where: { saleId: item.saleId } });
      const total = items.reduce((s, i) => s + Number(i.total), 0);
      return prisma.sale.update({ where: { id: item.saleId }, data: { total }, include: { items: { include: { product: true } } } });
    }),

  complete: protectedProcedure
    .input(z.string())
    .mutation(async ({ input: saleId }) => {
      const sale = await prisma.sale.findUniqueOrThrow({ where: { id: saleId }, include: { items: true } });
      if (!sale.items.length) throw new TRPCError({ code: 'BAD_REQUEST', message: 'La venta está vacía' });
      // Decrement stock for all items
      await Promise.all(sale.items.map(i => prisma.product.update({ where: { id: i.productId }, data: { stock: { decrement: i.quantity } } })));
      return prisma.sale.update({ where: { id: saleId }, data: { status: 'COMPLETED', completedAt: new Date() } });
    }),

  cancel: protectedProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.sale.update({ where: { id: input }, data: { status: 'CANCELLED' } })),
});"""

_PRESCRIPTION_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, pharmacistProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const prescriptionRouter = router({
  list: protectedProcedure
    .input(z.object({ status: z.enum(['PENDING', 'DISPENSED', 'EXPIRED', 'CANCELLED']).optional() }).optional())
    .query(({ input }) =>
      prisma.prescription.findMany({
        where: input?.status ? { status: input.status } : undefined,
        include: { items: { include: { product: { select: { name: true } } } } },
        orderBy: { createdAt: 'desc' },
        take: 50,
      })
    ),

  register: protectedProcedure
    .input(z.object({
      patientName:   z.string().min(2),
      patientDni:    z.string().optional(),
      doctorName:    z.string().min(2),
      doctorLicense: z.string().optional(),
      issuedAt:      z.string(),
      validUntil:    z.string().optional(),
      notes:         z.string().optional(),
      items:         z.array(z.object({ productId: z.string(), quantity: z.number().int().min(1), instructions: z.string().optional() })),
    }))
    .mutation(({ input }) =>
      prisma.prescription.create({
        data: {
          patientName: input.patientName, patientDni: input.patientDni,
          doctorName: input.doctorName, doctorLicense: input.doctorLicense,
          issuedAt: new Date(input.issuedAt),
          validUntil: input.validUntil ? new Date(input.validUntil) : undefined,
          notes: input.notes,
          items: { create: input.items },
        },
        include: { items: { include: { product: true } } },
      })
    ),

  dispense: pharmacistProcedure
    .input(z.string())
    .mutation(({ input }) =>
      prisma.prescription.update({ where: { id: input }, data: { status: 'DISPENSED' } })
    ),

  cancel: pharmacistProcedure
    .input(z.string())
    .mutation(({ input }) =>
      prisma.prescription.update({ where: { id: input }, data: { status: 'CANCELLED' } })
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
export const metadata: Metadata = { title: '__NAME__', description: 'Gestión de farmacia' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-white text-slate-900">
        <TRPCProvider>
          <nav className="bg-green-700 text-white px-6 py-3 flex items-center gap-6 shadow">
            <span className="font-bold">💊 __NAME__</span>
            <a href="/"           className="text-sm hover:text-green-200">Dispensario</a>
            <a href="/inventario" className="text-sm hover:text-green-200">Inventario</a>
            <a href="/recetas"    className="text-sm hover:text-green-200">Recetas</a>
            <a href="/ventas"     className="text-sm hover:text-green-200">Ventas</a>
          </nav>
          {children}
        </TRPCProvider>
      </body>
    </html>
  );
}"""

_DISPENSARIO_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

export default function DispensarioPage() {
  const user = useAuthStore(s => s.user);
  const [search, setSearch] = useState('');
  const { data: products } = trpc.products.list.useQuery({ search }, { enabled: search.length > 1 });
  const { data: currentSale, refetch } = trpc.sales.open.useQuery(undefined, { enabled: !!user });
  const createSale = trpc.sales.create.useMutation({ onSuccess: () => refetch() });
  const addItem    = trpc.sales.addItem.useMutation({ onSuccess: () => { refetch(); setSearch(''); } });
  const removeItem = trpc.sales.removeItem.useMutation({ onSuccess: () => refetch() });
  const complete   = trpc.sales.complete.useMutation({ onSuccess: () => refetch() });

  if (!user) return <main className="p-8 text-center text-slate-400">Inicia sesión para usar el dispensario.</main>;

  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-2xl font-bold">💊 Dispensario</h1>
      <div className="grid grid-cols-2 gap-6">
        {/* Search & add */}
        <div>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Buscar por nombre, principio activo o código de barras..."
            className="w-full rounded-xl border px-4 py-3 mb-3 text-sm" />
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {products?.map(p => (
              <button key={p.id} onClick={async () => {
                let saleId = currentSale?.id;
                if (!saleId) { const s = await createSale.mutateAsync(); saleId = s.id; }
                addItem.mutate({ saleId, productId: p.id, quantity: 1 });
              }} className="w-full text-left rounded-xl border p-3 hover:bg-green-50 transition">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{p.name}</p>
                    <p className="text-xs text-slate-400">{p.activeIngredient} · {p.format}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-700">{Number(p.unitPrice).toFixed(2)} €</p>
                    <p className={`text-xs ${p.stock <= p.minStock ? 'text-red-500' : 'text-slate-400'}`}>Stock: {p.stock}</p>
                  </div>
                </div>
                {p.requiresPrescription && <span className="text-xs text-amber-600 font-medium">⚕️ Requiere receta</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Current sale */}
        <div className="rounded-xl border bg-slate-50 p-4">
          <p className="mb-3 font-semibold text-slate-700">Venta actual</p>
          {!currentSale?.items?.length && <p className="text-slate-400 text-sm">Sin productos. Busca y añade artículos.</p>}
          <div className="space-y-2">
            {currentSale?.items?.map(i => (
              <div key={i.id} className="flex items-center justify-between rounded-lg bg-white border px-3 py-2">
                <div>
                  <p className="text-sm font-medium">{i.product.name}</p>
                  <p className="text-xs text-slate-400">x{i.quantity} · {Number(i.unitPrice).toFixed(2)} €/u</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-green-700">{Number(i.total).toFixed(2)} €</span>
                  <button onClick={() => removeItem.mutate(i.id)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
                </div>
              </div>
            ))}
          </div>
          {!!currentSale?.items?.length && (
            <div className="mt-4 border-t pt-3">
              <div className="flex justify-between font-bold mb-3">
                <span>Total</span>
                <span className="text-green-700">{Number(currentSale.total).toFixed(2)} €</span>
              </div>
              <button onClick={() => complete.mutate(currentSale.id)}
                className="w-full rounded-xl bg-green-700 py-3 font-bold text-white hover:bg-green-800">
                Cobrar y finalizar
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}"""

_INVENTORY_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

export default function InventarioPage() {
  const { data } = trpc.products.list.useQuery();
  const low = data?.filter(p => p.stock <= p.minStock) ?? [];

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h1 className="mb-2 text-2xl font-bold">Inventario</h1>
      {low.length > 0 && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="font-semibold text-red-700 mb-2">⚠️ {low.length} producto(s) con stock bajo</p>
          <div className="flex flex-wrap gap-2">
            {low.map(p => <span key={p.id} className="rounded-full bg-red-100 text-red-700 px-3 py-0.5 text-sm">{p.name} ({p.stock}/{p.minStock})</span>)}
          </div>
        </div>
      )}
      <div className="space-y-2">
        {data?.map(p => {
          const pct = Math.min((p.stock / (p.minStock * 4)) * 100, 100);
          const isLow = p.stock <= p.minStock;
          return (
            <div key={p.id} className={`rounded-xl border p-4 ${isLow ? 'border-red-200 bg-red-50' : 'bg-white'}`}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-semibold">{p.name}</p>
                  <p className="text-xs text-slate-400">{p.activeIngredient ?? '—'} · {p.format ?? '—'} · {p.category?.name ?? 'Sin categoría'}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">{Number(p.unitPrice).toFixed(2)} €</p>
                  {p.requiresPrescription && <p className="text-xs text-amber-600">⚕️ Receta</p>}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 rounded-full bg-slate-200">
                  <div className={`h-2 rounded-full ${isLow ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${pct}%` }} />
                </div>
                <span className={`text-sm font-bold w-20 text-right ${isLow ? 'text-red-600' : 'text-slate-700'}`}>{p.stock} uds</span>
                <span className="text-xs text-slate-400">mín. {p.minStock}</span>
              </div>
            </div>
          );
        })}
      </div>
    </main>
  );
}"""

_PRESCRIPTIONS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

const STATUS_COLORS: Record<string, string> = { PENDING: 'bg-yellow-100 text-yellow-700', DISPENSED: 'bg-green-100 text-green-700', EXPIRED: 'bg-slate-100 text-slate-500', CANCELLED: 'bg-red-100 text-red-600' };
const STATUS_LABELS: Record<string, string> = { PENDING: 'Pendiente', DISPENSED: 'Dispensada', EXPIRED: 'Caducada', CANCELLED: 'Cancelada' };

export default function RecetasPage() {
  const { data, refetch } = trpc.prescriptions.list.useQuery();
  const dispense = trpc.prescriptions.dispense.useMutation({ onSuccess: () => refetch() });
  const cancel   = trpc.prescriptions.cancel.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Recetas médicas</h1>
      <div className="space-y-3">
        {data?.map(rx => (
          <div key={rx.id} className="rounded-xl border bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-semibold">{rx.patientName}</p>
                <p className="text-sm text-slate-500">Dr. {rx.doctorName} · {rx.doctorLicense ?? ''}</p>
                <p className="text-xs text-slate-400">{new Date(rx.issuedAt).toLocaleDateString('es-ES')}</p>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[rx.status]}`}>{STATUS_LABELS[rx.status]}</span>
            </div>
            <div className="mt-2 space-y-1">
              {rx.items.map(i => (
                <p key={i.id} className="text-sm text-slate-600">• {i.product.name} × {i.quantity}{i.instructions ? ` — ${i.instructions}` : ''}</p>
              ))}
            </div>
            {rx.status === 'PENDING' && (
              <div className="mt-3 flex gap-2">
                <button onClick={() => dispense.mutate(rx.id)} className="rounded-lg bg-green-700 px-4 py-1.5 text-xs text-white hover:bg-green-800">Dispensar</button>
                <button onClick={() => cancel.mutate(rx.id)}   className="rounded-lg border border-red-300 px-4 py-1.5 text-xs text-red-600 hover:bg-red-50">Cancelar</button>
              </div>
            )}
          </div>
        ))}
        {data?.length === 0 && <p className="text-slate-400">Sin recetas registradas.</p>}
      </div>
    </main>
  );
}"""

_SALES_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

export default function VentasPage() {
  const { data } = trpc.sales.today.useQuery();
  const total = data?.reduce((s, v) => s + Number(v.total), 0) ?? 0;

  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Ventas de hoy</h1>
        <div className="rounded-xl bg-green-100 px-4 py-2 text-right">
          <p className="text-xs text-green-600">{data?.length ?? 0} ventas</p>
          <p className="text-lg font-bold text-green-700">{total.toFixed(2)} €</p>
        </div>
      </div>
      <div className="space-y-3">
        {data?.map(v => (
          <div key={v.id} className="rounded-xl border bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">{v.completedAt ? new Date(v.completedAt).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) : '—'} · {v.user.name}</p>
              <p className="font-bold text-green-700">{Number(v.total).toFixed(2)} €</p>
            </div>
            <div className="space-y-1">
              {v.items.map(i => (
                <p key={i.id} className="text-sm text-slate-600">{i.product.name} × {i.quantity} — {Number(i.total).toFixed(2)} €</p>
              ))}
            </div>
          </div>
        ))}
        {data?.length === 0 && <p className="text-slate-400">Sin ventas completadas hoy.</p>}
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
      POSTGRES_USER: farmacia
      POSTGRES_PASSWORD: farm_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://farmacia:farm_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://farmacia:farm_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Gestión de Farmacia

Sistema completo de gestión farmacéutica: inventario, punto de venta, recetas y control de stock.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, PHARMACIST, TECHNICIAN)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Dispensario | POS rápido: buscar producto → añadir → cobrar con descuento automático de stock |
| Inventario | Vista de stock con barras de nivel + alertas rojas de stock mínimo |
| Recetas | Registro de prescripciones médicas + flujo PENDING → DISPENSED |
| Ventas | Historial diario con totales por turno |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin:        admin@farmacia.com / password123
Farmacéutica: farm1@farmacia.com / password123
"""
