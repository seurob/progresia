"""
FINTECH template — sistema de gestión financiera personal/empresarial.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
Módulos: cuentas, transacciones, categorías, presupuestos, metas de ahorro.
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
        _f("apps/api/src/modules/accounts/account.router.ts", "typescript", _ACCOUNT_ROUTER),
        _f("apps/api/src/modules/transactions/transaction.router.ts", "typescript", _TRANSACTION_ROUTER),
        _f("apps/api/src/modules/budgets/budget.router.ts",   "typescript", _BUDGET_ROUTER),
        _f("apps/api/src/modules/goals/goal.router.ts",       "typescript", _GOAL_ROUTER),
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
        _f("apps/web/src/app/page.tsx",                       "typescript", _DASHBOARD),
        _f("apps/web/src/app/transacciones/page.tsx",         "typescript", _TRANSACTIONS_PAGE),
        _f("apps/web/src/app/presupuesto/page.tsx",           "typescript", _BUDGET_PAGE),
        _f("apps/web/src/app/metas/page.tsx",                 "typescript", _GOALS_PAGE),
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
console.log(`💰 __NAME__ API running on port ${port}`);"""

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
export const adminProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId || ctx.userRole !== 'ADMIN') throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});"""

_ROUTER = """import { router } from './trpc';
import { authRouter }        from './modules/auth/auth.router';
import { accountRouter }     from './modules/accounts/account.router';
import { transactionRouter } from './modules/transactions/transaction.router';
import { budgetRouter }      from './modules/budgets/budget.router';
import { goalRouter }        from './modules/goals/goal.router';

export const appRouter = router({
  auth:         authRouter,
  accounts:     accountRouter,
  transactions: transactionRouter,
  budgets:      budgetRouter,
  goals:        goalRouter,
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
  USER
}

enum AccountType {
  CHECKING
  SAVINGS
  INVESTMENT
  CREDIT
  CASH
}

enum TransactionType {
  INCOME
  EXPENSE
  TRANSFER
}

enum RecurrenceInterval {
  DAILY
  WEEKLY
  MONTHLY
  YEARLY
}

model User {
  id           String    @id @default(cuid())
  email        String    @unique
  name         String
  passwordHash String
  role         UserRole  @default(USER)
  currency     String    @default("EUR")
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  accounts     Account[]
  categories   Category[]
  budgets      Budget[]
  goals        Goal[]
}

model Account {
  id           String      @id @default(cuid())
  userId       String
  user         User        @relation(fields: [userId], references: [id], onDelete: Cascade)
  name         String
  type         AccountType
  balance      Decimal     @db.Decimal(14, 2) @default(0)
  currency     String      @default("EUR")
  color        String?
  icon         String?
  isActive     Boolean     @default(true)
  createdAt    DateTime    @default(now())
  updatedAt    DateTime    @updatedAt
  transactions Transaction[]
  fromTransfers Transaction[] @relation("TransferFrom")
  toTransfers   Transaction[] @relation("TransferTo")
}

model Category {
  id           String          @id @default(cuid())
  userId       String
  user         User            @relation(fields: [userId], references: [id], onDelete: Cascade)
  name         String
  icon         String?
  color        String?
  type         TransactionType @default(EXPENSE)
  createdAt    DateTime        @default(now())
  transactions Transaction[]
  budgets      Budget[]
}

model Transaction {
  id                 String             @id @default(cuid())
  accountId          String
  account            Account            @relation(fields: [accountId], references: [id], onDelete: Cascade)
  categoryId         String?
  category           Category?          @relation(fields: [categoryId], references: [id])
  transferToAccountId String?
  transferToAccount   Account?          @relation("TransferFrom", fields: [transferToAccountId], references: [id])
  transferFromAccountId String?
  transferFromAccount   Account?        @relation("TransferTo", fields: [transferFromAccountId], references: [id])
  type               TransactionType
  amount             Decimal            @db.Decimal(14, 2)
  description        String
  notes              String?
  date               DateTime
  recurrence         RecurrenceInterval?
  createdAt          DateTime           @default(now())
  updatedAt          DateTime           @updatedAt
}

model Budget {
  id         String   @id @default(cuid())
  userId     String
  user       User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  categoryId String
  category   Category @relation(fields: [categoryId], references: [id])
  amount     Decimal  @db.Decimal(14, 2)
  month      Int
  year       Int
  createdAt  DateTime @default(now())

  @@unique([userId, categoryId, month, year])
}

model Goal {
  id          String   @id @default(cuid())
  userId      String
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  name        String
  targetAmount Decimal @db.Decimal(14, 2)
  currentAmount Decimal @db.Decimal(14, 2) @default(0)
  deadline    DateTime?
  icon        String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}"""

_SEED = """import { PrismaClient, AccountType, TransactionType, UserRole } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding __NAME__ Fintech...');

  const hash = await bcrypt.hash('password123', 10);

  const admin = await prisma.user.upsert({
    where: { email: 'admin@finapp.com' },
    update: {},
    create: { email: 'admin@finapp.com', name: 'Admin', passwordHash: hash, role: UserRole.ADMIN },
  });

  const user = await prisma.user.upsert({
    where: { email: 'ana@finapp.com' },
    update: {},
    create: { email: 'ana@finapp.com', name: 'Ana García', passwordHash: hash, role: UserRole.USER },
  });

  // Accounts
  const checking = await prisma.account.create({
    data: { userId: user.id, name: 'Cuenta corriente', type: AccountType.CHECKING, balance: 2450.00, color: '#6366f1' },
  });
  const savings = await prisma.account.create({
    data: { userId: user.id, name: 'Ahorro vacaciones', type: AccountType.SAVINGS, balance: 800.00, color: '#10b981' },
  });

  // Categories
  const catFood = await prisma.category.create({
    data: { userId: user.id, name: 'Alimentación', icon: '🛒', color: '#f59e0b', type: TransactionType.EXPENSE },
  });
  const catSalary = await prisma.category.create({
    data: { userId: user.id, name: 'Salario', icon: '💼', color: '#10b981', type: TransactionType.INCOME },
  });
  const catLeisure = await prisma.category.create({
    data: { userId: user.id, name: 'Ocio', icon: '🎬', color: '#ec4899', type: TransactionType.EXPENSE },
  });
  const catTransport = await prisma.category.create({
    data: { userId: user.id, name: 'Transporte', icon: '🚇', color: '#8b5cf6', type: TransactionType.EXPENSE },
  });

  // Transactions
  const now = new Date();
  await prisma.transaction.createMany({
    data: [
      { accountId: checking.id, categoryId: catSalary.id, type: TransactionType.INCOME, amount: 2200.00, description: 'Nómina junio', date: new Date(now.getFullYear(), now.getMonth(), 1) },
      { accountId: checking.id, categoryId: catFood.id, type: TransactionType.EXPENSE, amount: 85.40, description: 'Supermercado Mercadona', date: new Date(now.getFullYear(), now.getMonth(), 5) },
      { accountId: checking.id, categoryId: catTransport.id, type: TransactionType.EXPENSE, amount: 54.00, description: 'Abono transporte mensual', date: new Date(now.getFullYear(), now.getMonth(), 3), recurrence: 'MONTHLY' },
      { accountId: checking.id, categoryId: catLeisure.id, type: TransactionType.EXPENSE, amount: 12.99, description: 'Netflix', date: new Date(now.getFullYear(), now.getMonth(), 8), recurrence: 'MONTHLY' },
      { accountId: checking.id, categoryId: catFood.id, type: TransactionType.EXPENSE, amount: 42.30, description: 'Restaurante con amigos', date: new Date(now.getFullYear(), now.getMonth(), 10) },
    ],
  });

  // Budget
  await prisma.budget.create({
    data: { userId: user.id, categoryId: catFood.id, amount: 350.00, month: now.getMonth() + 1, year: now.getFullYear() },
  });

  // Goal
  await prisma.goal.create({
    data: { userId: user.id, name: 'Vacaciones en Japón', targetAmount: 3000.00, currentAmount: 800.00, deadline: new Date(now.getFullYear() + 1, 5, 1), icon: '✈️' },
  });

  console.log('✅ Seed completado.');
  console.log('   Admin: admin@finapp.com / password123');
  console.log('   Usuario: ana@finapp.com / password123');
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
      if (existing) throw new Error('Email ya registrado');
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
    prisma.user.findUnique({ where: { id: ctx.userId }, select: { id: true, name: true, email: true, role: true, currency: true } })
  ),
});"""

_ACCOUNT_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const accountRouter = router({
  list: protectedProcedure.query(({ ctx }) =>
    prisma.account.findMany({
      where: { userId: ctx.userId, isActive: true },
      include: { _count: { select: { transactions: true } } },
      orderBy: { createdAt: 'asc' },
    })
  ),

  summary: protectedProcedure.query(async ({ ctx }) => {
    const accounts = await prisma.account.findMany({ where: { userId: ctx.userId, isActive: true } });
    const totalBalance  = accounts.reduce((s, a) => s + Number(a.balance), 0);
    const checkingTotal = accounts.filter(a => a.type === 'CHECKING').reduce((s, a) => s + Number(a.balance), 0);
    const savingsTotal  = accounts.filter(a => a.type === 'SAVINGS').reduce((s, a) => s + Number(a.balance), 0);
    return { totalBalance, checkingTotal, savingsTotal, accounts };
  }),

  create: protectedProcedure
    .input(z.object({
      name:     z.string().min(2),
      type:     z.enum(['CHECKING', 'SAVINGS', 'INVESTMENT', 'CREDIT', 'CASH']),
      balance:  z.number().default(0),
      currency: z.string().length(3).default('EUR'),
      color:    z.string().optional(),
      icon:     z.string().optional(),
    }))
    .mutation(({ input, ctx }) => prisma.account.create({ data: { ...input, userId: ctx.userId } })),

  update: protectedProcedure
    .input(z.object({ id: z.string(), name: z.string().min(2).optional(), color: z.string().optional(), isActive: z.boolean().optional() }))
    .mutation(({ input: { id, ...data } }) => prisma.account.update({ where: { id }, data })),
});"""

_TRANSACTION_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

const txInput = z.object({
  accountId:   z.string(),
  categoryId:  z.string().optional(),
  type:        z.enum(['INCOME', 'EXPENSE', 'TRANSFER']),
  amount:      z.number().positive(),
  description: z.string().min(1),
  notes:       z.string().optional(),
  date:        z.string(),
  transferToAccountId: z.string().optional(),
});

export const transactionRouter = router({
  list: protectedProcedure
    .input(z.object({
      accountId: z.string().optional(),
      type:      z.enum(['INCOME', 'EXPENSE', 'TRANSFER']).optional(),
      month:     z.number().int().min(1).max(12).optional(),
      year:      z.number().int().optional(),
      limit:     z.number().int().min(1).max(100).default(50),
    }).optional())
    .query(async ({ ctx, input }) => {
      const where: Record<string, unknown> = { account: { userId: ctx.userId } };
      if (input?.accountId) where['accountId'] = input.accountId;
      if (input?.type)      where['type']      = input.type;
      if (input?.month || input?.year) {
        const year  = input.year  ?? new Date().getFullYear();
        const month = input.month ?? new Date().getMonth() + 1;
        where['date'] = { gte: new Date(year, month - 1, 1), lt: new Date(year, month, 1) };
      }
      return prisma.transaction.findMany({
        where,
        include: { category: true, account: { select: { name: true, currency: true } } },
        orderBy: { date: 'desc' },
        take: input?.limit ?? 50,
      });
    }),

  monthSummary: protectedProcedure
    .input(z.object({ month: z.number().int().min(1).max(12), year: z.number().int() }))
    .query(async ({ ctx, input }) => {
      const start = new Date(input.year, input.month - 1, 1);
      const end   = new Date(input.year, input.month, 1);
      const txs   = await prisma.transaction.findMany({
        where: { account: { userId: ctx.userId }, date: { gte: start, lt: end }, type: { in: ['INCOME', 'EXPENSE'] } },
        include: { category: true },
      });
      const income  = txs.filter(t => t.type === 'INCOME').reduce((s, t) => s + Number(t.amount), 0);
      const expense = txs.filter(t => t.type === 'EXPENSE').reduce((s, t) => s + Number(t.amount), 0);
      const byCategory = Object.entries(
        txs.filter(t => t.type === 'EXPENSE').reduce((acc: Record<string, number>, t) => {
          const k = t.category?.name ?? 'Sin categoría';
          acc[k] = (acc[k] ?? 0) + Number(t.amount);
          return acc;
        }, {})
      ).map(([name, total]) => ({ name, total })).sort((a, b) => b.total - a.total);
      return { income, expense, balance: income - expense, byCategory };
    }),

  create: protectedProcedure
    .input(txInput)
    .mutation(async ({ input, ctx }) => {
      const { date, amount, transferToAccountId, ...rest } = input;
      const tx = await prisma.transaction.create({
        data: { ...rest, amount, date: new Date(date), userId: ctx.userId, transferToAccountId } as any,
      });
      // Update account balance
      const delta = input.type === 'INCOME' ? amount : -amount;
      await prisma.account.update({ where: { id: input.accountId }, data: { balance: { increment: delta } } });
      if (input.type === 'TRANSFER' && transferToAccountId) {
        await prisma.account.update({ where: { id: transferToAccountId }, data: { balance: { increment: amount } } });
      }
      return tx;
    }),

  delete: protectedProcedure
    .input(z.string())
    .mutation(async ({ input }) => {
      const tx = await prisma.transaction.findUniqueOrThrow({ where: { id: input } });
      const delta = tx.type === 'INCOME' ? -Number(tx.amount) : Number(tx.amount);
      await prisma.account.update({ where: { id: tx.accountId }, data: { balance: { increment: delta } } });
      return prisma.transaction.delete({ where: { id: input } });
    }),
});"""

_BUDGET_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const budgetRouter = router({
  list: protectedProcedure
    .input(z.object({ month: z.number().int().min(1).max(12), year: z.number().int() }))
    .query(async ({ ctx, input }) => {
      const budgets = await prisma.budget.findMany({
        where: { userId: ctx.userId, month: input.month, year: input.year },
        include: { category: true },
      });
      const start = new Date(input.year, input.month - 1, 1);
      const end   = new Date(input.year, input.month, 1);
      const txs   = await prisma.transaction.findMany({
        where: { account: { userId: ctx.userId }, type: 'EXPENSE', date: { gte: start, lt: end }, categoryId: { in: budgets.map(b => b.categoryId) } },
      });
      return budgets.map(b => ({
        ...b,
        spent: txs.filter(t => t.categoryId === b.categoryId).reduce((s, t) => s + Number(t.amount), 0),
      }));
    }),

  upsert: protectedProcedure
    .input(z.object({ categoryId: z.string(), amount: z.number().positive(), month: z.number().int().min(1).max(12), year: z.number().int() }))
    .mutation(({ input, ctx }) =>
      prisma.budget.upsert({
        where: { userId_categoryId_month_year: { userId: ctx.userId, categoryId: input.categoryId, month: input.month, year: input.year } },
        update: { amount: input.amount },
        create: { ...input, userId: ctx.userId },
      })
    ),
});"""

_GOAL_ROUTER = """import { z } from 'zod';
import { router, protectedProcedure } from '../../trpc';
import { prisma } from '../../trpc';

export const goalRouter = router({
  list: protectedProcedure.query(({ ctx }) =>
    prisma.goal.findMany({ where: { userId: ctx.userId }, orderBy: { createdAt: 'asc' } })
  ),

  create: protectedProcedure
    .input(z.object({
      name:         z.string().min(2),
      targetAmount: z.number().positive(),
      deadline:     z.string().optional(),
      icon:         z.string().optional(),
    }))
    .mutation(({ input, ctx }) =>
      prisma.goal.create({ data: { ...input, userId: ctx.userId, deadline: input.deadline ? new Date(input.deadline) : undefined } })
    ),

  addFunds: protectedProcedure
    .input(z.object({ id: z.string(), amount: z.number().positive() }))
    .mutation(({ input }) =>
      prisma.goal.update({ where: { id: input.id }, data: { currentAmount: { increment: input.amount } } })
    ),

  delete: protectedProcedure
    .input(z.string())
    .mutation(({ input }) => prisma.goal.delete({ where: { id: input } })),
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
export const metadata: Metadata = { title: '__NAME__', description: 'Finanzas personales' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        <TRPCProvider>{children}</TRPCProvider>
      </body>
    </html>
  );
}"""

_DASHBOARD = """'use client';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';
import Link from 'next/link';

const ACCOUNT_TYPE_LABELS: Record<string, string> = { CHECKING: 'Corriente', SAVINGS: 'Ahorro', INVESTMENT: 'Inversión', CREDIT: 'Crédito', CASH: 'Efectivo' };
const ACCOUNT_TYPE_ICONS: Record<string, string>  = { CHECKING: '🏦', SAVINGS: '💰', INVESTMENT: '📈', CREDIT: '💳', CASH: '💵' };

export default function DashboardPage() {
  const user = useAuthStore(s => s.user);
  const now  = new Date();
  const { data: summary } = trpc.accounts.summary.useQuery(undefined, { enabled: !!user });
  const { data: monthData } = trpc.transactions.monthSummary.useQuery({ month: now.getMonth() + 1, year: now.getFullYear() }, { enabled: !!user });
  const { data: recent }   = trpc.transactions.list.useQuery({ limit: 5 }, { enabled: !!user });

  if (!user) return (
    <main className="flex min-h-screen items-center justify-center gap-4 flex-col">
      <h1 className="text-3xl font-bold">💰 __NAME__</h1>
      <Link href="/login" className="rounded-xl bg-emerald-500 px-8 py-3 font-semibold text-white hover:bg-emerald-600">Acceder</Link>
    </main>
  );

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">💰 __NAME__</h1>
        <nav className="flex gap-2 text-sm">
          <Link href="/transacciones" className="rounded-lg bg-slate-800 px-3 py-1.5 hover:bg-slate-700">Transacciones</Link>
          <Link href="/presupuesto"   className="rounded-lg bg-slate-800 px-3 py-1.5 hover:bg-slate-700">Presupuesto</Link>
          <Link href="/metas"         className="rounded-lg bg-slate-800 px-3 py-1.5 hover:bg-slate-700">Metas</Link>
        </nav>
      </div>

      {/* Net worth */}
      <div className="mb-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 p-6">
        <p className="text-sm text-emerald-100">Balance total</p>
        <p className="text-4xl font-bold">{summary?.totalBalance.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
      </div>

      {/* Accounts */}
      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {summary?.accounts.map(a => (
          <div key={a.id} className="rounded-xl bg-slate-800 p-4" style={{ borderLeft: `3px solid ${a.color ?? '#6366f1'}` }}>
            <p className="text-xs text-slate-400">{ACCOUNT_TYPE_ICONS[a.type]} {ACCOUNT_TYPE_LABELS[a.type]}</p>
            <p className="font-medium truncate">{a.name}</p>
            <p className="text-lg font-bold text-emerald-400">{Number(a.balance).toLocaleString('es-ES', { style: 'currency', currency: a.currency })}</p>
          </div>
        ))}
      </div>

      {/* Month summary */}
      {monthData && (
        <div className="mb-4 grid grid-cols-3 gap-3">
          <div className="rounded-xl bg-slate-800 p-4"><p className="text-xs text-slate-400">Ingresos</p><p className="text-lg font-bold text-emerald-400">+{monthData.income.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</p></div>
          <div className="rounded-xl bg-slate-800 p-4"><p className="text-xs text-slate-400">Gastos</p><p className="text-lg font-bold text-red-400">-{monthData.expense.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</p></div>
          <div className="rounded-xl bg-slate-800 p-4"><p className="text-xs text-slate-400">Saldo mes</p><p className={`text-lg font-bold ${monthData.balance >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{monthData.balance >= 0 ? '+' : ''}{monthData.balance.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</p></div>
        </div>
      )}

      {/* Recent transactions */}
      <div className="rounded-xl bg-slate-800 p-4">
        <p className="mb-3 font-semibold text-slate-300">Últimas transacciones</p>
        <div className="space-y-2">
          {recent?.map(tx => (
            <div key={tx.id} className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">{tx.description}</p>
                <p className="text-xs text-slate-400">{tx.category?.name ?? 'Sin categoría'} · {new Date(tx.date).toLocaleDateString('es-ES')}</p>
              </div>
              <span className={`font-bold ${tx.type === 'INCOME' ? 'text-emerald-400' : 'text-red-400'}`}>
                {tx.type === 'INCOME' ? '+' : '-'}{Number(tx.amount).toFixed(2)} €
              </span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}"""

_TRANSACTIONS_PAGE = """'use client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

const TYPE_COLORS: Record<string, string>  = { INCOME: 'text-emerald-400', EXPENSE: 'text-red-400', TRANSFER: 'text-blue-400' };
const TYPE_SIGNS: Record<string, string>   = { INCOME: '+', EXPENSE: '-', TRANSFER: '⇄' };

export default function TransaccionesPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year]            = useState(now.getFullYear());
  const { data, refetch } = trpc.transactions.list.useQuery({ month, year, limit: 100 });
  const del = trpc.transactions.delete.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Transacciones</h1>
        <select value={month} onChange={e => setMonth(Number(e.target.value))}
          className="ml-auto rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm">
          {Array.from({ length: 12 }, (_, i) => (
            <option key={i} value={i + 1}>
              {new Date(year, i, 1).toLocaleDateString('es-ES', { month: 'long' })} {year}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-2">
        {data?.map(tx => (
          <div key={tx.id} className="flex items-center justify-between rounded-xl bg-slate-800 p-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{tx.category?.icon ?? '💸'}</span>
              <div>
                <p className="font-medium">{tx.description}</p>
                <p className="text-xs text-slate-400">{tx.category?.name ?? 'Sin categoría'} · {tx.account.name} · {new Date(tx.date).toLocaleDateString('es-ES')}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`font-bold ${TYPE_COLORS[tx.type]}`}>
                {TYPE_SIGNS[tx.type]}{Number(tx.amount).toFixed(2)} {tx.account.currency}
              </span>
              <button onClick={() => del.mutate(tx.id)} className="text-slate-500 hover:text-red-400 text-xs">✕</button>
            </div>
          </div>
        ))}
        {data?.length === 0 && <p className="text-slate-400">Sin transacciones este mes.</p>}
      </div>
    </main>
  );
}"""

_BUDGET_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

export default function PresupuestoPage() {
  const now  = new Date();
  const { data } = trpc.budgets.list.useQuery({ month: now.getMonth() + 1, year: now.getFullYear() });

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Presupuesto mensual</h1>
      <div className="space-y-4">
        {data?.map(b => {
          const pct = Math.min((b.spent / Number(b.amount)) * 100, 100);
          const over = b.spent > Number(b.amount);
          return (
            <div key={b.id} className="rounded-xl bg-slate-800 p-4">
              <div className="mb-2 flex items-center justify-between">
                <p className="font-medium">{b.category.icon} {b.category.name}</p>
                <p className={`text-sm font-bold ${over ? 'text-red-400' : 'text-slate-300'}`}>
                  {b.spent.toFixed(2)} / {Number(b.amount).toFixed(2)} €
                </p>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-700">
                <div className={`h-2 rounded-full transition-all ${over ? 'bg-red-500' : 'bg-emerald-500'}`} style={{ width: `${pct}%` }} />
              </div>
              <p className="mt-1 text-xs text-slate-400">{over ? `Excedido por ${(b.spent - Number(b.amount)).toFixed(2)} €` : `Queda ${(Number(b.amount) - b.spent).toFixed(2)} €`}</p>
            </div>
          );
        })}
        {data?.length === 0 && <p className="text-slate-400">Sin presupuestos configurados.</p>}
      </div>
    </main>
  );
}"""

_GOALS_PAGE = """'use client';
import { trpc } from '@/lib/trpc';

export default function MetasPage() {
  const { data, refetch } = trpc.goals.list.useQuery();
  const addFunds = trpc.goals.addFunds.useMutation({ onSuccess: () => refetch() });

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Metas de ahorro</h1>
      <div className="grid gap-4">
        {data?.map(g => {
          const pct = Math.min((Number(g.currentAmount) / Number(g.targetAmount)) * 100, 100);
          const remaining = Number(g.targetAmount) - Number(g.currentAmount);
          return (
            <div key={g.id} className="rounded-xl bg-slate-800 p-5">
              <div className="mb-3 flex items-center gap-3">
                <span className="text-3xl">{g.icon ?? '🎯'}</span>
                <div>
                  <p className="font-bold">{g.name}</p>
                  {g.deadline && <p className="text-xs text-slate-400">Meta: {new Date(g.deadline).toLocaleDateString('es-ES', { dateStyle: 'medium' })}</p>}
                </div>
                <div className="ml-auto text-right">
                  <p className="text-lg font-bold text-emerald-400">{Number(g.currentAmount).toFixed(2)} €</p>
                  <p className="text-xs text-slate-400">de {Number(g.targetAmount).toFixed(2)} €</p>
                </div>
              </div>
              <div className="h-3 w-full rounded-full bg-slate-700">
                <div className="h-3 rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all" style={{ width: `${pct}%` }} />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <p className="text-xs text-slate-400">{pct.toFixed(0)}% · faltan {remaining.toFixed(2)} €</p>
                <button onClick={() => { const n = prompt('¿Cuánto quieres añadir?'); if (n && !isNaN(+n)) addFunds.mutate({ id: g.id, amount: +n }); }}
                  className="rounded-lg bg-emerald-600 px-3 py-1 text-xs text-white hover:bg-emerald-700">
                  + Añadir
                </button>
              </div>
            </div>
          );
        })}
        {data?.length === 0 && <p className="text-slate-400">Sin metas de ahorro configuradas.</p>}
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
      POSTGRES_USER: fintech
      POSTGRES_PASSWORD: fintech_pass
      POSTGRES_DB: __SLUG___db
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  api:
    build: ./apps/api
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://fintech:fintech_pass@postgres:5432/__SLUG___db
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

_ENV = """DATABASE_URL="postgresql://fintech:fintech_pass@localhost:5432/__SLUG___db"
JWT_SECRET="change-me-in-production-use-a-long-random-string"
PORT=4000
CORS_ORIGIN="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:4000/trpc"
"""

_README = """# __NAME__ — Finanzas Personales

Plataforma de gestión financiera personal: cuentas, transacciones, presupuestos y metas.

## Stack
- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS (dark theme)
- **Auth:** JWT con roles (ADMIN, USER)

## Módulos
| Módulo | Funcionalidad |
|--------|---------------|
| Cuentas | Corriente, ahorro, inversión, crédito y efectivo con saldo actualizado automáticamente |
| Transacciones | Ingresos, gastos y transferencias con categorías y resumen mensual |
| Presupuesto | Límites por categoría con barra de progreso y alertas de exceso |
| Metas | Objetivos de ahorro con progreso visual y aportaciones manuales |

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d postgres
npx prisma migrate dev && npx prisma db seed
docker compose up --build
```
Admin: admin@finapp.com / password123
Usuario: ana@finapp.com / password123
"""
