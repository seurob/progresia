# ProgresIA Studio

## Título del TFM

**ProgresIA Studio: plataforma multiagente para transformar ideas de negocio en MVPs software desplegables mediante IA, Spec Driven Development, RAG y DevOps**

## Objetivo del proyecto

ProgresIA Studio es una plataforma web de desarrollo asistido por inteligencia artificial que permite a personas sin conocimientos técnicos transformar una idea de negocio en un MVP software funcional, documentado y desplegable.

El sistema guía al usuario mediante un formulario progresivo y un asistente virtual. A partir de la información introducida, genera una especificación técnica con OpenSpec, diseña la arquitectura, crea el modelo de datos, genera código frontend y backend, prepara Docker, configura el entorno, genera documentación, pruebas básicas, seguridad, observabilidad y una guía de despliegue.

El objetivo del MVP no es crear cualquier tipo de software sin control, sino generar proyectos dentro de patrones soportados, con una estructura profesional, validable y preparada para evolucionar.

---

# 1. Visión general del producto

## Problema

Muchas personas tienen ideas de negocio digitales, pero no saben cómo convertirlas en un proyecto software real. No conocen conceptos como requisitos, arquitectura, base de datos, API, frontend, backend, Docker, seguridad, testing o despliegue.

## Solución

ProgresIA Studio actúa como un estudio técnico asistido por IA. El usuario describe su idea en lenguaje natural y la plataforma genera un kit completo de MVP.

## Resultado esperado

Por cada idea de negocio, la plataforma puede generar:

- Especificación funcional.
- Especificación técnica.
- Historias de usuario.
- Modelo de datos.
- Arquitectura del sistema.
- Backend inicial.
- Frontend inicial.
- API documentada.
- Autenticación.
- CRUD principal.
- Docker Compose.
- Variables de entorno.
- Tests básicos.
- Documentación.
- Guía de despliegue.
- Repositorio inicial.
- Exportación del proyecto.

---

# 2. Stack tecnológico del MVP

## Frontend

- React 19.
- Vite 8.
- TypeScript.
- Tailwind CSS 4.
- React Router.
- TanStack Query.
- React Hook Form.
- Zod.
- Axios.

## Backend principal

- NestJS.
- TypeScript.
- PostgreSQL.
- Prisma ORM.
- JWT.
- RBAC.
- Swagger/OpenAPI.
- Redis.
- BullMQ.
- Sentry.

## Servicio de IA

- FastAPI.
- Python 3.12 o superior.
- LangChain.
- LangGraph.
- Qdrant.
- OpenAI, Gemini u Ollama como proveedores configurables.
- RAG sobre documentación del proyecto.
- Embeddings para recuperación semántica.

## Infraestructura

- Docker.
- Docker Compose.
- GitHub.
- GitHub Actions.
- MinIO o S3 compatible.
- Sentry.
- Nginx opcional para despliegue.

## Testing y calidad

- ESLint.
- Prettier.
- Vitest o Jest.
- Playwright.
- Coverage mínimo.
- Validación de tipos con TypeScript.
- Quality gates en GitHub Actions.

---

# 3. Arquitectura general

La plataforma se divide en tres grandes bloques:

## 3.1 Frontend

Aplicación web donde el usuario:

- Se registra.
- Crea un workspace.
- Crea un proyecto.
- Rellena el formulario de idea.
- Conversa con el asistente.
- Revisa especificaciones.
- Lanza la generación del MVP.
- Descarga el kit generado.
- Consulta documentación.
- Ve el estado de las tareas de generación.

## 3.2 Backend principal

API principal encargada de:

- Autenticación.
- Usuarios.
- Workspaces.
- Proyectos.
- Formularios.
- Especificaciones.
- Artefactos generados.
- Control de permisos.
- Jobs de generación.
- Integración con GitHub.
- Exportación ZIP.
- Logs.
- Observabilidad.

## 3.3 Servicio IA

Servicio especializado encargado de:

- Analizar ideas.
- Generar requisitos.
- Crear especificaciones OpenSpec.
- Orquestar agentes.
- Ejecutar RAG.
- Generar documentación.
- Generar código base.
- Revisar seguridad.
- Revisar testing.
- Coordinar el flujo multiagente.

---

# 4. Dominios principales

## Auth

Responsable de registro, login, refresh token, recuperación de sesión y control de permisos.

## Users

Gestión de usuarios, perfiles y configuración.

## Workspaces

Agrupación de proyectos por usuario o equipo.

## Projects

Entidad principal del sistema. Cada proyecto representa una idea de negocio que se convertirá en MVP.

## Ideas

Información inicial introducida por el usuario: problema, solución, público objetivo, sector, funcionalidades, restricciones y objetivos.

## Specifications

Requisitos, historias de usuario, criterios de aceptación y especificaciones OpenSpec.

## Agents

Registro de agentes, tareas, estados, resultados y trazabilidad de decisiones.

## Artifacts

Documentos y archivos generados: Markdown, YAML, JSON, código, Dockerfiles, tests, ZIP.

## GeneratedCode

Estructura de código generada para frontend, backend y configuración.

## Deployments

Información de despliegue, repositorio, pipelines, estados y URLs.

## Documents

Documentación utilizada para RAG y documentación generada por el sistema.

---

# 5. Roles de usuario

## Admin

Puede gestionar usuarios, modelos IA, límites de uso, logs, configuración global, proveedores IA y permisos.

## Owner

Puede crear proyectos, responder formularios, usar el asistente, generar MVPs, revisar resultados, exportar documentación y lanzar despliegues.

## Collaborator

Puede participar en proyectos, consultar el asistente, comentar especificaciones y revisar artefactos.

## Reviewer

Puede validar arquitectura, seguridad, testing, documentación y aprobar la generación final del kit.

---

# 6. Agentes IA

## Agent Supervisor

Coordina todo el flujo y decide qué agente interviene en cada fase. Valida que los resultados sean coherentes entre sí.

## Product Agent

Analiza la idea de negocio, define problema, usuario objetivo, propuesta de valor, alcance del MVP y funcionalidades futuras.

## Requirements Agent

Genera requisitos funcionales, requisitos no funcionales, historias de usuario y criterios de aceptación.

## OpenSpec Agent

Convierte los requisitos en una especificación estructurada mediante OpenSpec.

## Architecture Agent

Define arquitectura, módulos, capas, dependencias, decisiones técnicas y estructura del repositorio.

## Data Agent

Diseña entidades, relaciones, modelos Prisma, migraciones y datos iniciales.

## Backend Agent

Genera módulos NestJS, controladores, servicios, DTOs, validaciones, autenticación, roles y endpoints.

## Frontend Agent

Genera pantallas React, rutas, formularios, componentes, hooks, llamadas API y diseño base.

## DevOps Agent

Genera Dockerfiles, docker-compose, variables de entorno, GitHub Actions y guía de despliegue.

## Security Agent

Revisa autenticación, autorización, validación de inputs, CORS, rate limiting, secretos y OWASP Top 10.

## Testing Agent

Genera pruebas unitarias, pruebas de integración, pruebas E2E, coverage y quality gates.

## Documentation Agent

Genera README, documentación técnica, manual de uso, arquitectura, endpoints, instalación y despliegue.

---

# 7. Flujo funcional del MVP

## Paso 1. Registro y workspace

El usuario se registra y crea un workspace.

## Paso 2. Creación del proyecto

El usuario crea un proyecto indicando:

- Nombre.
- Sector.
- Tipo de producto.
- Problema que resuelve.
- Usuario objetivo.
- Funcionalidades principales.
- Nivel de complejidad.
- Necesidad de IA.
- Necesidad de panel de administración.
- Necesidad de autenticación.
- Necesidad de pagos.
- Necesidad de integraciones externas.

## Paso 3. Formulario inteligente

La plataforma hace preguntas progresivas para completar la idea.

Ejemplos:

- ¿Qué problema resuelve tu aplicación?
- ¿Quién usará el producto?
- ¿Qué acciones principales podrá hacer el usuario?
- ¿Qué información se debe guardar?
- ¿Necesitas diferentes roles?
- ¿Quieres una aplicación privada o pública?
- ¿Qué sería imprescindible para una primera versión?

## Paso 4. Análisis de idea

El Product Agent genera:

- Resumen de la idea.
- Público objetivo.
- Propuesta de valor.
- Riesgos.
- Alcance del MVP.
- Funcionalidades principales.
- Funcionalidades futuras.

## Paso 5. Especificación OpenSpec

El sistema genera:

- Requisitos.
- Casos de uso.
- Historias de usuario.
- Criterios de aceptación.
- Entidades.
- Reglas de negocio.
- Flujos principales.
- Contratos API.
- Restricciones técnicas.

## Paso 6. Diseño técnico

Los agentes generan:

- Arquitectura.
- Modelo de datos.
- Estructura de carpetas.
- Endpoints.
- Decisiones técnicas.
- Migraciones iniciales.

## Paso 7. Generación del MVP

El sistema genera:

- Frontend.
- Backend.
- API.
- Base de datos.
- Autenticación.
- CRUD principal.
- Dashboard.
- Validaciones.
- Docker.
- Tests.
- Documentación.

## Paso 8. Validación

El sistema revisa:

- Errores básicos.
- Tests mínimos.
- Rutas protegidas.
- Variables ENV.
- Validación de inputs.
- OWASP.
- Coverage inicial.
- Errores detectados por Sentry.

## Paso 9. Entrega

El usuario recibe:

- Repositorio GitHub.
- ZIP del proyecto.
- README.
- Dossier técnico.
- Instrucciones Docker.
- Guía de despliegue.
- URL de preview si está configurada.

---

# 8. MVP interno de ProgresIA Studio

El primer MVP de ProgresIA Studio debe demostrar el ciclo completo con un caso controlado.

## Caso inicial recomendado

Generar una aplicación para gestionar reservas de clases particulares.

## Entidades generadas

- User.
- Role.
- Student.
- Teacher.
- Course.
- Lesson.
- Booking.
- Availability.

## Funcionalidades generadas

- Login.
- Registro.
- Panel principal.
- CRUD de profesores.
- CRUD de alumnos.
- CRUD de clases.
- Sistema básico de reservas.
- Estados de reserva.
- API REST documentada.
- Frontend conectado al backend.
- PostgreSQL.
- Prisma.
- Docker Compose.
- README.
- Tests básicos.
- GitHub Actions.

---

# 9. Artefactos generados por cada proyecto

La plataforma debe generar como mínimo:

```text
generated-project/
├── README.md
├── architecture.md
├── requirements.md
├── openspec.yaml
├── openapi.yaml
├── database-schema.md
├── docker-compose.yml
├── .env.example
├── deployment-guide.md
├── security-checklist.md
├── testing-plan.md
├── project-roadmap.md
├── frontend/
├── backend/
├── prisma/
├── tests/
└── .github/
    └── workflows/
        └── ci.yml
```

---

# 10. Estructura inicial del repositorio de ProgresIA Studio

```text
progresia-studio/
├── apps/
│   ├── web/
│   ├── api/
│   └── ai-service/
├── packages/
│   ├── shared/
│   ├── contracts/
│   └── config/
├── docker/
├── docs/
├── infra/
├── scripts/
├── .github/
│   └── workflows/
├── docker-compose.yml
├── README.md
└── .env.example
```

---

# 11. Estructura recomendada del frontend

```text
apps/web/
├── src/
│   ├── app/
│   ├── components/
│   ├── features/
│   │   ├── auth/
│   │   ├── projects/
│   │   ├── idea-wizard/
│   │   ├── assistant/
│   │   ├── specifications/
│   │   ├── artifacts/
│   │   └── deployments/
│   ├── hooks/
│   ├── lib/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   ├── stores/
│   └── types/
├── index.html
├── vite.config.ts
└── package.json
```

---

# 12. Estructura recomendada del backend

```text
apps/api/
├── src/
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── workspaces/
│   │   ├── projects/
│   │   ├── ideas/
│   │   ├── specifications/
│   │   ├── agents/
│   │   ├── artifacts/
│   │   ├── generated-code/
│   │   ├── deployments/
│   │   └── documents/
│   ├── common/
│   ├── config/
│   ├── database/
│   ├── jobs/
│   ├── security/
│   └── main.ts
├── prisma/
│   └── schema.prisma
├── test/
└── package.json
```

---

# 13. Estructura recomendada del servicio IA

```text
apps/ai-service/
├── app/
│   ├── api/
│   ├── agents/
│   │   ├── supervisor_agent.py
│   │   ├── product_agent.py
│   │   ├── requirements_agent.py
│   │   ├── openspec_agent.py
│   │   ├── architecture_agent.py
│   │   ├── data_agent.py
│   │   ├── backend_agent.py
│   │   ├── frontend_agent.py
│   │   ├── devops_agent.py
│   │   ├── security_agent.py
│   │   ├── testing_agent.py
│   │   └── documentation_agent.py
│   ├── chains/
│   ├── graph/
│   ├── rag/
│   ├── schemas/
│   ├── services/
│   ├── tools/
│   └── main.py
├── tests/
├── pyproject.toml
└── Dockerfile
```

---

# 14. Primeras tareas de desarrollo

## Fase 1. Inicialización del monorepo

- Crear estructura `apps/web`, `apps/api`, `apps/ai-service`.
- Crear `packages/shared`, `packages/contracts`, `packages/config`.
- Añadir `docker-compose.yml`.
- Añadir `.env.example`.
- Añadir README inicial.
- Configurar GitHub Actions básico.

## Fase 2. Backend base

- Crear proyecto NestJS.
- Configurar PostgreSQL.
- Configurar Prisma.
- Crear AuthModule.
- Crear UsersModule.
- Crear WorkspacesModule.
- Crear ProjectsModule.
- Crear Swagger.
- Crear JWT.
- Crear RBAC básico.

## Fase 3. Frontend base

- Crear proyecto React con Vite.
- Configurar Tailwind CSS.
- Configurar rutas.
- Crear layout principal.
- Crear login.
- Crear registro.
- Crear dashboard.
- Crear pantalla de proyectos.
- Crear wizard de idea.

## Fase 4. Servicio IA base

- Crear FastAPI.
- Crear endpoint de healthcheck.
- Crear endpoint `/analyze-idea`.
- Crear Product Agent inicial.
- Crear Requirements Agent inicial.
- Crear LangGraph básico con Supervisor Agent.
- Configurar proveedor LLM.
- Configurar Qdrant.

## Fase 5. Generación de especificaciones

- Crear entidad Specification.
- Crear endpoint para generar requisitos.
- Crear endpoint para generar OpenSpec.
- Guardar resultados en PostgreSQL.
- Indexar documentación en Qdrant.
- Mostrar especificación en frontend.

## Fase 6. Generación de artefactos

- Generar README.
- Generar architecture.md.
- Generar openapi.yaml.
- Generar database-schema.md.
- Generar docker-compose.yml.
- Generar estructura backend.
- Generar estructura frontend.
- Exportar ZIP.

## Fase 7. Validación

- Añadir Security Agent.
- Añadir Testing Agent.
- Crear checklist de seguridad.
- Crear tests básicos.
- Añadir Playwright.
- Añadir Sentry.
- Crear quality gate en CI.

---

# 15. Prompt inicial para Codex

Usa este prompt para empezar el proyecto con Codex:

```text
Quiero crear el proyecto ProgresIA Studio desde cero.

Es una plataforma web multiagente de desarrollo asistido por IA que transforma ideas de negocio en MVPs software funcionales y desplegables.

Necesito crear un monorepo profesional con esta estructura:

progresia-studio/
├── apps/
│   ├── web/
│   ├── api/
│   └── ai-service/
├── packages/
│   ├── shared/
│   ├── contracts/
│   └── config/
├── docker/
├── docs/
├── infra/
├── scripts/
├── .github/
│   └── workflows/
├── docker-compose.yml
├── README.md
└── .env.example

Stack:

Frontend:
- React 19
- Vite
- TypeScript
- Tailwind CSS 4
- React Router
- TanStack Query
- React Hook Form
- Zod
- Axios

Backend:
- NestJS
- TypeScript
- PostgreSQL
- Prisma
- JWT
- RBAC
- Swagger/OpenAPI
- Redis
- BullMQ
- Sentry

IA:
- FastAPI
- Python
- LangChain
- LangGraph
- Qdrant
- RAG
- proveedor LLM configurable

Infraestructura:
- Docker
- Docker Compose
- GitHub Actions
- Sentry
- MinIO o S3 compatible

Primera tarea:
1. Crear la estructura inicial del monorepo.
2. Crear README.md principal.
3. Crear .env.example.
4. Crear docker-compose.yml con PostgreSQL, Redis, Qdrant y MinIO.
5. Crear carpetas base para web, api y ai-service.
6. Crear GitHub Actions inicial con lint, test y build.
7. No implementar todavía funcionalidades complejas.
8. Dejar comentarios claros y estructura profesional para continuar por fases.
```

---

# 16. Prompt para Codex después de crear el monorepo

```text
Ahora implementa la primera versión del backend en apps/api con NestJS.

Objetivo:
Crear la base de la API de ProgresIA Studio.

Módulos iniciales:
- AuthModule
- UsersModule
- WorkspacesModule
- ProjectsModule
- IdeasModule
- SpecificationsModule

Requisitos:
- Configurar Prisma con PostgreSQL.
- Crear schema.prisma inicial.
- Crear entidades User, Workspace, Project, Idea, Specification.
- Crear autenticación JWT.
- Crear roles Admin, Owner, Collaborator y Reviewer.
- Crear Swagger/OpenAPI.
- Crear endpoint /health.
- Crear validaciones.
- Crear estructura modular limpia.
- Preparar la arquitectura para Clean Architecture de forma pragmática.
- Añadir tests básicos.
```

---

# 17. Prompt para Codex para el frontend

```text
Ahora implementa la primera versión del frontend en apps/web.

Objetivo:
Crear la interfaz inicial de ProgresIA Studio.

Pantallas:
- Login.
- Register.
- Dashboard.
- Projects list.
- Create project.
- Idea wizard.
- Project detail.
- Assistant panel.
- Specifications view.
- Artifacts view.

Requisitos:
- React 19.
- Vite.
- TypeScript.
- Tailwind CSS 4.
- React Router.
- TanStack Query.
- React Hook Form.
- Zod.
- Axios.
- Layout limpio y profesional.
- Componentes reutilizables.
- Validación de formularios.
- Cliente API centralizado.
```

---

# 18. Prompt para Codex para el servicio IA

```text
Ahora implementa la primera versión del servicio IA en apps/ai-service.

Objetivo:
Crear el servicio FastAPI que gestionará agentes, RAG y generación de especificaciones.

Requisitos:
- FastAPI.
- Python.
- LangChain.
- LangGraph.
- Qdrant client.
- Pydantic.
- Endpoint /health.
- Endpoint /analyze-idea.
- Endpoint /generate-requirements.
- Endpoint /generate-openspec.
- Crear Product Agent.
- Crear Requirements Agent.
- Crear OpenSpec Agent.
- Crear Supervisor Agent básico con LangGraph.
- Crear schemas Pydantic.
- Preparar proveedor LLM configurable por variables de entorno.
- Añadir tests básicos.
```

---

# 19. Variables de entorno iniciales

```env
# General
NODE_ENV=development
APP_NAME=ProgresIA Studio

# Frontend
VITE_API_URL=http://localhost:3000/api
VITE_AI_SERVICE_URL=http://localhost:8000

# Backend
API_PORT=3000
DATABASE_URL=postgresql://progresia:progresia@localhost:5432/progresia_studio
JWT_SECRET=change_me
JWT_EXPIRES_IN=1d
REDIS_HOST=localhost
REDIS_PORT=6379
SENTRY_DSN=

# IA Service
AI_SERVICE_PORT=8000
LLM_PROVIDER=openai
OPENAI_API_KEY=
GEMINI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
QDRANT_URL=http://localhost:6333

# Storage
MINIO_ENDPOINT=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=progresia
MINIO_SECRET_KEY=progresia_secret
MINIO_BUCKET=progresia-artifacts
```

---

# 20. Docker Compose inicial

```yaml
services:
  postgres:
    image: postgres:16
    container_name: progresia-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: progresia
      POSTGRES_PASSWORD: progresia
      POSTGRES_DB: progresia_studio
    ports:
      - "5432:5432"
    volumes:
      - progresia_postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    container_name: progresia-redis
    restart: unless-stopped
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:latest
    container_name: progresia-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - progresia_qdrant_data:/qdrant/storage

  minio:
    image: minio/minio:latest
    container_name: progresia-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: progresia
      MINIO_ROOT_PASSWORD: progresia_secret
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - progresia_minio_data:/data

volumes:
  progresia_postgres_data:
  progresia_qdrant_data:
  progresia_minio_data:
```

---

# 21. Criterio de éxito del primer sprint

El primer sprint se considera completado cuando:

- El monorepo está creado.
- Docker Compose levanta PostgreSQL, Redis, Qdrant y MinIO.
- El backend NestJS responde en `/health`.
- El servicio IA FastAPI responde en `/health`.
- El frontend React carga la pantalla inicial.
- Existe `.env.example`.
- Existe README inicial.
- Existe pipeline GitHub Actions.
- El proyecto puede arrancarse con comandos documentados.
