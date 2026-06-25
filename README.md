# ProgresIA Studio

> De una idea a un MVP completo mediante desarrollo guiado por especificaciones e IA.

ProgresIA Studio es una plataforma educativa que convierte cualquier idea de producto en un proyecto técnico completo en minutos. Aplica la metodología **SDD (Spec-Driven Development)**: primero especifica con precisión usando múltiples agentes de IA encadenados, luego genera código, documentación, issues y un ZIP listo para continuar el desarrollo.

El diferenciador clave no es la velocidad de generación, sino la **trazabilidad pedagógica**: cada artefacto generado explica la decisión arquitectónica que lo motivó.

---

## Demo

| Recurso | Enlace |
|---------|--------|
| Aplicación | _URL de despliegue_ |
| Vídeo de presentación | _enlace al vídeo_ |
| Slides TFM | _enlace a las slides_ |

**Credenciales de prueba (entorno de desarrollo):**

| Rol | Email | Password |
|-----|-------|----------|
| Usuario demo | `demo@progresia.local` | `change_me_123` |
| Administrador | `admin@progresia.local` | `$eurobman2026` |

> Para crear estos usuarios en local: `cd apps/api && npm run prisma:seed`

---

## Características principales

- **Wizard conversacional** — guía al usuario en 6 pasos adaptados a su nivel técnico
- **Pipeline SDD de 7 etapas** — requisitos → arquitectura → OpenSpec → issues → tutorial → código → ZIP
- **OpenSpec como fuente de verdad** — contrato JSON central que todos los agentes downstream consumen
- **12 arquitecturas soportadas** — web, mobile y desktop, de principiante a avanzado
- **Fallback chain de 4 LLMs** — Groq → OpenAI → Gemini → Ollama → generación determinista
- **Exportación múltiple** — PDF, Markdown, ZIP descargable, publicación directa a GitHub
- **Panel de administración** aislado con auth propia
- **Modelo de datos profesional** — entidades, relaciones, índices, auditoría y diagrama ER adaptados al dominio
- **Observabilidad opcional** — Sentry integrado en React, NestJS y FastAPI con filtrado de datos sensibles
- **CI verde** — lint, tipos, tests y build validados en GitHub Actions

---

## Stack técnico

| Capa | Tecnología | Puerto |
|------|-----------|--------|
| Frontend | React 19, Vite 8, Tailwind CSS 4, TanStack Query, React Router 7 | 5173 |
| Backend | NestJS 11, Prisma 6, PostgreSQL 16, BullMQ, Passport-JWT | 3000 |
| AI Service | FastAPI 0.115, LangChain 0.3, LangGraph 0.5, Pydantic v2 | 8003 |
| Base de datos | PostgreSQL 16 | 5432 |
| Cola de jobs | Redis 7 | 6380 * |
| Vectores (RAG) | Qdrant | 6333 |
| Almacenamiento | MinIO | 9000 / 9001 |
| Email (dev) | Mailpit | 1025 SMTP / 8025 UI |

> \* Redis en el puerto 6380 para evitar conflicto con Docker Desktop en Windows.

---

## Requisitos previos

| Herramienta | Versión mínima | Notas |
|-------------|---------------|-------|
| Node.js | 22 LTS | Usar `nvm` o `volta` recomendado |
| Python | 3.12+ | Gestor `uv` o `pip` |
| Docker Desktop | Última estable | Con Docker Compose v2 integrado |
| Git | 2.40+ | |

**LLM (al menos uno requerido):**

| Proveedor | Clave | Gratuito |
|-----------|-------|---------|
| Groq | `GROQ_API_KEY` | Sí (tier gratuito generoso) |
| OpenAI | `OPENAI_API_KEY` | No |
| Google Gemini | `GEMINI_API_KEY` | Sí (tier gratuito) |
| Ollama | — (local) | Sí |

---

## Puesta en marcha (desarrollo local)

### 1. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd progresia

# Instalar dependencias de todos los packages y apps
npm install
```

### 2. Configurar variables de entorno

```bash
# Variables de infraestructura y API
cp .env.example .env
```

Editar `.env` con los valores reales. Los campos mínimos para arrancar:

```env
DATABASE_URL=postgresql://progresia:change_me_in_production@127.0.0.1:5432/progresia_studio
REDIS_HOST=127.0.0.1
REDIS_PORT=6380
MINIO_ENDPOINT=127.0.0.1
JWT_SECRET=una_clave_secreta_larga_y_aleatoria
JWT_REFRESH_SECRET=otra_clave_secreta_diferente
GROQ_API_KEY=gsk_...          # O cualquier otro proveedor LLM
```

```bash
# Variables del AI service (LLM keys)
cp apps/ai-service/.env.example apps/ai-service/.env
# Añadir al menos una clave LLM en GROQ_API_KEY, OPENAI_API_KEY o GEMINI_API_KEY
```

### 3. Levantar la infraestructura (Docker)

```bash
docker compose up -d
```

Esto inicia PostgreSQL, Redis, MinIO, Qdrant y Mailpit. Verificar que todo esté sano:

```bash
docker compose ps        # todos en estado "running"
curl http://localhost:9001  # MinIO console
curl http://localhost:8025  # Mailpit UI
```

### 4. Preparar la base de datos

```bash
cd apps/api

# Primera vez (desarrollo) — aplica migraciones y genera el cliente Prisma
npx prisma migrate dev
npx prisma generate

# Crear el usuario administrador de desarrollo
npm run prisma:seed
```

> En producción usar `npx prisma migrate deploy` en lugar de `migrate dev`.

### 5. Arrancar el AI Service (FastAPI)

```bash
cd apps/ai-service

# Instalar dependencias Python (una sola vez)
pip install -e ".[dev]"

# Arrancar (puerto 8003 — Docker Desktop ocupa 8000/8001 en Windows)
uvicorn app.main:app --port 8003 --reload
```

Verificar: `curl http://localhost:8003/health` → `{"status":"ok","service":"progresia-ai-service"}`

### 6. Arrancar el API (NestJS)

```bash
# Desde la raíz. Así la API carga la configuración compartida correctamente.
npm run build --workspace @progresia/api

# Arrancar el build
node --enable-source-maps apps/api/dist/main
```

> **Windows:** usar `127.0.0.1` para PostgreSQL, Redis y MinIO. Evita problemas de resolución IPv4/IPv6 del motor nativo de Prisma. Si se ejecuta desde `apps/api`, mantener su `.env` sincronizado con el de la raíz.

Verificar: `curl http://localhost:3000/api/health`

### 7. Arrancar el Frontend (React)

```bash
cd apps/web
npm install
npm run dev
```

Abrir `http://localhost:5173`

---

## Resumen de URLs en desarrollo

| Servicio | URL | Descripción |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | App principal |
| API | http://localhost:3000/api | REST API |
| AI Service | http://localhost:8003 | Agentes IA |
| AI Service docs | http://localhost:8003/docs | Swagger interactivo |
| Mailpit | http://localhost:8025 | Bandeja de email de desarrollo |
| MinIO | http://localhost:9001 | Consola de almacenamiento |
| Qdrant | http://localhost:6333/dashboard | Panel de vectores |

---

## Metodología SDD — Pipeline de generación

La plataforma impone un orden de trabajo que refleja cómo se construyen productos reales. Cada paso depende del anterior y consume el OpenSpec como fuente de verdad.

```
Idea del usuario  (wizard conversacional — 6 pasos)
      │
      ▼
1. Análisis de requisitos    ← requirements_agent.py
      │                         Extrae RF, RNF, user stories y restricciones
      ▼
2. Arquitectura tecnológica  ← architecture_agent.py
      │                         Selecciona stack, justifica la decisión
      ▼
3. OpenSpec completo         ← openspec_agent.py   ← FUENTE DE VERDAD
      │
      ├──▶ 4. Issues de GitHub    ← issue_generator_agent.py
      ├──▶ 5. Tutorial            ← tutorial_agent.py
      ├──▶ 6. Código base         ← codegen_agent.py
      └──▶ 7. Bundle ZIP          ← bundle_service
```

### El OpenSpec

El `OpenSpecDoc` es el contrato central que todos los agentes downstream consumen:

```json
{
  "project":        { "name", "sector", "target_users", "problem" },
  "architecture":   { "type", "name", "stack", "difficulty" },
  "requirements":   [{ "id", "title", "description", "acceptance_criteria" }],
  "user_stories":   [{ "id", "actor", "goal", "benefit" }],
  "modules":        ["Auth", "Reservas", "Admin"],
  "milestones":     ["Milestone 1: Setup", "..."],
  "data_entities":  [{ "name", "fields", "relations" }],
  "api_endpoints":  [{ "method", "path", "auth_required", "request_body", "response" }],
  "business_rules": ["Un usuario solo puede ver sus propios proyectos"],
  "dev_steps":      [{ "step", "title", "commands" }],
  "constraints":    { "delivery", "environments" }
}
```

Mejorar el OpenSpec (su esquema o el prompt del agente) mejora automáticamente todos los artefactos downstream.

---

## Arquitecturas soportadas

El `ArchitectureAgent` selecciona la arquitectura óptima según el nivel técnico del usuario y el tipo de producto. El `FallbackGenerator` incluye scaffolds deterministas para cada una.

| ID | Nombre | Nivel | Tipo |
|----|--------|-------|------|
| `LARAVEL_MONOLITH` | Laravel 11 REST API | Principiante | Web |
| `LARAVEL_INERTIA_REACT` | Laravel + Inertia + React | Intermedio | Web |
| `LARAVEL_INERTIA_VUE` | Laravel + Inertia + Vue 3 | Intermedio | Web |
| `DJANGO_REST` | Django 5 + DRF | Avanzado / dominio pesado | Web |
| `NEXTJS_APP` | Next.js 15 App Router | Intermedio | Web |
| `NESTJS_REACT` | NestJS 11 + React desacoplado | Intermedio/Avanzado | Web |
| `REACT_EXPRESS` | React + Express Node.js | Principiante | Web |
| `FASTAPI_AI` | FastAPI + LangChain/LangGraph | Avanzado | Web/IA |
| `FLUTTER_FASTAPI` | Flutter + FastAPI | Avanzado | Mobile |
| `REACT_NATIVE_NESTJS` | React Native (Expo) + NestJS | Avanzado | Mobile |
| `TAURI_FASTAPI` | Tauri (Rust) + FastAPI | Avanzado | Desktop |
| `ELECTRON_NESTJS` | Electron + NestJS | Intermedio | Desktop |

---

## Configuración LLM

### Fallback chain por tipo de tarea

El orden de proveedores cloud es configurable en tiempo real desde `/ai-settings`. El orden por defecto es Groq → OpenAI → Gemini.

| Tipo de tarea | Cadena de fallback |
|--------------|-------------------|
| Decisión tecnológica | Ollama Gemma 4 → Groq → OpenAI → Gemini → catálogo determinista |
| Requisitos, arquitectura, spec | IA configurada → siguiente IA disponible → determinístico |
| Generación de código | Ollama Gemma 4 → Groq → OpenAI → Gemini → FallbackGenerator |
| Tutorial, propuestas, features | IA configurada → siguiente IA disponible → determinístico |

Las propuestas tecnológicas y la generación de código prueban todas las IA
disponibles antes de recurrir a templates. Las respuestas de IA se validan
contra el tipo de producto: una propuesta móvil, desktop o Django injustificada
se descarta y se intenta con el siguiente modelo.

### Perfiles locales Gemma 4

```bash
ollama pull gemma4:26b-a4b-it-qat
ollama pull gemma4:31b
```

| Equipo | Modelo recomendado | Uso |
|--------|--------------------|-----|
| Ordenador normal, sin GPU potente | `gemma4:26b-a4b-it-qat` | Razonamiento, agentes, planificación y código con activación eficiente |
| Buena GPU o bastante RAM | `gemma4:31b` | Arquitectura, refactorización, análisis de repositorios y código largo |

El perfil equilibrado es el predeterminado. Para activar el perfil de máxima
calidad, establecer `OLLAMA_REASONING_MODEL` y `OLLAMA_CODE_MODEL` como
`gemma4:31b`.

### Estado verificado de la IA local

La integración local se comprobó el **25 de junio de 2026** con Ollama
`0.30.10` y el servicio FastAPI ejecutándose en `http://127.0.0.1:8003`:

| Prueba | Modelo | Resultado |
|--------|--------|-----------|
| Inferencia directa de razonamiento | `llama3.1:latest` | JSON válido en 30,59 s |
| Inferencia directa de código | `qwen2.5-coder:latest` | Respuesta JSON en 15,75 s |
| Agente `/suggest-features` | `qwen2.5-coder:latest` | 10 funciones generadas en 17,79 s |
| Propuesta tecnológica completa | modelos locales de 7-8B | Respuesta estructurada, rechazada cuando incumple las reglas de arquitectura; fallback correcto |

Esto confirma que la IA local funciona dentro del pipeline. Los modelos
pequeños instalados son adecuados para desarrollo y pruebas, aunque pueden
producir propuestas arquitectónicas menos fiables. La validación descarta, por
ejemplo, Django cuando el dominio no justifica un backend pesado. Los perfiles
Gemma 4 recomendados ofrecen más capacidad, pero requieren aproximadamente
16 GB (`26b-a4b-it-qat`) o 20 GB (`31b`) de descarga y memoria suficiente.

### Variables LLM en `.env`

```env
LLM_PROVIDER=groq                          # proveedor por defecto

GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash

OLLAMA_BASE_URL=http://localhost:11434     # solo si tienes Ollama instalado
OLLAMA_REASONING_MODEL=gemma4:26b-a4b-it-qat
OLLAMA_CODE_MODEL=gemma4:26b-a4b-it-qat
```

---

## Variables de entorno — referencia completa

### `.env` (raíz del monorepo)

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `DATABASE_URL` | Sí | PostgreSQL connection string |
| `JWT_SECRET` | Sí | Clave de firma del access token |
| `JWT_REFRESH_SECRET` | Sí | Clave de firma del refresh token |
| `JWT_EXPIRES_IN` | No | Duración del access token (default: `1d`) |
| `REDIS_HOST` | No | Host local de Redis (recomendado: `127.0.0.1`) |
| `REDIS_PORT` | No | Puerto Redis desde el host (default del proyecto: `6380`) |
| `REDIS_PUBLIC_PORT` | No | Puerto externo mapeado (default: `6380`) |
| `AI_SERVICE_URL` | No | URL del AI service (default: `http://127.0.0.1:8003`) |
| `CAPTCHA_ENABLED` | No | Activa CAPTCHA en backend (`true`/`false`, default: `false`) |
| `CAPTCHA_PROVIDER` | No | `turnstile`, `hcaptcha` o `recaptcha` |
| `CAPTCHA_SECRET_KEY` | No* | Secreto del proveedor (requerido si CAPTCHA_ENABLED=true) |
| `VITE_CAPTCHA_PROVIDER` | No | Proveedor del widget frontend |
| `VITE_CAPTCHA_SITE_KEY` | No* | Clave pública del widget (requerida si CAPTCHA activado) |
| `MINIO_ACCESS_KEY` | No | Credencial MinIO (default: `progresia`) |
| `MINIO_SECRET_KEY` | No | Secreto MinIO (default: `progresia_secret`) |
| `GITHUB_TOKEN` | No | Token para publicar issues en GitHub |
| `ADMIN_JWT_SECRET` | No | Clave JWT del panel admin (default: `admin_change_me`) |
| `ADMIN_EMAIL` | No | Email del admin inicial (default: `admin@progresia.local`) |
| `ADMIN_USERNAME` | No | Username del admin inicial |
| `ADMIN_PASSWORD` | No | Password del admin inicial |

### `apps/ai-service/.env`

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `LLM_PROVIDER` | No | Proveedor LLM por defecto (`groq`) |
| `GROQ_API_KEY` | No* | Al menos una clave LLM es requerida |
| `OPENAI_API_KEY` | No* | |
| `GEMINI_API_KEY` | No* | |
| `OLLAMA_BASE_URL` | No | URL de Ollama local |
| `QDRANT_URL` | No | URL de Qdrant (default: `http://localhost:6333`) |

> Las claves de API nunca se commitean. Solo existen en archivos `.env` (gitignored).

---

## API — endpoints principales

### Autenticación (`/api/auth`)

```
POST /api/auth/register   → crea cuenta, devuelve { accessToken, refreshToken, user }
POST /api/auth/login      → devuelve { accessToken, refreshToken, user }
POST /api/auth/refresh    → rota el refresh token
POST /api/auth/logout     → invalida el refresh token
```

El registro crea la cuenta activa al instante — no hay verificación por email en desarrollo.

### Proyectos (`/api/projects`)

```
GET    /api/projects                    → lista proyectos del usuario
POST   /api/projects                    → crea proyecto + workspace
GET    /api/projects/:idOrSlug          → detalle (acepta UUID o slug)
PATCH  /api/projects/:idOrSlug          → actualiza
DELETE /api/projects/:idOrSlug          → elimina
```

### Pipeline SDD (`/api/jobs`)

```
POST /api/jobs/generate-requirements    → inicia job de requisitos
POST /api/jobs/recommend-architecture   → inicia job de arquitectura
POST /api/jobs/generate-openspec        → inicia job de OpenSpec
POST /api/jobs/generate-issues          → inicia job de issues
POST /api/jobs/generate-tutorial        → inicia job de tutorial
POST /api/jobs/generate-code            → inicia job de código
GET  /api/jobs/:jobId                   → estado del job (pending/active/completed/failed)
```

### Especificaciones (`/api/specifications`)

```
GET  /api/specifications/project/:id           → todas las specs del proyecto
GET  /api/specifications/:id                   → spec individual
GET  /api/specifications/:id/export/pdf        → descarga PDF
GET  /api/specifications/:id/export/markdown   → descarga Markdown
```

### Artefactos (`/api/artifacts`)

```
POST /api/artifacts/project/:id/generate   → genera el bundle ZIP
GET  /api/artifacts/project/:id            → estado del bundle
GET  /api/artifacts/:bundleId/download-url → URL firmada de descarga (1h)
```

### AI Service (`http://localhost:8003`)

```
GET  /health                     → estado del servicio
GET  /docs                       → Swagger interactivo
POST /suggest-features           → sugerencias de features por sector
POST /propose-tech               → 3 propuestas de stack técnico
GET  /config/llm                 → estado actual del LLM (proveedor, modelos, cadena)
PATCH /config/llm                → cambiar proveedor/modelos en caliente
GET  /config/llm/provider-models → modelos disponibles por proveedor
GET  /ollama/models              → modelos instalados en Ollama local
```

---

## Autenticación y seguridad

- **JWT** — access token (1 día por defecto) + refresh token rotativo (7 días)
- **CAPTCHA** — configurable por proveedor (Turnstile, hCaptcha, reCAPTCHA); desactivado en desarrollo
- **Ownership** — todos los endpoints de proyectos validan que el usuario sea el propietario
- **Admin aislado** — `ADMIN_JWT_SECRET` separado; tokens admin no válidos en la app normal
- **Secretos fuera del código** — las claves de API solo existen en `.env` (gitignored)

---

## Observabilidad con Sentry

Sentry es opcional y está integrado en React, NestJS y FastAPI. Sin DSN, los
SDK permanecen desactivados y no alteran el arranque local.

```env
# NestJS API
SENTRY_DSN=
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=<git-sha>
SENTRY_TRACES_SAMPLE_RATE=0.1

# React (se inyecta durante npm run build)
VITE_SENTRY_DSN=
VITE_SENTRY_ENVIRONMENT=production
VITE_SENTRY_RELEASE=<git-sha>
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1

# FastAPI AI service
AI_SENTRY_DSN=
AI_SENTRY_ENVIRONMENT=production
AI_SENTRY_RELEASE=<git-sha>
AI_SENTRY_TRACES_SAMPLE_RATE=0.1
AI_SENTRY_ENABLE_LOGS=false
```

Se recomienda crear un proyecto Sentry por aplicación. La configuración elimina
usuarios, cuerpos, cookies, cabeceras de autorización y API keys antes de enviar
eventos. `sendDefaultPii` y Session Replay permanecen desactivados.

Para obtener stack traces legibles del frontend, CI puede subir source maps
definiendo `SENTRY_AUTH_TOKEN`, `SENTRY_ORG` y `SENTRY_PROJECT`. El token debe
guardarse exclusivamente como secreto del repositorio.

El health check de la API indica `observability.sentry: true|false`, pero nunca
expone el DSN.

---

## Panel de administración

Ruta: `http://localhost:5173/gestion-usuarios` — no aparece en ninguna navegación normal.

```bash
# Crear el usuario administrador de desarrollo
cd apps/api && npm run prisma:seed
```

| Campo | Valor por defecto |
|-------|-----------------|
| Email | `admin@progresia.local` |
| Username | `seurobman` |
| Password | `$eurobman2026` |

> Cambiar estos valores en `.env` antes de cualquier despliegue.

Los endpoints admin requieren `Authorization: Bearer <admin_token>` obtenido en `POST /api/admin/auth/login`.

```
POST /api/admin/auth/login     → acepta email o username
GET  /api/admin/users          → lista usuarios (con ?search=)
POST /api/admin/users          → crear usuario
PATCH /api/admin/users/:id     → editar usuario
DELETE /api/admin/users/:id    → eliminar usuario
GET  /api/admin/projects       → lista proyectos (con ?search=)
```

---

## Tests

```bash
# Desde la raíz
npm test
npm run lint
npm run typecheck
npm run build
npm run openspec:check

# AI Service
cd apps/ai-service
python -m pytest
python -m ruff check app tests
```

Estado verificado el 25 de junio de 2026:

- Frontend: **11 pruebas superadas**
- API: **50 pruebas superadas**
- AI Service: **150 pruebas superadas y 70 omitidas condicionalmente**
- Total ejecutado correctamente: **211 pruebas**
- Lint, typecheck, build y validación OpenSpec: **correctos**

La CI ejecuta los controles principales en cada push y pull request.

---

## Estructura del monorepo

```
progresia/
├── apps/
│   ├── api/                         NestJS API
│   │   ├── prisma/
│   │   │   ├── schema.prisma        modelos: User, Workspace, Project, Idea,
│   │   │   │                        Specification, ArtifactBundle
│   │   │   ├── migrations/
│   │   │   └── seed.ts              datos iniciales de desarrollo
│   │   └── src/modules/
│   │       ├── auth/                JWT + refresh token rotation
│   │       ├── projects/            CRUD + slug generation + UUID/slug dual-lookup
│   │       ├── ideas/               intake de la idea del usuario
│   │       ├── specifications/      pipeline SDD + exportación PDF/MD
│   │       ├── artifacts/           bundle ZIP + generación de código
│   │       └── ai-service/          cliente HTTP hacia FastAPI
│   │
│   ├── ai-service/                  FastAPI — Agentes IA
│   │   └── app/
│   │       ├── agents/
│   │       │   ├── requirements_agent.py
│   │       │   ├── architecture_agent.py
│   │       │   ├── openspec_agent.py    ← agente central SDD
│   │       │   ├── issue_generator_agent.py
│   │       │   ├── tutorial_agent.py
│   │       │   ├── codegen_agent.py
│   │       │   └── fallback/stacks/     19 scaffolds deterministas por stack
│   │       ├── schemas/
│   │       │   ├── openspec.py          OpenSpecDoc — fuente de verdad
│   │       │   ├── idea.py
│   │       │   └── architecture.py
│   │       ├── core/
│   │       │   └── llm.py               get_llm() con fallback chain configurable
│   │       └── api/
│   │           ├── specifications.py    endpoints del pipeline SDD
│   │           ├── llm_config.py        configuración LLM en caliente
│   │           └── rag.py               búsqueda y consulta RAG
│   │
│   └── web/                         React 19 Frontend
│       └── src/
│           ├── routes/
│           │   ├── NewProjectPage.tsx   wizard conversacional SDD (6 pasos)
│           │   ├── ProjectDetailPage.tsx pipeline + 7 tarjetas de resultado
│           │   └── DashboardPage.tsx
│           ├── hooks/
│           │   └── useGeneratePipeline.ts  máquina de estados del pipeline
│           ├── features/auth/
│           └── lib/api.ts
│
├── packages/
│   ├── config/       configuración ESLint/TypeScript compartida
│   ├── contracts/    contratos e interfaces cross-service
│   └── shared/       utilidades TypeScript compartidas
│
├── docker-compose.yml
├── .env.example
└── .github/workflows/
    ├── ci.yml              lint + types + tests + build
    └── dependency-review.yml
```

---

## Notas de plataforma (Windows)

- **Redis** — mapeado al puerto 6380 (Docker Desktop ocupa el 6379)
- **AI Service** — usar el puerto 8003 (Docker Desktop ocupa 8000 y 8001)
- **Hosts locales** — usar `127.0.0.1` para PostgreSQL, Redis y MinIO
- **NestJS** — no usar `nest start --watch`; compilar con `tsc` y lanzar con `node`
- **Prisma** — detener el servidor API antes de `npx prisma generate` (lock de DLL)

---

## Licencia

Copyright © 2026 Roberto Manca. Todos los derechos reservados.
Este proyecto es propietario y confidencial. Queda prohibida su copia, modificación, distribución o reutilización sin autorización expresa por escrito.
