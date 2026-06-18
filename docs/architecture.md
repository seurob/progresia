# Arquitectura Inicial

ProgresIA Studio se organiza como un monorepo con tres aplicaciones principales y paquetes compartidos.

## Aplicaciones

- `apps/web`: experiencia de usuario, formularios progresivos, revisión de especificaciones y descarga de artefactos.
- `apps/api`: API principal para autenticación, usuarios, workspaces, proyectos, jobs, permisos y artefactos.
- `apps/ai-service`: servicio especializado para agentes, RAG, generación de requisitos y OpenSpec.

## Servicios de infraestructura

- PostgreSQL para datos transaccionales.
- Redis para colas y jobs de larga duración.
- Qdrant para recuperación semántica.
- MinIO para almacenamiento de artefactos.

## Principio de diseño

El MVP se construye por fases. Primero se estabiliza el contrato entre servicios y después se incrementa la capacidad multiagente, la generación de código y la validación automática.
