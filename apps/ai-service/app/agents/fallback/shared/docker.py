"""Docker helper functions for fallback scaffold generators."""
from app.schemas.codegen import GeneratedFile


def generate_docker_compose(
    project_slug: str,
    needs_postgres: bool = True,
    needs_redis: bool = False,
    needs_ai_service: bool = False,
    api_port: int = 3000,
    web_port: int | None = None,
    db_type: str = "postgres",  # postgres | mysql
) -> GeneratedFile:
    """Genera un docker-compose.yml con los servicios necesarios."""

    db_block = ""
    if needs_postgres and db_type == "postgres":
        db_block = (
            "  postgres:\n"
            "    image: postgres:16-alpine\n"
            "    restart: unless-stopped\n"
            "    environment:\n"
            f"      POSTGRES_USER: {project_slug}\n"
            f"      POSTGRES_PASSWORD: {project_slug}\n"
            f"      POSTGRES_DB: {project_slug}_db\n"
            "    ports:\n"
            '      - "5432:5432"\n'
            "    volumes:\n"
            "      - postgres_data:/var/lib/postgresql/data\n"
            "    healthcheck:\n"
            f'      test: ["CMD-SHELL", "pg_isready -U {project_slug}"]\n'
            "      interval: 5s\n"
            "      timeout: 5s\n"
            "      retries: 5\n"
            "\n"
        )
    elif needs_postgres and db_type == "mysql":
        db_block = (
            "  mysql:\n"
            "    image: mysql:8.0\n"
            "    restart: unless-stopped\n"
            "    environment:\n"
            f"      MYSQL_ROOT_PASSWORD: {project_slug}_root\n"
            f"      MYSQL_DATABASE: {project_slug}_db\n"
            f"      MYSQL_USER: {project_slug}\n"
            f"      MYSQL_PASSWORD: {project_slug}\n"
            "    ports:\n"
            '      - "3306:3306"\n'
            "    volumes:\n"
            "      - mysql_data:/var/lib/mysql\n"
            "    healthcheck:\n"
            f'      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]\n'
            "      interval: 5s\n"
            "      timeout: 5s\n"
            "      retries: 10\n"
            "\n"
        )

    redis_block = ""
    if needs_redis:
        redis_block = (
            "  redis:\n"
            "    image: redis:7-alpine\n"
            "    restart: unless-stopped\n"
            "    ports:\n"
            '      - "6379:6379"\n'
            "    volumes:\n"
            "      - redis_data:/data\n"
            "\n"
        )

    ai_block = ""
    if needs_ai_service:
        ai_block = (
            "  ai-service:\n"
            "    build: ./apps/ai-service\n"
            "    restart: unless-stopped\n"
            "    environment:\n"
            "      - GROQ_API_KEY=${GROQ_API_KEY:-}\n"
            "      - OPENAI_API_KEY=${OPENAI_API_KEY:-}\n"
            "    ports:\n"
            '      - "8003:8003"\n'
            "    depends_on:\n"
            "      - postgres\n"
            "\n"
        )

    web_block = ""
    if web_port:
        web_block = (
            "  web:\n"
            "    build: ./\n"
            "    restart: unless-stopped\n"
            "    environment:\n"
            f"      - VITE_API_URL=http://localhost:{api_port}\n"
            "    ports:\n"
            f'      - "{web_port}:{web_port}"\n'
            "    depends_on:\n"
            "      - api\n"
            "\n"
        )

    db_depends = "postgres" if needs_postgres and db_type == "postgres" else ("mysql" if db_type == "mysql" else "")
    api_depends = f"    depends_on:\n      {db_depends}:\n        condition: service_healthy\n" if db_depends else ""

    api_block = (
        "  api:\n"
        "    build: ./\n"
        "    restart: unless-stopped\n"
        "    environment:\n"
        f"      - DATABASE_URL=postgresql://{project_slug}:{project_slug}@postgres:5432/{project_slug}_db\n"
        "      - JWT_SECRET=${JWT_SECRET:-change_me_in_production}\n"
        "      - NODE_ENV=production\n"
        "    ports:\n"
        f'      - "{api_port}:{api_port}"\n'
        f"{api_depends}"
        "\n"
    )

    # Volumes
    volume_names = []
    if needs_postgres and db_type == "postgres":
        volume_names.append("postgres_data")
    elif needs_postgres and db_type == "mysql":
        volume_names.append("mysql_data")
    if needs_redis:
        volume_names.append("redis_data")

    volumes_block = "volumes:\n" + "".join(f"  {v}:\n" for v in volume_names) if volume_names else ""

    content = (
        "services:\n"
        + db_block
        + redis_block
        + api_block
        + web_block
        + ai_block
        + volumes_block
    )

    return GeneratedFile(path="docker-compose.yml", language="yaml", content=content)


def generate_node_dockerfile(
    port: int = 3000,
    entry: str = "dist/main.js",
    needs_prisma: bool = True,
) -> GeneratedFile:
    """Genera un Dockerfile multi-stage para una app Node.js."""
    prisma_copy = "COPY --from=build /app/prisma ./prisma\n" if needs_prisma else ""

    content = (
        "FROM node:22-alpine AS deps\n"
        "WORKDIR /app\n"
        "COPY package.json package-lock.json* ./\n"
        "RUN npm ci --omit=dev\n"
        "\n"
        "FROM node:22-alpine AS build\n"
        "WORKDIR /app\n"
        "COPY package.json package-lock.json* ./\n"
        "RUN npm ci\n"
        "COPY . .\n"
        "RUN npm run build\n"
        "\n"
        "FROM node:22-alpine AS runner\n"
        "WORKDIR /app\n"
        "ENV NODE_ENV=production\n"
        "COPY --from=deps /app/node_modules ./node_modules\n"
        "COPY --from=build /app/dist ./dist\n"
        f"{prisma_copy}"
        f"EXPOSE {port}\n"
        f'CMD ["node", "{entry}"]\n'
    )
    return GeneratedFile(path="Dockerfile", language="dockerfile", content=content)


def generate_python_dockerfile(port: int = 8000) -> GeneratedFile:
    """Genera un Dockerfile para una app FastAPI/Python."""
    content = (
        "FROM python:3.11-slim\n"
        "\n"
        "WORKDIR /app\n"
        "\n"
        "# Instalar dependencias del sistema\n"
        "RUN apt-get update && apt-get install -y --no-install-recommends \\\n"
        "    gcc libpq-dev \\\n"
        "    && rm -rf /var/lib/apt/lists/*\n"
        "\n"
        "# Copiar e instalar dependencias Python\n"
        "COPY pyproject.toml ./\n"
        "RUN pip install --no-cache-dir --upgrade pip \\\n"
        "    && pip install --no-cache-dir .\n"
        "\n"
        "# Copiar el código de la aplicación\n"
        "COPY . .\n"
        "\n"
        f"EXPOSE {port}\n"
        "\n"
        f'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]\n'
    )
    return GeneratedFile(path="Dockerfile", language="dockerfile", content=content)
