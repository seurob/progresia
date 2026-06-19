"""
Academia online template — plataforma de cursos profesional.
Stack: tRPC v11 · Fastify · Prisma · Next.js 14 App Router · Tailwind CSS · JWT auth.
"""

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    files = [
        _f("apps/api/package.json",         "json",       _API_PKG.replace("__SLUG__", slug)),
        _f("apps/api/tsconfig.json",         "json",       _API_TSCONFIG),
        _f("apps/api/src/index.ts",          "typescript", _API_INDEX.replace("__NAME__", name).replace("__SLUG__", slug)),
        _f("apps/api/src/trpc.ts",           "typescript", _TRPC),
        _f("apps/api/src/router.ts",         "typescript", _ROUTER),
        _f("apps/api/src/lib/auth.ts",       "typescript", _LIB_AUTH),
        _f("apps/api/prisma/schema.prisma",  "prisma",     _PRISMA_SCHEMA),
        _f("apps/api/prisma/seed.ts",        "typescript", _SEED.replace("__NAME__", name)),
        _f("apps/api/src/modules/auth/auth.router.ts",               "typescript", _AUTH_ROUTER),
        _f("apps/api/src/modules/courses/course.router.ts",          "typescript", _COURSE_ROUTER),
        _f("apps/api/src/modules/enrollments/enrollment.router.ts",  "typescript", _ENROLLMENT_ROUTER),
        _f("apps/api/Dockerfile",            "dockerfile", _API_DOCKERFILE),
        _f("apps/web/package.json",          "json",       _WEB_PKG.replace("__SLUG__", slug)),
        _f("apps/web/tsconfig.json",         "json",       _WEB_TSCONFIG),
        _f("apps/web/tailwind.config.ts",    "typescript", _TAILWIND),
        _f("apps/web/next.config.js",        "javascript", _NEXT_CONFIG),
        _f("apps/web/postcss.config.js",     "javascript", _POSTCSS_CONFIG),
        _f("apps/web/src/app/globals.css",   "css",        _GLOBALS_CSS),
        _f("apps/web/src/lib/trpc.ts",       "typescript", _WEB_TRPC),
        _f("apps/web/src/lib/provider.tsx",  "typescript", _PROVIDER),
        _f("apps/web/src/lib/auth-store.ts", "typescript", _AUTH_STORE),
        _f("apps/web/src/components/Navbar.tsx",     "typescript", _NAVBAR.replace("__NAME__", name)),
        _f("apps/web/src/components/CourseCard.tsx", "typescript", _COURSE_CARD),
        _f("apps/web/src/components/ProgressBar.tsx","typescript", _PROGRESS_BAR),
        _f("apps/web/src/app/layout.tsx",            "typescript", _LAYOUT.replace("__NAME__", name)),
        _f("apps/web/src/app/page.tsx",              "typescript", _LANDING.replace("__NAME__", name)),
        _f("apps/web/src/app/cursos/page.tsx",       "typescript", _CATALOG),
        _f("apps/web/src/app/cursos/[slug]/page.tsx","typescript", _COURSE_DETAIL),
        _f("apps/web/src/app/mi-academia/page.tsx",  "typescript", _DASHBOARD),
        _f("apps/web/src/app/login/page.tsx",        "typescript", _LOGIN),
        _f("apps/web/src/app/registro/page.tsx",     "typescript", _REGISTER),
        _f("apps/web/Dockerfile",            "dockerfile", _WEB_DOCKERFILE),
        _f("nginx/nginx.conf",               "nginx",      _NGINX),
        _f("docker-compose.yml",             "yaml",       _DOCKER_COMPOSE.replace("__SLUG__", slug)),
        _f(".env.example",                   "env",        _ENV.replace("__SLUG__", slug)),
        _f("README.md",                      "markdown",   _README.replace("__NAME__", name).replace("__SLUG__", slug)),
    ]
    return CodeGenerationResponse(project_name=name, files=files)


def _slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _f(path: str, lang: str, content: str) -> GeneratedFile:
    return GeneratedFile(path=path, language=lang, content=content)


# ── Backend ────────────────────────────────────────────────────────────────────

_API_PKG = """\
{
  "name": "@__SLUG__/api",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc -p tsconfig.json",
    "start": "node dist/index.js",
    "db:migrate": "prisma migrate dev",
    "db:seed": "tsx prisma/seed.ts",
    "db:studio": "prisma studio"
  },
  "dependencies": {
    "@fastify/cors": "^9.0.1",
    "@prisma/client": "^5.22.0",
    "@trpc/server": "^11.0.0",
    "bcryptjs": "^2.4.3",
    "fastify": "^4.28.1",
    "jsonwebtoken": "^9.0.2",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/bcryptjs": "^2.4.6",
    "@types/jsonwebtoken": "^9.0.7",
    "@types/node": "^22.0.0",
    "prisma": "^5.22.0",
    "tsx": "^4.19.2",
    "typescript": "^5.7.2"
  }
}
"""

_API_TSCONFIG = """\
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src", "prisma"]
}
"""

_API_INDEX = """\
import { fastifyTRPCPlugin } from '@trpc/server/adapters/fastify';
import Fastify from 'fastify';
import cors from '@fastify/cors';
import { appRouter } from './router.js';
import { createContext } from './trpc.js';

const server = Fastify({ logger: { level: 'warn' } });

await server.register(cors, {
  origin: process.env.WEB_URL ?? 'http://localhost:3000',
  credentials: true,
});

await server.register(fastifyTRPCPlugin, {
  prefix: '/trpc',
  trpcOptions: { router: appRouter, createContext },
});

server.get('/health', async () => ({ status: 'ok', service: '__NAME__-api' }));

const port = Number(process.env.PORT ?? 4000);
await server.listen({ port, host: '0.0.0.0' });
console.log(`\\u{1F680}  __NAME__ API → http://0.0.0.0:${port}`);
"""

_TRPC = """\
import { initTRPC, TRPCError } from '@trpc/server';
import type { CreateFastifyContextOptions } from '@trpc/server/adapters/fastify';
import { PrismaClient } from '@prisma/client';
import { verifyToken } from './lib/auth.js';

export const prisma = new PrismaClient();

export async function createContext({ req }: CreateFastifyContextOptions) {
  const auth = req.headers.authorization;
  let userId: string | null = null;
  if (auth?.startsWith('Bearer ')) {
    try { userId = verifyToken(auth.slice(7)); } catch {}
  }
  return { prisma, userId };
}

export type Context = Awaited<ReturnType<typeof createContext>>;

const t = initTRPC.context<Context>().create();

export const router = t.router;
export const publicProcedure = t.procedure;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId) throw new TRPCError({ code: 'UNAUTHORIZED' });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});
"""

_ROUTER = """\
import { router } from './trpc.js';
import { authRouter } from './modules/auth/auth.router.js';
import { courseRouter } from './modules/courses/course.router.js';
import { enrollmentRouter } from './modules/enrollments/enrollment.router.js';

export const appRouter = router({
  auth: authRouter,
  course: courseRouter,
  enrollment: enrollmentRouter,
});

export type AppRouter = typeof appRouter;
"""

_LIB_AUTH = """\
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

const SECRET = process.env.JWT_SECRET ?? 'dev-secret-change-in-production';
const ROUNDS = 10;

export const hashPassword = (plain: string) => bcrypt.hash(plain, ROUNDS);
export const verifyPassword = (plain: string, hash: string) => bcrypt.compare(plain, hash);

export const signToken = (userId: string): string =>
  jwt.sign({ sub: userId }, SECRET, { expiresIn: '30d' });

export const verifyToken = (token: string): string => {
  const payload = jwt.verify(token, SECRET) as { sub: string };
  return payload.sub;
};
"""

_PRISMA_SCHEMA = """\
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum Role {
  STUDENT
  INSTRUCTOR
  ADMIN
}

model User {
  id           String       @id @default(uuid())
  email        String       @unique
  name         String
  passwordHash String
  role         Role         @default(STUDENT)
  bio          String?
  avatarUrl    String?
  courses      Course[]     @relation("InstructorCourses")
  enrollments  Enrollment[]
  createdAt    DateTime     @default(now())
  updatedAt    DateTime     @updatedAt
}

model Course {
  id           String       @id @default(uuid())
  slug         String       @unique
  title        String
  description  String
  shortDesc    String
  thumbnail    String?
  price        Float        @default(0)
  category     String
  level        String       @default("beginner")
  isPublished  Boolean      @default(false)
  instructor   User         @relation("InstructorCourses", fields: [instructorId], references: [id])
  instructorId String
  modules      Module[]
  enrollments  Enrollment[]
  createdAt    DateTime     @default(now())
  updatedAt    DateTime     @updatedAt
}

model Module {
  id       String   @id @default(uuid())
  title    String
  order    Int
  course   Course   @relation(fields: [courseId], references: [id], onDelete: Cascade)
  courseId String
  lessons  Lesson[]
}

model Lesson {
  id          String             @id @default(uuid())
  title       String
  content     String?
  videoUrl    String?
  durationMin Int                @default(5)
  order       Int
  isFree      Boolean            @default(false)
  module      Module             @relation(fields: [moduleId], references: [id], onDelete: Cascade)
  moduleId    String
  completions LessonCompletion[]
}

model Enrollment {
  id          String    @id @default(uuid())
  student     User      @relation(fields: [studentId], references: [id])
  studentId   String
  course      Course    @relation(fields: [courseId], references: [id])
  courseId    String
  amountPaid  Float     @default(0)
  completedAt DateTime?
  enrolledAt  DateTime  @default(now())

  @@unique([studentId, courseId])
}

model LessonCompletion {
  id          String   @id @default(uuid())
  lesson      Lesson   @relation(fields: [lessonId], references: [id])
  lessonId    String
  studentId   String
  completedAt DateTime @default(now())

  @@unique([lessonId, studentId])
}
"""

_SEED = """\
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  const hash = (p: string) => bcrypt.hash(p, 10);

  await prisma.user.create({
    data: { name: 'Admin', email: 'admin@academia.com', passwordHash: await hash('admin123'), role: 'ADMIN' },
  });

  const instructor = await prisma.user.create({
    data: {
      name: 'María González', email: 'instructor@academia.com',
      passwordHash: await hash('password123'), role: 'INSTRUCTOR',
      bio: 'Formadora con 15 años de experiencia. Especialista en marketing digital y comunicación.',
    },
  });

  const student = await prisma.user.create({
    data: { name: 'Carlos López', email: 'alumno@academia.com', passwordHash: await hash('password123') },
  });

  const course1 = await prisma.course.create({
    data: {
      slug: 'marketing-digital-fundamentos',
      title: 'Marketing Digital: Fundamentos',
      shortDesc: 'Todo lo que necesitas para empezar con el marketing digital desde cero.',
      description: 'Este curso te llevará desde los conceptos básicos hasta la creación de tu primera estrategia digital. Aprenderás SEO, redes sociales, email marketing y analítica web de forma práctica.',
      price: 0, category: 'Marketing', level: 'beginner', isPublished: true,
      instructorId: instructor.id,
      modules: {
        create: [
          {
            title: 'Introducción al Marketing Digital', order: 1,
            lessons: {
              create: [
                { title: '¿Qué es el marketing digital?', order: 1, durationMin: 10, isFree: true,
                  content: 'El marketing digital es el conjunto de estrategias y técnicas aplicadas en los canales digitales para promover productos o servicios.' },
                { title: 'Los 5 canales principales', order: 2, durationMin: 15, isFree: true,
                  content: 'SEO, SEM, Social Media, Email Marketing y Marketing de Contenidos son los pilares del marketing digital moderno.' },
                { title: 'Crea tu primera estrategia', order: 3, durationMin: 20,
                  content: 'Una estrategia digital efectiva empieza por definir tus objetivos SMART y conocer a tu buyer persona.' },
              ],
            },
          },
          {
            title: 'Redes Sociales para Negocios', order: 2,
            lessons: {
              create: [
                { title: 'Instagram Business: guía completa', order: 1, durationMin: 25,
                  content: 'Aprende a optimizar tu perfil, usar hashtags estratégicamente y crear contenido que convierte.' },
                { title: 'LinkedIn: marca personal y empresa', order: 2, durationMin: 20,
                  content: 'LinkedIn es la red profesional por excelencia. Aprende a construir autoridad en tu sector.' },
              ],
            },
          },
        ],
      },
    },
  });

  const course2 = await prisma.course.create({
    data: {
      slug: 'seo-avanzado-google',
      title: 'SEO Avanzado: De 0 a Experto',
      shortDesc: 'Posiciona tu web en la primera página de Google con técnicas probadas.',
      description: 'Domina el SEO técnico, on-page y off-page. Aprenderás investigación de palabras clave, optimización de contenido, link building y análisis con Google Search Console y Ahrefs.',
      price: 149, category: 'SEO', level: 'advanced', isPublished: true,
      instructorId: instructor.id,
      modules: {
        create: [
          {
            title: 'Fundamentos SEO', order: 1,
            lessons: {
              create: [
                { title: 'Cómo funciona Google en 2024', order: 1, durationMin: 15, isFree: true,
                  content: 'Entender el algoritmo de Google es fundamental para cualquier estrategia SEO.' },
                { title: 'Investigación de palabras clave con datos reales', order: 2, durationMin: 30,
                  content: 'Aprenderemos a usar Google Keyword Planner, Ahrefs y Semrush para encontrar keywords con alta intención y baja competencia.' },
                { title: 'Arquitectura web y SEO', order: 3, durationMin: 25,
                  content: 'La estructura de tu web es crítica para el rastreo e indexación. Aprenderemos sitemaps, robots.txt y estructura de URLs.' },
              ],
            },
          },
          {
            title: 'SEO Técnico', order: 2,
            lessons: {
              create: [
                { title: 'Core Web Vitals: velocidad que posiciona', order: 1, durationMin: 20,
                  content: 'Google mide LCP, FID y CLS para determinar la experiencia del usuario. Aprende a optimizarlos.' },
                { title: 'Schema markup y datos estructurados', order: 2, durationMin: 15,
                  content: 'Los rich snippets aumentan el CTR hasta un 30%. Implementaremos schema para artículos, productos y FAQ.' },
              ],
            },
          },
        ],
      },
    },
  });

  // Enroll student in free course
  await prisma.enrollment.create({
    data: { studentId: student.id, courseId: course1.id, amountPaid: 0 },
  });

  // Complete first lesson for demo progress
  const firstLesson = await prisma.lesson.findFirst({
    where: { module: { courseId: course1.id }, order: 1, module: { order: 1 } },
  });
  if (firstLesson) {
    await prisma.lessonCompletion.create({
      data: { lessonId: firstLesson.id, studentId: student.id },
    });
  }

  console.log('\\n✅ Seed completado para __NAME__');
  console.log('   Admin:      admin@academia.com      / admin123');
  console.log('   Instructor: instructor@academia.com / password123');
  console.log('   Alumno:     alumno@academia.com     / password123\\n');
}

main().catch(console.error).finally(() => prisma.$disconnect());
"""

_AUTH_ROUTER = """\
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, publicProcedure, protectedProcedure } from '../../trpc.js';
import { hashPassword, verifyPassword, signToken } from '../../lib/auth.js';

export const authRouter = router({
  register: publicProcedure
    .input(z.object({
      name: z.string().min(2, 'Nombre demasiado corto').max(100),
      email: z.string().email('Email no válido'),
      password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres'),
    }))
    .mutation(async ({ ctx, input }) => {
      const exists = await ctx.prisma.user.findUnique({ where: { email: input.email } });
      if (exists) throw new TRPCError({ code: 'CONFLICT', message: 'Este email ya está registrado' });

      const passwordHash = await hashPassword(input.password);
      const user = await ctx.prisma.user.create({
        data: { name: input.name, email: input.email, passwordHash },
        select: { id: true, name: true, email: true, role: true },
      });

      return { user, token: signToken(user.id) };
    }),

  login: publicProcedure
    .input(z.object({ email: z.string().email(), password: z.string() }))
    .mutation(async ({ ctx, input }) => {
      const user = await ctx.prisma.user.findUnique({ where: { email: input.email } });
      if (!user) throw new TRPCError({ code: 'NOT_FOUND', message: 'Usuario no encontrado' });

      const valid = await verifyPassword(input.password, user.passwordHash);
      if (!valid) throw new TRPCError({ code: 'UNAUTHORIZED', message: 'Contraseña incorrecta' });

      return {
        user: { id: user.id, name: user.name, email: user.email, role: user.role },
        token: signToken(user.id),
      };
    }),

  me: protectedProcedure.query(async ({ ctx }) => {
    return ctx.prisma.user.findUnique({
      where: { id: ctx.userId },
      select: { id: true, name: true, email: true, role: true, bio: true, avatarUrl: true },
    });
  }),
});
"""

_COURSE_ROUTER = """\
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, publicProcedure, protectedProcedure } from '../../trpc.js';

const courseSelect = {
  id: true, slug: true, title: true, shortDesc: true, thumbnail: true,
  price: true, category: true, level: true, isPublished: true,
  instructor: { select: { id: true, name: true, avatarUrl: true, bio: true } },
  _count: { select: { enrollments: true, modules: true } },
  createdAt: true,
} as const;

export const courseRouter = router({
  list: publicProcedure
    .input(z.object({
      category: z.string().optional(),
      search: z.string().optional(),
      limit: z.number().min(1).max(50).default(12),
    }).optional())
    .query(async ({ ctx, input }) => {
      return ctx.prisma.course.findMany({
        where: {
          isPublished: true,
          ...(input?.category ? { category: input.category } : {}),
          ...(input?.search ? { title: { contains: input.search, mode: 'insensitive' } } : {}),
        },
        select: courseSelect,
        orderBy: { createdAt: 'desc' },
        take: input?.limit ?? 12,
      });
    }),

  bySlug: publicProcedure
    .input(z.object({ slug: z.string() }))
    .query(async ({ ctx, input }) => {
      const course = await ctx.prisma.course.findUnique({
        where: { slug: input.slug },
        include: {
          instructor: { select: { id: true, name: true, bio: true, avatarUrl: true } },
          modules: {
            include: {
              lessons: {
                select: { id: true, title: true, durationMin: true, order: true, isFree: true },
                orderBy: { order: 'asc' },
              },
            },
            orderBy: { order: 'asc' },
          },
          _count: { select: { enrollments: true } },
        },
      });
      if (!course) throw new TRPCError({ code: 'NOT_FOUND', message: 'Curso no encontrado' });
      return course;
    }),

  categories: publicProcedure.query(async ({ ctx }) => {
    const rows = await ctx.prisma.course.groupBy({
      by: ['category'],
      where: { isPublished: true },
      _count: { category: true },
      orderBy: { _count: { category: 'desc' } },
    });
    return rows.map(r => ({ name: r.category, count: r._count.category }));
  }),

  create: protectedProcedure
    .input(z.object({
      title: z.string().min(5).max(200),
      shortDesc: z.string().max(300),
      description: z.string(),
      price: z.number().min(0).default(0),
      category: z.string(),
      level: z.enum(['beginner', 'intermediate', 'advanced']).default('beginner'),
    }))
    .mutation(async ({ ctx, input }) => {
      const slug = input.title
        .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
      return ctx.prisma.course.create({
        data: { ...input, slug, instructorId: ctx.userId },
        select: courseSelect,
      });
    }),

  publish: protectedProcedure
    .input(z.object({ courseId: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      const course = await ctx.prisma.course.findUnique({ where: { id: input.courseId } });
      if (!course) throw new TRPCError({ code: 'NOT_FOUND' });
      if (course.instructorId !== ctx.userId)
        throw new TRPCError({ code: 'FORBIDDEN', message: 'Solo el instructor puede publicar' });
      return ctx.prisma.course.update({
        where: { id: input.courseId },
        data: { isPublished: true },
        select: courseSelect,
      });
    }),
});
"""

_ENROLLMENT_ROUTER = """\
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, protectedProcedure } from '../../trpc.js';

export const enrollmentRouter = router({
  enroll: protectedProcedure
    .input(z.object({ courseId: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      const course = await ctx.prisma.course.findUnique({ where: { id: input.courseId } });
      if (!course || !course.isPublished) throw new TRPCError({ code: 'NOT_FOUND' });

      const existing = await ctx.prisma.enrollment.findUnique({
        where: { studentId_courseId: { studentId: ctx.userId, courseId: input.courseId } },
      });
      if (existing) throw new TRPCError({ code: 'CONFLICT', message: 'Ya estás matriculado en este curso' });

      return ctx.prisma.enrollment.create({
        data: { studentId: ctx.userId, courseId: input.courseId, amountPaid: course.price },
      });
    }),

  myEnrollments: protectedProcedure.query(async ({ ctx }) => {
    return ctx.prisma.enrollment.findMany({
      where: { studentId: ctx.userId },
      include: {
        course: {
          select: {
            id: true, slug: true, title: true, shortDesc: true, thumbnail: true,
            category: true, level: true,
            modules: { include: { lessons: { select: { id: true } } } },
          },
        },
      },
      orderBy: { enrolledAt: 'desc' },
    });
  }),

  progress: protectedProcedure
    .input(z.object({ courseId: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      const enrollment = await ctx.prisma.enrollment.findUnique({
        where: { studentId_courseId: { studentId: ctx.userId, courseId: input.courseId } },
      });
      if (!enrollment) throw new TRPCError({ code: 'NOT_FOUND', message: 'No estás matriculado' });

      const totalLessons = await ctx.prisma.lesson.count({
        where: { module: { courseId: input.courseId } },
      });
      const completed = await ctx.prisma.lessonCompletion.count({
        where: { studentId: ctx.userId, lesson: { module: { courseId: input.courseId } } },
      });

      return { totalLessons, completed, pct: totalLessons > 0 ? Math.round((completed / totalLessons) * 100) : 0 };
    }),

  completeLesson: protectedProcedure
    .input(z.object({ lessonId: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      const lesson = await ctx.prisma.lesson.findUnique({
        where: { id: input.lessonId }, include: { module: { select: { courseId: true } } },
      });
      if (!lesson) throw new TRPCError({ code: 'NOT_FOUND' });

      const enrolled = await ctx.prisma.enrollment.findUnique({
        where: { studentId_courseId: { studentId: ctx.userId, courseId: lesson.module.courseId } },
      });
      if (!enrolled) throw new TRPCError({ code: 'FORBIDDEN', message: 'Debes estar matriculado' });

      return ctx.prisma.lessonCompletion.upsert({
        where: { lessonId_studentId: { lessonId: input.lessonId, studentId: ctx.userId } },
        create: { lessonId: input.lessonId, studentId: ctx.userId },
        update: {},
      });
    }),
});
"""

_API_DOCKERFILE = """\
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/prisma ./prisma
EXPOSE 4000
CMD ["node", "dist/index.js"]
"""

# ── Frontend ────────────────────────────────────────────────────────────────────

_WEB_PKG = """\
{
  "name": "@__SLUG__/web",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.62.16",
    "@trpc/client": "^11.0.0",
    "@trpc/react-query": "^11.0.0",
    "@trpc/server": "^11.0.0",
    "next": "^14.2.21",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "zustand": "^5.0.2",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "^5.7.2"
  }
}
"""

_WEB_TSCONFIG = """\
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""

_TAILWIND = """\
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef2ff', 100: '#e0e7ff', 500: '#6366f1',
          600: '#4f46e5', 700: '#4338ca', 900: '#312e81',
        },
      },
    },
  },
  plugins: [],
};

export default config;
"""

_NEXT_CONFIG = """\
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: { domains: [] },
};

module.exports = nextConfig;
"""

_POSTCSS_CONFIG = """\
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""

_GLOBALS_CSS = """\
@tailwind base;
@tailwind components;
@tailwind utilities;

html {
  scroll-behavior: smooth;
}

body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
"""

_WEB_TRPC = """\
import { createTRPCReact } from '@trpc/react-query';
import type { AppRouter } from '../../../api/src/router';

export const trpc = createTRPCReact<AppRouter>();

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000/trpc';
"""

_PROVIDER = """\
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import { useState } from 'react';
import { trpc, API_URL } from './trpc';
import { useAuthStore } from './auth-store';

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { staleTime: 30_000 } } });
}

export function TRPCProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token);
  const [queryClient] = useState(makeQueryClient);
  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        httpBatchLink({
          url: API_URL,
          headers: () => (token ? { Authorization: `Bearer ${token}` } : {}),
        }),
      ],
    })
  );

  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </trpc.Provider>
  );
}
"""

_AUTH_STORE = """\
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthUser { id: string; name: string; email: string; role: string; }

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  setAuth: (user: AuthUser, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => set({ user, token }),
      clearAuth: () => set({ user: null, token: null }),
    }),
    { name: 'auth' }
  )
);
"""

_NAVBAR = """\
'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/auth-store';

export function Navbar() {
  const { user, clearAuth } = useAuthStore();

  return (
    <nav className="sticky top-0 z-50 border-b bg-white shadow-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-xl font-bold text-brand-600">
          __NAME__
        </Link>

        <div className="flex items-center gap-2">
          <Link href="/cursos" className="text-sm font-medium text-gray-600 hover:text-brand-600 px-3 py-1.5">
            Cursos
          </Link>

          {user ? (
            <>
              <Link href="/mi-academia"
                className="text-sm font-medium text-gray-600 hover:text-brand-600 px-3 py-1.5">
                Mi academia
              </Link>
              <span className="text-sm text-gray-500 px-2">{user.name}</span>
              <button onClick={clearAuth}
                className="text-sm text-gray-500 hover:text-red-600 px-3 py-1.5">
                Salir
              </button>
            </>
          ) : (
            <>
              <Link href="/login"
                className="text-sm font-medium text-gray-600 hover:text-brand-600 px-3 py-1.5">
                Iniciar sesión
              </Link>
              <Link href="/registro"
                className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 transition">
                Registrarse gratis
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
"""

_COURSE_CARD = """\
import Link from 'next/link';

interface Course {
  id: string; slug: string; title: string; shortDesc: string;
  thumbnail?: string | null; price: number; category: string; level: string;
  instructor: { name: string };
  _count: { enrollments: number };
}

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'Principiante', intermediate: 'Intermedio', advanced: 'Avanzado',
};

export function CourseCard({ course, progress }: {
  readonly course: Course;
  readonly progress?: number;
}) {
  return (
    <Link href={`/cursos/${course.slug}`}
      className="group flex flex-col overflow-hidden rounded-xl border bg-white shadow-sm hover:shadow-md transition-shadow">
      <div className="relative h-44 bg-gradient-to-br from-brand-100 to-brand-200 overflow-hidden">
        {course.thumbnail ? (
          <img src={course.thumbnail} alt={course.title}
            className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300" />
        ) : (
          <div className="flex h-full items-center justify-center text-5xl select-none">
            📚
          </div>
        )}
        <span className="absolute top-3 left-3 rounded-full bg-white/90 px-2.5 py-0.5 text-xs font-medium text-brand-700">
          {course.category}
        </span>
        {course.price === 0 && (
          <span className="absolute top-3 right-3 rounded-full bg-green-500 px-2.5 py-0.5 text-xs font-bold text-white">
            Gratis
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col p-4">
        <h3 className="font-semibold text-gray-900 line-clamp-2 group-hover:text-brand-600 transition-colors">
          {course.title}
        </h3>
        <p className="mt-1 text-xs text-gray-500 line-clamp-2">{course.shortDesc}</p>

        <div className="mt-auto pt-3 flex items-center justify-between border-t">
          <div>
            <p className="text-xs text-gray-500">{course.instructor.name}</p>
            <p className="text-xs text-gray-400">{LEVEL_LABEL[course.level] ?? course.level}</p>
          </div>
          <div className="text-right">
            {course.price === 0 ? (
              <span className="text-sm font-bold text-green-600">Gratuito</span>
            ) : (
              <span className="text-sm font-bold text-gray-900">{course.price}€</span>
            )}
          </div>
        </div>

        {typeof progress === 'number' && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Progreso</span><span>{progress}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-gray-100">
              <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
"""

_PROGRESS_BAR = """\
export function ProgressBar({ value, label }: { readonly value: number; readonly label?: string }) {
  return (
    <div>
      {label && (
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>{label}</span>
          <span className="font-medium">{value}%</span>
        </div>
      )}
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-brand-500 transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  );
}
"""

_LAYOUT = """\
import type { Metadata } from 'next';
import './globals.css';
import { TRPCProvider } from '@/lib/provider';
import { Navbar } from '@/components/Navbar';

export const metadata: Metadata = {
  title: '__NAME__ | Academia Online',
  description: 'Aprende de los mejores expertos con cursos online de calidad.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <TRPCProvider>
          <Navbar />
          {children}
          <footer className="mt-20 border-t bg-white py-8 text-center text-sm text-gray-400">
            © {new Date().getFullYear()} __NAME__. Todos los derechos reservados.
          </footer>
        </TRPCProvider>
      </body>
    </html>
  );
}
"""

_LANDING = """\
'use client';

import Link from 'next/link';
import { trpc } from '@/lib/trpc';
import { CourseCard } from '@/components/CourseCard';

const STATS = [
  { n: '1.200+', label: 'Alumnos activos' },
  { n: '48', label: 'Cursos disponibles' },
  { n: '4.8★', label: 'Valoración media' },
];

const CATEGORIES = [
  { icon: '📈', label: 'Marketing' },
  { icon: '🔍', label: 'SEO' },
  { icon: '🎨', label: 'Diseño' },
  { icon: '💻', label: 'Programación' },
  { icon: '💼', label: 'Negocios' },
  { icon: '📸', label: 'Fotografía' },
];

export default function HomePage() {
  const { data: courses, isLoading } = trpc.course.list.useQuery({ limit: 6 });

  return (
    <main>
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-900 via-brand-700 to-brand-600 py-24 px-4 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <p className="mb-4 text-brand-200 font-medium tracking-wide uppercase text-sm">
            Plataforma de formación profesional
          </p>
          <h1 className="mb-6 text-5xl font-extrabold leading-tight">
            Aprende lo que necesitas<br className="hidden sm:block" /> para avanzar en tu carrera
          </h1>
          <p className="mb-10 text-xl text-brand-100 max-w-2xl mx-auto">
            Más de 48 cursos online impartidos por expertos del sector. Aprende a tu ritmo, desde cualquier lugar.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href="/cursos"
              className="rounded-full bg-white px-8 py-3 font-semibold text-brand-700 hover:bg-brand-50 transition shadow-lg">
              Ver todos los cursos
            </Link>
            <Link href="/registro"
              className="rounded-full border-2 border-white px-8 py-3 font-semibold text-white hover:bg-white/10 transition">
              Empezar gratis
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-white border-b py-10">
        <div className="mx-auto max-w-4xl grid grid-cols-3 gap-4 px-4 text-center">
          {STATS.map(({ n, label }) => (
            <div key={label}>
              <div className="text-3xl font-bold text-brand-600">{n}</div>
              <div className="mt-1 text-sm text-gray-500">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Categories */}
      <section className="py-14 px-4">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-8 text-2xl font-bold text-gray-900">Explora por categoría</h2>
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
            {CATEGORIES.map(({ icon, label }) => (
              <Link key={label} href={`/cursos?category=${encodeURIComponent(label)}`}
                className="flex flex-col items-center gap-2 rounded-xl border bg-white p-4 hover:border-brand-300 hover:bg-brand-50 transition text-center">
                <span className="text-3xl">{icon}</span>
                <span className="text-xs font-medium text-gray-700">{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured courses */}
      <section className="bg-gray-50 py-14 px-4">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-end justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Cursos destacados</h2>
              <p className="text-gray-500 mt-1">Los más valorados por nuestra comunidad</p>
            </div>
            <Link href="/cursos" className="text-sm font-semibold text-brand-600 hover:underline">
              Ver todos →
            </Link>
          </div>

          {isLoading ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-72 rounded-xl bg-gray-200 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {courses?.map(course => <CourseCard key={course.id} course={course} />)}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">¿Listo para empezar?</h2>
        <p className="text-gray-500 mb-8 max-w-xl mx-auto">
          Únete a más de 1.200 profesionales que ya están aprendiendo en __NAME__.
          Tu primera clase es gratis.
        </p>
        <Link href="/registro"
          className="inline-block rounded-full bg-brand-600 px-10 py-3.5 font-semibold text-white hover:bg-brand-700 transition shadow-lg">
          Crear cuenta gratuita
        </Link>
      </section>
    </main>
  );
}
"""

_CATALOG = """\
'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { trpc } from '@/lib/trpc';
import { CourseCard } from '@/components/CourseCard';

export default function CoursesPage() {
  const params = useSearchParams();
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState(params.get('category') ?? '');

  const { data: courses, isLoading } = trpc.course.list.useQuery(
    { search: search || undefined, category: category || undefined, limit: 24 },
    { keepPreviousData: true }
  );
  const { data: categories } = trpc.course.categories.useQuery();

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Todos los cursos</h1>
      <p className="text-gray-500 mb-8">Elige el tema que quieres dominar</p>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-8">
        <input
          type="search"
          placeholder="Buscar cursos..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="rounded-full border px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white w-64"
        />
        <button
          onClick={() => setCategory('')}
          className={`rounded-full px-4 py-2 text-sm font-medium transition ${
            category === '' ? 'bg-brand-600 text-white' : 'bg-white border text-gray-600 hover:border-brand-400'
          }`}>
          Todos
        </button>
        {categories?.map(c => (
          <button
            key={c.name}
            onClick={() => setCategory(c.name)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              category === c.name ? 'bg-brand-600 text-white' : 'bg-white border text-gray-600 hover:border-brand-400'
            }`}>
            {c.name} ({c.count})
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-64 rounded-xl bg-gray-200 animate-pulse" />
          ))}
        </div>
      ) : courses?.length === 0 ? (
        <div className="py-20 text-center text-gray-400">
          <p className="text-5xl mb-4">🔍</p>
          <p className="text-lg">No se encontraron cursos</p>
          <button onClick={() => { setSearch(''); setCategory(''); }}
            className="mt-4 text-brand-600 hover:underline text-sm">
            Limpiar filtros
          </button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {courses?.map(course => <CourseCard key={course.id} course={course} />)}
        </div>
      )}
    </main>
  );
}
"""

_COURSE_DETAIL = """\
'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';
import { ProgressBar } from '@/components/ProgressBar';

const LEVEL: Record<string, string> = {
  beginner: 'Principiante', intermediate: 'Intermedio', advanced: 'Avanzado',
};

export default function CourseDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuthStore();
  const router = useRouter();
  const [openModule, setOpenModule] = useState<string | null>(null);

  const { data: course, isLoading } = trpc.course.bySlug.useQuery({ slug });
  const { data: progress } = trpc.enrollment.progress.useQuery(
    { courseId: course?.id ?? '' },
    { enabled: !!user && !!course?.id, retry: false }
  );

  const utils = trpc.useUtils();
  const enroll = trpc.enrollment.enroll.useMutation({
    onSuccess: () => utils.enrollment.progress.invalidate(),
  });

  if (isLoading) return <div className="py-32 text-center text-gray-400">Cargando...</div>;
  if (!course) return <div className="py-32 text-center text-gray-400">Curso no encontrado</div>;

  const totalLessons = course.modules.flatMap(m => m.lessons).length;
  const totalMin = course.modules.flatMap(m => m.lessons).reduce((a, l) => a + l.durationMin, 0);
  const isEnrolled = progress !== undefined && progress !== null;

  return (
    <main>
      {/* Hero */}
      <section className="bg-gradient-to-r from-gray-900 to-gray-800 text-white py-16 px-4">
        <div className="mx-auto max-w-5xl grid md:grid-cols-3 gap-8 items-start">
          <div className="md:col-span-2">
            <span className="text-sm text-brand-300 font-medium">{course.category} · {LEVEL[course.level]}</span>
            <h1 className="mt-2 text-3xl font-bold">{course.title}</h1>
            <p className="mt-3 text-gray-300">{course.shortDesc}</p>
            <p className="mt-4 text-sm text-gray-400">
              Por <strong className="text-white">{course.instructor.name}</strong> ·{' '}
              {course._count.enrollments} alumnos · {totalLessons} lecciones · {Math.round(totalMin / 60)}h {totalMin % 60}min
            </p>
          </div>

          <div className="rounded-xl bg-white text-gray-900 p-6 shadow-xl">
            {course.thumbnail ? (
              <img src={course.thumbnail} alt={course.title} className="rounded-lg w-full h-40 object-cover mb-4" />
            ) : (
              <div className="flex h-40 items-center justify-center rounded-lg bg-brand-50 mb-4 text-5xl">📚</div>
            )}
            <div className="text-3xl font-bold mb-4">
              {course.price === 0 ? <span className="text-green-600">Gratuito</span> : `${course.price}€`}
            </div>

            {isEnrolled ? (
              <>
                <ProgressBar value={progress!.pct} label="Tu progreso" />
                <button
                  onClick={() => router.push(`/mi-academia`)}
                  className="mt-4 w-full rounded-full bg-brand-600 py-3 font-semibold text-white hover:bg-brand-700 transition">
                  Continuar aprendiendo
                </button>
              </>
            ) : (
              <button
                onClick={() => {
                  if (!user) { router.push('/login'); return; }
                  enroll.mutate({ courseId: course.id });
                }}
                disabled={enroll.isPending}
                className="w-full rounded-full bg-brand-600 py-3 font-semibold text-white hover:bg-brand-700 transition disabled:opacity-60">
                {enroll.isPending ? 'Procesando...' : course.price === 0 ? 'Matricularse gratis' : `Comprar por ${course.price}€`}
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="mx-auto max-w-5xl px-4 py-12 grid md:grid-cols-3 gap-10">
        <div className="md:col-span-2">
          <h2 className="text-xl font-bold mb-2">Descripción</h2>
          <p className="text-gray-600 leading-relaxed">{course.description}</p>

          <h2 className="text-xl font-bold mt-10 mb-4">Contenido del curso</h2>
          <p className="text-sm text-gray-500 mb-4">
            {course.modules.length} módulos · {totalLessons} lecciones · {Math.round(totalMin / 60)}h en total
          </p>

          <div className="space-y-2">
            {course.modules.map(mod => (
              <div key={mod.id} className="rounded-xl border overflow-hidden">
                <button
                  onClick={() => setOpenModule(openModule === mod.id ? null : mod.id)}
                  className="flex w-full items-center justify-between bg-gray-50 px-5 py-3.5 text-left font-semibold text-gray-900 hover:bg-gray-100 transition">
                  <span>{mod.title}</span>
                  <span className="text-sm font-normal text-gray-400">
                    {mod.lessons.length} lecciones · {openModule === mod.id ? '▲' : '▼'}
                  </span>
                </button>
                {openModule === mod.id && (
                  <ul className="divide-y">
                    {mod.lessons.map(lesson => (
                      <li key={lesson.id}
                        className="flex items-center justify-between px-5 py-3 text-sm text-gray-700">
                        <span className="flex items-center gap-2">
                          {lesson.isFree ? '▶' : '🔒'} {lesson.title}
                        </span>
                        <span className="text-gray-400">{lesson.durationMin} min</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>

        <aside>
          <div className="rounded-xl border bg-white p-5 sticky top-20">
            <h3 className="font-bold mb-3">El instructor</h3>
            <p className="font-semibold text-gray-900">{course.instructor.name}</p>
            {course.instructor.bio && (
              <p className="mt-2 text-sm text-gray-500">{course.instructor.bio}</p>
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
"""

_DASHBOARD = """\
'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';
import { CourseCard } from '@/components/CourseCard';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!user) router.replace('/login');
  }, [user, router]);

  const { data: enrollments, isLoading } = trpc.enrollment.myEnrollments.useQuery(undefined, {
    enabled: !!user,
  });

  if (!user) return null;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-bold mb-1">Mi academia</h1>
      <p className="text-gray-500 mb-8">Bienvenido/a, {user.name}</p>

      {isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map(i => <div key={i} className="h-64 rounded-xl bg-gray-200 animate-pulse" />)}
        </div>
      ) : enrollments?.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-5xl mb-4">📚</p>
          <h2 className="text-xl font-semibold mb-2">Todavía no tienes cursos</h2>
          <p className="text-gray-500 mb-6">Explora el catálogo y empieza a aprender hoy.</p>
          <Link href="/cursos"
            className="rounded-full bg-brand-600 px-8 py-3 font-semibold text-white hover:bg-brand-700 transition">
            Ver cursos disponibles
          </Link>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500 mb-6">
            {enrollments!.length} {enrollments!.length === 1 ? 'curso matriculado' : 'cursos matriculados'}
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {enrollments!.map(({ course }) => {
              const totalLessons = course.modules.flatMap(m => m.lessons).length;
              return <CourseCard key={course.id} course={course as any} progress={0} />;
            })}
          </div>
        </>
      )}
    </main>
  );
}
"""

_LOGIN = """\
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore(s => s.setAuth);
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');

  const login = trpc.auth.login.useMutation({
    onSuccess: ({ user, token }) => {
      setAuth(user, token);
      router.push('/mi-academia');
    },
    onError: e => setError(e.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    login.mutate(form);
  };

  return (
    <main className="flex min-h-[80vh] items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-1">Iniciar sesión</h1>
        <p className="text-gray-500 text-sm mb-8">
          ¿No tienes cuenta?{' '}
          <Link href="/registro" className="text-brand-600 font-medium hover:underline">Regístrate gratis</Link>
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" required autoFocus
              value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="tu@email.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <input type="password" required
              value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="••••••••" />
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>}

          <button type="submit" disabled={login.isPending}
            className="w-full rounded-full bg-brand-600 py-3 font-semibold text-white hover:bg-brand-700 transition disabled:opacity-60">
            {login.isPending ? 'Iniciando sesión...' : 'Iniciar sesión'}
          </button>
        </form>

        <div className="mt-6 rounded-lg bg-gray-50 border p-4 text-xs text-gray-500">
          <p className="font-medium mb-1">Acceso de prueba:</p>
          <p>alumno@academia.com / password123</p>
          <p>instructor@academia.com / password123</p>
        </div>
      </div>
    </main>
  );
}
"""

_REGISTER = """\
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { trpc } from '@/lib/trpc';
import { useAuthStore } from '@/lib/auth-store';

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore(s => s.setAuth);
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');

  const register = trpc.auth.register.useMutation({
    onSuccess: ({ user, token }) => {
      setAuth(user, token);
      router.push('/cursos');
    },
    onError: e => setError(e.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    register.mutate(form);
  };

  return (
    <main className="flex min-h-[80vh] items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-1">Crear cuenta gratis</h1>
        <p className="text-gray-500 text-sm mb-8">
          ¿Ya tienes cuenta?{' '}
          <Link href="/login" className="text-brand-600 font-medium hover:underline">Iniciar sesión</Link>
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo</label>
            <input type="text" required autoFocus
              value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Tu nombre" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" required
              value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="tu@email.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <input type="password" required minLength={6}
              value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Mínimo 6 caracteres" />
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>}

          <button type="submit" disabled={register.isPending}
            className="w-full rounded-full bg-brand-600 py-3 font-semibold text-white hover:bg-brand-700 transition disabled:opacity-60">
            {register.isPending ? 'Creando cuenta...' : 'Crear cuenta gratis'}
          </button>
        </form>
      </div>
    </main>
  );
}
"""

_WEB_DOCKERFILE = """\
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
"""

# ── Infrastructure ──────────────────────────────────────────────────────────────

_NGINX = """\
upstream api { server api:4000; }
upstream web { server web:3000; }

server {
  listen 80;
  client_max_body_size 20M;

  location /trpc/ {
    proxy_pass http://api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 60s;
  }

  location /health {
    proxy_pass http://api;
  }

  location / {
    proxy_pass http://web;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
"""

_DOCKER_COMPOSE = """\
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: __SLUG__
      POSTGRES_PASSWORD: __SLUG__secret
      POSTGRES_DB: __SLUG___db
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U __SLUG__"]
      interval: 5s
      retries: 10

  api:
    build: ./apps/api
    env_file: .env
    ports: ["4000:4000"]
    depends_on:
      postgres:
        condition: service_healthy

  web:
    build: ./apps/web
    env_file: .env
    ports: ["3000:3000"]
    depends_on: [api]

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes: [./nginx/nginx.conf:/etc/nginx/conf.d/default.conf]
    depends_on: [api, web]

volumes:
  postgres_data:
"""

_ENV = """\
# Base de datos
DATABASE_URL=postgresql://__SLUG__:__SLUG__secret@localhost:5432/__SLUG___db

# API
PORT=4000
WEB_URL=http://localhost:3000

# JWT (genera uno seguro: openssl rand -hex 32)
JWT_SECRET=cambia_esto_en_produccion_ahora_mismo

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:4000/trpc
"""

_README = """\
# __NAME__

> Plataforma de academia online — generada con ProgresIA Studio.

## Stack

- **Backend:** tRPC v11 · Fastify · Prisma · PostgreSQL
- **Frontend:** Next.js 14 App Router · Tailwind CSS · Zustand
- **Infraestructura:** Docker Compose · nginx

---

## Instalación rápida (5 min)

### 1. Variables de entorno
```bash
cp .env.example .env
# Edita JWT_SECRET con un valor seguro
```

### 2. Arrancar base de datos
```bash
docker compose up postgres -d
```

### 3. Instalar dependencias y migrar base de datos
```bash
cd apps/api
npm install
npx prisma migrate dev --name init
npm run db:seed
```

### 4. Arrancar frontend (otra terminal)
```bash
cd apps/web
npm install
npm run dev
```

### 5. Acceder a la plataforma
- **Plataforma:** http://localhost:3000
- **API (tRPC):** http://localhost:4000/trpc

---

## Cuentas de prueba (creadas por el seed)

| Rol        | Email                        | Contraseña   |
|------------|------------------------------|--------------|
| Admin      | admin@academia.com           | admin123     |
| Instructor | instructor@academia.com      | password123  |
| Alumno     | alumno@academia.com          | password123  |

---

## Despliegue completo con Docker

```bash
docker compose up --build
```
Accede en: http://localhost

---

## Estructura del proyecto

```
apps/
  api/
    prisma/
      schema.prisma        # Modelos: User, Course, Module, Lesson, Enrollment
      seed.ts              # Datos de demo
    src/
      modules/
        auth/              # Login, registro, JWT
        courses/           # CRUD cursos, categorías
        enrollments/       # Matriculación, progreso por lección
      lib/auth.ts          # bcryptjs + jsonwebtoken helpers
      trpc.ts              # Context + procedures
      router.ts            # App router
  web/
    src/
      app/                 # Next.js App Router
        page.tsx           # Landing page
        cursos/            # Catálogo + detalle
        mi-academia/       # Dashboard alumno
        login/ registro/   # Auth forms
      components/          # CourseCard, Navbar, ProgressBar
      lib/                 # tRPC client, auth store (Zustand)
nginx/nginx.conf           # Reverse proxy
docker-compose.yml         # Todos los servicios
```

---

## Próximos pasos

- [ ] Pagos con Stripe (webhook + Enrollment.amountPaid)
- [ ] Player de video (videoUrl en Lesson)
- [ ] Panel de instructor (crear/editar cursos)
- [ ] Panel de admin
- [ ] Certificados en PDF al completar curso
- [ ] Notificaciones por email (Resend / SendGrid)

---

*Generado con [ProgresIA Studio](https://progresia.app)*
"""
