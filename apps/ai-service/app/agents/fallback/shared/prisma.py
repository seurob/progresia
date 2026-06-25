"""Prisma schema generation helpers for fallback scaffold generators."""
import re

from app.schemas.codegen import GeneratedFile
from app.agents.fallback.shared.entities import pascal, camel, pluralize, slug


def sql_type_to_prisma(type_str: str) -> str:
    """Convierte un tipo SQL a un tipo Prisma."""
    t = type_str.upper()
    if "BOOL" in t:
        return "Boolean"
    if "BIGINT" in t:
        return "BigInt"
    if "INT" in t:
        return "Int"
    if "DECIMAL" in t or "NUMERIC" in t or "MONEY" in t:
        return "Decimal"
    if "FLOAT" in t or "REAL" in t or "DOUBLE" in t:
        return "Float"
    if "TIMESTAMP" in t or "DATE" in t or "TIME" in t:
        return "DateTime"
    if "JSON" in t:
        return "Json"
    if "UUID" in t:
        return "String"
    return "String"


def entity_to_prisma_model(
    entity: dict,
    table_to_model: dict[str, str],
    reverse_relations: list[str] | None = None,
    relation_names: dict[str, str] | None = None,
) -> str:
    """Convert a SQL-like OpenSpec entity into a production-oriented Prisma model."""
    pascal_name = pascal(entity.get("name", "Entity"))
    raw_fields = entity.get("fields", [])
    lines = []
    relation_lines: list[str] = []
    index_fields: list[str] = []
    has_id = False

    for field_str in raw_fields[:20]:
        colon_idx = field_str.find(":")
        if colon_idx == -1:
            continue
        raw_field_name = field_str[:colon_idx].strip()
        field_name = camel(raw_field_name)
        rest = field_str[colon_idx + 1:].strip()
        rest_upper = rest.upper()

        prisma_type = sql_type_to_prisma(rest_upper)
        decorators = []
        is_pk = "PRIMARY KEY" in rest_upper or re.search(r"\bPK\b", rest_upper) is not None
        is_unique = "UNIQUE" in rest_upper
        is_nullable = "NOT NULL" not in rest_upper and not is_pk

        if is_pk:
            has_id = True
            decorators.append("@id @default(uuid())")
        elif is_unique:
            decorators.append("@unique")

        if "UUID" in rest_upper:
            decorators.append("@db.Uuid")

        name_lower = raw_field_name.lower()
        if name_lower in ("createdat", "created_at"):
            decorators.append("@default(now())")
        elif name_lower in ("updatedat", "updated_at"):
            decorators.append("@updatedAt")
        elif match := re.search(r"DEFAULT\s+'([^']+)'", rest, re.IGNORECASE):
            decorators.append(f'@default("{match.group(1)}")')
        elif re.search(r"DEFAULT\s+TRUE", rest, re.IGNORECASE):
            decorators.append("@default(true)")
        elif re.search(r"DEFAULT\s+FALSE", rest, re.IGNORECASE):
            decorators.append("@default(false)")
        elif match := re.search(r"DEFAULT\s+(\d+)", rest, re.IGNORECASE):
            decorators.append(f"@default({match.group(1)})")
        elif "default now()" in rest.lower() or "default now ()" in rest.lower():
            decorators.append("@default(now())")

        if field_name != raw_field_name:
            decorators.append(f'@map("{raw_field_name}")')

        reference = re.search(r"REFERENCES\s+([a-zA-Z0-9_]+)\s*\(", rest, re.IGNORECASE)
        if reference:
            target_table = reference.group(1).lower()
            target_model = table_to_model.get(target_table, pascal(target_table.rstrip("s")))
            relation_name = field_name[:-2] if field_name.endswith("Id") else camel(target_model)
            on_delete = "Cascade" if "ON DELETE CASCADE" in rest_upper else "Restrict"
            if "ON DELETE SET NULL" in rest_upper:
                on_delete = "SetNull"
            optional = "?" if is_nullable else ""
            named_relation = (relation_names or {}).get(raw_field_name)
            relation_arg = f'"{named_relation}", ' if named_relation else ""
            relation_lines.append(
                f"  {relation_name:<20} {target_model}{optional}  "
                f"@relation({relation_arg}fields: [{field_name}], references: [id], onDelete: {on_delete})"
            )
            index_fields.append(field_name)

        suffix = "?" if is_nullable else ""
        dec_str = " ".join(decorators)
        lines.append(f"  {field_name:<20} {prisma_type}{suffix}{'  ' + dec_str if dec_str else ''}")

    if not has_id:
        lines.insert(0, f"  {'id':<20} String  @id @default(uuid())")

    # Siempre añadir createdAt/updatedAt si no existen ya
    field_names_lower = {f.strip().split()[0].lower() for f in lines}
    if "createdat" not in field_names_lower and "created_at" not in field_names_lower:
        lines.append(f"  {'createdAt':<20} DateTime  @default(now())")
    if "updatedat" not in field_names_lower and "updated_at" not in field_names_lower:
        lines.append(f"  {'updatedAt':<20} DateTime  @updatedAt")

    lines.extend(relation_lines)
    lines.extend(reverse_relations or [])
    if any(line.strip().startswith("status ") for line in lines):
        index_fields.append("status")
    if any(line.strip().startswith("createdAt ") for line in lines):
        index_fields.append("createdAt")
    for field_name in dict.fromkeys(index_fields):
        lines.append(f"  @@index([{field_name}])")
    if {"userId", "status"}.issubset(index_fields):
        lines.append("  @@index([userId, status])")
    lines.append(f'  @@map("{slug(pluralize(entity.get("name", "entity"))).replace("-", "_")}")')

    body = "\n".join(lines)
    return f"\nmodel {pascal_name} {{\n{body}\n}}\n"


def _user_model(reverse_relations: list[str] | None = None) -> str:
    relations = "\n".join(reverse_relations or [])
    if relations:
        relations = f"{relations}\n"
    return (
        "\nmodel User {\n"
        "  id           String   @id @default(uuid()) @db.Uuid\n"
        "  email        String   @unique\n"
        "  name         String\n"
        "  passwordHash String   @map(\"password_hash\")\n"
        '  role         String   @default("user")\n'
        "  isActive     Boolean  @default(true) @map(\"is_active\")\n"
        "  version      Int      @default(1)\n"
        "  createdAt    DateTime @default(now()) @map(\"created_at\")\n"
        "  updatedAt    DateTime @updatedAt @map(\"updated_at\")\n"
        f"{relations}"
        "  @@index([role, isActive])\n"
        '  @@map("users")\n'
        "}\n"
    )


def generate_prisma_schema(
    modules: list[str],
    needs_auth: bool,
    data_entities: list[dict] | None = None,
    schema_path: str = "prisma/schema.prisma",
) -> GeneratedFile:
    """Genera un archivo schema.prisma completo."""
    user_model = _user_model() if needs_auth else ""

    if data_entities:
        entity_names_lower = {e.get("name", "").lower() for e in data_entities}
        has_user_entity = "user" in entity_names_lower
        table_to_model = {
            slug(pluralize(e.get("name", "entity"))).replace("-", "_"): pascal(e.get("name", "Entity"))
            for e in data_entities[:12]
        }
        if needs_auth:
            table_to_model.setdefault("users", "User")

        inbound: dict[str, list[str]] = {}
        entity_relation_names: dict[str, dict[str, str]] = {}
        for entity in data_entities[:12]:
            source_model = pascal(entity.get("name", "Entity"))
            references: list[tuple[str, str, str]] = []
            for field in entity.get("fields", []):
                reference = re.search(r"REFERENCES\s+([a-zA-Z0-9_]+)\s*\(", field, re.IGNORECASE)
                if not reference:
                    continue
                raw_field_name = field.split(":", 1)[0].strip()
                target_model = table_to_model.get(
                    reference.group(1).lower(),
                    pascal(reference.group(1).rstrip("s")),
                )
                references.append((raw_field_name, camel(raw_field_name), target_model))

            target_counts: dict[str, int] = {}
            for _, _, target_model in references:
                target_counts[target_model] = target_counts.get(target_model, 0) + 1

            for raw_field_name, field_name, target_model in references:
                named_relation = ""
                reverse_name = camel(pluralize(source_model))
                if target_counts[target_model] > 1:
                    relation_part = field_name[:-2] if field_name.endswith("Id") else field_name
                    named_relation = f"{source_model}{pascal(relation_part)}"
                    reverse_name = camel(f"{relation_part}{pluralize(source_model)}")
                    entity_relation_names.setdefault(source_model, {})[raw_field_name] = named_relation
                relation_suffix = f' @relation("{named_relation}")' if named_relation else ""
                inbound.setdefault(target_model, []).append(
                    f"  {reverse_name:<20} {source_model}[]{relation_suffix}"
                )

        entity_models = "".join(
            entity_to_prisma_model(
                entity,
                table_to_model,
                list(dict.fromkeys(inbound.get(pascal(entity.get("name", "Entity")), []))),
                entity_relation_names.get(pascal(entity.get("name", "Entity")), {}),
            )
            for entity in data_entities[:12]
        )
        if needs_auth and not has_user_entity:
            user_model = _user_model(list(dict.fromkeys(inbound.get("User", []))))
        domain_models = entity_models if has_user_entity else (user_model + entity_models)
    else:
        module_models = ""
        for mod in modules[:5]:
            p = pascal(mod)
            module_models += (
                f"\nmodel {p} {{\n"
                "  id          String   @id @default(uuid())\n"
                "  name        String\n"
                "  description String?\n"
                '  status      String   @default("active")\n'
                "  createdAt   DateTime @default(now())\n"
                "  updatedAt   DateTime @updatedAt\n"
                "}\n"
            )
        domain_models = user_model + module_models

    content = (
        "generator client {\n"
        '  provider = "prisma-client-js"\n'
        "}\n"
        "\n"
        "datasource db {\n"
        '  provider = "postgresql"\n'
        '  url      = env("DATABASE_URL")\n'
        "}\n"
        f"{domain_models}"
    )
    return GeneratedFile(path=schema_path, language="prisma", content=content)


def generate_seed_ts(
    entities: list[dict],
    project_name: str,
    seed_path: str = "prisma/seed.ts",
) -> GeneratedFile:
    """Genera un archivo prisma/seed.ts con 3 registros de ejemplo por entidad."""
    seed_blocks = []
    for entity in entities[:5]:
        entity_pascal = pascal(entity.get("name", "Item"))
        entity_camel_name = camel(entity.get("name", "Item"))
        rows = []
        for i in range(1, 4):
            rows.append(
                f'    {{ name: "{entity_pascal} ejemplo {i}", description: "Descripción del {entity_pascal.lower()} {i}", status: "active" }}'
            )
        rows_str = ",\n".join(rows)
        seed_blocks.append(
            f"  // Crear registros de ejemplo para {entity_pascal}\n"
            f"  await prisma.{entity_camel_name}.createMany({{\n"
            f"    data: [\n{rows_str}\n    ],\n"
            f"    skipDuplicates: true,\n"
            f"  }});\n"
            f'  console.log("Seed: {entity_pascal} creado con 3 registros de ejemplo");'
        )

    seed_code = "\n\n".join(seed_blocks) if seed_blocks else '  console.log("Sin entidades para sembrar");'

    content = f"""import {{ PrismaClient }} from "@prisma/client";

// Script de seed para {project_name}
// Ejecutar con: npx ts-node prisma/seed.ts  o  npx prisma db seed
const prisma = new PrismaClient();

async function main() {{
  console.log("Iniciando seed de {project_name}...");

{seed_code}

  console.log("Seed completado correctamente.");
}}

main()
  .catch((e) => {{
    console.error("Error en seed:", e);
    process.exit(1);
  }})
  .finally(async () => {{
    await prisma.$disconnect();
  }});
"""
    return GeneratedFile(path=seed_path, language="typescript", content=content)
