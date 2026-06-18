Aquí tienes una versión más profesional, cerrada y optimizada del proyecto, planteada como MVP realista pero ambicioso a fecha 17/06/2026.

Título del TFM

ProgresIA Studio: plataforma multiagente para transformar ideas de negocio en MVPs software desplegables mediante IA, Spec Driven Development, RAG y DevOps

Descripción del proyecto

ProgresIA Studio es una plataforma web de desarrollo asistido por inteligencia artificial que permite a personas sin conocimientos técnicos transformar una idea de negocio en un MVP software funcional, documentado y desplegable.

El usuario introduce su idea mediante un formulario progresivo y conversa con un asistente virtual que le ayuda a concretar el problema, el público objetivo, las funcionalidades principales, el alcance del MVP y las necesidades técnicas del producto. A partir de esta información, la plataforma genera una especificación estructurada mediante Spec Driven Development con OpenSpec, donde se definen requisitos, historias de usuario, reglas de negocio, entidades, casos de uso, endpoints, criterios de aceptación y restricciones técnicas.

Sobre esta especificación, un sistema de agentes especializados genera el kit completo del proyecto: arquitectura técnica, modelo de datos, backend, frontend, autenticación, API, documentación, pruebas básicas, configuración Docker, variables de entorno, integración con GitHub, pipeline CI/CD, observabilidad, seguridad y despliegue inicial.

La plataforma combina React 19, Vite 8, TypeScript, Tailwind CSS 4, NestJS, PostgreSQL, Prisma, FastAPI, LangChain, LangGraph, Qdrant, Docker, GitHub Actions, Sentry, Playwright y buenas prácticas de desarrollo moderno. El resultado es un MVP ejecutable que puede levantarse localmente con Docker, revisarse técnicamente, subirse a un repositorio y desplegarse en un entorno cloud inicial.

ProgresIA Studio actúa como un estudio de desarrollo asistido por IA: convierte una idea poco definida en una primera versión funcional del producto, reduciendo la barrera de entrada para usuarios no programadores y proporcionando una base técnica ordenada, segura, documentada y preparada para evolucionar.

Concepto principal

ProgresIA Studio convierte una idea en un MVP real.

El flujo central sería:

Idea de negocio → formulario guiado → asistente IA → especificación OpenSpec → agentes técnicos → generación de código → Docker → GitHub → testing → despliegue inicial

No es solo documentación.
No es solo un chatbot.
No es solo un generador de código.

Es una plataforma que une:

producto,
requisitos,
SDD,
arquitectura,
generación fullstack,
RAG,
agentes IA,
Docker,
CI/CD,
seguridad,
testing,
observabilidad,
despliegue.

MVP que generaría la plataforma

El MVP generado por ProgresIA Studio debería incluir:

Aplicación frontend funcional.
Backend con API REST.
Base de datos PostgreSQL.
Autenticación con JWT.
Roles básicos.
CRUD principal adaptado a la idea.
Panel inicial de administración.
Validaciones de formularios.
Documentación OpenAPI/Swagger.
Dockerfile de frontend.
Dockerfile de backend.
docker-compose.yml.
.env.example.
Migraciones de base de datos.
Tests unitarios básicos.
Tests E2E básicos.
Pipeline GitHub Actions.
Integración inicial con Sentry.
README técnico.
Guía de instalación.
Guía de despliegue.
Exportación del dossier del proyecto.

Stack tecnológico recomendado
Frontend

React 19
Es una opción actual y sólida. La documentación oficial de React indica que la versión actual documentada es React 19.2, y React 19 incorporó mejoras importantes para acciones, formularios, estados pendientes y manejo de errores.

Vite 8
Muy adecuado para un generador de MVPs por rapidez, simplicidad y buen rendimiento. Vite 8 incorpora Rolldown como bundler unificado en Rust, con mejoras importantes de velocidad en builds.

TypeScript
Base obligatoria para mantener tipado, contratos y coherencia entre frontend, backend y generación IA.

Tailwind CSS 4
Buena opción para generar interfaces rápidas, consistentes y adaptables. Tailwind CSS 4 fue rediseñado con foco en rendimiento, flexibilidad y una nueva experiencia de configuración.

React Hook Form + Zod
Para formularios guiados, validación de datos, esquemas reutilizables y control de la información que alimenta a los agentes.

TanStack Query
Para gestión de llamadas API, caché, estados de carga y sincronización frontend-backend.

Backend principal

NestJS con TypeScript
Muy adecuado para este proyecto porque ofrece una estructura modular, escalable y profesional para aplicaciones server-side. La documentación oficial lo define como un framework para construir aplicaciones Node.js eficientes y escalables, con soporte completo para TypeScript.

PostgreSQL
Base de datos principal para usuarios, proyectos, especificaciones, agentes, tareas, logs y artefactos generados.

Prisma ORM
Para modelos, migraciones y acceso tipado a PostgreSQL. Prisma documenta su integración directa con PostgreSQL y la generación de Prisma Client para acceso type-safe a datos.

Swagger/OpenAPI
Para documentar automáticamente la API generada y usarla como contrato técnico entre frontend, backend y agentes.

JWT + RBAC
Autenticación y control de acceso basado en roles.

Redis + BullMQ
Para procesar tareas largas de generación: especificación, backend, frontend, Docker, tests, documentación, exportación ZIP y subida a GitHub.

Servicio de IA

FastAPI con Python
Servicio separado para la parte IA, RAG y agentes. Permite aislar la lógica de IA del backend principal y trabajar mejor con librerías Python.

LangChain
Para conexión con modelos, prompts, herramientas, recuperación documental y pipelines RAG.

LangGraph
Para orquestar agentes especializados. LangGraph está diseñado para construir, gestionar y desplegar agentes stateful y workflows largos, lo que encaja muy bien con un sistema que debe coordinar varios agentes técnicos.

Qdrant
Base vectorial para RAG. Qdrant se presenta como motor de búsqueda vectorial y semántica, útil para extraer información significativa de datos no estructurados.

OpenAI, Gemini u Ollama
El sistema puede trabajar con modelos externos o modelos locales. Para el MVP, la configuración más profesional sería permitir al administrador seleccionar proveedor de IA y modelo.

Arquitectura del sistema

La arquitectura del proyecto sería:

Frontend React.
Backend NestJS.
Servicio IA FastAPI.
PostgreSQL.
Qdrant.
Redis.
Docker Compose.
GitHub Actions.
Sentry.
Storage S3 o MinIO.

División de dominios:

Auth.
Users.
Workspaces.
Projects.
Ideas.
Specifications.
Agents.
Artifacts.
GeneratedCode.
Deployments.
Documents.
Reviews.
Billing or usage limits, si quieres controlar consumo.

Agentes del sistema
Agent Supervisor

Coordina el flujo completo y decide qué agente debe intervenir en cada fase.

Product Agent

Analiza la idea de negocio, usuario objetivo, problema, propuesta de valor y alcance del MVP.

Requirements Agent

Genera requisitos funcionales, no funcionales, historias de usuario y criterios de aceptación.

OpenSpec Agent

Transforma los requisitos en especificaciones SDD estructuradas con OpenSpec.

Architecture Agent

Define arquitectura, módulos, capas, dependencias, patrones, decisiones técnicas y estructura del repositorio.

Data Agent

Diseña entidades, relaciones, modelos Prisma, migraciones y datos iniciales.

Backend Agent

Genera módulos NestJS, controladores, servicios, DTOs, validaciones, autenticación, roles y endpoints.

Frontend Agent

Genera pantallas React, rutas, formularios, componentes, hooks, llamadas API y diseño base.

DevOps Agent

Genera Dockerfiles, docker-compose, variables de entorno, GitHub Actions y guía de despliegue.

Security Agent

Revisa autenticación, autorización, validación de inputs, secretos, CORS, rate limiting y OWASP Top 10.

Testing Agent

Genera pruebas unitarias, integración, E2E, coverage y quality gates.

Documentation Agent

Genera README, documentación técnica, manual de uso, arquitectura, endpoints, instalación y despliegue.

Roles de usuario
Admin

Gestiona usuarios, modelos IA, proveedores, límites de uso, logs, costes, configuración global y permisos.

Owner

Crea proyectos, responde formularios, conversa con el asistente, genera MVPs, revisa resultados, exporta documentación y despliega.

Collaborator

Participa en proyectos, revisa especificaciones, consulta el asistente, comenta artefactos y valida tareas.

Reviewer

Revisa arquitectura, seguridad, testing y documentación antes de aprobar la generación final.

Flujo funcional del MVP
1. Onboarding

El usuario se registra, crea un workspace y empieza un nuevo proyecto.

2. Formulario inteligente

La plataforma pregunta por:

nombre de la idea,
problema,
usuarios,
sector,
funcionalidades,
nivel de complejidad,
datos necesarios,
tipo de app,
integraciones,
prioridades,
restricciones.

3. Análisis de idea

El Product Agent genera:

resumen de la idea,
público objetivo,
propuesta de valor,
riesgos,
alcance del MVP,
funcionalidades principales,
funcionalidades futuras.

4. Especificación OpenSpec

El OpenSpec Agent genera:

requisitos,
casos de uso,
historias de usuario,
criterios de aceptación,
entidades,
reglas de negocio,
flujos principales,
contratos API,
restricciones técnicas.

OpenSpec encaja bien porque su enfoque consiste en fijar la intención antes de la implementación, evitando que los requisitos queden solo en el historial del chat.

5. Diseño técnico

El Architecture Agent y el Data Agent generan:

arquitectura,
estructura de carpetas,
modelo de datos,
diagrama de módulos,
endpoints,
decisiones técnicas,
migraciones iniciales.

6. Generación del MVP

Los agentes generan:

frontend,
backend,
API,
base de datos,
auth,
CRUD principal,
dashboard,
validaciones,
Docker,
tests,
documentación.

7. Validación

Security Agent y Testing Agent revisan:

errores básicos,
tests mínimos,
rutas protegidas,
variables ENV,
validación de inputs,
OWASP,
coverage inicial,
errores detectados por Sentry.

8. Entrega

El usuario recibe:

repositorio GitHub,
ZIP del proyecto,
README,
dossier técnico,
instrucciones Docker,
guía de despliegue,
URL de preview si está configurada.

Artefactos generados

La plataforma debería generar como mínimo:

README.md
architecture.md
requirements.md
openspec.yaml
openapi.yaml
database-schema.md
docker-compose.yml
.env.example
deployment-guide.md
security-checklist.md
testing-plan.md
project-roadmap.md
frontend/
backend/
prisma/schema.prisma
tests/
.github/workflows/ci.yml

Alcance ideal del MVP de ProgresIA Studio

El MVP de ProgresIA Studio debería permitir demostrar el ciclo completo con un caso real.

Por ejemplo:

Una persona introduce:

“Quiero una plataforma para gestionar reservas de clases particulares.”

La plataforma genera:

MVP definido,
usuarios y roles,
alumnos, profesores, clases y reservas,
base de datos PostgreSQL,
backend NestJS,
frontend React,
login,
CRUD de profesores,
CRUD de clases,
sistema básico de reservas,
Docker Compose,
documentación,
tests básicos,
GitHub Actions,
guía de despliegue.

Esto permite demostrar que el sistema realmente pasa de idea a software ejecutable.

Versión final corta para memoria del TFM

ProgresIA Studio es una plataforma multiagente de desarrollo asistido por IA que transforma ideas de negocio en MVPs software funcionales y desplegables. Está orientada a usuarios no técnicos que necesitan validar una idea digital sin partir de conocimientos de programación.

El sistema guía al usuario mediante un formulario inteligente y un asistente virtual, genera una especificación estructurada con OpenSpec, diseña la arquitectura, crea el modelo de datos, produce código frontend y backend, configura Docker, genera documentación, pruebas básicas, seguridad, observabilidad y un flujo inicial de despliegue.

La arquitectura combina React 19, Vite 8, TypeScript, Tailwind CSS 4, NestJS, PostgreSQL, Prisma, FastAPI, LangChain, LangGraph, Qdrant, Redis, Docker, GitHub Actions, Sentry y Playwright. El resultado es un kit completo de MVP que incluye repositorio, aplicación ejecutable, API, base de datos, documentación técnica y guía de despliegue.

Frase de defensa

ProgresIA Studio permite que una persona no técnica pase de una idea de negocio a un MVP software real, ejecutable y desplegable, mediante un flujo controlado de especificación, agentes IA, generación fullstack, testing, seguridad y DevOps.