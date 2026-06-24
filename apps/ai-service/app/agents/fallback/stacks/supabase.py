"""Next.js 15 + Supabase (Auth + Database) scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_supabase(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Next.js 15 + Supabase con Auth y base de datos SQL."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    return [
        _package_json(project_slug),
        _tsconfig(),
        _next_config(),
        _tailwind_config(),
        _postcss_config(),
        _globals_css(),
        _layout_tsx(req.project_name, entity_slug_name, entity_pascal_name, entity_plural),
        _home_page_tsx(req.project_name),
        _entity_page_tsx(entity_pascal_name, entity_camel_name, entity_slug_name, entity_plural),
        _login_page_tsx(),
        _supabase_client(),
        _supabase_server(),
        _supabase_middleware(),
        _middleware_ts(),
        _types_index(entity_pascal_name),
        _migration_sql(entity_slug_name, entity_plural),
        _seed_sql(entity_plural),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Obtén estos valores desde tu proyecto Supabase:\n"
                "# https://app.supabase.com → Settings → API\n\n"
                "NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co\n"
                "NEXT_PUBLIC_SUPABASE_ANON_KEY=tu-anon-key\n"
                "SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Next.js 15 · Supabase · TypeScript · Tailwind CSS",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Cuenta Supabase — https://supabase.com (plan gratuito disponible)",
                "Supabase CLI (opcional) — https://supabase.com/docs/guides/cli",
            ],
            setup_commands=[
                "npm install",
                "cp .env.example .env.local        # añade tus keys de Supabase",
                "# En el SQL Editor de Supabase, ejecuta supabase/migrations/001_initial.sql",
                "# Luego ejecuta supabase/seed.sql para datos de prueba",
                "npm run dev",
            ],
            env_vars=[
                ("NEXT_PUBLIC_SUPABASE_URL", "desde Supabase → Settings → API"),
                ("NEXT_PUBLIC_SUPABASE_ANON_KEY", "desde Supabase → Settings → API"),
                ("SUPABASE_SERVICE_ROLE_KEY", "desde Supabase → Settings → API"),
            ],
            api_port=3000,
        ),
    ]


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
    "lint": "next lint"
  }},
  "dependencies": {{
    "@supabase/ssr": "^0.4.0",
    "@supabase/supabase-js": "^2.44.2",
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  }},
  "devDependencies": {{
    "@types/node": "^20.14.2",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.5.2"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "compilerOptions": {
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
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _next_config() -> GeneratedFile:
    content = """\
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    serverActions: { allowedOrigins: ['localhost:3000'] },
  },
};

export default nextConfig;
"""
    return GeneratedFile(path="next.config.ts", language="typescript", content=content)


def _tailwind_config() -> GeneratedFile:
    content = """\
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: { extend: {} },
  plugins: [],
};

export default config;
"""
    return GeneratedFile(path="tailwind.config.ts", language="typescript", content=content)


def _postcss_config() -> GeneratedFile:
    content = """\
const config = {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
export default config;
"""
    return GeneratedFile(path="postcss.config.mjs", language="javascript", content=content)


def _globals_css() -> GeneratedFile:
    content = """\
@tailwind base;
@tailwind components;
@tailwind utilities;
"""
    return GeneratedFile(path="src/app/globals.css", language="css", content=content)


def _layout_tsx(project_name: str, entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import type {{ Metadata }} from 'next';
import './globals.css';

export const metadata: Metadata = {{
  title: '{project_name}',
  description: 'Generado con ProgresIA Studio',
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="es">
      <body className="min-h-screen bg-gray-50">
        <nav className="bg-emerald-600 text-white px-6 py-3 flex items-center gap-6 shadow">
          <a href="/" className="font-bold text-lg hover:opacity-80">{project_name}</a>
          <a href="/{entity_plural}" className="text-sm hover:underline">{entity_pascal_name}s</a>
          <a href="/login" className="text-sm hover:underline ml-auto">Entrar</a>
        </nav>
        <main className="container mx-auto px-4 py-8">{{children}}</main>
        <footer className="text-center text-xs text-gray-400 py-4">
          {project_name} — powered by Supabase
        </footer>
      </body>
    </html>
  );
}}
"""
    return GeneratedFile(path="src/app/layout.tsx", language="tsx", content=content)


def _home_page_tsx(project_name: str) -> GeneratedFile:
    content = f"""\
export default function HomePage() {{
  return (
    <div className="max-w-xl mx-auto mt-20 text-center">
      <h1 className="text-4xl font-bold text-emerald-700 mb-4">{project_name}</h1>
      <p className="text-gray-600 text-lg">
        Tu proyecto Next.js + Supabase está listo.
      </p>
    </div>
  );
}}
"""
    return GeneratedFile(path="src/app/page.tsx", language="tsx", content=content)


def _entity_page_tsx(entity_pascal_name: str, entity_camel_name: str, entity_slug_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ createClient }} from '@/utils/supabase/server';

// Página de servidor — los datos se cargan directamente en Supabase
export default async function {entity_pascal_name}sPage() {{
  const supabase = await createClient();
  const {{ data: items, error }} = await supabase
    .from('{entity_plural}')
    .select('*')
    .order('created_at', {{ ascending: false }});

  if (error) {{
    return (
      <div className="text-red-600 bg-red-50 p-4 rounded-lg">
        Error cargando datos: {{error.message}}
      </div>
    );
  }}

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">{entity_pascal_name}s</h2>
      <ul className="divide-y divide-gray-200 bg-white shadow rounded-lg">
        {{items?.map(item => (
          <li key={{item.id}} className="px-6 py-4">
            <p className="font-medium text-gray-900">{{item.name}}</p>
            {{item.description && (
              <p className="text-sm text-gray-500">{{item.description}}</p>
            )}}
          </li>
        ))}}
        {{!items?.length && (
          <li className="py-12 text-center text-gray-400">No hay {entity_plural} todavía.</li>
        )}}
      </ul>
    </div>
  );
}}
"""
    return GeneratedFile(path=f"src/app/{entity_plural}/page.tsx", language="tsx", content=content)


def _login_page_tsx() -> GeneratedFile:
    content = """\
'use client';

import { useState } from 'react';
import { createClient } from '@/utils/supabase/client';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const supabase = createClient();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setError(error.message);
      setLoading(false);
    } else {
      router.push('/');
      router.refresh();
    }
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm space-y-4">
        <h2 className="text-2xl font-bold text-center text-gray-800">Iniciar sesión</h2>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-emerald-400 outline-none"
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-emerald-400 outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-600 text-white py-2 rounded-md hover:bg-emerald-700 transition font-medium disabled:opacity-60"
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}
"""
    return GeneratedFile(path="src/app/login/page.tsx", language="tsx", content=content)


def _supabase_client() -> GeneratedFile:
    content = """\
import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
"""
    return GeneratedFile(path="src/utils/supabase/client.ts", language="typescript", content=content)


def _supabase_server() -> GeneratedFile:
    content = """\
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // Ignorado en Server Components — el middleware refresca las cookies
          }
        },
      },
    },
  );
}
"""
    return GeneratedFile(path="src/utils/supabase/server.ts", language="typescript", content=content)


def _supabase_middleware() -> GeneratedFile:
    content = """\
import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // Refresca la sesión para que no expire
  await supabase.auth.getUser();

  return supabaseResponse;
}
"""
    return GeneratedFile(path="src/utils/supabase/middleware.ts", language="typescript", content=content)


def _middleware_ts() -> GeneratedFile:
    content = """\
import { type NextRequest } from 'next/server';
import { updateSession } from '@/utils/supabase/middleware';

export async function middleware(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
"""
    return GeneratedFile(path="src/middleware.ts", language="typescript", content=content)


def _types_index(entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
export interface {entity_pascal_name} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  created_at?: string;
  updated_at?: string;
  user_id?: string;
}}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _migration_sql(entity_slug_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
-- Migración inicial — ejecuta esto en el SQL Editor de Supabase
-- o con: supabase db push

CREATE TABLE IF NOT EXISTS {entity_plural} (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT         NOT NULL,
  description TEXT,
  status      TEXT         NOT NULL DEFAULT 'active',
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Habilitar Row Level Security
ALTER TABLE {entity_plural} ENABLE ROW LEVEL SECURITY;

-- Política: todos pueden leer
CREATE POLICY "allow_read" ON {entity_plural}
  FOR SELECT USING (true);

-- Política: solo el propietario puede modificar
CREATE POLICY "allow_own_write" ON {entity_plural}
  FOR ALL USING (auth.uid() = user_id);

-- Índice para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_{entity_plural}_status ON {entity_plural}(status);
CREATE INDEX IF NOT EXISTS idx_{entity_plural}_user_id ON {entity_plural}(user_id);
"""
    return GeneratedFile(path="supabase/migrations/001_initial.sql", language="sql", content=content)


def _seed_sql(entity_plural: str) -> GeneratedFile:
    content = f"""\
-- Datos de prueba — ejecuta después de la migración
-- Nota: estos registros no tienen user_id (acceso público)

INSERT INTO {entity_plural} (name, description, status) VALUES
  ('Ejemplo 1', 'Primer registro de prueba', 'active'),
  ('Ejemplo 2', 'Segundo registro de prueba', 'active'),
  ('Ejemplo 3', 'Registro archivado', 'archived')
ON CONFLICT DO NOTHING;
"""
    return GeneratedFile(path="supabase/seed.sql", language="sql", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
.next/
.env
.env.local
.env.*.local
.vercel
out/
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)
