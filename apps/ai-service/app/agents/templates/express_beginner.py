"""
Express Beginner template — stack simplificado para nivel BEGINNER.
Stack: Node.js + Express.js + PostgreSQL (pg) + React 18 + Vite
Sin TypeScript, sin DDD, sin decoradores. Comentado para aprendizaje.
"""

import re
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def _f(path: str, language: str, content: str) -> GeneratedFile:
    return GeneratedFile(path=path, language=language, content=content)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _snake(name: str) -> str:
    return re.sub(r"[\s\-]+", "_", name.lower().strip())


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    modules = req.modules if req.modules else ["item"]
    first_mod = modules[0]
    first_slug = _slug(first_mod)
    first_snake = _snake(first_mod)
    needs_auth = req.needs_auth

    files = [
        _f("package.json",             "json",       _pkg_json(slug)),
        _f(".env.example",             "dotenv",     _env_example(slug)),
        _f("src/index.js",             "javascript", _app_entry(name, needs_auth)),
        _f("src/db.js",               "javascript", _db()),
        _f("src/routes/index.js",     "javascript", _routes_index(modules)),
        _f(f"src/routes/{first_slug}.js", "javascript", _crud_routes(first_slug, first_snake, needs_auth)),
        _f("client/index.html",        "html",       _html(name)),
        _f("client/package.json",      "json",       _client_pkg(slug)),
        _f("client/vite.config.js",    "javascript", _vite_config()),
        _f("client/src/main.jsx",      "javascript", _main_jsx()),
        _f("client/src/App.jsx",       "javascript", _app_jsx(name, modules, first_slug)),
        _f("client/src/api.js",        "javascript", _api_helper()),
        _f(f"client/src/pages/{first_slug}/List.jsx",   "javascript", _list_page(first_mod, first_slug)),
        _f(f"client/src/pages/{first_slug}/Form.jsx",   "javascript", _form_page(first_mod, first_slug)),
        _f("docker-compose.yml",       "yaml",       _docker_compose(slug)),
        _f("README.md",                "markdown",   _readme(name, slug, needs_auth)),
    ]

    if needs_auth:
        files.append(_f("src/routes/auth.js",   "javascript", _auth_routes(slug)))
        files.append(_f("src/middleware/auth.js","javascript", _auth_middleware()))

    # Deduplicate by path — last entry for a path wins (auth routes take priority over CRUD)
    seen: dict[str, GeneratedFile] = {}
    for f in files:
        seen[f.path] = f
    files = list(seen.values())

    return CodeGenerationResponse(project_name=name, files=files)


# ── Backend files ─────────────────────────────────────────────────────────────

def _pkg_json(slug: str) -> str:
    return f"""{{"name": "{slug}-api",
  "version": "1.0.0",
  "description": "API backend — generada con ProgresIA Studio",
  "main": "src/index.js",
  "scripts": {{
    "start": "node src/index.js",
    "dev": "nodemon src/index.js"
  }},
  "dependencies": {{
    "bcryptjs": "^2.4.3",
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.19.2",
    "jsonwebtoken": "^9.0.2",
    "pg": "^8.11.5"
  }},
  "devDependencies": {{
    "nodemon": "^3.1.4"
  }}
}}"""


def _env_example(slug: str) -> str:
    return f"""# Variables de entorno — copia este archivo a .env y ajusta los valores
# NUNCA subas el archivo .env a git

# Puerto donde escucha el servidor
PORT=3000

# Conexion a la base de datos PostgreSQL
DATABASE_URL=postgresql://postgres:changeme@localhost:5432/{slug}_db

# Secreto para firmar tokens JWT (usa una cadena larga y aleatoria)
JWT_SECRET=cambia_esto_por_un_secreto_largo_min_32_caracteres

# URL del frontend (para CORS)
CLIENT_URL=http://localhost:5173
"""


def _app_entry(name: str, needs_auth: bool) -> str:
    auth_import = 'const authRoutes = require("./routes/auth");' if needs_auth else ""
    auth_use    = '  app.use("/api/auth", authRoutes);' if needs_auth else ""
    return f"""// ─── Punto de entrada de la aplicación ───────────────────────────────────────
// Aquí se configura Express y se registran todas las rutas.

// Carga las variables del archivo .env
require("dotenv").config();

const express = require("express");
const cors    = require("cors");

// Importamos el archivo de rutas
const routes  = require("./routes/index");
{auth_import}

// Creamos la aplicación Express
const app = express();

// ── Middlewares globales ──────────────────────────────────────────────────────
// CORS: permite que el frontend (puerto 5173) haga peticiones al backend (3000)
app.use(cors({{ origin: process.env.CLIENT_URL || "http://localhost:5173" }}));

// Permite leer JSON del body de las peticiones POST/PUT
app.use(express.json());

// ── Rutas ─────────────────────────────────────────────────────────────────────
app.use("/api", routes);
{auth_use}

// Ruta de verificación — útil para comprobar que el servidor está funcionando
app.get("/health", (req, res) => {{
  res.json({{ status: "ok", service: "{name}" }});
}});

// ── Arrancar el servidor ──────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {{
  console.log(`✅  Servidor arrancado en http://localhost:${{PORT}}`);
  console.log(`📖  Health check: http://localhost:${{PORT}}/health`);
}});
"""


def _db() -> str:
    return """// ─── Conexión a la base de datos PostgreSQL ──────────────────────────────────
// Usamos el módulo 'pg' para conectarnos a PostgreSQL.
// Pool gestiona múltiples conexiones de forma eficiente.

const { Pool } = require("pg");

// La URL de conexión viene de las variables de entorno
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

// Función helper para ejecutar queries
// Ejemplo de uso: const { rows } = await db.query("SELECT * FROM users");
async function query(text, params) {
  const result = await pool.query(text, params);
  return result;
}

module.exports = { query };
"""


def _routes_index(modules: list[str]) -> str:
    imports = "\n".join(
        f'const {_slug(m)}Routes = require("./{_slug(m)}");' for m in modules
    )
    uses = "\n".join(
        f'router.use("/{_slug(m)}s", {_slug(m)}Routes);' for m in modules
    )
    return f"""// ─── Router principal ────────────────────────────────────────────────────────
// Aquí registramos todos los grupos de rutas de la aplicación.

const express = require("express");
const router  = express.Router();

{imports}

// Cada módulo tiene sus propias rutas bajo /api/[modulo]s
{uses}

module.exports = router;
"""


def _crud_routes(slug: str, snake: str, needs_auth: bool) -> str:
    auth_import = '\nconst { authenticate } = require("../middleware/auth");' if needs_auth else ""
    auth_guard  = "authenticate, " if needs_auth else ""
    return f"""// ─── Rutas CRUD para el módulo "{slug}" ─────────────────────────────────────
// CRUD = Create, Read, Update, Delete — las 4 operaciones básicas.
// Cada función corresponde a una operación HTTP estándar.

const express = require("express");
const router  = express.Router();
const db      = require("../db");{auth_import}

// ── GET /api/{slug}s ─ Listar todos ──────────────────────────────────────────
router.get("/", {auth_guard}async (req, res) => {{
  try {{
    // Obtenemos todos los registros ordenados por fecha de creación
    const {{ rows }} = await db.query(
      "SELECT * FROM {snake}s ORDER BY created_at DESC"
    );
    res.json({{ data: rows }});
  }} catch (error) {{
    console.error("Error al obtener {snake}s:", error);
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

// ── GET /api/{slug}s/:id ─ Obtener uno por ID ────────────────────────────────
router.get("/:id", {auth_guard}async (req, res) => {{
  try {{
    const {{ id }} = req.params; // El :id viene de la URL
    const {{ rows }} = await db.query(
      "SELECT * FROM {snake}s WHERE id = $1",
      [id] // Usamos $1 para evitar SQL injection
    );

    // Si no encontramos el registro, devolvemos 404
    if (rows.length === 0) {{
      return res.status(404).json({{ error: "{slug} no encontrado" }});
    }}

    res.json({{ data: rows[0] }});
  }} catch (error) {{
    console.error("Error al obtener {snake}:", error);
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

// ── POST /api/{slug}s ─ Crear uno nuevo ──────────────────────────────────────
router.post("/", {auth_guard}async (req, res) => {{
  try {{
    const {{ name, description }} = req.body; // Datos que envía el cliente

    // Validación básica: comprobamos que los campos requeridos estén presentes
    if (!name) {{
      return res.status(400).json({{ error: "El campo 'name' es obligatorio" }});
    }}

    const {{ rows }} = await db.query(
      "INSERT INTO {snake}s (name, description) VALUES ($1, $2) RETURNING *",
      [name, description]
    );

    // 201 = recurso creado correctamente
    res.status(201).json({{ data: rows[0] }});
  }} catch (error) {{
    console.error("Error al crear {snake}:", error);
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

// ── PATCH /api/{slug}s/:id ─ Actualizar parcialmente ─────────────────────────
router.patch("/:id", {auth_guard}async (req, res) => {{
  try {{
    const {{ id }} = req.params;
    const {{ name, description }} = req.body;

    const {{ rows }} = await db.query(
      `UPDATE {snake}s
       SET name        = COALESCE($1, name),
           description = COALESCE($2, description),
           updated_at  = NOW()
       WHERE id = $3
       RETURNING *`,
      [name, description, id]
    );

    if (rows.length === 0) {{
      return res.status(404).json({{ error: "{slug} no encontrado" }});
    }}

    res.json({{ data: rows[0] }});
  }} catch (error) {{
    console.error("Error al actualizar {snake}:", error);
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

// ── DELETE /api/{slug}s/:id ─ Eliminar ───────────────────────────────────────
router.delete("/:id", {auth_guard}async (req, res) => {{
  try {{
    const {{ id }} = req.params;
    const {{ rows }} = await db.query(
      "DELETE FROM {snake}s WHERE id = $1 RETURNING *",
      [id]
    );

    if (rows.length === 0) {{
      return res.status(404).json({{ error: "{slug} no encontrado" }});
    }}

    // 204 = sin contenido — la eliminación fue exitosa
    res.status(204).send();
  }} catch (error) {{
    console.error("Error al eliminar {snake}:", error);
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

module.exports = router;
"""


def _auth_routes(slug: str) -> str:
    return f"""// ─── Rutas de autenticación ──────────────────────────────────────────────────
// Registro, login y perfil del usuario.

const express  = require("express");
const router   = express.Router();
const bcrypt   = require("bcryptjs");
const jwt      = require("jsonwebtoken");
const db       = require("../db");
const {{ authenticate }} = require("../middleware/auth");

// ── POST /api/auth/register ─ Registrar usuario ───────────────────────────────
router.post("/register", async (req, res) => {{
  try {{
    const {{ email, password, name }} = req.body;

    if (!email || !password) {{
      return res.status(400).json({{ error: "Email y contraseña son obligatorios" }});
    }}

    // Verificamos que el email no esté ya registrado
    const existing = await db.query("SELECT id FROM users WHERE email = $1", [email]);
    if (existing.rows.length > 0) {{
      return res.status(409).json({{ error: "El email ya está registrado" }});
    }}

    // Hasheamos la contraseña — NUNCA guardes passwords en texto plano
    const hashedPassword = await bcrypt.hash(password, 10);

    const {{ rows }} = await db.query(
      "INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id, email, name",
      [email, hashedPassword, name]
    );

    const user = rows[0];

    // Creamos el token JWT que el cliente guardará y enviará en futuras peticiones
    const token = jwt.sign({{ userId: user.id, email: user.email }}, process.env.JWT_SECRET, {{
      expiresIn: "7d"
    }});

    res.status(201).json({{ data: {{ user, token }} }});
  }} catch (error) {{
    console.error("Error en registro:", error);
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

// ── POST /api/auth/login ─ Iniciar sesión ────────────────────────────────────
router.post("/login", async (req, res) => {{
  try {{
    const {{ email, password }} = req.body;

    const {{ rows }} = await db.query("SELECT * FROM users WHERE email = $1", [email]);
    const user = rows[0];

    // Verificamos que el usuario exista Y que la contraseña sea correcta
    if (!user || !(await bcrypt.compare(password, user.password_hash))) {{
      return res.status(401).json({{ error: "Email o contraseña incorrectos" }});
    }}

    const token = jwt.sign({{ userId: user.id, email: user.email }}, process.env.JWT_SECRET, {{
      expiresIn: "7d"
    }});

    res.json({{ data: {{ user: {{ id: user.id, email: user.email, name: user.name }}, token }} }});
  }} catch (error) {{
    console.error("Error en login:", error);
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

// ── GET /api/auth/me ─ Perfil del usuario actual ─────────────────────────────
router.get("/me", authenticate, async (req, res) => {{
  try {{
    const {{ rows }} = await db.query(
      "SELECT id, email, name, created_at FROM users WHERE id = $1",
      [req.user.userId]
    );
    res.json({{ data: rows[0] }});
  }} catch (error) {{
    res.status(500).json({{ error: "Error interno del servidor" }});
  }}
}});

module.exports = router;
"""


def _auth_middleware() -> str:
    return """// ─── Middleware de autenticación JWT ─────────────────────────────────────────
// Este middleware protege las rutas que requieren estar autenticado.
// Se usa como: router.get("/ruta-protegida", authenticate, handler)

const jwt = require("jsonwebtoken");

function authenticate(req, res, next) {
  // El token viene en el header: Authorization: Bearer <token>
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Acceso no autorizado — falta el token" });
  }

  const token = authHeader.split(" ")[1];

  try {
    // Verificamos que el token sea válido y no haya expirado
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Añadimos el usuario al objeto request para usarlo en las rutas
    req.user = decoded;

    // next() pasa el control a la siguiente función (la ruta real)
    next();
  } catch {
    return res.status(401).json({ error: "Token inválido o expirado" });
  }
}

module.exports = { authenticate };
"""


# ── Frontend files ────────────────────────────────────────────────────────────

def _html(name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <!-- Vite inyecta aquí el bundle de React en desarrollo -->
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""


def _client_pkg(slug: str) -> str:
    return f"""{{"name": "{slug}-client",
  "version": "1.0.0",
  "private": true,
  "scripts": {{
    "dev":   "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react":     "^18.3.1",
    "react-dom": "^18.3.1"
  }},
  "devDependencies": {{
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.3.4"
  }}
}}"""


def _vite_config() -> str:
    return """import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // En desarrollo, las peticiones a /api se redirigen al backend (puerto 3000)
    proxy: {
      "/api": "http://localhost:3000"
    }
  }
});
"""


def _main_jsx() -> str:
    return """// ─── Punto de entrada del frontend React ─────────────────────────────────────
import React       from "react";
import ReactDOM    from "react-dom/client";
import App         from "./App";

// Montamos la aplicación en el div#root del index.html
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""


def _api_helper() -> str:
    return """// ─── Helper para llamadas a la API ───────────────────────────────────────────
// Centraliza todas las llamadas fetch para no repetir código.
// Si usas JWT, añade el token en el header Authorization.

const BASE_URL = "/api"; // Gracias al proxy de Vite, /api se redirige al backend

export async function apiGet(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Error ${res.status} en GET ${path}`);
  return res.json();
}

export async function apiPost(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `Error ${res.status}`);
  }
  return res.json();
}

export async function apiPatch(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Error ${res.status} en PATCH ${path}`);
  return res.json();
}

export async function apiDelete(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Error ${res.status} en DELETE ${path}`);
}

// Devuelve el header de autenticación si hay token guardado
function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}
"""


def _app_jsx(name: str, modules: list[str], first_slug: str) -> str:
    return f"""// ─── Componente principal de la aplicación ───────────────────────────────────
// Aquí gestionamos la navegación simple entre páginas.

import {{ useState }} from "react";
import {_pascal(first_slug)}List from "./pages/{first_slug}/List";

export default function App() {{
  // page: controla qué vista mostrar
  const [page, setPage] = useState("list");

  return (
    <div style={{{{ fontFamily: "sans-serif", maxWidth: 800, margin: "0 auto", padding: 20 }}}}>
      <header style={{{{ borderBottom: "1px solid #eee", paddingBottom: 12, marginBottom: 24 }}}}>
        <h1 style={{{{ margin: 0, fontSize: 22 }}}}>
          {name}
        </h1>
        <nav style={{{{ marginTop: 8, display: "flex", gap: 12 }}}}>
          <button onClick={{() => setPage("list")}}>
            Ver {modules[0] if modules else "items"}
          </button>
        </nav>
      </header>

      <main>
        {{/* Renderizamos la página activa */}}
        {{page === "list" && <{_pascal(first_slug)}List />}}
      </main>
    </div>
  );
}}
"""


def _list_page(mod: str, slug: str) -> str:
    pascal = _pascal(slug)
    return f"""// ─── Página: listado de {mod} ─────────────────────────────────────────────────
// Muestra todos los registros y permite crear/eliminar.

import {{ useState, useEffect }} from "react";
import {{ apiGet, apiPost, apiDelete }} from "../../api";
import {pascal}Form from "./Form";

export default function {pascal}List() {{
  // Estado local: lista de registros, carga, error y modal de creación
  const [items,   setItems]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [showForm, setShowForm] = useState(false);

  // useEffect con array vacío [] = se ejecuta una sola vez al montar el componente
  useEffect(() => {{
    loadItems();
  }}, []);

  async function loadItems() {{
    try {{
      setLoading(true);
      setError(null);
      const response = await apiGet("/{slug}s");
      setItems(response.data);
    }} catch (err) {{
      setError(err.message);
    }} finally {{
      setLoading(false);
    }}
  }}

  async function handleDelete(id) {{
    if (!confirm("¿Eliminar este registro?")) return;
    try {{
      await apiDelete(`/{slug}s/${{id}}`);
      // Actualizamos la lista sin volver a cargar del servidor
      setItems(prev => prev.filter(item => item.id !== id));
    }} catch (err) {{
      alert("Error al eliminar: " + err.message);
    }}
  }}

  if (loading) return <p>Cargando...</p>;
  if (error)   return <p style={{{{ color: "red" }}}}>Error: {{error}}</p>;

  return (
    <div>
      <div style={{{{ display: "flex", justifyContent: "space-between", alignItems: "center" }}}}>
        <h2>{mod}</h2>
        <button onClick={{() => setShowForm(true)}}>+ Nuevo</button>
      </div>

      {{showForm && (
        <{pascal}Form
          onSuccess={{(newItem) => {{
            setItems(prev => [newItem, ...prev]);
            setShowForm(false);
          }}}}
          onCancel={{() => setShowForm(false)}}
        />
      )}}

      {{items.length === 0 && <p>No hay registros todavía.</p>}}

      <ul style={{{{ listStyle: "none", padding: 0 }}}}>
        {{items.map(item => (
          <li key={{item.id}} style={{{{ border: "1px solid #eee", padding: 12, marginBottom: 8, borderRadius: 6 }}}}>
            <strong>{{item.name}}</strong>
            {{item.description && <p style={{{{ margin: "4px 0 0", color: "#666" }}}}>{{item.description}}</p>}}
            <button
              onClick={{() => handleDelete(item.id)}}
              style={{{{ marginTop: 8, color: "red", background: "none", border: "none", cursor: "pointer" }}}}
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


def _form_page(mod: str, slug: str) -> str:
    pascal = _pascal(slug)
    return f"""// ─── Formulario para crear {mod} ──────────────────────────────────────────────
// Componente reutilizable para el formulario de creación.

import {{ useState }} from "react";
import {{ apiPost }} from "../../api";

export default function {pascal}Form({{ onSuccess, onCancel }}) {{
  // Estado del formulario: un campo por cada dato que necesitamos
  const [name,        setName]        = useState("");
  const [description, setDescription] = useState("");
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);

  async function handleSubmit(e) {{
    e.preventDefault(); // Evita que el navegador recargue la página
    setLoading(true);
    setError(null);

    try {{
      const response = await apiPost("/{slug}s", {{ name, description }});
      onSuccess(response.data); // Notificamos al padre que se creó el registro
    }} catch (err) {{
      setError(err.message);
    }} finally {{
      setLoading(false);
    }}
  }}

  return (
    <form onSubmit={{handleSubmit}} style={{{{ border: "1px solid #ddd", padding: 16, borderRadius: 8, marginBottom: 16 }}}}>
      <h3>Crear {mod}</h3>

      <div style={{{{ marginBottom: 12 }}}}>
        <label>
          Nombre *
          <input
            type="text"
            value={{name}}
            onChange={{e => setName(e.target.value)}}
            required
            placeholder="Nombre del {mod.lower()}"
            style={{{{ display: "block", width: "100%", padding: 8, marginTop: 4 }}}}
          />
        </label>
      </div>

      <div style={{{{ marginBottom: 12 }}}}>
        <label>
          Descripción
          <textarea
            value={{description}}
            onChange={{e => setDescription(e.target.value)}}
            placeholder="Descripción opcional"
            rows={{3}}
            style={{{{ display: "block", width: "100%", padding: 8, marginTop: 4 }}}}
          />
        </label>
      </div>

      {{error && <p style={{{{ color: "red" }}}}>Error: {{error}}</p>}}

      <div style={{{{ display: "flex", gap: 8 }}}}>
        <button type="submit" disabled={{loading}}>
          {{loading ? "Guardando..." : "Guardar"}}
        </button>
        <button type="button" onClick={{onCancel}}>
          Cancelar
        </button>
      </div>
    </form>
  );
}}
"""


def _docker_compose(slug: str) -> str:
    return f"""# Docker Compose — entorno de desarrollo
# Levanta la base de datos. El frontend y backend se ejecutan con npm run dev.
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: {slug}_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  postgres_data:
"""


def _readme(name: str, slug: str, needs_auth: bool) -> str:
    auth_note = "\n- `POST /api/auth/register` — Registrar usuario\n- `POST /api/auth/login` — Iniciar sesión" if needs_auth else ""
    return f"""# {name}

MVP generado con **ProgresIA Studio** — Stack: Express.js + React + PostgreSQL

---

## Inicio rápido (Linux / macOS)

```bash
# 1. Clona o descarga el proyecto
cd {slug}

# 2. Arranca la base de datos con Docker
docker compose up -d

# 3. Configura las variables de entorno
cp .env.example .env
# Edita .env con tus valores (la DB por defecto ya funciona con Docker)

# 4. Instala dependencias del backend y arráncalo
npm install
npm run dev
# El servidor escucha en http://localhost:3000

# 5. En otra terminal, instala el frontend y arráncalo
cd client
npm install
npm run dev
# El frontend está en http://localhost:5173
```

## Windows (PowerShell)

```powershell
docker compose up -d
Copy-Item .env.example .env
npm install; npm run dev
# En otra terminal:
cd client; npm install; npm run dev
```

## Estructura del proyecto

```
{slug}/
├── src/
│   ├── index.js          # Punto de entrada del servidor Express
│   ├── db.js             # Conexión a PostgreSQL
│   ├── routes/           # Rutas de la API
│   └── middleware/       # Middleware (auth, etc.)
├── client/               # Frontend React con Vite
│   └── src/
│       ├── App.jsx       # Componente principal
│       ├── api.js        # Helper para llamadas a la API
│       └── pages/        # Páginas de la aplicación
├── docker-compose.yml    # Base de datos para desarrollo
├── .env.example          # Variables de entorno
└── README.md             # Este archivo
```

## API endpoints principales
{auth_note}
- `GET  /api/[modulo]s` — Listar todos
- `GET  /api/[modulo]s/:id` — Obtener uno
- `POST /api/[modulo]s` — Crear uno nuevo
- `PATCH /api/[modulo]s/:id` — Actualizar
- `DELETE /api/[modulo]s/:id` — Eliminar

## Próximos pasos

1. Crea la tabla en la base de datos (`psql` o DBeaver)
2. Ajusta los campos de las rutas en `src/routes/`
3. Personaliza las páginas React en `client/src/pages/`
4. Lee `sdd/constitution.md` para entender la arquitectura
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pascal(name: str) -> str:
    return "".join(w.capitalize() for w in re.split(r"[\s\-_]+", name.strip()))
