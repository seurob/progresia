"""Electron + React 19 + Vite + TypeScript + SQLite scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_desktop(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold de app de escritorio con Electron + React."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    files: list[GeneratedFile] = [
        _package_json(project_slug),
        _tsconfig(),
        _vite_config(),
        _electron_main(project_slug, entity_camel_name, entity_plural),
        _electron_preload(),
        _index_html(req.project_name),
        _app_tsx(req.project_name, req.modules, entity_pascal_name, entity_plural),
        _home_page(req.project_name),
        _entity_page(entity_pascal_name, entity_camel_name, entity_plural),
        _layout(req.project_name, req.modules),
        _api_lib(),
        _types_index(req.modules, req.data_entities),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content="# Variables de entorno — copia este archivo a .env y completa los valores\n\n# Nombre de la aplicación\nAPP_NAME=" + req.project_name + "\n\n# Entorno: development | production\nNODE_ENV=development\n",
        ),
        generate_readme(
            req,
            stack_summary="Electron · React 19 · Vite · TypeScript · SQLite",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Git 2.x — https://git-scm.com",
            ],
            setup_commands=[
                "npm install",
                "npm run dev",
            ],
            env_vars=[],
            api_port=3000,
        ),
    ]
    return files


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "1.0.0",
  "main": "dist-electron/main.js",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build && electron-builder",
    "electron:dev": "concurrently \\"vite\\" \\"wait-on tcp:5173 && electron .\\"",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "better-sqlite3": "^9.6.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0"
  }},
  "devDependencies": {{
    "@types/better-sqlite3": "^7.6.12",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "concurrently": "^9.0.0",
    "electron": "^33.0.0",
    "electron-builder": "^25.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "vite-plugin-electron": "^0.28.0",
    "wait-on": "^8.0.0"
  }},
  "build": {{
    "appId": "com.example.{project_slug.replace('-', '')}",
    "productName": "{project_slug.replace('-', ' ').title()}",
    "directories": {{
      "output": "release"
    }},
    "files": ["dist/**/*", "dist-electron/**/*"]
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
  "include": ["src", "electron"]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _vite_config() -> GeneratedFile:
    content = """\
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  base: "./",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
"""
    return GeneratedFile(path="vite.config.ts", language="typescript", content=content)


def _electron_main(project_slug: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ app, BrowserWindow, ipcMain }} from "electron";
import path from "path";
import Database from "better-sqlite3";

// Ruta a la base de datos SQLite (en el directorio de datos del usuario)
const DB_PATH = path.join(app.getPath("userData"), "{project_slug}.db");

// Inicializar la base de datos
function initDB() {{
  const db = new Database(DB_PATH);
  db.exec(`
    CREATE TABLE IF NOT EXISTS {entity_plural} (
      id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
      name TEXT NOT NULL,
      description TEXT,
      status TEXT DEFAULT 'active',
      createdAt TEXT DEFAULT (datetime('now')),
      updatedAt TEXT DEFAULT (datetime('now'))
    )
  `);
  return db;
}}

const db = initDB();

// Manejadores IPC para comunicación con el renderer
ipcMain.handle("{entity_plural}:findAll", () => {{
  return db.prepare("SELECT * FROM {entity_plural} ORDER BY createdAt DESC").all();
}});

ipcMain.handle("{entity_plural}:create", (_event, data: {{ name: string; description?: string }}) => {{
  const stmt = db.prepare("INSERT INTO {entity_plural} (name, description) VALUES (?, ?) RETURNING *");
  return stmt.get(data.name, data.description ?? null);
}});

ipcMain.handle("{entity_plural}:delete", (_event, id: string) => {{
  db.prepare("DELETE FROM {entity_plural} WHERE id = ?").run(id);
  return {{ success: true }};
}});

// Crear la ventana principal
function createWindow() {{
  const win = new BrowserWindow({{
    width: 1200,
    height: 800,
    webPreferences: {{
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    }},
    title: "{project_slug.replace('-', ' ').title()}",
  }});

  // En desarrollo carga desde Vite, en producción desde los archivos compilados
  if (process.env.NODE_ENV === "development") {{
    win.loadURL("http://localhost:5173");
    win.webContents.openDevTools();
  }} else {{
    win.loadFile(path.join(__dirname, "../dist/index.html"));
  }}
}}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {{
  if (process.platform !== "darwin") app.quit();
}});

app.on("activate", () => {{
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
}});
"""
    return GeneratedFile(path="electron/main.ts", language="typescript", content=content)


def _electron_preload() -> GeneratedFile:
    content = """\
import { contextBridge, ipcRenderer } from "electron";

// Expone la API de Electron al renderer de forma segura vía contextBridge
// El renderer accede a esto como window.electronAPI
contextBridge.exposeInMainWorld("electronAPI", {
  // Ejemplo de API para items
  findAll: (table: string) => ipcRenderer.invoke(`${table}:findAll`),
  create: (table: string, data: unknown) => ipcRenderer.invoke(`${table}:create`, data),
  delete: (table: string, id: string) => ipcRenderer.invoke(`${table}:delete`, id),
});
"""
    return GeneratedFile(path="electron/preload.ts", language="typescript", content=content)


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


def _app_tsx(project_name: str, modules: list[str], entity_pascal: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ BrowserRouter, Routes, Route }} from "react-router-dom";
import Layout from "@/components/Layout";
import HomePage from "@/pages/HomePage";
import {entity_pascal}Page from "@/pages/{entity_pascal}Page";

function App() {{
  return (
    <BrowserRouter>
      <Routes>
        <Route element={{<Layout />}}>
          <Route path="/" element={{<HomePage />}} />
          <Route path="/{entity_plural}" element={{<{entity_pascal}Page />}} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}}

export default App;
"""
    return GeneratedFile(path="src/App.tsx", language="typescript", content=content)


def _home_page(project_name: str) -> GeneratedFile:
    content = f"""\
export default function HomePage() {{
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold">{project_name}</h1>
      <p className="mt-2 text-gray-500">App de escritorio generada con ProgresIA Studio</p>
    </div>
  );
}}
"""
    return GeneratedFile(path="src/pages/HomePage.tsx", language="typescript", content=content)


def _entity_page(entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ useState, useEffect }} from "react";
import {{ api }} from "@/lib/api";
import type {{ {entity_pascal} }} from "@/types";

// Página de gestión de {entity_pascal}
export default function {entity_pascal}Page() {{
  const [items, setItems] = useState<{entity_pascal}[]>([]);
  const [newName, setNewName] = useState("");

  useEffect(() => {{
    api.findAll("{entity_plural}").then(setItems);
  }}, []);

  async function handleCreate(e: React.FormEvent) {{
    e.preventDefault();
    if (!newName.trim()) return;
    const item = await api.create("{entity_plural}", {{ name: newName.trim() }});
    setItems((prev) => [item, ...prev]);
    setNewName("");
  }}

  async function handleDelete(id: string) {{
    await api.delete("{entity_plural}", id);
    setItems((prev) => prev.filter((i) => i.id !== id));
  }}

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">{entity_pascal}</h1>

      <form onSubmit={{handleCreate}} className="flex gap-2 mb-6">
        <input
          value={{newName}}
          onChange={{(e) => setNewName(e.target.value)}}
          placeholder="Nuevo nombre..."
          className="flex-1 border rounded px-3 py-2"
        />
        <button type="submit" className="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600">
          Añadir
        </button>
      </form>

      <ul className="space-y-2">
        {{items.map((item) => (
          <li key={{item.id}} className="flex items-center justify-between bg-white border rounded p-3">
            <span>{{item.name}}</span>
            <button
              onClick={{() => handleDelete(item.id)}}
              className="text-red-500 text-sm hover:underline"
            >
              Eliminar
            </button>
          </li>
        ))}}
      </ul>
    </div>
  );
}}
"""
    return GeneratedFile(path=f"src/pages/{entity_pascal}Page.tsx", language="typescript", content=content)


def _layout(project_name: str, modules: list[str]) -> GeneratedFile:
    nav_items = "\n          ".join(
        f'<a href="/{slug(m)}s" className="text-sm hover:text-indigo-500">{m}</a>'
        for m in modules[:5]
    )
    content = f"""\
import {{ Outlet, Link }} from "react-router-dom";

// Layout principal con barra lateral
export default function Layout() {{
  return (
    <div className="flex h-screen bg-gray-100">
      <aside className="w-56 bg-white border-r flex flex-col">
        <div className="px-4 py-5 border-b">
          <span className="font-bold text-indigo-600">{project_name}</span>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          <Link to="/" className="text-sm px-3 py-2 rounded hover:bg-gray-100">Inicio</Link>
          {nav_items}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}}
"""
    return GeneratedFile(path="src/components/Layout.tsx", language="typescript", content=content)


def _api_lib() -> GeneratedFile:
    content = """\
// Abstracción sobre window.electronAPI para usar desde los componentes React
// En el renderer process, los datos provienen de IPC handlers en el proceso main

declare global {
  interface Window {
    electronAPI: {
      findAll: (table: string) => Promise<unknown[]>;
      create: (table: string, data: unknown) => Promise<unknown>;
      delete: (table: string, id: string) => Promise<{ success: boolean }>;
    };
  }
}

export const api = {
  findAll: <T>(table: string): Promise<T[]> =>
    window.electronAPI.findAll(table) as Promise<T[]>,

  create: <T>(table: string, data: unknown): Promise<T> =>
    window.electronAPI.create(table, data) as Promise<T>,

  delete: (table: string, id: string) => window.electronAPI.delete(table, id),
};
"""
    return GeneratedFile(path="src/lib/api.ts", language="typescript", content=content)


def _types_index(modules: list[str], data_entities: list[dict]) -> GeneratedFile:
    if data_entities:
        type_defs = "\n\n".join(
            f"""\
export interface {pascal(e.get("name", "Item"))} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt: string;
}}"""
            for e in data_entities[:6]
        )
    else:
        type_defs = "\n\n".join(
            f"""\
export interface {pascal(m)} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt: string;
}}"""
            for m in modules[:4]
        )
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=type_defs + "\n")


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
dist-electron/
release/
.env
*.log
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
