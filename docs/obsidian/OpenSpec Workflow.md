# OpenSpec Workflow

Tags: #openspec #workflow

## Regla

Toda capacidad relevante empieza con un cambio en `openspec/changes/`.

## Flujo

1. Crear `proposal.md`.
2. Crear `design.md`.
3. Crear `tasks.md`.
4. Crear delta en `specs/progresia-studio/spec.md`.
5. Implementar.
6. Validar.
7. Crear o actualizar issue GitHub asociado.

## Quality gates

```bash
npm run openspec:check
npm run lint
npm run typecheck
npm run test
npm run build
```

## Cambios activos

- `0001-initialize-platform`
- `0002-api-foundation`
- `0003-web-foundation`
