"""Entity helper functions for fallback scaffold generators."""
import re

from app.schemas.codegen import CodeGenerationRequest

_TECHNICAL_MODULES = {"auth", "authentication", "admin", "security"}


def slug(name: str) -> str:
    """Convierte un nombre a kebab-case."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def pascal(name: str) -> str:
    """Convierte un nombre a PascalCase."""
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name.strip())
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[\s\-_]+", separated) if w)


def camel(name: str) -> str:
    """Convierte un nombre a camelCase."""
    p = pascal(name)
    return p[0].lower() + p[1:] if p else name


def entity_fields_summary(entity: dict) -> str:
    """Genera un resumen de los campos de una entidad para mensajes de LLM."""
    fields = entity.get("fields", [])[:6]
    rels = entity.get("relations", [])[:3]
    fields_str = " | ".join(fields) if fields else "id, name"
    rel_str = f" — {', '.join(rels)}" if rels else ""
    return f"  - {entity.get('name', '?')}: [{fields_str}]{rel_str}"


def get_primary_entity(req: CodeGenerationRequest) -> dict:
    """Return the first business entity, avoiding infrastructure-only modules."""
    if req.data_entities:
        return next(
            (
                entity
                for entity in req.data_entities
                if slug(entity.get("name", "")) not in _TECHNICAL_MODULES
            ),
            req.data_entities[0],
        )

    name = next(
        (module for module in req.modules if slug(module) not in _TECHNICAL_MODULES),
        "Item",
    )
    return {
        "name": name,
        "fields": ["id: UUID PK", "name: VARCHAR NOT NULL", "description: TEXT", "status: VARCHAR", "createdAt: TIMESTAMP", "updatedAt: TIMESTAMP"],
        "relations": [],
    }


def get_entity_name(entity: dict) -> str:
    """Obtiene el nombre de la entidad."""
    return entity.get("name", "Item")


def get_entity_slug(entity: dict) -> str:
    """Obtiene el slug de la entidad."""
    return slug(get_entity_name(entity))


def get_entity_pascal(entity: dict) -> str:
    """Obtiene el nombre en PascalCase de la entidad."""
    return pascal(get_entity_name(entity))


def get_entity_camel(entity: dict) -> str:
    """Obtiene el nombre en camelCase de la entidad."""
    return camel(get_entity_name(entity))


def pluralize(name: str) -> str:
    """Pluraliza un nombre simple en inglés/español."""
    name_lower = name.lower()
    if name_lower.endswith("s") and not name_lower.endswith(("ss", "us")):
        return name
    if name_lower.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    if name_lower.endswith("y") and len(name) > 1 and name_lower[-2] not in "aeiou":
        return name[:-1] + "ies"
    return name + "s"
