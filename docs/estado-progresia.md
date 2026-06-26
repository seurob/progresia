# Estado De ProgresIA Studio

Ultima revision: 2026-06-18

## Resumen

ProgresIA Studio ya tiene una base funcional de MVP en monorepo. No es un monolito estricto: comparte repositorio y contratos, pero corre como tres procesos principales.

```text
progresia-studio
|- apps/web        React + Vite + Tailwind
|- apps/api        NestJS + Prisma + PostgreSQL + BullMQ + MinIO
|- apps/ai-service FastAPI + agentes IA
|- packages        contratos/config/shared
|- openspec        base spec + cambios 0001-0007
`- docs            issues, Obsidian, ADRs y estado
```

## Arquitectura Actual

| Area | Estado | Detalle |
| --- | --- | --- |
| Frontend | Implementado | App React con autenticacion, dashboard, detalle de proyecto, OpenSpec, requirements, artifacts, jobs y pruebas unitarias. |
| API | Implementado | NestJS modular con auth, workspaces, projects, specifications, artifacts, jobs, GitHub push, MinIO y BullMQ. |
| AI service | Implementado | FastAPI con agentes para requirements, OpenSpec y generacion de codigo. |
| OpenSpec | Implementado | Validacion propia y cambios 0001-0007. |
| GitHub | Implementado | Repo remoto, issues, Dependabot, CI, dependency review, CodeQL y Scorecard. |
| Obsidian | Inicial | Vault local en `docs/obsidian` con roadmap, backlog y workflow. |

## Sprints Cerrados

| Sprint / Cambio | Resultado |
| --- | --- |
| 0001 Initialize platform | Base del monorepo, documentacion inicial y OpenSpec base. |
| 0002 API foundation | Backend NestJS, Prisma, auth, workspaces y proyectos. |
| 0003 Web foundation | Frontend React, rutas principales, formularios y UI base. |
| 0004 AI service integration | Conexion con FastAPI y flujo de generacion IA. |
| 0005 Generated artifacts | Manifest y export de artefactos generados. |
| 0006 GitHub security quality | CI, Dependabot, security policy, dependency review y Scorecard. |
| 0007 Delivery flow consolidation | Project status transitions, requirements UI, jobs async, SSE, MinIO, refresh token y pruebas. |
| 0008 Bug fixes post-analysis | BullMQ processor discovery, SHA-256 refresh tokens, idea fields en generateCode, errores UI pollers, timeout poller, REQUIREMENTS_READY enum. |
| 0009 MVP completion | Dockerfiles produccion (nginx SPA, prisma migrate, non-root), ProductAgent en pipeline supervisor, gestion de miembros de workspace (API + UI). |

## Trabajo Implementado De Prioridad

| Prioridad | Gap original | Estado |
| --- | --- | --- |
| Critico | Project status nunca cambia | Resuelto: DRAFT, REQUIREMENTS_READY, SPEC_READY y GENERATED se actualizan desde services. REQUIREMENTS_READY añadido al enum. |
| Critico | Frontend sin tests | Resuelto: Vitest con tests de flujos principales. |
| Critico / Alta | Generacion sincrona | Resuelto: jobs async con BullMQ. |
| Alta | Progress en tiempo real | Resuelto: SSE/polling de jobs desde API y frontend. |
| Alta | MinIO para ZIPs | Resuelto: artefactos se guardan y descargan con storage service. |
| Alta | Refresh token | Resuelto: endpoint funcional y renovacion. |
| Media | Requirements en UI | Resuelto: seccion y accion para generar requirements. |
| Seguridad | Dependabot PRs | Parcial: PRs de Actions mergeadas, PRs agrupadas cerradas y migraciones mayores separadas. |

## Dependencias Y Seguridad

Hecho:

- Resuelta alerta low de `esbuild` alineando Vitest con Vite 8.
- Mergeadas PRs de GitHub Actions:
  - #1 `actions/setup-python@6`
  - #2 `ossf/scorecard-action@2.4.3`
  - #3 `actions/setup-node@6`
  - #4 `actions/checkout@6`
  - #5 `actions/dependency-review-action@5`
- Cerrada PR #6 como agrupacion peligrosa; se aplicaron solo partes seguras:
  - `lucide-react@1.21.0`
  - `zod@4.4.3`
  - `class-validator@0.15.1`
- Cerrada PR #15 por agrupar TypeScript 6, ESLint 10 y Prisma 7 con CI fallando.
- Creados issues separados:
  - #16 Prisma 7
  - #17 React Router 8
  - #18 TypeScript 6
  - #19 ESLint 10

Pendiente bloqueado por upstream:

- `multer` via `@nestjs/platform-express`.
- `js-yaml` via `@nestjs/swagger` y tooling Jest.
- `npm audit fix --force` propone downgrades incompatibles de Nest/Swagger, por eso no se aplica.

## Validacion Actual

Comandos validados localmente:

```powershell
npm ci
npm run openspec:check
npm run lint
npm run typecheck
npm run test
npm run build
python -m ruff check .
python -m pytest
```

GitHub Actions en `main`:

- CI: success.
- OpenSSF Scorecard: success.
- CodeQL: skipped en el plan actual.

## Pendiente Priorizado

| Orden | Trabajo | Issue |
| --- | --- | --- |
| 1 | Mantener seguimiento de `multer` y `js-yaml` hasta que Nest/Swagger publiquen fix seguro. | #14 |
| 2 | Migrar Prisma 7 con CLI, client y config coordinados. | #16 |
| 3 | Evaluar React Router 8 sin mezclarlo con otras majors. | #17 |
| 4 | Evaluar TypeScript 6 en todo el monorepo. | #18 |
| 5 | Evaluar ESLint 10 y plugins asociados. | #19 |
| 6 | RAG con Qdrant — embeddings de specs y busqueda semantica. | Pendiente |
| 7 | E2E Playwright — smoke tests del flujo idea-to-GitHub. | Pendiente |
| 8 | Sentry — errores y trazas en web, API y servicio IA con filtrado de PII. | Implementado |
| 9 | Cloudflare Turnstile real en produccion. | #27 |
| 10 | SMTP y confirmacion de email. | #28 |
| 11 | Ollama local con modelos cargados en servidor. | #29 |

## Regla Operativa

Cada bloque nuevo debe seguir esta secuencia:

1. Crear o actualizar cambio OpenSpec.
2. Crear o actualizar issue GitHub.
3. Implementar cambios pequenos y verificables.
4. Ejecutar validacion local.
5. Subir a `main` solo con CI verde.
6. Reflejar el estado en `docs/estado-progresia.md` y `docs/obsidian`.
