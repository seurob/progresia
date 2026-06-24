# CLAUDE.md — ProgresIA Studio

Contexto operativo para Claude Code al trabajar en este repositorio.

---

## Visión del proyecto

**ProgresIA Studio** es una plataforma educativa de desarrollo guiado por IA.
Su propósito: que cualquier persona con una idea de producto pueda generar un MVP completo, estructurado y coherente en minutos — aprendiendo la metodología SDD en el proceso.

El diferenciador clave no es la velocidad de generación, sino la **calidad pedagógica**: el usuario entiende qué se genera y por qué. Cada paso explica la decisión arquitectónica, el tradeoff y cómo implementarlo.

---

## Metodología SDD implementada

El pipeline sigue este orden estricto — cada paso depende del anterior:

```
Idea (wizard)
  → requirementsAgent   → Specification(REQUIREMENTS)
  → architectureAgent   → Specification(ARCHITECTURE)
  → openspecAgent       → Specification(OPENSPEC)       ← fuente de verdad
  → issueGenerator      → Specification(ISSUES)
  → tutorialAgent       → Specification(TUTORIAL)
  → codeGenAgent        → Specification(CODE)
  → bundleService       → ArtifactBundle + ZIP
```

El **OpenSpec** es el artefacto central. Todos los agentes downstream lo leen.
Al modificar el OpenSpec schema o el prompt del agente, los demás agentes se benefician automáticamente.

---

## Estructura del monorepo

```
apps/web/          React 19 + Vite + Tailwind CSS 4  → puerto 5173
apps/api/          NestJS 11 + Prisma + PostgreSQL    → puerto 3000
apps/ai-service/   FastAPI + LangChain + LangGraph    → puerto 8003
```

### Cómo arranca cada servicio

```bash
# Docker (DB + Redis)
docker compose up -d

# API — siempre compilar antes de lanzar (no usar nest start --watch en Windows)
# tsconfig.build.json excluye tests → rootDir=src → output en dist/main.js
cd apps/api && npx tsc --project tsconfig.build.json && node --enable-source-maps dist/main

# AI Service (puerto 8003 — Docker Desktop ocupa 8000 y 8001 en Windows)
cd apps/ai-service && python -m uvicorn app.main:app --port 8003 --reload

# Frontend
cd apps/web && npm run dev
```

> **Windows gotcha:** `nest start --watch` crea procesos zombi. Usar siempre `npx tsc --project tsconfig.build.json` + `node dist/main`.
> Antes de `npx prisma generate`, detener el servidor API (DLL lock en Windows).

---

## Convenciones del código

### NestJS (api)

- Todos los métodos de servicio que reciben `projectId` deben llamar a `ensureProjectAccess(projectId, userId)` y usar `project.id` para todas las queries FK subsiguientes. El `projectId` del cliente puede ser un slug o un UUID — `ensureProjectAccess` resuelve ambos.
- El helper `complexityToLevel(idea.complexity)` convierte el campo de DB (`"simple"/"standard"/"complex"`) al valor que espera el AI service (`"BEGINNER"/"INTERMEDIATE"/"ADVANCED"`).

### FastAPI (ai-service)

- Cada agente tiene una variante LLM (con `with_structured_output`) y una variante determinista como fallback. La determinista siempre debe producir un resultado válido.
- El `OpenSpecDoc` en `schemas/openspec.py` es el contrato estable. Los cambios de schema requieren actualizar el prompt en `openspec_agent.py` y el `_OpenSpecLLMOutput` en el mismo archivo.
- Los agentes no leen variables de entorno directamente — usan `get_llm(task_type)` de `core/llm.py`.

### React (web)

- El wizard de nuevo proyecto (`NewProjectPage.tsx`) usa un sistema de cola para los mensajes de IA. No hay llamadas directas al AI service desde el frontend — todo va vía `/api`.
- El `ProjectDetailPage.tsx` hace polling cada 2500ms mientras el pipeline está activo.

---

## Seguridad — regla absoluta

**Las claves de API nunca se hardcodean en el código fuente.**
- `GROQ_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GITHUB_TOKEN` → solo en `apps/ai-service/.env` (gitignored)
- `JWT_SECRET`, `JWT_REFRESH_SECRET`, `DATABASE_URL` → solo en `apps/api/.env` (gitignored)
- El `.env.example` contiene nombres de variables pero NUNCA valores reales

---

## Skills de Claude Code disponibles

### `/code-review`
Revisión de código del branch actual o de un PR de GitHub.

```bash
/code-review              # revisa los cambios del branch actual
/code-review ultra        # revisión multi-agente en profundidad (branch actual)
/code-review ultra 42     # revisión multi-agente del PR #42 en GitHub
```

Útil para:
- Antes de hacer un commit grande con cambios en el pipeline SDD
- Para validar cambios en el OpenSpec schema que afectan a múltiples agentes
- Para revisar migraciones de Prisma antes de hacer `migrate deploy`

---

## Flujo de trabajo recomendado

### Añadir un nuevo agente al pipeline

1. Crear `apps/ai-service/app/agents/nuevo_agent.py` con clase + método principal + fallback determinista
2. Añadir endpoint en `apps/ai-service/app/api/routes.py`
3. Añadir tipo en `SpecificationType` enum de Prisma y migrar
4. Añadir interface en `apps/api/src/modules/ai-service/ai-service.client.ts`
5. Añadir método en `AiServiceClient`
6. Crear job type en `apps/api/src/modules/specifications/` (processor + job)
7. Registrar en `specifications.service.ts` y `specifications.processor.ts`
8. Añadir tarjeta en `ProjectDetailPage.tsx`

### Modificar el OpenSpec

1. Editar `apps/ai-service/app/schemas/openspec.py` (añadir campo al modelo Pydantic)
2. Editar `apps/ai-service/app/agents/openspec_agent.py`:
   - Añadir campo a `_OpenSpecLLMOutput`
   - Actualizar `_SYSTEM_PROMPT` con instrucciones para el nuevo campo
   - Actualizar `_llm_output_to_doc()` para mapear el nuevo campo
   - Actualizar `_deterministic_generate()` con un fallback razonable
3. Si el campo es relevante para código/tutorial, actualizar esos agentes también

### Debugging del pipeline en desarrollo

```bash
# Ver logs del api con job processing
cd apps/api && npx tsc --project tsconfig.build.json && node --enable-source-maps dist/main

# Ver logs del ai-service (incluye LLM calls y fallbacks)
cd apps/ai-service && uvicorn app.main:app --port 8003 --reload --log-level debug

# Probar un agente directamente
cd apps/ai-service && python -c "
from app.agents.openspec_agent import OpenSpecAgent
from app.schemas.idea import IdeaRequest
# ... test
"

# Health check del ai-service
curl http://localhost:8003/health
```

---

## Base de datos — modelos principales

```
User          id, email, password_hash, name
Workspace     id, name, ownerId → User
Project       id, slug, name, sector, productType, status, workspaceId
Idea          id, problem, targetUsers, coreFeatures[], complexity, needsAuth, needsAdminPanel, needsAi, projectId
Specification id, type (REQUIREMENTS|ARCHITECTURE|OPENSPEC|ISSUES|TUTORIAL|CODE), status, content(JSON), projectId
ArtifactBundle id, status, zipUrl, projectId
```

`Project.slug` es único y se genera desde el nombre en el momento de creación.
Todos los endpoints aceptan `projectId` como UUID o slug — `ensureProjectAccess()` resuelve ambos.

---

## Panel de administración

Ruta: `http://localhost:5173/gestion-usuarios` — no aparece en ninguna navegación normal.

- **Auth separada**: `POST /api/admin/auth/login` (acepta email o username). Usa `ADMIN_JWT_SECRET` y emite tokens con `type: "admin"`. Los tokens admin no son válidos en el app normal y viceversa.
- **Guard**: `AdminJwtGuard` verifica `ADMIN_JWT_SECRET` y comprueba `payload.type === "admin"`.
- **Seed**: `npx ts-node prisma/seed.ts` → crea `admin@progresia.local / $eurobman2026` (rol ADMIN).
- **Seguridad**: no devuelve `passwordHash`, no permite eliminar el último admin, no permite que el admin se elimine a sí mismo.
- **Frontend**: usa `sessionStorage` (clave `admin_access_token`), completamente aislado del `localStorage` del app normal.

---

## Tareas pendientes (al día de hoy)

- Añadir `TutorialCard` al frontend (`ProjectDetailPage.tsx`) y extender el pipeline a 7 pasos visuales
- Tests para `TutorialAgent` y suite completa del ai-service
- Revisar y fortalecer `code_generation_agent.py` para usar `data_entities` y `api_endpoints` del OpenSpec
- Dependabot alerts: revisar remediación pendiente
