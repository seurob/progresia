"""React 19 + Vite + TypeScript + Tailwind CSS 4 + React Router scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_react_vite(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold React 19 + Vite SPA."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal = pascal(primary.get("name", "Item"))
    entity_camel = camel(primary.get("name", "Item"))
    entity_slug = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug)

    files: list[GeneratedFile] = [
        _package_json(project_slug),
        _tsconfig(),
        _vite_config(),
        _tailwind_config(),
        _postcss_config(),
        _index_html(req.project_name),
        _main_tsx(),
        _app_tsx(req.modules, entity_plural, entity_pascal),
        _home_page(req.project_name, req.modules),
        _entity_list_page(entity_pascal, entity_camel, entity_plural, entity_slug),
        _entity_form_page(entity_pascal, entity_camel, entity_plural),
        _layout(req.project_name, req.modules),
        _entity_card(entity_pascal),
        _api_lib(project_slug),
        _types(req.data_entities, req.modules),
        _mock_data(entity_pascal, entity_camel),
        _env_example(),
        _gitignore(),
        generate_readme(
            req,
            stack_summary="React 19 · Vite · TypeScript · Tailwind CSS 4",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Git 2.x — https://git-scm.com",
            ],
            setup_commands=[
                "npm install",
                "npm run dev",
            ],
            env_vars=[
                ("VITE_API_URL", "http://localhost:3000"),
            ],
            api_port=5173,
        ),
    ]
    return files


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint ."
  }},
  "dependencies": {{
    "axios": "^1.7.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-hook-form": "^7.54.0",
    "react-router-dom": "^7.0.0",
    "zod": "^3.23.0"
  }},
  "devDependencies": {{
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.7.0",
    "vite": "^6.0.0"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _vite_config() -> GeneratedFile:
    content = """\
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    // Proxy las peticiones API al backend
    proxy: {
      "/api": {
        target: process.env.VITE_API_URL ?? "http://localhost:3000",
        changeOrigin: true,
      },
    },
  },
});
"""
    return GeneratedFile(path="vite.config.ts", language="typescript", content=content)


def _tailwind_config() -> GeneratedFile:
    content = """\
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#6366f1",
          dark: "#4f46e5",
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
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
"""
    return GeneratedFile(path="postcss.config.js", language="javascript", content=content)


def _index_html(project_name: str) -> GeneratedFile:
    content = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
    return GeneratedFile(path="index.html", language="html", content=content)


def _main_tsx() -> GeneratedFile:
    content = """\
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

// Punto de entrada de la aplicación React
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
"""
    return GeneratedFile(path="src/main.tsx", language="typescript", content=content)


def _app_tsx(modules: list[str], entity_plural: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
import {{ BrowserRouter as Router, Routes, Route }} from "react-router-dom";
import Layout from "@/components/Layout";
import HomePage from "@/pages/HomePage";
import {entity_pascal}ListPage from "@/pages/{entity_pascal}ListPage";
import {entity_pascal}FormPage from "@/pages/{entity_pascal}FormPage";

// Configuración de rutas de la aplicación
function App() {{
  return (
    <Router>
      <Routes>
        <Route element={{<Layout />}}>
          <Route path="/" element={{<HomePage />}} />
          <Route path="/{entity_plural}" element={{<{entity_pascal}ListPage />}} />
          <Route path="/{entity_plural}/nuevo" element={{<{entity_pascal}FormPage />}} />
          <Route path="/{entity_plural}/:id/editar" element={{<{entity_pascal}FormPage />}} />
        </Route>
      </Routes>
    </Router>
  );
}}

export default App;
"""
    return GeneratedFile(path="src/App.tsx", language="typescript", content=content)


def _home_page(project_name: str, modules: list[str]) -> GeneratedFile:
    links = "\n        ".join(
        f'<a href="/{slug(m)}s" className="block rounded-xl border bg-white p-6 shadow-sm hover:shadow-md transition-all">'
        f'<h2 className="text-lg font-semibold">{m}</h2>'
        f'<p className="mt-1 text-sm text-gray-500">Ver todos los {m.lower()}</p>'
        f"</a>"
        for m in modules[:6]
    )
    content = f"""\
// Página de inicio
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
    return GeneratedFile(path="src/pages/HomePage.tsx", language="typescript", content=content)


def _entity_list_page(entity_pascal: str, entity_camel: str, entity_plural: str, entity_slug: str) -> GeneratedFile:
    content = f"""\
import {{ useState, useEffect }} from "react";
import {{ Link }} from "react-router-dom";
import {{ api }} from "@/lib/api";
import {entity_pascal}Card from "@/components/{entity_pascal}Card";
import type {{ {entity_pascal} }} from "@/types";

// Página de listado de {entity_pascal}
export default function {entity_pascal}ListPage() {{
  const [items, setItems] = useState<{entity_pascal}[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {{
    api
      .get<{entity_pascal}[]>("/{entity_plural}")
      .then((res) => setItems(res.data))
      .catch(() => setError("No se pudieron cargar los datos. ¿Está activo el backend?"))
      .finally(() => setLoading(false));
  }}, []);

  async function handleDelete(id: string) {{
    if (!confirm("¿Eliminar este elemento?")) return;
    await api.delete(`/{entity_plural}/${{id}}`);
    setItems((prev) => prev.filter((item) => item.id !== id));
  }}

  if (loading) return <p className="text-gray-500">Cargando...</p>;
  if (error) return <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-amber-800">{{error}}</div>;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{entity_pascal}</h1>
        <Link
          to="/{entity_plural}/nuevo"
          className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
        >
          Nuevo
        </Link>
      </div>

      {{items.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <p>No hay {entity_camel}s todavía.</p>
          <Link to="/{entity_plural}/nuevo" className="mt-2 inline-block text-brand hover:underline">
            Crear el primero
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {{items.map((item) => (
            <{entity_pascal}Card key={{item.id}} item={{item}} onDelete={{handleDelete}} />
          ))}}
        </div>
      )}}
    </div>
  );
}}
"""
    return GeneratedFile(path=f"src/pages/{entity_pascal}ListPage.tsx", language="typescript", content=content)


def _entity_form_page(entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ useForm }} from "react-hook-form";
import {{ zodResolver }} from "@hookform/resolvers/zod";
import {{ z }} from "zod";
import {{ useNavigate, useParams }} from "react-router-dom";
import {{ api }} from "@/lib/api";

// Esquema de validación con Zod
const schema = z.object({{
  name: z.string().min(1, "El nombre es obligatorio").max(200),
  description: z.string().max(1000).optional(),
}});

type FormData = z.infer<typeof schema>;

// Formulario para crear o editar {entity_pascal}
export default function {entity_pascal}FormPage() {{
  const navigate = useNavigate();
  const {{ id }} = useParams();
  const isEditing = !!id;

  const {{
    register,
    handleSubmit,
    formState: {{ errors, isSubmitting }},
  }} = useForm<FormData>({{
    resolver: zodResolver(schema),
  }});

  async function onSubmit(data: FormData) {{
    if (isEditing) {{
      await api.put(`/{entity_plural}/${{id}}`, data);
    }} else {{
      await api.post("/{entity_plural}", data);
    }}
    navigate("/{entity_plural}");
  }}

  return (
    <div className="max-w-lg">
      <h1 className="mb-6 text-2xl font-bold">
        {{isEditing ? "Editar" : "Nuevo"}} {entity_pascal}
      </h1>

      <form onSubmit={{handleSubmit(onSubmit)}} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Nombre</label>
          <input
            {{...register("name")}}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
          {{errors.name && (
            <p className="mt-1 text-sm text-red-500">{{errors.name.message}}</p>
          )}}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Descripción</label>
          <textarea
            {{...register("description")}}
            rows={{3}}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={{isSubmitting}}
            className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {{isSubmitting ? "Guardando..." : "Guardar"}}
          </button>
          <button
            type="button"
            onClick={{() => navigate("/{entity_plural}")}}
            className="rounded-lg border px-4 py-2 text-sm hover:bg-gray-50"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}}
"""
    return GeneratedFile(path=f"src/pages/{entity_pascal}FormPage.tsx", language="typescript", content=content)


def _layout(project_name: str, modules: list[str]) -> GeneratedFile:
    nav_links = "\n          ".join(
        f'<a href="/{slug(m)}s" className="text-sm text-gray-600 hover:text-brand">{m}</a>'
        for m in modules[:5]
    )
    content = f"""\
import {{ Outlet }} from "react-router-dom";

// Layout principal con navegación
export default function Layout() {{
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="border-b bg-white px-6 py-3 shadow-sm">
        <div className="container mx-auto flex max-w-6xl items-center justify-between">
          <a href="/" className="text-lg font-bold text-brand">{project_name}</a>
          <div className="flex gap-6">
            {nav_links}
          </div>
        </div>
      </nav>
      <main className="container mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}}
"""
    return GeneratedFile(path="src/components/Layout.tsx", language="typescript", content=content)


def _entity_card(entity_pascal: str) -> GeneratedFile:
    content = f"""\
import type {{ {entity_pascal} }} from "@/types";

interface Props {{
  item: {entity_pascal};
  onDelete: (id: string) => void;
}}

// Tarjeta para mostrar un elemento {entity_pascal}
export default function {entity_pascal}Card({{ item, onDelete }}: Props) {{
  return (
    <div className="flex items-center justify-between rounded-xl border bg-white px-4 py-3 shadow-sm">
      <div>
        <p className="font-medium text-gray-900">{{item.name}}</p>
        {{item.description && (
          <p className="text-sm text-gray-500">{{item.description}}</p>
        )}}
      </div>
      <button
        onClick={{() => onDelete(item.id)}}
        className="text-sm text-red-500 hover:underline"
      >
        Eliminar
      </button>
    </div>
  );
}}
"""
    return GeneratedFile(path=f"src/components/{entity_pascal}Card.tsx", language="typescript", content=content)


def _api_lib(project_slug: str) -> GeneratedFile:
    content = """\
import axios from "axios";

// Instancia de Axios configurada para la API del backend
// La URL base se configura con la variable de entorno VITE_API_URL
export const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL ?? "http://localhost:3000") + "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10_000,
});

// Interceptor para manejar errores de forma centralizada
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirigir al login si la sesión expiró
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
"""
    return GeneratedFile(path="src/lib/api.ts", language="typescript", content=content)


def _types(data_entities: list[dict], modules: list[str]) -> GeneratedFile:
    if data_entities:
        type_blocks = []
        for entity in data_entities[:8]:
            entity_name = pascal(entity.get("name", "Item"))
            type_blocks.append(f"""\
export interface {entity_name} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt: string;
  updatedAt: string;
}}""")
        types_content = "\n\n".join(type_blocks)
    else:
        types_content = "\n\n".join(
            f"""\
export interface {pascal(m)} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt: string;
  updatedAt: string;
}}"""
            for m in modules[:5]
        )

    content = f"""\
// Tipos TypeScript generados desde las entidades del proyecto

{types_content}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _mock_data(entity_pascal: str, entity_camel: str) -> GeneratedFile:
    content = f"""\
// Datos de ejemplo para desarrollo sin backend
// Estos datos se usan cuando VITE_API_URL no está configurado

import type {{ {entity_pascal} }} from "@/types";

export const mock{entity_pascal}s: {entity_pascal}[] = [
  {{
    id: "1",
    name: "{entity_pascal} de ejemplo 1",
    description: "Descripción del primer elemento de ejemplo",
    status: "active",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }},
  {{
    id: "2",
    name: "{entity_pascal} de ejemplo 2",
    description: "Descripción del segundo elemento de ejemplo",
    status: "active",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }},
  {{
    id: "3",
    name: "{entity_pascal} de ejemplo 3",
    description: null,
    status: "inactive",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }},
];
"""
    return GeneratedFile(path="src/data/mockData.ts", language="typescript", content=content)


def _env_example() -> GeneratedFile:
    content = """\
# URL del backend API
VITE_API_URL=http://localhost:3000
"""
    return GeneratedFile(path=".env.example", language="env", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.env
.env.local
.DS_Store
*.log
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
