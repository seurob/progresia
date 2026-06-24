"""React 19 + Vite + Firebase (Auth + Firestore) scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_firebase(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold React + Vite + Firebase 10 con Firestore y Auth opcional."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    files: list[GeneratedFile] = [
        _package_json(project_slug, req.needs_auth),
        _tsconfig(),
        _vite_config(),
        _tailwind_config(),
        _postcss_config(),
        _index_html(req.project_name),
        _main_tsx(req.needs_auth),
        _app_tsx(entity_slug_name, entity_pascal_name, entity_plural, req.needs_auth),
        _firebase_lib(),
        _firestore_lib(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _types_index(entity_pascal_name),
        _home_page(req.project_name),
        _entity_list_page(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural, req.needs_auth),
        _firestore_rules(entity_plural, req.needs_auth),
        _firebase_json(project_slug),
        _firebaserc(project_slug),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Obtén estos valores desde Firebase Console → Configuración del proyecto\n"
                "# https://console.firebase.google.com\n\n"
                "VITE_FIREBASE_API_KEY=tu-api-key\n"
                "VITE_FIREBASE_AUTH_DOMAIN=tu-proyecto.firebaseapp.com\n"
                "VITE_FIREBASE_PROJECT_ID=tu-proyecto\n"
                "VITE_FIREBASE_STORAGE_BUCKET=tu-proyecto.appspot.com\n"
                "VITE_FIREBASE_MESSAGING_SENDER_ID=123456789\n"
                "VITE_FIREBASE_APP_ID=1:123456789:web:abcdef\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="React 19 · Vite · Firebase 10 · Firestore · Tailwind CSS",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Cuenta Firebase — https://firebase.google.com",
                "Firebase CLI — npm install -g firebase-tools",
            ],
            setup_commands=[
                "npm install",
                "cp .env.example .env           # rellena con tus credenciales de Firebase",
                "npm run dev",
                "# Para desplegar:",
                "firebase login",
                "firebase deploy",
            ],
            env_vars=[
                ("VITE_FIREBASE_API_KEY", "desde Firebase Console"),
                ("VITE_FIREBASE_PROJECT_ID", "id de tu proyecto"),
            ],
            api_port=5173,
        ),
    ]

    if req.needs_auth:
        files.append(_auth_context())
        files.append(_login_page(req.project_name))

    return files


def _package_json(project_slug: str, needs_auth: bool) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "firebase": "^10.12.2",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^6.24.0"
  }},
  "devDependencies": {{
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


def _vite_config() -> GeneratedFile:
    content = """\
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
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


def _main_tsx(needs_auth: bool) -> GeneratedFile:
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


def _app_tsx(entity_slug_name: str, entity_pascal_name: str, entity_plural: str, needs_auth: bool) -> GeneratedFile:
    auth_import = "import { AuthProvider } from './contexts/AuthContext';\n" if needs_auth else ""
    auth_wrap_open = "<AuthProvider>\n      " if needs_auth else ""
    auth_wrap_close = "\n      </AuthProvider>" if needs_auth else ""
    login_route = "<Route path='/login' element={<LoginPage />} />\n          " if needs_auth else ""
    login_import = "import LoginPage from './pages/LoginPage';\n" if needs_auth else ""

    content = f"""\
import {{ Routes, Route }} from 'react-router-dom';
{auth_import}import HomePage from './pages/HomePage';
import {entity_pascal_name}ListPage from './pages/{entity_pascal_name}ListPage';
{login_import}
export default function App() {{
  return (
    {auth_wrap_open}<Routes>
        <Route path="/" element={{<HomePage />}} />
        <Route path="/{entity_plural}" element={{<{entity_pascal_name}ListPage />}} />
        {login_route}
      </Routes>{auth_wrap_close}
  );
}}
"""
    return GeneratedFile(path="src/App.tsx", language="tsx", content=content)


def _firebase_lib() -> GeneratedFile:
    content = """\
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

// Las credenciales vienen de variables de entorno (archivo .env)
const firebaseConfig = {
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId:             import.meta.env.VITE_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);

export const db = getFirestore(app);
export const auth = getAuth(app);
"""
    return GeneratedFile(path="src/lib/firebase.ts", language="typescript", content=content)


def _firestore_lib(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{
  collection,
  getDocs,
  getDoc,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
  query,
  orderBy,
  serverTimestamp,
}} from 'firebase/firestore';
import {{ db }} from './firebase';
import type {{ {entity_pascal_name} }} from '../types';

const col = collection(db, '{entity_plural}');

export async function getAll{entity_pascal_name}s(): Promise<{entity_pascal_name}[]> {{
  const q = query(col, orderBy('createdAt', 'desc'));
  const snap = await getDocs(q);
  return snap.docs.map(d => ({{ id: d.id, ...d.data() }} as {entity_pascal_name}));
}}

export async function get{entity_pascal_name}ById(id: string): Promise<{entity_pascal_name} | null> {{
  const snap = await getDoc(doc(db, '{entity_plural}', id));
  return snap.exists() ? ({{ id: snap.id, ...snap.data() }} as {entity_pascal_name}) : null;
}}

export async function create{entity_pascal_name}(data: Omit<{entity_pascal_name}, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {{
  const ref = await addDoc(col, {{ ...data, createdAt: serverTimestamp(), updatedAt: serverTimestamp() }});
  return ref.id;
}}

export async function update{entity_pascal_name}(id: string, data: Partial<{entity_pascal_name}>): Promise<void> {{
  await updateDoc(doc(db, '{entity_plural}', id), {{ ...data, updatedAt: serverTimestamp() }});
}}

export async function delete{entity_pascal_name}(id: string): Promise<void> {{
  await deleteDoc(doc(db, '{entity_plural}', id));
}}
"""
    return GeneratedFile(path="src/lib/firestore.ts", language="typescript", content=content)


def _types_index(entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
export interface {entity_pascal_name} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt?: unknown;
  updatedAt?: unknown;
}}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _home_page(project_name: str) -> GeneratedFile:
    content = f"""\
export default function HomePage() {{
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-orange-500 mb-4">{project_name}</h1>
        <p className="text-gray-600 text-lg">
          Tu app Firebase está lista. Modifica esta página para empezar.
        </p>
      </div>
    </div>
  );
}}
"""
    return GeneratedFile(path="src/pages/HomePage.tsx", language="tsx", content=content)


def _entity_list_page(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str, needs_auth: bool) -> GeneratedFile:
    content = f"""\
import {{ useEffect, useState }} from 'react';
import {{ getAll{entity_pascal_name}s, delete{entity_pascal_name} }} from '../lib/firestore';
import type {{ {entity_pascal_name} }} from '../types';

export default function {entity_pascal_name}ListPage() {{
  const [items, setItems] = useState<{entity_pascal_name}[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {{
    getAll{entity_pascal_name}s()
      .then(setItems)
      .catch(() => setError('No se pudieron cargar los datos.'))
      .finally(() => setLoading(false));
  }}, []);

  async function handleDelete(id: string) {{
    if (!confirm('¿Eliminar este elemento?')) return;
    await delete{entity_pascal_name}(id);
    setItems(prev => prev.filter(i => i.id !== id));
  }}

  if (loading) return <div className="text-center py-20 text-gray-500">Cargando...</div>;
  if (error) return <div className="text-red-600 text-center py-20">{{error}}</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">{entity_pascal_name}s</h2>
      <ul className="divide-y divide-gray-200 bg-white shadow rounded-lg">
        {{items.map(item => (
          <li key={{item.id}} className="px-6 py-4 flex justify-between items-center">
            <div>
              <p className="font-medium text-gray-900">{{item.name}}</p>
              {{item.description && <p className="text-sm text-gray-500">{{item.description}}</p>}}
            </div>
            <button
              onClick={{() => handleDelete(item.id)}}
              className="text-red-500 hover:text-red-700 text-sm"
            >
              Eliminar
            </button>
          </li>
        ))}}
        {{items.length === 0 && (
          <li className="py-12 text-center text-gray-400">No hay {entity_plural} todavía.</li>
        )}}
      </ul>
    </div>
  );
}}
"""
    return GeneratedFile(path=f"src/pages/{entity_pascal_name}ListPage.tsx", language="tsx", content=content)


def _auth_context() -> GeneratedFile:
    content = """\
import { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import type { User } from 'firebase/auth';
import { auth } from '../lib/firebase';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    return onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  async function login(email: string, password: string) {
    await signInWithEmailAndPassword(auth, email, password);
  }

  async function logout() {
    await signOut(auth);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
"""
    return GeneratedFile(path="src/contexts/AuthContext.tsx", language="tsx", content=content)


def _login_page(project_name: str) -> GeneratedFile:
    content = """\
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate('/');
    } catch {
      setError('Credenciales incorrectas. Verifica tu email y contraseña.');
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm space-y-4">
        <h2 className="text-2xl font-bold text-center text-gray-800">Iniciar sesión</h2>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-orange-400 outline-none"
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-orange-400 outline-none"
        />
        <button
          type="submit"
          className="w-full bg-orange-500 text-white py-2 rounded-md hover:bg-orange-600 transition font-medium"
        >
          Entrar
        </button>
      </form>
    </div>
  );
}
"""
    return GeneratedFile(path="src/pages/LoginPage.tsx", language="tsx", content=content)


def _firestore_rules(entity_plural: str, needs_auth: bool) -> GeneratedFile:
    if needs_auth:
        rules = f"""\
rules_version = '2';
service cloud.firestore {{
  match /databases/{{database}}/documents {{
    // Solo usuarios autenticados pueden leer y escribir
    match /{entity_plural}/{{docId}} {{
      allow read, write: if request.auth != null;
    }}
  }}
}}
"""
    else:
        rules = f"""\
rules_version = '2';
service cloud.firestore {{
  match /databases/{{database}}/documents {{
    // Acceso público de lectura; escritura solo autenticados
    match /{entity_plural}/{{docId}} {{
      allow read: if true;
      allow write: if request.auth != null;
    }}
  }}
}}
"""
    return GeneratedFile(path="firestore.rules", language="text", content=rules)


def _firebase_json(project_slug: str) -> GeneratedFile:
    content = """\
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  },
  "firestore": {
    "rules": "firestore.rules"
  }
}
"""
    return GeneratedFile(path="firebase.json", language="json", content=content)


def _firebaserc(project_slug: str) -> GeneratedFile:
    content = """\
{
  "projects": {
    "default": "TU_PROYECTO_FIREBASE"
  }
}
"""
    return GeneratedFile(path=".firebaserc", language="json", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.env
.firebase/
*.local
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)
