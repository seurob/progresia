"""Laravel 11 Monolith template — REST API + PostgreSQL + Docker.

Placeholders:
  __SLUG__   = kebab-case project name   (e.g. "mi-proyecto")
  __NAME__   = display project name      (e.g. "Mi Proyecto")
  __ENTITY__ = Pascal-case main entity   (e.g. "Producto")
  __ENTITY_LOWER__ = snake_case entity   (e.g. "producto")
  __ENTITY_PLURAL__ = snake_case plural  (e.g. "productos")
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

_README = """# __NAME__ — Laravel 11 REST API

> Generado por **ProgresIA Studio** · Arquitectura: Laravel Monolítico

## ¿Qué es este proyecto?

`__NAME__` es una API REST construida con **Laravel 11**, el framework PHP más popular del mundo.
Esta guía te enseñará cómo funciona cada parte del proyecto y cómo empezar a desarrollar.

---

## Stack tecnológico

| Tecnología | Versión | Propósito | Documentación |
|-----------|---------|-----------|---------------|
| Laravel | 11.x | Framework PHP backend MVC + API | https://laravel.com/docs/11.x |
| Laravel Sanctum | 4.x | Autenticación con tokens Bearer | https://laravel.com/docs/11.x/sanctum |
| PostgreSQL | 16 | Base de datos relacional | https://www.postgresql.org/docs/16/ |
| PHP | 8.3 | Lenguaje de programación | https://www.php.net/docs.php |
| Docker | 26.x | Contenerización | https://docs.docker.com/ |
| nginx | 1.25 | Proxy inverso | https://nginx.org/en/docs/ |

---

## Arquitectura del proyecto

```
__SLUG__/
├── app/
│   ├── Http/
│   │   ├── Controllers/
│   │   │   └── Api/
│   │   │       ├── AuthController.php     ← registro, login, logout
│   │   │       └── __ENTITY__Controller.php ← CRUD de __ENTITY_PLURAL__
│   │   ├── Requests/
│   │   │   └── Auth/                      ← validación de formularios
│   │   └── Resources/
│   │       └── UserResource.php           ← transformación JSON de respuestas
│   └── Models/
│       ├── User.php                       ← modelo usuario (Eloquent)
│       └── __ENTITY__.php                 ← modelo principal del proyecto
├── database/
│   ├── migrations/                        ← historial de cambios en la BD
│   └── seeders/                          ← datos de prueba
├── routes/
│   └── api.php                           ← endpoints de la API
├── tests/
│   └── Feature/                          ← tests de integración
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md                             ← este archivo
```

### ¿Por qué esta arquitectura?

**MVC (Model-View-Controller)** separa la lógica en tres capas:

- **Model** (`app/Models/`): Representa los datos y la lógica de negocio. Eloquent ORM mapea las tablas de la base de datos a objetos PHP.
- **View**: En una API REST no hay vistas HTML; los "Resources" de Laravel formatean los datos como JSON.
- **Controller** (`app/Http/Controllers/`): Recibe las peticiones HTTP, llama a los modelos y devuelve la respuesta.

---

## Instalación rápida (5 minutos)

### Opción A: Con Docker (recomendado)

```bash
# 1. Clonar el proyecto
git clone <tu-repo> __SLUG__
cd __SLUG__

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Levantar todos los servicios
docker compose up --build

# 4. Ejecutar migraciones y seed (en otra terminal)
docker compose exec app php artisan migrate --seed

# 5. ¡Listo! La API está en:
# http://localhost:8000/api
```

### Opción B: Sin Docker (desarrollo local)

```bash
# Requisitos: PHP 8.3+, Composer, PostgreSQL 16

# 1. Instalar dependencias PHP
composer install

# 2. Configurar entorno
cp .env.example .env
php artisan key:generate

# 3. Crear la base de datos y ejecutar migraciones
php artisan migrate --seed

# 4. Generar clave de Sanctum
php artisan vendor:publish --provider="Laravel\\Sanctum\\SanctumServiceProvider"

# 5. Iniciar servidor de desarrollo
php artisan serve
# API disponible en: http://localhost:8000/api
```

---

## Endpoints de la API

### Autenticación

| Método | Endpoint | Descripción | Auth requerida |
|--------|----------|-------------|----------------|
| `POST` | `/api/register` | Crear cuenta nueva | No |
| `POST` | `/api/login` | Iniciar sesión (devuelve token) | No |
| `POST` | `/api/logout` | Cerrar sesión (invalida token) | Sí |
| `GET` | `/api/user` | Perfil del usuario autenticado | Sí |

### __ENTITY_PLURAL__ (recurso principal)

| Método | Endpoint | Descripción | Auth requerida |
|--------|----------|-------------|----------------|
| `GET` | `/api/__ENTITY_PLURAL__` | Listar todos | Sí |
| `POST` | `/api/__ENTITY_PLURAL__` | Crear nuevo | Sí |
| `GET` | `/api/__ENTITY_PLURAL__/{id}` | Ver detalle | Sí |
| `PUT` | `/api/__ENTITY_PLURAL__/{id}` | Actualizar | Sí |
| `DELETE` | `/api/__ENTITY_PLURAL__/{id}` | Eliminar | Sí |

### Cómo usar la autenticación

```bash
# 1. Registrar usuario
curl -X POST http://localhost:8000/api/register \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Ana García","email":"ana@example.com","password":"password123","password_confirmation":"password123"}'

# Respuesta: {"token": "1|abc123...", "user": {...}}

# 2. Usar el token en peticiones protegidas
curl http://localhost:8000/api/__ENTITY_PLURAL__ \\
  -H "Authorization: Bearer 1|abc123..."
```

---

## Conceptos clave de Laravel

### Eloquent ORM

Eloquent mapea tablas de base de datos a clases PHP. En lugar de escribir SQL:

```php
// Sin Eloquent (SQL puro):
$result = DB::select("SELECT * FROM __ENTITY_PLURAL__ WHERE user_id = ?", [$userId]);

// Con Eloquent (más legible y seguro):
$__ENTITY_PLURAL__ = __ENTITY__::where('user_id', $userId)->get();
```

### Migraciones

Las migraciones son la "historia" de tu base de datos, versionada en Git:

```bash
# Crear una nueva migración:
php artisan make:migration add_status_to___ENTITY_PLURAL___table

# Ejecutar migraciones pendientes:
php artisan migrate

# Deshacer la última migración:
php artisan migrate:rollback
```

### Artisan CLI

Laravel incluye una potente CLI para generar código:

```bash
php artisan make:model Product -m        # Modelo + migración
php artisan make:controller ProductController --resource  # Controller REST
php artisan make:request StoreProductRequest  # Clase de validación
php artisan make:resource ProductResource     # Transformador JSON
php artisan route:list                        # Ver todos los endpoints
php artisan tinker                            # REPL interactivo de PHP
```

---

## Seguridad

- **Tokens Bearer**: Sanctum genera tokens personales para cada usuario. Nunca se almacenan en texto plano.
- **Validación**: Todas las entradas se validan con `FormRequest` antes de llegar al controlador.
- **Autorización**: Las rutas bajo `auth:sanctum` solo son accesibles con un token válido.
- **CORS**: Configurado en `config/cors.php` para permitir solo los orígenes autorizados.
- **Variables sensibles**: Todas en `.env`, nunca en el código fuente.

---

## Testing

```bash
# Ejecutar todos los tests
php artisan test

# O con PHPUnit directamente
./vendor/bin/phpunit

# Ver cobertura de código
./vendor/bin/phpunit --coverage-html coverage/
```

---

## Despliegue en producción

Ver `docs/deployment.md` para instrucciones completas de despliegue en Railway, Fly.io o un servidor propio.

---

## Próximos pasos

- [ ] Añadir más campos al modelo `__ENTITY__` según las necesidades del proyecto
- [ ] Implementar paginación en el endpoint de listado
- [ ] Añadir búsqueda y filtros en los endpoints de listado
- [ ] Configurar emails con Mailpit (desarrollo) y SMTP (producción)
- [ ] Añadir roles y permisos con Laravel Permission (Spatie)
- [ ] Implementar caché con Redis para mejorar el rendimiento
- [ ] Configurar CI/CD con GitHub Actions (ver `.github/workflows/ci.yml`)

---

*Generado con ❤️ por ProgresIA Studio — https://progresia.studio*
"""

_COMPOSER_JSON = """{
  "name": "__SLUG__/api",
  "description": "__NAME__ — Laravel 11 REST API",
  "type": "project",
  "keywords": ["laravel", "framework"],
  "license": "MIT",
  "require": {
    "php": "^8.3",
    "laravel/framework": "^11.0",
    "laravel/sanctum": "^4.0",
    "laravel/tinker": "^2.9"
  },
  "require-dev": {
    "fakerphp/faker": "^1.23",
    "laravel/pint": "^1.13",
    "laravel/sail": "^1.26",
    "mockery/mockery": "^1.6",
    "nunomaduro/collision": "^8.0",
    "phpunit/phpunit": "^11.0"
  },
  "autoload": {
    "psr-4": {
      "App\\\\": "app/",
      "Database\\\\Factories\\\\": "database/factories/",
      "Database\\\\Seeders\\\\": "database/seeders/"
    }
  },
  "autoload-dev": {
    "psr-4": {
      "Tests\\\\": "tests/"
    }
  },
  "scripts": {
    "post-autoload-dump": [
      "Illuminate\\\\Foundation\\\\ComposerScripts::postAutoloadDump",
      "@php artisan package:discover --ansi"
    ],
    "post-update-cmd": [
      "@php artisan vendor:publish --tag=laravel-assets --ansi --force"
    ],
    "post-root-package-install": [
      "@php -r \\"file_exists('.env') || copy('.env.example', '.env');\\"",
      "@php artisan key:generate --ansi"
    ],
    "post-create-project-cmd": [
      "@php artisan key:generate --ansi",
      "@php -r \\"file_exists('database/database.sqlite') || touch('database/database.sqlite');\\"",
      "@php artisan migrate --graceful --ansi"
    ]
  },
  "extra": {
    "laravel": {
      "dont-discover": []
    }
  },
  "config": {
    "optimize-autoloader": true,
    "preferred-install": "dist",
    "sort-packages": true,
    "allow-plugins": {
      "pestphp/pest-plugin": true,
      "php-http/discovery": true
    }
  },
  "minimum-stability": "stable",
  "prefer-stable": true
}
"""

_DOCKERFILE = """FROM php:8.3-fpm-alpine AS base

RUN apk add --no-cache \\
    postgresql-dev \\
    libzip-dev \\
    zip \\
    unzip \\
    && docker-php-ext-install pdo pdo_pgsql zip opcache

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

FROM base AS deps
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --no-autoloader --prefer-dist

FROM base AS production
COPY --from=deps /var/www/html/vendor ./vendor
COPY . .
RUN composer dump-autoload --optimize \\
    && php artisan config:cache \\
    && php artisan route:cache \\
    && chown -R www-data:www-data storage bootstrap/cache

EXPOSE 9000
CMD ["php-fpm"]
"""

_DOCKER_COMPOSE = """services:
  app:
    build: .
    restart: unless-stopped
    volumes:
      - .:/var/www/html
    environment:
      - APP_ENV=local
      - APP_DEBUG=true
    depends_on:
      db:
        condition: service_healthy
    networks:
      - __SLUG__-net

  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "8000:80"
    volumes:
      - .:/var/www/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - app
    networks:
      - __SLUG__-net

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: __SLUG___db
      POSTGRES_USER: __SLUG___user
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U __SLUG___user -d __SLUG___db"]
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

_NGINX_CONF = """server {
    listen 80;
    server_name _;
    root /var/www/html/public;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \\.php$ {
        fastcgi_pass app:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\\.ht {
        deny all;
    }
}
"""

_ENV_EXAMPLE = """APP_NAME=__NAME__
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost:8000

LOG_CHANNEL=stack
LOG_DEPRECATIONS_CHANNEL=null
LOG_LEVEL=debug

DB_CONNECTION=pgsql
DB_HOST=db
DB_PORT=5432
DB_DATABASE=__SLUG___db
DB_USERNAME=__SLUG___user
DB_PASSWORD=secret

BCRYPT_ROUNDS=12

CACHE_STORE=file
SESSION_DRIVER=file
QUEUE_CONNECTION=sync

SANCTUM_STATEFUL_DOMAINS=localhost:3000,127.0.0.1:3000
"""

_BOOTSTRAP_APP = """<?php

use Illuminate\\Foundation\\Application;
use Illuminate\\Foundation\\Configuration\\Exceptions;
use Illuminate\\Foundation\\Configuration\\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        api: __DIR__.'/../routes/api.php',
        apiPrefix: 'api',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->api(prepend: [
            \\Laravel\\Sanctum\\Http\\Middleware\\EnsureFrontendRequestsAreStateful::class,
        ]);

        $middleware->alias([
            'verified' => \\Illuminate\\Auth\\Middleware\\EnsureEmailIsVerified::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions) {
        //
    })->create();
"""

_BOOTSTRAP_PROVIDERS = """<?php

return [
    App\\Providers\\AppServiceProvider::class,
];
"""

_ROUTES_API = """<?php

use App\\Http\\Controllers\\Api\\AuthController;
use App\\Http\\Controllers\\Api\\__ENTITY__Controller;
use Illuminate\\Http\\Request;
use Illuminate\\Support\\Facades\\Route;

// ── Rutas públicas (sin autenticación) ────────────────────────────────────────

Route::post('/register', [AuthController::class, 'register']);
Route::post('/login', [AuthController::class, 'login']);

// ── Rutas protegidas (requieren token Bearer de Sanctum) ──────────────────────

Route::middleware('auth:sanctum')->group(function () {
    // Auth
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/user', [AuthController::class, 'me']);

    // CRUD de __ENTITY_PLURAL__
    Route::apiResource('__ENTITY_PLURAL__', __ENTITY__Controller::class);
});
"""

_MODEL_USER = """<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Relations\\HasMany;
use Illuminate\\Foundation\\Auth\\User as Authenticatable;
use Illuminate\\Notifications\\Notifiable;
use Laravel\\Sanctum\\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    protected $fillable = [
        'name',
        'email',
        'password',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
        ];
    }

    public function __ENTITY_PLURAL__(): HasMany
    {
        return $this->hasMany(__ENTITY__::class);
    }
}
"""

_MODEL_ENTITY = """<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Database\\Eloquent\\Relations\\BelongsTo;

class __ENTITY__ extends Model
{
    use HasFactory;

    protected $fillable = [
        'title',
        'description',
        'status',
        'user_id',
    ];

    protected function casts(): array
    {
        return [
            'created_at' => 'datetime',
            'updated_at' => 'datetime',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
"""

_CONTROLLER_AUTH = """<?php

namespace App\\Http\\Controllers\\Api;

use App\\Http\\Controllers\\Controller;
use App\\Http\\Requests\\Auth\\LoginRequest;
use App\\Http\\Requests\\Auth\\RegisterRequest;
use App\\Http\\Resources\\UserResource;
use App\\Models\\User;
use Illuminate\\Http\\JsonResponse;
use Illuminate\\Http\\Request;

class AuthController extends Controller
{
    public function register(RegisterRequest $request): JsonResponse
    {
        $user = User::create($request->validated());

        $token = $user->createToken('api-token')->plainTextToken;

        return response()->json([
            'user'  => new UserResource($user),
            'token' => $token,
        ], 201);
    }

    public function login(LoginRequest $request): JsonResponse
    {
        if (! auth()->attempt($request->only('email', 'password'))) {
            return response()->json(['message' => 'Credenciales incorrectas.'], 401);
        }

        $user = User::where('email', $request->email)->firstOrFail();
        $token = $user->createToken('api-token')->plainTextToken;

        return response()->json([
            'user'  => new UserResource($user),
            'token' => $token,
        ]);
    }

    public function logout(Request $request): JsonResponse
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => 'Sesión cerrada correctamente.']);
    }

    public function me(Request $request): UserResource
    {
        return new UserResource($request->user());
    }
}
"""

_CONTROLLER_ENTITY = """<?php

namespace App\\Http\\Controllers\\Api;

use App\\Http\\Controllers\\Controller;
use App\\Models\\__ENTITY__;
use Illuminate\\Http\\JsonResponse;
use Illuminate\\Http\\Request;
use Illuminate\\Http\\Resources\\Json\\JsonResource;

class __ENTITY__Controller extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $items = __ENTITY__::where('user_id', $request->user()->id)
            ->latest()
            ->paginate(15);

        return response()->json($items);
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'title'       => 'required|string|max:255',
            'description' => 'nullable|string|max:2000',
            'status'      => 'nullable|string|in:pendiente,en_progreso,completado',
        ]);

        $item = $request->user()->__ENTITY_PLURAL__()->create($validated);

        return response()->json($item, 201);
    }

    public function show(Request $request, __ENTITY__ $__ENTITY_LOWER__): JsonResponse
    {
        $this->authorize('view', $__ENTITY_LOWER__);

        return response()->json($__ENTITY_LOWER__);
    }

    public function update(Request $request, __ENTITY__ $__ENTITY_LOWER__): JsonResponse
    {
        $this->authorize('update', $__ENTITY_LOWER__);

        $validated = $request->validate([
            'title'       => 'sometimes|string|max:255',
            'description' => 'nullable|string|max:2000',
            'status'      => 'nullable|string|in:pendiente,en_progreso,completado',
        ]);

        $__ENTITY_LOWER__->update($validated);

        return response()->json($__ENTITY_LOWER__);
    }

    public function destroy(Request $request, __ENTITY__ $__ENTITY_LOWER__): JsonResponse
    {
        $this->authorize('delete', $__ENTITY_LOWER__);

        $__ENTITY_LOWER__->delete();

        return response()->json(null, 204);
    }
}
"""

_REQUEST_REGISTER = """<?php

namespace App\\Http\\Requests\\Auth;

use Illuminate\\Foundation\\Http\\FormRequest;

class RegisterRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'name'     => ['required', 'string', 'max:255'],
            'email'    => ['required', 'string', 'email', 'max:255', 'unique:users'],
            'password' => ['required', 'string', 'min:8', 'confirmed'],
        ];
    }

    public function messages(): array
    {
        return [
            'name.required'      => 'El nombre es obligatorio.',
            'email.required'     => 'El email es obligatorio.',
            'email.unique'       => 'Este email ya está registrado.',
            'password.min'       => 'La contraseña debe tener al menos 8 caracteres.',
            'password.confirmed' => 'Las contraseñas no coinciden.',
        ];
    }
}
"""

_REQUEST_LOGIN = """<?php

namespace App\\Http\\Requests\\Auth;

use Illuminate\\Foundation\\Http\\FormRequest;

class LoginRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'email'    => ['required', 'string', 'email'],
            'password' => ['required', 'string'],
        ];
    }
}
"""

_RESOURCE_USER = """<?php

namespace App\\Http\\Resources;

use Illuminate\\Http\\Request;
use Illuminate\\Http\\Resources\\Json\\JsonResource;

class UserResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id'         => $this->id,
            'name'       => $this->name,
            'email'      => $this->email,
            'created_at' => $this->created_at->toIso8601String(),
        ];
    }
}
"""

_MIGRATION_USERS = """<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('users', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('email')->unique();
            $table->timestamp('email_verified_at')->nullable();
            $table->string('password');
            $table->rememberToken();
            $table->timestamps();
        });

        Schema::create('personal_access_tokens', function (Blueprint $table) {
            $table->id();
            $table->morphs('tokenable');
            $table->string('name');
            $table->string('token', 64)->unique();
            $table->text('abilities')->nullable();
            $table->timestamp('last_used_at')->nullable();
            $table->timestamp('expires_at')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('personal_access_tokens');
        Schema::dropIfExists('users');
    }
};
"""

_MIGRATION_ENTITY = """<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('__ENTITY_PLURAL__', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('title');
            $table->text('description')->nullable();
            $table->string('status')->default('pendiente');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('__ENTITY_PLURAL__');
    }
};
"""

_SEEDER = """<?php

namespace Database\\Seeders;

use App\\Models\\User;
use App\\Models\\__ENTITY__;
use Illuminate\\Database\\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        // Usuario de prueba (demo)
        $demo = User::firstOrCreate(
            ['email' => 'demo@__SLUG__.local'],
            [
                'name'     => 'Usuario Demo',
                'password' => bcrypt('password'),
            ]
        );

        // Datos de ejemplo
        if ($demo->__ENTITY_PLURAL__()->count() === 0) {
            $demo->__ENTITY_PLURAL__()->createMany([
                ['title' => 'Primer __ENTITY_LOWER__ de ejemplo',  'description' => 'Este es el primer registro creado automáticamente.',  'status' => 'completado'],
                ['title' => 'Segundo __ENTITY_LOWER__ de prueba', 'description' => 'Modifica estos datos según las necesidades de tu proyecto.', 'status' => 'en_progreso'],
                ['title' => 'Tercer __ENTITY_LOWER__',            'description' => 'Puedes añadir más campos en la migración correspondiente.', 'status' => 'pendiente'],
            ]);
        }

        $this->command->info('✅ Seed completado: 1 usuario demo + 3 __ENTITY_PLURAL__');
        $this->command->info('   Email: demo@__SLUG__.local');
        $this->command->info('   Password: password');
    }
}
"""

_TEST_AUTH = """<?php

namespace Tests\\Feature;

use App\\Models\\User;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

class AuthTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_register(): void
    {
        $response = $this->postJson('/api/register', [
            'name'                  => 'Test User',
            'email'                 => 'test@example.com',
            'password'              => 'password123',
            'password_confirmation' => 'password123',
        ]);

        $response->assertStatus(201)
            ->assertJsonStructure(['user' => ['id', 'name', 'email'], 'token']);
    }

    public function test_user_can_login(): void
    {
        $user = User::factory()->create(['password' => bcrypt('password123')]);

        $response = $this->postJson('/api/login', [
            'email'    => $user->email,
            'password' => 'password123',
        ]);

        $response->assertOk()
            ->assertJsonStructure(['user', 'token']);
    }

    public function test_login_fails_with_wrong_credentials(): void
    {
        $response = $this->postJson('/api/login', [
            'email'    => 'nobody@example.com',
            'password' => 'wrong',
        ]);

        $response->assertStatus(401);
    }

    public function test_authenticated_user_can_get_profile(): void
    {
        $user  = User::factory()->create();
        $token = $user->createToken('test')->plainTextToken;

        $this->withToken($token)
            ->getJson('/api/user')
            ->assertOk()
            ->assertJsonPath('email', $user->email);
    }

    public function test_user_can_logout(): void
    {
        $user  = User::factory()->create();
        $token = $user->createToken('test')->plainTextToken;

        $this->withToken($token)
            ->postJson('/api/logout')
            ->assertOk();
    }
}
"""

_TEST_API = """<?php

namespace Tests\\Feature;

use App\\Models\\User;
use App\\Models\\__ENTITY__;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

class ApiTest extends TestCase
{
    use RefreshDatabase;

    private User $user;
    private string $token;

    protected function setUp(): void
    {
        parent::setUp();
        $this->user  = User::factory()->create();
        $this->token = $this->user->createToken('test')->plainTextToken;
    }

    public function test_can_list___ENTITY_PLURAL__(): void
    {
        __ENTITY__::factory()->count(3)->create(['user_id' => $this->user->id]);

        $this->withToken($this->token)
            ->getJson('/api/__ENTITY_PLURAL__')
            ->assertOk()
            ->assertJsonStructure(['data', 'total']);
    }

    public function test_can_create___ENTITY_LOWER__(): void
    {
        $this->withToken($this->token)
            ->postJson('/api/__ENTITY_PLURAL__', [
                'title'       => 'Nuevo __ENTITY_LOWER__',
                'description' => 'Descripción de prueba',
                'status'      => 'pendiente',
            ])
            ->assertStatus(201)
            ->assertJsonPath('title', 'Nuevo __ENTITY_LOWER__');
    }

    public function test_cannot_create___ENTITY_LOWER___without_title(): void
    {
        $this->withToken($this->token)
            ->postJson('/api/__ENTITY_PLURAL__', ['description' => 'Sin título'])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['title']);
    }

    public function test_cannot_access_other_users___ENTITY_PLURAL__(): void
    {
        $other = User::factory()->create();
        $item  = __ENTITY__::factory()->create(['user_id' => $other->id]);

        $this->withToken($this->token)
            ->getJson("/api/__ENTITY_PLURAL__/{$item->id}")
            ->assertForbidden();
    }
}
"""

_PHPUNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="vendor/autoload.php"
         colors="true">
    <testsuites>
        <testsuite name="Feature">
            <directory suffix="Test.php">./tests/Feature</directory>
        </testsuite>
    </testsuites>
    <php>
        <env name="APP_ENV" value="testing"/>
        <env name="BCRYPT_ROUNDS" value="4"/>
        <env name="CACHE_STORE" value="array"/>
        <env name="DB_CONNECTION" value="pgsql"/>
        <env name="DB_DATABASE" value="__SLUG___test"/>
        <env name="SESSION_DRIVER" value="array"/>
        <env name="MAIL_MAILER" value="array"/>
        <env name="QUEUE_CONNECTION" value="sync"/>
    </php>
</phpunit>
"""

_CI_YML = """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: PHP ${{ matrix.php }} Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: __SLUG___test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: secret
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    strategy:
      matrix:
        php: ['8.3']

    steps:
      - uses: actions/checkout@v4

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}
          extensions: pdo, pdo_pgsql, zip
          coverage: none

      - name: Install dependencies
        run: composer install --prefer-dist --no-progress

      - name: Copy environment
        run: |
          cp .env.example .env
          php artisan key:generate

      - name: Run migrations
        run: php artisan migrate --force
        env:
          DB_HOST: localhost
          DB_DATABASE: __SLUG___test
          DB_USERNAME: test_user
          DB_PASSWORD: secret

      - name: Run tests
        run: php artisan test
        env:
          DB_HOST: localhost
          DB_DATABASE: __SLUG___test
          DB_USERNAME: test_user
          DB_PASSWORD: secret
"""

_DOCS_ARCHITECTURE = """# Arquitectura de __NAME__

## Patrón MVC en Laravel

```
Petición HTTP
     ↓
routes/api.php          ← Define qué controlador maneja cada URL
     ↓
app/Http/Requests/      ← Valida los datos de entrada
     ↓
app/Http/Controllers/   ← Lógica de la petición
     ↓
app/Models/             ← Acceso a la base de datos (Eloquent ORM)
     ↓
app/Http/Resources/     ← Formatea la respuesta JSON
     ↓
Respuesta JSON
```

## Por qué Laravel para este proyecto

1. **Productividad alta**: Eloquent ORM, migraciones, seeders, Artisan CLI y generadores de código reducen el tiempo de desarrollo significativamente.

2. **Autenticación madura**: Laravel Sanctum proporciona tokens Bearer con invalidación, scopes y expiración sin configuración compleja.

3. **Validación robusta**: Las clases `FormRequest` centralizan la validación y devuelven errores 422 automáticamente en el formato JSON estándar.

4. **Testing integrado**: PHPUnit + helpers de Laravel (`RefreshDatabase`, `withToken`, `assertJsonPath`) permiten tests de integración rápidos.

## Flujo de autenticación con Sanctum

```
POST /api/login
  → LoginRequest valida email + password
  → AuthController verifica credenciales con auth()->attempt()
  → Crea token: $user->createToken('api-token')->plainTextToken
  → Devuelve { user: {...}, token: "1|abc123..." }

GET /api/__ENTITY_PLURAL__ (con Bearer token)
  → Middleware auth:sanctum verifica el token en la cabecera Authorization
  → Inyecta $request->user() con el usuario autenticado
  → El controlador filtra por user_id para aislar los datos de cada usuario
```

## Modelo de datos

```
users
  id              bigint PK
  name            varchar(255)
  email           varchar(255) UNIQUE
  email_verified_at  timestamp NULL
  password        varchar(255) [hash bcrypt]
  remember_token  varchar(100) NULL
  created_at      timestamp
  updated_at      timestamp

__ENTITY_PLURAL__
  id              bigint PK
  user_id         bigint FK → users.id (CASCADE DELETE)
  title           varchar(255)
  description     text NULL
  status          varchar [pendiente|en_progreso|completado]
  created_at      timestamp
  updated_at      timestamp
```

## Escalabilidad

Para escalar este monolito cuando crezca el tráfico:

1. **Horizontal scaling**: Múltiples instancias PHP-FPM detrás de nginx con load balancer
2. **Caché**: Añadir Redis con `CACHE_STORE=redis` para respuestas frecuentes
3. **Queues**: Usar `QUEUE_CONNECTION=redis` para procesar tareas pesadas en background
4. **Read replicas**: PostgreSQL permite replicas de solo lectura para distribuir la carga
5. **Separar frontend**: Si el frontend crece, extraerlo a un proyecto React/Next.js separado
"""

_DOCS_DEPLOYMENT = """# Guía de despliegue — __NAME__

## Railway (recomendado para MVPs)

Railway detecta automáticamente el `Dockerfile` y despliega con un clic.

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Crear proyecto y desplegar
railway init
railway up

# 4. Añadir base de datos PostgreSQL desde el dashboard de Railway

# 5. Configurar variables de entorno en Railway dashboard:
#    APP_KEY, DB_CONNECTION, DB_HOST, DB_DATABASE, DB_USERNAME, DB_PASSWORD
```

## Fly.io

```bash
# 1. Instalar flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login y crear app
fly auth login
fly launch

# 3. Crear PostgreSQL
fly postgres create --name __SLUG__-db

# 4. Attach BD al proyecto
fly postgres attach __SLUG__-db

# 5. Desplegar
fly deploy
```

## Servidor propio (VPS)

```bash
# En el servidor (Ubuntu 24.04):
apt install docker.io docker-compose-v2

# Clonar el proyecto
git clone <tu-repo> /opt/__SLUG__
cd /opt/__SLUG__

# Configurar entorno de producción
cp .env.example .env
# Editar .env: APP_ENV=production, APP_DEBUG=false, credenciales de BD reales

# Levantar servicios
docker compose up -d --build

# Ejecutar migraciones
docker compose exec app php artisan migrate --force

# Configurar SSL con Certbot (si tienes dominio propio)
apt install certbot python3-certbot-nginx
certbot --nginx -d tu-dominio.com
```

## Variables de entorno para producción

```bash
APP_ENV=production
APP_DEBUG=false
APP_KEY=base64:...  # Generado con php artisan key:generate
APP_URL=https://tu-dominio.com

DB_CONNECTION=pgsql
DB_HOST=<host-de-produccion>
DB_PORT=5432
DB_DATABASE=<nombre-bd>
DB_USERNAME=<usuario>
DB_PASSWORD=<contraseña-segura>

SANCTUM_STATEFUL_DOMAINS=tu-dominio.com
```
"""


def build(req: CodeGenerationRequest) -> CodeGenerationResponse:
    slug = _slug(req.project_name)
    name = req.project_name
    entity = _pascal((req.modules[0] if req.modules else req.project_name).split()[0])

    def f(path: str, lang: str, content: str) -> GeneratedFile:
        return _f(path, lang, content, slug, name, entity)

    return CodeGenerationResponse(
        project_name=name,
        files=[
            # Documentation
            f("README.md",                                          "markdown",   _README),
            f("docs/architecture.md",                              "markdown",   _DOCS_ARCHITECTURE),
            f("docs/deployment.md",                                "markdown",   _DOCS_DEPLOYMENT),
            # Infrastructure
            f("Dockerfile",                                         "dockerfile", _DOCKERFILE),
            f("docker-compose.yml",                                 "yaml",       _DOCKER_COMPOSE),
            f("nginx.conf",                                         "nginx",      _NGINX_CONF),
            f(".env.example",                                       "dotenv",     _ENV_EXAMPLE),
            f(".github/workflows/ci.yml",                           "yaml",       _CI_YML),
            # Laravel bootstrap
            f("bootstrap/app.php",                                  "php",        _BOOTSTRAP_APP),
            f("bootstrap/providers.php",                            "php",        _BOOTSTRAP_PROVIDERS),
            # Routes
            f("routes/api.php",                                     "php",        _ROUTES_API),
            # Models
            f("app/Models/User.php",                                "php",        _MODEL_USER),
            f(f"app/Models/{entity}.php",                           "php",        _MODEL_ENTITY),
            # Controllers
            f("app/Http/Controllers/Api/AuthController.php",        "php",        _CONTROLLER_AUTH),
            f(f"app/Http/Controllers/Api/{entity}Controller.php",   "php",        _CONTROLLER_ENTITY),
            # Requests
            f("app/Http/Requests/Auth/RegisterRequest.php",         "php",        _REQUEST_REGISTER),
            f("app/Http/Requests/Auth/LoginRequest.php",            "php",        _REQUEST_LOGIN),
            # Resources
            f("app/Http/Resources/UserResource.php",                "php",        _RESOURCE_USER),
            # Database
            f("database/migrations/0001_create_users_table.php",    "php",        _MIGRATION_USERS),
            f(f"database/migrations/0002_create_{slug}_table.php",  "php",        _MIGRATION_ENTITY),
            f("database/seeders/DatabaseSeeder.php",                "php",        _SEEDER),
            # Composer
            f("composer.json",                                      "json",       _COMPOSER_JSON),
            # Tests
            f("tests/Feature/AuthTest.php",                         "php",        _TEST_AUTH),
            f("tests/Feature/ApiTest.php",                          "php",        _TEST_API),
            f("phpunit.xml",                                        "xml",        _PHPUNIT_XML),
        ],
    )
