"""Flask + Python 3.11 + SQLAlchemy + PostgreSQL scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.docker import generate_python_dockerfile
from app.agents.fallback.shared.readme import generate_readme


def build_flask(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Flask con blueprints, SQLAlchemy y Marshmallow."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)
    module_name = project_slug.replace("-", "_")

    return [
        _pyproject_toml(project_slug, req.needs_auth),
        _run_py(module_name),
        _app_init(module_name, entity_slug_name, req.needs_auth),
        _config_py(),
        _extensions_py(req.needs_auth),
        _entity_model(entity_slug_name, entity_pascal_name),
        _entity_schema(entity_slug_name, entity_pascal_name),
        _api_init(),
        _entity_blueprint(entity_slug_name, entity_pascal_name, entity_plural, req.needs_auth),
        _health_blueprint(),
        _test_health(module_name),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Copia este archivo a .env y ajusta los valores\n\n"
                f"DATABASE_URL=postgresql://user:password@localhost:5432/{project_slug}_db\n"
                "SECRET_KEY=genera-con-openssl-rand-hex-32\n"
                "FLASK_ENV=development\n"
                "FLASK_DEBUG=1\n"
                "PORT=5000\n"
                "CORS_ORIGINS=http://localhost:5173\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Flask · Python 3.11 · SQLAlchemy · Marshmallow · PostgreSQL",
            prerequisites=[
                "Python 3.11+ — https://python.org",
                "Docker Desktop — https://docker.com",
            ],
            setup_commands=[
                "docker compose up -d          # levanta PostgreSQL",
                "python -m venv .venv",
                "source .venv/bin/activate     # Windows: .venv\\Scripts\\activate",
                "pip install -e .",
                "cp .env.example .env          # ajusta los valores",
                "flask db upgrade              # crea las tablas",
                "python run.py",
            ],
            env_vars=[
                ("DATABASE_URL", f"postgresql://user:password@localhost:5432/{project_slug}_db"),
                ("SECRET_KEY", "genera con: openssl rand -hex 32"),
                ("FLASK_ENV", "development"),
            ],
            api_port=5000,
        ),
        generate_python_dockerfile(port=5000),
        _docker_compose(project_slug),
    ]


def _pyproject_toml(project_slug: str, needs_auth: bool) -> GeneratedFile:
    auth_deps = '  "flask-jwt-extended>=4.6.0",\n' if needs_auth else ""
    bcrypt_dep = '  "bcrypt>=4.1.0",\n' if needs_auth else ""
    content = f"""\
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "{project_slug}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "flask>=3.0.0",
  "flask-sqlalchemy>=3.1.1",
  "flask-migrate>=4.0.7",
  "flask-cors>=4.0.0",
  "marshmallow>=3.21.3",
  "marshmallow-sqlalchemy>=1.0.0",
  "psycopg2-binary>=2.9.9",
  "python-dotenv>=1.0.1",
{auth_deps}{bcrypt_dep}]

[project.optional-dependencies]
dev = ["pytest>=8.2.0", "pytest-flask>=1.3.0", "ruff>=0.4.0"]

[tool.ruff]
line-length = 100
"""
    return GeneratedFile(path="pyproject.toml", language="toml", content=content)


def _run_py(module_name: str) -> GeneratedFile:
    content = f"""\
import os
from dotenv import load_dotenv

load_dotenv()

from {module_name} import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""
    return GeneratedFile(path="run.py", language="python", content=content)


def _app_init(module_name: str, entity_slug_name: str, needs_auth: bool) -> GeneratedFile:
    jwt_init = "    jwt.init_app(app)\n" if needs_auth else ""
    content = f"""\
from flask import Flask
from .config import Config
from .extensions import db, migrate, cors{', jwt' if needs_auth else ''}
from .api.health import health_bp
from .api.{entity_slug_name} import {entity_slug_name}_bp


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={{r"/api/*": {{"origins": app.config["CORS_ORIGINS"]}}}})
{jwt_init}
    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint({entity_slug_name}_bp, url_prefix='/api/{pluralize(entity_slug_name)}')

    return app
"""
    return GeneratedFile(path=f"{module_name}/__init__.py", language="python", content=content)


def _config_py() -> GeneratedFile:
    content = """\
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173')
    JWT_SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    JSON_SORT_KEYS = False
"""
    return GeneratedFile(path="app/config.py", language="python", content=content)


def _extensions_py(needs_auth: bool) -> GeneratedFile:
    jwt_import = "from flask_jwt_extended import JWTManager\n" if needs_auth else ""
    jwt_decl = "jwt = JWTManager()\n" if needs_auth else ""
    content = f"""\
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
{jwt_import}
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
{jwt_decl}"""
    return GeneratedFile(path="app/extensions.py", language="python", content=content)


def _entity_model(entity_slug_name: str, entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
import uuid
from datetime import datetime
from app.extensions import db


class {entity_pascal_name}(db.Model):
    __tablename__ = '{pluralize(entity_slug_name)}'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {{
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }}
"""
    return GeneratedFile(path=f"app/models/{entity_slug_name}.py", language="python", content=content)


def _entity_schema(entity_slug_name: str, entity_pascal_name: str) -> GeneratedFile:
    entity_camel_name = camel(entity_slug_name)
    content = f"""\
from marshmallow import Schema, fields, validate


class {entity_pascal_name}Schema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True, load_default=None)
    status = fields.Str(load_default='active', validate=validate.OneOf(['active', 'inactive', 'archived']))
    createdAt = fields.DateTime(attribute='created_at', dump_only=True)
    updatedAt = fields.DateTime(attribute='updated_at', dump_only=True)


{entity_camel_name}_schema = {entity_pascal_name}Schema()
{pluralize(entity_slug_name)}_schema = {entity_pascal_name}Schema(many=True)
"""
    return GeneratedFile(path=f"app/schemas/{entity_slug_name}.py", language="python", content=content)


def _api_init() -> GeneratedFile:
    return GeneratedFile(path="app/api/__init__.py", language="python", content='"""API blueprints."""\n')


def _entity_blueprint(entity_slug_name: str, entity_pascal_name: str, entity_plural: str, needs_auth: bool) -> GeneratedFile:
    jwt_decorator = "@jwt_required()\n    " if needs_auth else ""
    jwt_import = "from flask_jwt_extended import jwt_required\n" if needs_auth else ""
    content = f"""\
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.{entity_slug_name} import {entity_pascal_name}
from app.schemas.{entity_slug_name} import {camel(entity_slug_name)}_schema, {entity_plural}_schema
{jwt_import}
{entity_slug_name}_bp = Blueprint('{entity_slug_name}', __name__)


@{entity_slug_name}_bp.get('/')
def list_{entity_plural}():
    items = {entity_pascal_name}.query.order_by({entity_pascal_name}.created_at.desc()).all()
    return jsonify({entity_plural}_schema.dump(items))


@{entity_slug_name}_bp.post('/')
def create_{entity_slug_name}():
    body = request.get_json(silent=True) or {{}}
    errors = {camel(entity_slug_name)}_schema.validate(body)
    if errors:
        return jsonify({{'errors': errors}}), 422

    item = {entity_pascal_name}(
        name=body['name'],
        description=body.get('description'),
        status=body.get('status', 'active'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({camel(entity_slug_name)}_schema.dump(item)), 201


@{entity_slug_name}_bp.get('/<string:item_id>')
def get_{entity_slug_name}(item_id: str):
    item = {entity_pascal_name}.query.get_or_404(item_id)
    return jsonify({camel(entity_slug_name)}_schema.dump(item))


@{entity_slug_name}_bp.patch('/<string:item_id>')
def update_{entity_slug_name}(item_id: str):
    item = {entity_pascal_name}.query.get_or_404(item_id)
    body = request.get_json(silent=True) or {{}}
    if 'name' in body:
        item.name = body['name']
    if 'description' in body:
        item.description = body['description']
    if 'status' in body:
        item.status = body['status']
    db.session.commit()
    return jsonify({camel(entity_slug_name)}_schema.dump(item))


@{entity_slug_name}_bp.delete('/<string:item_id>')
def delete_{entity_slug_name}(item_id: str):
    item = {entity_pascal_name}.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
"""
    return GeneratedFile(path=f"app/api/{entity_slug_name}.py", language="python", content=content)


def _health_blueprint() -> GeneratedFile:
    content = """\
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.get('/health')
def health():
    return jsonify({'status': 'ok'})
"""
    return GeneratedFile(path="app/api/health.py", language="python", content=content)


def _test_health(module_name: str) -> GeneratedFile:
    content = f"""\
import pytest
from {module_name} import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json['status'] == 'ok'
"""
    return GeneratedFile(path="tests/test_health.py", language="python", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
__pycache__/
*.pyc
*.pyo
.env
.venv/
venv/
dist/
*.egg-info/
.pytest_cache/
instance/
migrations/versions/
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)


def _docker_compose(project_slug: str) -> GeneratedFile:
    safe = project_slug.replace("-", "_")
    content = f"""\
services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://{safe}:{safe}@db:5432/{safe}_db
      SECRET_KEY: dev-secret-change-in-production
      FLASK_ENV: production
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: {safe}
      POSTGRES_PASSWORD: {safe}
      POSTGRES_DB: {safe}_db
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {safe}"]
      interval: 10s
      retries: 5

volumes:
  pg_data:
"""
    return GeneratedFile(path="docker-compose.yml", language="yaml", content=content)
