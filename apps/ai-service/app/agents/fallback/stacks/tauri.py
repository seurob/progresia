"""Tauri 2 + React 19 + Vite + TypeScript scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_tauri(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Tauri 2 con frontend React y comandos Rust."""
    project_slug = slug(req.project_name)
    project_id = project_slug.replace("-", "_")
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    return [
        _package_json(project_slug),
        _tsconfig(),
        _vite_config(project_id),
        _tailwind_config(),
        _postcss_config(),
        _index_html(req.project_name),
        _main_tsx(),
        _app_tsx(req.project_name, entity_slug_name, entity_pascal_name, entity_plural),
        _layout(req.project_name, entity_slug_name, entity_pascal_name, entity_plural),
        _home_page(req.project_name),
        _entity_page(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _tauri_lib(entity_slug_name, entity_pascal_name, entity_plural),
        _types_index(entity_pascal_name),
        _cargo_toml(project_id, req.project_name),
        _tauri_conf(project_slug, project_id, req.project_name),
        _main_rs(project_id),
        _lib_rs(entity_pascal_name, entity_camel_name, entity_slug_name, entity_plural),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Variables de entorno para Tauri\n\n"
                "# Modo de Rust (debug | release)\n"
                "TAURI_RUST_BUILD=debug\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Tauri 2 · React 19 · Vite · TypeScript · Rust · Tailwind CSS",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Rust (via rustup) — https://rustup.rs",
                "Prerrequisitos Tauri — https://tauri.app/start/prerequisites/",
            ],
            setup_commands=[
                "npm install",
                "npm run tauri dev     # arranca la app de escritorio en modo desarrollo",
                "# Para construir el instalador:",
                "npm run tauri build",
            ],
            env_vars=[],
            api_port=1420,
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
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri",
    "tauri dev": "tauri dev",
    "tauri build": "tauri build"
  }},
  "dependencies": {{
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/plugin-opener": "^2.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^6.24.0"
  }},
  "devDependencies": {{
    "@tauri-apps/cli": "^2.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.5.2",
    "vite": "^5.3.1"
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
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src"]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _vite_config(project_id: str) -> GeneratedFile:
    content = f"""\
import {{ defineConfig }} from "vite";
import react from "@vitejs/plugin-react";

// Tauri espera un puerto fijo en desarrollo
const host = process.env.TAURI_DEV_HOST;

export default defineConfig(async () => ({{
  plugins: [react()],
  clearScreen: false,
  server: {{
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {{ protocol: "ws", host, port: 1421 }}
      : undefined,
    watch: {{ ignored: ["**/src-tauri/**"] }},
  }},
}}));
"""
    return GeneratedFile(path="vite.config.ts", language="typescript", content=content)


def _tailwind_config() -> GeneratedFile:
    content = """\
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
};
"""
    return GeneratedFile(path="tailwind.config.ts", language="typescript", content=content)


def _postcss_config() -> GeneratedFile:
    return GeneratedFile(
        path="postcss.config.js", language="javascript",
        content="export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n"
    )


def _index_html(project_name: str) -> GeneratedFile:
    content = f"""\
<!DOCTYPE html>
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
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
"""
    return GeneratedFile(path="src/main.tsx", language="tsx", content=content)


def _app_tsx(project_name: str, entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ Routes, Route }} from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import {entity_pascal_name}Page from './pages/{entity_pascal_name}Page';

export default function App() {{
  return (
    <Layout>
      <Routes>
        <Route path="/" element={{<HomePage />}} />
        <Route path="/{entity_plural}" element={{<{entity_pascal_name}Page />}} />
      </Routes>
    </Layout>
  );
}}
"""
    return GeneratedFile(path="src/App.tsx", language="tsx", content=content)


def _layout(project_name: str, entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ Link, useLocation }} from 'react-router-dom';

export default function Layout({{ children }}: {{ children: React.ReactNode }}) {{
  const {{ pathname }} = useLocation();

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
        <Link to="/" className="font-bold text-lg text-violet-400 hover:text-violet-300">
          {project_name}
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link
            to="/{entity_plural}"
            className={{`hover:text-white transition ${{pathname === '/{entity_plural}' ? 'text-white' : 'text-gray-400'}}`}}
          >
            {entity_pascal_name}s
          </Link>
        </nav>
        <span className="ml-auto text-xs text-gray-600">App de escritorio</span>
      </header>
      <main className="flex-1 container mx-auto px-6 py-8">{{children}}</main>
    </div>
  );
}}
"""
    return GeneratedFile(path="src/components/Layout.tsx", language="tsx", content=content)


def _home_page(project_name: str) -> GeneratedFile:
    content = f"""\
import {{ invoke }} from '@tauri-apps/api/core';
import {{ useState }} from 'react';

export default function HomePage() {{
  const [greeting, setGreeting] = useState<string>('');

  async function handleGreet() {{
    const msg = await invoke<string>('greet', {{ name: '{project_name}' }});
    setGreeting(msg);
  }}

  return (
    <div className="max-w-xl mx-auto mt-20 text-center">
      <h1 className="text-4xl font-bold text-violet-400 mb-4">{project_name}</h1>
      <p className="text-gray-400 text-lg mb-8">
        App de escritorio Tauri + React. El botón llama a un comando Rust.
      </p>
      <button
        onClick={{handleGreet}}
        className="bg-violet-600 text-white px-6 py-2 rounded-lg hover:bg-violet-700 transition"
      >
        Saludar desde Rust
      </button>
      {{greeting && (
        <p className="mt-6 text-green-400 font-mono">{{greeting}}</p>
      )}}
    </div>
  );
}}
"""
    return GeneratedFile(path="src/pages/HomePage.tsx", language="tsx", content=content)


def _entity_page(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ useEffect, useState }} from 'react';
import {{ get{entity_pascal_name}s, create{entity_pascal_name} }} from '../lib/tauri';
import type {{ {entity_pascal_name} }} from '../types';

export default function {entity_pascal_name}Page() {{
  const [items, setItems] = useState<{entity_pascal_name}[]>([]);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    get{entity_pascal_name}s().then(data => {{ setItems(data); setLoading(false); }});
  }}, []);

  async function handleCreate(e: React.FormEvent) {{
    e.preventDefault();
    if (!name.trim()) return;
    const item = await create{entity_pascal_name}({{ name }});
    setItems(prev => [item, ...prev]);
    setName('');
  }}

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-white mb-6">{entity_pascal_name}s</h2>

      <form onSubmit={{handleCreate}} className="flex gap-3 mb-8">
        <input
          value={{name}}
          onChange={{e => setName(e.target.value)}}
          placeholder="Nombre del {entity_camel_name}..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-violet-500 outline-none"
        />
        <button
          type="submit"
          className="bg-violet-600 text-white px-5 py-2 rounded-lg hover:bg-violet-700 transition"
        >
          Crear
        </button>
      </form>

      {{loading ? (
        <p className="text-gray-500 text-center py-8">Cargando...</p>
      ) : (
        <ul className="space-y-2">
          {{items.map(item => (
            <li key={{item.id}} className="bg-gray-900 border border-gray-800 rounded-lg px-5 py-3 flex justify-between">
              <span className="font-medium">{{item.name}}</span>
              <span className="text-xs text-gray-500 self-center">{{item.status}}</span>
            </li>
          ))}}
          {{items.length === 0 && (
            <li className="text-center text-gray-600 py-8">No hay {entity_plural} todavía.</li>
          )}}
        </ul>
      )}}
    </div>
  );
}}
"""
    return GeneratedFile(path=f"src/pages/{entity_pascal_name}Page.tsx", language="tsx", content=content)


def _tauri_lib(entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ invoke }} from '@tauri-apps/api/core';
import type {{ {entity_pascal_name} }} from '../types';

// Wrappers tipados sobre los comandos Rust de Tauri

export async function get{entity_pascal_name}s(): Promise<{entity_pascal_name}[]> {{
  return invoke<{entity_pascal_name}[]>('get_{entity_plural}');
}}

export async function create{entity_pascal_name}(data: {{ name: string; description?: string }}): Promise<{entity_pascal_name}> {{
  return invoke<{entity_pascal_name}>('create_{entity_slug_name}', {{ payload: data }});
}}

export async function delete{entity_pascal_name}(id: string): Promise<void> {{
  return invoke('delete_{entity_slug_name}', {{ id }});
}}

export async function greet(name: string): Promise<string> {{
  return invoke<string>('greet', {{ name }});
}}
"""
    return GeneratedFile(path="src/lib/tauri.ts", language="typescript", content=content)


def _types_index(entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
export interface {entity_pascal_name} {{
  id: string;
  name: string;
  description?: string | null;
  status: string;
  created_at?: string;
}}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _cargo_toml(project_id: str, project_name: str) -> GeneratedFile:
    content = f"""\
[package]
name = "{project_id}"
version = "0.1.0"
description = "{project_name} — app de escritorio Tauri"
authors = ["Tu Nombre <tu@email.com>"]
license = ""
repository = ""
default-run = "{project_id}"
edition = "2021"
rust-version = "1.77.2"

[build-dependencies]
tauri-build = {{ version = "2", features = [] }}

[dependencies]
tauri = {{ version = "2", features = [] }}
tauri-plugin-opener = "2"
serde = {{ version = "1", features = ["derive"] }}
serde_json = "1"
uuid = {{ version = "1", features = ["v4"] }}
chrono = {{ version = "0.4", features = ["serde"] }}

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
"""
    return GeneratedFile(path="src-tauri/Cargo.toml", language="toml", content=content)


def _tauri_conf(project_slug: str, project_id: str, project_name: str) -> GeneratedFile:
    content = f"""\
{{
  "productName": "{project_name}",
  "version": "0.1.0",
  "identifier": "com.progresia.{project_id}",
  "build": {{
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:1420",
    "frontendDist": "../dist"
  }},
  "app": {{
    "windows": [
      {{
        "label": "main",
        "title": "{project_name}",
        "width": 1200,
        "height": 750,
        "resizable": true,
        "fullscreen": false
      }}
    ],
    "security": {{
      "csp": null
    }}
  }},
  "bundle": {{
    "active": true,
    "targets": "all",
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.icns", "icons/icon.ico"]
  }}
}}
"""
    return GeneratedFile(path="src-tauri/tauri.conf.json", language="json", content=content)


def _main_rs(project_id: str) -> GeneratedFile:
    content = f"""\
// Previene que aparezca una consola extra en Windows al lanzar la app
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {{
    {project_id}_lib::run();
}}
"""
    return GeneratedFile(path="src-tauri/src/main.rs", language="rust", content=content)


def _lib_rs(entity_pascal_name: str, entity_camel_name: str, entity_slug_name: str, entity_plural: str) -> GeneratedFile:
    entity_rust = entity_pascal_name  # PascalCase en Rust
    content = f"""\
use serde::{{Deserialize, Serialize}};
use std::sync::Mutex;
use tauri::State;

// ── Modelo de datos ───────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct {entity_rust} {{
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub status: String,
    pub created_at: String,
}}

#[derive(Debug, Deserialize)]
pub struct Create{entity_rust}Payload {{
    pub name: String,
    pub description: Option<String>,
}}

// Estado compartido entre comandos (en memoria — para persistencia usa SQLite con tauri-plugin-sql)
pub struct AppState {{
    pub {entity_plural}: Mutex<Vec<{entity_rust}>>,
}}

// ── Comandos Tauri ────────────────────────────────────────────────────────────

#[tauri::command]
fn greet(name: &str) -> String {{
    format!("¡Hola, {{}}! Este mensaje viene de Rust 🦀", name)
}}

#[tauri::command]
fn get_{entity_plural}(state: State<AppState>) -> Vec<{entity_rust}> {{
    state.{entity_plural}.lock().unwrap().clone()
}}

#[tauri::command]
fn create_{entity_slug_name}(
    payload: Create{entity_rust}Payload,
    state: State<AppState>,
) -> {entity_rust} {{
    let item = {entity_rust} {{
        id: uuid::Uuid::new_v4().to_string(),
        name: payload.name,
        description: payload.description,
        status: "active".to_string(),
        created_at: chrono::Utc::now().to_rfc3339(),
    }};
    state.{entity_plural}.lock().unwrap().push(item.clone());
    item
}}

#[tauri::command]
fn delete_{entity_slug_name}(id: String, state: State<AppState>) {{
    let mut items = state.{entity_plural}.lock().unwrap();
    items.retain(|i| i.id != id);
}}

// ── Punto de entrada ──────────────────────────────────────────────────────────

pub fn run() {{
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(AppState {{
            {entity_plural}: Mutex::new(vec![
                // Datos de ejemplo — elimínalos cuando tengas persistencia real
                {entity_rust} {{
                    id: "1".to_string(),
                    name: "Ejemplo inicial".to_string(),
                    description: Some("Dato de demostración".to_string()),
                    status: "active".to_string(),
                    created_at: chrono::Utc::now().to_rfc3339(),
                }},
            ]),
        }})
        .invoke_handler(tauri::generate_handler![
            greet,
            get_{entity_plural},
            create_{entity_slug_name},
            delete_{entity_slug_name},
        ])
        .run(tauri::generate_context!())
        .expect("Error al arrancar la aplicación Tauri");
}}
"""
    return GeneratedFile(path="src-tauri/src/lib.rs", language="rust", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.env
/src-tauri/target/
/src-tauri/gen/
WixTools/
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)
