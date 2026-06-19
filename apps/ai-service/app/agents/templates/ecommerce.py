"""
ECOMMERCE template — tienda online completa.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: productos, categorías, carrito, pedidos, pagos.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",                       "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",                       "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",                        "typescript", _API_INDEX.replace("__NAME__", name)),
        _f("apps/api/src/trpc.ts",                         "typescript", _TRPC),
        _f("apps/api/src/router.ts",                       "typescript", _ROUTER),
        _f("apps/api/prisma/schema.prisma",                "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",                      "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",     "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/products/product.router.ts", "typescript", _PRODUCT_ROUTER),
        _f("apps/api/src/modules/cart/cart.router.ts",     "typescript", _CART_ROUTER),
        _f("apps/api/src/modules/orders/order.router.ts",  "typescript", _ORDER_ROUTER),
        _f("apps/api/Dockerfile",                          "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",                        "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",                       "json",       _WEB_TSCONFIG),
        _f("apps/web/next.config.js",                      "javascript", _NEXT_CONFIG),
        _f("apps/web/tailwind.config.ts",                  "typescript", _TAILWIND),
        _f("apps/web/postcss.config.js",                   "javascript", _POSTCSS),
        _f("apps/web/src/app/globals.css",                 "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",                     "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",                "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts",               "typescript", _AUTH_STORE),
        _f("apps/web/src/lib/cart-store.ts",               "typescript", _CART_STORE),
        _f("apps/web/src/app/layout.tsx",                  "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",                    "typescript", _LANDING.replace("__NAME__", name)),
        _f("apps/web/src/app/productos/page.tsx",          "typescript", _PRODUCTS_PAGE),
        _f("apps/web/src/app/carrito/page.tsx",            "typescript", _CART_PAGE),
        _f("apps/web/src/app/pedidos/page.tsx",            "typescript", _ORDERS_PAGE),
        _f("apps/web/Dockerfile",                          "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",                             "nginx",      _NGINX),
        _f("docker-compose.yml",                           "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                                 "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                                    "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
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
console.log(`🛒 __NAME__ API running on port ${port}`);"""

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
export const router            = t.router;
export const publicProcedure   = t.procedure;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId) throw new TRPCError({ code: 'UNAUTHORIZED' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN') throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }    from './modules/auth/auth.router';
import { productRouter } from './modules/products/product.router';
import { cartRouter }    from './modules/cart/cart.router';
import { orderRouter }   from './modules/orders/order.router';

export const appRouter = router({
  auth:     authRouter,
  products: productRouter,
  cart:     cartRouter,
  orders:   orderRouter,
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
  CUSTOMER
}

enum OrderStatus {
  PENDING
  CONFIRMED
  PROCESSING
  SHIPPED
  DELIVERED
  CANCELLED
  REFUNDED
}

enum PaymentStatus {
  PENDING
  PAID
  FAILED
  REFUNDED
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         UserRole  @default(CUSTOMER)
  phone        String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  addresses    Address[]
  cart         Cart?
  orders       Order[]
}

model Address {
  id         String  @id @default(cuid())
  userId     String
  user       User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  label      String  @default("Casa")
  street     String
  city       String
  postalCode String
  country    String  @default("ES")
  isDefault  Boolean @default(false)
  orders     Order[]
}

model Category {
  id          String     @id @default(cuid())
  name        String     @unique
  slug        String     @unique
  description String?
  imageUrl    String?
  createdAt   DateTime   @default(now())
  products    Product[]
}

model Product {
  id          String      @id @default(cuid())
  categoryId  String
  category    Category    @relation(fields: [categoryId], references: [id])
  name        String
  slug        String      @unique
  description String?
  price       Decimal     @db.Decimal(10, 2)
  comparePrice Decimal?   @db.Decimal(10, 2)
  stock       Int         @default(0)
  sku         String?     @unique
  imageUrls   String[]
  tags        String[]
  isPublished Boolean     @default(true)
  weight      Decimal?    @db.Decimal(6, 3)
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
  cartItems   CartItem[]
  orderItems  OrderItem[]
}

model Cart {
  id        String     @id @default(cuid())
  userId    String     @unique
  user      User       @relation(fields: [userId], references: [id], onDelete: Cascade)
  updatedAt DateTime   @updatedAt
  items     CartItem[]
}

model CartItem {
  id        String   @id @default(cuid())
  cartId    String
  cart      Cart     @relation(fields: [cartId], references: [id], onDelete: Cascade)
  productId String
  product   Product  @relation(fields: [productId], references: [id])
  quantity  Int      @default(1)
  addedAt   DateTime @default(now())

  @@unique([cartId, productId])
}

model Order {
  id            String        @id @default(cuid())
  userId        String
  user          User          @relation(fields: [userId], references: [id])
  addressId     String?
  address       Address?      @relation(fields: [addressId], references: [id])
  status        OrderStatus   @default(PENDING)
  paymentStatus PaymentStatus @default(PENDING)
  subtotal      Decimal       @db.Decimal(10, 2)
  shippingCost  Decimal       @db.Decimal(8, 2) @default(0)
  total         Decimal       @db.Decimal(10, 2)
  notes         String?
  createdAt     DateTime      @default(now())
  updatedAt     DateTime      @updatedAt
  items         OrderItem[]
}

model OrderItem {
  id        String  @id @default(cuid())
  orderId   String
  order     Order   @relation(fields: [orderId], references: [id], onDelete: Cascade)
  productId String
  product   Product @relation(fields: [productId], references: [id])
  quantity  Int
  unitPrice Decimal @db.Decimal(10, 2)
  total     Decimal @db.Decimal(10, 2)
}"""

_SEED = """import { PrismaClient, UserRole } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Ecommerce...');

  const hash = await bcrypt.hash('password123', 10);

  await prisma.user.upsert({
    where: { email: 'admin@tienda.com' },
    update: {},
    create: { email: 'admin@tienda.com', name: 'Admin', passwordHash: hash, role: UserRole.ADMIN },
  });

  const customer = await prisma.user.upsert({
    where: { email: 'cliente@email.com' },
    update: {},
    create: { email: 'cliente@email.com', name: 'Ana Cliente', passwordHash: hash, role: UserRole.CUSTOMER, phone: '611 222 333' },
  });

  // Categories
  const electronics = await prisma.category.upsert({
    where: { slug: 'electronica' },
    update: {},
    create: { name: 'Electrónica', slug: 'electronica', description: 'Dispositivos y gadgets' },
  });
  const clothing = await prisma.category.upsert({
    where: { slug: 'ropa' },
    update: {},
    create: { name: 'Ropa', slug: 'ropa', description: 'Moda y accesorios' },
  });
  const home = await prisma.category.upsert({
    where: { slug: 'hogar' },
    update: {},
    create: { name: 'Hogar', slug: 'hogar', description: 'Decoración y menaje' },
  });

  // Products
  const products = [
    { categoryId: electronics.id, name: 'Auriculares Bluetooth Pro', slug: 'auriculares-bt-pro', description: 'Cancelación de ruido activa, 30h batería', price: 89.99, stock: 50, sku: 'AUD-001', tags: ['audio', 'bluetooth', 'inalámbrico'] },
    { categoryId: electronics.id, name: 'Cargador USB-C 65W', slug: 'cargador-usbc-65w', description: 'Carga rápida compatible con portátiles', price: 29.99, comparePrice: 39.99, stock: 120, sku: 'CHG-001', tags: ['cargador', 'usb-c'] },
    { categoryId: clothing.id, name: 'Camiseta Algodón Orgánico', slug: 'camiseta-algodon-organico', description: 'Algodón 100% orgánico, lavable a máquina', price: 19.99, stock: 200, sku: 'CAM-001', tags: ['camiseta', 'sostenible'] },
    { categoryId: clothing.id, name: 'Zapatillas Running Trail', slug: 'zapatillas-running-trail', description: 'Suela Vibram, drop 8mm', price: 119.00, comparePrice: 149.00, stock: 30, sku: 'ZAP-001', tags: ['running', 'trail'] },
    { categoryId: home.id, name: 'Lámpara LED escritorio', slug: 'lampara-led-escritorio', description: '5 niveles de brillo, USB-A integrado', price: 34.99, stock: 75, sku: 'LAM-001', tags: ['lámpara', 'led', 'escritorio'] },
  ];

  for (const p of products) {
    await prisma.product.upsert({ where: { slug: p.slug }, update: {}, create: p });
  }

  // Customer address
  await prisma.address.create({
    data: { userId: customer.id, label: 'Casa', street: 'Calle Mayor 10, 2ºA', city: 'Madrid', postalCode: '28001', isDefault: true },
  });

  console.log('✅ Seed completado.');
  console.log('   Admin: admin@tienda.com / password123');
  console.log('   Cliente: cliente@email.com / password123');
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
      const existing = await prisma.user.findUnique({ where: { email: input.email } });
      if (existing) throw new Error('El email ya está registrado');
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
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true, phone: true, addresses: true } })
  ),
});"""

_PRODUCT_ROUTER = """import { z } from 'zod';
import { router, publicProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const productInput = z.object({
  categoryId:   z.string(),
  name:         z.string().min(2),
  slug:         z.string().min(2),
  description:  z.string().optional(),
  price:        z.number().positive(),
  comparePrice: z.number().positive().optional(),
  stock:        z.number().int().min(0).default(0),
  sku:          z.string().optional(),
  tags:         z.string().array().default([]),
  isPublished:  z.boolean().default(true),
});

export const productRouter = router({
  list: publicProcedure
    .input(z.object({
      categorySlug: z.string().optional(),
      search:       z.string().optional(),
      minPrice:     z.number().optional(),
      maxPrice:     z.number().optional(),
      inStock:      z.boolean().default(false),
      page:         z.number().int().min(1).default(1),
      limit:        z.number().int().min(1).max(50).default(20),
    }).optional())
    .query(async ({ input }) => {
      const where = {
        isPublished: true,
        ...(input?.categorySlug && { category: { slug: input.categorySlug } }),
        ...(input?.search       && { name: { contains: input.search, mode: 'insensitive' as const } }),
        ...(input?.minPrice     && { price: { gte: input.minPrice } }),
        ...(input?.maxPrice     && { price: { lte: input.maxPrice } }),
        ...(input?.inStock      && { stock: { gt: 0 } }),
      };
      const [items, total] = await prisma.$transaction([
        prisma.product.findMany({ where, include: { category: true }, orderBy: { createdAt: 'desc' }, skip: ((input?.page ?? 1) - 1) * (input?.limit ?? 20), take: input?.limit ?? 20 }),
        prisma.product.count({ where }),
      ]);
      return { items, total, page: input?.page ?? 1, pages: Math.ceil(total / (input?.limit ?? 20)) };
    }),

  bySlug: publicProcedure
    .input(z.string())
    .query(({ input }) => prisma.product.findUnique({ where: { slug: input }, include: { category: true } })),

  categories: publicProcedure.query(() => prisma.category.findMany({ orderBy: { name: 'asc' } })),

  create: adminProcedure.input(productInput).mutation(({ input }) => prisma.product.create({ data: input })),
  update: adminProcedure.input(productInput.partial().extend({ id: z.string() })).mutation(({ input: { id, ...data } }) => prisma.product.update({ where: { id }, data })),
  delete: adminProcedure.input(z.string()).mutation(({ input }) => prisma.product.delete({ where: { id: input } })),
});"""

_CART_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

async function getOrCreateCart(userId: string) {
  return prisma.cart.upsert({
    where: { userId },
    update: {},
    create: { userId },
    include: { items: { include: { product: { include: { category: true } } } } },
  });
}

export const cartRouter = router({
  get: protectedProcedure.query(({ ctx }) => getOrCreateCart(ctx.userId)),

  addItem: protectedProcedure
    .input(z.object({ productId: z.string(), quantity: z.number().int().min(1).default(1) }))
    .mutation(async ({ ctx, input }) => {
      const cart = await getOrCreateCart(ctx.userId);
      const product = await prisma.product.findUniqueOrThrow({ where: { id: input.productId } });
      if (product.stock < input.quantity) throw new Error('Stock insuficiente');
      await prisma.cartItem.upsert({
        where: { cartId_productId: { cartId: cart.id, productId: input.productId } },
        update: { quantity: { increment: input.quantity } },
        create: { cartId: cart.id, productId: input.productId, quantity: input.quantity },
      });
      return getOrCreateCart(ctx.userId);
    }),

  updateQuantity: protectedProcedure
    .input(z.object({ productId: z.string(), quantity: z.number().int().min(0) }))
    .mutation(async ({ ctx, input }) => {
      const cart = await getOrCreateCart(ctx.userId);
      if (input.quantity === 0) {
        await prisma.cartItem.deleteMany({ where: { cartId: cart.id, productId: input.productId } });
      } else {
        await prisma.cartItem.update({ where: { cartId_productId: { cartId: cart.id, productId: input.productId } }, data: { quantity: input.quantity } });
      }
      return getOrCreateCart(ctx.userId);
    }),

  clear: protectedProcedure
    .mutation(async ({ ctx }) => {
      const cart = await prisma.cart.findUnique({ where: { userId: ctx.userId } });
      if (cart) await prisma.cartItem.deleteMany({ where: { cartId: cart.id } });
      return { ok: true };
    }),
});"""

_ORDER_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure, adminProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const orderRouter = router({
  myOrders: protectedProcedure.query(({ ctx }) =>
    prisma.order.findMany({ where: { userId: ctx.userId }, include: { items: { include: { product: true } } }, orderBy: { createdAt: 'desc' } })
  ),

  checkout: protectedProcedure
    .input(z.object({ addressId: z.string().optional(), notes: z.string().optional() }))
    .mutation(async ({ ctx, input }) => {
      const cart = await prisma.cart.findUnique({ where: { userId: ctx.userId }, include: { items: { include: { product: true } } } });
      if (!cart || cart.items.length === 0) throw new Error('El carrito está vacío');

      const subtotal = cart.items.reduce((acc, i) => acc + Number(i.product.price) * i.quantity, 0);
      const shippingCost = subtotal >= 50 ? 0 : 4.95;
      const total = subtotal + shippingCost;

      const order = await prisma.order.create({
        data: {
          userId: ctx.userId,
          addressId: input.addressId,
          subtotal,
          shippingCost,
          total,
          notes: input.notes,
          items: {
            create: cart.items.map(i => ({
              productId: i.productId,
              quantity:  i.quantity,
              unitPrice: i.product.price,
              total:     Number(i.product.price) * i.quantity,
            })),
          },
        },
        include: { items: { include: { product: true } } },
      });

      // Decrease stock + clear cart
      await prisma.$transaction([
        ...cart.items.map(i => prisma.product.update({ where: { id: i.productId }, data: { stock: { decrement: i.quantity } } })),
        prisma.cartItem.deleteMany({ where: { cartId: cart.id } }),
      ]);

      return order;
    }),

  updateStatus: adminProcedure
    .input(z.object({ id: z.string(), status: z.enum(['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED']) }))
    .mutation(({ input }) => prisma.order.update({ where: { id: input.id }, data: { status: input.status } })),

  allOrders: adminProcedure
    .input(z.object({ status: z.enum(['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED']).optional() }).optional())
    .query(({ input }) =>
      prisma.order.findMany({ where: input?.status ? { status: input.status } : {}, include: { user: { select: { name: true, email: true } }, items: { include: { product: true } } }, orderBy: { createdAt: 'desc' }, take: 100 })
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

_CART_STORE = """import { create } from 'zustand';
import { persist } from 'zustand/middleware';
interface CartState { count: number; setCount: (n: number) => void; }
export const useCartStore = create<CartState>()(persist((set) => ({ count: 0, setCount: (count) => set({ count }) }), { name: 'cart-store' }));"""

_LAYOUT = """import type { Metadata } from 'next';
import { TRPCProvider } from '@/lib/provider';
import './globals.css';
export const metadata: Metadata = { title: '__NAME__', description: 'Tienda online' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-white text-slate-900">
        <TRPCProvider>{children}</TRPCProvider>
      </body>
    </html>
  );
}"""

_LANDING = """'use client';
import { trpc } from '@/lib/trpc';
import Link from 'next/link';

export default function HomePage() {
  const { data } = trpc.products.categories.useQuery();
  const { data: featured } = trpc.products.list.useQuery({ limit: 4 });

  return (
    <main>
      {/* Hero */}
      <section className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-20 text-white text-center">
        <h1 className="text-5xl font-bold mb-4">__NAME__</h1>
        <p className="text-xl opacity-90 mb-8">Los mejores productos al mejor precio</p>
        <Link href="/productos" className="rounded-full bg-white px-8 py-3 text-indigo-600 font-bold hover:bg-indigo-50 transition">
          Ver catálogo
        </Link>
      </section>

      {/* Categories */}
      {data && data.length > 0 && (
        <section className="mx-auto max-w-6xl px-6 py-12">
          <h2 className="mb-6 text-2xl font-bold text-slate-800">Categorías</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {data.map(c => (
              <Link key={c.id} href={`/productos?categoria=${c.slug}`}
                className="rounded-xl border bg-white p-4 text-center shadow-sm hover:shadow-md transition font-medium">
                {c.name}
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured products */}
      {featured && featured.items.length > 0 && (
        <section className="mx-auto max-w-6xl px-6 py-4 pb-16">
          <h2 className="mb-6 text-2xl font-bold text-slate-800">Destacados</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {featured.items.map(p => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

function ProductCard({ product }: { product: { id: string; name: string; price: unknown; comparePrice?: unknown; stock: number; category: { name: string } } }) {
  return (
    <div className="overflow-hidden rounded-xl border bg-white shadow-sm hover:shadow-md transition">
      <div className="h-40 bg-gradient-to-br from-indigo-50 to-purple-100 flex items-center justify-center text-4xl">🛍️</div>
      <div className="p-4">
        <p className="text-xs text-slate-400">{product.category.name}</p>
        <p className="font-semibold leading-tight mt-1">{product.name}</p>
        <div className="mt-3 flex items-end gap-2">
          <span className="font-bold text-indigo-700">{Number(product.price).toFixed(2)} €</span>
          {product.comparePrice && <span className="text-sm text-slate-400 line-through">{Number(product.comparePrice).toFixed(2)} €</span>}
        </div>
        {product.stock === 0 && <p className="mt-1 text-xs text-red-500">Sin stock</p>}
      </div>
    </div>
  );
}"""

_PRODUCTS_PAGE = """'use client';
import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

export default function ProductosPage() {
  const params = useSearchParams();
  const [search, setSearch] = useState('');
  const user = useAuthStore(s => s.user);
  const { data, isLoading } = trpc.products.list.useQuery({ search: search || undefined, categorySlug: params.get('categoria') ?? undefined });
  const addItem = trpc.cart.addItem.useMutation();
  const utils = trpc.useUtils();

  const handleAdd = (productId: string) => {
    if (!user) { alert('Inicia sesión para añadir al carrito'); return; }
    addItem.mutate({ productId }, { onSuccess: () => utils.cart.get.invalidate() });
  };

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold text-slate-800">Productos</h1>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar..."
          className="ml-auto w-64 rounded-lg border px-3 py-2 text-sm" />
      </div>
      {isLoading && <p className="text-slate-400">Cargando...</p>}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {data?.items.map(p => (
          <div key={p.id} className={`overflow-hidden rounded-xl border bg-white shadow-sm ${!p.isPublished ? 'opacity-60' : ''}`}>
            <div className="h-40 bg-gradient-to-br from-indigo-50 to-purple-100 flex items-center justify-center text-4xl">🛍️</div>
            <div className="p-4">
              <p className="text-xs text-slate-400">{p.category.name}</p>
              <p className="font-semibold">{p.name}</p>
              {p.description && <p className="mt-1 text-xs text-slate-500 line-clamp-2">{p.description}</p>}
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <span className="font-bold text-indigo-700">{Number(p.price).toFixed(2)} €</span>
                  {p.comparePrice && <span className="ml-1 text-xs text-slate-400 line-through">{Number(p.comparePrice).toFixed(2)} €</span>}
                </div>
                <button onClick={() => handleAdd(p.id)} disabled={p.stock === 0 || addItem.isPending}
                  className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs text-white hover:bg-indigo-700 disabled:opacity-50">
                  {p.stock === 0 ? 'Sin stock' : '+ Carrito'}
                </button>
              </div>
              <p className="mt-1 text-xs text-slate-400">Stock: {p.stock}</p>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}"""

_CART_PAGE = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';
import { useRouter } from 'next/navigation';

export default function CarritoPage() {
  const user = useAuthStore(s => s.user);
  const router = useRouter();
  const { data: cart, refetch } = trpc.cart.get.useQuery(undefined, { enabled: !!user });
  const updateQty = trpc.cart.updateQuantity.useMutation({ onSuccess: () => refetch() });
  const checkout  = trpc.orders.checkout.useMutation({ onSuccess: (order) => { refetch(); router.push(`/pedidos?nuevo=${order.id}`); } });

  if (!user) return (
    <main className="mx-auto max-w-lg px-6 py-16 text-center">
      <p className="text-slate-500">Inicia sesión para ver tu carrito.</p>
    </main>
  );

  const subtotal = cart?.items.reduce((acc, i) => acc + Number(i.product.price) * i.quantity, 0) ?? 0;
  const shipping = subtotal >= 50 ? 0 : 4.95;
  const total    = subtotal + shipping;

  return (
    <main className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold text-slate-800">Mi carrito</h1>
      {(!cart || cart.items.length === 0) && <p className="text-slate-400">El carrito está vacío.</p>}
      <div className="space-y-3">
        {cart?.items.map(item => (
          <div key={item.id} className="flex items-center gap-4 rounded-xl border bg-white p-4 shadow-sm">
            <div className="h-12 w-12 rounded-lg bg-indigo-50 flex items-center justify-center text-xl shrink-0">🛍️</div>
            <div className="flex-1">
              <p className="font-semibold">{item.product.name}</p>
              <p className="text-sm text-indigo-700">{Number(item.product.price).toFixed(2)} € / ud</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => updateQty.mutate({ productId: item.productId, quantity: item.quantity - 1 })}
                className="h-7 w-7 rounded-full border text-center leading-none hover:bg-slate-50">−</button>
              <span className="w-6 text-center text-sm">{item.quantity}</span>
              <button onClick={() => updateQty.mutate({ productId: item.productId, quantity: item.quantity + 1 })}
                className="h-7 w-7 rounded-full border text-center leading-none hover:bg-slate-50">+</button>
            </div>
            <span className="w-20 text-right font-semibold">{(Number(item.product.price) * item.quantity).toFixed(2)} €</span>
          </div>
        ))}
      </div>

      {cart && cart.items.length > 0 && (
        <div className="mt-6 rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex justify-between text-sm"><span>Subtotal</span><span>{subtotal.toFixed(2)} €</span></div>
          <div className="flex justify-between text-sm mt-1"><span>Envío</span><span>{shipping === 0 ? 'Gratis' : `${shipping.toFixed(2)} €`}</span></div>
          {shipping === 0 && <p className="text-xs text-green-600 mt-1">¡Envío gratis por compras superiores a 50 €!</p>}
          <div className="mt-3 flex justify-between border-t pt-3 text-lg font-bold"><span>Total</span><span>{total.toFixed(2)} €</span></div>
          <button onClick={() => checkout.mutate({})} disabled={checkout.isPending}
            className="mt-4 w-full rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
            {checkout.isPending ? 'Procesando...' : 'Finalizar compra'}
          </button>
        </div>
      )}
    </main>
  );
}"""

_ORDERS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700', CONFIRMED: 'bg-blue-100 text-blue-700',
  PROCESSING: 'bg-purple-100 text-purple-700', SHIPPED: 'bg-indigo-100 text-indigo-700',
  DELIVERED: 'bg-green-100 text-green-700', CANCELLED: 'bg-red-100 text-red-700', REFUNDED: 'bg-stone-100 text-stone-600',
};
const STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pendiente', CONFIRMED: 'Confirmado', PROCESSING: 'En preparación',
  SHIPPED: 'Enviado', DELIVERED: 'Entregado', CANCELLED: 'Cancelado', REFUNDED: 'Reembolsado',
};

export default function PedidosPage() {
  const user = useAuthStore(s => s.user);
  const { data, isLoading } = trpc.orders.myOrders.useQuery(undefined, { enabled: !!user });

  if (!user) return <main className="mx-auto max-w-lg px-6 py-16 text-center"><p className="text-slate-500">Inicia sesión para ver tus pedidos.</p></main>;
  if (isLoading) return <p className="p-8 text-slate-400">Cargando...</p>;

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold text-slate-800">Mis pedidos</h1>
      {data?.length === 0 && <p className="text-slate-400">No tienes pedidos aún.</p>}
      <div className="space-y-4">
        {data?.map(order => (
          <div key={order.id} className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-mono text-xs text-slate-400">#{order.id.slice(-8).toUpperCase()}</p>
                <p className="text-xs text-slate-400">{new Date(order.createdAt).toLocaleDateString('es-ES', { dateStyle: 'medium' })}</p>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[order.status]}`}>{STATUS_LABELS[order.status]}</span>
            </div>
            <ul className="space-y-1 text-sm">
              {order.items.map(i => (
                <li key={i.id} className="flex justify-between">
                  <span>{i.quantity}× {i.product.name}</span>
                  <span className="text-slate-500">{Number(i.total).toFixed(2)} €</span>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex justify-between border-t pt-3 font-bold">
              <span>Total</span>
              <span className="text-indigo-700">{Number(order.total).toFixed(2)} €</span>
            </div>
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
      POSTGRES_USER: shop
      POSTGRES_PASSWORD: shop_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://shop:shop_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://shop:shop_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Tienda Online

Plataforma ecommerce completa con catálogo, carrito y gestión de pedidos.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS
- **Auth:** JWT con roles (ADMIN, CUSTOMER)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Productos | Catálogo público con búsqueda, filtros por categoría y stock |
| Carrito | Persistido en BD por usuario con stock en tiempo real |
| Checkout | Cálculo automático de envío (gratis ≥ 50 €), descuento de stock |
| Pedidos | Historial del cliente, gestión de estados por admin |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin: admin@tienda.com / password123
Cliente: cliente@email.com / password123
"""
