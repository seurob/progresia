import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.schemas.architecture import (
    ArchitectureRecommendation,
    ArchitectureRequest,
    LearningResource,
    TechStackItem,
    UpgradeSignal,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Eres un arquitecto de software senior especializado en recomendar arquitecturas para proyectos web educativos y profesionales.

Tu misión es recomendar la arquitectura MÁS ADECUADA para el nivel técnico del usuario y el tipo de proyecto.

Devuelve un JSON con este esquema:
{
  "architecture_type": "LARAVEL_MONOLITH | LARAVEL_INERTIA_REACT | NEXTJS_APP | NESTJS_REACT | REACT_EXPRESS | FASTAPI_AI | DJANGO_REST",
  "name": "nombre legible de la arquitectura",
  "justification": "explicación clara y didáctica de por qué esta arquitectura es la más adecuada",
  "tech_stack": [
    {"name": "tecnología", "version": "versión", "purpose": "para qué sirve en este proyecto", "official_docs": "https://..."}
  ],
  "alternatives": ["alternativa 1 — cuándo usarla en lugar de la recomendada", "alternativa 2..."],
  "difficulty": "BEGINNER | INTERMEDIATE | ADVANCED",
  "risks": ["riesgo concreto del proyecto 1", "riesgo 2"],
  "first_steps": ["comando o acción concreta paso 1", "paso 2", ...],
  "educational_notes": ["concepto que el usuario debe entender sobre esta arquitectura", ...]
}

CRITERIOS POR NIVEL TÉCNICO (usar como guía principal):
- BEGINNER → priorizar LARAVEL_MONOLITH, NEXTJS_APP o REACT_EXPRESS (simple, bien documentado, curva baja)
- INTERMEDIATE → NEXTJS_APP o NESTJS_REACT (moderno, escalable, buenas prácticas)
- ADVANCED → NESTJS_REACT, FASTAPI_AI o arquitecturas desacopladas (máxima flexibilidad)

CRITERIOS POR TIPO DE PROYECTO:
- LARAVEL_MONOLITH: backends PHP, CRUD, APIs REST simples, teams PHP
- LARAVEL_INERTIA_REACT: fullstack PHP+React sin API separada (SPA unificada)
- NEXTJS_APP: apps con SEO, serverless, Vercel/Railway, TypeScript puro
- NESTJS_REACT: frontend+backend desacoplados, escalabilidad alta, TypeScript
- REACT_EXPRESS: proyectos Node.js simples, equipos JavaScript puros
- FASTAPI_AI: IA, RAG, LLMs, procesamiento de datos, Python
- DJANGO_REST: reservar para back-office pesado, CMS complejo, muchos modelos relacionales,
  permisos/workflows/reporting o preferencia explícita por Django/Python. No usarlo como opción web por defecto.

REGLA CRÍTICA: Si technical_level es BEGINNER, NO recomendar NESTJS_REACT ni FASTAPI_AI.
Si el proyecto tiene necesidades de IA, puede hacerse una excepción para FASTAPI_AI.

Responde ÚNICAMENTE con el JSON, sin markdown ni texto adicional."""


# ── Repeated URL / title constants ────────────────────────────────────────────

_URL_LARAVEL_DOCS  = "https://laravel.com/docs/11.x"
_URL_REACT_LEARN   = "https://react.dev/learn"
_URL_REACT_DOCS    = "https://react.dev/"
_URL_PG_DOCS       = "https://www.postgresql.org/docs/16/"
_URL_DOCKER_DOCS   = "https://docs.docker.com/"
_TITLE_REACT_QS    = "React oficial: Quick Start"
_PURPOSE_PG_MAIN   = "Base de datos relacional principal"
_PURPOSE_DOCKER    = "Contenerización del entorno completo"
_STEP_DOCKER_COMPOSE = "O directamente: `docker compose up --build` para levantar todo el stack"

# ── Curated tech stacks per architecture ──────────────────────────────────────

_STACKS: dict[str, list[TechStackItem]] = {
    "LARAVEL_MONOLITH": [
        TechStackItem(name="Laravel", version="11.x", purpose="Framework PHP backend MVC + API REST", official_docs=_URL_LARAVEL_DOCS),
        TechStackItem(name="PostgreSQL", version="16", purpose=_PURPOSE_PG_MAIN, official_docs=_URL_PG_DOCS),
        TechStackItem(name="Laravel Sanctum", version="4.x", purpose="Autenticación API con tokens Bearer", official_docs="https://laravel.com/docs/11.x/sanctum"),
        TechStackItem(name="Docker", version="26.x", purpose=_PURPOSE_DOCKER, official_docs=_URL_DOCKER_DOCS),
        TechStackItem(name="nginx", version="1.25", purpose="Proxy inverso y servidor de archivos estáticos", official_docs="https://nginx.org/en/docs/"),
    ],
    "LARAVEL_INERTIA_REACT": [
        TechStackItem(name="Laravel", version="11.x", purpose="Framework PHP backend + controladores Inertia", official_docs=_URL_LARAVEL_DOCS),
        TechStackItem(name="Inertia.js", version="2.x", purpose="Puente entre Laravel y React sin API REST", official_docs="https://inertiajs.com/"),
        TechStackItem(name="React", version="19.x", purpose="UI components para las vistas Inertia", official_docs=_URL_REACT_DOCS),
        TechStackItem(name="Vite", version="6.x", purpose="Bundler frontend integrado con Laravel Mix", official_docs="https://vitejs.dev/"),
        TechStackItem(name="PostgreSQL", version="16", purpose="Base de datos relacional", official_docs=_URL_PG_DOCS),
    ],
    "NEXTJS_APP": [
        TechStackItem(name="Next.js", version="15.x", purpose="Framework React con App Router, SSR y API routes", official_docs="https://nextjs.org/docs"),
        TechStackItem(name="TypeScript", version="5.x", purpose="Tipado estático en todo el proyecto", official_docs="https://www.typescriptlang.org/docs/"),
        TechStackItem(name="Prisma", version="6.x", purpose="ORM type-safe con migraciones", official_docs="https://www.prisma.io/docs"),
        TechStackItem(name="PostgreSQL", version="16", purpose=_PURPOSE_PG_MAIN, official_docs=_URL_PG_DOCS),
        TechStackItem(name="Tailwind CSS", version="4.x", purpose="Framework CSS utility-first", official_docs="https://tailwindcss.com/docs"),
        TechStackItem(name="NextAuth.js", version="5.x", purpose="Autenticación completa con múltiples providers", official_docs="https://authjs.dev/"),
        TechStackItem(name="Docker", version="26.x", purpose="Contenerización del entorno", official_docs=_URL_DOCKER_DOCS),
    ],
    "NESTJS_REACT": [
        TechStackItem(name="NestJS", version="11.x", purpose="Framework Node.js para APIs REST y microservicios", official_docs="https://docs.nestjs.com/"),
        TechStackItem(name="React", version="19.x", purpose="Biblioteca UI para el frontend SPA", official_docs=_URL_REACT_DOCS),
        TechStackItem(name="TypeScript", version="5.x", purpose="Tipado estático en frontend y backend", official_docs="https://www.typescriptlang.org/docs/"),
        TechStackItem(name="Prisma", version="6.x", purpose="ORM type-safe con migraciones", official_docs="https://www.prisma.io/docs"),
        TechStackItem(name="PostgreSQL", version="16", purpose=_PURPOSE_PG_MAIN, official_docs=_URL_PG_DOCS),
        TechStackItem(name="Docker", version="26.x", purpose=_PURPOSE_DOCKER, official_docs=_URL_DOCKER_DOCS),
    ],
    "FASTAPI_AI": [
        TechStackItem(name="FastAPI", version="0.115.x", purpose="Framework Python async para el microservicio IA", official_docs="https://fastapi.tiangolo.com/"),
        TechStackItem(name="LangChain", version="0.3.x", purpose="Integración con LLMs y cadenas de razonamiento", official_docs="https://python.langchain.com/docs/"),
        TechStackItem(name="LangGraph", version="0.5.x", purpose="Orquestación de agentes IA con grafos de estado", official_docs="https://langchain-ai.github.io/langgraph/"),
        TechStackItem(name="Qdrant", version="1.x", purpose="Base de datos vectorial para RAG y búsqueda semántica", official_docs="https://qdrant.tech/documentation/"),
        TechStackItem(name="PostgreSQL", version="16", purpose=_PURPOSE_PG_MAIN, official_docs=_URL_PG_DOCS),
        TechStackItem(name="React", version="19.x", purpose="Frontend SPA para consumir la API", official_docs=_URL_REACT_DOCS),
    ],
    "DJANGO_REST": [
        TechStackItem(name="Django", version="5.x", purpose="Framework web Python MVC con admin panel integrado", official_docs="https://docs.djangoproject.com/en/5.0/"),
        TechStackItem(name="Django REST Framework", version="3.x", purpose="Toolkit para construir APIs REST en Django", official_docs="https://www.django-rest-framework.org/"),
        TechStackItem(name="djangorestframework-simplejwt", version="5.x", purpose="Autenticación JWT para DRF", official_docs="https://django-rest-framework-simplejwt.readthedocs.io/"),
        TechStackItem(name="PostgreSQL", version="16", purpose=_PURPOSE_PG_MAIN, official_docs=_URL_PG_DOCS),
        TechStackItem(name="psycopg2", version="2.x", purpose="Driver PostgreSQL para Python", official_docs="https://www.psycopg.org/docs/"),
        TechStackItem(name="Docker", version="26.x", purpose=_PURPOSE_DOCKER, official_docs=_URL_DOCKER_DOCS),
    ],
    # ── Mobile ──────────────────────────────────────────────────────────────────
    "FLUTTER_FASTAPI": [
        TechStackItem(name="Flutter", version="3.24.x", purpose="Framework UI multiplataforma iOS/Android con Dart", official_docs="https://docs.flutter.dev/"),
        TechStackItem(name="Dart", version="3.5.x", purpose="Lenguaje compilado de Flutter — tipado fuerte, null-safe", official_docs="https://dart.dev/guides"),
        TechStackItem(name="FastAPI", version="0.115.x", purpose="API REST asíncrona para el backend de la app", official_docs="https://fastapi.tiangolo.com/"),
        TechStackItem(name="SQLModel", version="0.0.21", purpose="ORM Python con tipado Pydantic para PostgreSQL", official_docs="https://sqlmodel.tiangolo.com/"),
        TechStackItem(name="PostgreSQL", version="16", purpose=_PURPOSE_PG_MAIN, official_docs=_URL_PG_DOCS),
        TechStackItem(name="Docker", version="26.x", purpose="Contenerización del backend (API + DB)", official_docs=_URL_DOCKER_DOCS),
    ],
    "REACT_NATIVE_NESTJS": [
        TechStackItem(name="Expo", version="51.x", purpose="Framework React Native con build cloud — iOS/Android sin Xcode/Android Studio", official_docs="https://docs.expo.dev/"),
        TechStackItem(name="React Native", version="0.74.x", purpose="UI nativa iOS/Android con componentes React", official_docs="https://reactnative.dev/docs/getting-started"),
        TechStackItem(name="TypeScript", version="5.x", purpose="Tipado estático en frontend y backend", official_docs="https://www.typescriptlang.org/docs/"),
        TechStackItem(name="NestJS", version="11.x", purpose="API REST backend con módulos, guards y pipes", official_docs="https://docs.nestjs.com/"),
        TechStackItem(name="Prisma", version="6.x", purpose="ORM type-safe con migraciones automáticas", official_docs="https://www.prisma.io/docs"),
        TechStackItem(name="PostgreSQL", version="16", purpose=_PURPOSE_PG_MAIN, official_docs=_URL_PG_DOCS),
    ],
    # ── Desktop ─────────────────────────────────────────────────────────────────
    "TAURI_FASTAPI": [
        TechStackItem(name="Tauri", version="2.x", purpose="Framework desktop nativo (Rust + webview) con bundler multiplataforma", official_docs="https://v2.tauri.app/"),
        TechStackItem(name="React", version="19.x", purpose="UI frontend dentro del webview de Tauri", official_docs=_URL_REACT_DOCS),
        TechStackItem(name="TypeScript", version="5.x", purpose="Tipado estático para la UI y la capa IPC de Tauri", official_docs="https://www.typescriptlang.org/docs/"),
        TechStackItem(name="FastAPI", version="0.115.x", purpose="API REST para datos remotos / sincronización cloud", official_docs="https://fastapi.tiangolo.com/"),
        TechStackItem(name="SQLite", version="3.x", purpose="Base de datos local embebida en el instalable de escritorio", official_docs="https://www.sqlite.org/docs.html"),
        TechStackItem(name="PostgreSQL", version="16", purpose="Base de datos remota para sincronización cloud opcional", official_docs=_URL_PG_DOCS),
    ],
    "ELECTRON_NESTJS": [
        TechStackItem(name="Electron", version="31.x", purpose="Framework desktop cross-platform basado en Chromium + Node.js", official_docs="https://www.electronjs.org/docs/latest/"),
        TechStackItem(name="React", version="19.x", purpose="UI moderna dentro de la ventana Electron", official_docs=_URL_REACT_DOCS),
        TechStackItem(name="TypeScript", version="5.x", purpose="Tipado estático en main process y renderer", official_docs="https://www.typescriptlang.org/docs/"),
        TechStackItem(name="NestJS", version="11.x", purpose="API REST backend opcional para funcionalidades cloud", official_docs="https://docs.nestjs.com/"),
        TechStackItem(name="SQLite", version="3.x", purpose="Base de datos local embebida para persistencia offline", official_docs="https://www.sqlite.org/docs.html"),
    ],
}

_NOTES: dict[str, list[str]] = {
    "LARAVEL_INERTIA_REACT": [
        "Inertia.js elimina la necesidad de una API REST separada: los controladores de Laravel envían datos directamente a componentes React como props.",
        "Blade desaparece por completo: las vistas se convierten en componentes React (.tsx) que reciben los datos del servidor como props tipadas.",
        "Los formularios se envían con `router.post()` de Inertia: mismo comportamiento que un formulario Laravel, pero con validación reactiva en React sin escribir fetch().",
        "Vite está integrado con `laravel-vite-plugin`: cambios en los archivos React se reflejan instantáneamente con Hot Module Replacement.",
        "Sanctum gestiona la autenticación con cookies CSRF: más seguro que tokens Bearer cuando frontend y backend comparten dominio.",
    ],
    "LARAVEL_INERTIA_VUE": [
        "Inertia.js conecta los controladores de Laravel con componentes Vue 3 sin necesidad de API REST ni CORS.",
        "Las vistas Blade se reemplazan por Single File Components (.vue) que reciben los datos de Laravel como props reactivas.",
        "Vue 3 con Composition API y `<script setup>` ofrece TypeScript first-class en el frontend con muy poco boilerplate.",
        "Vite es el bundler nativo de Vue 3: `laravel-vite-plugin` integra ambos ecosistemas con recarga instantánea.",
        "Pinia es el gestor de estado recomendado para Vue 3: más simple que Vuex y con TypeScript completo.",
    ],
    "REACT_EXPRESS": [
        "Express.js es minimalista por diseño: no impone estructura, tú decides cómo organizar rutas, middleware y servicios.",
        "Los routers de Express se montan con `app.use('/api/recurso', router)`: cada recurso tiene su propio archivo de rutas.",
        "Prisma funciona con Express igual que con NestJS: define el schema, ejecuta `npx prisma migrate dev` y usa el cliente TypeScript generado.",
        "El ciclo de desarrollo es muy rápido: `tsx watch` o `ts-node-dev` recompila automáticamente al guardar.",
        "Para producción añade Helmet.js (cabeceras de seguridad) y express-rate-limit (protección de endpoints) desde el día 1.",
    ],
    "LARAVEL_MONOLITH": [
        "Laravel es el framework PHP más popular del mundo, con una curva de aprendizaje amigable para principiantes.",
        "Eloquent ORM abstrae las consultas SQL: defines modelos PHP y Laravel gestiona la base de datos.",
        "Artisan es la CLI de Laravel: `php artisan make:model`, `make:controller`, `make:migration` generan código automáticamente.",
        "Sanctum protege la API con tokens Bearer: cada usuario tiene un token que se envía en la cabecera Authorization.",
        "Las migraciones son archivos PHP que describen cambios en la base de datos, versionados en Git igual que el código.",
    ],
    "NEXTJS_APP": [
        "Next.js unifica frontend y backend en un solo proyecto: las API Routes en `src/app/api/` son funciones serverless.",
        "El App Router (carpeta `app/`) usa React Server Components por defecto: el HTML se genera en el servidor para mejor SEO.",
        "Prisma genera un cliente TypeScript type-safe: el IDE autocompletará todos los campos de tus modelos de base de datos.",
        "NextAuth.js gestiona sesiones, JWT y OAuth con muy poco código: soporta Google, GitHub, credenciales propias y más.",
        "`npx prisma studio` abre una interfaz web para explorar y editar la base de datos sin escribir SQL.",
    ],
    "NESTJS_REACT": [
        "NestJS usa decoradores (@Controller, @Get, @Post) similares a Spring Boot o Django, facilitando la transición desde otros frameworks.",
        "La separación frontend/backend permite escalar cada parte independientemente y trabajar en equipos paralelos.",
        "Swagger/OpenAPI se genera automáticamente desde los decoradores de NestJS: tu API queda documentada sin esfuerzo extra.",
        "BullMQ permite procesar tareas pesadas (emails, exportaciones, IA) de forma asíncrona sin bloquear las peticiones HTTP.",
        "Docker Compose levanta toda la infraestructura con un solo comando: `docker compose up --build`.",
    ],
    "FASTAPI_AI": [
        "FastAPI genera documentación interactiva en /docs (Swagger) y /redoc automáticamente desde las anotaciones Python.",
        "LangGraph modela flujos de agentes como un grafo de estados: cada nodo es una función, las aristas son transiciones condicionales.",
        "Qdrant almacena embeddings vectoriales para búsqueda semántica: puedes buscar documentos por significado, no solo por palabras clave.",
        "Los modelos LLM (Groq, OpenAI, Gemini) se intercambian configurando variables de entorno, sin cambiar el código.",
        "El patrón RAG (Retrieval-Augmented Generation) combina búsqueda vectorial con LLMs para respuestas precisas sobre tus propios datos.",
    ],
    "DJANGO_REST": [
        "Django ORM mapea clases Python a tablas SQL: defines `class Producto(models.Model)` y Django crea la tabla en PostgreSQL.",
        "Las migraciones de Django son archivos Python versionados en Git que describen cambios en el esquema de la base de datos.",
        "El admin panel en `/admin/` se genera automáticamente: registra un modelo con `@admin.register(Producto)` y tendrás CRUD sin código extra.",
        "DRF ViewSets generan todos los endpoints CRUD (list, create, retrieve, update, destroy) con muy pocas líneas de código.",
        "`python manage.py startapp nombre` crea la estructura completa de una aplicación Django: models, views, urls, admin, tests.",
    ],
    "FLUTTER_FASTAPI": [
        "Flutter compila a código nativo ARM: la app resultante tiene el mismo rendimiento que una app nativa de iOS o Android.",
        "Dart es el lenguaje de Flutter — tipado fuerte, null-safety y sintaxis similar a Java/Kotlin, con una curva de aprendizaje suave.",
        "Un único código base en Flutter genera apps para iOS y Android simultáneamente: menos coste de mantenimiento que dos apps nativas.",
        "Los `Widget` de Flutter son inmutables: el árbol de widgets se reconstruye eficientemente con el motor Skia/Impeller.",
        "FastAPI como backend mantiene la separación limpia: la app móvil consume la API REST con `http` o `dio` (cliente HTTP de Dart).",
    ],
    "REACT_NATIVE_NESTJS": [
        "Expo elimina la necesidad de Xcode/Android Studio para el desarrollo inicial: puedes probar en tu móvil real con Expo Go.",
        "React Native comparte el 90% del código entre iOS y Android, usando componentes nativos reales (no webview).",
        "TypeScript funciona igual en el frontend móvil (Expo) y el backend (NestJS): un único lenguaje en todo el stack.",
        "NestJS genera Swagger automáticamente desde los decoradores: documentación de la API siempre actualizada.",
        "Expo EAS Build compila el .ipa (iOS) y .apk (Android) en la nube sin hardware Apple — clave para desarrolladores Windows/Linux.",
    ],
    "TAURI_FASTAPI": [
        "Tauri usa el webview nativo del SO (WebKit en macOS/Linux, WebView2 en Windows): el instalable pesa ~5MB vs ~150MB de Electron.",
        "La lógica de Rust en Tauri es extremadamente eficiente y segura: no hay acceso al sistema desde el JavaScript sin aprobar comandos explícitamente.",
        "React en el webview de Tauri es idéntico a una SPA web: reutilizas todo el conocimiento de React.",
        "SQLite embebido permite que la app funcione completamente offline: los datos se sincronizan con PostgreSQL cuando hay conexión.",
        "FastAPI en el backend permite añadir funcionalidades cloud o colaboración en tiempo real manteniendo la app como cliente ligero.",
    ],
    "ELECTRON_NESTJS": [
        "Electron usa Node.js como main process y Chromium como renderer: puedes acceder al sistema de archivos desde JavaScript.",
        "La arquitectura de Electron separa el main process (Node.js, acceso al SO) del renderer process (React, UI).",
        "IPC (Inter-Process Communication) es el canal seguro entre main y renderer: `ipcMain.handle()` y `ipcRenderer.invoke()`.",
        "SQLite embebido con `better-sqlite3` permite persistencia local sin servidor externo — ideal para apps de escritorio offline.",
        "El empaquetador `electron-builder` genera instalables para Windows (.exe), macOS (.dmg) y Linux (.AppImage) desde un mismo código.",
    ],
}


def _r(title: str, url: str, rtype: str, level: str) -> LearningResource:
    return LearningResource(title=title, url=url, type=rtype, level=level)


def _u(signal: str, reason: str, next_step: str) -> UpgradeSignal:
    return UpgradeSignal(signal=signal, reason=reason, next_step=next_step)


_LEARNING_PATHS: dict[str, list[LearningResource]] = {
    "LARAVEL_MONOLITH": [
        _r("Laravel Bootcamp oficial", "https://bootcamp.laravel.com/", "course", "BEGINNER"),
        _r("Documentación oficial Laravel 11", _URL_LARAVEL_DOCS, "docs", "BEGINNER"),
        _r("Laracasts — Laravel desde cero", "https://laracasts.com/series/laravel-8-from-scratch", "video", "BEGINNER"),
        _r("Laravel Sanctum: API Token Auth", "https://laravel.com/docs/11.x/sanctum", "docs", "INTERMEDIATE"),
        _r("Eloquent ORM en profundidad", "https://laravel.com/docs/11.x/eloquent", "docs", "INTERMEDIATE"),
        _r("Testing en Laravel con PHPUnit", "https://laravel.com/docs/11.x/testing", "docs", "INTERMEDIATE"),
    ],
    "LARAVEL_INERTIA_REACT": [
        _r("Laravel Bootcamp oficial (con Inertia)", "https://bootcamp.laravel.com/", "course", "BEGINNER"),
        _r("Documentación Inertia.js", "https://inertiajs.com/", "docs", "INTERMEDIATE"),
        _r("Documentación Laravel 11", _URL_LARAVEL_DOCS, "docs", "BEGINNER"),
        _r(_TITLE_REACT_QS, _URL_REACT_LEARN, "docs", "BEGINNER"),
        _r("Vite + Laravel: configuración", "https://laravel.com/docs/11.x/vite", "docs", "INTERMEDIATE"),
    ],
    "NEXTJS_APP": [
        _r("Next.js Learn — tutorial oficial", "https://nextjs.org/learn", "course", "BEGINNER"),
        _r("Documentación Next.js App Router", "https://nextjs.org/docs/app", "docs", "BEGINNER"),
        _r("Prisma: primeros pasos", "https://www.prisma.io/docs/getting-started", "docs", "BEGINNER"),
        _r("Auth.js (NextAuth 5) — Getting Started", "https://authjs.dev/getting-started/installation", "docs", "INTERMEDIATE"),
        _r("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html", "docs", "INTERMEDIATE"),
        _r("Tailwind CSS — Tutorial de 20 minutos", "https://tailwindcss.com/docs/installation", "docs", "BEGINNER"),
        _r("«Full Stack Next.js» — Lee Robinson (Vercel)", "https://leerob.io/", "article", "ADVANCED"),
    ],
    "NESTJS_REACT": [
        _r("Documentación oficial NestJS", "https://docs.nestjs.com/", "docs", "BEGINNER"),
        _r(_TITLE_REACT_QS, _URL_REACT_LEARN, "docs", "BEGINNER"),
        _r("NestJS + Prisma — guía completa", "https://docs.nestjs.com/recipes/prisma", "docs", "INTERMEDIATE"),
        _r("NestJS + BullMQ — colas de trabajo", "https://docs.nestjs.com/techniques/queues", "docs", "INTERMEDIATE"),
        _r("«NestJS: The Complete Developer's Guide» (Udemy — Stephen Grider)", "https://www.udemy.com/course/nestjs-the-complete-developers-guide/", "course", "INTERMEDIATE"),
        _r("React Query: servidor-estado en el frontend", "https://tanstack.com/query/latest/docs/framework/react/overview", "docs", "INTERMEDIATE"),
        _r("Swagger/OpenAPI con NestJS", "https://docs.nestjs.com/openapi/introduction", "docs", "ADVANCED"),
    ],
    "FASTAPI_AI": [
        _r("FastAPI — Tutorial oficial", "https://fastapi.tiangolo.com/tutorial/", "docs", "BEGINNER"),
        _r("LangChain Python — Quickstart", "https://python.langchain.com/docs/get_started/quickstart", "docs", "INTERMEDIATE"),
        _r("LangGraph — Introduction", "https://langchain-ai.github.io/langgraph/tutorials/introduction/", "course", "INTERMEDIATE"),
        _r("«Designing Machine Learning Systems» — Chip Huyen", "https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/", "book", "ADVANCED"),
        _r("Qdrant — Getting Started", "https://qdrant.tech/documentation/quick-start/", "docs", "INTERMEDIATE"),
        _r("RAG desde cero con LangChain", "https://python.langchain.com/docs/tutorials/rag/", "docs", "INTERMEDIATE"),
        _r("OpenAI API Reference", "https://platform.openai.com/docs/api-reference", "docs", "BEGINNER"),
    ],
    "DJANGO_REST": [
        _r("Django Girls Tutorial", "https://tutorial.djangogirls.org/en/", "course", "BEGINNER"),
        _r("Documentación oficial Django 5", "https://docs.djangoproject.com/en/5.0/", "docs", "BEGINNER"),
        _r("Django REST Framework — Tutorial", "https://www.django-rest-framework.org/tutorial/quickstart/", "docs", "BEGINNER"),
        _r("«Two Scoops of Django 3.x» — Greenfield & Greenfield", "https://www.feldroy.com/books/two-scoops-of-django-3-x", "book", "INTERMEDIATE"),
        _r("djangorestframework-simplejwt — Docs", "https://django-rest-framework-simplejwt.readthedocs.io/", "docs", "INTERMEDIATE"),
        _r("Django Testing — guía oficial", "https://docs.djangoproject.com/en/5.0/topics/testing/", "docs", "INTERMEDIATE"),
    ],
    "REACT_EXPRESS": [
        _r(_TITLE_REACT_QS, _URL_REACT_LEARN, "docs", "BEGINNER"),
        _r("Express.js — Getting Started", "https://expressjs.com/en/starter/installing.html", "docs", "BEGINNER"),
        _r("Prisma + Express — guía", "https://www.prisma.io/express", "docs", "BEGINNER"),
        _r("Passport.js — Node.js auth", "https://www.passportjs.org/", "docs", "INTERMEDIATE"),
        _r("«Node.js Design Patterns» — Casciaro & Mammino", "https://www.nodejsdesignpatterns.com/", "book", "ADVANCED"),
    ],
    # ── Mobile ──────────────────────────────────────────────────────────────────
    "FLUTTER_FASTAPI": [
        _r("Flutter — Instalación y primeros pasos", "https://docs.flutter.dev/get-started/install", "docs", "BEGINNER"),
        _r("Tour del lenguaje Dart", "https://dart.dev/language", "docs", "BEGINNER"),
        _r("FastAPI — Tutorial oficial", "https://fastapi.tiangolo.com/tutorial/", "docs", "BEGINNER"),
        _r("Flutter — Cookbook (recetas prácticas)", "https://docs.flutter.dev/cookbook", "docs", "INTERMEDIATE"),
        _r("SQLModel — Quickstart", "https://sqlmodel.tiangolo.com/", "docs", "INTERMEDIATE"),
        _r("EAS Build — Expo Application Services", "https://docs.expo.dev/build/introduction/", "docs", "INTERMEDIATE"),
    ],
    "REACT_NATIVE_NESTJS": [
        _r("Expo — Getting Started", "https://docs.expo.dev/get-started/introduction/", "docs", "BEGINNER"),
        _r("React Native — Core Components", "https://reactnative.dev/docs/components-and-apis", "docs", "BEGINNER"),
        _r("Documentación oficial NestJS", "https://docs.nestjs.com/", "docs", "BEGINNER"),
        _r("Prisma — Primeros pasos", "https://www.prisma.io/docs/getting-started", "docs", "BEGINNER"),
        _r("EAS Build — compila sin Xcode/Android Studio", "https://docs.expo.dev/build/introduction/", "docs", "INTERMEDIATE"),
        _r("React Query (TanStack) para React Native", "https://tanstack.com/query/latest/docs/framework/react/overview", "docs", "INTERMEDIATE"),
    ],
    # ── Desktop ─────────────────────────────────────────────────────────────────
    "TAURI_FASTAPI": [
        _r("Tauri 2 — Guía de inicio", "https://v2.tauri.app/start/", "docs", "BEGINNER"),
        _r("The Rust Book (capítulos 1-6)", "https://doc.rust-lang.org/book/", "book", "INTERMEDIATE"),
        _r(_TITLE_REACT_QS, _URL_REACT_LEARN, "docs", "BEGINNER"),
        _r("FastAPI — Tutorial oficial", "https://fastapi.tiangolo.com/tutorial/", "docs", "BEGINNER"),
        _r("Tauri 2 — Commands y IPC", "https://v2.tauri.app/develop/calling-rust/", "docs", "INTERMEDIATE"),
        _r("Tauri 2 — Capabilities (permisos)", "https://v2.tauri.app/security/capabilities/", "docs", "INTERMEDIATE"),
    ],
    "ELECTRON_NESTJS": [
        _r("Electron — Tutorial oficial (proceso main + renderer)", "https://www.electronjs.org/docs/latest/tutorial/tutorial-first-app", "docs", "BEGINNER"),
        _r("electron-builder — empaquetado multiplataforma", "https://www.electron.build/", "docs", "INTERMEDIATE"),
        _r(_TITLE_REACT_QS, _URL_REACT_LEARN, "docs", "BEGINNER"),
        _r("Documentación oficial NestJS", "https://docs.nestjs.com/", "docs", "BEGINNER"),
        _r("better-sqlite3 — API docs", "https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md", "docs", "INTERMEDIATE"),
        _r("Electron — IPC entre main y renderer", "https://www.electronjs.org/docs/latest/tutorial/ipc", "docs", "INTERMEDIATE"),
    ],
}

_WHEN_TO_UPGRADE: dict[str, list[UpgradeSignal]] = {
    "LARAVEL_MONOLITH": [
        _u("El deploy tarda más de 10 minutos", "El monolito ha crecido y el pipeline CI/CD es lento", "Divide en paquetes Composer internos o considera Microservicios"),
        _u("Necesitas escalar solo una parte (ej. procesamiento de imágenes)", "El monolito escala todo o nada", "Extrae ese módulo a un microservicio Laravel o Python independiente"),
        _u("El equipo ha crecido a más de 6 personas trabajando en el mismo repositorio", "Los merge conflicts y los bloqueos de deploy se vuelven frecuentes", "Considera DDD dentro del monolito o transición a NestJS + React desacoplado"),
        _u("El frontend necesita interactividad compleja (dashboard en tiempo real, drag & drop)", "Blade es limitado para SPAs ricas", "Migra el frontend a React/Vue con Inertia o como SPA separada"),
    ],
    "NEXTJS_APP": [
        _u("La lógica de negocio en las API Routes supera las 500 líneas por ruta", "Las API Routes no están diseñadas para backends complejos", "Extrae el backend a NestJS y consúmelo desde Next.js"),
        _u("Necesitas WebSockets o procesamiento en tiempo real pesado", "Next.js no tiene soporte nativo robusto para WebSockets en el App Router", "Añade un servicio dedicado con Socket.io o usa un backend NestJS separado"),
        _u("El tiempo de build supera los 5 minutos", "El proyecto ha crecido y el bundler empieza a ser un cuello de botella", "Revisa el tree-shaking, evalúa Turbopack o separa en monorepo"),
        _u("Varios equipos trabajan en partes muy distintas del sistema", "Un solo repositorio Next.js mezcla responsabilidades de equipos diferentes", "Extrae en un monorepo con paquetes separados por dominio"),
    ],
    "NESTJS_REACT": [
        _u("Un módulo concreto recibe 10x más tráfico que el resto", "NestJS en un solo servicio escala todo junto", "Extrae ese módulo a un microservicio independiente con su propia base de datos"),
        _u("Necesitas equipos de 10+ personas en Backend y Frontend independientes", "La coordinación en un solo repositorio empieza a generar fricción", "Considera un monorepo con Nx, o repositorios separados con contratos OpenAPI"),
        _u("La latencia del API supera los 200ms bajo carga normal", "Un solo proceso Node.js puede ser el cuello de botella", "Añade Redis para caching, revisa queries N+1 de Prisma, o escala horizontalmente"),
    ],
    "FASTAPI_AI": [
        _u("El coste de los LLM supera el 40% del presupuesto de infraestructura", "Los LLMs en producción son caros si no se optimiza el uso", "Implementa caché semántica, reduce el tamaño de contexto, evalúa modelos locales (Ollama)"),
        _u("Las respuestas del agente son incoherentes con regularidad", "La arquitectura basada en prompts tiene límites de consistencia", "Añade evaluación automática (LangSmith, Weights & Biases) y fine-tuning"),
        _u("Necesitas procesar más de 1000 documentos en tiempo real", "RAG con Qdrant síncrono tiene límites de throughput", "Implementa un pipeline de indexación asíncrono con Celery o background workers"),
    ],
    "DJANGO_REST": [
        _u("El admin panel es usado por usuarios finales, no solo por el equipo interno", "El admin de Django no está diseñado como UI de producto", "Construye un frontend dedicado (Next.js, React) que consuma la DRF API"),
        _u("Necesitas múltiples endpoints en tiempo real o event-driven", "Django es síncrono; Channels añade complejidad significativa", "Evalúa FastAPI para los endpoints async o añade un servicio dedicado"),
        _u("El proyecto crece a más de 15 apps Django", "Sin una arquitectura de dominio clara, el código se mezcla entre apps", "Aplica DDD: reorganiza por bounded contexts, no por capas técnicas"),
    ],
    "REACT_EXPRESS": [
        _u("El backend supera los 3 routers de Express con lógica compleja", "Express no impone estructura; el código se vuelve difícil de mantener", "Migra a NestJS para obtener módulos, inyección de dependencias y Swagger"),
        _u("El equipo necesita onboardear a desarrolladores rápidamente", "Express tiene muy poca convención: cada proyecto organiza el código diferente", "Adopta un framework con más estructura (NestJS) o documenta arquitectura propia"),
        _u("Necesitas gestión de colas, workers o tareas programadas", "Express no tiene primitivas para trabajo asíncrono complejo", "Añade BullMQ o migra a NestJS que tiene integración nativa"),
    ],
    # ── Mobile ──────────────────────────────────────────────────────────────────
    "FLUTTER_FASTAPI": [
        _u("Necesitas una funcionalidad nativa no cubierta por plugins de Flutter", "Flutter depende de plugins de la comunidad para acceso a hardware específico", "Añade un plugin con platform channels para escribir código Kotlin/Swift nativo puntual"),
        _u("El rendimiento en pantallas con animaciones complejas es inaceptable", "Flutter/Skia puede tener drops en dispositivos muy antiguos con animaciones 3D", "Perfilar con DevTools; considerar Impeller renderer o reimplementar la pantalla con código nativo"),
        _u("El equipo crece y necesita separar iOS y Android con especialistas nativos", "Un único código base en Dart tiene límites cuando los requisitos de plataforma divergen mucho", "Evalúa React Native si el equipo tiene fuerte experiencia JavaScript, o apps nativas por plataforma"),
    ],
    "REACT_NATIVE_NESTJS": [
        _u("Los límites de builds de EAS afectan al ciclo de desarrollo del equipo", "El plan gratuito de EAS Build tiene cuota mensual de minutos de compilación", "Migra al plan de pago de EAS o configura build local con Xcode/Android Studio"),
        _u("Necesitas integración profunda con hardware nativo (Bluetooth BLE, NFC, ARKit)", "Algunos módulos nativos de React Native tienen soporte irregular en iOS/Android", "Implementa el módulo crítico en código nativo (Kotlin/Swift) y expo-modules para exponerlo"),
        _u("La API crece y NestJS genera demasiado boilerplate para endpoints simples", "NestJS está diseñado para APIs complejas; para APIs CRUD simples puede ser excesivo", "Evalúa Hono o Fastify + Prisma como backend más ligero si la complejidad de dominio es baja"),
    ],
    # ── Desktop ─────────────────────────────────────────────────────────────────
    "TAURI_FASTAPI": [
        _u("Los comandos Rust empiezan a superar las 1000 líneas en un solo archivo", "Rust tiene una curva empinada; un core grande se vuelve difícil de mantener sin experiencia", "Organiza en módulos Rust por dominio en src-tauri/src/; considera extraer lógica a una crate interna"),
        _u("Necesitas acceso a APIs nativas del SO no cubiertas por los plugins de Tauri", "Tauri 2 requiere declarar permisos explícitos; algunas APIs del SO aún no tienen plugin oficial", "Escribe un comando Rust personalizado usando las crates del ecosistema (winapi, cocoa, x11rb)"),
        _u("La app necesita colaboración en tiempo real entre usuarios remotos", "Tauri + SQLite es offline-first; la sincronización cloud requiere diseño cuidadoso de conflictos", "Implementa el backend FastAPI con WebSockets y un protocolo de sync tipo CRDT o event sourcing"),
    ],
    "ELECTRON_NESTJS": [
        _u("El tamaño del instalable supera los 200MB y los usuarios se quejan", "Electron incluye Chromium completo (~120MB base) más Node.js", "Evalúa Tauri como alternativa (~5MB); o usa ASAR packaging agresivo y tree-shaking para reducir el instalador"),
        _u("La app consume demasiada RAM en segundo plano (>500MB idle)", "Cada ventana Electron tiene su propio proceso Chromium — el consumo escala con ventanas abiertas", "Usa BrowserView en lugar de múltiples BrowserWindows; implementa lazy loading de renderer; considera Tauri para apps muy sensibles a memoria"),
        _u("La comunicación IPC entre main y renderer se vuelve compleja con muchos canales", "Sin un protocolo IPC claro, el código de comunicación main↔renderer se enreda rápido", "Define contratos IPC tipados con TypeScript; usa un bus de eventos centralizado en el preload; considera tRPC sobre IPC para type-safety completo"),
    ],
}


_MOBILE_DESKTOP_ARCH: dict[str, dict[str, str]] = {
    "mobile":  {"BEGINNER": "FLUTTER_FASTAPI",  "INTERMEDIATE": "REACT_NATIVE_NESTJS", "ADVANCED": "REACT_NATIVE_NESTJS"},
    "desktop": {"BEGINNER": "ELECTRON_NESTJS", "INTERMEDIATE": "TAURI_FASTAPI",        "ADVANCED": "TAURI_FASTAPI"},
}

# LLM is only prompted for web projects; restrict accepted types so a hallucinated
# mobile/desktop type cannot slip through the _STACKS guard.
_WEB_ARCH_TYPES = frozenset({
    "LARAVEL_MONOLITH", "LARAVEL_INERTIA_REACT", "LARAVEL_INERTIA_VUE",
    "NEXTJS_APP", "NESTJS_REACT", "REACT_EXPRESS", "FASTAPI_AI", "DJANGO_REST",
})

_STYLE_ARCH_HINTS: dict[str, str] = {
    "single": "NEXTJS_APP",
    "modular": "LARAVEL_MONOLITH",
    "frontend_api": "NESTJS_REACT",
    "ai_service": "FASTAPI_AI",
}

_DJANGO_HEAVY_TERMS = {
    "erp", "backoffice", "back-office", "cms", "reporting", "auditor",
    "workflow", "inventario", "contabilidad", "historial clínico",
    "multi-tenant", "permisos", "logística", "finanzas", "facturación",
}


def _django_is_justified(req: ArchitectureRequest) -> bool:
    preferred = req.preferred_stack.lower()
    if any(term in preferred for term in ("django", "drf", "python web")):
        return True
    if (req.technical_level or "INTERMEDIATE") == "BEGINNER":
        return False
    context = " ".join([req.sector, req.problem, *req.key_features]).lower()
    domain_signals = sum(term in context for term in _DJANGO_HEAVY_TERMS)
    structural_signals = int(len(req.key_features) >= 7) + int(req.needs_admin_panel)
    return domain_signals + structural_signals >= 3


class ArchitectureAgent:
    def recommend(self, req: ArchitectureRequest) -> ArchitectureRecommendation:
        # Mobile/desktop product types have curated stacks — skip LLM entirely.
        mobile_desktop_map = _MOBILE_DESKTOP_ARCH.get(req.product_type)
        if mobile_desktop_map:
            level = req.technical_level or "INTERMEDIATE"
            arch_type = mobile_desktop_map.get(level, mobile_desktop_map["INTERMEDIATE"])
            return self._build_recommendation(arch_type, req)

        llm = get_llm("general")
        if llm is not None:
            try:
                prompt = self._build_prompt(req)
                resp = llm.invoke([SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=prompt)])
                content = resp.content if hasattr(resp, "content") else str(resp)
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    arch_type = data.get("architecture_type", "")
                    if arch_type in _WEB_ARCH_TYPES and (
                        arch_type != "DJANGO_REST" or _django_is_justified(req)
                    ):
                        return ArchitectureRecommendation(
                            architecture_type=arch_type,
                            name=data.get("name", arch_type),
                            justification=data.get("justification", ""),
                            tech_stack=_STACKS.get(arch_type, []),
                            alternatives=data.get("alternatives", []),
                            difficulty=data.get("difficulty", "INTERMEDIATE"),
                            risks=data.get("risks", []),
                            first_steps=data.get("first_steps", []),
                            educational_notes=_NOTES.get(arch_type, []),
                            learning_path=_LEARNING_PATHS.get(arch_type, []),
                            when_to_upgrade=_WHEN_TO_UPGRADE.get(arch_type, []),
                        )
            except Exception as exc:
                logger.warning("Architecture LLM call failed, using rule-based: %s", exc)

        return self._rule_based(req)

    @staticmethod
    def _build_prompt(req: ArchitectureRequest) -> str:
        features = "\n".join(f"  - {f}" for f in req.key_features[:10])
        level = req.technical_level or "INTERMEDIATE"
        return (
            f"Proyecto: {req.project_name}\n"
            f"Sector: {req.sector}\n"
            f"Problema: {req.problem}\n"
            f"Usuarios objetivo: {req.target_users}\n"
            f"Funcionalidades:\n{features}\n"
            f"Necesita auth: {req.needs_auth}\n"
            f"Necesita panel admin: {req.needs_admin_panel}\n"
            f"Necesita IA: {req.needs_ai}\n"
            f"Nivel técnico del usuario: {level}\n"
            f"Estilo de arquitectura elegido: {req.architecture_style or 'sin preferencia'}\n"
            f"Necesidades de datos: {', '.join(req.data_needs) if req.data_needs else 'no especificadas'}\n"
            f"Tipo de IA preferida: {req.ai_needs or 'no especificada'}\n"
            f"Objetivo de despliegue: {req.deployment_target or 'no especificado'}\n"
            f"Stack preferido: {req.preferred_stack or 'ninguno especificado'}"
        )

    def _rule_based(self, req: ArchitectureRequest) -> ArchitectureRecommendation:
        preferred = req.preferred_stack.lower()
        level = req.technical_level or "INTERMEDIATE"

        mobile_desktop_map = _MOBILE_DESKTOP_ARCH.get(req.product_type)
        if mobile_desktop_map:
            arch_type = mobile_desktop_map.get(level, mobile_desktop_map["INTERMEDIATE"])
            return self._build_recommendation(arch_type, req)

        style_arch = _STYLE_ARCH_HINTS.get(req.architecture_style or "")

        if any(k in preferred for k in ["inertia vue", "laravel vue", "laravel inertia vue"]):
            arch_type = "LARAVEL_INERTIA_VUE"
        elif any(k in preferred for k in ["inertia react", "laravel react", "laravel inertia react", "inertia"]):
            arch_type = "LARAVEL_INERTIA_REACT"
        elif any(k in preferred for k in ["laravel", "php"]):
            arch_type = "LARAVEL_MONOLITH"
        elif any(k in preferred for k in ["nextjs", "next.js", "next js", "vercel"]):
            arch_type = "NEXTJS_APP"
        elif any(k in preferred for k in ["django", "drf", "python web"]):
            arch_type = "DJANGO_REST"
        elif any(k in preferred for k in ["express", "react express", "node simple"]):
            arch_type = "REACT_EXPRESS"
        elif style_arch == "FASTAPI_AI" and req.needs_ai:
            arch_type = "FASTAPI_AI"
        elif style_arch in _WEB_ARCH_TYPES and style_arch != "FASTAPI_AI":
            arch_type = style_arch
        elif req.needs_ai:
            arch_type = "FASTAPI_AI"
        elif level == "BEGINNER":
            arch_type = "LARAVEL_MONOLITH"
        elif len(req.key_features) <= 6 and not req.needs_admin_panel:
            arch_type = "NEXTJS_APP"
        else:
            arch_type = "NESTJS_REACT"

        return self._build_recommendation(arch_type, req)

    @staticmethod
    def _build_recommendation(arch_type: str, req: ArchitectureRequest) -> ArchitectureRecommendation:
        slug = req.project_name.lower().replace(" ", "-")
        configs: dict[str, dict] = {
            "LARAVEL_INERTIA_REACT": {
                "name": "Laravel + Inertia.js + React (Fullstack monorepo)",
                "justification": (
                    f"Para '{req.project_name}', Inertia.js conecta los controladores de Laravel con componentes React "
                    "sin necesidad de API REST ni CORS. Un único repositorio, un único deploy, y toda la potencia de "
                    "Laravel (Eloquent, Queue, Mail, Sanctum) con una UI React moderna."
                ),
                "alternatives": [
                    "Laravel Monolítico: si el frontend es simple y Blade es suficiente",
                    "NestJS + React: si necesitas frontend y backend completamente desacoplados y equipos separados",
                    "Next.js: si el SEO es prioritario y prefieres TypeScript en todo el stack",
                ],
                "difficulty": "BEGINNER",
                "risks": [
                    "Inertia limita la reutilización del backend: si necesitas una API pública para móvil o terceros, añade Sanctum API tokens",
                    "El ecosistema Inertia es más pequeño que Next.js o NestJS: menos recursos y menos ejemplos en internet",
                    "Mezcla PHP y JavaScript en el mismo repo: el equipo debe sentirse cómodo con ambos lenguajes",
                ],
                "first_steps": [
                    f"Crear proyecto: `composer create-project laravel/laravel {slug}`",
                    "Instalar Inertia server-side: `composer require inertiajs/inertia-laravel`",
                    "Instalar Inertia cliente + React: `npm install @inertiajs/react react react-dom`",
                    "Publicar configuración: `php artisan inertia:middleware`",
                    "Arrancar frontend: `npm run dev` + backend: `php artisan serve`",
                    _STEP_DOCKER_COMPOSE,
                ],
            },
            "LARAVEL_INERTIA_VUE": {
                "name": "Laravel + Inertia.js + Vue 3 (Fullstack monorepo)",
                "justification": (
                    f"Para '{req.project_name}', Laravel con Inertia.js y Vue 3 ofrece la misma ventaja de Inertia "
                    "(sin API REST) con el ecosistema Vue: Composition API, Pinia, y un tooling muy limpio. "
                    "Ideal si el equipo ya conoce Vue o prefiere su sintaxis de templates."
                ),
                "alternatives": [
                    "Laravel + Inertia + React: si el equipo prefiere React sobre Vue",
                    "Laravel Monolítico: si el frontend es simple y Blade es suficiente",
                    "Nuxt.js: si quieres SSR/SSG con Vue independiente del backend",
                ],
                "difficulty": "BEGINNER",
                "risks": [
                    "Vue 3 tiene una adopción más baja en el mercado laboral que React en España",
                    "Inertia no permite crear una API pública fácilmente sin refactoring",
                    "Mezcla PHP y JavaScript: el equipo debe dominar ambos ecosistemas",
                ],
                "first_steps": [
                    f"Crear proyecto: `composer create-project laravel/laravel {slug}`",
                    "Instalar Inertia server-side: `composer require inertiajs/inertia-laravel`",
                    "Instalar Inertia + Vue 3: `npm install @inertiajs/vue3 vue`",
                    "Configurar Vite para Vue: `npm install @vitejs/plugin-vue`",
                    "Arrancar: `npm run dev` + `php artisan serve`",
                    _STEP_DOCKER_COMPOSE,
                ],
            },
            "REACT_EXPRESS": {
                "name": "React + Express.js (Node.js fullstack simple)",
                "justification": (
                    f"Para '{req.project_name}', Express.js como backend ligero con React en el frontend es "
                    "la arquitectura Node.js más flexible. Ideal para proyectos pequeños, equipos JavaScript puros "
                    "o como base antes de migrar a NestJS cuando el proyecto crezca."
                ),
                "alternatives": [
                    "NestJS + React: evolución natural cuando el proyecto crece y necesitas más estructura y DI",
                    "Next.js: si prefieres un único proyecto con frontend y backend integrados en TypeScript",
                    "Laravel: si el equipo prefiere un framework con más convenciones y admin panel integrado",
                ],
                "difficulty": "BEGINNER",
                "risks": [
                    "Express sin framework impone muy poca estructura: el código puede volverse difícil de mantener con más de 2 devs",
                    "No hay inyección de dependencias ni módulos: el testing requiere más setup manual que NestJS",
                    "Escalar más allá de ~3 rutas por recurso suele requerir refactoring; considera NestJS desde el inicio para proyectos grandes",
                ],
                "first_steps": [
                    f"Crear directorio y package.json: `mkdir {slug} && cd {slug} && npm init -y`",
                    "Instalar dependencias: `npm install express cors dotenv && npm install -D typescript ts-node @types/node @types/express`",
                    "Inicializar Prisma: `npx prisma init --datasource-provider postgresql`",
                    "Crear el frontend: `npm create vite@latest web -- --template react-ts`",
                    "Configurar variables de entorno y arrancar: `ts-node src/index.ts`",
                ],
            },
            "LARAVEL_MONOLITH": {
                "name": "Laravel Monolítico (REST API)",
                "justification": (
                    f"Para '{req.project_name}' en el sector {req.sector}, Laravel 11 ofrece una arquitectura "
                    "MVC madura con Eloquent ORM, migraciones y un ecosistema completo. Ideal para equipos PHP "
                    "o proyectos que priorizan velocidad de desarrollo sobre escalabilidad extrema."
                ),
                "alternatives": [
                    "Laravel + Inertia + React: si quieres SPA moderna sin separar backend/frontend",
                    "Next.js: si el proyecto tiene componente de SEO importante o prefieres TypeScript",
                    "NestJS + React: si anticipas escalabilidad alta y equipos separados",
                ],
                "difficulty": "BEGINNER",
                "risks": [
                    "El monolito puede ser difícil de escalar horizontalmente cuando el tráfico crezca mucho",
                    "PHP requiere configuración de servidor diferente a Node.js; el equipo debe conocer el ecosistema",
                    "Si el proyecto necesita frontend muy interactivo, Blade puede limitar la experiencia de usuario",
                ],
                "first_steps": [
                    "Instalar PHP 8.3 y Composer: https://getcomposer.org/download/",
                    f"Crear proyecto: `composer create-project laravel/laravel {slug}`",
                    "Configurar .env con credenciales de PostgreSQL",
                    "Ejecutar migraciones: `php artisan migrate`",
                    "Iniciar servidor de desarrollo: `php artisan serve`",
                    _STEP_DOCKER_COMPOSE,
                ],
            },
            "NEXTJS_APP": {
                "name": "Next.js Full-stack (App Router)",
                "justification": (
                    f"Para '{req.project_name}', Next.js 15 con App Router unifica frontend y backend en un "
                    "solo proyecto TypeScript. Las API Routes son funciones serverless, Prisma gestiona la base "
                    "de datos, y el despliegue es trivial en Vercel o Railway. Excelente para proyectos con SEO."
                ),
                "alternatives": [
                    "NestJS + React: si el backend necesita ser un servicio independiente con lógica compleja",
                    "Laravel: si el equipo prefiere PHP y un framework MVC más tradicional",
                    "Remix: alternativa a Next.js con mejor manejo de formularios y carga de datos",
                ],
                "difficulty": "INTERMEDIATE",
                "risks": [
                    "El App Router tiene una curva de aprendizaje para entender Server vs Client Components",
                    "Las API Routes no son un backend completo: para lógica muy compleja considera NestJS separado",
                    "La caché de Next.js puede dar comportamientos inesperados si no se configura correctamente",
                ],
                "first_steps": [
                    f"Crear proyecto: `npx create-next-app@latest {slug} --typescript --tailwind --app`",
                    "Añadir Prisma: `npx prisma init --datasource-provider postgresql`",
                    "Definir el schema de Prisma y ejecutar: `npx prisma migrate dev`",
                    "Añadir NextAuth: `npm install next-auth`",
                    "Configurar variables de entorno en .env.local",
                    _STEP_DOCKER_COMPOSE,
                ],
            },
            "NESTJS_REACT": {
                "name": "NestJS + React (Fullstack desacoplado)",
                "justification": (
                    f"Para '{req.project_name}', NestJS proporciona un backend robusto y tipado con "
                    "decoradores, Swagger automático y módulos independientes. React en el frontend "
                    "permite equipos paralelos y escalado independiente. Esta es la arquitectura del propio ProgresIA Studio."
                ),
                "alternatives": [
                    "Next.js: si prefieres un solo proyecto con frontend y backend unificados",
                    "Express + React: opción más ligera si no necesitas la estructura de NestJS",
                    "Laravel + Inertia + React: si el equipo tiene background PHP",
                ],
                "difficulty": "INTERMEDIATE",
                "risks": [
                    "Mayor complejidad inicial: dos proyectos separados con configuraciones independientes",
                    "CORS y comunicación entre frontend y backend requieren configuración explícita",
                    "Más tiempo de setup inicial comparado con Next.js o Laravel",
                ],
                "first_steps": [
                    f"Crear el backend: `npx @nestjs/cli new {slug}-api`",
                    f"Crear el frontend: `npm create vite@latest {slug}-web -- --template react-ts`",
                    "Añadir Prisma al backend: `npm install prisma @prisma/client`",
                    "Configurar variables de entorno y CORS en NestJS",
                    "Arrancar ambos en modo desarrollo o usar Docker Compose",
                ],
            },
            "FASTAPI_AI": {
                "name": "FastAPI + Microservicio IA (RAG + Agentes)",
                "justification": (
                    f"Para '{req.project_name}' que necesita capacidades de IA, FastAPI como microservicio "
                    "especializado con LangChain/LangGraph proporciona la infraestructura para RAG, agentes "
                    "y procesamiento de lenguaje natural. Se conecta a cualquier backend principal."
                ),
                "alternatives": [
                    "NestJS + React + FastAPI: arquitectura completa con backend principal separado del microservicio IA",
                    "Next.js + API Routes de Python (via proxy): si quieres menos servicios",
                    "Genkit (Google): si el proyecto vive en el ecosistema Google Cloud y Firebase",
                ],
                "difficulty": "ADVANCED",
                "risks": [
                    "Alta complejidad operacional: múltiples servicios que deben comunicarse",
                    "Los LLMs tienen latencia y coste variable; requieren gestión de errores robusta",
                    "Qdrant y las bases de datos vectoriales tienen conceptos propios que requieren aprendizaje",
                ],
                "first_steps": [
                    "Crear el microservicio IA: `fastapi new ai-service` o usar uv/poetry",
                    "Instalar dependencias: `pip install langchain langgraph qdrant-client`",
                    "Configurar variables de entorno para las API keys de LLM (Groq, OpenAI, Gemini)",
                    "Implementar el primer endpoint `/generate` con LangChain",
                    "Conectar Qdrant para indexar documentos y hacer búsquedas semánticas",
                ],
            },
            "DJANGO_REST": {
                "name": "Django 5 + Django REST Framework",
                "justification": (
                    f"Para '{req.project_name}' en el sector {req.sector}, Django 5 ofrece el admin panel "
                    "más potente del ecosistema web y DRF convierte cualquier modelo en una API REST con mínimo código. "
                    "Ideal para equipos Python, proyectos con datos complejos o que necesitan un CMS integrado."
                ),
                "alternatives": [
                    "FastAPI: si necesitas mayor rendimiento async o construir específicamente un microservicio IA",
                    "Laravel: si el equipo prefiere PHP con una experiencia similar (MVC, ORM, migraciones, admin)",
                    "Next.js: si el frontend es la prioridad y el backend puede ser ligero con API Routes",
                ],
                "difficulty": "BEGINNER",
                "risks": [
                    "Django es síncrono por defecto; para websockets o tareas async se necesita Django Channels o Celery",
                    "El ORM de Django puede generar consultas N+1 si no se usa select_related/prefetch_related correctamente",
                    "El admin panel no está pensado como UI de producción para usuarios finales, solo para administradores",
                ],
                "first_steps": [
                    "Instalar Python 3.12 y crear entorno virtual: `python -m venv venv && source venv/bin/activate`",
                    "Instalar Django y DRF: `pip install django djangorestframework djangorestframework-simplejwt psycopg2-binary`",
                    "Crear proyecto Django: `django-admin startproject config .`",
                    "Aplicar migraciones iniciales: `python manage.py migrate`",
                    "Crear superusuario para el admin: `python manage.py createsuperuser`",
                    _STEP_DOCKER_COMPOSE,
                ],
            },
            "FLUTTER_FASTAPI": {
                "name": "Flutter 3 + FastAPI (App Móvil + API REST)",
                "justification": (
                    f"Para '{req.project_name}', Flutter genera apps nativas para iOS y Android desde un único código base en Dart. "
                    "FastAPI proporciona el backend REST asíncrono con tipado automático y documentación Swagger. "
                    "Es el stack mobile más productivo para un desarrollador solo o un equipo pequeño sin experiencia nativa específica."
                ),
                "alternatives": [
                    "React Native + Expo + NestJS: si el equipo viene de JavaScript/TypeScript y quiere reutilizar ese conocimiento",
                    "Flutter + NestJS: si prefieres NestJS (Node.js/TypeScript) sobre Python en el backend",
                    "Kotlin Multiplatform: si la experiencia Android nativa es prioritaria y se acepta mayor complejidad",
                ],
                "difficulty": "INTERMEDIATE",
                "risks": [
                    "Dart es un lenguaje nuevo para la mayoría: curva inicial de aprendizaje antes de ser productivo",
                    "Flutter no tiene acceso total a las APIs nativas del SO sin plugins; algunos casos edge requieren código Kotlin/Swift",
                    "FastAPI en producción requiere gestión de workers (uvicorn + gunicorn) y Docker bien configurado",
                ],
                "first_steps": [
                    "Instalar Flutter SDK: https://docs.flutter.dev/get-started/install",
                    f"Crear proyecto Flutter: `flutter create {slug}_mobile`",
                    "Añadir dependencia HTTP: `flutter pub add dio` (cliente HTTP para Dart)",
                    "Crear API FastAPI: `pip install fastapi uvicorn sqlmodel psycopg2-binary`",
                    "Crear `docker-compose.yml` con los servicios: api (FastAPI) + db (PostgreSQL)",
                    "Conectar la app al backend en `lib/services/api_client.dart`",
                ],
            },
            "REACT_NATIVE_NESTJS": {
                "name": "React Native (Expo) + NestJS (App Móvil + API REST)",
                "justification": (
                    f"Para '{req.project_name}', Expo SDK permite desarrollar para iOS y Android con React y TypeScript "
                    "— el mismo lenguaje del backend NestJS. Expo EAS Build compila en la nube, sin necesitar Mac ni Android Studio. "
                    "Es el stack mobile más accesible para equipos con experiencia en el ecosistema JavaScript/TypeScript."
                ),
                "alternatives": [
                    "Flutter + FastAPI: si la máxima performance nativa es prioritaria y el equipo acepta aprender Dart",
                    "Next.js PWA: si no necesitas acceso a funciones nativas del móvil (cámara, GPS, notificaciones push)",
                    "Expo + FastAPI: si el backend Python es preferible a TypeScript",
                ],
                "difficulty": "INTERMEDIATE",
                "risks": [
                    "El ecosistema Expo está muy activo pero algunos plugins de terceros tienen soporte irregular en iOS/Android",
                    "EAS Build tiene límites de minutos en el plan gratuito: necesitarás el plan de pago para builds frecuentes",
                    "NestJS tiene más boilerplate que Express; para una API simple puede ser sobredimensionado",
                ],
                "first_steps": [
                    "Instalar Expo CLI: `npm install -g expo-cli`",
                    f"Crear app: `npx create-expo-app {slug}-mobile --template blank-typescript`",
                    "Crear API NestJS: `npx @nestjs/cli new {slug}-api`",
                    "Instalar Prisma en la API: `npm install prisma @prisma/client` + `npx prisma init`",
                    "Crear `docker-compose.yml` para el backend (NestJS + PostgreSQL + Redis)",
                    "Conectar la app al backend con `axios` o `@tanstack/react-query`",
                ],
            },
            "TAURI_FASTAPI": {
                "name": "Tauri 2 + FastAPI (App Escritorio + API REST)",
                "justification": (
                    f"Para '{req.project_name}', Tauri genera instalables nativos para Windows, macOS y Linux "
                    "con un instalable de ~5MB. FastAPI proporciona el backend cloud. "
                    "Es la opción más moderna para apps de escritorio: Rust para la capa de sistema, React para la UI."
                ),
                "alternatives": [
                    "Electron + NestJS: si el equipo prefiere JavaScript puro y acepta un instalable más grande",
                    "Next.js (Electron): si la app web y la de escritorio deben ser la misma base de código",
                    "PyInstaller + Tkinter: si el equipo es Python-only y la UI puede ser básica",
                ],
                "difficulty": "INTERMEDIATE",
                "risks": [
                    "Tauri requiere Rust instalado: el entorno de desarrollo es más complejo de configurar",
                    "Algunos módulos npm del ecosistema web no funcionan en Tauri sin adaptación",
                    "El debugging entre el renderer (React) y el main process (Rust) tiene herramientas más limitadas que Electron",
                ],
                "first_steps": [
                    "Instalar Rust: https://rustup.rs/",
                    f"Crear proyecto Tauri + React: `npm create tauri-app@latest {slug}`",
                    "Crear API FastAPI: `pip install fastapi uvicorn sqlmodel`",
                    "Configurar `tauri.conf.json` con los permisos necesarios (filesystem, HTTP, shell)",
                    "Desarrollar los comandos Tauri en `src-tauri/src/lib.rs` para operaciones de sistema",
                ],
            },
            "ELECTRON_NESTJS": {
                "name": "Electron 31 + NestJS (App Escritorio + API REST)",
                "justification": (
                    f"Para '{req.project_name}', Electron permite crear apps de escritorio cross-platform "
                    "con React y TypeScript. NestJS proporciona el backend cloud. "
                    "Es el stack más probado para apps de escritorio: VS Code, Slack y Figma están construidos con Electron."
                ),
                "alternatives": [
                    "Tauri + FastAPI: si el tamaño del instalable es crítico y el equipo acepta Rust",
                    "Electron + Express: si NestJS es sobredimensionado y la API puede ser más simple",
                    "PWA + NestJS: si no se necesita acceso al sistema de archivos y la app puede funcionar en el navegador",
                ],
                "difficulty": "BEGINNER",
                "risks": [
                    "Los instalables de Electron pesan ~120-200MB por incluir Chromium completo",
                    "La gestión del IPC entre main y renderer puede volverse compleja en apps grandes",
                    "Las actualizaciones automáticas requieren configurar `electron-updater` y un servidor de distribución",
                ],
                "first_steps": [
                    f"Crear proyecto Electron + React: `npx create-electron-app@latest {slug} --template=webpack-typescript`",
                    "Instalar dependencias adicionales: `npm install electron-store better-sqlite3`",
                    "Crear API NestJS: `npx @nestjs/cli new {slug}-api`",
                    "Configurar el IPC en `src/main/index.ts` para los canales main↔renderer",
                    "Configurar `electron-builder` en `package.json` para compilar instalables",
                ],
            },
        }

        cfg = configs.get(arch_type, configs["NESTJS_REACT"])
        return ArchitectureRecommendation(
            architecture_type=arch_type,
            name=cfg["name"],
            justification=cfg["justification"],
            tech_stack=_STACKS.get(arch_type, _STACKS["NESTJS_REACT"]),
            alternatives=cfg["alternatives"],
            difficulty=cfg["difficulty"],
            risks=cfg["risks"],
            first_steps=cfg["first_steps"],
            educational_notes=_NOTES.get(arch_type, _NOTES.get("NESTJS_REACT", [])),
            learning_path=_LEARNING_PATHS.get(arch_type, []),
            when_to_upgrade=_WHEN_TO_UPGRADE.get(arch_type, []),
        )
