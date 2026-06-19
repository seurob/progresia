"""Next.js 15 App Router template — TypeScript + Prisma + PostgreSQL + NextAuth + Docker.

Placeholders:
  __SLUG__   = kebab-case project name   (e.g. "mi-proyecto")
  __NAME__   = display project name      (e.g. "Mi Proyecto")
  __ENTITY__ = Pascal-case main entity   (e.g. "Producto")
  __ENTITY_LOWER__ = camelCase entity    (e.g. "producto")
  __ENTITY_PLURAL__ = camelCase plural   (e.g. "productos")
"""
from __future__ import annotations

import re

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _pascal(name: str) -> str:
    return "".join(w.capitalize() for w in re.split(r"[\s\-_]+", name.strip()))


def _f(path: str, lang: str, content: str, slug: str, name: str, entity: str) -> GeneratedFile:
    ep = entity.lower()
    eps = ep + "s"
    return GeneratedFile(
        path=path,
        language=lang,
        content=content
            .replace("__SLUG__", slug)
            .replace("__NAME__", name)
            .replace("__ENTITY__", entity)
            .replace("__ENTITY_LOWER__", ep)
            .replace("__ENTITY_PLURAL__", eps),
    )


# ── File contents ──────────────────────────────────────────────────────────────

_README = """# __NAME__ — Next.js 15 Full-stack

> Generado por **ProgresIA Studio** · Arquitectura: Next.js App Router

## ¿Qué es este proyecto?

`__NAME__` es una aplicación web moderna construida con **Next.js 15**, el framework React más usado en producción.
Combina frontend y backend en un solo proyecto TypeScript, con Prisma como ORM y NextAuth para autenticación.

---

## Stack tecnológico

| Tecnología | Versión | Propósito | Documentación |
|-----------|---------|-----------|---------------|
| Next.js | 15.x | Framework React con SSR, API Routes y App Router | https://nextjs.org/docs |
| TypeScript | 5.x | Tipado estático en todo el proyecto | https://www.typescriptlang.org/docs/ |
| Prisma | 6.x | ORM type-safe con migraciones | https://www.prisma.io/docs |
| PostgreSQL | 16 | Base de datos relacional | https://www.postgresql.org/docs/16/ |
| NextAuth.js | 5.x | Autenticación con múltiples providers | https://authjs.dev/ |
| Tailwind CSS | 4.x | Framework CSS utility-first | https://tailwindcss.com/docs |
| Docker | 26.x | Contenerización | https://docs.docker.com/ |

---

## Arquitectura del proyecto

```
__SLUG__/
├── prisma/
│   ├── schema.prisma         ← Modelos de la base de datos
│   └── seed.ts               ← Datos de prueba
├── src/
│   ├── app/
│   │   ├── layout.tsx        ← Layout raíz (HTML, providers)
│   │   ├── page.tsx          ← Página de inicio
│   │   ├── (auth)/           ← Rutas de autenticación (agrupadas)
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── dashboard/        ← Panel principal (protegido)
│   │   │   └── page.tsx
│   │   └── api/              ← API Routes (serverless functions)
│   │       ├── auth/[...nextauth]/route.ts   ← NextAuth handler
│   │       └── __ENTITY_PLURAL__/
│   │           ├── route.ts           ← GET /api/__ENTITY_PLURAL__ + POST
│   │           └── [id]/route.ts      ← GET/PUT/DELETE por ID
│   ├── components/           ← Componentes React reutilizables
│   │   ├── Navbar.tsx
│   │   └── ui/               ← UI primitivos (Button, Card...)
│   ├── lib/
│   │   ├── db.ts             ← Cliente Prisma (singleton)
│   │   ├── auth.ts           ← Configuración NextAuth
│   │   └── utils.ts          ← Funciones utilitarias
│   ├── types/index.ts        ← Tipos TypeScript compartidos
│   └── middleware.ts         ← Protección de rutas
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### ¿Por qué Next.js App Router?

**App Router** (carpeta `app/`) es el sistema de routing de Next.js 13+:

- **React Server Components** (por defecto): el HTML se genera en el servidor → mejor SEO, menos JS en el cliente
- **Client Components** (`"use client"`): componentes interactivos que se hidratan en el navegador
- **API Routes** (`app/api/`): funciones serverless que actúan como backend REST
- **Server Actions**: formularios que llaman directamente a código del servidor sin fetch manual

---

## Instalación rápida (5 minutos)

### Opción A: Con Docker (recomendado)

```bash
# 1. Clonar el proyecto
git clone <tu-repo> __SLUG__
cd __SLUG__

# 2. Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local: NEXTAUTH_SECRET=<cadena-aleatoria-segura>

# 3. Levantar todos los servicios
docker compose up --build

# 4. Ejecutar migraciones y seed (en otra terminal)
docker compose exec app npx prisma migrate dev --name init
docker compose exec app npx tsx prisma/seed.ts

# 5. ¡Listo! Abrir http://localhost:3000
```

### Opción B: Sin Docker (desarrollo local)

```bash
# Requisitos: Node.js 22+, PostgreSQL 16

# 1. Instalar dependencias
npm install

# 2. Configurar entorno
cp .env.example .env.local
# Editar .env.local con tus credenciales de PostgreSQL

# 3. Crear la base de datos y ejecutar migraciones
npx prisma migrate dev --name init

# 4. Cargar datos de prueba
npx tsx prisma/seed.ts

# 5. Iniciar servidor de desarrollo
npm run dev
# App disponible en: http://localhost:3000
```

---

## API Endpoints

### Autenticación (NextAuth)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/auth/signin` | Iniciar sesión |
| `POST` | `/api/auth/signout` | Cerrar sesión |
| `GET` | `/api/auth/session` | Obtener sesión actual |
| `POST` | `/api/auth/register` | Crear cuenta nueva |

### __ENTITY_PLURAL__ (recurso principal)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/__ENTITY_PLURAL__` | Listar todos (del usuario autenticado) |
| `POST` | `/api/__ENTITY_PLURAL__` | Crear nuevo |
| `GET` | `/api/__ENTITY_PLURAL__/[id]` | Ver detalle |
| `PUT` | `/api/__ENTITY_PLURAL__/[id]` | Actualizar |
| `DELETE` | `/api/__ENTITY_PLURAL__/[id]` | Eliminar |

---

## Conceptos clave de Next.js

### Server Components vs Client Components

```tsx
// Server Component (por defecto) — se ejecuta en el servidor
// Puede acceder directamente a la BD sin fetch
async function DashboardPage() {
  const items = await prisma.__ENTITY_LOWER__.findMany({ where: { userId: session.user.id } });
  return <ItemList items={items} />;
}

// Client Component — añadir "use client" al inicio
"use client";
function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Prisma — ORM type-safe

```typescript
// El IDE autocompletará todos los campos gracias a TypeScript
const item = await prisma.__ENTITY_LOWER__.create({
  data: {
    title: "Mi primer __ENTITY_LOWER__",
    userId: session.user.id,
  },
});

// Filtros, ordenación y paginación
const items = await prisma.__ENTITY_LOWER__.findMany({
  where: { userId: session.user.id, status: "activo" },
  orderBy: { createdAt: "desc" },
  take: 10,
  skip: 0,
});
```

### Comandos Prisma esenciales

```bash
npx prisma studio          # Interfaz web para explorar la BD
npx prisma migrate dev     # Crear migración y aplicarla
npx prisma migrate deploy  # Aplicar migraciones en producción
npx prisma db seed         # Ejecutar el seeder
npx prisma generate        # Regenerar el cliente TypeScript
```

---

## Seguridad

- **NextAuth Session**: las sesiones se almacenan en JWT firmados o en BD (configurable)
- **middleware.ts**: protege rutas automáticamente redirigiendo a login si no hay sesión
- **Variables sensibles**: `NEXTAUTH_SECRET` y credenciales de BD solo en `.env.local` (gitignoreado)
- **Prisma**: previene SQL injection automáticamente con consultas parametrizadas
- **CSRF**: NextAuth incluye protección CSRF en todos los endpoints de auth

---

## Testing

```bash
# Tests unitarios con Vitest
npm run test

# Tests en modo watch
npm run test:watch

# Cobertura
npm run test:coverage
```

---

## Despliegue

Ver `docs/deployment.md` para instrucciones en Vercel, Railway y servidor propio.

---

## Próximos pasos

- [ ] Añadir más campos al modelo `__ENTITY__` en `prisma/schema.prisma`
- [ ] Implementar paginación en el endpoint GET `/api/__ENTITY_PLURAL__`
- [ ] Añadir upload de archivos con Vercel Blob o S3
- [ ] Configurar emails con Resend o Nodemailer
- [ ] Añadir OAuth (Google, GitHub) en NextAuth config
- [ ] Implementar roles y permisos con middleware

---

*Generado con ❤️ por ProgresIA Studio — https://progresia.studio*
"""

_PACKAGE_JSON = """{
  "name": "__SLUG__",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "db:seed": "tsx prisma/seed.ts",
    "db:studio": "prisma studio"
  },
  "dependencies": {
    "next": "15.3.3",
    "next-auth": "^5.0.0-beta.25",
    "@auth/prisma-adapter": "^2.7.4",
    "@prisma/client": "^6.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "prisma": "^6.0.0",
    "tsx": "^4.19.2",
    "typescript": "^5.7.2",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/postcss": "^4.0.0",
    "vitest": "^3.0.0",
    "@vitejs/plugin-react": "^4.3.4",
    "eslint": "^9.0.0",
    "eslint-config-next": "15.3.3"
  }
}
"""

_NEXT_CONFIG = """import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
"""

_TSCONFIG = """{
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
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""

_TAILWIND_CONFIG = """import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
"""

_POSTCSS_CONFIG = """const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
"""

_DOCKERFILE = """FROM node:22-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npx prisma generate
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
"""

_DOCKER_COMPOSE = """services:
  app:
    build: .
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://dev_user:secret@db:5432/__SLUG___db
      - NEXTAUTH_URL=http://localhost:3000
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
    depends_on:
      db:
        condition: service_healthy
    networks:
      - __SLUG__-net

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: __SLUG___db
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev_user -d __SLUG___db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - __SLUG__-net

volumes:
  postgres_data:

networks:
  __SLUG__-net:
    driver: bridge
"""

_ENV_EXAMPLE = """# Base de datos PostgreSQL
DATABASE_URL="postgresql://dev_user:secret@localhost:5432/__SLUG___db"

# NextAuth — obligatorio en producción
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET=""  # Generar con: openssl rand -base64 32

# OAuth opcional (añadir los que necesites)
# GOOGLE_CLIENT_ID=""
# GOOGLE_CLIENT_SECRET=""
# GITHUB_ID=""
# GITHUB_SECRET=""
"""

_PRISMA_SCHEMA = """// Prisma schema — __NAME__
// Docs: https://pris.ly/d/prisma-schema

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum Role {
  USER
  ADMIN
}

model User {
  id            String    @id @default(cuid())
  name          String?
  email         String    @unique
  emailVerified DateTime?
  image         String?
  password      String?
  role          Role      @default(USER)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  accounts Account[]
  sessions Session[]
  __ENTITY_PLURAL__  __ENTITY__[]
}

// NextAuth — no modificar estos modelos
model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String?
  access_token      String?
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String?
  session_state     String?

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
}

model Session {
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}

// Modelo principal del proyecto — ampliar según necesidades
model __ENTITY__ {
  id          String   @id @default(cuid())
  title       String
  description String?
  status      String   @default("pendiente")
  userId      String
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)
}
"""

_PRISMA_SEED = """import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  // Usuario demo
  const demo = await prisma.user.upsert({
    where: { email: "demo@__SLUG__.local" },
    update: {},
    create: {
      email: "demo@__SLUG__.local",
      name: "Usuario Demo",
      role: "ADMIN",
    },
  });

  // Datos de ejemplo
  const existing = await prisma.__ENTITY_LOWER__.count({ where: { userId: demo.id } });
  if (existing === 0) {
    await prisma.__ENTITY_LOWER__.createMany({
      data: [
        { title: "Primer __ENTITY_LOWER__ de ejemplo",  description: "Registro creado automáticamente por el seeder.",    status: "completado", userId: demo.id },
        { title: "Segundo __ENTITY_LOWER__ en progreso", description: "Modifica los campos en prisma/schema.prisma.", status: "en_progreso", userId: demo.id },
        { title: "Tercer __ENTITY_LOWER__ pendiente",   description: "Añade más campos según las necesidades del proyecto.", status: "pendiente",  userId: demo.id },
      ],
    });
  }

  console.log("✅ Seed completado:");
  console.log("   Email: demo@__SLUG__.local");
  console.log("   Recuerda crear la contraseña desde /register o la consola de Prisma");
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
"""

_LIB_DB = """import { PrismaClient } from "@prisma/client";

// Patrón singleton para evitar múltiples conexiones en desarrollo (hot-reload)
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
});

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
"""

_LIB_AUTH = """import NextAuth from "next-auth";
import { PrismaAdapter } from "@auth/prisma-adapter";
import Credentials from "next-auth/providers/credentials";
import { prisma } from "./db";

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  session: { strategy: "jwt" },
  pages: {
    signIn: "/login",
  },
  providers: [
    Credentials({
      credentials: {
        email:    { label: "Email",    type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const user = await prisma.user.findUnique({
          where: { email: credentials.email as string },
        });

        if (!user?.password) return null;

        // En producción: usar bcryptjs para comparar hashes
        // const valid = await bcrypt.compare(credentials.password, user.password);
        const valid = credentials.password === user.password;
        if (!valid) return null;

        return { id: user.id, email: user.email, name: user.name };
      },
    }),
  ],
  callbacks: {
    jwt({ token, user }) {
      if (user) token.id = user.id;
      return token;
    },
    session({ session, token }) {
      if (token.id) session.user.id = token.id as string;
      return session;
    },
  },
});
"""

_LIB_UTILS = """import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleDateString("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatRelativeTime(date: Date | string): string {
  const d    = new Date(date);
  const now  = new Date();
  const diff = now.getTime() - d.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return "hoy";
  if (days === 1) return "ayer";
  if (days < 7)  return `hace ${days} días`;
  return formatDate(d);
}
"""

_TYPES_INDEX = """export type Status = "pendiente" | "en_progreso" | "completado";

export interface __ENTITY__Item {
  id:          string;
  title:       string;
  description: string | null;
  status:      Status;
  userId:      string;
  createdAt:   string;
  updatedAt:   string;
}

export interface PaginatedResponse<T> {
  data:    T[];
  total:   number;
  page:    number;
  limit:   number;
  hasMore: boolean;
}

export interface ApiError {
  error:   string;
  message: string;
  status:  number;
}
"""

_MIDDLEWARE = """import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isAuthRoute = req.nextUrl.pathname.startsWith("/login") ||
                      req.nextUrl.pathname.startsWith("/register");
  const isApiRoute  = req.nextUrl.pathname.startsWith("/api");

  if (isApiRoute) return NextResponse.next();

  if (!isLoggedIn && !isAuthRoute) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (isLoggedIn && isAuthRoute) {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
"""

_LAYOUT_TSX = """import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title:       "__NAME__",
  description: "Generado por ProgresIA Studio",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
"""

_GLOBALS_CSS = """@import "tailwindcss";
"""

_PAGE_HOME = """import Link from "next/link";
import { auth } from "@/lib/auth";

export default async function HomePage() {
  const session = await auth();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Bienvenido a __NAME__
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Generado por ProgresIA Studio con Next.js 15 + Prisma + PostgreSQL
        </p>

        <div className="flex gap-4 justify-center">
          {session ? (
            <Link
              href="/dashboard"
              className="rounded-lg bg-blue-600 px-6 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
            >
              Ir al dashboard
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg bg-blue-600 px-6 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
              >
                Iniciar sesión
              </Link>
              <Link
                href="/register"
                className="rounded-lg border border-gray-300 px-6 py-3 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
              >
                Crear cuenta
              </Link>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
"""

_PAGE_LOGIN = """"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const router  = useRouter();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    if (result?.error) {
      setError("Email o contraseña incorrectos.");
    } else {
      router.push("/dashboard");
      router.refresh();
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Iniciar sesión</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="tu@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          ¿No tienes cuenta?{" "}
          <Link href="/register" className="text-blue-600 hover:underline font-medium">
            Regístrate aquí
          </Link>
        </p>
      </div>
    </div>
  );
}
"""

_PAGE_REGISTER = """"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const res = await fetch("/api/auth/register", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name, email, password }),
    });

    if (!res.ok) {
      const data = await res.json();
      setError(data.error ?? "Error al crear la cuenta.");
    } else {
      router.push("/login?registered=1");
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Crear cuenta</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
            <input
              type="text"
              required
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Tu nombre"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="tu@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Mínimo 8 caracteres"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? "Creando cuenta..." : "Crear cuenta"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="text-blue-600 hover:underline font-medium">
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
"""

_PAGE_DASHBOARD = """import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { formatDate } from "@/lib/utils";
import Navbar from "@/components/Navbar";

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.user) redirect("/login");

  const items = await prisma.__ENTITY_LOWER__.findMany({
    where:   { userId: session.user.id },
    orderBy: { createdAt: "desc" },
    take:    20,
  });

  const stats = {
    total:     items.length,
    pendiente:  items.filter(i => i.status === "pendiente").length,
    enProgreso: items.filter(i => i.status === "en_progreso").length,
    completado: items.filter(i => i.status === "completado").length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={session.user} />

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">__ENTITY_PLURAL__</h1>
            <p className="text-gray-500 mt-1">Gestiona tus __ENTITY_PLURAL__ desde aquí</p>
          </div>
          <button className="rounded-lg bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 transition-colors">
            + Nuevo __ENTITY_LOWER__
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total",      value: stats.total,     color: "bg-gray-100 text-gray-800" },
            { label: "Pendientes", value: stats.pendiente,  color: "bg-yellow-50 text-yellow-800" },
            { label: "En progreso",value: stats.enProgreso, color: "bg-blue-50 text-blue-800" },
            { label: "Completados",value: stats.completado, color: "bg-green-50 text-green-800" },
          ].map(s => (
            <div key={s.label} className={`rounded-xl p-4 ${s.color}`}>
              <div className="text-2xl font-bold">{s.value}</div>
              <div className="text-sm mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Items list */}
        {items.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <p className="text-lg">No hay __ENTITY_PLURAL__ todavía.</p>
            <p className="text-sm mt-2">Crea el primero haciendo clic en &quot;+ Nuevo __ENTITY_LOWER__&quot;.</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Título</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Estado</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Creado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map(item => (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{item.title}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        item.status === "completado"  ? "bg-green-50 text-green-700" :
                        item.status === "en_progreso" ? "bg-blue-50 text-blue-700"  :
                                                        "bg-yellow-50 text-yellow-700"
                      }`}>
                        {item.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(item.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
"""

_API_AUTH_NEXTAUTH = """import { handlers } from "@/lib/auth";

export const { GET, POST } = handlers;
"""

_API_AUTH_REGISTER = """import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function POST(req: NextRequest) {
  try {
    const { name, email, password } = await req.json();

    if (!email || !password || password.length < 8) {
      return NextResponse.json({ error: "Datos inválidos." }, { status: 400 });
    }

    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      return NextResponse.json({ error: "Este email ya está registrado." }, { status: 409 });
    }

    // En producción: usar bcryptjs para hashear la contraseña
    // const hashedPassword = await bcrypt.hash(password, 12);
    const user = await prisma.user.create({
      data: { name, email, password },
      select: { id: true, email: true, name: true },
    });

    return NextResponse.json(user, { status: 201 });
  } catch {
    return NextResponse.json({ error: "Error interno del servidor." }, { status: 500 });
  }
}
"""

_API_ENTITY_ROUTE = """import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "No autorizado." }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const page  = Number(searchParams.get("page")  ?? 1);
  const limit = Number(searchParams.get("limit") ?? 15);
  const skip  = (page - 1) * limit;

  const [data, total] = await Promise.all([
    prisma.__ENTITY_LOWER__.findMany({
      where:   { userId: session.user.id },
      orderBy: { createdAt: "desc" },
      take:    limit,
      skip,
    }),
    prisma.__ENTITY_LOWER__.count({ where: { userId: session.user.id } }),
  ]);

  return NextResponse.json({ data, total, page, limit, hasMore: skip + data.length < total });
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "No autorizado." }, { status: 401 });
  }

  const { title, description, status } = await req.json();

  if (!title?.trim()) {
    return NextResponse.json({ error: "El título es obligatorio." }, { status: 400 });
  }

  const item = await prisma.__ENTITY_LOWER__.create({
    data: {
      title:       title.trim(),
      description: description ?? null,
      status:      status ?? "pendiente",
      userId:      session.user.id,
    },
  });

  return NextResponse.json(item, { status: 201 });
}
"""

_API_ENTITY_ID_ROUTE = """import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

async function getItem(id: string, userId: string) {
  return prisma.__ENTITY_LOWER__.findFirst({ where: { id, userId } });
}

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const session = await auth();
  if (!session?.user) return NextResponse.json({ error: "No autorizado." }, { status: 401 });

  const { id } = await params;
  const item = await getItem(id, session.user.id);
  if (!item) return NextResponse.json({ error: "No encontrado." }, { status: 404 });

  return NextResponse.json(item);
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const session = await auth();
  if (!session?.user) return NextResponse.json({ error: "No autorizado." }, { status: 401 });

  const { id } = await params;
  const existing = await getItem(id, session.user.id);
  if (!existing) return NextResponse.json({ error: "No encontrado." }, { status: 404 });

  const { title, description, status } = await req.json();
  const item = await prisma.__ENTITY_LOWER__.update({
    where: { id },
    data: {
      ...(title       !== undefined && { title }),
      ...(description !== undefined && { description }),
      ...(status      !== undefined && { status }),
    },
  });

  return NextResponse.json(item);
}

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const session = await auth();
  if (!session?.user) return NextResponse.json({ error: "No autorizado." }, { status: 401 });

  const { id } = await params;
  const existing = await getItem(id, session.user.id);
  if (!existing) return NextResponse.json({ error: "No encontrado." }, { status: 404 });

  await prisma.__ENTITY_LOWER__.delete({ where: { id } });
  return new NextResponse(null, { status: 204 });
}
"""

_COMPONENT_NAVBAR = """"use client";

import Link from "next/link";
import { signOut } from "next-auth/react";
import type { User } from "next-auth";

interface NavbarProps {
  user: User;
}

export default function Navbar({ user }: NavbarProps) {
  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/dashboard" className="font-bold text-gray-900 hover:text-blue-600 transition-colors">
          __NAME__
        </Link>

        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">{user.name ?? user.email}</span>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Salir
          </button>
        </div>
      </div>
    </nav>
  );
}
"""

_COMPONENT_BUTTON = """import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  size?:    "sm" | "md" | "lg";
}

const variantClasses = {
  primary:   "bg-blue-600 text-white hover:bg-blue-700",
  secondary: "border border-gray-300 text-gray-700 hover:bg-gray-50",
  danger:    "bg-red-600 text-white hover:bg-red-700",
};

const sizeClasses = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export function Button({ variant = "primary", size = "md", className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    />
  );
}
"""

_COMPONENT_CARD = """import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: boolean;
}

export function Card({ className, padding = true, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white shadow-sm",
        padding && "p-6",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
"""

_CI_YML = """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: __SLUG___test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: secret
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Generate Prisma client
        run: npx prisma generate
        env:
          DATABASE_URL: postgresql://test_user:secret@localhost:5432/__SLUG___test

      - name: Run migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://test_user:secret@localhost:5432/__SLUG___test

      - name: Run tests
        run: npm test
        env:
          DATABASE_URL: postgresql://test_user:secret@localhost:5432/__SLUG___test
          NEXTAUTH_URL: http://localhost:3000
          NEXTAUTH_SECRET: test-secret-for-ci-only

      - name: Type check
        run: npx tsc --noEmit
"""

_DOCS_ARCHITECTURE = """# Arquitectura de __NAME__

## Next.js App Router — Flujo de datos

```
Navegador
   ↓
src/middleware.ts          ← Comprueba la sesión; redirige si no hay auth
   ↓
src/app/dashboard/page.tsx ← React Server Component (se ejecuta en el servidor)
   ↓
src/lib/db.ts (Prisma)     ← Consulta la BD directamente (sin fetch HTTP)
   ↓
HTML renderizado           ← Se envía al navegador ya con los datos
```

## Server Components vs Client Components

| | Server Component | Client Component |
|--|--|--|
| Marcador | (ninguno — por defecto) | `"use client"` al inicio |
| Ejecución | Servidor | Navegador |
| Acceso a BD | ✅ Directo con Prisma | ❌ Solo via API Route |
| Estado React | ❌ Sin useState/useEffect | ✅ Completo |
| SEO | ✅ Excelente (HTML pre-renderizado) | ⚠️ Requiere configuración |
| Uso ideal | Páginas que muestran datos | Formularios, botones, interactividad |

## API Routes — Endpoints serverless

Las API Routes en `src/app/api/` son funciones serverless que se ejecutan en el servidor:

```typescript
// src/app/api/__ENTITY_PLURAL__/route.ts
export async function GET(req: NextRequest) {
  const session = await auth();            // Verificar sesión
  const data    = await prisma.__ENTITY_LOWER__.findMany(...);  // Consultar BD
  return NextResponse.json(data);         // Respuesta JSON
}
```

Cada archivo `route.ts` puede exportar: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`.

## Modelo de datos (Prisma)

```
User
  id            cuid() PK
  email         unique
  password      nullable (algunos users usan OAuth)
  role          USER | ADMIN
  ──── relaciones ────
  accounts      Account[]     (OAuth)
  sessions      Session[]     (NextAuth)
  __ENTITY_PLURAL__  __ENTITY__[]

__ENTITY__
  id            cuid() PK
  title         string
  description   nullable
  status        pendiente | en_progreso | completado
  userId        FK → User.id (CASCADE)
```

## Por qué Next.js para este proyecto

1. **Un solo proyecto**: frontend + backend en el mismo repositorio → deploy simplificado
2. **TypeScript end-to-end**: Prisma genera tipos desde el schema → autocompletado en toda la app
3. **SEO nativo**: Server Components generan HTML en el servidor sin JavaScript extra
4. **Deploy en 1 clic**: Vercel detecta Next.js automáticamente y despliega en segundos
5. **NextAuth maduro**: autenticación completa (JWT, OAuth, credenciales) con poco código
"""


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    entity = _pascal((req.modules[0] if req.modules else req.project_name).split()[0])

    def f(path: str, lang: str, content: str) -> GeneratedFile:
        return _f(path, lang, content, slug, name, entity)

    ep = entity.lower()

    return CodeGenerationResponse(
        project_name=name,
        files=[
            # Documentation
            f("README.md",                                               "markdown",   _README),
            f("docs/architecture.md",                                    "markdown",   _DOCS_ARCHITECTURE),
            # Infrastructure
            f("Dockerfile",                                              "dockerfile", _DOCKERFILE),
            f("docker-compose.yml",                                      "yaml",       _DOCKER_COMPOSE),
            f(".env.example",                                            "dotenv",     _ENV_EXAMPLE),
            f(".github/workflows/ci.yml",                                "yaml",       _CI_YML),
            # Next.js config
            f("package.json",                                            "json",       _PACKAGE_JSON),
            f("next.config.ts",                                          "typescript", _NEXT_CONFIG),
            f("tsconfig.json",                                           "json",       _TSCONFIG),
            f("tailwind.config.ts",                                      "typescript", _TAILWIND_CONFIG),
            f("postcss.config.mjs",                                      "javascript", _POSTCSS_CONFIG),
            # Prisma
            f("prisma/schema.prisma",                                    "prisma",     _PRISMA_SCHEMA),
            f("prisma/seed.ts",                                          "typescript", _PRISMA_SEED),
            # App
            f("src/app/globals.css",                                     "css",        _GLOBALS_CSS),
            f("src/app/layout.tsx",                                      "typescript", _LAYOUT_TSX),
            f("src/app/page.tsx",                                        "typescript", _PAGE_HOME),
            f("src/app/(auth)/login/page.tsx",                           "typescript", _PAGE_LOGIN),
            f("src/app/(auth)/register/page.tsx",                        "typescript", _PAGE_REGISTER),
            f("src/app/dashboard/page.tsx",                              "typescript", _PAGE_DASHBOARD),
            # API Routes
            f("src/app/api/auth/[...nextauth]/route.ts",                 "typescript", _API_AUTH_NEXTAUTH),
            f("src/app/api/auth/register/route.ts",                      "typescript", _API_AUTH_REGISTER),
            f(f"src/app/api/{ep}s/route.ts",                             "typescript", _API_ENTITY_ROUTE),
            f(f"src/app/api/{ep}s/[id]/route.ts",                        "typescript", _API_ENTITY_ID_ROUTE),
            # Components
            f("src/components/Navbar.tsx",                               "typescript", _COMPONENT_NAVBAR),
            f("src/components/ui/Button.tsx",                            "typescript", _COMPONENT_BUTTON),
            f("src/components/ui/Card.tsx",                              "typescript", _COMPONENT_CARD),
            # Lib
            f("src/lib/db.ts",                                           "typescript", _LIB_DB),
            f("src/lib/auth.ts",                                         "typescript", _LIB_AUTH),
            f("src/lib/utils.ts",                                        "typescript", _LIB_UTILS),
            # Types & middleware
            f("src/types/index.ts",                                      "typescript", _TYPES_INDEX),
            f("src/middleware.ts",                                        "typescript", _MIDDLEWARE),
        ],
    )
