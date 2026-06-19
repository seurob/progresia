"""Django 5 + Django REST Framework template — REST API + PostgreSQL + JWT + Docker.

Placeholders:
  __SLUG__   = kebab-case project name    (e.g. "mi-proyecto")
  __NAME__   = display project name       (e.g. "Mi Proyecto")
  __ENTITY__ = Pascal-case main entity    (e.g. "Producto")
  __ENTITY_LOWER__ = snake_case entity    (e.g. "producto")
  __ENTITY_PLURAL__ = snake_case plural   (e.g. "productos")
"""
from __future__ import annotations

import re

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _pascal(name: str) -> str:
    return "".join(w.capitalize() for w in re.split(r"[\s\-_]+", name.strip()))


def _f(path: str, lang: str, content: str, slug: str, name: str, entity: str) -> GeneratedFile:
    ep = entity.lower()
    eps = ep + "s"
    return GeneratedFile(
        path=path,
        language=lang,
        content=content
            .replace("__SLUG__", slug)
            .replace("__NAME__", name)
            .replace("__ENTITY__", entity)
            .replace("__ENTITY_LOWER__", ep)
            .replace("__ENTITY_PLURAL__", eps),
    )


# ── File contents ──────────────────────────────────────────────────────────────

_README = """# __NAME__ — Django 5 REST API

> Generado por **ProgresIA Studio** · Arquitectura: Django REST Framework

## ¿Qué es este proyecto?

`__NAME__` es una API REST construida con **Django 5** y **Django REST Framework (DRF)**, el dúo más popular para APIs Python en producción. Utiliza PostgreSQL como base de datos y JWT para autenticación.

---

## Stack tecnológico

| Tecnología | Versión | Propósito | Documentación |
|-----------|---------|-----------|---------------|
| Django | 5.x | Framework web Python | https://docs.djangoproject.com/en/5.0/ |
| Django REST Framework | 3.x | Toolkit para APIs REST | https://www.django-rest-framework.org/ |
| djangorestframework-simplejwt | 5.x | Auth JWT | https://django-rest-framework-simplejwt.readthedocs.io/ |
| PostgreSQL | 16 | Base de datos relacional | https://www.postgresql.org/docs/16/ |
| psycopg2 | 2.x | Driver PostgreSQL para Python | https://www.psycopg.org/docs/ |
| Python | 3.12+ | Lenguaje de programación | https://docs.python.org/3.12/ |
| Docker | 26.x | Contenerización | https://docs.docker.com/ |

---

## Arquitectura del proyecto

```
__SLUG__/
├── apps/
│   ├── __ENTITY_PLURAL__/               ← Aplicación Django para el modelo principal
│   │   ├── models.py              ← Modelo ORM de la entidad
│   │   ├── serializers.py         ← Serialización JSON (DRF)
│   │   ├── views.py               ← ViewSets (lógica HTTP)
│   │   ├── urls.py                ← Router DRF
│   │   ├── admin.py               ← Panel de administración
│   │   └── tests.py               ← Tests de la app
│   └── users/                     ← Aplicación de usuarios y auth
│       ├── models.py              ← Modelo User personalizado
│       ├── serializers.py
│       ├── views.py               ← Register, Login, Me
│       └── urls.py
├── config/
│   ├── settings.py                ← Configuración Django
│   ├── urls.py                    ← URLs raíz
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

### ¿Por qué Django + DRF?

**Django** proporciona:
- **ORM potente**: define modelos Python y Django crea y migra las tablas automáticamente
- **Admin panel**: interfaz de administración generada automáticamente en `/admin/`
- **Migraciones**: historial de cambios en la BD, versionado en Git
- **Ecosistema maduro**: 20+ años de evolución, enorme comunidad

**DRF** añade:
- **Serializers**: convierte modelos Django ↔ JSON con validación automática
- **ViewSets**: define CRUD completo con pocas líneas de código
- **Router**: genera URLs REST automáticamente desde ViewSets
- **Browsable API**: interfaz web para probar la API en desarrollo

---

## Instalación rápida (5 minutos)

### Opción A: Con Docker (recomendado)

```bash
# 1. Clonar y configurar entorno
git clone <tu-repo> __SLUG__ && cd __SLUG__
cp .env.example .env

# 2. Levantar servicios
docker compose up --build

# 3. Migraciones + datos de prueba (en otra terminal)
docker compose exec app python manage.py migrate
docker compose exec app python manage.py loaddata fixtures/demo_data.json
# o con el seeder personalizado:
docker compose exec app python manage.py seed_data

# 4. ¡Listo! API en http://localhost:8000/api/
#    Admin panel en http://localhost:8000/admin/
```

### Opción B: Sin Docker (entorno virtual)

```bash
# Requisitos: Python 3.12+, PostgreSQL 16

# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar entorno
cp .env.example .env
# Editar .env con credenciales de PostgreSQL

# 4. Aplicar migraciones
python manage.py migrate

# 5. Crear superusuario para el admin
python manage.py createsuperuser

# 6. Iniciar servidor
python manage.py runserver
# API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

---

## Endpoints de la API

### Autenticación (JWT)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Crear cuenta nueva |
| `POST` | `/api/auth/login/` | Obtener tokens (access + refresh) |
| `POST` | `/api/auth/refresh/` | Renovar access token |
| `GET` | `/api/auth/me/` | Perfil del usuario autenticado |

### __ENTITY_PLURAL__ (recurso principal)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/__ENTITY_PLURAL__/` | Listar (con paginación) |
| `POST` | `/api/__ENTITY_PLURAL__/` | Crear nuevo |
| `GET` | `/api/__ENTITY_PLURAL__/{id}/` | Ver detalle |
| `PUT` | `/api/__ENTITY_PLURAL__/{id}/` | Actualizar completo |
| `PATCH` | `/api/__ENTITY_PLURAL__/{id}/` | Actualizar parcial |
| `DELETE` | `/api/__ENTITY_PLURAL__/{id}/` | Eliminar |

### Cómo usar los tokens JWT

```bash
# 1. Registrar usuario
curl -X POST http://localhost:8000/api/auth/register/ \\
  -H "Content-Type: application/json" \\
  -d '{"username":"ana","email":"ana@example.com","password":"mipassword123"}'

# 2. Login — obtener tokens
curl -X POST http://localhost:8000/api/auth/login/ \\
  -H "Content-Type: application/json" \\
  -d '{"email":"ana@example.com","password":"mipassword123"}'
# Respuesta: {"access": "eyJ...", "refresh": "eyJ..."}

# 3. Usar el access token
curl http://localhost:8000/api/__ENTITY_PLURAL__/ \\
  -H "Authorization: Bearer eyJ..."

# 4. Renovar el access token
curl -X POST http://localhost:8000/api/auth/refresh/ \\
  -H "Content-Type: application/json" \\
  -d '{"refresh":"eyJ..."}'
```

---

## Conceptos clave de Django + DRF

### ORM de Django

```python
# Crear un registro
__ENTITY_LOWER__ = __ENTITY__.objects.create(title="Mi primer __ENTITY_LOWER__", user=request.user)

# Consultar con filtros
mis___ENTITY_PLURAL__ = __ENTITY__.objects.filter(user=request.user).order_by("-created_at")

# Actualizar
__ENTITY_LOWER__.status = "completado"
__ENTITY_LOWER__.save()

# Eliminar
__ENTITY_LOWER__.delete()
```

### Comandos Django esenciales

```bash
python manage.py startapp nueva_app           # Crear nueva aplicación
python manage.py makemigrations               # Generar migraciones
python manage.py migrate                      # Aplicar migraciones
python manage.py createsuperuser              # Crear admin
python manage.py shell                        # REPL de Django
python manage.py test apps/                   # Ejecutar tests
python manage.py collectstatic                # Recolectar estáticos
```

### Admin panel de Django

El admin panel en `/admin/` está disponible automáticamente y te permite:
- Ver, crear, editar y eliminar registros de todos los modelos
- Filtrar y buscar en los datos
- Gestionar usuarios y permisos

Accede con las credenciales del superusuario que creaste con `createsuperuser`.

---

## Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Solo una aplicación
python manage.py test apps.__ENTITY_PLURAL__

# Con cobertura
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Genera informe HTML
```

---

## Despliegue

Ver `docs/deployment.md` para instrucciones completas en Railway, Fly.io o servidor propio.

---

## Próximos pasos

- [ ] Añadir más campos al modelo `__ENTITY__` en `apps/__ENTITY_PLURAL__/models.py`
- [ ] Implementar búsqueda y filtros con `django-filters`
- [ ] Añadir paginación personalizada
- [ ] Configurar CORS para el frontend (`django-cors-headers`)
- [ ] Añadir caché con Redis (`django-redis`)
- [ ] Implementar Celery para tareas asíncronas
- [ ] Configurar Sentry para monitorización de errores

---

*Generado con ❤️ por ProgresIA Studio — https://progresia.studio*
"""

_REQUIREMENTS_TXT = """Django==5.0.7
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
psycopg2-binary==2.9.9
python-decouple==3.8
django-cors-headers==4.4.0
gunicorn==22.0.0
"""

_DOCKERFILE = """FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    libpq-dev gcc \\
    && rm -rf /var/lib/apt/lists/*

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS production
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
"""

_DOCKER_COMPOSE = """services:
  app:
    build: .
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    networks:
      - __SLUG__-net

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: __SLUG___db
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev_user -d __SLUG___db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - __SLUG__-net

volumes:
  postgres_data:

networks:
  __SLUG__-net:
    driver: bridge
"""

_ENV_EXAMPLE = """DJANGO_SECRET_KEY=insecure-dev-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost 127.0.0.1

DB_NAME=__SLUG___db
DB_USER=dev_user
DB_PASSWORD=secret
DB_HOST=db
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""

_SETTINGS = """from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="insecure-dev-key-change-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost 127.0.0.1").split()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Project apps
    "apps.users",
    "apps.__ENTITY_PLURAL__",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     config("DB_NAME",     default="__SLUG___db"),
        "USER":     config("DB_USER",     default="dev_user"),
        "PASSWORD": config("DB_PASSWORD", default="secret"),
        "HOST":     config("DB_HOST",     default="localhost"),
        "PORT":     config("DB_PORT",     default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 15,
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000").split(",")
"""

_CONFIG_URLS = """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/",     admin.site.urls),
    path("api/auth/",  include("apps.users.urls")),
    path("api/",       include("apps.__ENTITY_PLURAL__.urls")),
]
"""

_WSGI = """import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
"""

_MANAGE = """#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. "
            "Asegúrate de tener el entorno virtual activado."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
"""

_USER_MODEL = """from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio   = models.TextField(blank=True, default="")

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return self.email
"""

_USER_SERIALIZERS = """from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "date_joined")
        read_only_fields = ("id", "date_joined")
"""

_USER_VIEWS = """from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user":    UserSerializer(user).data,
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
"""

_USER_URLS = """from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/",    TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("refresh/",  TokenRefreshView.as_view(), name="token-refresh"),
    path("me/",       MeView.as_view(), name="auth-me"),
]
"""

_USER_ADMIN = """from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ("email", "username", "is_staff", "date_joined")
    list_filter   = ("is_staff", "is_active")
    search_fields = ("email", "username")
    ordering      = ("-date_joined",)
"""

_ENTITY_MODEL = """from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class __ENTITY__(models.Model):
    STATUS_CHOICES = [
        ("pendiente",   "Pendiente"),
        ("en_progreso", "En progreso"),
        ("completado",  "Completado"),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="__ENTITY_PLURAL__")
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendiente")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "__ENTITY_LOWER__"
        verbose_name_plural = "__ENTITY_PLURAL__"

    def __str__(self) -> str:
        return self.title
"""

_ENTITY_SERIALIZERS = """from rest_framework import serializers
from .models import __ENTITY__


class __ENTITY__Serializer(serializers.ModelSerializer):
    class Meta:
        model = __ENTITY__
        fields = ("id", "title", "description", "status", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_status(self, value):
        allowed = ["pendiente", "en_progreso", "completado"]
        if value not in allowed:
            raise serializers.ValidationError(f"Estado inválido. Opciones: {allowed}")
        return value
"""

_ENTITY_VIEWS = """from rest_framework import permissions, viewsets
from .models import __ENTITY__
from .serializers import __ENTITY__Serializer


class __ENTITY__ViewSet(viewsets.ModelViewSet):
    serializer_class   = __ENTITY__Serializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Cada usuario solo ve sus propios registros
        return __ENTITY__.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
"""

_ENTITY_URLS = """from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import __ENTITY__ViewSet

router = DefaultRouter()
router.register(r"__ENTITY_PLURAL__", __ENTITY__ViewSet, basename="__ENTITY_LOWER__")

urlpatterns = [
    path("", include(router.urls)),
]
"""

_ENTITY_ADMIN = """from django.contrib import admin
from .models import __ENTITY__


@admin.register(__ENTITY__)
class __ENTITY__Admin(admin.ModelAdmin):
    list_display   = ("title", "status", "user", "created_at")
    list_filter    = ("status", "created_at")
    search_fields  = ("title", "description", "user__email")
    ordering       = ("-created_at",)
    raw_id_fields  = ("user",)
"""

_ENTITY_TESTS = """from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import __ENTITY__

User = get_user_model()


def create_user(email="test@example.com", password="testpass123"):
    return User.objects.create_user(username=email.split("@")[0], email=email, password=password)


def auth_header(user):
    refresh = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}


class AuthTests(APITestCase):
    def test_register(self):
        resp = self.client.post("/api/auth/register/", {
            "username": "ana", "email": "ana@test.com", "password": "testpass123"
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", resp.data)

    def test_login(self):
        create_user()
        resp = self.client.post("/api/auth/login/", {"email": "test@example.com", "password": "testpass123"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_login_wrong_password(self):
        create_user()
        resp = self.client.post("/api/auth/login/", {"email": "test@example.com", "password": "wrongpass"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class __ENTITY__Tests(APITestCase):
    def setUp(self):
        self.user    = create_user()
        self.headers = auth_header(self.user)

    def test_list___ENTITY_PLURAL__(self):
        __ENTITY__.objects.create(user=self.user, title="Test")
        resp = self.client.get("/api/__ENTITY_PLURAL__/", **self.headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(resp.data["count"], 0)

    def test_create___ENTITY_LOWER__(self):
        resp = self.client.post("/api/__ENTITY_PLURAL__/", {"title": "Nuevo", "status": "pendiente"}, **self.headers)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["title"], "Nuevo")

    def test_cannot_create_without_title(self):
        resp = self.client.post("/api/__ENTITY_PLURAL__/", {"description": "sin título"}, **self.headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_see_other_users___ENTITY_PLURAL__(self):
        other = create_user("other@example.com")
        item  = __ENTITY__.objects.create(user=other, title="De otro usuario")
        resp  = self.client.get(f"/api/__ENTITY_PLURAL__/{item.id}/", **self.headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
"""

_CI_YML = """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Django Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: secret
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DJANGO_SECRET_KEY: ci-test-secret-key
          DEBUG: "True"
          DB_NAME: test_db
          DB_USER: test_user
          DB_PASSWORD: secret
          DB_HOST: localhost
          DB_PORT: "5432"
        run: python manage.py test apps/
"""

_DOCS_ARCHITECTURE = """# Arquitectura de __NAME__

## Patrón MTV de Django

```
Petición HTTP
     ↓
config/urls.py          ← URL dispatcher (decide qué view maneja la petición)
     ↓
apps.users.urls         ← URLs de autenticación
apps.__ENTITY_PLURAL__.urls ← URLs del recurso principal (DRF Router)
     ↓
ViewSet / APIView       ← Lógica HTTP (GET, POST, PUT, DELETE)
     ↓
Serializer              ← Validación y serialización JSON ↔ Python
     ↓
Model (ORM)             ← Acceso a PostgreSQL via Django ORM
     ↓
Respuesta JSON
```

## Flujo de autenticación JWT

```
POST /api/auth/register/
  → RegisterSerializer valida campos y crea User
  → Se genera JWT (access + refresh)
  → Respuesta: { user: {...}, access: "...", refresh: "..." }

POST /api/auth/login/
  → TokenObtainPairView verifica email + password
  → Devuelve { access: "...", refresh: "..." }
  → access_token expira en 1h, refresh_token en 7 días

GET /api/__ENTITY_PLURAL__/ (con Authorization: Bearer <token>)
  → JWTAuthentication verifica el token
  → Inyecta request.user
  → ViewSet filtra por user=request.user
```

## Modelo de datos

```
users_user (AUTH_USER_MODEL)
  id           bigint PK
  email        varchar(254) UNIQUE
  username     varchar(150)
  password     varchar(128) [hash argon2/pbkdf2]
  is_active    boolean
  date_joined  timestamp

__ENTITY_PLURAL__ (__ENTITY_LOWER__)
  id           bigint PK
  user_id      bigint FK → users_user.id (CASCADE DELETE)
  title        varchar(255)
  description  text
  status       varchar(20) [pendiente|en_progreso|completado]
  created_at   timestamp (auto_now_add)
  updated_at   timestamp (auto_now)
```

## Por qué Django + DRF para este proyecto

1. **ORM maduro**: las relaciones, migraciones y consultas complejas son simples de implementar con Django ORM
2. **DRF ViewSets**: un ViewSet genera todos los endpoints CRUD con mínimo código
3. **Admin gratuito**: el panel `/admin/` es invaluable para gestionar datos en desarrollo y producción
4. **Validación automática**: los Serializers validan tipos, longitudes y unicidades sin código extra
5. **JWT robusto**: `djangorestframework-simplejwt` es la librería JWT de referencia para DRF
6. **Ecosistema**: `django-filters`, `django-redis`, `celery`, `channels` — todo está disponible como packages Django
"""


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug   = _slug(req.project_name)
    name   = req.project_name
    entity = _pascal((req.modules[0] if req.modules else req.project_name).split()[0])

    def f(path: str, lang: str, content: str) -> GeneratedFile:
        return _f(path, lang, content, slug, name, entity)

    ep  = entity.lower()

    return CodeGenerationResponse(
        project_name=name,
        files=[
            # Documentation
            f("README.md",                                           "markdown",   _README),
            f("docs/architecture.md",                               "markdown",   _DOCS_ARCHITECTURE),
            # Infrastructure
            f("Dockerfile",                                          "dockerfile", _DOCKERFILE),
            f("docker-compose.yml",                                  "yaml",       _DOCKER_COMPOSE),
            f(".env.example",                                        "dotenv",     _ENV_EXAMPLE),
            f(".github/workflows/ci.yml",                            "yaml",       _CI_YML),
            # Django root
            f("manage.py",                                           "python",     _MANAGE),
            f("requirements.txt",                                    "text",       _REQUIREMENTS_TXT),
            # Config
            f("config/__init__.py",                                  "python",     ""),
            f("config/settings.py",                                  "python",     _SETTINGS),
            f("config/urls.py",                                      "python",     _CONFIG_URLS),
            f("config/wsgi.py",                                      "python",     _WSGI),
            # Users app
            f("apps/__init__.py",                                    "python",     ""),
            f("apps/users/__init__.py",                              "python",     ""),
            f("apps/users/models.py",                                "python",     _USER_MODEL),
            f("apps/users/serializers.py",                           "python",     _USER_SERIALIZERS),
            f("apps/users/views.py",                                 "python",     _USER_VIEWS),
            f("apps/users/urls.py",                                  "python",     _USER_URLS),
            f("apps/users/admin.py",                                 "python",     _USER_ADMIN),
            # Entity app
            f(f"apps/{ep}s/__init__.py",                             "python",     ""),
            f(f"apps/{ep}s/models.py",                               "python",     _ENTITY_MODEL),
            f(f"apps/{ep}s/serializers.py",                          "python",     _ENTITY_SERIALIZERS),
            f(f"apps/{ep}s/views.py",                                "python",     _ENTITY_VIEWS),
            f(f"apps/{ep}s/urls.py",                                 "python",     _ENTITY_URLS),
            f(f"apps/{ep}s/admin.py",                                "python",     _ENTITY_ADMIN),
            f(f"apps/{ep}s/tests.py",                                "python",     _ENTITY_TESTS),
        ],
    )
