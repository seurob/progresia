"""SvelteKit + TypeScript + Tailwind CSS + Prisma scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.prisma import generate_prisma_schema, generate_seed_ts
from app.agents.fallback.shared.docker import generate_docker_compose, generate_node_dockerfile
from app.agents.fallback.shared.readme import generate_readme


def build_sveltekit(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold SvelteKit 2 con Svelte 5, Tailwind CSS 4 y Prisma."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    return [
        _package_json(project_slug),
        _tsconfig(),
        _svelte_config(),
        _vite_config(),
        _app_html(req.project_name),
        _app_css(),
        _prisma_client_lib(),
        _layout_svelte(req.project_name, entity_slug_name, entity_pascal_name),
        _layout_ts(),
        _home_page_svelte(req.project_name),
        _entity_page_svelte(entity_pascal_name, entity_slug_name, entity_plural),
        _entity_page_server_ts(entity_slug_name, entity_pascal_name, entity_plural),
        _entity_api_server_ts(entity_slug_name, entity_pascal_name, entity_plural),
        _entity_id_api_server_ts(entity_slug_name, entity_pascal_name),
        generate_prisma_schema(
            req.modules, req.needs_auth, req.data_entities or None,
            schema_path="prisma/schema.prisma"
        ),
        generate_seed_ts(
            req.data_entities or [primary], req.project_name,
            seed_path="prisma/seed.ts"
        ),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Copia a .env y ajusta los valores\n\n"
                f"DATABASE_URL=postgresql://user:password@localhost:5432/{project_slug}_db\n"
                "PUBLIC_APP_NAME=" + req.project_name + "\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="SvelteKit 2 · Svelte 5 · TypeScript · Tailwind CSS 4 · Prisma · PostgreSQL",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Docker Desktop — https://docker.com",
            ],
            setup_commands=[
                "docker compose up -d",
                "npm install",
                "cp .env.example .env",
                "npx prisma migrate dev --name init",
                "npx prisma db seed",
                "npm run dev",
            ],
            env_vars=[
                ("DATABASE_URL", f"postgresql://user:password@localhost:5432/{project_slug}_db"),
            ],
            api_port=5173,
        ),
        generate_node_dockerfile(port=3000, entry="build/index.js", needs_prisma=True),
        generate_docker_compose(project_slug, needs_postgres=True, api_port=3000),
    ]


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "db:studio": "prisma studio",
    "db:migrate": "prisma migrate dev"
  }},
  "dependencies": {{
    "@prisma/client": "^5.15.0"
  }},
  "devDependencies": {{
    "@sveltejs/adapter-node": "^5.0.1",
    "@sveltejs/kit": "^2.5.10",
    "@tailwindcss/vite": "^4.0.0",
    "prisma": "^5.15.0",
    "svelte": "^5.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.5.0",
    "vite": "^5.3.1"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true,
    "moduleResolution": "bundler"
  }
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _svelte_config() -> GeneratedFile:
    content = """\
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
  },
};

export default config;
"""
    return GeneratedFile(path="svelte.config.js", language="javascript", content=content)


def _vite_config() -> GeneratedFile:
    content = """\
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
});
"""
    return GeneratedFile(path="vite.config.ts", language="typescript", content=content)


def _app_html(project_name: str) -> GeneratedFile:
    content = f"""\
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{project_name}</title>
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
"""
    return GeneratedFile(path="src/app.html", language="html", content=content)


def _app_css() -> GeneratedFile:
    content = """\
@import "tailwindcss";
"""
    return GeneratedFile(path="src/app.css", language="css", content=content)


def _prisma_client_lib() -> GeneratedFile:
    content = """\
import { PrismaClient } from '@prisma/client';

// En desarrollo, reutiliza la misma instancia entre hot-reloads
const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ?? new PrismaClient({ log: ['error'] });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}
"""
    return GeneratedFile(path="src/lib/prisma.ts", language="typescript", content=content)


def _layout_svelte(project_name: str, entity_slug_name: str, entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
<script lang="ts">
  import '../app.css';
  let {{ children }} = $props();
</script>

<div class="min-h-screen bg-gray-50 flex flex-col">
  <header class="bg-indigo-600 text-white px-6 py-3 flex items-center gap-6 shadow">
    <a href="/" class="font-bold text-lg hover:opacity-80">{project_name}</a>
    <nav class="flex gap-4 text-sm">
      <a href="/{entity_plural(entity_slug_name)}" class="hover:underline">{entity_pascal_name}s</a>
    </nav>
  </header>
  <main class="flex-1 container mx-auto px-4 py-8">
    {{@render children()}}
  </main>
  <footer class="text-center text-xs text-gray-400 py-4">
    {project_name} © {{new Date().getFullYear()}}
  </footer>
</div>
"""
    return GeneratedFile(path="src/routes/+layout.svelte", language="svelte", content=content)


def _layout_ts() -> GeneratedFile:
    content = """\
export const prerender = false;
export const ssr = true;
"""
    return GeneratedFile(path="src/routes/+layout.ts", language="typescript", content=content)


def _home_page_svelte(project_name: str) -> GeneratedFile:
    content = f"""\
<div class="max-w-xl mx-auto mt-20 text-center">
  <h1 class="text-4xl font-bold text-indigo-700 mb-4">{project_name}</h1>
  <p class="text-gray-600 text-lg">
    Tu proyecto SvelteKit está listo. Modifica esta página para empezar.
  </p>
</div>
"""
    return GeneratedFile(path="src/routes/+page.svelte", language="svelte", content=content)


def _entity_page_svelte(entity_pascal_name: str, entity_slug_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
<script lang="ts">
  let {{ data }} = $props();
</script>

<div class="max-w-4xl mx-auto">
  <h2 class="text-2xl font-bold text-gray-800 mb-6">{entity_pascal_name}s</h2>

  <ul class="divide-y divide-gray-200 bg-white shadow rounded-lg">
    {{#each data.items as item}}
      <li class="px-6 py-4 flex justify-between items-center">
        <div>
          <p class="font-medium text-gray-900">{{item.name}}</p>
          {{#if item.description}}
            <p class="text-sm text-gray-500">{{item.description}}</p>
          {{/if}}
        </div>
        <span class="text-xs px-2 py-1 rounded-full {{item.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}}">
          {{item.status ?? 'activo'}}
        </span>
      </li>
    {{:else}}
      <li class="py-12 text-center text-gray-400">
        No hay {entity_plural} todavía.
      </li>
    {{/each}}
  </ul>
</div>
"""
    return GeneratedFile(path=f"src/routes/{entity_plural}/+page.svelte", language="svelte", content=content)


def _entity_page_server_ts(entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import type {{ PageServerLoad }} from './$types';
import {{ prisma }} from '$lib/prisma';

export const load: PageServerLoad = async () => {{
  const items = await prisma.{entity_camel(entity_slug_name)}.findMany({{
    orderBy: {{ createdAt: 'desc' }},
    take: 50,
  }});
  return {{ items }};
}};
"""
    return GeneratedFile(
        path=f"src/routes/{entity_plural}/+page.server.ts",
        language="typescript",
        content=content,
    )


def _entity_api_server_ts(entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ json }} from '@sveltejs/kit';
import type {{ RequestHandler }} from './$types';
import {{ prisma }} from '$lib/prisma';

export const GET: RequestHandler = async () => {{
  const items = await prisma.{entity_camel(entity_slug_name)}.findMany({{
    orderBy: {{ createdAt: 'desc' }},
  }});
  return json(items);
}};

export const POST: RequestHandler = async ({{ request }}) => {{
  const body = await request.json();
  if (!body.name) {{
    return json({{ error: 'El campo name es obligatorio' }}, {{ status: 422 }});
  }}
  const item = await prisma.{entity_camel(entity_slug_name)}.create({{
    data: {{
      name: body.name,
      description: body.description ?? null,
      status: body.status ?? 'active',
    }},
  }});
  return json(item, {{ status: 201 }});
}};
"""
    return GeneratedFile(
        path=f"src/routes/api/{entity_plural}/+server.ts",
        language="typescript",
        content=content,
    )


def _entity_id_api_server_ts(entity_slug_name: str, entity_pascal_name: str) -> GeneratedFile:
    entity_plural = pluralize(entity_slug_name)
    content = f"""\
import {{ json, error }} from '@sveltejs/kit';
import type {{ RequestHandler }} from './$types';
import {{ prisma }} from '$lib/prisma';

export const GET: RequestHandler = async ({{ params }}) => {{
  const item = await prisma.{entity_camel(entity_slug_name)}.findUnique({{
    where: {{ id: params.id }},
  }});
  if (!item) throw error(404, '{entity_pascal_name} no encontrado');
  return json(item);
}};

export const PATCH: RequestHandler = async ({{ params, request }}) => {{
  const body = await request.json();
  const item = await prisma.{entity_camel(entity_slug_name)}.update({{
    where: {{ id: params.id }},
    data: body,
  }});
  return json(item);
}};

export const DELETE: RequestHandler = async ({{ params }}) => {{
  await prisma.{entity_camel(entity_slug_name)}.delete({{ where: {{ id: params.id }} }});
  return new Response(null, {{ status: 204 }});
}};
"""
    return GeneratedFile(
        path=f"src/routes/api/{entity_plural}/[id]/+server.ts",
        language="typescript",
        content=content,
    )


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
.svelte-kit/
build/
.env
.env.*
!.env.example
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)


def entity_plural(entity_slug_name: str) -> str:
    return pluralize(entity_slug_name)


def entity_camel(entity_slug_name: str) -> str:
    return camel(entity_slug_name)
