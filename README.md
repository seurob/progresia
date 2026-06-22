# ProgresIA Studio

**Plataforma educativa de desarrollo guiado por IA — de la idea al MVP.**

ProgresIA Studio convierte ideas en proyectos técnicos completos a través de la metodología **Spec-to-Software (SDD)**: primero se especifica con precisión, luego la IA genera. El resultado es un MVP con requisitos, arquitectura, código base, issues de GitHub y tutorial — todo coherente y listo para implementar.

---

## Metodología SDD (Spec-to-Software)

La plataforma impone un orden de trabajo que refleja cómo se construyen productos reales:

```
Idea del usuario
      │
      ▼
1. Análisis de requisitos   ← agente: requirements_agent
      │
      ▼
2. Arquitectura recomendada ← agente: architecture_agent
      │
      ▼
3. OpenSpec completo        ← agente: openspec_agent  (fuente de verdad)
      │
      ├──▶ 4. Issues GitHub      ← agente: issue_generator_agent
      ├──▶ 5. Tutorial           ← agente: tutorial_agent
      ├──▶ 6. Código base        ← agente: code_generation_agent
      └──▶ 7. Bundle ZIP         ← service: bundle_service
```

El **OpenSpec** es el documento central: un JSON estructurado con entidades de datos, contratos de API, reglas de negocio y pasos de implementación. Cualquier modelo de IA puede leerlo y continuar el desarrollo.

---

## Arquitectura del sistema

```
apps/
├── web/          React 19 + Vite + Tailwind CSS 4  (puerto 5173)
├── api/          NestJS 11 + Prisma + PostgreSQL    (puerto 3000)
└── ai-service/   FastAPI + LangChain + LangGraph    (puerto 8001)

packages/
└── shared-types/ Tipos TypeScript compartidos

infra/
└── docker-compose.yml  PostgreSQL, Redis, pgAdmin
```

### Flujo de datos

1. El usuario define su proyecto en el **wizard conversacional** (web)
2. El **api** almacena el proyecto e idea en PostgreSQL y encola jobs con BullMQ
3. Cada job llama al **ai-service** que ejecuta el agente correspondiente
4. Los resultados se persisten como `Specification` y se exponen vía REST

### Autenticación

- JWT access token (15 min) + refresh token rotativo (7 días)
- Todos los endpoints privados validan ownership del proyecto

---

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 19, Vite 6, Tailwind CSS 4, TanStack Query, React Router 7 |
| Backend | NestJS 11, Prisma 6, PostgreSQL 16, BullMQ, Passport-JWT |
| AI Service | FastAPI 0.115, LangChain 0.3, LangGraph 0.5, Pydantic v2 |
| Infra | Docker Compose, Redis (queue), pgAdmin |
| LLM | Groq (primario), OpenAI, Google Gemini (fallback) |

---

## Puesta en marcha

### Requisitos

- Node.js ≥ 20, Python ≥ 3.11, Docker Desktop

### 1. Variables de entorno

```bash
cp .env.example .env
# Editar .env: DATABASE_URL, JWT_SECRET, SMTP_*, CAPTCHA_*, GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, GITHUB_TOKEN
```

Para el ai-service:

```bash
cp apps/ai-service/.env.example apps/ai-service/.env
# Añadir claves de LLM
```

### 2. Infraestructura

```bash
docker compose up -d   # PostgreSQL + Redis + pgAdmin
```

### 3. Base de datos

```bash
cd apps/api
npx prisma migrate deploy   # producción
# o
npx prisma migrate dev      # desarrollo (recrea si es necesario)
npx prisma generate
npx prisma db seed
```

### 4. API (NestJS)

```bash
cd apps/api
npm install
npm run build          # compila a dist/
node --enable-source-maps dist/main
```

### 5. AI Service (FastAPI)

```bash
cd apps/ai-service
pip install -e ".[dev]"
uvicorn app.main:app --port 8001 --reload
```

### 6. Frontend (React)

```bash
cd apps/web
npm install
npm run dev            # http://localhost:5173
```

---

## Niveles técnicos del usuario

El wizard pregunta por el nivel técnico del desarrollador. Este valor fluye por todo el pipeline:

| Nivel | Campo DB | Arquitecturas recomendadas |
|-------|----------|---------------------------|
| Principiante | `complexity: "simple"` | Laravel Monolith, Django REST, React+Express |
| Intermedio | `complexity: "standard"` | Next.js App Router, NestJS+React |
| Avanzado | `complexity: "complex"` | NestJS+React, FastAPI+IA, arquitecturas desacopladas |

---

## Arquitecturas soportadas

| ID | Nombre | Nivel |
|----|--------|-------|
| `LARAVEL_MONOLITH` | Laravel 11 REST API | Principiante |
| `LARAVEL_INERTIA_REACT` | Laravel + Inertia + React | Intermedio |
| `DJANGO_REST` | Django 5 + DRF | Principiante |
| `NEXTJS_APP` | Next.js 15 App Router | Intermedio |
| `NESTJS_REACT` | NestJS + React desacoplado | Intermedio/Avanzado |
| `REACT_EXPRESS` | React + Express Node.js | Principiante |
| `FASTAPI_AI` | FastAPI + LangChain/LangGraph | Avanzado |

---

## Estructura del OpenSpec

El `OpenSpecDoc` es la fuente de verdad para todos los agentes downstream:

```json
{
  "project":        { "name", "sector", "target_users", "problem", "description" },
  "architecture":   { "type", "name", "stack", "difficulty" },
  "requirements":   [{ "id", "title", "description", "acceptance_criteria" }],
  "user_stories":   [{ "id", "actor", "goal", "benefit" }],
  "modules":        ["Auth", "Reservas", "Admin"],
  "milestones":     ["Milestone 1: Setup", "..."],
  "data_entities":  [{ "name", "description", "fields", "relations" }],
  "api_endpoints":  [{ "method", "path", "description", "auth_required", "request_body", "response" }],
  "business_rules": ["Un usuario solo puede acceder a sus propios recursos", "..."],
  "dev_steps":      [{ "step", "title", "description", "commands" }],
  "constraints":    { "delivery", "environments" }
}
```

---

## Variables de entorno

| Variable | Servicio | Descripción |
|----------|----------|-------------|
| `DATABASE_URL` | api | PostgreSQL connection string |
| `JWT_SECRET` | api | Clave de firma JWT |
| `JWT_REFRESH_SECRET` | api | Clave de firma refresh token |
| `CAPTCHA_ENABLED` | api | Activa validacion CAPTCHA en backend (`true`/`false`) |
| `CAPTCHA_PROVIDER` | api | `turnstile`, `hcaptcha` o `recaptcha` |
| `CAPTCHA_SECRET_KEY` | api | Secreto del proveedor CAPTCHA |
| `SMTP_HOST` | api | Servidor SMTP para enviar codigos de verificacion |
| `EMAIL_FROM` | api | Remitente de los correos de verificacion |
| `VITE_CAPTCHA_SITE_KEY` | web | Clave publica del widget CAPTCHA |
| `AI_SERVICE_URL` | api | URL del ai-service (default: `http://127.0.0.1:8001`) |
| `GROQ_API_KEY` | ai-service | Clave Groq (LLM primario) |
| `OPENAI_API_KEY` | ai-service | Clave OpenAI (fallback) |
| `GEMINI_API_KEY` | ai-service | Clave Google Gemini (fallback) |
| `GITHUB_TOKEN` | ai-service | Token para crear issues en GitHub |

> Las claves de API nunca se commitean. Solo existen en `.env` (gitignored).

## Registro seguro

El registro crea cuentas en estado pendiente. El usuario debe verificar un codigo de 6 digitos enviado por correo antes de iniciar sesion. En local, CAPTCHA queda desactivado si `CAPTCHA_ENABLED=false`; en produccion debe configurarse un proveedor como Cloudflare Turnstile y un SMTP real.

Endpoints principales:

- `POST /api/auth/register`
- `POST /api/auth/verify-email`
- `POST /api/auth/resend-verification-code`
- `POST /api/auth/change-pending-email`
- `POST /api/auth/login`

---

## Testing

```bash
# AI Service
cd apps/ai-service
pytest -v

# API
cd apps/api
npm run test
npm run test:e2e
```

---

## Estructura del repositorio

```
apps/api/
  prisma/
    schema.prisma           modelos: User, Workspace, Project, Idea, Specification, ArtifactBundle
    migrations/             historial de migraciones
    seed.ts                 datos iniciales de desarrollo
  src/
    modules/
      auth/                 JWT + refresh token rotation
      projects/             CRUD + slug generation + UUID/slug dual-lookup
      ideas/                intake de la idea del usuario
      specifications/       pipeline de generación de specs
      artifacts/            bundle ZIP + code generation
      ai-service/           cliente HTTP hacia FastAPI

apps/ai-service/
  app/
    agents/
      requirements_agent.py
      architecture_agent.py
      openspec_agent.py       agente central SDD
      issue_generator_agent.py
      tutorial_agent.py
      code_generation_agent.py
    schemas/
      openspec.py             OpenSpecDoc (fuente de verdad)
      idea.py
      architecture.py
    core/
      llm.py                  get_llm() con fallback chain

apps/web/
  src/
    routes/
      NewProjectPage.tsx      wizard conversacional SDD (6 pasos)
      ProjectDetailPage.tsx   pipeline + 7 tarjetas de resultado
      DashboardPage.tsx
    features/auth/
    lib/api.ts
```
