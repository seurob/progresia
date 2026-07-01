"""Laravel 11 + PHP 8.3 + MySQL/PostgreSQL + API REST scaffold generator."""
from datetime import datetime
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_laravel(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Laravel 11 completo."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    files: list[GeneratedFile] = [
        _composer_json(project_slug),
        _entity_model(entity_slug_name, entity_pascal_name, entity_plural),
        _entity_controller(entity_slug_name, entity_pascal_name, entity_plural),
        _store_request(entity_slug_name, entity_pascal_name),
        _entity_resource(entity_slug_name, entity_pascal_name),
        _migration(entity_plural, timestamp),
        _entity_seeder(entity_slug_name, entity_pascal_name, entity_plural),
        _database_seeder(entity_pascal_name),
        _api_routes(entity_slug_name, entity_pascal_name, entity_plural),
        _web_routes(),
        _welcome_blade(req.project_name, req.modules),
        _bootstrap_app(entity_slug_name, entity_pascal_name),
        _env_example(project_slug),
        _gitignore(),
        generate_readme(
            req,
            stack_summary="Laravel 11 · PHP 8.3 · PostgreSQL · REST API",
            prerequisites=[
                "PHP 8.3+ — https://php.net",
                "Composer — https://getcomposer.org",
                "Docker Desktop 4.x — https://docker.com/products/docker-desktop",
                "Git 2.x — https://git-scm.com",
            ],
            setup_commands=[
                "composer install",
                "php artisan key:generate",
                "docker compose up -d",
                "php artisan migrate --seed",
                "php artisan serve",
            ],
            env_vars=[
                ("DB_CONNECTION", "pgsql"),
                ("DB_HOST", "127.0.0.1"),
                ("DB_DATABASE", project_slug + "_db"),
                ("DB_USERNAME", project_slug),
                ("DB_PASSWORD", project_slug),
            ],
            api_port=8000,
        ),
        _laravel_dockerfile(),
        _laravel_docker_compose(project_slug),
    ]

    return files


def _composer_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
    "name": "{project_slug}/{project_slug}",
    "type": "project",
    "description": "MVP generado con ProgresIA Studio",
    "require": {{
        "php": "^8.3",
        "laravel/framework": "^11.0",
        "laravel/sanctum": "^4.0"
    }},
    "require-dev": {{
        "fakerphp/faker": "^1.23",
        "laravel/pint": "^1.0",
        "phpunit/phpunit": "^11.0"
    }},
    "autoload": {{
        "psr-4": {{
            "App\\\\": "app/",
            "Database\\\\Factories\\\\": "database/factories/",
            "Database\\\\Seeders\\\\": "database/seeders/"
        }}
    }},
    "autoload-dev": {{
        "psr-4": {{
            "Tests\\\\": "tests/"
        }}
    }},
    "scripts": {{
        "post-autoload-dump": [
            "Illuminate\\\\Foundation\\\\ComposerScripts::postAutoloadDump",
            "@php artisan package:discover --ansi"
        ]
    }},
    "config": {{
        "optimize-autoloader": true,
        "preferred-install": "dist",
        "sort-packages": true
    }},
    "minimum-stability": "stable",
    "prefer-stable": true
}}
"""
    return GeneratedFile(path="composer.json", language="json", content=content)


def _entity_model(entity_slug: str, entity_pascal: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Support\\Str;

/**
 * Modelo Eloquent para {entity_pascal}
 */
class {entity_pascal} extends Model
{{
    use HasFactory;

    protected $table = '{entity_plural}';

    /**
     * Atributos que se pueden asignar masivamente.
     */
    protected $fillable = [
        'name',
        'description',
        'status',
    ];

    /**
     * Casts de atributos a tipos nativos de PHP.
     */
    protected $casts = [
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];

    /**
     * Valores por defecto de los atributos.
     */
    protected $attributes = [
        'status' => 'active',
    ];

    /**
     * Generar UUID antes de crear el registro.
     */
    protected static function boot()
    {{
        parent::boot();
        static::creating(function ($model) {{
            if (empty($model->id)) {{
                $model->id = Str::uuid()->toString();
            }}
        }});
    }}

    public $incrementing = false;
    protected $keyType = 'string';
}}
"""
    return GeneratedFile(path=f"app/Models/{entity_pascal}.php", language="php", content=content)


def _entity_controller(entity_slug: str, entity_pascal: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
<?php

namespace App\\Http\\Controllers\\Api;

use App\\Http\\Controllers\\Controller;
use App\\Http\\Requests\\Store{entity_pascal}Request;
use App\\Http\\Resources\\{entity_pascal}Resource;
use App\\Models\\{entity_pascal};
use Illuminate\\Http\\Request;

/**
 * Controlador REST para {entity_pascal}
 * Maneja CRUD completo vía API JSON
 */
class {entity_pascal}Controller extends Controller
{{
    /**
     * Listar todos los registros
     * GET /api/{entity_plural}
     */
    public function index()
    {{
        $items = {entity_pascal}::orderByDesc('created_at')->paginate(20);
        return {entity_pascal}Resource::collection($items);
    }}

    /**
     * Crear un nuevo registro
     * POST /api/{entity_plural}
     */
    public function store(Store{entity_pascal}Request $request)
    {{
        $item = {entity_pascal}::create($request->validated());
        return new {entity_pascal}Resource($item);
    }}

    /**
     * Mostrar un registro por ID
     * GET /api/{entity_plural}/{{id}}
     */
    public function show({entity_pascal} ${entity_slug})
    {{
        return new {entity_pascal}Resource(${entity_slug});
    }}

    /**
     * Actualizar un registro
     * PUT /api/{entity_plural}/{{id}}
     */
    public function update(Store{entity_pascal}Request $request, {entity_pascal} ${entity_slug})
    {{
        ${entity_slug}->update($request->validated());
        return new {entity_pascal}Resource(${entity_slug});
    }}

    /**
     * Eliminar un registro
     * DELETE /api/{entity_plural}/{{id}}
     */
    public function destroy({entity_pascal} ${entity_slug})
    {{
        ${entity_slug}->delete();
        return response()->noContent();
    }}
}}
"""
    return GeneratedFile(path=f"app/Http/Controllers/Api/{entity_pascal}Controller.php", language="php", content=content)


def _store_request(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
<?php

namespace App\\Http\\Requests;

use Illuminate\\Foundation\\Http\\FormRequest;

/**
 * Request de validación para crear/actualizar {entity_pascal}
 */
class Store{entity_pascal}Request extends FormRequest
{{
    /**
     * Determina si el usuario tiene autorización para hacer esta solicitud.
     */
    public function authorize(): bool
    {{
        return true; // Añadir lógica de autorización aquí
    }}

    /**
     * Reglas de validación para los datos de entrada.
     */
    public function rules(): array
    {{
        return [
            'name'        => ['required', 'string', 'min:1', 'max:200'],
            'description' => ['nullable', 'string', 'max:1000'],
            'status'      => ['nullable', 'string', 'in:active,inactive'],
        ];
    }}

    /**
     * Mensajes de error personalizados en español.
     */
    public function messages(): array
    {{
        return [
            'name.required' => 'El nombre es obligatorio.',
            'name.max'      => 'El nombre no puede superar los 200 caracteres.',
        ];
    }}
}}
"""
    return GeneratedFile(path=f"app/Http/Requests/Store{entity_pascal}Request.php", language="php", content=content)


def _entity_resource(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
<?php

namespace App\\Http\\Resources;

use Illuminate\\Http\\Request;
use Illuminate\\Http\\Resources\\Json\\JsonResource;

/**
 * API Resource para transformar {entity_pascal} a JSON
 */
class {entity_pascal}Resource extends JsonResource
{{
    /**
     * Transforma el recurso en un array para la respuesta JSON.
     */
    public function toArray(Request $request): array
    {{
        return [
            'id'          => $this->id,
            'name'        => $this->name,
            'description' => $this->description,
            'status'      => $this->status,
            'createdAt'   => $this->created_at?->toISOString(),
            'updatedAt'   => $this->updated_at?->toISOString(),
        ];
    }}
}}
"""
    return GeneratedFile(path=f"app/Http/Resources/{entity_pascal}Resource.php", language="php", content=content)


def _migration(entity_plural: str, timestamp: str) -> GeneratedFile:
    content = f"""\
<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

/**
 * Migración para crear la tabla {entity_plural}
 */
return new class extends Migration
{{
    public function up(): void
    {{
        Schema::create('{entity_plural}', function (Blueprint $table) {{
            $table->uuid('id')->primary();
            $table->string('name', 200);
            $table->text('description')->nullable();
            $table->string('status', 50)->default('active');
            $table->timestamps();
        }});
    }}

    public function down(): void
    {{
        Schema::dropIfExists('{entity_plural}');
    }}
}};
"""
    return GeneratedFile(path=f"database/migrations/{timestamp}_create_{entity_plural}_table.php", language="php", content=content)


def _entity_seeder(entity_slug: str, entity_pascal: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
<?php

namespace Database\\Seeders;

use App\\Models\\{entity_pascal};
use Illuminate\\Database\\Seeder;

/**
 * Seeder con datos de ejemplo para {entity_pascal}
 */
class {entity_pascal}Seeder extends Seeder
{{
    public function run(): void
    {{
        // Crear 3 registros de ejemplo
        $examples = [
            ['name' => '{entity_pascal} de ejemplo 1', 'description' => 'Primer registro de prueba'],
            ['name' => '{entity_pascal} de ejemplo 2', 'description' => 'Segundo registro de prueba'],
            ['name' => '{entity_pascal} de ejemplo 3', 'description' => null],
        ];

        foreach ($examples as $data) {{
            {entity_pascal}::create($data);
        }}

        $this->command->info("Seeder: {{count($examples)}} {entity_pascal.lower()} creados");
    }}
}}
""".replace("{entity_pascal.lower()}", entity_pascal.lower())
    return GeneratedFile(path=f"database/seeders/{entity_pascal}Seeder.php", language="php", content=content)


def _database_seeder(entity_pascal: str) -> GeneratedFile:
    content = f"""\
<?php

namespace Database\\Seeders;

use Illuminate\\Database\\Seeder;

/**
 * Seeder principal — orquesta todos los seeders del proyecto
 */
class DatabaseSeeder extends Seeder
{{
    public function run(): void
    {{
        $this->call([
            {entity_pascal}Seeder::class,
        ]);
    }}
}}
"""
    return GeneratedFile(path="database/seeders/DatabaseSeeder.php", language="php", content=content)


def _api_routes(entity_slug: str, entity_pascal: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
<?php

use App\\Http\\Controllers\\Api\\{entity_pascal}Controller;
use Illuminate\\Support\\Facades\\Route;

/*
|--------------------------------------------------------------------------
| Rutas API
|--------------------------------------------------------------------------
| Todas las rutas de la API REST del proyecto.
| Documentación automática en /api/docs (si instalas L5-Swagger)
*/

// Rutas CRUD para {entity_pascal}
Route::apiResource('{entity_plural}', {entity_pascal}Controller::class);

// Health check
Route::get('/health', fn() => response()->json([
    'status' => 'ok',
    'timestamp' => now()->toISOString(),
]));
"""
    return GeneratedFile(path="routes/api.php", language="php", content=content)


def _web_routes() -> GeneratedFile:
    content = """\
<?php

use Illuminate\\Support\\Facades\\Route;

// Ruta de bienvenida — redirige al frontend o muestra la vista de bienvenida
Route::get('/', fn() => view('welcome'));
"""
    return GeneratedFile(path="routes/web.php", language="php", content=content)


def _welcome_blade(project_name: str, modules: list[str]) -> GeneratedFile:
    module_links = "\n                ".join(
        f'<a href="/api/{slug(m)}s" class="block px-4 py-3 bg-white rounded-lg border hover:shadow-md transition">{m}</a>'
        for m in modules[:6]
    )
    content = f"""\
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="max-w-2xl mx-auto px-6 py-12 text-center">
        <h1 class="text-4xl font-bold text-gray-900 mb-2">{project_name}</h1>
        <p class="text-gray-500 mb-8">MVP generado con ProgresIA Studio &mdash; Laravel 11</p>

        <div class="grid gap-3 sm:grid-cols-2 text-left mb-8">
            {module_links}
        </div>

        <p class="text-sm text-gray-400">
            API disponible en <code class="bg-gray-100 px-2 py-1 rounded">/api</code>
            &bull;
            Documentación en <code class="bg-gray-100 px-2 py-1 rounded">/api/health</code>
        </p>
    </div>
</body>
</html>
"""
    return GeneratedFile(path="resources/views/welcome.blade.php", language="php", content=content)


def _bootstrap_app(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = """\
<?php

use Illuminate\\Foundation\\Application;
use Illuminate\\Foundation\\Configuration\\Exceptions;
use Illuminate\\Foundation\\Configuration\\Middleware;

// Laravel 11 — bootstrap/app.php simplificado
return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware) {
        // Añadir middleware global aquí
    })
    ->withExceptions(function (Exceptions $exceptions) {
        // Configurar manejo de excepciones aquí
    })
    ->create();
"""
    return GeneratedFile(path="bootstrap/app.php", language="php", content=content)


def _laravel_dockerfile() -> GeneratedFile:
    content = """\
FROM php:8.3-fpm-alpine AS base

# Instalar dependencias del sistema
RUN apk add --no-cache \
    git \
    curl \
    libpng-dev \
    libxml2-dev \
    zip \
    unzip \
    postgresql-dev

# Instalar extensiones PHP
RUN docker-php-ext-install pdo pdo_pgsql pgsql xml

# Instalar Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Copiar e instalar dependencias
COPY composer.json composer.lock ./
RUN composer install --no-dev --optimize-autoloader --no-scripts

# Copiar la aplicación
COPY . .

# Permisos
RUN chown -R www-data:www-data storage bootstrap/cache

EXPOSE 8000

CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000"]
"""
    return GeneratedFile(path="Dockerfile", language="dockerfile", content=content)


def _laravel_docker_compose(project_slug: str) -> GeneratedFile:
    content = f"""\
services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: {project_slug}
      POSTGRES_PASSWORD: {project_slug}
      POSTGRES_DB: {project_slug}_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {project_slug}"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    restart: unless-stopped
    environment:
      - APP_ENV=local
      - APP_DEBUG=true
      - DB_CONNECTION=pgsql
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_DATABASE={project_slug}_db
      - DB_USERNAME={project_slug}
      - DB_PASSWORD={project_slug}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - .:/var/www/html
      - /var/www/html/vendor

volumes:
  postgres_data:
"""
    return GeneratedFile(path="docker-compose.yml", language="yaml", content=content)


def _env_example(project_slug: str) -> GeneratedFile:
    content = f"""\
APP_NAME="{project_slug.replace('-', ' ').title()}"
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost:8000

# Base de datos PostgreSQL
DB_CONNECTION=pgsql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE={project_slug}_db
DB_USERNAME={project_slug}
DB_PASSWORD={project_slug}

# Cache y sesiones
CACHE_DRIVER=file
SESSION_DRIVER=file
QUEUE_CONNECTION=sync
"""
    return GeneratedFile(path=".env.example", language="env", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
/node_modules
/public/hot
/public/storage
/storage/*.key
/vendor
.env
.env.backup
.phpunit.result.cache
database/database.sqlite
Homestead.json
Homestead.yaml
npm-debug.log
yarn-error.log
/.idea
/.vscode
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
