# ProgresIA Studio

Tags: #progresia #openspec #tfm

## Estado

ProgresIA Studio es un monorepo con runtime modular:

- [[OpenSpec Workflow]]
- [[Roadmap]]
- [[Backlog]]
- [[Estado actual]]
- [[Architecture Decisions]]

## Enlaces clave

- OpenSpec base: `../../openspec/specs/progresia-studio/spec.md`
- Cambios: `../../openspec/changes`
- Issues locales: `../issues`
- ADRs: `../adr`

## Decisiones actuales

- El proyecto se gestiona como un MVP de producto unico.
- El repositorio es monorepo.
- El runtime no es un monolito estricto: web, API y AI service son procesos separados.
- La API NestJS puede evolucionar como modular monolith pragmatico.

## Proxima prioridad

Resolver deuda controlada de dependencias mayores y continuar con RAG Qdrant, ProductAgent y colaboracion.
