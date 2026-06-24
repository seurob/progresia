"""Vue 3 + Vite + TypeScript + Tailwind CSS + Pinia scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_vue_vite(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Vue 3 con Pinia, Vue Router, Axios y Tailwind CSS."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    return [
        _package_json(project_slug),
        _tsconfig(),
        _vite_config(),
        _tailwind_config(),
        _postcss_config(),
        _index_html(req.project_name),
        _main_ts(entity_slug_name),
        _app_vue(),
        _router(entity_slug_name, entity_pascal_name),
        _entity_store(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _api_service(),
        _types_index(entity_pascal_name),
        _layout_vue(req.project_name, entity_slug_name, entity_pascal_name),
        _home_page(req.project_name),
        _entity_list_page(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _entity_form_page(entity_slug_name, entity_pascal_name, entity_camel_name),
        _entity_card(entity_pascal_name),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Variables de entorno — copia este archivo a .env y ajusta\n\n"
                "# URL del backend API\n"
                "VITE_API_URL=http://localhost:3000\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Vue 3 · Vite · TypeScript · Pinia · Tailwind CSS",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
            ],
            setup_commands=[
                "npm install",
                "cp .env.example .env",
                "npm run dev",
            ],
            env_vars=[
                ("VITE_API_URL", "http://localhost:3000"),
            ],
            api_port=5173,
        ),
    ]


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "axios": "^1.7.2",
    "pinia": "^2.1.7",
    "vue": "^3.4.27",
    "vue-router": "^4.3.2"
  }},
  "devDependencies": {{
    "@vitejs/plugin-vue": "^5.0.5",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.4.5",
    "vite": "^5.2.11",
    "vue-tsc": "^2.0.16"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _vite_config() -> GeneratedFile:
    content = """\
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
});
"""
    return GeneratedFile(path="vite.config.ts", language="typescript", content=content)


def _tailwind_config() -> GeneratedFile:
    content = """\
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
"""
    return GeneratedFile(path="tailwind.config.ts", language="typescript", content=content)


def _postcss_config() -> GeneratedFile:
    content = """\
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
    return GeneratedFile(path="postcss.config.js", language="javascript", content=content)


def _index_html(project_name: str) -> GeneratedFile:
    content = f"""\
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
"""
    return GeneratedFile(path="index.html", language="html", content=content)


def _main_ts(entity_slug_name: str) -> GeneratedFile:
    content = f"""\
import {{ createApp }} from 'vue';
import {{ createPinia }} from 'pinia';
import App from './App.vue';
import {{ router }} from './router';
import './style.css';

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount('#app');
"""
    return GeneratedFile(path="src/main.ts", language="typescript", content=content)


def _app_vue() -> GeneratedFile:
    content = """\
<template>
  <Layout />
</template>

<script setup lang="ts">
import Layout from './components/Layout.vue';
</script>
"""
    return GeneratedFile(path="src/App.vue", language="vue", content=content)


def _router(entity_slug_name: str, entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
import {{ createRouter, createWebHistory }} from 'vue-router';
import type {{ RouteRecordRaw }} from 'vue-router';

const routes: RouteRecordRaw[] = [
  {{
    path: '/',
    component: () => import('../pages/HomePage.vue'),
  }},
  {{
    path: '/{entity_plural(entity_slug_name)}',
    component: () => import('../pages/{entity_pascal_name}ListPage.vue'),
  }},
  {{
    path: '/{entity_plural(entity_slug_name)}/new',
    component: () => import('../pages/{entity_pascal_name}FormPage.vue'),
  }},
  {{
    path: '/{entity_plural(entity_slug_name)}/:id/edit',
    component: () => import('../pages/{entity_pascal_name}FormPage.vue'),
  }},
];

export const router = createRouter({{
  history: createWebHistory(),
  routes,
}});
"""
    return GeneratedFile(path="src/router/index.ts", language="typescript", content=content)


def _entity_store(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural_name: str) -> GeneratedFile:
    content = f"""\
import {{ defineStore }} from 'pinia';
import {{ ref }} from 'vue';
import {{ api }} from '../services/api';
import type {{ {entity_pascal_name} }} from '../types';

export const use{entity_pascal_name}Store = defineStore('{entity_camel_name}', () => {{
  const items = ref<{entity_pascal_name}[]>([]);
  const current = ref<{entity_pascal_name} | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchAll() {{
    loading.value = true;
    error.value = null;
    try {{
      const {{ data }} = await api.get<{entity_pascal_name}[]>('/{entity_plural_name}');
      items.value = data;
    }} catch (e) {{
      error.value = 'Error al cargar los datos.';
    }} finally {{
      loading.value = false;
    }}
  }}

  async function create(payload: Partial<{entity_pascal_name}>) {{
    const {{ data }} = await api.post<{entity_pascal_name}>('/{entity_plural_name}', payload);
    items.value.unshift(data);
    return data;
  }}

  async function update(id: string, payload: Partial<{entity_pascal_name}>) {{
    const {{ data }} = await api.patch<{entity_pascal_name}>(`/{entity_plural_name}/${{id}}`, payload);
    const idx = items.value.findIndex(i => i.id === id);
    if (idx !== -1) items.value[idx] = data;
    return data;
  }}

  async function remove(id: string) {{
    await api.delete(`/{entity_plural_name}/${{id}}`);
    items.value = items.value.filter(i => i.id !== id);
  }}

  return {{ items, current, loading, error, fetchAll, create, update, remove }};
}});
"""
    return GeneratedFile(path=f"src/stores/{entity_slug_name}Store.ts", language="typescript", content=content)


def _api_service() -> GeneratedFile:
    content = """\
import axios from 'axios';

export const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
});

// Interceptor: adjunta JWT si está guardado
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
"""
    return GeneratedFile(path="src/services/api.ts", language="typescript", content=content)


def _types_index(entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
export interface {entity_pascal_name} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt?: string;
  updatedAt?: string;
}}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _layout_vue(project_name: str, entity_slug_name: str, entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <header class="bg-indigo-600 text-white px-6 py-3 flex items-center gap-6 shadow">
      <router-link to="/" class="font-bold text-lg hover:opacity-80">{project_name}</router-link>
      <nav class="flex gap-4 text-sm">
        <router-link to="/{pluralize(entity_slug_name)}" class="hover:underline">{entity_pascal_name}s</router-link>
      </nav>
    </header>
    <main class="flex-1 container mx-auto px-4 py-8">
      <router-view />
    </main>
    <footer class="text-center text-xs text-gray-400 py-4">
      {project_name} © {{{{ year }}}}
    </footer>
  </div>
</template>

<script setup lang="ts">
import {{ computed }} from 'vue';
const year = computed(() => new Date().getFullYear());
</script>
"""
    return GeneratedFile(path="src/components/Layout.vue", language="vue", content=content)


def _home_page(project_name: str) -> GeneratedFile:
    content = f"""\
<template>
  <div class="max-w-xl mx-auto mt-20 text-center">
    <h1 class="text-4xl font-bold text-indigo-700 mb-4">{project_name}</h1>
    <p class="text-gray-600 text-lg mb-8">
      Tu proyecto Vue 3 está listo. Modifica esta página para empezar.
    </p>
    <router-link
      to="/"
      class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition"
    >
      Explorar
    </router-link>
  </div>
</template>
"""
    return GeneratedFile(path="src/pages/HomePage.vue", language="vue", content=content)


def _entity_list_page(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural_name: str) -> GeneratedFile:
    content = f"""\
<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">{entity_pascal_name}s</h2>
      <router-link
        to="/{entity_plural_name}/new"
        class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition text-sm"
      >
        + Nuevo
      </router-link>
    </div>

    <div v-if="store.loading" class="text-center text-gray-500 py-12">Cargando...</div>

    <div v-else-if="store.error" class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
      {{{{ store.error }}}}
    </div>

    <ul v-else class="divide-y divide-gray-200 bg-white shadow rounded-lg">
      <{entity_pascal_name}Card
        v-for="item in store.items"
        :key="item.id"
        :item="item"
        @delete="handleDelete"
      />
      <li v-if="store.items.length === 0" class="py-12 text-center text-gray-400">
        No hay {entity_plural_name} todavía. ¡Crea el primero!
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import {{ onMounted }} from 'vue';
import {{ use{entity_pascal_name}Store }} from '../stores/{entity_slug_name}Store';
import {entity_pascal_name}Card from '../components/{entity_pascal_name}Card.vue';

const store = use{entity_pascal_name}Store();

onMounted(() => store.fetchAll());

async function handleDelete(id: string) {{
  if (confirm('¿Eliminar este elemento?')) await store.remove(id);
}}
</script>
"""
    return GeneratedFile(path=f"src/pages/{entity_pascal_name}ListPage.vue", language="vue", content=content)


def _entity_form_page(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str) -> GeneratedFile:
    content = f"""\
<template>
  <div class="max-w-lg mx-auto">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">
      {{{{ isEdit ? 'Editar' : 'Nuevo' }}}} {entity_pascal_name}
    </h2>

    <form @submit.prevent="handleSubmit" class="bg-white shadow rounded-lg p-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
        <input
          v-model="form.name"
          type="text"
          required
          placeholder="Nombre del {entity_camel_name}"
          class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
        <textarea
          v-model="form.description"
          rows="3"
          placeholder="Descripción opcional"
          class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div class="flex gap-3 pt-2">
        <button
          type="submit"
          class="flex-1 bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition"
        >
          {{{{ isEdit ? 'Guardar cambios' : 'Crear' }}}}
        </button>
        <router-link
          to="/{pluralize(entity_slug_name)}"
          class="flex-1 text-center border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition"
        >
          Cancelar
        </router-link>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import {{ reactive, computed }} from 'vue';
import {{ useRoute, useRouter }} from 'vue-router';
import {{ use{entity_pascal_name}Store }} from '../stores/{entity_slug_name}Store';

const route = useRoute();
const router = useRouter();
const store = use{entity_pascal_name}Store();
const isEdit = computed(() => !!route.params.id);

const form = reactive({{ name: '', description: '' }});

async function handleSubmit() {{
  if (isEdit.value) {{
    await store.update(route.params.id as string, form);
  }} else {{
    await store.create(form);
  }}
  router.push('/{pluralize(entity_slug_name)}');
}}
</script>
"""
    return GeneratedFile(path=f"src/pages/{entity_pascal_name}FormPage.vue", language="vue", content=content)


def _entity_card(entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
<template>
  <li class="px-6 py-4 flex justify-between items-center hover:bg-gray-50">
    <div>
      <p class="font-medium text-gray-900">{{{{ item.name }}}}</p>
      <p v-if="item.description" class="text-sm text-gray-500">{{{{ item.description }}}}</p>
    </div>
    <div class="flex items-center gap-3">
      <span
        class="text-xs px-2 py-1 rounded-full"
        :class="item.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'"
      >
        {{{{ item.status ?? 'activo' }}}}
      </span>
      <button @click="$emit('delete', item.id)" class="text-red-500 hover:text-red-700 text-sm">
        Eliminar
      </button>
    </div>
  </li>
</template>

<script setup lang="ts">
import type {{ {entity_pascal_name} }} from '../types';

defineProps<{{ item: {entity_pascal_name} }}>();
defineEmits<{{ delete: [id: string] }}>();
</script>
"""
    return GeneratedFile(path=f"src/components/{entity_pascal_name}Card.vue", language="vue", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.env
*.local
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)


def entity_plural(entity_slug_name: str) -> str:
    """Helper local para las plantillas."""
    from app.agents.fallback.shared.entities import pluralize
    return pluralize(entity_slug_name)
