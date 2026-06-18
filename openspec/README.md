# OpenSpec de ProgresIA Studio

Esta carpeta es la fuente de verdad funcional y tecnica del proyecto. Antes de implementar una fase relevante, se debe crear o actualizar una propuesta en `openspec/changes/` y reflejar el contrato resultante en `openspec/specs/`.

## Flujo de trabajo

1. Crear un cambio en `openspec/changes/<id>/`.
2. Definir la intencion en `proposal.md`.
3. Definir decisiones tecnicas en `design.md`.
4. Desglosar trabajo verificable en `tasks.md`.
5. Actualizar o crear specs en `openspec/changes/<id>/specs/`.
6. Al cerrar el cambio, consolidar la capacidad en `openspec/specs/`.

## Convenciones

- Los requisitos normativos usan `MUST`, `SHOULD` y `MAY`.
- Cada requisito relevante incluye al menos un `Scenario`.
- Las decisiones de arquitectura se escriben antes de tocar codigo productivo.
- Las tareas deben ser comprobables con comandos o endpoints concretos.

## Validacion local

```bash
npm run openspec:check
```

Este comando comprueba que la estructura minima de OpenSpec existe y que cada cambio tiene propuesta, diseno, tareas y al menos una spec modificada.
