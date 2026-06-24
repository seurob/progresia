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


def _electron_nestjs(req: TutorialRequest) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Instala Electron, Node.js y levanta el entorno de desarrollo.", [
            _s("Instalar Node.js LTS (≥ 20) y npm", None, "Descarga desde https://nodejs.org/"),
            _s("Clonar el repositorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Instalar dependencias del proyecto", "npm install"),
            _s("Copiar variables de entorno", "cp .env.example .env"),
            _s("Iniciar la app Electron en modo desarrollo", "npm run dev", "Abre la ventana de la app automáticamente"),
        ]),
        _p("Fase 1: Estructura Electron (main + renderer)", "Entiende la separación entre el proceso principal y el renderer.", [
            _s("Abrir el proceso principal", "code src/main/index.ts", "Aquí vive la lógica de sistema: archivos, ventanas, IPC"),
            _s("Abrir el proceso renderer (React)", "code src/renderer/src/App.tsx", "Aquí vive la UI — es una SPA React normal"),
            _s("Revisar el puente IPC entre procesos", "code src/main/ipc/", "ipcMain.handle() expone funciones del SO al renderer"),
            _s("Verificar que la ventana carga correctamente", "npm run dev"),
        ]),
        _p("Fase 2: Base de datos SQLite local", "Configura better-sqlite3 para persistencia local sin servidor.", [
            _s("Verificar que better-sqlite3 está instalado", "npm list better-sqlite3"),
            _s("Abrir la capa de base de datos", "code src/main/database/"),
            _s("Crear las tablas iniciales con migraciones SQL", None, "Las migraciones corren automáticamente al iniciar la app"),
            _s("Verificar que la BD se crea en el directorio de datos del usuario", None, "app.getPath('userData') — no se pierde al actualizar"),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 3: Autenticación local", "Implementa login local o integración con servicios externos.", [
            _s("Revisar el módulo de autenticación en src/main/auth/"),
            _s("Implementar login con credenciales locales (bcrypt)", None, "Las contraseñas se hashean y almacenan en SQLite"),
            _s("Gestionar la sesión activa con electron-store"),
            _s("Proteger rutas IPC con validación de sesión"),
        ]))

    for module in modules[:4]:
        mod_lower = module.lower()
        phases.append(_p(
            f"Fase {len(phases)}: Módulo {module}",
            f"Implementa la funcionalidad {module} con IPC + React.",
            [
                _s(f"Crear handler IPC para {module}", f"code src/main/ipc/{mod_lower}.ts", "ipcMain.handle('{mod_lower}:list', ...)"),
                _s(f"Exponer el canal en el preload", "code src/preload/index.ts"),
                _s(f"Crear componente React que consume el canal", f"code src/renderer/src/pages/{module}.tsx"),
                _s("Probar la funcionalidad en la ventana de la app"),
            ]
        ))

    phases.append(_p(f"Fase {len(phases)}: Build y empaquetado", "Genera instalables para Windows, macOS y Linux.", [
        _s("Compilar TypeScript", "npm run build"),
        _s("Generar instalable para la plataforma actual", "npm run dist", "electron-builder empaqueta todo en un .exe / .dmg / .AppImage"),
        _s("Revisar la carpeta dist/ con el instalable generado"),
        _s("Probar el instalable en una máquina limpia"),
        _s("Configurar electron-updater si necesitas actualizaciones automáticas", "code package.json", "Añade la URL del servidor de actualización en 'build.publish'"),
    ]))

    return phases


def _tauri_fastapi(req: TutorialRequest) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Instala Rust, Node.js y las dependencias del proyecto.", [
            _s("Instalar Rust (necesario para compilar Tauri)", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh", "En Windows: descarga rustup-init.exe desde https://rustup.rs/"),
            _s("Instalar las dependencias de sistema para Tauri", None, "Linux: sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev"),
            _s("Clonar el repositorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Instalar dependencias Node.js (UI React)", "npm install"),
            _s("Instalar dependencias Rust (core Tauri)", "cd src-tauri && cargo fetch"),
            _s("Iniciar la app en modo desarrollo", "npm run tauri dev", "Abre la ventana nativa con Hot Module Replacement en la UI"),
        ]),
        _p("Fase 1: Estructura Tauri (commands + frontend)", "Entiende la separación entre Rust y React.", [
            _s("Abrir la configuración de Tauri", "code src-tauri/tauri.conf.json", "Aquí se configuran permisos, ventana, íconos y bundle ID"),
            _s("Abrir el core Rust", "code src-tauri/src/lib.rs", "Los #[tauri::command] exponen funciones Rust al frontend"),
            _s("Abrir la UI React", "code src/App.tsx", "La UI usa invoke() para llamar a comandos Tauri"),
            _s("Revisar los permisos declarados en capabilities/", "code src-tauri/capabilities/", "Tauri 2 requiere permisos explícitos para filesystem, shell, http..."),
        ]),
        _p("Fase 2: Base de datos SQLite embebida", "Configura SQLite local para persistencia offline-first.", [
            _s("Verificar la dependencia de SQLite en Cargo.toml", "code src-tauri/Cargo.toml", "Busca rusqlite o sqlx con feature sqlite"),
            _s("Revisar la capa de base de datos en Rust", "code src-tauri/src/database/"),
            _s("Probar que la BD se crea correctamente al iniciar", "npm run tauri dev"),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 3: Autenticación con FastAPI backend", "Conecta la app de escritorio con el backend cloud.", [
            _s("Levantar el backend FastAPI", "cd api && uvicorn app.main:app --reload"),
            _s("Verificar que el comando Tauri para auth existe", "code src-tauri/src/commands/auth.rs"),
            _s("Probar el login desde la UI", None, "La app envía las credenciales a la API y almacena el token localmente"),
        ]))

    for module in modules[:3]:
        phases.append(_p(
            f"Fase {len(phases)}: Módulo {module}",
            f"Implementa la funcionalidad {module} con Tauri commands.",
            [
                _s(f"Crear el command Rust para {module}", f"code src-tauri/src/commands/{module.lower()}.rs"),
                _s("Registrar el command en lib.rs", "code src-tauri/src/lib.rs", ".invoke_handler(tauri::generate_handler![...])"),
                _s(f"Crear componente React que invoca el command", f"code src/{module}Page.tsx", "import {{ invoke }} from '@tauri-apps/api/core'; invoke('{module.lower()}:list')"),
                _s("Probar en la app", "npm run tauri dev"),
            ]
        ))

    phases.append(_p(f"Fase {len(phases)}: Build y distribución", "Genera instalables nativos multiplataforma.", [
        _s("Compilar para producción", "npm run tauri build"),
        _s("Encontrar el instalable en src-tauri/target/release/bundle/"),
        _s("Probar el instalable en una máquina limpia", None, "El instalable pesa ~5MB — órdenes de magnitud menos que Electron"),
        _s("Configurar actualizaciones automáticas con Tauri Updater si es necesario"),
    ]))

    return phases


def _flutter_fastapi(req: TutorialRequest) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Instala Flutter SDK y levanta el backend FastAPI.", [
            _s("Instalar Flutter SDK", None, "Descarga desde https://docs.flutter.dev/get-started/install · Añade flutter/bin al PATH"),
            _s("Verificar la instalación", "flutter doctor", "Resuelve los problemas indicados por flutter doctor antes de continuar"),
            _s("Clonar el repositorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Instalar dependencias Flutter", "flutter pub get"),
            _s("Levantar el backend FastAPI", "cd api && pip install -r requirements.txt && uvicorn app.main:app --reload"),
            _s("Iniciar la app en un emulador o dispositivo", "flutter run", "Elige el dispositivo cuando se te pregunte"),
        ]),
        _p("Fase 1: Estructura del proyecto Flutter", "Entiende la arquitectura de la app móvil.", [
            _s("Abrir el punto de entrada", "code lib/main.dart"),
            _s("Revisar la estructura de carpetas", None, "lib/screens/ → páginas · lib/widgets/ → componentes · lib/services/ → llamadas a la API"),
            _s("Abrir el cliente HTTP (dio o http)", "code lib/services/api_client.dart"),
            _s("Actualizar la URL base de la API en api_client.dart", None, "En desarrollo: http://10.0.2.2:8000 (Android emulator) o http://localhost:8000 (iOS simulator)"),
        ]),
        _p("Fase 2: Modelos Dart y serialización", "Define los modelos de datos del dominio.", [
            _s("Crear los modelos Dart en lib/models/"),
            _s("Añadir fromJson/toJson (o usar json_serializable)", "flutter pub add json_serializable build_runner"),
            _s("Generar el código de serialización", "dart run build_runner build"),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 3: Autenticación JWT", "Implementa login y persistencia del token.", [
            _s("Crear la pantalla de login en lib/screens/login_screen.dart"),
            _s("Implementar el método login en lib/services/auth_service.dart"),
            _s("Almacenar el token JWT con flutter_secure_storage", "flutter pub add flutter_secure_storage"),
            _s("Añadir el token a las cabeceras HTTP en api_client.dart"),
            _s("Redirigir al dashboard si ya hay sesión activa al iniciar"),
        ]))

    for module in modules[:3]:
        mod_lower = module.lower()
        phases.append(_p(
            f"Fase {len(phases)}: Módulo {module}",
            f"Implementa la pantalla y el servicio para {module}.",
            [
                _s(f"Crear el servicio de API para {module}", f"code lib/services/{mod_lower}_service.dart"),
                _s(f"Crear la pantalla de listado", f"code lib/screens/{mod_lower}_list_screen.dart"),
                _s(f"Crear la pantalla de detalle/formulario", f"code lib/screens/{mod_lower}_form_screen.dart"),
                _s("Añadir la ruta en lib/main.dart", None, "MaterialApp(routes: {'/modulo': (ctx) => ModuloScreen()})"),
                _s("Probar en el emulador", "flutter run"),
            ]
        ))

    phases.append(_p(f"Fase {len(phases)}: Build y distribución", "Genera los APK/IPA para las tiendas.", [
        _s("Build Android (APK de debug)", "flutter build apk --debug"),
        _s("Build Android (APK de release)", "flutter build apk --release", "Requiere configurar una keystore de firma"),
        _s("Build iOS (requiere Mac con Xcode)", "flutter build ios --release"),
        _s("Alternativa: Expo EAS Build en la nube (si usas Expo)", "eas build --platform all"),
        _s("Probar la APK en un dispositivo real", "flutter install"),
    ]))

    return phases


def _react_native_nestjs(req: TutorialRequest) -> list[TutorialPhase]:
    slug = req.project_name.lower().replace(" ", "-")
    modules = req.modules or ["Core"]

    phases: list[TutorialPhase] = [
        _p("Fase 0: Configuración del entorno", "Instala Expo CLI y levanta el backend NestJS.", [
            _s("Instalar Expo CLI globalmente", "npm install -g expo-cli"),
            _s("Clonar el repositorio", f"git clone <url> {slug} && cd {slug}"),
            _s("Instalar dependencias de la app móvil", f"cd {slug}-mobile && npm install"),
            _s("Instalar dependencias del backend", f"cd {slug}-api && npm install"),
            _s("Levantar PostgreSQL y Redis", f"cd {slug}-api && docker compose up -d postgres redis"),
            _s("Levantar el backend NestJS", f"cd {slug}-api && npm run start:dev"),
            _s("Levantar la app Expo", f"cd {slug}-mobile && npx expo start", "Escanea el QR con Expo Go en tu móvil o usa un emulador"),
        ]),
        _p("Fase 1: Estructura React Native + Expo", "Entiende la organización del proyecto móvil.", [
            _s("Abrir el punto de entrada", "code app/_layout.tsx", "Expo Router usa file-based routing — igual que Next.js"),
            _s("Revisar la carpeta app/ con las pantallas", "code app/", "Cada archivo .tsx en app/ es una ruta/pantalla"),
            _s("Abrir el cliente API", "code src/lib/api.ts", "Configura la URL base: http://TU_IP:3000 (no localhost en el dispositivo real)"),
            _s("Verificar que el backend responde", f"curl http://localhost:3000/health"),
        ]),
        _p("Fase 2: Schema Prisma y backend NestJS", "Define los módulos del backend.", [
            _s(f"cd {slug}-api && abrir el schema de Prisma", f"code {slug}-api/prisma/schema.prisma"),
            _s("Crear migración inicial", f"cd {slug}-api && npx prisma migrate dev --name init"),
            _s("Explorar los datos con Prisma Studio", f"cd {slug}-api && npx prisma studio"),
            _s("Verificar los módulos NestJS generados en src/modules/"),
        ]),
    ]

    if req.needs_auth:
        phases.append(_p("Fase 3: Autenticación JWT (móvil + backend)", "Implementa login con persistencia segura del token.", [
            _s("Probar el endpoint de login en el backend", f"curl -X POST http://localhost:3000/auth/login -d '{{...}}'"),
            _s("Instalar expo-secure-store para guardar el token", "npx expo install expo-secure-store"),
            _s("Implementar el AuthContext en src/contexts/AuthContext.tsx"),
            _s("Proteger las rutas con un guard de autenticación"),
            _s("Probar login y logout en el emulador"),
        ]))

    for module in modules[:4]:
        mod_lower = module.lower()
        phases.append(_p(
            f"Fase {len(phases)}: Módulo {module}",
            f"Implementa la pantalla y el hook de React Query para {module}.",
            [
                _s(f"Crear el hook useQuery para {module}", f"code src/hooks/use{module}.ts"),
                _s(f"Crear la pantalla de listado", f"code app/{mod_lower}.tsx"),
                _s(f"Crear la pantalla de detalle", f"code app/{mod_lower}/[id].tsx"),
                _s("Añadir FlatList con pull-to-refresh y estados de carga"),
                _s("Probar en el emulador o dispositivo real"),
            ]
        ))

    phases.append(_p(f"Fase {len(phases)}: Build y distribución con EAS", "Compila la app para las tiendas sin necesitar Mac.", [
        _s("Instalar EAS CLI", "npm install -g eas-cli && eas login"),
        _s("Inicializar el proyecto en EAS", "eas init"),
        _s("Configurar el perfil de build", "code eas.json"),
        _s("Build para Android en la nube", "eas build --platform android"),
        _s("Build para iOS en la nube (sin Mac)", "eas build --platform ios", "Requiere cuenta Apple Developer — EAS compila en servidores Mac"),
        _s("Publicar actualización OTA (sin nueva build)", "eas update --branch production"),
    ]))

    return phases


_ARCH_BUILDERS = {
    "DJANGO_REST":             _django_rest,
    "NEXTJS_APP":              _nextjs_app,
    "LARAVEL_MONOLITH":        lambda req: _laravel(req, has_frontend=False),
    "LARAVEL_INERTIA_REACT":   lambda req: _laravel(req, has_frontend=True),
    "LARAVEL_INERTIA_VUE":     lambda req: _laravel(req, has_frontend=True),
    "NESTJS_REACT":            _nestjs_react,
    "FASTAPI_AI":              _fastapi_ai,
    "REACT_EXPRESS":           _nestjs_react,      # close enough — both use npm/prisma
    # Mobile
    "FLUTTER_FASTAPI":         _flutter_fastapi,
    "REACT_NATIVE_NESTJS":     _react_native_nestjs,
    # Desktop
    "ELECTRON_NESTJS":         _electron_nestjs,
    "TAURI_FASTAPI":           _tauri_fastapi,
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
