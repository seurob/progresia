import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import TaskType, get_llm
from app.schemas.tech_proposal import TechProposal, TechProposalRequest, TechProposalResponse

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a senior software architect proposing technology stacks for new software projects.

Given project context, generate exactly 3 concrete tech stack proposals — not abstract concepts.

Rules:
- Each proposal must name specific technologies with version numbers when relevant
- Tailor difficulty to the stated technical level
- For BEGINNER: prefer frameworks with fewer moving parts, strong documentation, single language
- For INTERMEDIATE: prefer modern architecture, TypeScript, containerization, production-ready
- Consider architecture_style: single (monolith), frontend_api (SPA+API), ai_service (SPA+API+AI microservice)
- Consider ai_needs: if not "none", include the appropriate AI integration libraries
- Consider deployment_target to include Docker, CI hints, etc.
- advantages: 3 specific, technical, honest advantages
- limitations: 2 real, honest limitations (no sugarcoating)
- learning_outcomes: 2-3 concrete skills the developer will gain
- recommended_id: 1, 2, or 3 (the best fit for THIS project)
- Respond in the same language as the project description (Spanish if the project seems Spanish)"""


def _build_human_message(req: TechProposalRequest) -> str:
    features = "\n".join(f"  - {f}" for f in req.core_features[:5]) if req.core_features else "  - (not specified)"
    return f"""Project: {req.name}
Sector: {req.sector}
Level: {req.level}
Product type: {req.product_type}
Main objective: {req.main_objective}
Preferred architecture: {req.architecture_style}
Data needs: {', '.join(req.data_needs) if req.data_needs else 'none specified'}
AI needs: {req.ai_needs}
Deployment target: {req.deployment_target}
Core features:
{features}"""


# ── Deterministic stack catalog ───────────────────────────────────────────────

_STACKS: dict[str, list[TechProposal]] = {
    # BEGINNER ─────────────────────────────────────────────────────────────────
    "BEGINNER_single": [
        TechProposal(
            id=1, name="Stack Clásico Full-stack", tagline="Laravel + MySQL + Tailwind CSS",
            stack=["PHP 8.3", "Laravel 11", "MySQL 8", "Tailwind CSS 3", "Alpine.js", "Blade"],
            difficulty="Principiante",
            description="Monolito Laravel con renderizado en servidor. Ideal si quieres que todo funcione desde el primer día sin configurar APIs separadas.",
            advantages=["Todo en un solo proyecto — frontend, backend y base de datos", "Laravel tiene las mejores guías para principiantes", "Despliegue en cualquier hosting PHP barato"],
            limitations=["Escala peor que una arquitectura desacoplada", "Alpine.js es suficiente para UI simple, pero no para SPAs complejas"],
            recommended_for="Primera aplicación web real con formularios, auth y CRUD",
            learning_outcomes=["Arquitectura MVC", "ORM con Eloquent", "Autenticación con Laravel Breeze"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=15,
        ),
        TechProposal(
            id=2, name="Stack JavaScript Unificado", tagline="Next.js + Prisma + PostgreSQL",
            stack=["TypeScript 5", "Next.js 14 (App Router)", "Prisma ORM", "PostgreSQL 16", "Tailwind CSS 3"],
            difficulty="Principiante",
            description="Next.js como frontend y backend a la vez. Un solo lenguaje (TypeScript) para todo, con Prisma para la base de datos.",
            advantages=["Un único lenguaje para todo — TypeScript en frontend y backend", "Excelente experiencia de desarrollo con hot-reload", "Deploy gratuito en Vercel con un clic"],
            limitations=["Los Server Components de App Router tienen una curva de aprendizaje inicial", "No es ideal si luego necesitas añadir un servicio de IA separado"],
            recommended_for="Desarrollador que ya sabe algo de JavaScript y quiere aprender TypeScript moderno",
            learning_outcomes=["TypeScript full-stack", "Server Components y API routes", "ORM tipado con Prisma"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=20,
        ),
        TechProposal(
            id=3, name="Stack Python Backend", tagline="Django + React + PostgreSQL",
            stack=["Python 3.12", "Django 5", "Django REST Framework", "React 18", "PostgreSQL 16", "Tailwind CSS"],
            difficulty="Principiante",
            description="Django maneja el backend con REST API automática, React el frontend. Python es más fácil de aprender y tiene el mejor ecosistema de IA.",
            advantages=["Django genera migraciones, panel admin y auth automáticamente", "Python es el lenguaje con más tutoriales y comunidad IA", "Fácil añadir IA más adelante con LangChain o FastAPI"],
            limitations=["Dos proyectos separados (Django + React) — más configuración inicial", "El panel admin de Django no es responsivo por defecto"],
            recommended_for="Si planeas añadir IA en el futuro o ya sabes algo de Python",
            learning_outcomes=["Django ORM y migraciones", "REST API con DRF", "Separación frontend/backend"],
            docker_ready=True, ai_ready=True, estimated_setup_minutes=25,
        ),
    ],
    "BEGINNER_frontend_api": [
        TechProposal(
            id=1, name="Stack React + Laravel API", tagline="React + Laravel API + MySQL",
            stack=["TypeScript 5", "React 18", "Vite 5", "Tailwind CSS 3", "PHP 8.3", "Laravel 11 (API)", "MySQL 8"],
            difficulty="Principiante",
            description="Frontend React moderno conectado a una API Laravel. Dos proyectos separados pero bien documentados.",
            advantages=["Laravel genera la API REST automáticamente con Sanctum para auth", "React es el framework frontend más demandado en el mercado", "MySQL tiene hosting gratuito en Railway y PlanetScale"],
            limitations=["Dos bases de código para mantener (React + Laravel)", "Configuración de CORS puede ser frustrante al principio"],
            recommended_for="Quieres aprender React moderno y tener una API robusta sin complejidad de Node.js",
            learning_outcomes=["React con hooks y TypeScript", "REST API stateless", "Autenticación JWT"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=30,
        ),
        TechProposal(
            id=2, name="Stack MERN Simplificado", tagline="React + Express.js + MongoDB",
            stack=["TypeScript 5", "React 18", "Vite 5", "Express.js 4", "Mongoose", "MongoDB", "Tailwind CSS 3"],
            difficulty="Principiante",
            description="El stack MERN clásico con TypeScript. Todo en JavaScript, esquema flexible con MongoDB, ideal para MVPs rápidos.",
            advantages=["Un solo lenguaje (JavaScript/TypeScript) en toda la aplicación", "MongoDB no requiere definir el esquema estrictamente al principio", "Millones de tutoriales disponibles para el stack MERN"],
            limitations=["MongoDB no es adecuado para datos muy relacionales", "Sin validaciones de tipo en la BD puede generar bugs difíciles de rastrear"],
            recommended_for="MVP rápido donde el esquema de datos puede cambiar frecuentemente",
            learning_outcomes=["API REST con Express", "Mongoose y modelado de documentos", "React con hooks"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=20,
        ),
        TechProposal(
            id=3, name="Stack Python API + React", tagline="FastAPI + React + PostgreSQL",
            stack=["Python 3.12", "FastAPI", "SQLAlchemy 2", "Alembic", "PostgreSQL 16", "TypeScript 5", "React 18", "Vite 5"],
            difficulty="Principiante",
            description="FastAPI genera documentación Swagger automática. Perfecto si quieres explorar Python o integrar IA más adelante.",
            advantages=["FastAPI es el framework Python más rápido y genera docs automáticas", "Python permite añadir LangChain o scikit-learn en cualquier momento", "PostgreSQL es el estándar de facto para aplicaciones serias"],
            limitations=["Dos lenguajes (Python + TypeScript) — más contexto para aprender", "Alembic para migraciones es más manual que Prisma o Eloquent"],
            recommended_for="Interesado en Python o en añadir funcionalidades de IA en el futuro",
            learning_outcomes=["FastAPI y pydantic para validación", "SQLAlchemy ORM", "React con TypeScript"],
            docker_ready=True, ai_ready=True, estimated_setup_minutes=30,
        ),
    ],
    # INTERMEDIATE ──────────────────────────────────────────────────────────────
    "INTERMEDIATE_frontend_api": [
        TechProposal(
            id=1, name="Stack Producción Estándar", tagline="React + NestJS + PostgreSQL + Docker",
            stack=["TypeScript 5", "React 19", "Vite 5", "NestJS 11", "Prisma ORM", "PostgreSQL 16", "Redis 7", "Docker Compose"],
            difficulty="Intermedio",
            description="La arquitectura de referencia para aplicaciones TypeScript de producción. NestJS impone estructura y escalabilidad desde el día 1.",
            advantages=["NestJS genera módulos, DTOs y validaciones automáticamente con CLI", "Prisma ofrece migraciones con type-safety y autocompletado en IDE", "Redis listo para caché, sesiones y BullMQ para jobs async"],
            limitations=["NestJS tiene mayor boilerplate que Express para proyectos pequeños", "Requiere dominar TypeScript decorators y DI — curva inicial"],
            recommended_for="MVP que debe evolucionar a producto real con múltiples devs",
            learning_outcomes=["Arquitectura por módulos con NestJS", "ORM type-safe con Prisma", "Cola de jobs async con BullMQ"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=25,
        ),
        TechProposal(
            id=2, name="Stack Next.js + tRPC", tagline="Next.js 14 + tRPC + Prisma + PostgreSQL",
            stack=["TypeScript 5", "Next.js 14 (App Router)", "tRPC v11", "Prisma ORM", "PostgreSQL 16", "NextAuth.js v5", "Tailwind CSS 4"],
            difficulty="Intermedio",
            description="Todo en Next.js con tRPC para API type-safe end-to-end. Cero boilerplate de REST, type errors detectados en compile-time.",
            advantages=["tRPC elimina la sincronización manual de tipos cliente-servidor", "NextAuth.js soporta OAuth, magic links, credenciales out of the box", "Deploy trivial en Vercel con edge functions y CDN global"],
            limitations=["Vendor lock-in con Vercel si no se configura self-hosting", "tRPC no genera una API REST consumible por mobile apps fácilmente"],
            recommended_for="Equipo TypeScript que prioriza velocidad de desarrollo sobre interoperabilidad",
            learning_outcomes=["Next.js App Router y RSC", "API type-safe con tRPC", "Auth moderna con NextAuth.js"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=20,
        ),
        TechProposal(
            id=3, name="Stack Microservicios Ligeros", tagline="React + NestJS + FastAPI + PostgreSQL",
            stack=["TypeScript 5", "React 19", "NestJS 11", "Python 3.12", "FastAPI", "PostgreSQL 16", "Redis 7", "Docker Compose"],
            difficulty="Intermedio",
            description="Frontend React + API NestJS + servicio de IA en FastAPI. La misma arquitectura que usa ProgresIA Studio.",
            advantages=["Separación limpia entre lógica de negocio (NestJS) e IA (FastAPI)", "Cada servicio escala de forma independiente", "Python accede a LangChain, transformers y todo el ecosistema ML"],
            limitations=["Tres proyectos que mantener — más overhead operacional", "Requiere Docker Compose para desarrollo local sin fricción"],
            recommended_for="Proyecto con componentes de IA significativos o que crecerá a startup",
            learning_outcomes=["Arquitectura multi-servicio", "Comunicación inter-servicio REST", "Integración de IA con LangChain"],
            docker_ready=True, ai_ready=True, estimated_setup_minutes=35,
        ),
    ],
    "INTERMEDIATE_ai_service": [
        TechProposal(
            id=1, name="Stack IA Estándar", tagline="React + NestJS + FastAPI + LangChain",
            stack=["TypeScript 5", "React 19", "NestJS 11", "Prisma ORM", "PostgreSQL 16", "Python 3.12", "FastAPI", "LangChain", "Redis 7", "Docker Compose"],
            difficulty="Intermedio",
            description="Arquitectura de tres capas con servicio de IA dedicado. NestJS orquesta los jobs, FastAPI ejecuta los agentes LangChain.",
            advantages=["LangChain tiene adaptadores para OpenAI, Groq, Gemini y Ollama", "FastAPI puede escalar el servicio de IA de forma independiente", "NestJS con BullMQ gestiona la cola de jobs async de forma robusta"],
            limitations=["Tres servicios que levantar en local (docker-compose recomendado)", "LangChain cambia la API frecuentemente — pin versiones"],
            recommended_for="Proyecto donde la IA es el componente central del negocio",
            learning_outcomes=["Agentes LangChain con fallbacks", "Colas async con BullMQ", "Arquitectura event-driven"],
            docker_ready=True, ai_ready=True, estimated_setup_minutes=40,
        ),
        TechProposal(
            id=2, name="Stack IA con RAG", tagline="React + FastAPI + LangChain + pgvector",
            stack=["TypeScript 5", "React 19", "Vite 5", "Python 3.12", "FastAPI", "LangChain", "SQLAlchemy 2", "PostgreSQL 16 + pgvector", "Docker Compose"],
            difficulty="Intermedio",
            description="FastAPI como backend único con extensión pgvector para búsqueda semántica. Ideal para chatbots, RAG y búsqueda inteligente.",
            advantages=["pgvector es más simple que mantener Qdrant o Chroma separados", "FastAPI + async es extremadamente rápido para streaming de LLM", "Un solo servicio Python para negocio + IA — menos complejidad"],
            limitations=["Python no tiene el mismo ecosistema de auth/permisos que NestJS", "pgvector en PostgreSQL escala peor que una BD vectorial dedicada para >1M docs"],
            recommended_for="RAG, chat con documentos, búsqueda semántica como funcionalidad principal",
            learning_outcomes=["Embeddings y búsqueda vectorial con pgvector", "Streaming de LLM con FastAPI", "Pipeline RAG con LangChain"],
            docker_ready=True, ai_ready=True, estimated_setup_minutes=30,
        ),
        TechProposal(
            id=3, name="Stack IA Multi-agente", tagline="React + NestJS + LangGraph + PostgreSQL",
            stack=["TypeScript 5", "React 19", "NestJS 11", "Python 3.12", "LangGraph", "LangChain", "PostgreSQL 16", "Redis 7", "Qdrant", "Docker Compose"],
            difficulty="Intermedio",
            description="LangGraph para orquestación de agentes especializados con estado persistente. Para proyectos donde varios agentes colaboran.",
            advantages=["LangGraph permite flujos de agentes con ramificación, ciclos y estado", "Qdrant escala a millones de vectores con búsqueda sublinear", "Arquitectura extensible — añadir un agente nuevo es trivial"],
            limitations=["LangGraph tiene curva de aprendizaje alta — entender grafos dirigidos", "Qdrant añade otro servicio a mantener en producción"],
            recommended_for="Plataformas con múltiples agentes de IA especializados trabajando en pipeline",
            learning_outcomes=["LangGraph y orquestación de agentes", "Búsqueda vectorial con Qdrant", "Diseño de pipelines multi-agente"],
            docker_ready=True, ai_ready=True, estimated_setup_minutes=45,
        ),
    ],
    "INTERMEDIATE_single": [
        TechProposal(
            id=1, name="Stack Django Moderno", tagline="Django 5 + HTMX + PostgreSQL + Tailwind",
            stack=["Python 3.12", "Django 5", "HTMX 2", "Alpine.js", "PostgreSQL 16", "Celery + Redis", "Tailwind CSS 3", "Docker Compose"],
            difficulty="Intermedio",
            description="Monolito Django con HTMX para interactividad sin JavaScript pesado. El stack más productivo para un desarrollador solo.",
            advantages=["HTMX añade interactividad sin escribir casi nada de JavaScript", "Django incluye auth, admin, ORM y migraciones — todo listo", "Un solo proyecto en Python — sin cambios de contexto de lenguaje"],
            limitations=["HTMX no es apto para SPAs muy complejas o juegos en tiempo real", "Difícil añadir una app móvil nativa después (necesitarías añadir REST API)"],
            recommended_for="Aplicación web clásica con formularios, admin y operaciones CRUD complejas",
            learning_outcomes=["Django ORM avanzado y señales", "HTMX y arquitectura hypermedia", "Celery para tareas asíncronas"],
            docker_ready=True, ai_ready=True, estimated_setup_minutes=20,
        ),
        TechProposal(
            id=2, name="Stack Laravel Avanzado", tagline="Laravel 11 + Livewire + PostgreSQL + Redis",
            stack=["PHP 8.3", "Laravel 11", "Livewire v3", "Alpine.js", "PostgreSQL 16", "Redis 7", "Laravel Horizon", "Tailwind CSS 3", "Docker Compose"],
            difficulty="Intermedio",
            description="Livewire v3 elimina la necesidad de React/Vue para la mayoría de casos. Componentes interactivos en PHP puro.",
            advantages=["Livewire v3 con Volt permite componentes full-stack en un solo archivo PHP", "Laravel Horizon para monitorizar queues en tiempo real", "Ecosistema maduro con Cashier (pagos), Socialite (OAuth), Scout (búsqueda)"],
            limitations=["El componente WebSocket/broadcasting requiere Pusher o Reverb extra", "Livewire no es adecuado si necesitas offline-first o PWA avanzada"],
            recommended_for="PHP developer que quiere modernizar su stack sin abandonar el ecosistema Laravel",
            learning_outcomes=["Livewire v3 y programación reactiva en PHP", "Queues y jobs con Horizon", "PostgreSQL avanzado con Laravel"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=20,
        ),
        TechProposal(
            id=3, name="Stack Ruby on Rails", tagline="Rails 7.2 + Hotwire + PostgreSQL",
            stack=["Ruby 3.3", "Rails 7.2", "Hotwire (Turbo + Stimulus)", "PostgreSQL 16", "Sidekiq", "Tailwind CSS 3", "Docker Compose"],
            difficulty="Intermedio",
            description="Rails sigue siendo el framework más productivo para monolitos. Convention over configuration extremo.",
            advantages=["Rails genera scaffold completo (model, migration, controller, views) en un comando", "Hotwire da interactividad sin JavaScript complejo — como HTMX pero más integrado", "Sidekiq con Redis es el estándar de jobs async en Ruby"],
            limitations=["Ruby tiene menos adopción que Python o JavaScript — menos ofertas de trabajo", "El ecosistema de IA en Ruby es muy limitado comparado con Python"],
            recommended_for="Developer que prioriza velocidad de entrega sobre adopción tecnológica en el mercado",
            learning_outcomes=["Convenciones Rails y Active Record", "Hotwire y arquitectura SPA sin JavaScript", "Sidekiq para procesamiento async"],
            docker_ready=True, ai_ready=False, estimated_setup_minutes=25,
        ),
    ],
}

_RECOMMENDATION_TEXTS: dict[str, str] = {
    "BEGINNER_single":        "Para tu nivel, recomendamos el **Stack Clásico (Laravel)**. Máximo aprendizaje con mínima frustración — todo en un proyecto, con la mejor documentación para principiantes.",
    "BEGINNER_frontend_api":  "Para tu nivel, recomendamos **React + Laravel API**. Laravel genera la API con comandos Artisan y React es el framework frontend más demandado en el mercado laboral.",
    "INTERMEDIATE_frontend_api": "Para un MVP productivo, recomendamos el **Stack Producción Estándar (React + NestJS)**. Arquitectura escalable, type-safety end-to-end y listo para Docker desde el primer commit.",
    "INTERMEDIATE_ai_service": "Para un proyecto centrado en IA, recomendamos el **Stack IA Estándar**. La separación NestJS/FastAPI es la arquitectura correcta cuando la IA es el corazón del negocio.",
    "INTERMEDIATE_single":    "Para máxima productividad individual, recomendamos **Django + HTMX**. Un solo lenguaje, sin frontend framework pesado, con el ecosistema IA de Python disponible.",
}

_ARCH_MAP: dict[str, str] = {
    "single":       "single",
    "modular":      "frontend_api",
    "frontend_api": "frontend_api",
    "ai_service":   "ai_service",
    "mobile_api":   "frontend_api",
    "desktop_api":  "frontend_api",
}


def _catalog_key(req: TechProposalRequest) -> str:
    normalized_arch = _ARCH_MAP.get(req.architecture_style, "frontend_api")
    needs_ai = req.ai_needs not in ("none", "recommendation", "")
    if needs_ai and req.level == "INTERMEDIATE":
        return "INTERMEDIATE_ai_service"
    return f"{req.level}_{normalized_arch}"


class TechProposalAgent:
    def propose(
        self,
        req: TechProposalRequest,
        llm: BaseChatModel | None = None,
        task: TaskType = "reasoning",
    ) -> TechProposalResponse:
        resolved_llm = llm if llm is not None else get_llm(task)

        if resolved_llm is not None:
            try:
                structured = resolved_llm.with_structured_output(TechProposalResponse)
                result = structured.invoke([
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=_build_human_message(req)),
                ])
                if isinstance(result, TechProposalResponse) and len(result.proposals) >= 2:
                    return result
            except Exception as exc:
                logger.warning("LLM tech proposal failed, using catalog fallback: %s", exc)

        return self._catalog_fallback(req)

    def _catalog_fallback(self, req: TechProposalRequest) -> TechProposalResponse:
        key = _catalog_key(req)
        proposals = _STACKS.get(key) or _STACKS["INTERMEDIATE_frontend_api"]
        reason = _RECOMMENDATION_TEXTS.get(key, _RECOMMENDATION_TEXTS["INTERMEDIATE_frontend_api"])
        return TechProposalResponse(
            proposals=proposals,
            recommended_id=1,
            recommendation_reason=reason,
        )
