import logging
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import TaskType, get_llm
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile
from app.agents.templates import academia as academia_template
from app.agents.templates import django_rest as django_template
from app.agents.templates import laravel_monolith as laravel_template
from app.agents.templates import nextjs_app as nextjs_template
from app.agents.templates import rrhh as rrhh_template
from app.agents.templates import salud as salud_template
from app.agents.templates import horeca as horeca_template
from app.agents.templates import inmobiliaria as inmobiliaria_template
from app.agents.templates import ecommerce as ecommerce_template
from app.agents.templates import logistica as logistica_template
from app.agents.templates import fintech as fintech_template
from app.agents.templates import eventos as eventos_template
from app.agents.templates import veterinaria as veterinaria_template
from app.agents.templates import gym as gym_template
from app.agents.templates import farmacia as farmacia_template
from app.agents.templates import abogados as abogados_template

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert fullstack developer generating a production-ready MVP scaffold.

Stack:
- Backend: tRPC v11 + Fastify + Prisma + PostgreSQL (TypeScript, DDD)
- Frontend: Next.js 14 App Router + Tailwind CSS + tRPC client (TypeScript)
- Infrastructure: Docker Compose, multi-stage Dockerfiles, nginx reverse proxy

DDD structure per module (one bounded context per feature):
  apps/api/src/modules/{module}/
    {module}.entity.ts      -- domain entity (plain class)
    {module}.service.ts     -- business logic, calls Prisma
    {module}.router.ts      -- tRPC router with CRUD procedures

Generate the full scaffold and respond with valid JSON matching the CodeGenerationResponse schema."""


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _pascal(name: str) -> str:
    return "".join(w.capitalize() for w in re.split(r"[\s\-_]+", name.strip()))


def _camel(name: str) -> str:
    p = _pascal(name)
    return p[0].lower() + p[1:] if p else name


def _build_human_message(req: CodeGenerationRequest) -> str:
    modules = ", ".join(req.modules) if req.modules else "Core"
    stack = ", ".join(req.stack)
    reqs = "\n".join(
        f"  - {r.get('id', '')}: {r.get('title', '')}" for r in req.requirements[:8]
    )
    return f"""Project: {req.project_name}
Sector: {req.sector}
Modules / bounded contexts: {modules}
Tech stack: {stack}
Needs auth: {req.needs_auth}
Needs admin panel: {req.needs_admin_panel}
Needs AI service: {req.needs_ai}

Top requirements:
{reqs if reqs else "  (none provided)"}

First module name (for file naming): {(req.modules[0] if req.modules else "item").lower().replace(" ", "-")}"""


class CodeGenerationAgent:
    def generate(
        self,
        req: CodeGenerationRequest,
        llm: BaseChatModel | None = None,
        task: TaskType = "code",
    ) -> CodeGenerationResponse:
        # Sector-specific templates always take priority — they produce
        # deterministic, high-quality output that an LLM cannot match.
        if self._has_sector_template(req):
            return self._scaffold_fallback(req)

        resolved_llm = llm if llm is not None else get_llm(task)

        if resolved_llm is not None:
            try:
                structured = resolved_llm.with_structured_output(CodeGenerationResponse)
                result = structured.invoke([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=_build_human_message(req)),
                ])
                if isinstance(result, CodeGenerationResponse) and self._is_valid_output(result):
                    return result
            except Exception as exc:
                logger.warning("LLM code generation failed, using scaffold fallback: %s", exc)

        return self._scaffold_fallback(req)

    def _has_sector_template(self, req: CodeGenerationRequest) -> bool:
        if req.architecture_type and req.architecture_type in self._ARCHITECTURE_TEMPLATES:
            return True
        sector = req.sector.lower()
        stack  = " ".join(req.stack).lower()
        text   = f"{sector} {stack}"
        return (
            any(k in text for k in self._ACADEMIA_KEYWORDS)
            or any(k in text for k in self._LARAVEL_KEYWORDS)
            or any(k in text for k in self._NEXTJS_KEYWORDS)
            or any(k in text for k in self._DJANGO_KEYWORDS)
            or any(k in text for k in self._RRHH_KEYWORDS)
            or any(k in text for k in self._SALUD_KEYWORDS)
            or any(k in text for k in self._HORECA_KEYWORDS)
            or any(k in text for k in self._INMOBILIARIA_KEYWORDS)
            or any(k in text for k in self._ECOMMERCE_KEYWORDS)
            or any(k in text for k in self._LOGISTICA_KEYWORDS)
            or any(k in text for k in self._FINTECH_KEYWORDS)
            or any(k in text for k in self._EVENTOS_KEYWORDS)
            or any(k in text for k in self._VETERINARIA_KEYWORDS)
            or any(k in text for k in self._GYM_KEYWORDS)
            or any(k in text for k in self._FARMACIA_KEYWORDS)
            or any(k in text for k in self._ABOGADOS_KEYWORDS)
        )

    @staticmethod
    def _is_valid_output(result: CodeGenerationResponse) -> bool:
        if not result.files:
            return False
        paths = [f.path for f in result.files]
        # Reject if more than 60 files (LLM hallucination) or duplicate paths
        return len(paths) <= 60 and len(paths) == len(set(paths))

    # ── Scaffold fallback: sector-specific or generic DDD ─────────────────

    _ACADEMIA_KEYWORDS = {"educac", "formac", "ensena", "academia", "curso", "escuela", "capacitac"}
    _LARAVEL_KEYWORDS  = {"laravel", "php", "blade", "eloquent", "artisan"}
    _NEXTJS_KEYWORDS   = {"nextjs", "next.js", "next js", "vercel", "app router"}
    _DJANGO_KEYWORDS   = {"django", "drf", "django rest", "python web"}
    _RRHH_KEYWORDS          = {"rrhh", "recursos humanos", "empleados", "nomina", "nómina", "payroll", "hr ", "human resources"}
    _SALUD_KEYWORDS         = {"salud", "clinica", "clínica", "medic", "paciente", "doctor", "hospital", "cita medica", "consulta"}
    _HORECA_KEYWORDS        = {"restaurante", "hosteleria", "hostelería", "hotel", "bar ", "cafeteria", "cafetería", "horeca", "comanda", "carta restaurante", "menu restaurante"}
    _INMOBILIARIA_KEYWORDS  = {"inmobiliaria", "inmueble", "propiedad", "piso", "alquiler piso", "venta piso", "agencia inmobiliaria", "real estate", "crm inmobiliario"}
    _ECOMMERCE_KEYWORDS     = {"ecommerce", "e-commerce", "tienda online", "tienda virtual", "shop online", "carrito", "catalogo", "catálogo", "marketplace", "venta online"}
    _LOGISTICA_KEYWORDS     = {"logistica", "logística", "envio", "envío", "mensajeria", "mensajería", "reparto", "transporte", "tracking", "flota", "almacen", "almacén"}
    _FINTECH_KEYWORDS       = {"fintech", "finanzas", "banco", "banca", "presupuesto", "ahorro", "inversion", "inversión", "contabilidad", "tesoreria", "tesorería", "billetera", "wallet"}
    _EVENTOS_KEYWORDS       = {"evento", "concierto", "conferencia", "festival", "ticketing", "entrada", "ticket", "asistente evento", "venta entradas", "check-in evento"}
    _VETERINARIA_KEYWORDS   = {"veterinaria", "veterinario", "mascota", "clinica veterinaria", "clínica veterinaria", "animales domésticos", "animales domesticos", "perros gatos", "clinica animal", "hospital veterinario"}
    _GYM_KEYWORDS           = {"gimnasio", "gym", "fitness", "membresía", "membresia", "crossfit", "pilates", "yoga gym", "spinning", "entrenamiento personal", "clases grupales", "sala fitness"}
    _FARMACIA_KEYWORDS      = {"farmacia", "botica", "medicamento", "dispensario", "farmaceutico", "farmacéutico", "medicacion", "medicación", "receta medica", "receta médica", "stock farmacia"}
    _ABOGADOS_KEYWORDS      = {"abogado", "bufete", "despacho juridico", "despacho jurídico", "expediente juridico", "expediente jurídico", "caso legal", "vista judicial", "horas facturables", "juridico", "jurídico"}

    _ARCHITECTURE_TEMPLATES: dict[str, object] = {
        "LARAVEL_MONOLITH":       laravel_template,
        "LARAVEL_INERTIA_REACT":  laravel_template,
        "LARAVEL_INERTIA_VUE":    laravel_template,
        "NEXTJS_APP":             nextjs_template,
        "ACADEMIA":               academia_template,
        "DJANGO_REST":            django_template,
    }

    def _scaffold_fallback(self, req: CodeGenerationRequest) -> CodeGenerationResponse:
        # Explicit architecture_type takes priority
        if req.architecture_type:
            tmpl = self._ARCHITECTURE_TEMPLATES.get(req.architecture_type)
            if tmpl is not None:
                base = tmpl.build(req)  # type: ignore[union-attr]
                return self._extend_with_sdd(base, req)

        sector_lower = req.sector.lower()
        stack_lower  = " ".join(req.stack).lower()
        text         = f"{sector_lower} {stack_lower}"

        # Check specific sector templates before ACADEMIA to avoid false positives
        # ("recursos" contains "curso" as a substring, which would incorrectly match ACADEMIA)
        if any(k in text for k in self._RRHH_KEYWORDS):
            return self._extend_with_sdd(rrhh_template.build(req), req)
        # VETERINARIA before SALUD: "clínica veterinaria" contains "clínica" from _SALUD_KEYWORDS
        if any(k in text for k in self._VETERINARIA_KEYWORDS):
            return self._extend_with_sdd(veterinaria_template.build(req), req)
        if any(k in text for k in self._SALUD_KEYWORDS):
            return self._extend_with_sdd(salud_template.build(req), req)
        if any(k in text for k in self._HORECA_KEYWORDS):
            return self._extend_with_sdd(horeca_template.build(req), req)
        if any(k in text for k in self._INMOBILIARIA_KEYWORDS):
            return self._extend_with_sdd(inmobiliaria_template.build(req), req)
        if any(k in text for k in self._ECOMMERCE_KEYWORDS):
            return self._extend_with_sdd(ecommerce_template.build(req), req)
        if any(k in text for k in self._LOGISTICA_KEYWORDS):
            return self._extend_with_sdd(logistica_template.build(req), req)
        if any(k in text for k in self._FINTECH_KEYWORDS):
            return self._extend_with_sdd(fintech_template.build(req), req)
        if any(k in text for k in self._EVENTOS_KEYWORDS):
            return self._extend_with_sdd(eventos_template.build(req), req)
        if any(k in text for k in self._GYM_KEYWORDS):
            return self._extend_with_sdd(gym_template.build(req), req)
        if any(k in text for k in self._FARMACIA_KEYWORDS):
            return self._extend_with_sdd(farmacia_template.build(req), req)
        if any(k in text for k in self._ABOGADOS_KEYWORDS):
            return self._extend_with_sdd(abogados_template.build(req), req)
        if any(k in sector_lower for k in self._ACADEMIA_KEYWORDS):
            return self._extend_with_sdd(academia_template.build(req), req)
        if any(k in text for k in self._LARAVEL_KEYWORDS):
            return self._extend_with_sdd(laravel_template.build(req), req)
        if any(k in text for k in self._NEXTJS_KEYWORDS):
            return self._extend_with_sdd(nextjs_template.build(req), req)
        if any(k in text for k in self._DJANGO_KEYWORDS):
            return self._extend_with_sdd(django_template.build(req), req)

        slug = _slug(req.project_name)
        modules = req.modules if req.modules else ["Item"]
        first_mod = modules[0]
        first_slug = _slug(first_mod)
        first_pascal = _pascal(first_mod)
        first_camel = _camel(first_mod)

        files: list[GeneratedFile] = [
            self._api_package_json(slug),
            self._api_tsconfig(),
            self._api_index(slug),
            self._api_trpc(req),
            self._api_router(modules),
            self._prisma_schema(modules, req.needs_auth),
            self._module_entity(first_slug, first_pascal),
            self._module_service(first_slug, first_pascal, first_camel),
            self._module_router(first_slug, first_pascal, first_camel),
            self._web_package_json(slug),
            self._web_tsconfig(),
            self._web_tailwind(),
            self._web_layout(req.project_name),
            self._web_home_page(req.project_name, modules),
            self._web_module_page(first_pascal, first_camel),
            self._web_trpc_client(),
            self._web_provider(),
            self._api_dockerfile(),
            self._web_dockerfile(),
            self._nginx_conf(),
            self._docker_compose(slug, req.needs_ai),
            self._env_example(slug),
        ]
        files += self._sdd_and_docs_files(req)

        return CodeGenerationResponse(project_name=req.project_name, files=files)

    def _extend_with_sdd(
        self, base: CodeGenerationResponse, req: CodeGenerationRequest
    ) -> CodeGenerationResponse:
        """Append SDD + docs scaffold to any template-generated response."""
        existing_paths = {f.path for f in base.files}
        extra = [f for f in self._sdd_and_docs_files(req) if f.path not in existing_paths]
        return CodeGenerationResponse(
            project_name=base.project_name,
            files=base.files + extra,
        )

    # ── SDD + docs folder generation ─────────────────────────────────────────

    def _sdd_and_docs_files(self, req: CodeGenerationRequest) -> list[GeneratedFile]:
        slug = _slug(req.project_name)
        stack = req.stack or ["React", "NestJS", "PostgreSQL"]
        modules_list = "\n".join(f"- {m}" for m in (req.modules or ["Core"]))
        reqs_list = "\n".join(
            f"- **{r.get('id', '')}** {r.get('title', '')}" for r in req.requirements[:10]
        ) or "- (pendiente de definir)"

        readme = self._readme_file(req, slug, stack)

        constitution = GeneratedFile(
            path="sdd/constitution.md",
            language="markdown",
            content=f"""# Constitución del Proyecto — {req.project_name}

> Este documento es la fuente de verdad del proyecto.
> Cualquier IA o desarrollador debe leer este archivo antes de trabajar en el código.

## Propósito

{req.project_name} es un MVP del sector **{req.sector}**.

## Stack tecnológico seleccionado

{chr(10).join(f'- {t}' for t in stack)}

## Módulos principales

{modules_list}

## Decisiones de arquitectura

| # | Decisión | Motivo |
|---|----------|--------|
| 1 | {stack[0] if stack else 'React'} como frontend | Ecosistema maduro, compatibilidad con TypeScript |
| 2 | {'PostgreSQL' if any('postgres' in s.lower() for s in stack) else stack[-1] if stack else 'PostgreSQL'} como base de datos | ACID, soporte JSON, extensiones vectoriales |
| 3 | Docker Compose para desarrollo local | Reproducibilidad en cualquier OS |

## Principios de desarrollo

- **SDD-first**: cada cambio empieza con una especificación, no con código
- **Convenciones sobre configuración**: seguir las convenciones del framework elegido
- **Test antes de refactorizar**: no refactorizar código sin cobertura de tests

## Cambios a este documento

Cualquier cambio de stack, arquitectura o módulos debe actualizarse aquí y en `sdd/specifications/openspec.md`.
""",
        )

        requirements_md = GeneratedFile(
            path="sdd/requirements/requirements.md",
            language="markdown",
            content=f"""# Requisitos — {req.project_name}

## Requisitos funcionales

{reqs_list}

## Requisitos no funcionales

- **Seguridad**: autenticación JWT con refresh tokens
- **Rendimiento**: respuesta API < 300ms en p95
- **Fiabilidad**: 99.9% uptime en producción
- **Mantenibilidad**: cobertura de tests > 70%
- **Escalabilidad**: arquitectura preparada para múltiples instancias

## Funcionalidades prioritarias (MoSCoW)

### Must have
{chr(10).join(f'- {m}' for m in (req.modules[:3] if req.modules else ['Autenticación de usuarios', 'Dashboard principal', 'CRUD de entidades']))}

### Should have
- Notificaciones por email
- Exportación de datos

### Could have
- Modo oscuro
- Integración con terceros

### Won't have (MVP)
- App móvil nativa
- Funcionalidades offline
""",
        )

        user_stories = GeneratedFile(
            path="sdd/requirements/user-stories.md",
            language="markdown",
            content=f"""# User Stories — {req.project_name}

## Actor principal: Usuario final

{chr(10).join(
    f'- **US-{i+1:03d}**: Como usuario quiero {m.lower()} para mejorar mi flujo de trabajo.'
    for i, m in enumerate(req.modules[:6] if req.modules else ['gestionar mis datos'])
)}

## Actor: Administrador

- **US-A01**: Como administrador quiero gestionar usuarios para mantener el acceso controlado.
- **US-A02**: Como administrador quiero ver métricas del sistema para tomar decisiones informadas.

## Criterios de aceptación generales

- Los formularios validan datos en cliente y servidor
- Los errores muestran mensajes descriptivos al usuario
- Las acciones destructivas piden confirmación
""",
        )

        openspec_stub = GeneratedFile(
            path="sdd/specifications/openspec.md",
            language="markdown",
            content=f"""# OpenSpec — {req.project_name}

> Generado por ProgresIA Studio. Ver especificación completa en el panel del proyecto.

## Resumen

- **Proyecto**: {req.project_name}
- **Sector**: {req.sector}
- **Stack**: {', '.join(stack)}
- **Módulos**: {', '.join(req.modules or ['Core'])}

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /auth/login | Autenticación de usuario |
| POST | /auth/refresh | Renovar token de acceso |
| GET | /api/v1/{(req.modules[0] if req.modules else 'items').lower().replace(' ', '-')}s | Listar recursos |
| POST | /api/v1/{(req.modules[0] if req.modules else 'items').lower().replace(' ', '-')}s | Crear recurso |
| PUT | /api/v1/{(req.modules[0] if req.modules else 'items').lower().replace(' ', '-')}s/:id | Actualizar recurso |
| DELETE | /api/v1/{(req.modules[0] if req.modules else 'items').lower().replace(' ', '-')}s/:id | Eliminar recurso |

## Entidades de datos

{chr(10).join(f'### {m}{chr(10)}- id: UUID{chr(10)}- createdAt: DateTime{chr(10)}- updatedAt: DateTime{chr(10)}' for m in (req.modules[:3] if req.modules else ['Item']))}

## Ver especificación completa

La especificación OpenSpec completa en JSON está disponible en el panel de ProgresIA Studio
bajo el proyecto **{req.project_name}** → Especificaciones → OpenSpec.
""",
        )

        milestones = GeneratedFile(
            path="sdd/plans/milestones.md",
            language="markdown",
            content=f"""# Milestones — {req.project_name}

## M1: Foundation (Semana 1-2)

- [ ] Setup del entorno de desarrollo con Docker Compose
- [ ] Autenticación JWT (registro, login, refresh)
- [ ] Estructura base del proyecto
- [ ] CI básica con GitHub Actions

## M2: Core features (Semana 3-5)

{chr(10).join(f'- [ ] {m}' for m in (req.modules[:4] if req.modules else ['CRUD de entidades principales']))}

## M3: Polish & deploy (Semana 6-8)

- [ ] Tests de integración > 70% cobertura
- [ ] Dockerización para producción
- [ ] Documentación de API (Swagger/OpenAPI)
- [ ] Deploy en entorno de staging
""",
        )

        context_prompt = GeneratedFile(
            path="sdd/prompts/project-context.md",
            language="markdown",
            content=f"""# Contexto del proyecto para IA — {req.project_name}

> Copia y pega este archivo al inicio de cualquier sesión con Claude, Copilot o ChatGPT
> para que la IA tenga el contexto completo del proyecto.

---

## Descripción del proyecto

Estoy trabajando en **{req.project_name}**, un MVP del sector **{req.sector}**.

## Stack tecnológico

{chr(10).join(f'- {t}' for t in stack)}

## Módulos implementados

{modules_list}

## Convenciones del proyecto

- TypeScript estricto en todo el código
- Nombres de variables y funciones en camelCase
- Nombres de archivos en kebab-case
- Commits siguiendo Conventional Commits (feat:, fix:, docs:, refactor:)
- Cada módulo tiene su propio directorio con: entity, service, controller/router

## Qué puedes hacer ahora

Lee los archivos de `sdd/` para entender el contexto completo antes de hacer cambios.
Empieza siempre con `sdd/constitution.md` y `sdd/requirements/requirements.md`.
""",
        )

        resume_prompt = GeneratedFile(
            path="sdd/prompts/resume-session.md",
            language="markdown",
            content=f"""# Prompt: Retomar sesión de trabajo

> Usa este prompt cuando abras una nueva sesión con una IA y quieras continuar donde lo dejaste.

---

Estoy retomando el trabajo en **{req.project_name}**.

Por favor lee estos archivos en orden:
1. `sdd/constitution.md` — Arquitectura y decisiones del proyecto
2. `sdd/requirements/requirements.md` — Requisitos del sistema
3. `sdd/plans/milestones.md` — Estado actual del desarrollo

El stack es: {', '.join(stack)}.

Cuando termines de leer, dime qué entiendes del proyecto y espera mis instrucciones.
""",
        )

        add_feature_prompt = GeneratedFile(
            path="sdd/prompts/add-feature.md",
            language="markdown",
            content="""# Prompt: Añadir nueva funcionalidad

> Usa este prompt cuando quieras añadir un nuevo módulo o funcionalidad al proyecto.

---

Quiero añadir la siguiente funcionalidad al proyecto:

**Descripción**: [describe qué debe hacer]
**Módulo afectado**: [nombre del módulo o "nuevo módulo"]
**Casos de uso**:
- Como [actor], quiero [acción] para [beneficio]

Antes de escribir código:
1. Dime qué archivos vas a crear o modificar
2. Explica las decisiones de arquitectura
3. Muestra el schema de base de datos si es necesario
4. Pide confirmación antes de proceder

No toques archivos fuera del módulo afectado sin justificación.
""",
        )

        fix_bug_prompt = GeneratedFile(
            path="sdd/prompts/fix-bug.md",
            language="markdown",
            content="""# Prompt: Corregir un bug

> Usa este prompt cuando necesites ayuda para resolver un error.

---

Tengo el siguiente error en el proyecto:

**Error**:
```
[pega aquí el mensaje de error completo]
```

**Contexto**: [describe qué estabas haciendo cuando ocurrió]
**Archivo**: [ruta del archivo si la conoces]

Por favor:
1. Identifica la causa raíz del error
2. Explica por qué ocurre
3. Propón la solución mínima necesaria
4. No refactorices código que no está relacionado con el bug
""",
        )

        env_setup = GeneratedFile(
            path="sdd/setup/environment.md",
            language="markdown",
            content=f"""# Configuración del entorno — {req.project_name}

## Requisitos previos

| Herramienta | Versión mínima | Instalación |
|-------------|---------------|-------------|
| Node.js | 20 LTS | https://nodejs.org |
| Docker Desktop | 4.x | https://docker.com/products/docker-desktop |
| Git | 2.x | https://git-scm.com |

## Variables de entorno

Copia `.env.example` a `.env` y rellena los valores:

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

## Levantar el entorno

```bash
# Linux / macOS
docker compose up -d && npm install && npm run db:migrate

# Windows (PowerShell)
docker compose up -d; npm install; npm run db:migrate
```

## Verificar que todo funciona

```bash
# Comprueba el health de la API
curl http://localhost:3000/health

# O en Windows con PowerShell
Invoke-RestMethod http://localhost:3000/health
```
""",
        )

        arch_overview = GeneratedFile(
            path="docs/architecture/overview.md",
            language="markdown",
            content=f"""# Arquitectura — {req.project_name}

## Diagrama de componentes

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │   Frontend   │   │     API      │   │  Database  │  │
│  │  {stack[0][:12]:12} │──▶│  {stack[1][:12]:12} │──▶│ PostgreSQL │  │
│  │   :5173      │   │   :3000      │   │   :5432    │  │
│  └──────────────┘   └──────────────┘   └────────────┘  │
│                                                         │
{'│                       ┌──────────────┐                │' if req.needs_ai else ''}
{'│                       │  AI Service  │                │' if req.needs_ai else ''}
{'│                       │  FastAPI     │                │' if req.needs_ai else ''}
{'│                       │   :8003      │                │' if req.needs_ai else ''}
{'│                       └──────────────┘                │' if req.needs_ai else ''}
└─────────────────────────────────────────────────────────┘
```

## Stack seleccionado

{chr(10).join(f'| {t.split(" ")[0]} | {" ".join(t.split(" ")[1:])} | |' for t in stack) if stack else '| React | Frontend | SPA |'}

## Decisiones de registro (ADR)

Ver `docs/adr/` para las decisiones de arquitectura documentadas.
""",
        )

        adr_001 = GeneratedFile(
            path="docs/adr/adr-001-tech-stack.md",
            language="markdown",
            content=f"""# ADR-001: Selección del stack tecnológico

**Estado**: Aceptado
**Fecha**: {__import__('datetime').date.today().isoformat()}
**Deciders**: ProgresIA Studio (generado automáticamente)

## Contexto

Se necesita seleccionar el stack tecnológico para el MVP de {req.project_name},
un proyecto del sector {req.sector}.

## Decisión

Stack seleccionado: **{', '.join(stack[:4])}**

## Justificación

- Ecosistema maduro con amplia documentación
- Buena integración entre los componentes del stack
- Preparado para escalar cuando el MVP valide la propuesta de valor

## Consecuencias

- **Positivas**: Velocidad de desarrollo, comunidad activa, compatibilidad
- **Negativas**: Requiere conocimiento previo del stack
- **Neutras**: Dependencia del ecosistema JavaScript/TypeScript

## Alternativas consideradas

- Stack alternativo A: descartado por mayor complejidad operacional
- Stack alternativo B: descartado por menor soporte de la comunidad
""",
        )

        contributing = GeneratedFile(
            path="docs/development/contributing.md",
            language="markdown",
            content=f"""# Guía de contribución — {req.project_name}

## Flujo de trabajo Git

```bash
# 1. Crea una rama para tu tarea
git checkout -b feat/nombre-de-la-funcionalidad

# 2. Trabaja en tu cambio
# ...

# 3. Commit con Conventional Commits
git commit -m "feat: añadir gestión de reservas"

# 4. Push y crea un Pull Request
git push origin feat/nombre-de-la-funcionalidad
```

## Convenciones de commits

| Prefijo | Cuándo usarlo |
|---------|---------------|
| `feat:` | Nueva funcionalidad |
| `fix:` | Corrección de bug |
| `docs:` | Documentación |
| `refactor:` | Refactorización sin cambio de comportamiento |
| `test:` | Añadir o corregir tests |
| `chore:` | Mantenimiento (deps, config) |

## Antes de hacer un PR

- [ ] Los tests pasan: `npm test`
- [ ] Sin errores TypeScript: `npx tsc --noEmit`
- [ ] Linting pasa: `npm run lint`
- [ ] Actualizar `sdd/plans/milestones.md` si la tarea estaba en el backlog
""",
        )

        return [
            readme,
            constitution,
            requirements_md,
            user_stories,
            openspec_stub,
            milestones,
            context_prompt,
            resume_prompt,
            add_feature_prompt,
            fix_bug_prompt,
            env_setup,
            arch_overview,
            adr_001,
            contributing,
        ]

    def _readme_file(
        self, req: CodeGenerationRequest, slug: str, stack: list[str]
    ) -> GeneratedFile:
        has_python   = any(s.lower() in {"fastapi", "django", "flask", "python"} for s in stack)
        db_name      = next((s for s in stack if any(db in s.lower() for db in ["postgres", "mysql", "mongo", "sqlite"])), "PostgreSQL")
        api_port     = "8003" if has_python else "3000"
        web_port     = "5173"

        content = f"""# {req.project_name}

> MVP generado con [ProgresIA Studio](https://progresia.studio) — metodología SDD.

**Sector**: {req.sector} | **Stack**: {', '.join(stack[:4])}

---

## Requisitos previos

| Herramienta | Versión | Descarga |
|-------------|---------|----------|
| Node.js | 20 LTS | https://nodejs.org |
| Docker Desktop | 4.x+ | https://docker.com/products/docker-desktop |
| Git | 2.x+ | https://git-scm.com |
{'| Python | 3.12+ | https://python.org |' if has_python else ''}

---

## Instalación y arranque

### 1. Clonar el repositorio

```bash
git clone <repo-url> {slug}
cd {slug}
```

### 2. Configurar variables de entorno

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Edita `.env` con tus valores.

### 3. Levantar la base de datos

```bash
docker compose up -d
```

### 4. Instalar dependencias y migrar

```bash
# Linux / macOS
npm install && npm run db:migrate

# Windows (PowerShell)
npm install; npm run db:migrate
```

{'### 5. Instalar dependencias Python' + chr(10) + chr(10) + '```bash' + chr(10) + '# Linux / macOS' + chr(10) + 'cd apps/ai-service && pip install -r requirements.txt && cd ../' + chr(10) + chr(10) + '# Windows (PowerShell)' + chr(10) + 'cd apps\\ai-service; pip install -r requirements.txt; cd ../' + chr(10) + '```' + chr(10) if has_python else ''}
### {6 if has_python else 5}. Arrancar en desarrollo

```bash
# Linux / macOS — arranca todos los servicios
npm run dev

# Windows (PowerShell) — arranca cada servicio por separado
# Terminal 1 — API
cd apps/api; npm run dev

# Terminal 2 — Frontend
cd apps/web; npm run dev
{'# Terminal 3 — AI Service' + chr(10) + 'cd apps/ai-service; python -m uvicorn app.main:app --port 8003 --reload' if has_python else ''}
```

---

## URLs en desarrollo

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:{web_port} |
| API | http://localhost:{api_port} |
{'| AI Service | http://localhost:8003 |' if has_python else ''}
| {db_name} | localhost:5432 |

---

## Estructura del proyecto

```
{slug}/
├── apps/
│   ├── web/          # Frontend ({stack[0] if stack else 'React'})
│   ├── api/          # Backend ({stack[1] if len(stack) > 1 else 'API'})
{'│   └── ai-service/  # Servicio de IA (FastAPI)' if has_python else ''}
├── sdd/              # Especificaciones SDD del proyecto
│   ├── constitution.md
│   ├── requirements/
│   ├── specifications/
│   ├── plans/
│   ├── prompts/      # Instrucciones para IA (Claude, Copilot...)
│   └── setup/
├── docs/             # Documentación técnica
│   ├── architecture/
│   ├── development/
│   └── adr/          # Architecture Decision Records
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Comandos útiles

```bash
# Ver logs de todos los servicios
docker compose logs -f

# Resetear la base de datos
npm run db:reset

# Ejecutar tests
npm test

# Comprobar tipos TypeScript
npx tsc --noEmit
```

---

## Continuar con IA

Este proyecto incluye instrucciones optimizadas para IA en `sdd/prompts/`:

- `project-context.md` — Contexto completo para abrir una nueva sesión
- `resume-session.md` — Para retomar el trabajo donde lo dejaste
- `add-feature.md` — Para añadir nuevas funcionalidades
- `fix-bug.md` — Para resolver errores con ayuda de IA

---

## Licencia

MIT © {req.project_name}
"""
        return GeneratedFile(path="README.md", language="markdown", content=content)

    # ── Backend files ───────────────────────────────────────────────────────

    def _api_package_json(self, slug: str) -> GeneratedFile:
        content = (
            '{\n'
            f'  "name": "@{slug}/api",\n'
            '  "version": "0.1.0",\n'
            '  "private": true,\n'
            '  "scripts": {\n'
            '    "dev": "tsx watch src/index.ts",\n'
            '    "build": "tsc -p tsconfig.json",\n'
            '    "start": "node dist/index.js",\n'
            '    "db:push": "prisma db push",\n'
            '    "db:migrate": "prisma migrate dev",\n'
            '    "db:seed": "tsx src/seed.ts"\n'
            '  },\n'
            '  "dependencies": {\n'
            '    "@fastify/cors": "^9.0.1",\n'
            '    "@prisma/client": "^5.22.0",\n'
            '    "@trpc/server": "^11.0.0",\n'
            '    "fastify": "^4.28.1",\n'
            '    "zod": "^3.23.8"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "@types/node": "^22.0.0",\n'
            '    "prisma": "^5.22.0",\n'
            '    "tsx": "^4.19.2",\n'
            '    "typescript": "^5.7.2"\n'
            '  }\n'
            '}\n'
        )
        return GeneratedFile(path="apps/api/package.json", language="json", content=content)

    def _api_tsconfig(self) -> GeneratedFile:
        content = (
            '{\n'
            '  "compilerOptions": {\n'
            '    "target": "ES2022",\n'
            '    "module": "ESNext",\n'
            '    "moduleResolution": "Bundler",\n'
            '    "outDir": "dist",\n'
            '    "rootDir": "src",\n'
            '    "strict": true,\n'
            '    "esModuleInterop": true,\n'
            '    "skipLibCheck": true\n'
            '  },\n'
            '  "include": ["src"]\n'
            '}\n'
        )
        return GeneratedFile(path="apps/api/tsconfig.json", language="json", content=content)

    def _api_index(self, slug: str) -> GeneratedFile:
        content = (
            "import { fastifyTRPCPlugin } from '@trpc/server/adapters/fastify';\n"
            "import Fastify from 'fastify';\n"
            "import cors from '@fastify/cors';\n"
            "import { appRouter } from './router.js';\n"
            "import { createContext } from './trpc.js';\n"
            "\n"
            "const server = Fastify({ logger: true });\n"
            "\n"
            "await server.register(cors, { origin: process.env.WEB_URL ?? 'http://localhost:3000' });\n"
            "\n"
            "await server.register(fastifyTRPCPlugin, {\n"
            "  prefix: '/trpc',\n"
            "  trpcOptions: { router: appRouter, createContext },\n"
            "});\n"
            "\n"
            f"server.get('/health', async () => ({{ status: 'ok', service: '{slug}-api' }}));\n"
            "\n"
            "const port = Number(process.env.PORT ?? 4000);\n"
            "await server.listen({ port, host: '0.0.0.0' });\n"
            "console.log(`\U0001f680 API ready at http://0.0.0.0:${port}/trpc`);\n"
        )
        return GeneratedFile(path="apps/api/src/index.ts", language="typescript", content=content)

    def _api_trpc(self, req: CodeGenerationRequest) -> GeneratedFile:
        auth_comment = "// import { verifyToken } from './modules/auth/auth.service.js';" if req.needs_auth else ""
        content = (
            "import { initTRPC, TRPCError } from '@trpc/server';\n"
            "import type { CreateFastifyContextOptions } from '@trpc/server/adapters/fastify';\n"
            "import { PrismaClient } from '@prisma/client';\n"
            f"{auth_comment}\n"
            "\n"
            "export const prisma = new PrismaClient();\n"
            "\n"
            "export async function createContext({ req }: CreateFastifyContextOptions) {\n"
            "  return { prisma, req };\n"
            "}\n"
            "\n"
            "export type Context = Awaited<ReturnType<typeof createContext>>;\n"
            "\n"
            "const t = initTRPC.context<Context>().create();\n"
            "\n"
            "export const router = t.router;\n"
            "export const publicProcedure = t.procedure;\n"
            "export const protectedProcedure = t.procedure.use(async ({ ctx, next }) => {\n"
            "  const auth = ctx.req.headers.authorization;\n"
            "  if (!auth?.startsWith('Bearer ')) throw new TRPCError({ code: 'UNAUTHORIZED' });\n"
            "  return next();\n"
            "});\n"
        )
        return GeneratedFile(path="apps/api/src/trpc.ts", language="typescript", content=content)

    def _api_router(self, modules: list[str]) -> GeneratedFile:
        import_lines = "\n".join(
            f"import {{ {_camel(_slug(m))}Router }} from './modules/{_slug(m)}/{_slug(m)}.router.js';"
            for m in modules[:5]
        )
        route_lines = "\n  ".join(
            f"{_camel(_slug(m))}: {_camel(_slug(m))}Router,"
            for m in modules[:5]
        )
        content = (
            "import { router } from './trpc.js';\n"
            f"{import_lines}\n"
            "\n"
            f"export const appRouter = router({{\n"
            f"  {route_lines}\n"
            "});\n"
            "\n"
            "export type AppRouter = typeof appRouter;\n"
        )
        return GeneratedFile(path="apps/api/src/router.ts", language="typescript", content=content)

    def _prisma_schema(self, modules: list[str], needs_auth: bool) -> GeneratedFile:
        user_model = (
            "\nmodel User {\n"
            "  id           String   @id @default(uuid())\n"
            "  email        String   @unique\n"
            "  name         String\n"
            "  passwordHash String\n"
            '  role         String   @default("user")\n'
            "  createdAt    DateTime @default(now())\n"
            "  updatedAt    DateTime @updatedAt\n"
            "}\n"
        ) if needs_auth else ""

        module_models = ""
        for mod in modules[:5]:
            pascal = _pascal(mod)
            module_models += (
                f"\nmodel {pascal} {{\n"
                "  id          String   @id @default(uuid())\n"
                "  name        String\n"
                "  description String?\n"
                '  status      String   @default("active")\n'
                "  createdAt   DateTime @default(now())\n"
                "  updatedAt   DateTime @updatedAt\n"
                "}\n"
            )

        content = (
            "generator client {\n"
            '  provider = "prisma-client-js"\n'
            "}\n"
            "\n"
            "datasource db {\n"
            '  provider = "postgresql"\n'
            '  url      = env("DATABASE_URL")\n'
            "}\n"
            f"{user_model}{module_models}"
        )
        return GeneratedFile(path="apps/api/prisma/schema.prisma", language="prisma", content=content)

    def _module_entity(self, slug: str, pascal: str) -> GeneratedFile:
        content = (
            f"export class {pascal}Entity {{\n"
            "  constructor(\n"
            "    public readonly id: string,\n"
            "    public name: string,\n"
            "    public description: string | null,\n"
            "    public status: string,\n"
            "    public readonly createdAt: Date,\n"
            "    public updatedAt: Date,\n"
            "  ) {}\n"
            "\n"
            "  isActive(): boolean {\n"
            "    return this.status === 'active';\n"
            "  }\n"
            "\n"
            "  deactivate(): void {\n"
            "    this.status = 'inactive';\n"
            "    this.updatedAt = new Date();\n"
            "  }\n"
            "}\n"
        )
        return GeneratedFile(
            path=f"apps/api/src/modules/{slug}/{slug}.entity.ts",
            language="typescript",
            content=content,
        )

    def _module_service(self, slug: str, pascal: str, camel: str) -> GeneratedFile:
        content = (
            "import type { PrismaClient } from '@prisma/client';\n"
            f"import {{ {pascal}Entity }} from './{slug}.entity.js';\n"
            "\n"
            f"export class {pascal}Service {{\n"
            "  constructor(private readonly prisma: PrismaClient) {}\n"
            "\n"
            f"  async findAll(): Promise<{pascal}Entity[]> {{\n"
            f"    const records = await this.prisma.{camel}.findMany({{\n"
            "      orderBy: { createdAt: 'desc' },\n"
            "    }});\n"
            f"    return records.map(r => new {pascal}Entity(r.id, r.name, r.description, r.status, r.createdAt, r.updatedAt));\n"
            "  }\n"
            "\n"
            f"  async findById(id: string): Promise<{pascal}Entity | null> {{\n"
            f"    const r = await this.prisma.{camel}.findUnique({{ where: {{ id }} }});\n"
            "    if (!r) return null;\n"
            f"    return new {pascal}Entity(r.id, r.name, r.description, r.status, r.createdAt, r.updatedAt);\n"
            "  }\n"
            "\n"
            f"  async create(data: {{ name: string; description?: string }}): Promise<{pascal}Entity> {{\n"
            f"    const r = await this.prisma.{camel}.create({{\n"
            "      data: { name: data.name, description: data.description ?? null },\n"
            "    }});\n"
            f"    return new {pascal}Entity(r.id, r.name, r.description, r.status, r.createdAt, r.updatedAt);\n"
            "  }\n"
            "\n"
            f"  async update(id: string, data: {{ name?: string; description?: string; status?: string }}): Promise<{pascal}Entity> {{\n"
            f"    const r = await this.prisma.{camel}.update({{ where: {{ id }}, data }});\n"
            f"    return new {pascal}Entity(r.id, r.name, r.description, r.status, r.createdAt, r.updatedAt);\n"
            "  }\n"
            "\n"
            "  async delete(id: string): Promise<void> {\n"
            f"    await this.prisma.{camel}.delete({{ where: {{ id }} }});\n"
            "  }\n"
            "}\n"
        )
        return GeneratedFile(
            path=f"apps/api/src/modules/{slug}/{slug}.service.ts",
            language="typescript",
            content=content,
        )

    def _module_router(self, slug: str, pascal: str, camel: str) -> GeneratedFile:
        content = (
            "import { z } from 'zod';\n"
            "import { router, publicProcedure } from '../../trpc.js';\n"
            f"import {{ {pascal}Service }} from './{slug}.service.js';\n"
            "\n"
            "const createInput = z.object({\n"
            "  name: z.string().min(1).max(200),\n"
            "  description: z.string().max(1000).optional(),\n"
            "});\n"
            "\n"
            "const updateInput = z.object({\n"
            "  id: z.string().uuid(),\n"
            "  name: z.string().min(1).max(200).optional(),\n"
            "  description: z.string().max(1000).optional(),\n"
            "  status: z.enum(['active', 'inactive']).optional(),\n"
            "});\n"
            "\n"
            f"export const {camel}Router = router({{\n"
            "  list: publicProcedure.query(async ({ ctx }) => {\n"
            f"    const svc = new {pascal}Service(ctx.prisma);\n"
            "    return svc.findAll();\n"
            "  }),\n"
            "\n"
            "  byId: publicProcedure\n"
            "    .input(z.object({ id: z.string().uuid() }))\n"
            "    .query(async ({ ctx, input }) => {\n"
            f"      const svc = new {pascal}Service(ctx.prisma);\n"
            "      return svc.findById(input.id);\n"
            "    }),\n"
            "\n"
            "  create: publicProcedure\n"
            "    .input(createInput)\n"
            "    .mutation(async ({ ctx, input }) => {\n"
            f"      const svc = new {pascal}Service(ctx.prisma);\n"
            "      return svc.create(input);\n"
            "    }),\n"
            "\n"
            "  update: publicProcedure\n"
            "    .input(updateInput)\n"
            "    .mutation(async ({ ctx, input }) => {\n"
            "      const { id, ...data } = input;\n"
            f"      const svc = new {pascal}Service(ctx.prisma);\n"
            "      return svc.update(id, data);\n"
            "    }),\n"
            "\n"
            "  delete: publicProcedure\n"
            "    .input(z.object({ id: z.string().uuid() }))\n"
            "    .mutation(async ({ ctx, input }) => {\n"
            f"      const svc = new {pascal}Service(ctx.prisma);\n"
            "      await svc.delete(input.id);\n"
            "      return { success: true };\n"
            "    }),\n"
            "}});\n"
        )
        return GeneratedFile(
            path=f"apps/api/src/modules/{slug}/{slug}.router.ts",
            language="typescript",
            content=content,
        )

    # ── Frontend files ──────────────────────────────────────────────────────

    def _web_package_json(self, slug: str) -> GeneratedFile:
        content = (
            '{\n'
            f'  "name": "@{slug}/web",\n'
            '  "version": "0.1.0",\n'
            '  "private": true,\n'
            '  "scripts": {\n'
            '    "dev": "next dev",\n'
            '    "build": "next build",\n'
            '    "start": "next start"\n'
            '  },\n'
            '  "dependencies": {\n'
            '    "@tanstack/react-query": "^5.62.16",\n'
            '    "@trpc/client": "^11.0.0",\n'
            '    "@trpc/react-query": "^11.0.0",\n'
            '    "@trpc/server": "^11.0.0",\n'
            '    "next": "^14.2.21",\n'
            '    "react": "^18.3.1",\n'
            '    "react-dom": "^18.3.1",\n'
            '    "zod": "^3.23.8"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "@types/node": "^22.0.0",\n'
            '    "@types/react": "^18.3.12",\n'
            '    "@types/react-dom": "^18.3.1",\n'
            '    "autoprefixer": "^10.4.20",\n'
            '    "postcss": "^8.4.49",\n'
            '    "tailwindcss": "^3.4.16",\n'
            '    "typescript": "^5.7.2"\n'
            '  }\n'
            '}\n'
        )
        return GeneratedFile(path="apps/web/package.json", language="json", content=content)

    def _web_tsconfig(self) -> GeneratedFile:
        content = (
            '{\n'
            '  "compilerOptions": {\n'
            '    "target": "ES2022",\n'
            '    "lib": ["dom", "dom.iterable", "esnext"],\n'
            '    "allowJs": true,\n'
            '    "skipLibCheck": true,\n'
            '    "strict": true,\n'
            '    "noEmit": true,\n'
            '    "esModuleInterop": true,\n'
            '    "module": "esnext",\n'
            '    "moduleResolution": "Bundler",\n'
            '    "resolveJsonModule": true,\n'
            '    "isolatedModules": true,\n'
            '    "jsx": "preserve",\n'
            '    "incremental": true,\n'
            '    "plugins": [{ "name": "next" }],\n'
            '    "paths": { "@/*": ["./src/*"] }\n'
            '  },\n'
            '  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],\n'
            '  "exclude": ["node_modules"]\n'
            '}\n'
        )
        return GeneratedFile(path="apps/web/tsconfig.json", language="json", content=content)

    def _web_tailwind(self) -> GeneratedFile:
        content = (
            "import type { Config } from 'tailwindcss';\n"
            "\n"
            "const config: Config = {\n"
            "  content: ['./src/**/*.{ts,tsx}'],\n"
            "  theme: {\n"
            "    extend: {\n"
            "      colors: {\n"
            "        brand: { DEFAULT: '#6366f1', dark: '#4f46e5' },\n"
            "      },\n"
            "    },\n"
            "  },\n"
            "  plugins: [],\n"
            "};\n"
            "\n"
            "export default config;\n"
        )
        return GeneratedFile(path="apps/web/tailwind.config.ts", language="typescript", content=content)

    def _web_layout(self, project_name: str) -> GeneratedFile:
        content = (
            "import type { Metadata } from 'next';\n"
            "import './globals.css';\n"
            "import { TRPCProvider } from '@/lib/provider';\n"
            "\n"
            "export const metadata: Metadata = {\n"
            f"  title: '{project_name}',\n"
            "  description: 'Generated by ProgresIA Studio',\n"
            "};\n"
            "\n"
            "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
            "  return (\n"
            '    <html lang="es">\n'
            '      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">\n'
            "        <TRPCProvider>\n"
            '          <header className="border-b bg-white px-6 py-3 shadow-sm">\n'
            f'            <h1 className="text-xl font-bold text-brand">{project_name}</h1>\n'
            "          </header>\n"
            '          <main className="container mx-auto px-4 py-8">{children}</main>\n'
            "        </TRPCProvider>\n"
            "      </body>\n"
            "    </html>\n"
            "  );\n"
            "}\n"
        )
        return GeneratedFile(path="apps/web/src/app/layout.tsx", language="typescript", content=content)

    def _web_home_page(self, project_name: str, modules: list[str]) -> GeneratedFile:
        links = "\n        ".join(
            f'<a href="/{_slug(m)}" className="rounded-lg border bg-white p-4 shadow-sm hover:shadow-md transition-shadow">'
            f'<h2 className="font-semibold">{m}</h2></a>'
            for m in modules[:6]
        )
        content = (
            "export default function HomePage() {\n"
            "  return (\n"
            "    <div>\n"
            f'      <h2 className="mb-6 text-2xl font-bold">Bienvenido a {project_name}</h2>\n'
            '      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">\n'
            f"        {links}\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )
        return GeneratedFile(path="apps/web/src/app/page.tsx", language="typescript", content=content)

    def _web_module_page(self, pascal: str, camel: str) -> GeneratedFile:
        content = (
            "'use client';\n"
            "\n"
            "import { trpc } from '@/lib/trpc';\n"
            "import { useState } from 'react';\n"
            "\n"
            f"export default function {pascal}Page() {{\n"
            "  const [name, setName] = useState('');\n"
            "  const utils = trpc.useUtils();\n"
            "\n"
            f"  const list = trpc.{camel}.list.useQuery();\n"
            f"  const create = trpc.{camel}.create.useMutation({{\n"
            "    onSuccess: () => {\n"
            f"      void utils.{camel}.list.invalidate();\n"
            "      setName('');\n"
            "    },\n"
            "  }});\n"
            f"  const del = trpc.{camel}.delete.useMutation({{\n"
            f"    onSuccess: () => void utils.{camel}.list.invalidate(),\n"
            "  }});\n"
            "\n"
            "  return (\n"
            '    <div className="max-w-2xl">\n'
            f'      <h2 className="mb-4 text-xl font-bold">{pascal}</h2>\n'
            "\n"
            '      <form\n'
            '        className="mb-6 flex gap-2"\n'
            "        onSubmit={(e) => {\n"
            "          e.preventDefault();\n"
            "          if (name.trim()) create.mutate({ name: name.trim() });\n"
            "        }}\n"
            "      >\n"
            '        <input\n'
            '          className="flex-1 rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"\n'
            '          placeholder="Nuevo nombre..."\n'
            "          value={name}\n"
            "          onChange={(e) => setName(e.target.value)}\n"
            "        />\n"
            "        <button\n"
            '          type="submit"\n'
            "          disabled={create.isPending}\n"
            '          className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"\n'
            "        >\n"
            "          Añadir\n"
            "        </button>\n"
            "      </form>\n"
            "\n"
            '      {list.isLoading && <p className="text-gray-500">Cargando...</p>}\n'
            '      <ul className="grid gap-2">\n'
            "        {list.data?.map((item) => (\n"
            '          <li key={item.id} className="flex items-center justify-between rounded-lg border bg-white px-4 py-3 shadow-sm">\n'
            "            <span>{item.name}</span>\n"
            "            <button\n"
            "              onClick={() => del.mutate({ id: item.id })}\n"
            '              className="text-sm text-red-500 hover:underline"\n'
            "            >\n"
            "              Eliminar\n"
            "            </button>\n"
            "          </li>\n"
            "        ))}\n"
            "      </ul>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )
        return GeneratedFile(
            path=f"apps/web/src/app/{camel}/page.tsx",
            language="typescript",
            content=content,
        )

    def _web_trpc_client(self) -> GeneratedFile:
        content = (
            "import { createTRPCReact } from '@trpc/react-query';\n"
            "import type { AppRouter } from '../../../api/src/router';\n"
            "\n"
            "export const trpc = createTRPCReact<AppRouter>();\n"
            "\n"
            "export const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000/trpc';\n"
        )
        return GeneratedFile(path="apps/web/src/lib/trpc.ts", language="typescript", content=content)

    def _web_provider(self) -> GeneratedFile:
        content = (
            "'use client';\n"
            "\n"
            "import { QueryClient, QueryClientProvider } from '@tanstack/react-query';\n"
            "import { httpBatchLink } from '@trpc/client';\n"
            "import { useState } from 'react';\n"
            "import { trpc, apiUrl } from './trpc';\n"
            "\n"
            "export function TRPCProvider({ children }: { children: React.ReactNode }) {\n"
            "  const [queryClient] = useState(() => new QueryClient());\n"
            "  const [trpcClient] = useState(() =>\n"
            "    trpc.createClient({\n"
            "      links: [httpBatchLink({ url: apiUrl })],\n"
            "    })\n"
            "  );\n"
            "\n"
            "  return (\n"
            "    <trpc.Provider client={trpcClient} queryClient={queryClient}>\n"
            "      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>\n"
            "    </trpc.Provider>\n"
            "  );\n"
            "}\n"
        )
        return GeneratedFile(path="apps/web/src/lib/provider.tsx", language="typescript", content=content)

    # ── Infrastructure ──────────────────────────────────────────────────────

    def _api_dockerfile(self) -> GeneratedFile:
        content = (
            "FROM node:22-alpine AS deps\n"
            "WORKDIR /app\n"
            "COPY package.json package-lock.json ./\n"
            "RUN npm ci --omit=dev\n"
            "\n"
            "FROM node:22-alpine AS build\n"
            "WORKDIR /app\n"
            "COPY package.json package-lock.json ./\n"
            "RUN npm ci\n"
            "COPY . .\n"
            "RUN npm run build\n"
            "\n"
            "FROM node:22-alpine AS runner\n"
            "WORKDIR /app\n"
            "ENV NODE_ENV=production\n"
            "COPY --from=deps /app/node_modules ./node_modules\n"
            "COPY --from=build /app/dist ./dist\n"
            "COPY --from=build /app/prisma ./prisma\n"
            "EXPOSE 4000\n"
            'CMD ["node", "dist/index.js"]\n'
        )
        return GeneratedFile(path="apps/api/Dockerfile", language="dockerfile", content=content)

    def _web_dockerfile(self) -> GeneratedFile:
        content = (
            "FROM node:22-alpine AS deps\n"
            "WORKDIR /app\n"
            "COPY package.json package-lock.json ./\n"
            "RUN npm ci\n"
            "\n"
            "FROM node:22-alpine AS build\n"
            "WORKDIR /app\n"
            "COPY --from=deps /app/node_modules ./node_modules\n"
            "COPY . .\n"
            "RUN npm run build\n"
            "\n"
            "FROM node:22-alpine AS runner\n"
            "WORKDIR /app\n"
            "ENV NODE_ENV=production\n"
            "COPY --from=build /app/.next/standalone ./\n"
            "COPY --from=build /app/.next/static ./.next/static\n"
            "COPY --from=build /app/public ./public\n"
            "EXPOSE 3000\n"
            'CMD ["node", "server.js"]\n'
        )
        return GeneratedFile(path="apps/web/Dockerfile", language="dockerfile", content=content)

    def _nginx_conf(self) -> GeneratedFile:
        content = (
            "upstream api {\n"
            "    server api:4000;\n"
            "}\n"
            "\n"
            "upstream web {\n"
            "    server web:3000;\n"
            "}\n"
            "\n"
            "server {\n"
            "    listen 80;\n"
            "\n"
            "    location /trpc/ {\n"
            "        proxy_pass http://api;\n"
            "        proxy_set_header Host $host;\n"
            "        proxy_set_header X-Real-IP $remote_addr;\n"
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            "    }\n"
            "\n"
            "    location /health {\n"
            "        proxy_pass http://api;\n"
            "    }\n"
            "\n"
            "    location / {\n"
            "        proxy_pass http://web;\n"
            "        proxy_set_header Host $host;\n"
            "        proxy_set_header X-Real-IP $remote_addr;\n"
            "        proxy_http_version 1.1;\n"
            "        proxy_set_header Upgrade $http_upgrade;\n"
            '        proxy_set_header Connection "upgrade";\n'
            "    }\n"
            "}\n"
        )
        return GeneratedFile(path="nginx/nginx.conf", language="nginx", content=content)

    def _docker_compose(self, slug: str, needs_ai: bool) -> GeneratedFile:
        ai_block = (
            "\n"
            "  ai:\n"
            "    build: ./apps/ai-service\n"
            "    environment:\n"
            "      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://ollama:11434}\n"
            "    ports:\n"
            '      - "8002:8002"\n'
            "    depends_on: [postgres]\n"
            "\n"
            "  ollama:\n"
            "    image: ollama/ollama:latest\n"
            "    ports:\n"
            '      - "11434:11434"\n'
            "    volumes:\n"
            "      - ollama_data:/root/.ollama\n"
        ) if needs_ai else ""

        ollama_vol = "\n  ollama_data:" if needs_ai else ""

        content = (
            "services:\n"
            "  postgres:\n"
            "    image: postgres:16-alpine\n"
            "    environment:\n"
            f"      POSTGRES_USER: {slug}\n"
            f"      POSTGRES_PASSWORD: {slug}\n"
            f"      POSTGRES_DB: {slug}_db\n"
            "    ports:\n"
            '      - "5432:5432"\n'
            "    volumes:\n"
            "      - postgres_data:/var/lib/postgresql/data\n"
            "    healthcheck:\n"
            '      test: ["CMD-SHELL", "pg_isready -U '
            f'{slug}"]\n'
            "      interval: 5s\n"
            "      timeout: 5s\n"
            "      retries: 5\n"
            "\n"
            "  redis:\n"
            "    image: redis:7-alpine\n"
            "    ports:\n"
            '      - "6379:6379"\n'
            "\n"
            "  api:\n"
            "    build: ./apps/api\n"
            "    environment:\n"
            f"      - DATABASE_URL=postgresql://{slug}:{slug}@postgres:5432/{slug}_db\n"
            "      - PORT=4000\n"
            "      - WEB_URL=http://nginx\n"
            "    ports:\n"
            '      - "4000:4000"\n'
            "    depends_on:\n"
            "      postgres:\n"
            "        condition: service_healthy\n"
            f"{ai_block}"
            "\n"
            "  web:\n"
            "    build: ./apps/web\n"
            "    environment:\n"
            "      - NEXT_PUBLIC_API_URL=http://nginx/trpc\n"
            "    ports:\n"
            '      - "3000:3000"\n'
            "    depends_on: [api]\n"
            "\n"
            "  nginx:\n"
            "    image: nginx:alpine\n"
            "    ports:\n"
            '      - "80:80"\n'
            "    volumes:\n"
            "      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf\n"
            "    depends_on: [api, web]\n"
            "\n"
            "volumes:\n"
            f"  postgres_data:{ollama_vol}\n"
        )
        return GeneratedFile(path="docker-compose.yml", language="yaml", content=content)

    def _env_example(self, slug: str) -> GeneratedFile:
        content = (
            "# Database\n"
            f"DATABASE_URL=postgresql://{slug}:{slug}@localhost:5432/{slug}_db\n"
            "\n"
            "# API\n"
            "PORT=4000\n"
            "WEB_URL=http://localhost:3000\n"
            "\n"
            "# Frontend\n"
            "NEXT_PUBLIC_API_URL=http://localhost:4000/trpc\n"
            "\n"
            "# Auth (generate with: openssl rand -hex 32)\n"
            "JWT_SECRET=change_me_in_production\n"
            "\n"
            "# AI (optional)\n"
            "OLLAMA_BASE_URL=http://localhost:11434\n"
            "GROQ_API_KEY=\n"
            "OPENAI_API_KEY=\n"
        )
        return GeneratedFile(path=".env.example", language="env", content=content)
