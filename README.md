# ProgresIA Studio

ProgresIA Studio es una plataforma web multiagente de desarrollo asistido por IA que transforma ideas de negocio en MVPs software funcionales, documentados y desplegables.

El primer sprint deja preparado el monorepo, la infraestructura local y los tres servicios principales:

- `apps/web`: frontend React, Vite, TypeScript y Tailwind CSS.
- `apps/api`: backend NestJS con estructura modular y endpoint `/health`.
- `apps/ai-service`: servicio FastAPI preparado para agentes, RAG y generación de especificaciones.

## Requisitos

- Node.js 22 o superior.
- npm 10 o superior.
- Python 3.12 o superior.
- Docker y Docker Compose.

## Puesta en marcha

```bash
cp .env.example .env
npm install
docker compose up -d
npm run prisma:migrate -w apps/api
npm run dev:web
npm run dev:api
```

Para el servicio IA:

```bash
cd apps/ai-service
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

## URLs locales

- Frontend: `http://localhost:5173`
- API: `http://localhost:3000/api`
- API health: `http://localhost:3000/api/health`
- Swagger API: `http://localhost:3000/api/docs`
- Servicio IA: `http://localhost:8000`
- Servicio IA health: `http://localhost:8000/health`
- MinIO Console: `http://localhost:9001`
- Qdrant Dashboard/API: `http://localhost:6333`
- Redis Docker: `localhost:6380` por defecto si `6379` ya está ocupado localmente.

## Scripts principales

```bash
npm run openspec:check
npm run lint
npm run test
npm run build
npm run typecheck
npm run prisma:generate -w apps/api
npm run prisma:migrate -w apps/api
```

## API inicial

La primera base funcional del backend incluye:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/me`
- `GET|POST /api/workspaces`
- `GET|POST /api/projects`
- `GET|PUT /api/projects/:id`
- `POST /api/ideas`
- `GET /api/ideas/project/:projectId`
- `POST /api/specifications`
- `GET /api/specifications/project/:projectId`
- `POST /api/specifications/project/:projectId/generate-openspec`
- `POST /api/artifacts/project/:projectId/generate`
- `GET /api/artifacts/project/:projectId`

## OpenSpec

El contrato funcional y tecnico vive en `openspec/`. Antes de implementar una capacidad relevante, crea o actualiza un cambio en `openspec/changes/` y valida la estructura con:

```bash
npm run openspec:check
```

## GitHub Issues

El backlog inicial vive en `docs/issues/` y esta preparado para GitHub Issues. Cuando exista autenticacion de GitHub en la maquina:

```powershell
$env:GH_TOKEN="..."
node scripts/create-github-repo.mjs
git push -u origin main
node scripts/configure-github-security.mjs
node scripts/create-github-issues.mjs
```

Tambien hay una plantilla de issue en `.github/ISSUE_TEMPLATE/openspec-task.yml` para que cada tarea quede conectada a su cambio OpenSpec.

Para configurar Security and quality en GitHub hace falta un token con permisos de administracion del repositorio, issues, actions y security events:

```powershell
$env:GH_TOKEN="ghp_..."
node scripts/configure-github-security.mjs
node scripts/create-github-issues.mjs
```

La automatizacion de seguridad versionada incluye CodeQL, Dependency Review, OpenSSF Scorecard, Dependabot y `SECURITY.md`.

## Obsidian

El vault local de documentacion esta en `docs/obsidian/`. Abre esa carpeta con Obsidian para trabajar con:

- mapa del proyecto,
- roadmap,
- backlog,
- ADRs,
- enlaces a OpenSpec.

El proyecto se considera un monorepo con runtime modular: no es un monolito estricto, aunque el MVP se gobierna como una unica unidad de producto. La decision esta documentada en `docs/adr/0001-repository-and-runtime-shape.md`.

## Estructura

```text
openspec/
apps/
  web/
  api/
  ai-service/
packages/
  shared/
  contracts/
  config/
docker/
docs/
infra/
scripts/
```

## Próximas fases

1. Exportar el kit de MVP generado.
2. Ampliar los agentes para generar codigo y pruebas a partir del manifiesto.
3. Preparar almacenamiento de artefactos en MinIO.
