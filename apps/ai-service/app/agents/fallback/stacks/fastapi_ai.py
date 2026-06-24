"""FastAPI + Python 3.11+ + SQLModel + PostgreSQL/SQLite scaffold generator.

Detecta si es un proyecto RAG/AI y añade ChromaDB + documentos si es necesario.
"""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.docker import generate_docker_compose, generate_python_dockerfile
from app.agents.fallback.shared.readme import generate_readme


def build_fastapi_ai(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold FastAPI con SQLModel."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_name = primary.get("name", "Item")
    entity_pascal_name = pascal(entity_name)
    entity_camel_name = camel(entity_name)
    entity_slug_name = slug(entity_name)
    entity_plural = pluralize(entity_slug_name)

    # Detectar si es un proyecto RAG/IA
    reqs_text = " ".join(
        r.get("title", "") + " " + r.get("description", "")
        for r in req.requirements[:10]
    ).lower()
    stack_lower = " ".join(req.stack).lower()
    is_rag = any(k in reqs_text + stack_lower for k in (
        "rag", "embeddings", "chromadb", "langchain", "llm", "ai agent",
        "chat", "vector", "document", "semantic search"
    ))

    files: list[GeneratedFile] = [
        _pyproject_toml(project_slug, is_rag),
        _app_init(),
        _main_py(project_slug, entity_slug_name, entity_plural),
        _core_init(),
        _core_config(project_slug),
        _core_database(),
        _api_init(),
        _api_routes(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _models_init(),
        _entity_model(entity_slug_name, entity_pascal_name),
        _schemas_init(),
        _entity_schema(entity_slug_name, entity_pascal_name),
        _services_init(),
        _entity_service(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _tests_init(),
        _test_health(),
        _env_example(project_slug),
        _gitignore(),
        generate_readme(
            req,
            stack_summary="FastAPI · Python 3.11 · SQLModel · PostgreSQL",
            prerequisites=[
                "Python 3.11+ — https://python.org",
                "Docker Desktop 4.x — https://docker.com/products/docker-desktop",
                "Git 2.x — https://git-scm.com",
            ],
            setup_commands=[
                "docker compose up -d",
                "pip install -e .",
                "python -m uvicorn app.main:app --port 8000 --reload",
            ],
            env_vars=[
                ("DATABASE_URL", f"postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"),
                ("SECRET_KEY", "genera con: openssl rand -hex 32"),
                ("OPENAI_API_KEY", "opcional — para funcionalidades de IA"),
            ],
            api_port=8000,
        ),
        generate_python_dockerfile(port=8000),
        generate_docker_compose(project_slug, needs_postgres=True, api_port=8000),
    ]

    if is_rag:
        files.append(_ai_service())

    return files


def _pyproject_toml(project_slug: str, is_rag: bool) -> GeneratedFile:
    rag_deps = ""
    if is_rag:
        rag_deps = """
    "chromadb>=0.4.0",
    "langchain>=0.2.0",
    "langchain-openai>=0.1.0",
    "openai>=1.0.0","""

    content = f"""\
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "{project_slug}"
version = "0.1.0"
description = "MVP generado con ProgresIA Studio"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlmodel>=0.0.22",
    "psycopg2-binary>=2.9.10",
    "python-dotenv>=1.0.0",
    "pydantic-settings>=2.6.0",
    "python-multipart>=0.0.12",{rag_deps}
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.28.0",
    "pytest-asyncio>=0.24.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
"""
    return GeneratedFile(path="pyproject.toml", language="toml", content=content)


def _app_init() -> GeneratedFile:
    return GeneratedFile(path="app/__init__.py", language="python", content='"""Aplicación FastAPI."""\n')


def _main_py(project_slug: str, entity_slug: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.database import engine
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas en la base de datos al iniciar (solo para desarrollo)
    # En producción usar alembic migrate
    SQLModel.metadata.create_all(engine)
    yield


# Inicializar la aplicación FastAPI
app = FastAPI(
    title="{project_slug.replace('-', ' ').title()} API",
    description="API REST generada con ProgresIA Studio",
    version="0.1.0",
    lifespan=lifespan,
)

# Configurar CORS para el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(router, prefix="/api")


@app.get("/health")
def health_check():
    return {{"status": "ok", "version": "0.1.0"}}
"""
    return GeneratedFile(path="app/main.py", language="python", content=content)


def _core_init() -> GeneratedFile:
    return GeneratedFile(path="app/core/__init__.py", language="python", content='"""Core: configuración y base de datos."""\n')


def _core_config(project_slug: str) -> GeneratedFile:
    content = """\
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de datos
    database_url: str = "sqlite:///./dev.db"

    # Seguridad
    secret_key: str = "dev_secret_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 días

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # IA (opcional)
    openai_api_key: str = ""
    groq_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton de configuración — importar desde aquí en toda la app
settings = Settings()
"""
    return GeneratedFile(path="app/core/config.py", language="python", content=content)


def _core_database() -> GeneratedFile:
    # Nota: no usamos triple comilla dentro de la cadena para evitar conflicto con f-string
    content = (
        "from sqlmodel import Session, create_engine\n"
        "from app.core.config import settings\n"
        "\n"
        "# Motor de base de datos SQLModel\n"
        "engine = create_engine(\n"
        "    settings.database_url,\n"
        '    echo=True if "sqlite" in settings.database_url else False,\n'
        ")\n"
        "\n"
        "\n"
        "def get_session():\n"
        "    # Dependencia FastAPI para obtener una sesion de base de datos\n"
        "    with Session(engine) as session:\n"
        "        yield session\n"
    )
    return GeneratedFile(path="app/core/database.py", language="python", content=content)


def _api_init() -> GeneratedFile:
    return GeneratedFile(path="app/api/__init__.py", language="python", content='"""Módulo de rutas API."""\n')


def _api_routes(entity_slug: str, entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.{entity_slug} import {entity_pascal}Create, {entity_pascal}Read, {entity_pascal}Update
from app.services.{entity_slug}_service import {entity_pascal}Service

router = APIRouter()


@router.get("/{entity_plural}", response_model=list[{entity_pascal}Read])
def list_{entity_camel}s(session: Session = Depends(get_session)):
    # Obtener todos los {entity_pascal}s
    return {entity_pascal}Service(session).find_all()


@router.get("/{entity_plural}/{{item_id}}", response_model={entity_pascal}Read)
def get_{entity_camel}(item_id: str, session: Session = Depends(get_session)):
    # Obtener un {entity_pascal} por ID
    item = {entity_pascal}Service(session).find_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="{entity_pascal} no encontrado")
    return item


@router.post("/{entity_plural}", response_model={entity_pascal}Read, status_code=201)
def create_{entity_camel}(data: {entity_pascal}Create, session: Session = Depends(get_session)):
    # Crear un nuevo {entity_pascal}
    return {entity_pascal}Service(session).create(data)


@router.put("/{entity_plural}/{{item_id}}", response_model={entity_pascal}Read)
def update_{entity_camel}(
    item_id: str, data: {entity_pascal}Update, session: Session = Depends(get_session)
):
    # Actualizar un {entity_pascal} existente
    item = {entity_pascal}Service(session).update(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="{entity_pascal} no encontrado")
    return item


@router.delete("/{entity_plural}/{{item_id}}", status_code=204)
def delete_{entity_camel}(item_id: str, session: Session = Depends(get_session)):
    # Eliminar un {entity_pascal}
    deleted = {entity_pascal}Service(session).delete(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="{entity_pascal} no encontrado")
"""
    return GeneratedFile(path="app/api/routes.py", language="python", content=content)


def _models_init() -> GeneratedFile:
    return GeneratedFile(path="app/models/__init__.py", language="python", content='"""Modelos de base de datos SQLModel."""\n')


def _entity_model(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
import uuid


# Modelo de base de datos para {entity_pascal}
# SQLModel combina Pydantic y SQLAlchemy en una sola clase
class {entity_pascal}(SQLModel, table=True):
    \"\"\"Tabla {entity_pascal} en la base de datos.\"\"\"
    __tablename__ = "{{entity_plural}}"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
""".replace("{entity_plural}", entity_plural_from_slug(entity_slug))
    return GeneratedFile(path=f"app/models/{entity_slug}.py", language="python", content=content)


def entity_plural_from_slug(entity_slug: str) -> str:
    """Pluraliza el slug de la entidad."""
    if entity_slug.endswith(("s", "x", "z")):
        return entity_slug + "es"
    return entity_slug + "s"


def _schemas_init() -> GeneratedFile:
    return GeneratedFile(path="app/schemas/__init__.py", language="python", content='"""Esquemas Pydantic para validación."""\n')


def _entity_schema(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Esquemas Pydantic para la API (request/response bodies)

class {entity_pascal}Create(BaseModel):
    \"\"\"Datos para crear un {entity_pascal.lower()}.\"\"\"
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class {entity_pascal}Update(BaseModel):
    \"\"\"Datos para actualizar un {entity_pascal.lower()} (todos opcionales).\"\"\"
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = None


class {entity_pascal}Read(BaseModel):
    \"\"\"Datos que devuelve la API al leer un {entity_pascal.lower()}.\"\"\"
    id: str
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {{"from_attributes": True}}
"""
    return GeneratedFile(path=f"app/schemas/{entity_slug}.py", language="python", content=content)


def _services_init() -> GeneratedFile:
    return GeneratedFile(path="app/services/__init__.py", language="python", content='"""Servicios de negocio."""\n')


def _entity_service(entity_slug: str, entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select

from app.models.{entity_slug} import {entity_pascal}
from app.schemas.{entity_slug} import {entity_pascal}Create, {entity_pascal}Update


class {entity_pascal}Service:
    \"\"\"Servicio con la lógica de negocio para {entity_pascal}.\"\"\"

    def __init__(self, session: Session):
        self.session = session

    def find_all(self) -> list[{entity_pascal}]:
        \"\"\"Obtener todos los registros ordenados por fecha de creación.\"\"\"
        return list(self.session.exec(
            select({entity_pascal}).order_by({entity_pascal}.created_at.desc())
        ).all())

    def find_by_id(self, item_id: str) -> Optional[{entity_pascal}]:
        \"\"\"Buscar un registro por su ID.\"\"\"
        return self.session.get({entity_pascal}, item_id)

    def create(self, data: {entity_pascal}Create) -> {entity_pascal}:
        \"\"\"Crear un nuevo registro.\"\"\"
        item = {entity_pascal}(**data.model_dump())
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def update(self, item_id: str, data: {entity_pascal}Update) -> Optional[{entity_pascal}]:
        \"\"\"Actualizar un registro existente.\"\"\"
        item = self.session.get({entity_pascal}, item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        item.updated_at = datetime.utcnow()

        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, item_id: str) -> bool:
        \"\"\"Eliminar un registro. Devuelve True si existía.\"\"\"
        item = self.session.get({entity_pascal}, item_id)
        if not item:
            return False
        self.session.delete(item)
        self.session.commit()
        return True
"""
    return GeneratedFile(path=f"app/services/{entity_slug}_service.py", language="python", content=content)


def _ai_service() -> GeneratedFile:
    content = """\
"""
    content = '''\
"""Servicio de IA con soporte para modo demo cuando no hay API key."""
import os
from typing import Optional


class AIService:
    """Servicio de IA que funciona en modo demo si no hay OPENAI_API_KEY."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.demo_mode = not bool(self.api_key)
        if self.demo_mode:
            print("[AIService] Modo demo activo — sin OPENAI_API_KEY")

    def chat(self, message: str, context: Optional[str] = None) -> str:
        """Envía un mensaje al modelo de IA o devuelve una respuesta demo."""
        if self.demo_mode:
            return self._demo_response(message)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": message})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[Error de IA: {str(e)}] {self._demo_response(message)}"

    def _demo_response(self, message: str) -> str:
        """Respuesta de demostración cuando no hay API key configurada."""
        return (
            f"[Modo demo] Recibido: '{message[:50]}...'. "
            "Para activar la IA real, configura OPENAI_API_KEY en .env"
        )


# Singleton del servicio de IA
ai_service = AIService()
'''
    return GeneratedFile(path="app/services/ai_service.py", language="python", content=content)


def _tests_init() -> GeneratedFile:
    return GeneratedFile(path="tests/__init__.py", language="python", content="")


def _test_health() -> GeneratedFile:
    content = """\
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    \"\"\"El endpoint /health debe responder con status ok.\"\"\"
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
"""
    return GeneratedFile(path="tests/test_health.py", language="python", content=content)


def _env_example(project_slug: str) -> GeneratedFile:
    content = f"""\
# Base de datos (PostgreSQL en producción, SQLite en desarrollo)
DATABASE_URL="postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"
# Para desarrollo local sin Docker:
# DATABASE_URL="sqlite:///./dev.db"

# Seguridad
SECRET_KEY="genera con: openssl rand -hex 32"

# CORS — URL del frontend
CORS_ORIGINS='["http://localhost:5173","http://localhost:3000"]'

# IA (opcional)
OPENAI_API_KEY=""
GROQ_API_KEY=""
"""
    return GeneratedFile(path=".env.example", language="env", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
__pycache__/
*.py[cod]
*.pyc
.venv/
venv/
.env
.env.local
*.log
.DS_Store
dist/
*.egg-info/
dev.db
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
