# ProgresIA Studio — Documento de Proyecto Final de Máster

> **Máster en Desarrollo de Software con IA**
> Proyecto final — plataforma educativa de generación de MVPs guiada por IA

---

## 1. Descripción general

**ProgresIA Studio** es una plataforma web que convierte cualquier idea de producto en un MVP técnico completo y coherente, siguiendo la metodología **SDD (Spec-Driven Development)**. El usuario no recibe código mágico: aprende a especificar antes de generar. Cada paso del pipeline le explica la decisión arquitectónica, el tradeoff y cómo implementarlo.

### El problema que resuelve

Los desarrolladores junior y estudiantes se lanzan a codificar sin especificar. El resultado son proyectos sin estructura, sin documentación y difíciles de mantener. Las herramientas de IA actuales (GitHub Copilot, ChatGPT) generan código sin contexto previo, lo que agrava el problema.

### La solución

Un pipeline orquestado de agentes de IA donde **cada artefacto depende del anterior**: requisitos → arquitectura → especificación técnica (OpenSpec) → issues de GitHub → tutorial de implementación → código base → bundle ZIP descargable. El usuario entiende cada paso porque la IA explica su razonamiento.

### Diferenciador clave

No es un generador de código. Es una **plataforma pedagógica**: el OpenSpec que genera el sistema puede ser leído por cualquier LLM para continuar el desarrollo, y el tutorial generado enseña exactamente cómo construir lo que se ha especificado.

---

## 2. Metodología SDD — El Pipeline

```
Wizard (idea del usuario)
        │
        ▼
1. Requisitos        ← requirements_agent.py    → Specification(REQUIREMENTS)
        │
        ▼
2. Arquitectura      ← architecture_agent.py    → Specification(ARCHITECTURE)
        │
        ▼
3. OpenSpec ★        ← openspec_agent.py         → Specification(OPENSPEC)
        │                  [FUENTE DE VERDAD]
        ├──────────────────────────────────────────┐
        ▼                                          ▼
4. Issues GitHub     ← issue_generator_agent.py  5. Tutorial  ← tutorial_agent.py
        │                                          │
        └──────────────┬───────────────────────────┘
                       ▼
               6. Código base       ← codegen_agent.py
                       │
                       ▼
               7. Bundle ZIP        ← artifacts.service.ts
                                       (validación + secrets scan + export)
```

El **OpenSpec** es el artefacto central: un documento JSON estructurado con entidades de datos, contratos de API, reglas de negocio y pasos de implementación. Todos los agentes downstream lo leen; si se mejora el OpenSpec, todos los artefactos mejoran automáticamente.

### Wizard del proyecto (6 pasos)

| Paso | Pregunta | Campo resultante |
|------|----------|-----------------|
| 1 | Tipo de producto | `productType` (web / mobile / desktop / api / saas / ai_tool) |
| 2 | Sector | `sector` |
| 3 | Nivel técnico | `complexity` → `BEGINNER / INTERMEDIATE / ADVANCED` |
| 4 | Arquitectura preferida | `architectureStyle` (auto para mobile/desktop) |
| 5 | Datos e IA | `dataNeeds`, `aiNeeds` |
| 6 | Despliegue | `deploymentTarget` |

### Arquitecturas soportadas

| ID | Stack | Nivel | Tipo |
|----|-------|-------|------|
| `LARAVEL_MONOLITH` | Laravel 11 + Blade | Principiante | Web |
| `LARAVEL_INERTIA_REACT` | Laravel + Inertia.js + React | Intermedio | Web |
| `LARAVEL_INERTIA_VUE` | Laravel + Inertia.js + Vue | Intermedio | Web |
| `DJANGO_REST` | Django 5 + DRF | Avanzado / dominio pesado | Web |
| `REACT_EXPRESS` | React + Express.js | Principiante | Web |
| `NEXTJS_APP` | Next.js 15 App Router | Intermedio | Web |
| `NESTJS_REACT` | NestJS 11 + React desacoplado | Intermedio/Avanzado | Web |
| `FASTAPI_AI` | FastAPI + LangChain + LangGraph | Avanzado | Web/IA |
| `FLUTTER_FASTAPI` | Flutter + FastAPI | Principiante Mobile | Mobile |
| `REACT_NATIVE_NESTJS` | React Native (Expo) + NestJS | Intermedio Mobile | Mobile |
| `ELECTRON_NESTJS` | Electron + NestJS + SQLite | Principiante Desktop | Desktop |
| `TAURI_FASTAPI` | Tauri (Rust) + FastAPI + SQLite | Intermedio Desktop | Desktop |

---

## 3. Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        MONOREPO                             │
│                                                             │
│  apps/web/          → React 19 + Vite        :5173          │
│  apps/api/          → NestJS 11 + Prisma     :3000          │
│  apps/ai-service/   → FastAPI + LangChain    :8003          │
│                                                             │
│  Infraestructura Docker:                                    │
│  ├── PostgreSQL 16                           :5432          │
│  ├── Redis 7                                 :6380 *        │
│  ├── MinIO (object storage)                  :9000          │
│  ├── Qdrant (vector DB)                      :6333          │
│  └── Mailpit (SMTP dev)                      :1025/:8025    │
│                                                             │
│  * Redis en 6380 para evitar conflicto con Docker Desktop   │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de datos completo

```
Usuario (browser)
    │  HTTP/JSON
    ▼
apps/web (React)
    │  axios → http://localhost:3000/api
    ▼
apps/api (NestJS)
    │  Prisma ORM → PostgreSQL (persistencia)
    │  BullMQ → Redis (cola de jobs asíncrona)
    │  fetch → http://localhost:8003 (ai-service)
    ▼
apps/ai-service (FastAPI)
    │  LangChain → Groq / OpenAI / Gemini / Ollama (LLMs)
    │  Pydantic → validación y estructuración de salidas
    └─ Qdrant (búsqueda vectorial para RAG)
```

---

## 4. Frontend — `apps/web/`

**Puerto:** 5173

### Stack

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| **React** | 19.1 | UI framework — concurrent rendering, Suspense |
| **Vite** | 6.3+ | Bundler + dev server — HMR instantáneo |
| **Tailwind CSS** | 4.3 | Estilos utility-first — CSS custom properties nativas |
| **React Router** | 7.6 | Enrutamiento SPA |
| **TanStack Query** | 5.81 | Server state, caché, invalidación automática |
| **React Hook Form** | 7.59 | Formularios performantes sin re-renders |
| **Zod** | 4.4 | Validación de esquemas en cliente |
| **Axios** | 1.10 | HTTP client con interceptores de auth |
| **Lucide React** | 1.21 | Iconografía |
| **Vitest** | 4.1 | Testing unitario de autenticación, instrumentación y UI crítica |
| **Sentry React** | 10.61 | Errores y rendimiento, sin Session Replay ni PII |

### Páginas y rutas

| Ruta | Componente | Descripción |
|------|-----------|-------------|
| `/login` | `AuthPage` (mode=login) | Login con CAPTCHA integrado |
| `/register` | `AuthPage` (mode=register) | Registro con CAPTCHA integrado |
| `/` | `DashboardPage` | Listado de workspaces y proyectos |
| `/projects/new` | `NewProjectPage` | Wizard SDD de 6 pasos |
| `/projects/:projectId` | `ProjectDetailPage` | Pipeline + tarjetas de resultado con polling |
| `/ai-settings` | `AiSettingsPage` | Configuración de proveedores LLM en tiempo real |
| `/gestion-usuarios` | `AdminPage` | Panel admin (ruta oculta, auth separada) — `seurobman` / `$eurobman2026` |
| `*` | `NotFoundPage` | 404 con navegación de vuelta al dashboard |

### Características de la UI

- **Wizard conversacional**: cada paso del wizard muestra mensajes de la IA con efecto de cola (typewriter)
- **Polling automático**: `ProjectDetailPage` hace polling cada 2.500ms mientras el pipeline está activo
- **Auth JWT**: interceptor Axios rota el access token automáticamente usando el refresh token
- **CAPTCHA integrado**: widget estilo Cloudflare Turnstile en login y registro — se auto-verifica
- **Admin panel**: completamente aislado del app normal, usa `sessionStorage` y `ADMIN_JWT_SECRET` distinto
- **Configuración IA**: página `/ai-settings` para cambiar proveedor LLM y modelos en caliente

---

## 5. Backend de Gestión — `apps/api/`

**Puerto:** 3000

### Stack

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| **NestJS** | 11.1 | Framework Node.js — módulos, DI, guards, interceptors |
| **Prisma** | 6.19 | ORM type-safe — migrations, query builder |
| **PostgreSQL** | 16 | Base de datos relacional principal |
| **BullMQ** | 5.79 | Cola de jobs distribuida sobre Redis |
| **@nestjs/jwt + Passport** | — | Autenticación — access token (1 día) + refresh rotativo (7 días) |
| **class-validator** | 0.15 | Validación de DTOs con decorators |
| **@nestjs/swagger** | 11.2 | Documentación OpenAPI automática en `/api/docs` |
| **@nestjs/throttler** | 6.5 | Rate limiting — 300 req/min por IP |
| **bcryptjs** | 3.0 | Hash de contraseñas (bcrypt, coste 10) |
| **JSZip** | 3.10 | Generación de bundles ZIP en memoria |
| **MinIO SDK** | 8.0 | Object storage para ZIPs generados |
| **TypeScript** | 5.9 | Tipado estático end-to-end |
| **Sentry NestJS** | 10.61 | Captura de errores 5xx y trazas con sanitización |

### Módulos NestJS

```
src/modules/
├── auth/           JWT register/login/refresh/logout + admin auth separado
├── users/          Perfil de usuario + listado admin
├── workspaces/     CRUD + gestión de miembros
├── projects/       CRUD + slug único + lookup UUID/slug dual
├── ideas/          Intake del wizard → modelo Idea en DB
├── specifications/ Pipeline SDD — cola BullMQ → ai-service → DB
├── artifacts/      Bundle ZIP + code generation + validación + push GitHub
├── github/         Integración con API de GitHub (crear repos, push código)
├── ai-service/     Cliente HTTP hacia FastAPI (AiServiceClient)
├── llm-config/     Proxy GET/PATCH /llm-config → AI service (configuración LLM)
├── jobs/           Gestión de jobs BullMQ — cola asíncrona del pipeline
├── storage/        Object storage (MinIO SDK)
├── health/         Health check con estado de DB
└── admin/          Panel admin — usuarios + proyectos (guard AdminJwtGuard)
```

### Seguridad implementada

- **Guard de ownership**: `ensureProjectAccess(projectId, userId)` en todos los métodos — acepta UUID o slug
- **Admin auth aislada**: `AdminJwtGuard` verifica `payload.type === "admin"` y usa `ADMIN_JWT_SECRET` distinto
- **CAPTCHA**: validación en register y login — soporta Turnstile (Cloudflare), hCaptcha y reCAPTCHA (Google)
- **Rate limiting**: throttler en todos los endpoints públicos (300 req/min por IP)
- **Secrets scanning**: en `validateBundle()` — detecta credenciales hardcodeadas en código generado antes de permitir descarga
- **Refresh token rotation**: cada uso invalida el anterior (previene replay attacks)
- **Observabilidad privada**: Sentry elimina usuarios, cuerpos, cookies, cabeceras de autorización y API keys antes de enviar eventos

---

## 6. Backend de IA — `apps/ai-service/`

**Puerto:** 8003

### Stack

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| **FastAPI** | 0.115 | Framework Python asíncrono — endpoints, validación automática |
| **Uvicorn** | 0.35 | Servidor ASGI — `--reload` en desarrollo |
| **Pydantic v2** | 2.11 | Modelos de datos + validación + `with_structured_output` |
| **LangChain** | 0.3 | Orquestación de LLMs — chains, prompts, parsers |
| **LangGraph** | 0.5 | Grafos de agentes — flujos con estado y condiciones |
| **LangChain-Groq** | 1.1 | Proveedor LLM primario (llama-3.3-70b) |
| **LangChain-OpenAI** | 0.3 | Proveedor LLM fallback (gpt-4o-mini) |
| **LangChain-Google GenAI** | 2.0 | Proveedor LLM fallback secundario (gemini-2.0-flash) |
| **LangChain-Ollama** | 0.3 | LLM local — sin coste, privacidad total, sin API key |
| **Qdrant Client** | 1.9 | Búsqueda vectorial para RAG |
| **Ruff** | 0.12 | Linter + formatter Python |
| **pytest** | 8.4 | Testing |
| **Sentry SDK** | 2.63 | Errores, trazas y logs opcionales en FastAPI |

### Agentes implementados (10)

| Agente | Archivo | Tarea LLM | Descripción |
|--------|---------|-----------|-------------|
| `ProductAgent` | `product_agent.py` | general | Análisis inicial de idea — valida alcance y funcionalidades clave |
| `RequirementsAgent` | `requirements_agent.py` | reasoning | Requisitos funcionales, no funcionales y user stories |
| `ArchitectureAgent` | `architecture_agent.py` | reasoning | Stack recomendado + learning path + señales de upgrade por arquitectura |
| `SupervisorAgent` | `supervisor_agent.py` | spec | Orquestador LangGraph del OpenSpec — enruta a fallback si los requisitos son insuficientes |
| `OpenSpecAgent` | `openspec_agent.py` | spec | OpenSpec completo (JSON estructurado) — fuente de verdad para agentes downstream |
| `IssueGeneratorAgent` | `issue_generator_agent.py` | reasoning | Issues de GitHub con milestones, labels y prioridad a partir del OpenSpec |
| `TutorialAgent` | `tutorial_agent.py` | general | Tutorial paso a paso con comandos específicos por arquitectura |
| `CodeGenerationAgent` | `codegen_agent.py` | code | Scaffold de código — LLM-first usando `data_entities` y `api_endpoints` del OpenSpec; delega en `FallbackGenerator` (19 stacks) si el LLM falla |
| `TechProposalAgent` | `tech_proposal_agent.py` | general | 3 propuestas de stack con ventajas, limitaciones y learning outcomes |
| `RAGAgent` | `rag_agent.py` | general | Respuestas fundamentadas en documentos indexados — retrieval sobre Qdrant + citas de fuente |

### FallbackGenerator — Scaffolds de arquitectura (19 stacks)

Cuando el LLM no está disponible o falla, el `CodeGenerationAgent` delega en el `FallbackGenerator`, que produce un scaffold estructurado determinístico según el `architecture_type` del OpenSpec.

El `FallbackGenerator` detecta el stack del proyecto (`detector.py`) y selecciona el template adecuado entre 19 stacks disponibles (`fallback/stacks/`). Cada stack genera archivos de proyecto reales: estructura de directorios, configuración, `package.json` / `pyproject.toml`, `docker-compose.yml`, `Dockerfile`, README y esquema de base de datos.

| Stack | Archivo | Cuándo se usa |
|-------|---------|---------------|
| `nextjs.py` | Next.js 15 App Router + Prisma | Default web moderno |
| `nestjs.py` | NestJS 11 + React + Prisma + PostgreSQL | Proyectos web desacoplados |
| `express_ts.py` | Express.js + TypeScript + Prisma | BEGINNER / `REACT_EXPRESS` |
| `react_vite.py` | React 19 + Vite + Tailwind | SPA puro sin backend propio |
| `vue_vite.py` | Vue 3 + Vite + Pinia | Alternativa Vue |
| `angular.py` | Angular + TypeScript + RxJS | Proyectos empresariales |
| `svelte­kit.py` | SvelteKit + Prisma | Apps web ligeras |
| `astro.py` | Astro + React | Sites con SSR/SSG |
| `fastapi_ai.py` | FastAPI + LangChain + PostgreSQL | Proyectos IA / `FASTAPI_AI` |
| `flask_app.py` | Flask + SQLAlchemy + PostgreSQL | Python BEGINNER |
| `go_gin.py` | Go + Gin + PostgreSQL | APIs de alto rendimiento |
| `laravel.py` | Laravel 11 + Blade/Inertia | Stack PHP / `LARAVEL_*` |
| `node_postgres.py` | Node.js + PostgreSQL (sin ORM) | Backend minimalista |
| `firebase.py` | React + Firebase + Tailwind | Serverless / sin backend propio |
| `supabase.py` | React + Supabase + Tailwind | BaaS con auth incluida |
| `mobile.py` | Flutter / React Native | `productType: mobile` |
| `desktop.py` | Tauri / Electron | `productType: desktop` |
| `tauri.py` | Tauri + React + Rust | Desktop nativo / `TAURI_FASTAPI` |
| `universal.py` | Scaffold genérico | Fallback absoluto |

**Flujo de generación de código:**
```
CodeGenerationAgent.generate(payload)
    │
    ├─ LLM disponible → genera archivos con structured output (calidad máxima)
    │
    └─ LLM falla / no disponible
           │
           └─ FallbackGenerator.generate()
                  │
                  ├─ StackDetector.detect(payload) → identifica stack
                  └─ StackModule.build(ctx) → archivos determinísticos
```

### Cadena de fallback LLM (por tipo de tarea)

El orden de proveedores cloud es configurable en tiempo real desde `/ai-settings` (campo `cloud_order`). El orden por defecto es **Groq → OpenAI → Gemini**.

```
Tipo "reasoning" (requisitos, arquitectura):
  Groq → OpenAI → Gemini → Ollama (Gemma 4) → determinístico

Tipo "spec" (OpenSpec):
  OpenAI → Gemini → Groq → Ollama (Gemma 4) → determinístico

Tipo "code" (generación de código):
  Ollama (Gemma 4) → Groq → OpenAI → Gemini → FallbackGenerator

Tipo "general" (features, tutorial, propuestas):
  Ollama (Gemma 4) → Groq → OpenAI → Gemini → catálogo determinístico
```

En la decisión tecnológica y la generación de código se prueban todos los
modelos disponibles antes de usar catálogos o scaffolds deterministas. Las
propuestas de cada modelo se validan contra el tipo de producto y las
restricciones obligatorias. Si se configura un proveedor forzado desde
`/ai-settings`, se intenta primero y después continúa la cadena completa.

### Validación práctica de la IA local

El 25 de junio de 2026 se verificó el flujo local con Ollama `0.30.10`,
FastAPI en el puerto `8003` y los modelos ya disponibles en el equipo:
`llama3.1:latest` para razonamiento y `qwen2.5-coder:latest` para código.

La inferencia directa devolvió JSON válido en 30,59 y 15,75 segundos,
respectivamente. Una llamada real a `/suggest-features` generó diez
funcionalidades contextualizadas en 17,79 segundos, confirmando que el agente
utiliza el modelo local y no únicamente el catálogo fijo.

La prueba de `/propose-tech` también confirmó el funcionamiento de las barreras
de calidad: el modelo produjo una respuesta estructurada, pero recomendó Django
para un proyecto educativo que no requería un backend pesado. La propuesta fue
rechazada y el sistema continuó por la cadena de fallback. Este comportamiento
es intencionado: la plataforma prioriza IA, pero no acepta una salida que
incumpla las restricciones arquitectónicas.

### Endpoints del AI service

```
Pipeline de generación
POST /analyze-idea              → ProductAgent — análisis de idea inicial
POST /generate-requirements     → RequirementsAgent — requisitos y user stories
POST /recommend-architecture    → ArchitectureAgent — stack + learning path
POST /generate-openspec         → SupervisorAgent → OpenSpecAgent — OpenSpec completo
POST /propose-tech              → TechProposalAgent — 3 propuestas de stack
POST /generate-issues           → IssueGeneratorAgent — issues GitHub
POST /generate-tutorial         → TutorialAgent — tutorial paso a paso
POST /generate-code             → CodeGenerationAgent — archivos de scaffold
POST /suggest-features          → sugerencias de funcionalidades por sector

Configuración LLM (en caliente, sin reiniciar)
GET  /config/llm                → estado actual (proveedor, modelos, enrutamiento, cloud_order)
PATCH /config/llm               → forzar proveedor / cambiar modelos / reordenar fallback chain
GET  /config/llm/provider-models → modelos disponibles en cada proveedor cloud (consulta APIs externas)
GET  /ollama/models             → modelos instalados en Ollama local

RAG (Retrieval-Augmented Generation)
POST /rag/index                 → indexar documentos en Qdrant
POST /rag/search                → búsqueda semántica en chunks
POST /rag/query                 → RAGAgent: retrieval + respuesta con citas
GET  /rag/eval/{collection}     → evaluación de coherencia del retrieval
DELETE /rag/collection/{name}   → eliminar colección de Qdrant

Salud
GET  /health                    → {"status": "ok", "service": "progresia-ai-service"}
```

### Patrón de resiliencia de agentes

```python
def generate(self, req):
    llm = get_llm("task_type")          # selecciona Groq / OpenAI / Gemini / Ollama
    if llm is not None:
        try:
            result = llm.with_structured_output(Schema).invoke(prompt)
            return result                # LLM path (calidad máxima)
        except Exception:
            pass                         # fallback si el LLM falla
    return self._deterministic(req)      # siempre produce un resultado válido
```

### OpenSpec — La fuente de verdad

```json
{
  "project":        { "name", "sector", "target_users", "problem", "description" },
  "architecture":   { "type", "name", "stack[]", "difficulty" },
  "requirements":   [{ "id", "title", "description", "acceptance_criteria[]" }],
  "user_stories":   [{ "id", "actor", "goal", "benefit" }],
  "modules":        ["Auth", "Reservas", "Pagos"],
  "milestones":     ["M1: Foundation", "M2: Core features"],
  "data_entities":  [{ "name", "description", "fields[]", "relations[]" }],
  "data_model":     { "storage_type", "technology", "orm", "relationships[]", "indexes[]", "mermaid_diagram" },
  "api_endpoints":  [{ "method", "path", "description", "auth_required", "request_body", "response" }],
  "business_rules": ["string"],
  "dev_steps":      [{ "step", "title", "description", "commands[]" }],
  "constraints":    { "delivery", "environments[]" }
}
```

Todos los campos son consumidos downstream:
- `requirements` → `IssueGeneratorAgent`
- `architecture.type` → `CodeGenerationAgent` (selección de template)
- `architecture.stack` → `TutorialAgent` (comandos específicos)
- `data_entities` → `CodeGenerationAgent` (schema Prisma real)
- `api_endpoints` → `CodeGenerationAgent` (stub OpenSpec en SDD docs)
- `dev_steps` → `TutorialAgent` (fases del tutorial)

---

## 7. Base de datos

### PostgreSQL 16

| Modelo | Campos clave | Descripción |
|--------|-------------|-------------|
| `User` | id, email, name, passwordHash, role | Usuarios del sistema |
| `RefreshToken` | userId, tokenHash, expiresAt | Tokens de refresco activos |
| `Workspace` | id, name, ownerId | Espacio de trabajo del equipo |
| `WorkspaceMember` | workspaceId, userId, role | Membresías con rol |
| `Project` | id, slug, name, sector, productType, status, workspaceId | Proyecto SDD — slug único |
| `Idea` | problem, targetUsers, coreFeatures[], complexity, needsAuth, needsAdminPanel, needsAi, mandatoryTechs | Intake del wizard |
| `Specification` | type (enum), status, content (JSON), projectId | Artefactos del pipeline |
| `ArtifactBundle` | manifest (JSON), generatedContent (JSON), status, specificationId | Bundle final descargable |

### Enums relevantes

```
SpecificationType:  REQUIREMENTS | ARCHITECTURE | OPENSPEC | ISSUES | TUTORIAL | CODE | TECH_PROPOSAL
ProjectStatus:      DRAFT → REQUIREMENTS_READY → SPEC_READY → GENERATING → GENERATED → REVIEW → DEPLOYED
Role:               ADMIN | OWNER | COLLABORATOR | REVIEWER
```

### Redis 7

Usado como broker de colas por **BullMQ**. Cada job del pipeline (generar requisitos, arquitectura, OpenSpec, etc.) se encola en Redis y se procesa de forma asíncrona, permitiendo al frontend hacer polling sin bloquear la respuesta HTTP.

---

## 8. Infraestructura

### Servicios Docker

| Servicio | Imagen | Puerto | Uso |
|---------|--------|--------|-----|
| `postgres` | `postgres:16` | 5432 | DB principal |
| `redis` | `redis:7` | 6380 | Cola BullMQ (6380 para evitar conflicto con Docker Desktop) |
| `minio` | `minio/minio` | 9000/9001 | Object storage (ZIPs generados) |
| `qdrant` | `qdrant/qdrant` | 6333 | Vectores para RAG |
| `mailpit` | `axllent/mailpit` | 1025/8025 | SMTP local (dev) |

### Variables de entorno — `apps/api/.env`

```env
NODE_ENV=development
API_PORT=3000

DATABASE_URL=postgresql://progresia:progresia@127.0.0.1:5432/progresia_studio

JWT_SECRET=<string aleatorio seguro>
JWT_EXPIRES_IN=1d

REDIS_HOST=127.0.0.1
REDIS_PORT=6380

AI_SERVICE_URL=http://127.0.0.1:8003

MINIO_ENDPOINT=127.0.0.1
MINIO_PORT=9000
MINIO_ACCESS_KEY=progresia
MINIO_SECRET_KEY=progresia_secret
MINIO_BUCKET=progresia-artifacts

CORS_ORIGINS=http://localhost:5173

CAPTCHA_ENABLED=false
CAPTCHA_PROVIDER=turnstile
CAPTCHA_SECRET_KEY=<Cloudflare Turnstile secret key>

SENTRY_DSN=
SENTRY_ENVIRONMENT=development
SENTRY_RELEASE=
SENTRY_TRACES_SAMPLE_RATE=0.1

ADMIN_JWT_SECRET=<string aleatorio seguro>
ADMIN_EMAIL=admin@progresia.local
ADMIN_USERNAME=seurobman
ADMIN_PASSWORD=<contraseña admin>
```

### Variables de entorno — `apps/ai-service/.env`

```env
LLM_PROVIDER=groq

GROQ_API_KEY=<clave de https://console.groq.com>
GROQ_MODEL=llama-3.3-70b-versatile

OPENAI_API_KEY=<clave de https://platform.openai.com>
OPENAI_MODEL=gpt-4o-mini

GEMINI_API_KEY=<clave de https://aistudio.google.com>
GEMINI_MODEL=gemini-2.0-flash

OLLAMA_BASE_URL=http://localhost:11434

QDRANT_URL=http://localhost:6333

AI_SENTRY_DSN=
AI_SENTRY_ENVIRONMENT=development
AI_SENTRY_RELEASE=
AI_SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Variables de entorno — `apps/web/.env`

```env
VITE_API_URL=http://localhost:3000/api

VITE_CAPTCHA_PROVIDER=turnstile
VITE_CAPTCHA_SITE_KEY=<Cloudflare Turnstile site key>

VITE_SENTRY_DSN=
VITE_SENTRY_ENVIRONMENT=development
VITE_SENTRY_RELEASE=
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## 9. Seguridad

- Las claves de API **nunca se commitean** — solo existen en archivos `.env` (gitignored)
- El panel de administración usa un JWT secret distinto (`ADMIN_JWT_SECRET`) y tokens con `type: "admin"` — incompatibles con tokens de usuario normal
- `validateBundle()` escanea el código generado con regex para detectar credenciales hardcodeadas antes de permitir la descarga
- El registro crea la cuenta en estado activo sin verificación de email (flujo simplificado para MVP educativo)
- CAPTCHA configurable: Cloudflare Turnstile, hCaptcha o reCAPTCHA
- Sentry opcional en las tres aplicaciones, con DSN independientes y filtrado de datos sensibles
- Source maps del frontend subidos solo desde CI mediante secretos de GitHub

### Observabilidad con Sentry

La plataforma incorpora Sentry en React, NestJS y FastAPI. La integración es
opcional: si no existe DSN, los SDK permanecen desactivados. Se recomienda crear
un proyecto Sentry por aplicación para separar errores del navegador, API y
servicio de IA.

La política de privacidad desactiva el envío de PII y elimina usuario, cookies,
cuerpo de la petición, `Authorization`, `x-api-key` y otras credenciales. El
health check de NestJS informa únicamente si la captura está configurada, sin
exponer el DSN.

---

## 10. Testing

| Capa | Framework | Cobertura actual |
|------|-----------|-----------------|
| AI Service | pytest 9.1 | 150 pruebas superadas, 70 omitidas condicionalmente |
| API — unitario e integración | Jest 30 + Supertest | 50 pruebas superadas |
| Frontend | Vitest 4 + Testing Library | 11 pruebas superadas |
| Calidad estática | ESLint, TypeScript, Ruff | lint y typecheck correctos |
| Entrega | Builds + OpenSpec validator | build completo y 13 cambios OpenSpec válidos |

**Resultado verificado el 25 de junio de 2026:** 211 pruebas superadas, además
de lint, typecheck, build y validación OpenSpec.

---

## 11. Lo que está hecho ✅

- [x] Wizard conversacional de 6 pasos con mensajes de IA en cola
- [x] Pipeline SDD completo: requisitos → arquitectura → OpenSpec → issues → tutorial → código → ZIP
- [x] 12 arquitecturas soportadas: 8 web + 2 mobile + 2 desktop
- [x] **FallbackGenerator con 19 stacks** — generación de código LLM-first; si el LLM falla, scaffold determinístico por stack (Next.js, NestJS, Express TS, React Vite, Vue, Angular, SvelteKit, Astro, FastAPI AI, Flask, Go Gin, Laravel, Node+Postgres, Firebase, Supabase, mobile, desktop, Tauri, universal)
- [x] Cadena de fallback LLM con 4 proveedores (Groq → OpenAI → Gemini → Ollama → determinístico)
- [x] Enrutamiento de tarea: cada tipo de agente usa el proveedor óptimo
- [x] **UI de configuración LLM** (`/ai-settings`) — cambio de proveedor, modelo y **orden de fallback chain** en caliente sin reiniciar; selects validados con modelos reales de cada proveedor
- [x] Auth JWT con refresh token rotation
- [x] **CAPTCHA** en login y registro (widget estilo Cloudflare Turnstile — soporta Turnstile, hCaptcha, reCAPTCHA)
- [x] Panel de administración aislado (`/gestion-usuarios`) con auth separada
- [x] Bundle ZIP descargable con validación y secrets scanning
- [x] Push a repositorio GitHub desde el panel de proyecto
- [x] RAG pipeline (indexar documentos en Qdrant, búsqueda vectorial, respuestas con citas)
- [x] Propuestas de stack tecnológico antes de generar el MVP (`TechProposalAgent`) con tarjeta visual en `ProjectDetailPage`
- [x] **TutorialCard** en `ProjectDetailPage` — muestra el tutorial por fases con comandos expandibles
- [x] **`CodeGenerationAgent` lee OpenSpec** — usa `data_entities` para generar el schema Prisma real y `api_endpoints` para el stub de documentación
- [x] Routing mobile/desktop determinístico (bypasa LLM — sin alucinaciones de stack)
- [x] Learning paths y upgrade signals por arquitectura
- [x] Rate limiting en todos los endpoints públicos
- [x] Documentación OpenAPI automática (`/api/docs`)
- [x] NotFoundPage (404) con navegación de vuelta al dashboard
- [x] **Modelo de datos profesional** — entidades enriquecidas, relaciones, índices, restricciones, auditoría y diagrama ER
- [x] **PDF de especificaciones** y exportación Markdown desde la aplicación
- [x] **Sentry opcional** en React, NestJS y FastAPI con privacidad por defecto
- [x] **GitHub Actions** para lint, tipos, tests, build, CodeQL y revisión de dependencias

---

## 12. Lo que falta / Mejoras pendientes ⏳

### Media prioridad

- [ ] **Visor de OpenSpec en el frontend** — el JSON se guarda pero no hay UI para inspeccionarlo ni editarlo inline
- [ ] **CodeGenAgent multi-step** — plan → implementar módulo por módulo → revisar (mejor calidad que generación en paso único)
- [ ] **RAG en el wizard** — el pipeline RAG existe pero no está conectado al wizard de nueva idea (podría sugerir funcionalidades basadas en proyectos anteriores)
- [ ] **Itinerarios formativos ampliados** — convertir las rutas pedagógicas en una experiencia navegable y evaluable
- [ ] **Activación operativa de Sentry** — crear los tres proyectos, configurar DSN y alertas en despliegue

### Baja prioridad / Post-MVP

- [ ] **Despliegue público reproducible** — CI configurada; falta automatizar el despliegue a un entorno público
- [ ] **Colaboradores en workspace** — el modelo de datos soporta `WorkspaceMember` con roles, pero la UI solo permite al owner trabajar
- [x] **MinIO activo** — `StorageService.uploadBuffer()` sube el ZIP a MinIO y `getSignedUrl()` devuelve la URL firmada de descarga (TTL 1 hora)
- [ ] **Historial de generaciones** — los `ArtifactBundle` anteriores se listan pero no permiten restaurar una versión anterior completa

---

## 13. Instalación desde cero

### Prerrequisitos

Instala las siguientes herramientas antes de continuar. Las versiones indicadas son las mínimas probadas.

#### 1. Node.js 22 LTS

```bash
# Windows — descarga el instalador desde:
# https://nodejs.org/en/download  (elige LTS)

# Verificar instalación:
node --version    # >= 22.0
npm --version     # >= 10.0
```

#### 2. Python 3.12+

```bash
# Windows — descarga el instalador desde:
# https://www.python.org/downloads/
# IMPORTANTE: marcar "Add Python to PATH" durante la instalación

# Verificar:
python --version    # >= 3.12
pip --version
```

#### 3. Docker Desktop

```bash
# Windows — descarga desde:
# https://www.docker.com/products/docker-desktop/
# Requiere WSL 2 en Windows 10/11

# Verificar:
docker --version           # >= 24.0
docker compose version     # >= 2.20
```

#### 4. Git

```bash
# https://git-scm.com/download/win
git --version    # >= 2.40
```

---

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/seurob/progresia.git progresia-studio
cd progresia-studio
```

---

### Paso 2 — Instalar dependencias

#### API (NestJS)

```bash
cd apps/api
npm install
```

#### Frontend (React + Vite)

```bash
cd apps/web
npm install
```

#### AI Service (Python)

```bash
cd apps/ai-service

# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar entorno virtual
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -e ".[dev]"
```

---

### Paso 3 — Instalar Ollama (LLM local, requerido)

Ollama ejecuta los modelos de lenguaje en tu ordenador. Es necesario para que el pipeline de generación de código funcione sin depender exclusivamente de APIs externas.

```bash
# 1. Descargar e instalar Ollama desde:
# https://ollama.com

# 2. Instalar uno de los perfiles recomendados (descarga única):
ollama pull gemma4:26b-a4b-it-qat    # perfil equilibrado: ordenador normal
ollama pull gemma4:31b               # máxima calidad: buena GPU o bastante RAM

# 3. Verificar que los modelos están instalados:
ollama list
```

> Ollama se arranca automáticamente como servicio en Windows después de instalarlo.
> Si necesitas arrancarlo manualmente: `ollama serve`

| Hardware | Configuración |
|----------|---------------|
| Ordenador normal, 32 GB de RAM recomendados | `gemma4:26b-a4b-it-qat`, descarga aproximada de 16 GB |
| Buena GPU o bastante RAM | `gemma4:31b`, descarga aproximada de 20 GB |
| Desarrollo ligero | `llama3.1:latest` para razonamiento y `qwen2.5-coder:latest` para código |

---

### Paso 4 — Configurar variables de entorno

#### API

```bash
# Crear apps/api/.env con este contenido:
NODE_ENV=development
API_PORT=3000

DATABASE_URL=postgresql://progresia:progresia@127.0.0.1:5432/progresia_studio

JWT_SECRET=cambia_esto_por_un_string_aleatorio_largo
JWT_EXPIRES_IN=1d

REDIS_HOST=127.0.0.1
REDIS_PORT=6380

AI_SERVICE_URL=http://127.0.0.1:8003

MINIO_ENDPOINT=127.0.0.1
MINIO_PORT=9000
MINIO_ACCESS_KEY=progresia
MINIO_SECRET_KEY=progresia_secret
MINIO_BUCKET=progresia-artifacts

CORS_ORIGINS=http://localhost:5173

# CAPTCHA — desactivado por defecto en desarrollo
CAPTCHA_ENABLED=false
CAPTCHA_PROVIDER=turnstile
CAPTCHA_SECRET_KEY=1x0000000000000000000000000000000AA

ADMIN_JWT_SECRET=otro_string_aleatorio_para_admin
ADMIN_EMAIL=admin@progresia.local
ADMIN_USERNAME=seurobman
ADMIN_PASSWORD=$eurobman2026
```

#### AI Service

```bash
# Crear apps/ai-service/.env con este contenido:
LLM_PROVIDER=groq

# Al menos una key es obligatoria para que el pipeline use LLM (sin key usa fallback determinístico)
GROQ_API_KEY=tu_clave_de_groq         # https://console.groq.com  (gratis)
OPENAI_API_KEY=tu_clave_de_openai     # https://platform.openai.com (de pago)
GEMINI_API_KEY=tu_clave_de_gemini     # https://aistudio.google.com (gratis con límites)

GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_MODEL=gpt-4o-mini
GEMINI_MODEL=gemini-2.0-flash

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_REASONING_MODEL=gemma4:26b-a4b-it-qat
OLLAMA_CODE_MODEL=gemma4:26b-a4b-it-qat

QDRANT_URL=http://localhost:6333
```

#### Frontend

```bash
# Crear apps/web/.env con este contenido:
VITE_API_URL=http://localhost:3000/api

# Test keys de Cloudflare Turnstile (funcionan en local, muestran widget de prueba)
VITE_CAPTCHA_PROVIDER=turnstile
VITE_CAPTCHA_SITE_KEY=1x00000000000000000000AA
```

---

### Paso 5 — Arrancar la infraestructura (Docker)

```bash
# Desde la raíz del monorepo
docker compose up -d

# Verificar que todos los contenedores están en estado "running":
docker compose ps
```

Esto levanta: PostgreSQL, Redis, MinIO, Qdrant y Mailpit.

---

### Paso 6 — Preparar la base de datos

```bash
cd apps/api

# Aplicar todas las migraciones Prisma
npx prisma migrate deploy

# Generar el cliente Prisma (obligatorio tras migrate)
npx prisma generate

# Poblar con datos iniciales (crea el usuario admin)
npx ts-node prisma/seed.ts
```

> **Windows:** Si aparece error de DLL lock, asegúrate de que el servidor API no está corriendo antes de ejecutar `prisma generate`.

El seed crea:
- **Admin**: `admin@progresia.local` / contraseña configurada en `ADMIN_PASSWORD`

---

### Paso 7 — Arrancar los servicios

Abre **tres terminales separadas**:

#### Terminal 1 — API (NestJS)

```bash
# Ejecutar desde la raíz para cargar la configuración compartida
npm run build --workspace @progresia/api

# Arrancar el servidor
node --enable-source-maps apps/api/dist/main
```

Verás: `Nest application successfully started`

> **Windows:** usar `127.0.0.1` en `DATABASE_URL`, `REDIS_HOST` y
> `MINIO_ENDPOINT`. Esto evita fallos intermitentes de resolución IPv4/IPv6 en
> Prisma y los SDK nativos. No usar `nest start --watch`; compilar y arrancar el
> build explícitamente.

#### Terminal 2 — AI Service (FastAPI)

```bash
cd apps/ai-service

# Activar el entorno virtual si no está activo
.\.venv\Scripts\Activate.ps1   # Windows PowerShell

# Arrancar con recarga automática
python -m uvicorn app.main:app --port 8003 --reload
```

Verás: `Application startup complete.`

#### Terminal 3 — Frontend (React + Vite)

```bash
cd apps/web
npm run dev
```

Verás: `Local: http://localhost:5173/`

---

### Paso 8 — Verificar la instalación

| URL | Descripción | Resultado esperado |
|-----|-------------|-------------------|
| `http://localhost:5173` | Frontend | Página de login |
| `http://localhost:3000/api/health` | API health | `{"status":"ok"}` |
| `http://localhost:8003/health` | AI Service health | `{"status":"ok"}` |
| `http://localhost:3000/api/docs` | Swagger UI | Documentación interactiva |
| `http://localhost:5173/gestion-usuarios` | Admin panel | Formulario de login admin |

---

### (Opcional) CAPTCHA real con Cloudflare Turnstile

Las test keys incluidas en la configuración de desarrollo muestran un widget funcional. Para producción o para eliminar el indicador de "modo prueba":

1. Crea una cuenta gratuita en [dash.cloudflare.com](https://dash.cloudflare.com)
2. Ve a **Turnstile** → **Add site** → elige `localhost` como dominio
3. Copia la **Site Key** y la **Secret Key**
4. Reemplaza en `apps/web/.env`: `VITE_CAPTCHA_SITE_KEY=<tu site key>`
5. Reemplaza en `apps/api/.env`: `CAPTCHA_SECRET_KEY=<tu secret key>`
6. Reinicia ambos servicios

---

### Comandos útiles de mantenimiento

```bash
# Ver logs en tiempo real de cada servicio
docker compose logs -f postgres
docker compose logs -f redis

# Resetear la base de datos completamente
cd apps/api
npx prisma migrate reset   # borra todos los datos y re-aplica migraciones

# Ejecutar tests
cd apps/api && npm test                    # tests unitarios NestJS
cd apps/api && npm run test:e2e            # tests de integración
cd apps/ai-service && pytest               # tests Python

# Linting
cd apps/ai-service && ruff check .         # linter Python
cd apps/api && npm run lint                # linter TypeScript
cd apps/web && npm run lint

# Abrir Prisma Studio (GUI para inspeccionar la DB)
cd apps/api && npx prisma studio
```

---

## 14. URLs de referencia durante el desarrollo

| Servicio | URL | Credenciales |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | — |
| API REST | http://localhost:3000/api | — |
| Swagger UI | http://localhost:3000/api/docs | — |
| AI Service | http://localhost:8003 | — |
| AI Service docs | http://localhost:8003/docs | — |
| Admin panel | http://localhost:5173/gestion-usuarios | `seurobman` / `$eurobman2026` |
| Configuración IA | http://localhost:5173/ai-settings | requiere login |
| MinIO console | http://localhost:9001 | `progresia` / `progresia_secret` |
| Mailpit (SMTP) | http://localhost:8025 | — |
| Qdrant dashboard | http://localhost:6333/dashboard | — |
