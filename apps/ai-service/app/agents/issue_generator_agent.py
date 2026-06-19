"""IssueGeneratorAgent: transforms an OpenSpec into structured GitHub Issues.

Reads exclusively from the canonical OpenSpecDoc keys:
  spec["requirements"]           — list of {id, title, description, acceptance_criteria}
  spec["user_stories"]           — list of {id, actor, goal, benefit}
  spec["modules"]                — list of module name strings
  spec["milestones"]             — ordered milestone list
  spec["architecture"]["type"]   — drives architecture-specific setup issues

Never guesses key names. If the spec was produced by OpenSpecAgent, all keys exist.
"""
from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.schemas.issues import GitHubIssue, IssueGenerationRequest, IssueGenerationResponse

logger = logging.getLogger(__name__)

# ── Milestones ─────────────────────────────────────────────────────────────────

_DEFAULT_MILESTONES = [
    "Milestone 1: Setup y arquitectura",
    "Milestone 2: Modelos y base de datos",
    "Milestone 3: API y lógica de negocio",
    "Milestone 4: Frontend y UX",
    "Milestone 5: Testing y despliegue",
]

# ── Architecture-specific setup issues ────────────────────────────────────────
# Each entry: (title, body_md, labels, priority)
_ARCH_SETUP: dict[str, list[tuple[str, str, list[str], str]]] = {
    "DJANGO_REST": [
        (
            "Crear modelos Django y aplicar migraciones iniciales",
            (
                "## Descripción\nDefinir los modelos ORM de Django y generar las migraciones de base de datos.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] Modelos definidos en `apps/<módulo>/models.py`\n"
                "- [ ] Migraciones generadas con `python manage.py makemigrations`\n"
                "- [ ] Migraciones aplicadas con `python manage.py migrate`\n"
                "- [ ] Campos validados con el ORM de Django\n\n"
                "## Tareas técnicas\n"
                "- [ ] Definir campos, tipos y relaciones en los modelos\n"
                "- [ ] Registrar modelos en `apps/<módulo>/admin.py`\n"
                "- [ ] Crear fixtures de datos de prueba"
            ),
            ["database", "backend"], "high",
        ),
        (
            "Implementar DRF ViewSets y registrar rutas con Router",
            (
                "## Descripción\nCrear los ViewSets de Django REST Framework y registrarlos con el DefaultRouter.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] `ModelViewSet` implementado por cada recurso principal\n"
                "- [ ] Router registrado en `urls.py`\n"
                "- [ ] Serializers con validación de campos\n"
                "- [ ] Paginación configurada (`PAGE_SIZE` en settings)\n\n"
                "## Tareas técnicas\n"
                "- [ ] Crear `serializers.py` con `ModelSerializer`\n"
                "- [ ] Crear `views.py` con `ModelViewSet`\n"
                "- [ ] Registrar en `urls.py` con `DefaultRouter`\n"
                "- [ ] Configurar filtros con `django-filters`"
            ),
            ["api", "backend"], "high",
        ),
        (
            "Configurar Django Admin para gestión de datos",
            (
                "## Descripción\nRegistrar todos los modelos en el panel de administración de Django.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] Acceso en `/admin/` con superusuario\n"
                "- [ ] Todos los modelos registrados con `@admin.register`\n"
                "- [ ] `list_display`, `search_fields` y `list_filter` configurados\n"
                "- [ ] Superusuario creado con `python manage.py createsuperuser`\n\n"
                "## Tareas técnicas\n"
                "- [ ] Configurar `admin.py` en cada app\n"
                "- [ ] Definir `list_display` útil para cada modelo\n"
                "- [ ] Añadir acciones personalizadas si procede"
            ),
            ["backend", "ui/ux"], "medium",
        ),
    ],
    "NEXTJS_APP": [
        (
            "Definir Prisma schema y ejecutar migración inicial",
            (
                "## Descripción\nDefinir el esquema de Prisma con todos los modelos del proyecto.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] `prisma/schema.prisma` con todos los modelos definidos\n"
                "- [ ] Migración inicial generada: `npx prisma migrate dev --name init`\n"
                "- [ ] `npx prisma studio` abre la BD correctamente\n"
                "- [ ] Seed de datos de prueba ejecutable\n\n"
                "## Tareas técnicas\n"
                "- [ ] Definir modelos con relaciones y tipos correctos\n"
                "- [ ] Crear `prisma/seed.ts` con datos de ejemplo\n"
                "- [ ] Añadir `db:seed` al `package.json`"
            ),
            ["database", "backend"], "high",
        ),
        (
            "Implementar API Routes con validación Zod",
            (
                "## Descripción\nCrear los endpoints REST en `src/app/api/` usando Next.js API Routes.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] Rutas CRUD en `src/app/api/<recurso>/route.ts` y `[id]/route.ts`\n"
                "- [ ] Validación de entrada con Zod schemas\n"
                "- [ ] Respuestas tipadas con `NextResponse.json()`\n"
                "- [ ] Errores HTTP correctos (400, 401, 404, 500)\n\n"
                "## Tareas técnicas\n"
                "- [ ] Crear schemas Zod para validación\n"
                "- [ ] Implementar handlers GET, POST, PUT, DELETE\n"
                "- [ ] Proteger rutas con NextAuth session check"
            ),
            ["api", "backend"], "high",
        ),
        (
            "Configurar NextAuth con provider de credenciales",
            (
                "## Descripción\nImplementar autenticación con NextAuth 5 y provider de email+contraseña.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] `src/app/api/auth/[...nextauth]/route.ts` configurado\n"
                "- [ ] Login y registro funcionando\n"
                "- [ ] `middleware.ts` protege rutas del dashboard\n"
                "- [ ] `useSession()` disponible en Client Components\n\n"
                "## Tareas técnicas\n"
                "- [ ] Configurar `AUTH_SECRET` en `.env`\n"
                "- [ ] Crear `src/lib/auth.ts` con NextAuth config\n"
                "- [ ] Implementar callback de credenciales con bcrypt"
            ),
            ["auth", "backend"], "high",
        ),
    ],
    "LARAVEL_MONOLITH": [
        (
            "Crear Eloquent Models y migraciones de base de datos",
            (
                "## Descripción\nDefinir los modelos Eloquent y generar las migraciones para PostgreSQL.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] Modelos en `app/Models/` con relaciones Eloquent\n"
                "- [ ] Migraciones en `database/migrations/`\n"
                "- [ ] `php artisan migrate` ejecuta sin errores\n"
                "- [ ] `$fillable` y `$hidden` configurados en cada modelo\n\n"
                "## Tareas técnicas\n"
                "- [ ] `php artisan make:model NombreModelo -m` por cada entidad\n"
                "- [ ] Definir relaciones `belongsTo`, `hasMany`, etc.\n"
                "- [ ] Crear seeder con `php artisan make:seeder`"
            ),
            ["database", "backend"], "high",
        ),
        (
            "Implementar controllers API Resource y proteger con Sanctum",
            (
                "## Descripción\nCrear controllers REST y proteger las rutas con Laravel Sanctum.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] Controllers con `php artisan make:controller --api`\n"
                "- [ ] Rutas en `routes/api.php` con `->middleware('auth:sanctum')`\n"
                "- [ ] Form Requests para validación de entrada\n"
                "- [ ] API Resources para formatear las respuestas JSON\n\n"
                "## Tareas técnicas\n"
                "- [ ] `php artisan make:request` para cada operación\n"
                "- [ ] `php artisan make:resource` para las respuestas\n"
                "- [ ] Configurar CORS en `config/cors.php`"
            ),
            ["api", "backend"], "high",
        ),
    ],
    "LARAVEL_INERTIA_REACT": [
        (
            "Configurar Inertia.js con React y Vite",
            (
                "## Descripción\nConfigurar el stack Laravel + Inertia.js + React + Vite.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] `npm run dev` sirve assets con HMR\n"
                "- [ ] `Inertia::render('NombrePagina')` desde controllers Laravel\n"
                "- [ ] `usePage()` disponible en componentes React\n"
                "- [ ] Shared data (auth user) disponible en todas las páginas\n\n"
                "## Tareas técnicas\n"
                "- [ ] `composer require inertiajs/inertia-laravel`\n"
                "- [ ] `npm install @inertiajs/react`\n"
                "- [ ] Configurar `HandleInertiaRequests` middleware"
            ),
            ["frontend", "backend"], "high",
        ),
    ],
    "NESTJS_REACT": [
        (
            "Configurar módulos NestJS y conexión Prisma",
            (
                "## Descripción\nCrear la estructura modular de NestJS con Prisma como ORM.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] `PrismaModule` global disponible en todos los módulos\n"
                "- [ ] Módulo por cada bounded context (`AuthModule`, `<Recurso>Module`...)\n"
                "- [ ] `prisma/schema.prisma` con todos los modelos\n"
                "- [ ] `npx prisma migrate dev` ejecuta sin errores\n\n"
                "## Tareas técnicas\n"
                "- [ ] `nest g module <nombre>` por cada feature\n"
                "- [ ] Crear `PrismaService` extendiendo `PrismaClient`\n"
                "- [ ] Registrar guards JWT en `APP_GUARD`"
            ),
            ["backend", "database"], "high",
        ),
    ],
    "FASTAPI_AI": [
        (
            "Configurar FastAPI con SQLAlchemy y Alembic",
            (
                "## Descripción\nEstructurar el proyecto FastAPI con ORM y migraciones.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] Modelos SQLAlchemy en `app/models/`\n"
                "- [ ] Migraciones con Alembic: `alembic upgrade head`\n"
                "- [ ] `/docs` Swagger UI disponible\n"
                "- [ ] Inyección de dependencias (`Depends`) para la sesión DB\n\n"
                "## Tareas técnicas\n"
                "- [ ] Configurar `DATABASE_URL` en `.env`\n"
                "- [ ] `alembic init` y configurar `env.py`\n"
                "- [ ] Schemas Pydantic para request/response"
            ),
            ["backend", "database"], "high",
        ),
        (
            "Integrar LangChain/LangGraph para el pipeline de IA",
            (
                "## Descripción\nConfigurar el pipeline de agentes IA con LangChain y LangGraph.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] Al menos un LLM provider configurado (Groq, OpenAI o Gemini)\n"
                "- [ ] Pipeline de agentes con LangGraph StateGraph\n"
                "- [ ] Fallback a Ollama local si no hay API key externa\n"
                "- [ ] Endpoint POST `/generate` devuelve respuesta estructurada\n\n"
                "## Tareas técnicas\n"
                "- [ ] `pip install langchain langgraph langchain-groq`\n"
                "- [ ] Configurar API keys en `.env`\n"
                "- [ ] Crear agente base con `StateGraph`"
            ),
            ["api", "backend"], "high",
        ),
    ],
}

# ── Label inference ────────────────────────────────────────────────────────────

_LABEL_KEYWORDS: dict[str, list[str]] = {
    "auth":         ["auth", "security", "backend"],
    "usuario":      ["auth", "backend"],
    "registro":     ["auth", "backend"],
    "login":        ["auth", "backend"],
    "base de datos":["database", "backend"],
    "modelo":       ["database", "backend"],
    "migración":    ["database"],
    "api":          ["api", "backend"],
    "endpoint":     ["api", "backend"],
    "frontend":     ["frontend", "ui/ux"],
    "interfaz":     ["frontend", "ui/ux"],
    "pantalla":     ["frontend", "ui/ux"],
    "docker":       ["devops"],
    "deploy":       ["devops"],
    "despliegue":   ["devops"],
    "test":         ["testing"],
    "documentación":["docs"],
}


def _infer_labels(text: str) -> list[str]:
    lower = text.lower()
    labels: set[str] = set()
    for keyword, kw_labels in _LABEL_KEYWORDS.items():
        if keyword in lower:
            labels.update(kw_labels)
    return list(labels) if labels else ["feature"]


def _infer_priority(text: str, index: int) -> str:
    lower = text.lower()
    if any(k in lower for k in ["auth", "login", "seguridad", "base de datos", "modelo", "setup", "configurar", "migración"]):
        return "high"
    if index < 3:
        return "high"
    if any(k in lower for k in ["test", "documentación", "readme", "deploy", "documentar", "despliegue"]):
        return "low"
    return "medium"


# ── Deterministic builder ─────────────────────────────────────────────────────

def _rule_based_issues(req: IssueGenerationRequest) -> IssueGenerationResponse:
    spec     = req.openspec
    name     = req.project_name
    arch_type = spec.get("architecture", {}).get("type", "") if isinstance(spec.get("architecture"), dict) else ""

    # Canonical keys — no fallback guessing
    requirements = spec.get("requirements", [])
    user_stories = spec.get("user_stories", [])
    modules      = spec.get("modules", [])
    milestones   = spec.get("milestones", []) or _DEFAULT_MILESTONES

    ms = {
        "setup":    milestones[0] if len(milestones) > 0 else _DEFAULT_MILESTONES[0],
        "models":   milestones[1] if len(milestones) > 1 else _DEFAULT_MILESTONES[1],
        "api":      milestones[2] if len(milestones) > 2 else _DEFAULT_MILESTONES[2],
        "frontend": milestones[3] if len(milestones) > 3 else _DEFAULT_MILESTONES[3],
        "testing":  milestones[4] if len(milestones) > 4 else _DEFAULT_MILESTONES[4],
    }

    issues: list[GitHubIssue] = []

    # 1. Universal setup issue
    issues.append(GitHubIssue(
        title=f"Configurar entorno de desarrollo y repositorio de {name}",
        body=(
            "## Descripción\n"
            f"Preparar el repositorio, el entorno Docker y la estructura base del proyecto `{name}`.\n\n"
            "## Criterios de aceptación\n"
            "- [ ] Repositorio Git inicializado con `.gitignore` y `README.md`\n"
            "- [ ] `docker-compose.yml` funcional con todos los servicios\n"
            "- [ ] Variables de entorno documentadas en `.env.example`\n"
            "- [ ] Pipeline CI/CD configurado en GitHub Actions\n\n"
            "## Tareas técnicas\n"
            "- [ ] Crear estructura de carpetas del proyecto\n"
            "- [ ] Configurar Docker y docker-compose\n"
            "- [ ] Añadir GitHub Actions workflow (lint, test, build)\n"
            "- [ ] Documentar comandos de instalación en README"
        ),
        labels=["devops", "docs"],
        priority="high",
        milestone=ms["setup"],
    ))

    # 2. Architecture-specific setup issues
    for title, body, labels, priority in _ARCH_SETUP.get(arch_type, []):
        issues.append(GitHubIssue(
            title=title, body=body, labels=labels,
            priority=priority, milestone=ms["models"],
        ))

    # 3. Universal auth issue (if not already covered by arch-specific)
    arch_handles_auth = arch_type in {"NEXTJS_APP", "LARAVEL_MONOLITH", "DJANGO_REST", "NESTJS_REACT", "LARAVEL_INERTIA_REACT"}
    if not arch_handles_auth:
        issues.append(GitHubIssue(
            title="Implementar autenticación de usuarios con JWT",
            body=(
                "## Descripción\nSistema de registro, login y gestión de sesiones con tokens JWT.\n\n"
                "## Criterios de aceptación\n"
                "- [ ] `POST /auth/register` — crear cuenta con email y contraseña\n"
                "- [ ] `POST /auth/login` — devolver access token + refresh token\n"
                "- [ ] `GET /auth/me` — perfil del usuario autenticado\n"
                "- [ ] Contraseñas hasheadas con bcrypt\n"
                "- [ ] Rutas protegidas con middleware de auth\n\n"
                "## Tareas técnicas\n"
                "- [ ] Crear modelo/entidad User\n"
                "- [ ] Implementar generación y verificación de JWT\n"
                "- [ ] Tests unitarios del flujo de auth"
            ),
            labels=["auth", "backend", "api"],
            priority="high",
            milestone=ms["models"],
        ))

    # 4. Module issues (from spec.modules)
    for module in modules[:5]:
        module_name = module.strip()
        if module_name.lower() == "auth":
            continue
        issues.append(GitHubIssue(
            title=f"Implementar módulo {module_name}: CRUD completo y validación",
            body=(
                f"## Descripción\nCRUD completo para el recurso `{module_name}` con endpoints REST y validación.\n\n"
                "## Criterios de aceptación\n"
                f"- [ ] Modelo/entidad `{module_name}` con todos los campos definidos en el OpenSpec\n"
                f"- [ ] `GET /{module_name.lower()}s` — listado con paginación\n"
                f"- [ ] `POST /{module_name.lower()}s` — crear con validación\n"
                f"- [ ] `GET /{module_name.lower()}s/:id` — detalle del recurso\n"
                f"- [ ] `PUT /{module_name.lower()}s/:id` — actualización completa\n"
                f"- [ ] `DELETE /{module_name.lower()}s/:id` — eliminación con verificación de permisos\n"
                "- [ ] Solo el propietario puede gestionar sus propios recursos\n\n"
                "## Tareas técnicas\n"
                f"- [ ] Crear migración/schema para la tabla `{module_name.lower()}s`\n"
                f"- [ ] Implementar modelo `{module_name}` con ORM\n"
                "- [ ] Crear controller/viewset/resolver con CRUD\n"
                "- [ ] Validación de datos de entrada\n"
                "- [ ] Tests de integración del CRUD"
            ),
            labels=_infer_labels(module_name),
            priority="medium",
            milestone=ms["api"],
        ))

    # 5. Requirement issues (from spec.requirements)
    for i, req_item in enumerate(requirements[:6]):
        if not isinstance(req_item, dict):
            continue
        title    = req_item.get("title", "")
        desc     = req_item.get("description", "")
        req_id   = req_item.get("id", f"RF-{i+1:03d}")
        criteria = req_item.get("acceptance_criteria", [])
        if not title:
            continue
        criteria_md = "\n".join(f"- [ ] {c}" for c in criteria) if criteria else "- [ ] Funcionalidad implementada y probada"
        issues.append(GitHubIssue(
            title=f"[{req_id}] {title}",
            body=(
                f"## Descripción\n{desc or title}\n\n"
                "## Criterios de aceptación\n"
                f"{criteria_md}\n\n"
                "## Tareas técnicas\n"
                "- [ ] Implementar la funcionalidad\n"
                "- [ ] Añadir tests\n"
                "- [ ] Actualizar documentación"
            ),
            labels=_infer_labels(title),
            priority=_infer_priority(title, i),
            milestone=ms["api"],
        ))

    # 6. User story issues (from spec.user_stories)
    for story in user_stories[:3]:
        if not isinstance(story, dict):
            continue
        actor   = story.get("actor", "Usuario")
        goal    = story.get("goal", "")
        benefit = story.get("benefit", "")
        if not goal:
            continue
        issues.append(GitHubIssue(
            title=f"[UX] Como {actor}: {goal}",
            body=(
                f"## Historia de usuario\n**Como** {actor}, **quiero** {goal}"
                + (f", **para** {benefit}" if benefit else "") + "\n\n"
                "## Criterios de aceptación\n"
                "- [ ] El usuario puede completar el flujo descrito sin errores\n"
                "- [ ] La interfaz es intuitiva y accesible (WCAG AA)\n"
                "- [ ] Los estados de carga y error están manejados\n"
                "- [ ] Test E2E o de integración verifica el flujo completo"
            ),
            labels=["feature", "frontend", "ui/ux"],
            priority="medium",
            milestone=ms["frontend"],
        ))

    # 7. Testing issue
    issues.append(GitHubIssue(
        title="Añadir suite de tests y cobertura de código",
        body=(
            "## Descripción\nImplementar tests unitarios y de integración para los módulos principales.\n\n"
            "## Criterios de aceptación\n"
            "- [ ] Cobertura > 70% en módulos principales\n"
            "- [ ] Tests de auth: register, login, rutas protegidas\n"
            "- [ ] Tests de los endpoints CRUD principales\n"
            "- [ ] Tests ejecutables con un solo comando\n"
            "- [ ] CI los ejecuta automáticamente en cada PR\n\n"
            "## Tareas técnicas\n"
            "- [ ] Configurar framework de testing con BD de test\n"
            "- [ ] Escribir tests unitarios de servicios/agentes\n"
            "- [ ] Escribir tests de integración de endpoints\n"
            "- [ ] Configurar reporte de cobertura en CI"
        ),
        labels=["testing"],
        priority="medium",
        milestone=ms["testing"],
    ))

    # 8. Deployment issue
    issues.append(GitHubIssue(
        title="Configurar despliegue en producción con Docker",
        body=(
            "## Descripción\nPreparar el proyecto para despliegue reproducible en producción.\n\n"
            "## Criterios de aceptación\n"
            "- [ ] Dockerfile multi-stage optimizado para producción\n"
            "- [ ] Variables de entorno de producción documentadas\n"
            "- [ ] Migraciones aplicadas automáticamente en el arranque\n"
            "- [ ] Health check endpoint `/health` funcionando\n"
            "- [ ] HTTPS configurado (Railway/Fly.io/nginx + certbot)\n\n"
            "## Tareas técnicas\n"
            "- [ ] Optimizar Dockerfile (imagen slim, sin dev deps)\n"
            "- [ ] Configurar Railway/Fly.io o VPS propio\n"
            "- [ ] Documentar proceso de despliegue en `docs/deployment.md`\n"
            "- [ ] Añadir step de deploy al GitHub Actions workflow"
        ),
        labels=["devops"],
        priority="low",
        milestone=ms["testing"],
    ))

    return IssueGenerationResponse(
        project_name=name,
        milestones=milestones,
        issues=issues,
        total=len(issues),
    )


# ── LLM system prompt ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Eres un experto en gestión de proyectos de software y GitHub.
Tu misión es transformar una especificación técnica (OpenSpec) en GitHub Issues bien estructurados.

Cada issue debe:
- Tener un título accionable (verbo infinitivo: "Implementar", "Crear", "Añadir", "Configurar")
- Cuerpo en Markdown con: descripción, criterios de aceptación con checkboxes, tareas técnicas
- Etiquetas de: feature, auth, api, frontend, backend, database, testing, devops, docs, ui/ux
- Prioridad: high | medium | low
- Milestone: usa los milestones exactos del OpenSpec proporcionado

Genera entre 8 y 15 issues. Cubre: setup inicial, modelos, API, frontend, auth, testing y despliegue.
Si el OpenSpec incluye arquitectura específica (Django, Next.js, Laravel...), genera issues específicos a esa tecnología.

Responde ÚNICAMENTE con JSON:
{
  "milestones": ["(usa los milestones del OpenSpec exactamente)"],
  "issues": [
    {
      "title": "...",
      "body": "## Descripción\\n...\\n## Criterios de aceptación\\n- [ ] ...\\n## Tareas técnicas\\n- [ ] ...",
      "labels": ["..."],
      "priority": "high|medium|low",
      "milestone": "(nombre exacto del milestone)"
    }
  ]
}"""


class IssueGeneratorAgent:
    def generate(self, req: IssueGenerationRequest) -> IssueGenerationResponse:
        llm = get_llm("general")
        if llm is not None:
            try:
                spec_summary = json.dumps(req.openspec, ensure_ascii=False, indent=2)[:4000]
                prompt = (
                    f"Proyecto: {req.project_name}\n"
                    f"Sector: {req.sector}\n\n"
                    f"OpenSpec:\n{spec_summary}"
                )
                resp    = llm.invoke([SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=prompt)])
                content = resp.content if hasattr(resp, "content") else str(resp)
                match   = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data       = json.loads(match.group())
                    milestones = data.get("milestones", [])
                    raw_issues = data.get("issues", [])
                    if raw_issues:
                        return IssueGenerationResponse(
                            project_name=req.project_name,
                            milestones=milestones,
                            issues=[
                                GitHubIssue(
                                    title=i.get("title", ""),
                                    body=i.get("body", ""),
                                    labels=i.get("labels", ["feature"]),
                                    priority=i.get("priority", "medium"),
                                    milestone=i.get("milestone"),
                                )
                                for i in raw_issues
                                if i.get("title")
                            ],
                            total=len(raw_issues),
                        )
            except Exception as exc:
                logger.warning("Issue generation LLM call failed, using rule-based: %s", exc)

        return _rule_based_issues(req)
