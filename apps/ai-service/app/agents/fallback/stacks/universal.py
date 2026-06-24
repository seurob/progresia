"""Universal fallback scaffold: React 19 + Vite + TypeScript + Tailwind CSS 4 (SPA, mock data).

Used when no specific stack can be detected. Includes clear README explaining how to add a backend.
"""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_universal(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold SPA universal con React 19 + Vite y datos mock."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))

    files: list[GeneratedFile] = [
        _package_json(project_slug),
        _tsconfig(),
        _vite_config(),
        _tailwind_config(),
        _postcss_config(),
        _index_html(req.project_name),
        _main_tsx(),
        _app_tsx(req.modules, entity_pascal_name),
        _home_page(req.project_name, req.modules),
        _item_list_page(entity_pascal_name, entity_camel_name),
        _item_detail_page(entity_pascal_name),
        _layout(req.project_name, req.modules),
        _mock_data(entity_pascal_name, entity_camel_name),
        _types(req.data_entities, req.modules),
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
                ("VITE_API_URL", "http://localhost:3000  # URL del backend cuando lo tengas"),
            ],
            api_port=5173,
            extra_sections=_backend_instructions(),
        ),
    ]
    return files


def _backend_instructions() -> str:
    return """\
## Cómo añadir un backend

Este scaffold incluye datos mock para que puedas ver la interfaz funcionando sin backend.
Cuando estés listo para conectar una API real, sigue estos pasos:

### Opción A: Express + Node.js (recomendado para principiantes)

```bash
mkdir api && cd api
npm init -y
npm install express cors dotenv
```

### Opción B: NestJS (recomendado para TypeScript avanzado)

```bash
npx @nestjs/cli new api
```

### Opción C: FastAPI (Python)

```bash
pip install fastapi uvicorn sqlmodel
uvicorn app.main:app --reload
```

Luego edita `src/lib/api.ts` y reemplaza los datos mock con llamadas reales a tu API.
"""


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0"
  }},
  "devDependencies": {{
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
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
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
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

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
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
        brand: { DEFAULT: "#6366f1", dark: "#4f46e5" },
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
  plugins: { "@tailwindcss/postcss": {} },
};
"""
    return GeneratedFile(path="postcss.config.js", language="javascript", content=content)


def _index_html(project_name: str) -> GeneratedFile:
    content = f"""\
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
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
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
"""
    return GeneratedFile(path="src/main.tsx", language="typescript", content=content)


def _app_tsx(modules: list[str], entity_pascal: str) -> GeneratedFile:
    content = """\
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import HomePage from "@/pages/HomePage";
import ItemListPage from "@/pages/ItemListPage";
import ItemDetailPage from "@/pages/ItemDetailPage";

// Configuración de rutas de la aplicación
// Usa datos mock hasta que conectes un backend real
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/items" element={<ItemListPage />} />
          <Route path="/items/:id" element={<ItemDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
"""
    return GeneratedFile(path="src/App.tsx", language="typescript", content=content)


def _home_page(project_name: str, modules: list[str]) -> GeneratedFile:
    links = "\n        ".join(
        f'<a href="/items" className="block rounded-xl border bg-white p-6 shadow-sm hover:shadow-md transition">'
        f'<h2 className="text-lg font-semibold">{m}</h2>'
        f'<p className="mt-1 text-sm text-gray-500">Ver {m.lower()}</p>'
        f"</a>"
        for m in modules[:6]
    )
    content = f"""\
// Página de inicio del proyecto
export default function HomePage() {{
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{project_name}</h1>
        <p className="mt-2 text-gray-500">MVP generado con ProgresIA Studio</p>
        <div className="mt-3 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          Actualmente usando datos mock. Conecta un backend para datos reales.
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {links}
      </div>
    </div>
  );
}}
"""
    return GeneratedFile(path="src/pages/HomePage.tsx", language="typescript", content=content)


def _item_list_page(entity_pascal: str, entity_camel: str) -> GeneratedFile:
    content = """\
import { useState } from "react";
import { Link } from "react-router-dom";
import { mockItems } from "@/data/mockData";
import type { Item } from "@/types";

// Página de listado con datos mock
// TODO: reemplazar mockItems con llamadas reales a la API
export default function ItemListPage() {
  const [items, setItems] = useState<Item[]>(mockItems);
  const [newName, setNewName] = useState("");

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    const newItem: Item = {
      id: crypto.randomUUID(),
      name: newName.trim(),
      description: null,
      status: "active",
      createdAt: new Date().toISOString(),
    };
    setItems((prev) => [newItem, ...prev]);
    setNewName("");
  }

  function handleDelete(id: string) {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold">Items</h1>

      <form onSubmit={handleCreate} className="mb-6 flex gap-2">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Nombre del nuevo elemento..."
          className="flex-1 rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
        />
        <button
          type="submit"
          className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
        >
          Añadir
        </button>
      </form>

      <ul className="grid gap-2">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex items-center justify-between rounded-xl border bg-white px-4 py-3"
          >
            <div>
              <Link
                to={`/items/${item.id}`}
                className="font-medium hover:text-brand hover:underline"
              >
                {item.name}
              </Link>
              {item.description && (
                <p className="text-sm text-gray-500">{item.description}</p>
              )}
            </div>
            <button
              onClick={() => handleDelete(item.id)}
              className="text-sm text-red-500 hover:underline"
            >
              Eliminar
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
"""
    return GeneratedFile(path="src/pages/ItemListPage.tsx", language="typescript", content=content)


def _item_detail_page(entity_pascal: str) -> GeneratedFile:
    content = """\
import { useParams, Link } from "react-router-dom";
import { mockItems } from "@/data/mockData";

// Página de detalle con datos mock
export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const item = mockItems.find((i) => i.id === id);

  if (!item) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Elemento no encontrado</p>
        <Link to="/items" className="mt-4 inline-block text-brand hover:underline">
          Volver a la lista
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-lg">
      <Link to="/items" className="text-sm text-brand hover:underline mb-4 inline-block">
        ← Volver a la lista
      </Link>
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold mb-4">{item.name}</h1>
        {item.description && (
          <p className="text-gray-600 mb-4">{item.description}</p>
        )}
        <div className="text-sm text-gray-400 space-y-1">
          <p>ID: {item.id}</p>
          <p>Estado: {item.status}</p>
          <p>Creado: {new Date(item.createdAt).toLocaleDateString("es")}</p>
        </div>
      </div>
    </div>
  );
}
"""
    return GeneratedFile(path="src/pages/ItemDetailPage.tsx", language="typescript", content=content)


def _layout(project_name: str, modules: list[str]) -> GeneratedFile:
    nav_links = "\n          ".join(
        f'<a href="/items" className="text-sm text-gray-600 hover:text-brand">{m}</a>'
        for m in modules[:5]
    )
    content = f"""\
import {{ Outlet }} from "react-router-dom";

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


def _mock_data(entity_pascal: str, entity_camel: str) -> GeneratedFile:
    content = f"""\
// Datos mock para desarrollo sin backend
// Reemplaza estos datos con llamadas reales a la API cuando tengas un backend

import type {{ Item }} from "@/types";

export const mockItems: Item[] = [
  {{
    id: "mock-1",
    name: "{entity_pascal} de ejemplo 1",
    description: "Descripción del primer elemento de ejemplo",
    status: "active",
    createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
  }},
  {{
    id: "mock-2",
    name: "{entity_pascal} de ejemplo 2",
    description: "Descripción del segundo elemento de ejemplo",
    status: "active",
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  }},
  {{
    id: "mock-3",
    name: "{entity_pascal} de ejemplo 3",
    description: null,
    status: "inactive",
    createdAt: new Date().toISOString(),
  }},
];
"""
    return GeneratedFile(path="src/data/mockData.ts", language="typescript", content=content)


def _types(data_entities: list[dict], modules: list[str]) -> GeneratedFile:
    content = """\
// Tipos TypeScript del proyecto

// Tipo genérico Item — reemplaza con tus tipos específicos
export interface Item {
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt: string;
}
"""
    if data_entities:
        for entity in data_entities[:6]:
            entity_name = pascal(entity.get("name", "Item"))
            if entity_name != "Item":
                content += f"""\

export interface {entity_name} {{
  id: string;
  name: string;
  description?: string | null;
  createdAt: string;
}}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _env_example() -> GeneratedFile:
    content = """\
# URL del backend API (configura cuando tengas un backend)
VITE_API_URL=http://localhost:3000
"""
    return GeneratedFile(path=".env.example", language="env", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.env
.env.local
*.log
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
