"""README generation helpers for fallback scaffold generators."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug


def generate_readme(
    req: CodeGenerationRequest,
    stack_summary: str,
    prerequisites: list[str] | None = None,
    setup_commands: list[str] | None = None,
    env_vars: list[tuple[str, str]] | None = None,
    project_structure: str | None = None,
    extra_sections: str | None = None,
    api_port: int = 3000,
    web_port: int | None = None,
) -> GeneratedFile:
    """Genera un README.md completo y amigable para principiantes.

    El README está en español para que sea comprensible por los usuarios
    que aprenden con ProgresIA Studio.
    """
    project_slug = slug(req.project_name)

    # Prerequisites section
    if prerequisites is None:
        prerequisites = [
            "Node.js 20 LTS — https://nodejs.org",
            "Docker Desktop 4.x — https://docker.com/products/docker-desktop",
            "Git 2.x — https://git-scm.com",
        ]

    prereqs_rows = "\n".join(
        f"| {p.split(' — ')[0]} | {p.split(' — ')[1] if ' — ' in p else ''} |"
        for p in prerequisites
    )

    prereqs_text = " ".join(prerequisites).lower()
    verify_commands = ["git --version", "docker --version"]
    if "node" in prereqs_text or "npm" in prereqs_text:
        verify_commands.extend(["node --version", "npm --version"])
    if "php" in prereqs_text:
        verify_commands.append("php --version")
    if "composer" in prereqs_text:
        verify_commands.append("composer --version")
    if "python" in prereqs_text:
        verify_commands.append("python --version")
    verify_str = " && ".join(dict.fromkeys(verify_commands))
    # Setup commands
    if setup_commands is None:
        setup_commands = [
            "docker compose up -d",
            "npm install",
            "npm run db:migrate",
            "npm run dev",
        ]
    setup_str = "\n".join(f"    {cmd}" for cmd in setup_commands)

    # Env vars table
    if env_vars is None:
        env_vars = [
            ("DATABASE_URL", f"postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"),
            ("JWT_SECRET", "genera con: openssl rand -hex 32"),
        ]
    env_rows = "\n".join(f"| `{k}` | `{v}` |" for k, v in env_vars)

    # API endpoints from req or defaults
    if req.api_endpoints:
        endpoint_rows = "\n".join(
            f"| `{ep.get('method','GET')}` | `{ep.get('path','/')}` | {ep.get('description','')} |"
            for ep in req.api_endpoints[:12]
        )
    else:
        first_res = (req.modules[0] if req.modules else "items").lower().replace(" ", "-") + "s"
        endpoint_rows = (
            f"| `GET` | `/health` | Estado del servidor |\n"
            f"| `GET` | `/api/{first_res}` | Listar todos |\n"
            f"| `POST` | `/api/{first_res}` | Crear nuevo |\n"
            f"| `GET` | `/api/{first_res}/:id` | Obtener uno |\n"
            f"| `PUT` | `/api/{first_res}/:id` | Actualizar |\n"
            f"| `DELETE` | `/api/{first_res}/:id` | Eliminar |"
        )
        if req.needs_auth:
            endpoint_rows = "| `POST` | `/auth/register` | Registro |\n| `POST` | `/auth/login` | Login |\n" + endpoint_rows

    # Project structure
    if project_structure is None:
        project_structure = f"""{project_slug}/
├── src/              # Código fuente
├── prisma/           # Esquema y migraciones de base de datos
├── sdd/              # Especificaciones SDD del proyecto
├── docker-compose.yml
├── .env.example
└── README.md"""

    urls_section = f"| Frontend | http://localhost:{web_port} |\n" if web_port else ""
    urls_section += f"| API | http://localhost:{api_port} |\n"
    urls_section += "| Base de datos | localhost:5432 |"

    extra = extra_sections or ""

    content = f"""# {req.project_name}

> MVP generado con [ProgresIA Studio](https://progresia.studio) — metodología SDD.

**Sector**: {req.sector} | **Stack**: {stack_summary}

---

## Requisitos previos

Antes de empezar, asegúrate de tener instalado:

| Herramienta | Enlace de descarga |
|-------------|-------------------|
{prereqs_rows}

---

## Instalación rápida

```bash
# 1. Obten el proyecto desde Git o ZIP
git clone <URL-del-repositorio> {project_slug}
cd {project_slug}
# Si descargaste un ZIP, descomprimelo y entra en la carpeta del proyecto.

# 2. Verifica herramientas base
{verify_str}
# Si algun comando falla, instala la herramienta indicada en Requisitos previos.

# 3. Copia el archivo de variables de entorno
cp .env.example .env
# Edita .env con tus valores reales

# 4. Inicia servicios e instala dependencias del stack
{setup_str}
```

---

## URLs en desarrollo

| Servicio | URL |
|----------|-----|
{urls_section}

---

## Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores:

| Variable | Ejemplo / Descripción |
|----------|-----------------------|
{env_rows}

---

## Estructura del proyecto

```
{project_structure}
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
{endpoint_rows}

---

## Cómo continuar desarrollando

1. **Empieza por `sdd/constitution.md`** — explica la arquitectura y decisiones del proyecto
2. **Lee `sdd/requirements/requirements.md`** — los requisitos funcionales y no funcionales
3. **Usa los prompts de `sdd/prompts/`** — instrucciones optimizadas para Claude, Copilot o ChatGPT

### Añadir una nueva funcionalidad

```bash
# 1. Crea una rama
git checkout -b feat/nombre-de-la-funcionalidad

# 2. Implementa el cambio

# 3. Commit con Conventional Commits
git commit -m "feat: descripción del cambio"
```

{extra}

---

## Generado con ProgresIA Studio

Este proyecto fue generado usando la metodología SDD (Specification-Driven Development).
Visita [progresia.studio](https://progresia.studio) para aprender más.

**Licencia**: MIT
"""

    return GeneratedFile(path="README.md", language="markdown", content=content)
