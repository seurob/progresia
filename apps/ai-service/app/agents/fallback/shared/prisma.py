"""Prisma schema generation helpers for fallback scaffold generators."""
from app.schemas.codegen import GeneratedFile
from app.agents.fallback.shared.entities import pascal, camel


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


def entity_to_prisma_model(entity: dict) -> str:
    """Convierte una entidad de datos a un modelo Prisma."""
    pascal_name = pascal(entity.get("name", "Entity"))
    raw_fields = entity.get("fields", [])
    lines = []
    has_id = False

    for field_str in raw_fields[:20]:
        colon_idx = field_str.find(":")
        if colon_idx == -1:
            continue
        field_name = field_str[:colon_idx].strip()
        rest = field_str[colon_idx + 1:].strip()
        rest_upper = rest.upper()

        prisma_type = sql_type_to_prisma(rest_upper)
        decorators = []
        is_pk = "PK" in rest_upper
        is_unique = "UNIQUE" in rest_upper
        is_nullable = "NOT NULL" not in rest_upper and not is_pk

        if is_pk:
            has_id = True
            decorators.append("@id @default(uuid())")
        elif is_unique:
            decorators.append("@unique")

        name_lower = field_name.lower()
        if name_lower in ("createdat", "created_at"):
            decorators.append("@default(now())")
        elif name_lower in ("updatedat", "updated_at"):
            decorators.append("@updatedAt")
        elif "default now()" in rest.lower() or "default now ()" in rest.lower():
            decorators.append("@default(now())")

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

    body = "\n".join(lines)
    return f"\nmodel {pascal_name} {{\n{body}\n}}\n"


def generate_prisma_schema(
    modules: list[str],
    needs_auth: bool,
    data_entities: list[dict] | None = None,
    schema_path: str = "prisma/schema.prisma",
) -> GeneratedFile:
    """Genera un archivo schema.prisma completo."""
    user_model = (
        "\nmodel User {\n"
        "  id           String   @id @default(uuid())\n"
        "  email        String   @unique\n"
        "  name         String\n"
        "  passwordHash String\n"
        '  role         String   @default("user")\n'
        "  createdAt    DateTime @default(now())\n"
        "  updatedAt    DateTime @updatedAt\n"
        "}\n"
    ) if needs_auth else ""

    if data_entities:
        entity_names_lower = {e.get("name", "").lower() for e in data_entities}
        has_user_entity = "user" in entity_names_lower
        entity_models = "".join(entity_to_prisma_model(e) for e in data_entities[:12])
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
