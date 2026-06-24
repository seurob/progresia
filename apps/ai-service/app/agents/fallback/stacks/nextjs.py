"""Next.js 15 App Router scaffold generator.

Stack: Next.js 15 + TypeScript + Tailwind CSS 4 + Prisma + PostgreSQL
"""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.prisma import generate_prisma_schema, generate_seed_ts
from app.agents.fallback.shared.docker import generate_docker_compose, generate_node_dockerfile
from app.agents.fallback.shared.readme import generate_readme


def build_nextjs(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold completo de Next.js 15 con App Router."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal = pascal(primary.get("name", "Item"))
    entity_camel = camel(primary.get("name", "Item"))
    entity_slug = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug)

    files: list[GeneratedFile] = [
        _package_json(project_slug),
        _tsconfig(),
        _next_config(),
        _tailwind_config(),
        _postcss_config(),
        _globals_css(),
        _layout(req.project_name),
        _home_page(req.project_name, req.modules),
        _entity_route(entity_slug, entity_pascal),
        _entity_id_route(entity_slug, entity_pascal),
        _health_route(),
        _entity_list_page(entity_pascal, entity_camel, entity_plural),
        _navigation(req.project_name, req.modules),
        _prisma_client(),
        generate_prisma_schema(
            req.modules, req.needs_auth, req.data_entities or None,
            schema_path="prisma/schema.prisma"
        ),
        generate_seed_ts(
            req.data_entities or [primary], req.project_name,
            seed_path="prisma/seed.ts"
        ),
        _env_example(project_slug),
        _gitignore(),
        generate_readme(
            req,
            stack_summary="Next.js 15 · Tailwind CSS 4 · Prisma · PostgreSQL",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Docker Desktop 4.x — https://docker.com/products/docker-desktop",
                "Git 2.x — https://git-scm.com",
            ],
            setup_commands=[
                "docker compose up -d",
                "npm install",
                "npx prisma migrate dev --name init",
                "npx prisma db seed",
                "npm run dev",
            ],
            env_vars=[
                ("DATABASE_URL", f"postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"),
                ("NEXTAUTH_SECRET", "genera con: openssl rand -hex 32"),
                ("NEXT_PUBLIC_APP_URL", "http://localhost:3000"),
            ],
            api_port=3000,
        ),
        generate_node_dockerfile(port=3000, entry="server.js", needs_prisma=True),
        generate_docker_compose(project_slug, needs_postgres=True, api_port=3000),
    ]

    return files


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "db:migrate": "prisma migrate dev",
    "db:seed": "ts-node --compiler-options '{{\"module\":\"CommonJS\"}}' prisma/seed.ts",
    "db:studio": "prisma studio"
  }},
  "dependencies": {{
    "@prisma/client": "^5.22.0",
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  }},
  "devDependencies": {{
    "@tailwindcss/postcss": "^4.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "prisma": "^5.22.0",
    "tailwindcss": "^4.0.0",
    "ts-node": "^10.9.2",
    "typescript": "^5.7.0"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
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
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _next_config() -> GeneratedFile:
    content = """\
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Configuración de Next.js 15
  experimental: {
    // Habilita componentes de servidor por defecto
  },
};

export default nextConfig;
"""
    return GeneratedFile(path="next.config.ts", language="typescript", content=content)


def _tailwind_config() -> GeneratedFile:
    content = """\
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#6366f1",
          dark: "#4f46e5",
          light: "#a5b4fc",
        },
      },
    },
  },
  plugins: [],
};

export default config;
"""
    return GeneratedFile(path="tailwind.config.ts", language="typescript", content=content)


def _postcss_config() -> GeneratedFile:
    content = """\
/** @type {import('postcss').Config} */
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
"""
    return GeneratedFile(path="postcss.config.mjs", language="javascript", content=content)


def _globals_css() -> GeneratedFile:
    content = """\
@import "tailwindcss";

/* Estilos globales del proyecto */
:root {
  --color-brand: #6366f1;
}

body {
  @apply antialiased;
}
"""
    return GeneratedFile(path="app/globals.css", language="css", content=content)


def _layout(project_name: str) -> GeneratedFile:
    content = f"""\
import type {{ Metadata }} from "next";
import "./globals.css";
import Navigation from "@/components/Navigation";

export const metadata: Metadata = {{
  title: "{project_name}",
  description: "MVP generado con ProgresIA Studio",
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="es">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <Navigation />
        <main className="container mx-auto px-4 py-8 max-w-6xl">
          {{children}}
        </main>
      </body>
    </html>
  );
}}
"""
    return GeneratedFile(path="app/layout.tsx", language="typescript", content=content)


def _home_page(project_name: str, modules: list[str]) -> GeneratedFile:
    links = "\n        ".join(
        f'<a href="/{slug(m)}s" className="block rounded-xl border bg-white p-6 shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5">'
        f'<h2 className="text-lg font-semibold text-gray-900">{m}</h2>'
        f'<p className="mt-1 text-sm text-gray-500">Gestionar {m.lower()}</p>'
        f"</a>"
        for m in modules[:6]
    )
    content = f"""\
// Página de inicio — muestra los módulos principales del proyecto
export default function HomePage() {{
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{project_name}</h1>
        <p className="mt-2 text-gray-500">MVP generado con ProgresIA Studio</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {links}
      </div>
    </div>
  );
}}
"""
    return GeneratedFile(path="app/page.tsx", language="typescript", content=content)


def _entity_route(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
import {{ NextResponse }} from "next/server";
import {{ prisma }} from "@/lib/prisma";

// GET /api/{entity_slug}s — obtener todos los registros
export async function GET() {{
  try {{
    const items = await prisma.{camel(entity_pascal)}.findMany({{
      orderBy: {{ createdAt: "desc" }},
    }});
    return NextResponse.json(items);
  }} catch (error) {{
    console.error("Error al obtener {entity_pascal}:", error);
    return NextResponse.json({{ error: "Error interno" }}, {{ status: 500 }});
  }}
}}

// POST /api/{entity_slug}s — crear un nuevo registro
export async function POST(request: Request) {{
  try {{
    const body = await request.json();
    const item = await prisma.{camel(entity_pascal)}.create({{
      data: {{
        name: body.name,
        description: body.description ?? null,
      }},
    }});
    return NextResponse.json(item, {{ status: 201 }});
  }} catch (error) {{
    console.error("Error al crear {entity_pascal}:", error);
    return NextResponse.json({{ error: "Error al crear el registro" }}, {{ status: 400 }});
  }}
}}
"""
    return GeneratedFile(path=f"app/api/{entity_slug}s/route.ts", language="typescript", content=content)


def _entity_id_route(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    entity_camel = camel(entity_pascal)
    content = f"""\
import {{ NextResponse }} from "next/server";
import {{ prisma }} from "@/lib/prisma";

// GET /api/{entity_slug}s/:id — obtener un registro por ID
export async function GET(
  _request: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  const item = await prisma.{entity_camel}.findUnique({{
    where: {{ id: params.id }},
  }});
  if (!item) return NextResponse.json({{ error: "No encontrado" }}, {{ status: 404 }});
  return NextResponse.json(item);
}}

// PUT /api/{entity_slug}s/:id — actualizar un registro
export async function PUT(
  request: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    const body = await request.json();
    const item = await prisma.{entity_camel}.update({{
      where: {{ id: params.id }},
      data: {{ name: body.name, description: body.description }},
    }});
    return NextResponse.json(item);
  }} catch {{
    return NextResponse.json({{ error: "No encontrado" }}, {{ status: 404 }});
  }}
}}

// DELETE /api/{entity_slug}s/:id — eliminar un registro
export async function DELETE(
  _request: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    await prisma.{entity_camel}.delete({{ where: {{ id: params.id }} }});
    return NextResponse.json({{ success: true }});
  }} catch {{
    return NextResponse.json({{ error: "No encontrado" }}, {{ status: 404 }});
  }}
}}
"""
    return GeneratedFile(path=f"app/api/{entity_slug}s/[id]/route.ts", language="typescript", content=content)


def _health_route() -> GeneratedFile:
    content = """\
import { NextResponse } from "next/server";

// GET /api/health — comprueba que el servidor está activo
export async function GET() {
  return NextResponse.json({
    status: "ok",
    timestamp: new Date().toISOString(),
  });
}
"""
    return GeneratedFile(path="app/api/health/route.ts", language="typescript", content=content)


def _entity_list_page(entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
"use client";

import {{ useState, useEffect }} from "react";

// Tipo para los datos de {entity_pascal}
interface {entity_pascal}Item {{
  id: string;
  name: string;
  description: string | null;
  createdAt: string;
}}

// Página de listado de {entity_pascal}
export default function {entity_pascal}ListPage() {{
  const [items, setItems] = useState<{entity_pascal}Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");

  // Cargar los datos al montar el componente
  useEffect(() => {{
    fetchItems();
  }}, []);

  async function fetchItems() {{
    try {{
      const res = await fetch("/api/{entity_plural}");
      const data = await res.json();
      setItems(data);
    }} catch (err) {{
      console.error("Error al cargar:", err);
    }} finally {{
      setLoading(false);
    }}
  }}

  async function handleCreate(e: React.FormEvent) {{
    e.preventDefault();
    if (!newName.trim()) return;

    await fetch("/api/{entity_plural}", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{ name: newName.trim() }}),
    }});

    setNewName("");
    fetchItems(); // Recargar la lista
  }}

  async function handleDelete(id: string) {{
    if (!confirm("¿Eliminar este elemento?")) return;
    await fetch(`/api/{entity_plural}/${{id}}`, {{ method: "DELETE" }});
    fetchItems();
  }}

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">{entity_pascal}</h1>

      {{/* Formulario para crear nuevo */}}
      <form onSubmit={{handleCreate}} className="mb-6 flex gap-2">
        <input
          type="text"
          value={{newName}}
          onChange={{(e) => setNewName(e.target.value)}}
          placeholder="Nombre del nuevo elemento..."
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
        />
        <button
          type="submit"
          className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
        >
          Añadir
        </button>
      </form>

      {{/* Lista de elementos */}}
      {{loading ? (
        <p className="text-gray-500">Cargando...</p>
      ) : (
        <ul className="grid gap-2">
          {{items.map((item) => (
            <li
              key={{item.id}}
              className="flex items-center justify-between rounded-xl border bg-white px-4 py-3 shadow-sm"
            >
              <div>
                <p className="font-medium">{{item.name}}</p>
                {{item.description && (
                  <p className="text-sm text-gray-500">{{item.description}}</p>
                )}}
              </div>
              <button
                onClick={{() => handleDelete(item.id)}}
                className="text-sm text-red-500 hover:underline"
              >
                Eliminar
              </button>
            </li>
          ))}}
          {{items.length === 0 && (
            <li className="py-8 text-center text-gray-400">
              No hay elementos todavía. ¡Crea el primero!
            </li>
          )}}
        </ul>
      )}}
    </div>
  );
}}
"""
    return GeneratedFile(path=f"app/{entity_plural}/page.tsx", language="typescript", content=content)


def _navigation(project_name: str, modules: list[str]) -> GeneratedFile:
    links = "\n        ".join(
        f'<a href="/{slug(m)}s" className="text-sm text-gray-600 hover:text-brand">{m}</a>'
        for m in modules[:5]
    )
    content = f"""\
// Componente de navegación principal
export default function Navigation() {{
  return (
    <nav className="border-b bg-white px-6 py-3 shadow-sm">
      <div className="container mx-auto flex max-w-6xl items-center justify-between">
        <a href="/" className="text-lg font-bold text-brand">{project_name}</a>
        <div className="flex gap-6">
          {links}
        </div>
      </div>
    </nav>
  );
}}
"""
    return GeneratedFile(path="components/Navigation.tsx", language="typescript", content=content)


def _prisma_client() -> GeneratedFile:
    content = """\
import { PrismaClient } from "@prisma/client";

// Singleton de Prisma para evitar múltiples conexiones en desarrollo
// Ver: https://www.prisma.io/docs/guides/performance-and-optimization/connection-management

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["query", "error"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
"""
    return GeneratedFile(path="lib/prisma.ts", language="typescript", content=content)


def _env_example(project_slug: str) -> GeneratedFile:
    content = f"""\
# Base de datos
DATABASE_URL="postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"

# Next.js
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="genera con: openssl rand -hex 32"

# URL pública de la aplicación
NEXT_PUBLIC_APP_URL="http://localhost:3000"
"""
    return GeneratedFile(path=".env.example", language="env", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
# Dependencias
node_modules/
.pnp
.pnp.js

# Build
.next/
out/
dist/

# Entorno
.env
.env.local
.env.*.local

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Editor
.vscode/
.idea/
*.swp
*.swo

# Sistema operativo
.DS_Store
Thumbs.db
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
