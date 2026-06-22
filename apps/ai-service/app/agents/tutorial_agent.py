"""TutorialAgent: generates a step-by-step implementation tutorial from an OpenSpec.

For every known architecture type, produces a concrete, command-rich tutorial
that guides a developer from zero to a running MVP. Commands are specific to the
stack (python manage.py for Django, php artisan for Laravel, npx prisma for Next.js).

For unknown architectures the LLM is used; deterministic fallback is the generic guide.
"""
from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.schemas.tutorial import TutorialPhase, TutorialRequest, TutorialResponse, TutorialStep

logger = logging.getLogger(__name__)


def _s(action: str, command: str | None = None, notes: str | None = None) -> TutorialStep:
    return TutorialStep(action=action, command=command, notes=notes)


def _p(title: str, description: str, steps: list[TutorialStep]) -> TutorialPhase:
    return TutorialPhase(title=title, description=description, steps=steps)


# ── Architecture-specific tutorial builders ────────────────────────────────────

def _django_rest(req: TutorialRequest) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Prepara el entorno Python y levanta los servicios Docker.", [
            _s("Clonar el repositorio e ir al directorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Crear y activar el entorno virtual", "python -m venv .venv && source .venv/bin/activate", "En Windows: .venv\\Scripts\\activate"),
            _s("Instalar dependencias del proyecto", "pip install -r requirements.txt"),
            _s("Copiar variables de entorno", "cp .env.example .env"),
            _s("Arrancar PostgreSQL con Docker", "docker compose up -d postgres"),
            _s("Aplicar migraciones iniciales", "python manage.py migrate"),
            _s("Verificar que el servidor arranca", "python manage.py runserver", "Accede a http://localhost:8000"),
        ]),
        _p("Fase 1: Modelos y migraciones", "Define las entidades del dominio como modelos Django.", [
            _s("Abrir models.py del módulo principal", f"code apps/{(modules[0] if modules else 'core').lower()}s/models.py"),
            _s("Definir campos, tipos y relaciones del modelo"),
            _s("Generar migración automática", "python manage.py makemigrations"),
            _s("Aplicar la migración a la base de datos", "python manage.py migrate"),
            _s("Verificar en la shell de Django", "python manage.py shell", ">>> from apps.modulo.models import Modelo; Modelo.objects.all()"),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 2: Autenticación JWT con simplejwt", "Configura el sistema de autenticación basado en tokens JWT.", [
            _s("Verificar que simplejwt está en INSTALLED_APPS y REST_FRAMEWORK en settings.py"),
            _s("Probar obtener token de acceso", "curl -X POST http://localhost:8000/api/token/ -d 'username=admin&password=...'"),
            _s("Crear superusuario para pruebas", "python manage.py createsuperuser"),
            _s("Probar endpoint protegido con el token", 'curl -H "Authorization: Bearer <token>" http://localhost:8000/api/...'),
        ]))

    for module in modules[:4]:
        mod_lower = module.lower()
        phases.append(_p(
            f"Fase {len(phases)}: Módulo {module}",
            f"Implementa el CRUD completo para el recurso {module} con DRF.",
            [
                _s(f"Completar serializers.py de {module}", f"code apps/{mod_lower}s/serializers.py"),
                _s("Implementar ModelViewSet en views.py", f"code apps/{mod_lower}s/views.py"),
                _s("Registrar rutas con DefaultRouter en urls.py", f"code apps/{mod_lower}s/urls.py"),
                _s("Probar el endpoint CRUD", f"curl http://localhost:8000/api/{mod_lower}s/"),
                _s(f"Registrar {module} en Django Admin", f"code apps/{mod_lower}s/admin.py"),
            ]
        ))

    if req.needs_admin_panel:
        phases.append(_p(f"Fase {len(phases)}: Django Admin", "Configura el panel de administración para gestión interna.", [
            _s("Acceder al admin con superusuario", "python manage.py runserver"),
            _s("Abrir panel de administración", None, "Accede a http://localhost:8000/admin/"),
            _s("Personalizar list_display y search_fields en admin.py de cada módulo"),
        ]))

    phases.append(_p(f"Fase {len(phases)}: Tests", "Ejecuta la suite de tests antes de desplegar.", [
        _s("Ejecutar todos los tests", "python manage.py test"),
        _s("Ejecutar tests con cobertura", "coverage run manage.py test && coverage report"),
        _s("Generar informe HTML de cobertura", "coverage html", "Abre htmlcov/index.html en el navegador"),
    ]))

    phases.append(_p(f"Fase {len(phases)}: Despliegue con Docker", "Prepara la imagen de producción y despliega.", [
        _s("Construir imagen Docker de producción", f"docker build -t {slug}:latest ."),
        _s("Arrancar todos los servicios", "docker compose -f docker-compose.yml up -d"),
        _s("Aplicar migraciones en producción", "docker compose exec web python manage.py migrate"),
        _s("Recopilar archivos estáticos", "docker compose exec web python manage.py collectstatic --no-input"),
        _s("Verificar que todos los servicios están sanos", "docker compose ps"),
    ]))

    return phases


def _nextjs_app(req: TutorialRequest) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Instala dependencias y levanta la base de datos.", [
            _s("Clonar el repositorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Instalar dependencias Node.js", "npm install"),
            _s("Copiar variables de entorno", "cp .env.example .env.local"),
            _s("Levantar PostgreSQL", "docker compose up -d postgres"),
            _s("Generar cliente Prisma", "npx prisma generate"),
            _s("Aplicar migración inicial", "npx prisma migrate dev --name init"),
            _s("Cargar datos de prueba", "npx prisma db seed", "Requiere que exista prisma/seed.ts"),
            _s("Iniciar servidor de desarrollo", "npm run dev", "Accede a http://localhost:3000"),
        ]),
        _p("Fase 1: Schema de Prisma", "Define las entidades del dominio en el schema de Prisma.", [
            _s("Abrir schema de Prisma", "code prisma/schema.prisma"),
            _s("Añadir o ajustar modelos con sus relaciones"),
            _s("Crear migración con el cambio", "npx prisma migrate dev --name <nombre-del-cambio>"),
            _s("Explorar los datos en Prisma Studio", "npx prisma studio", "Abre http://localhost:5555"),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 2: Autenticación con NextAuth 5", "Configura el login con provider de credenciales.", [
            _s("Revisar src/lib/auth.ts con la configuración de NextAuth"),
            _s("Verificar que AUTH_SECRET está en .env.local"),
            _s("Probar login en http://localhost:3000/login"),
            _s("Comprobar que el middleware protege las rutas del dashboard", "code src/middleware.ts"),
        ]))

    for module in modules[:4]:
        mod_lower = module.lower()
        phases.append(_p(
            f"Fase {len(phases)}: API de {module}",
            f"Crea los API Routes para el recurso {module}.",
            [
                _s("Crear route handler GET/POST", f"code src/app/api/{mod_lower}s/route.ts"),
                _s("Crear route handler con parámetro [id]", f"code src/app/api/{mod_lower}s/[id]/route.ts"),
                _s("Añadir validación de entrada con Zod"),
                _s("Proteger endpoint con session check"),
                _s("Probar con curl o Postman", f"curl http://localhost:3000/api/{mod_lower}s"),
            ]
        ))

    phases.append(_p(f"Fase {len(phases)}: Componentes React", "Crea los Server y Client Components.", [
        _s("Crear página de listado (Server Component)", f"code src/app/{(modules[0] if modules else 'dashboard').lower()}s/page.tsx"),
        _s("Crear componente de formulario (Client Component)"),
        _s("Usar React Query para mutaciones y optimistic updates"),
        _s("Añadir estados de carga y error"),
    ]))

    phases.append(_p(f"Fase {len(phases)}: Build y tests", "Verifica que la app compila y los tests pasan.", [
        _s("Ejecutar type-check", "npx tsc --noEmit"),
        _s("Ejecutar tests unitarios", "npm run test"),
        _s("Compilar para producción", "npm run build"),
        _s("Probar el build de producción", "npm start"),
    ]))

    phases.append(_p(f"Fase {len(phases)}: Despliegue", "Despliega el proyecto en Vercel o con Docker.", [
        _s("Opción A — Vercel (recomendado)", "npx vercel deploy", "Conecta con el repositorio de GitHub para CI/CD automático"),
        _s("Opción B — Docker", f"docker build -t {slug}:latest . && docker compose up -d"),
        _s("Configurar variables de entorno en producción (DATABASE_URL, AUTH_SECRET, etc.)"),
        _s("Verificar el health check", "curl https://tu-app.vercel.app/api/health"),
    ]))

    return phases


def _laravel(req: TutorialRequest, has_frontend: bool = False) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Instala dependencias PHP y levanta los servicios.", [
            _s("Clonar el repositorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Instalar dependencias PHP con Composer", "composer install"),
            _s("Copiar variables de entorno", "cp .env.example .env"),
            _s("Generar clave de aplicación Laravel", "php artisan key:generate"),
            _s("Levantar PostgreSQL con Docker", "docker compose up -d postgres"),
            _s("Actualizar .env con las credenciales de la BD"),
            _s("Ejecutar migraciones y seeders", "php artisan migrate --seed"),
            _s("Iniciar el servidor de desarrollo", "php artisan serve", "Accede a http://localhost:8000"),
        ]),
    ]

    if has_frontend:
        phases[0].steps.insert(-1, _s("Instalar dependencias frontend", "npm install && npm run dev", "El servidor de Vite arranca en http://localhost:5173"))

    phases.append(_p("Fase 1: Eloquent Models y migraciones", "Define las entidades con Eloquent y crea las migraciones.", [
        _s("Crear modelo con migración", "php artisan make:model NombreModelo -m"),
        _s("Definir columnas en la migración", "code database/migrations/<timestamp>_create_nombre_modelos_table.php"),
        _s("Añadir relaciones en el modelo ($fillable, hasMany, belongsTo...)"),
        _s("Aplicar la migración", "php artisan migrate"),
        _s("Crear seeder de datos de prueba", "php artisan make:seeder NombreModeloSeeder && php artisan db:seed"),
    ]))

    if req.needs_auth:
        phases.append(_p("Fase 2: Autenticación con Laravel Sanctum", "Protege la API con tokens de Sanctum.", [
            _s("Verificar que Sanctum está instalado en config/auth.php"),
            _s("Crear endpoints de auth en routes/api.php"),
            _s("Probar registro de usuario", "curl -X POST http://localhost:8000/api/auth/register -d '{...}'"),
            _s("Probar login y obtener token", "curl -X POST http://localhost:8000/api/auth/login -d '{...}'"),
            _s("Probar endpoint protegido", 'curl -H "Authorization: Bearer <token>" http://localhost:8000/api/user'),
        ]))

    for module in modules[:4]:
        phases.append(_p(
            f"Fase {len(phases)}: Módulo {module}",
            f"Implementa el API Resource controller para {module}.",
            [
                _s("Crear controller API", f"php artisan make:controller {module}Controller --api"),
                _s("Crear Form Request para validación", f"php artisan make:request {module}Request"),
                _s("Crear API Resource para la respuesta", f"php artisan make:resource {module}Resource"),
                _s("Registrar rutas en routes/api.php", None, f"Route::apiResource('{module.lower()}s', {module}Controller::class);"),
                _s("Implementar los métodos CRUD en el controller"),
                _s("Probar el CRUD", f"curl http://localhost:8000/api/{module.lower()}s"),
            ]
        ))

    phases.append(_p(f"Fase {len(phases)}: Tests con PHPUnit", "Ejecuta la suite de tests antes de desplegar.", [
        _s("Configurar .env.testing con BD de test"),
        _s("Ejecutar todos los tests", "php artisan test"),
        _s("Ejecutar tests con cobertura (requiere Xdebug)", "php artisan test --coverage"),
    ]))

    phases.append(_p(f"Fase {len(phases)}: Despliegue", "Despliega Laravel en producción.", [
        _s("Construir imagen Docker", f"docker build -t {slug}:latest ."),
        _s("Arrancar servicios de producción", "docker compose up -d"),
        _s("Ejecutar migraciones en producción", "docker compose exec app php artisan migrate --force"),
        _s("Optimizar para producción", "docker compose exec app php artisan optimize"),
        _s("Verificar que la app responde", "curl http://tu-dominio.com/api/health"),
    ]))

    return phases


def _nestjs_react(req: TutorialRequest) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Instala dependencias y levanta los servicios.", [
            _s("Clonar e ir al directorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Instalar dependencias del monorepo", "npm install"),
            _s("Copiar variables de entorno", "cp .env.example .env"),
            _s("Levantar PostgreSQL y Redis", "docker compose up -d postgres redis"),
            _s("Generar cliente Prisma", "npx prisma generate"),
            _s("Aplicar migración inicial", "npx prisma migrate dev --name init"),
            _s("Iniciar backend NestJS", "npm run start:dev", "Accede a http://localhost:3000"),
            _s("Iniciar frontend React", "npm run dev:web", "Accede a http://localhost:5173"),
        ]),
        _p("Fase 1: Módulos NestJS y Prisma", "Crea los módulos bounded contexts con NestJS CLI.", [
            _s("Crear un módulo con CLI", f"nest g module {(modules[0] if modules else 'recursos').lower()}"),
            _s("Crear service y controller del módulo", f"nest g service {(modules[0] if modules else 'recursos').lower()} && nest g controller {(modules[0] if modules else 'recursos').lower()}"),
            _s("Definir modelo en prisma/schema.prisma"),
            _s("Crear migración", "npx prisma migrate dev --name add_modulo"),
            _s("Explorar datos con Prisma Studio", "npx prisma studio"),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 2: Autenticación JWT", "Implementa auth con Passport.js y JWT.", [
            _s("Verificar AuthModule y JwtModule en src/auth/"),
            _s("Probar endpoint de login", "curl -X POST http://localhost:3000/auth/login -d '{...}'"),
            _s("Probar ruta protegida con el token", 'curl -H "Authorization: Bearer <token>" http://localhost:3000/me'),
            _s("Verificar guards en los controllers (@UseGuards(JwtAuthGuard))"),
        ]))

    for module in modules[:4]:
        mod_lower = module.lower()
        phases.append(_p(
            f"Fase {len(phases)}: Módulo {module}",
            f"Implementa el CRUD del módulo {module}.",
            [
                _s(f"Implementar {module}Service con métodos findAll, findOne, create, update, remove"),
                _s(f"Implementar {module}Controller con endpoints REST"),
                _s("Crear DTOs de validación con class-validator"),
                _s("Probar el endpoint", f"curl http://localhost:3000/{mod_lower}s"),
                _s("Ver documentación Swagger", None, "Abre http://localhost:3000/api para ver todos los endpoints"),
            ]
        ))

    phases.append(_p(f"Fase {len(phases)}: Frontend React", "Conecta el frontend con la API.", [
        _s("Configurar el cliente API (Axios o fetch) con baseURL y auth header"),
        _s("Crear hooks de React Query para cada recurso"),
        _s("Implementar páginas de listado y formularios"),
        _s("Gestionar el token JWT en localStorage y añadir interceptor de auth"),
    ]))

    phases.append(_p(f"Fase {len(phases)}: Tests y despliegue", "Verifica y despliega.", [
        _s("Ejecutar tests unitarios del backend", "npm run test"),
        _s("Ejecutar tests e2e", "npm run test:e2e"),
        _s("Construir para producción", "npm run build"),
        _s("Desplegar con Docker", "docker compose -f docker-compose.prod.yml up -d"),
    ]))

    return phases


def _fastapi_ai(req: TutorialRequest) -> list[TutorialPhase]:
    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Crea el entorno Python y arranca los servicios.", [
            _s("Crear entorno virtual", "python -m venv .venv && source .venv/bin/activate", "En Windows: .venv\\Scripts\\activate"),
            _s("Instalar dependencias", "pip install -r requirements.txt"),
            _s("Copiar variables de entorno", "cp .env.example .env"),
            _s("Configurar las API keys en .env (OPENAI_API_KEY, GROQ_API_KEY, etc.)"),
            _s("Levantar PostgreSQL con Docker", "docker compose up -d postgres"),
            _s("Aplicar migraciones con Alembic", "alembic upgrade head"),
            _s("Iniciar el servidor FastAPI", "uvicorn app.main:app --reload", "Accede a http://localhost:8000/docs"),
        ]),
        _p("Fase 1: Modelos SQLAlchemy y migraciones", "Define las entidades de la base de datos.", [
            _s("Crear modelos SQLAlchemy en app/models/"),
            _s("Generar script de migración con Alembic", "alembic revision --autogenerate -m 'add modelos'"),
            _s("Revisar el script generado en alembic/versions/"),
            _s("Aplicar la migración", "alembic upgrade head"),
            _s("Verificar en psql o pgAdmin", "docker compose exec postgres psql -U $DB_USER -d $DB_NAME"),
        ]),
        _p("Fase 2: Schemas Pydantic y endpoints FastAPI", "Crea los schemas de validación y los endpoints.", [
            _s("Definir schemas de request/response en app/schemas/"),
            _s("Implementar router con dependencias en app/routers/"),
            _s("Registrar el router en app/main.py"),
            _s("Probar en Swagger UI", None, "Accede a http://localhost:8000/docs"),
            _s("Probar endpoint con curl", "curl http://localhost:8000/api/v1/..."),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 3: Autenticación JWT con OAuth2", "Protege los endpoints con JWT.", [
            _s("Verificar endpoints de auth: POST /auth/register, POST /auth/login"),
            _s("Probar obtención de token", "curl -X POST http://localhost:8000/auth/login -d '{...}'"),
            _s("Probar endpoint protegido", 'curl -H "Authorization: Bearer <token>" http://localhost:8000/users/me'),
            _s("Configurar OAuth2PasswordBearer en los Depends()"),
        ]))

    phases.append(_p(f"Fase {len(phases)}: Pipeline de IA con LangChain", "Configura el agente o cadena de IA.", [
        _s("Verificar conexión al proveedor LLM (Groq/OpenAI)", "python -c \"from app.core.llm import get_llm; print(get_llm('general'))\""),
        _s("Implementar la cadena principal en app/agents/"),
        _s("Probar el agente en modo interactivo", "python -m app.agents.tu_agente"),
        _s("Exponer el agente via endpoint FastAPI"),
        _s("Monitorizar latencia y tokens usados con LangSmith (opcional)", None, "Configura LANGCHAIN_TRACING_V2=true en .env"),
    ]))

    phases.append(_p(f"Fase {len(phases)}: Tests y despliegue", "Verifica y despliega.", [
        _s("Ejecutar tests con pytest", "pytest tests/ -v"),
        _s("Ejecutar con cobertura", "coverage run -m pytest && coverage report"),
        _s("Construir imagen Docker", "docker build -t fastapi-ai:latest ."),
        _s("Desplegar en producción", "docker compose -f docker-compose.prod.yml up -d"),
    ]))

    return phases


def _generic(req: TutorialRequest) -> list[TutorialPhase]:
    modules = req.modules or ["Core"]

    return [
        _p("Fase 0: Configuración del entorno", "Prepara el entorno de desarrollo.", [
            _s("Clonar el repositorio e instalar dependencias"),
            _s("Copiar variables de entorno", "cp .env.example .env"),
            _s("Levantar servicios de infraestructura", "docker compose up -d"),
            _s("Verificar que todos los servicios están activos", "docker compose ps"),
        ]),
        _p("Fase 1: Modelos y base de datos", "Define el esquema de datos.", [
            _s("Definir los modelos según el OpenSpec"),
            _s("Crear y aplicar migraciones"),
            _s("Cargar datos de prueba (seed)"),
        ]),
        *(
            _p(
                f"Fase {i + 2}: Módulo {m}",
                f"Implementa el CRUD para el recurso {m}.",
                [
                    _s(f"Crear el modelo/entidad {m}"),
                    _s("Implementar los endpoints CRUD"),
                    _s("Añadir validaciones de entrada"),
                    _s("Escribir tests unitarios"),
                ]
            )
            for i, m in enumerate(modules[:4])
        ),
        _p(f"Fase {len(modules[:4]) + 2}: Tests y despliegue", "Verifica y despliega el MVP.", [
            _s("Ejecutar la suite de tests completa"),
            _s("Verificar que el build de producción funciona"),
            _s("Desplegar con Docker Compose"),
            _s("Verificar health checks en producción"),
        ]),
    ]


_ARCH_BUILDERS = {
    "DJANGO_REST":           _django_rest,
    "NEXTJS_APP":            _nextjs_app,
    "LARAVEL_MONOLITH":      lambda req: _laravel(req, has_frontend=False),
    "LARAVEL_INERTIA_REACT": lambda req: _laravel(req, has_frontend=True),
    "LARAVEL_INERTIA_VUE":   lambda req: _laravel(req, has_frontend=True),
    "NESTJS_REACT":          _nestjs_react,
    "FASTAPI_AI":            _fastapi_ai,
    "REACT_EXPRESS":         _nestjs_react,   # close enough — both use npm/prisma
}

# ── LLM prompt ─────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Eres un experto en desarrollo de software generando tutoriales de implementación.

A partir del OpenSpec del proyecto, genera un tutorial paso a paso específico para la arquitectura indicada.
Responde SIEMPRE en español. Sé específico con los comandos reales del stack elegido.

Responde ÚNICAMENTE con JSON con este esquema:
{
  "phases": [
    {
      "title": "Fase 0: Nombre de la fase",
      "description": "Qué se hace en esta fase.",
      "steps": [
        { "action": "Descripción clara de la acción", "command": "comando exacto si aplica", "notes": "nota opcional" }
      ]
    }
  ]
}

Genera entre 5 y 8 fases que cubran: setup del entorno, base de datos, autenticación (si aplica),
implementación de módulos, tests y despliegue. Los comandos deben ser específicos para el stack."""


# ── Agent ───────────────────────────────────────────────────────────────────────

class TutorialAgent:
    def generate(self, req: TutorialRequest) -> TutorialResponse:
        # Try architecture-specific deterministic builder first
        builder = _ARCH_BUILDERS.get(req.architecture_type)
        if builder:
            phases = builder(req)
            return _build_response(req, phases)

        # Unknown architecture → try LLM
        llm = get_llm("spec")
        if llm is not None:
            try:
                prompt = (
                    f"Proyecto: {req.project_name} (sector: {req.sector})\n"
                    f"Arquitectura: {req.architecture_type}\n"
                    f"Stack: {', '.join(req.stack)}\n"
                    f"Módulos: {', '.join(req.modules)}\n"
                    f"Auth: {'sí' if req.needs_auth else 'no'} | "
                    f"Admin: {'sí' if req.needs_admin_panel else 'no'}"
                )
                resp    = llm.invoke([SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=prompt)])
                content = resp.content if hasattr(resp, "content") else str(resp)
                match   = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data   = json.loads(match.group())
                    phases = [
                        TutorialPhase(
                            title=p.get("title", ""),
                            description=p.get("description", ""),
                            steps=[
                                TutorialStep(action=s.get("action", ""), command=s.get("command"), notes=s.get("notes"))
                                for s in p.get("steps", [])
                            ],
                        )
                        for p in data.get("phases", [])
                        if p.get("title")
                    ]
                    if phases:
                        return _build_response(req, phases)
            except Exception as exc:
                logger.warning("Tutorial LLM generation failed: %s", exc)

        # Final fallback
        return _build_response(req, _generic(req))


def _build_response(req: TutorialRequest, phases: list[TutorialPhase]) -> TutorialResponse:
    total = sum(len(p.steps) for p in phases)
    return TutorialResponse(
        project_name=req.project_name,
        architecture_type=req.architecture_type,
        phases=phases,
        total_steps=total,
    )
