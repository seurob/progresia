"""Astro 4 + TypeScript + Tailwind CSS scaffold generator (SSG/SSR híbrido)."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_astro(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Astro 4 con Tailwind CSS — ideal para sitios estáticos y marketing."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    return [
        _package_json(project_slug),
        _tsconfig(),
        _astro_config(),
        _tailwind_config(),
        _base_layout(req.project_name),
        _main_layout(req.project_name, entity_slug_name, entity_pascal_name, entity_plural),
        _index_page(req.project_name),
        _entity_page(entity_pascal_name, entity_slug_name, entity_plural),
        _about_page(req.project_name),
        _navigation(req.project_name, entity_slug_name, entity_pascal_name, entity_plural),
        _footer(req.project_name),
        _entity_card(entity_pascal_name),
        _data_file(entity_slug_name, entity_pascal_name, entity_plural),
        _favicon_svg(),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Variables de entorno — copia a .env\n\n"
                "# URL del API si necesitas datos dinámicos\n"
                "PUBLIC_API_URL=http://localhost:3000\n"
                f"PUBLIC_APP_NAME={req.project_name}\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Astro 4 · TypeScript · Tailwind CSS · SSG",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
            ],
            setup_commands=[
                "npm install",
                "cp .env.example .env",
                "npm run dev",
                "# Para construir el sitio estático:",
                "npm run build",
                "npm run preview",
            ],
            env_vars=[
                ("PUBLIC_API_URL", "http://localhost:3000"),
            ],
            api_port=4321,
        ),
    ]


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "astro dev",
    "start": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "astro": "astro"
  }},
  "dependencies": {{
    "astro": "^4.11.0",
    "@astrojs/tailwind": "^5.1.0",
    "@astrojs/sitemap": "^3.1.5",
    "tailwindcss": "^3.4.4"
  }},
  "devDependencies": {{
    "typescript": "^5.5.2"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "extends": "astro/tsconfigs/strict",
  "compilerOptions": {
    "strictNullChecks": true,
    "allowJs": true
  }
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _astro_config() -> GeneratedFile:
    content = """\
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  integrations: [
    tailwind(),
    sitemap(),
  ],
  output: 'static',
  // Cambia a 'server' si necesitas SSR con adaptador
  // Para Vercel: instala @astrojs/vercel y añade adapter: vercel()
});
"""
    return GeneratedFile(path="astro.config.mjs", language="javascript", content=content)


def _tailwind_config() -> GeneratedFile:
    content = """\
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
};
"""
    return GeneratedFile(path="tailwind.config.mjs", language="javascript", content=content)


def _base_layout(project_name: str) -> GeneratedFile:
    content = f"""\
---
interface Props {{
  title: string;
  description?: string;
}}
const {{ title, description = '{project_name}' }} = Astro.props;
---

<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="description" content={{description}} />
    <title>{{title}} | {project_name}</title>
  </head>
  <body class="antialiased text-gray-900">
    <slot />
  </body>
</html>
"""
    return GeneratedFile(path="src/layouts/BaseLayout.astro", language="astro", content=content)


def _main_layout(project_name: str, entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
---
import BaseLayout from './BaseLayout.astro';
import Navigation from '../components/Navigation.astro';
import Footer from '../components/Footer.astro';

interface Props {{
  title: string;
  description?: string;
}}
const {{ title, description }} = Astro.props;
---

<BaseLayout title={{title}} description={{description}}>
  <div class="min-h-screen flex flex-col">
    <Navigation />
    <main class="flex-1">
      <slot />
    </main>
    <Footer />
  </div>
</BaseLayout>
"""
    return GeneratedFile(path="src/layouts/MainLayout.astro", language="astro", content=content)


def _index_page(project_name: str) -> GeneratedFile:
    content = f"""\
---
import MainLayout from '../layouts/MainLayout.astro';
---

<MainLayout title="Inicio">
  <!-- Hero -->
  <section class="bg-gradient-to-br from-brand-600 to-brand-700 text-white py-24 px-4">
    <div class="max-w-4xl mx-auto text-center">
      <h1 class="text-5xl font-bold mb-6">{project_name}</h1>
      <p class="text-xl text-blue-100 mb-10 max-w-2xl mx-auto">
        Una plataforma pensada para ayudarte a conseguir tus objetivos.
        Empieza gratis hoy.
      </p>
      <div class="flex gap-4 justify-center flex-wrap">
        <a
          href="#features"
          class="bg-white text-brand-700 font-semibold px-8 py-3 rounded-lg hover:bg-blue-50 transition"
        >
          Ver funcionalidades
        </a>
        <a
          href="/about"
          class="border border-white text-white px-8 py-3 rounded-lg hover:bg-white/10 transition"
        >
          Saber más
        </a>
      </div>
    </div>
  </section>

  <!-- Features -->
  <section id="features" class="py-20 px-4 bg-white">
    <div class="max-w-5xl mx-auto">
      <h2 class="text-3xl font-bold text-center text-gray-800 mb-12">
        ¿Qué puedes hacer?
      </h2>
      <div class="grid md:grid-cols-3 gap-8">
        {{[
          {{ icon: '⚡', title: 'Rápido', desc: 'Generado como sitio estático, velocidad máxima.' }},
          {{ icon: '🎨', title: 'Personalizable', desc: 'Tailwind CSS para adaptar el diseño a tu marca.' }},
          {{ icon: '🔒', title: 'Seguro', desc: 'Sin servidor, sin base de datos expuesta.' }},
        ].map(f => (
          <div class="text-center p-6 rounded-xl border border-gray-100 hover:shadow-md transition">
            <div class="text-4xl mb-4">{{f.icon}}</div>
            <h3 class="font-semibold text-lg text-gray-800 mb-2">{{f.title}}</h3>
            <p class="text-gray-600 text-sm">{{f.desc}}</p>
          </div>
        ))}}
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="py-16 px-4 bg-gray-50 text-center">
    <h2 class="text-2xl font-bold text-gray-800 mb-4">¿Listo para empezar?</h2>
    <p class="text-gray-600 mb-8">Modifica este sitio y despliégalo en minutos.</p>
    <a
      href="/about"
      class="bg-brand-600 text-white px-8 py-3 rounded-lg hover:bg-brand-700 transition font-semibold"
    >
      Comenzar
    </a>
  </section>
</MainLayout>
"""
    return GeneratedFile(path="src/pages/index.astro", language="astro", content=content)


def _entity_page(entity_pascal_name: str, entity_slug_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
---
import MainLayout from '../layouts/MainLayout.astro';
import {entity_pascal_name}Card from '../components/{entity_pascal_name}Card.astro';
import {{ {entity_camel(entity_slug_name)}Data }} from '../data/{entity_slug_name}';
---

<MainLayout title="{entity_pascal_name}s">
  <div class="max-w-5xl mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold text-gray-800 mb-2">{entity_pascal_name}s</h1>
    <p class="text-gray-500 mb-10">Explora todos los {entity_plural} disponibles.</p>

    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {{{entity_camel(entity_slug_name)}Data.map(item => (
        <{entity_pascal_name}Card item={{item}} />
      ))}}
    </div>

    {{!{entity_camel(entity_slug_name)}Data.length && (
      <p class="text-center text-gray-400 py-16">No hay {entity_plural} todavía.</p>
    )}}
  </div>
</MainLayout>
"""
    return GeneratedFile(path=f"src/pages/{entity_slug_name}.astro", language="astro", content=content)


def _about_page(project_name: str) -> GeneratedFile:
    content = f"""\
---
import MainLayout from '../layouts/MainLayout.astro';
---

<MainLayout title="Sobre nosotros">
  <div class="max-w-3xl mx-auto px-4 py-16">
    <h1 class="text-4xl font-bold text-gray-800 mb-6">Sobre {project_name}</h1>
    <div class="prose prose-lg text-gray-600 space-y-4">
      <p>
        Bienvenido a <strong>{project_name}</strong>. Esta es la página de información
        del proyecto. Modifícala para explicar tu propuesta de valor.
      </p>
      <p>
        Este sitio está generado con <a href="https://astro.build" class="text-brand-600 hover:underline">Astro</a>,
        un framework moderno para crear sitios web ultrarrápidos.
      </p>
    </div>
  </div>
</MainLayout>
"""
    return GeneratedFile(path="src/pages/about.astro", language="astro", content=content)


def _navigation(project_name: str, entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
---
const navItems = [
  {{ href: '/', label: 'Inicio' }},
  {{ href: '/{entity_slug_name}', label: '{entity_pascal_name}s' }},
  {{ href: '/about', label: 'Nosotros' }},
];

const currentPath = Astro.url.pathname;
---

<header class="bg-white border-b border-gray-100 shadow-sm sticky top-0 z-50">
  <nav class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
    <a href="/" class="font-bold text-xl text-brand-600">{project_name}</a>
    <ul class="flex gap-6 text-sm font-medium">
      {{navItems.map(item => (
        <li>
          <a
            href={{item.href}}
            class={{`hover:text-brand-600 transition ${{currentPath === item.href ? 'text-brand-600 font-semibold' : 'text-gray-600'}}`}}
          >
            {{item.label}}
          </a>
        </li>
      ))}}
    </ul>
  </nav>
</header>
"""
    return GeneratedFile(path="src/components/Navigation.astro", language="astro", content=content)


def _footer(project_name: str) -> GeneratedFile:
    content = f"""\
---
const year = new Date().getFullYear();
---

<footer class="bg-gray-900 text-gray-400 py-8 text-center text-sm">
  <p>© {{year}} {project_name}. Generado con ProgresIA Studio.</p>
</footer>
"""
    return GeneratedFile(path="src/components/Footer.astro", language="astro", content=content)


def _entity_card(entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
---
interface Props {{
  item: {{
    id: string;
    name: string;
    description?: string;
    status?: string;
  }};
}}
const {{ item }} = Astro.props;
---

<article class="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition group">
  <div class="flex justify-between items-start mb-3">
    <h3 class="font-semibold text-gray-900 group-hover:text-brand-600 transition">
      {{item.name}}
    </h3>
    {{item.status && (
      <span class={{`text-xs px-2 py-0.5 rounded-full ${{
        item.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
      }}`}}>
        {{item.status}}
      </span>
    )}}
  </div>
  {{item.description && (
    <p class="text-sm text-gray-500 leading-relaxed">{{item.description}}</p>
  )}}
</article>
"""
    return GeneratedFile(path=f"src/components/{entity_pascal_name}Card.astro", language="astro", content=content)


def _data_file(entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    data_var = entity_camel(entity_slug_name) + "Data"
    content = f"""\
// Datos estáticos — reemplaza por llamadas a tu API o CMS si necesitas datos dinámicos

export interface {entity_pascal_name} {{
  id: string;
  name: string;
  description?: string;
  status?: string;
}}

export const {data_var}: {entity_pascal_name}[] = [
  {{
    id: '1',
    name: 'Ejemplo 1',
    description: 'Descripción del primer ejemplo',
    status: 'active',
  }},
  {{
    id: '2',
    name: 'Ejemplo 2',
    description: 'Descripción del segundo ejemplo',
    status: 'active',
  }},
  {{
    id: '3',
    name: 'Ejemplo 3',
    description: 'Un ejemplo más con estado diferente',
    status: 'archived',
  }},
];
"""
    return GeneratedFile(path=f"src/data/{entity_slug_name}.ts", language="typescript", content=content)


def _favicon_svg() -> GeneratedFile:
    content = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#2563eb"/>
  <text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-family="sans-serif" font-weight="bold">P</text>
</svg>
"""
    return GeneratedFile(path="public/favicon.svg", language="svg", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.output/
.vercel/
.netlify/
.env
.env.local
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)


def entity_camel(entity_slug_name: str) -> str:
    return camel(entity_slug_name)
