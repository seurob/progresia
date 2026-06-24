"""Angular 18 + TypeScript + Tailwind CSS scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_angular(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Angular 18 con componentes standalone y Tailwind CSS."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    return [
        _package_json(project_slug),
        _tsconfig(),
        _tsconfig_app(),
        _angular_json(project_slug),
        _tailwind_config(),
        _postcss_config(),
        _index_html(req.project_name),
        _main_ts(),
        _app_config(),
        _app_routes(entity_slug_name),
        _app_component(req.project_name),
        _home_component(req.project_name),
        _entity_list_component(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _entity_service(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _entity_model(entity_slug_name, entity_pascal_name, primary),
        _environment_ts(),
        _environment_prod_ts(),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Variables de entorno — copia a .env y ajusta los valores\n\n"
                "# URL de la API backend\n"
                "NG_APP_API_URL=http://localhost:3000\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Angular 18 · TypeScript · Tailwind CSS · HttpClient",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Angular CLI — npm install -g @angular/cli",
            ],
            setup_commands=[
                "npm install",
                "npm start",
            ],
            env_vars=[
                ("NG_APP_API_URL", "http://localhost:3000"),
            ],
            api_port=4200,
        ),
    ]


# ── package.json ──────────────────────────────────────────────────────────────

def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build",
    "watch": "ng build --watch --configuration development",
    "test": "ng test"
  }},
  "dependencies": {{
    "@angular/animations": "^18.0.0",
    "@angular/common": "^18.0.0",
    "@angular/compiler": "^18.0.0",
    "@angular/core": "^18.0.0",
    "@angular/forms": "^18.0.0",
    "@angular/platform-browser": "^18.0.0",
    "@angular/platform-browser-dynamic": "^18.0.0",
    "@angular/router": "^18.0.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "~0.14.3"
  }},
  "devDependencies": {{
    "@angular-devkit/build-angular": "^18.0.0",
    "@angular/cli": "^18.0.0",
    "@angular/compiler-cli": "^18.0.0",
    "@types/jasmine": "~5.1.0",
    "autoprefixer": "^10.4.19",
    "jasmine-core": "~5.1.0",
    "karma": "~6.4.0",
    "karma-chrome-launcher": "~3.2.0",
    "karma-coverage": "~2.2.0",
    "karma-jasmine": "~5.1.0",
    "karma-jasmine-html-reporter": "~2.1.0",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "~5.4.2"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


# ── tsconfig ──────────────────────────────────────────────────────────────────

def _tsconfig() -> GeneratedFile:
    content = """\
{
  "compileOnSave": false,
  "compilerOptions": {
    "baseUrl": "./",
    "outDir": "./dist/out-tsc",
    "forceConsistentCasingInFileNames": true,
    "strict": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "sourceMap": true,
    "declaration": false,
    "experimentalDecorators": true,
    "moduleResolution": "bundler",
    "importHelpers": true,
    "target": "ES2022",
    "module": "ES2022",
    "useDefineForClassFields": false,
    "lib": ["ES2022", "dom"]
  },
  "angularCompilerOptions": {
    "enableI18nLegacyMessageIdFormat": false,
    "strictInjectionParameters": true,
    "strictInputAccessModifiers": true,
    "strictTemplates": true
  }
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _tsconfig_app() -> GeneratedFile:
    content = """\
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./out-tsc/app",
    "types": []
  },
  "files": [
    "src/main.ts"
  ],
  "include": [
    "src/**/*.d.ts"
  ]
}
"""
    return GeneratedFile(path="tsconfig.app.json", language="json", content=content)


# ── angular.json ──────────────────────────────────────────────────────────────

def _angular_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "newProjectRoot": "projects",
  "projects": {{
    "{project_slug}": {{
      "projectType": "application",
      "schematics": {{
        "@schematics/angular:component": {{
          "standalone": true,
          "style": "none"
        }}
      }},
      "root": "",
      "sourceRoot": "src",
      "prefix": "app",
      "architect": {{
        "build": {{
          "builder": "@angular-devkit/build-angular:application",
          "options": {{
            "outputPath": "dist/{project_slug}",
            "index": "src/index.html",
            "browser": "src/main.ts",
            "polyfills": ["zone.js"],
            "tsConfig": "tsconfig.app.json",
            "styles": ["src/styles.css"],
            "scripts": []
          }},
          "configurations": {{
            "production": {{
              "budgets": [
                {{ "type": "initial", "maximumWarning": "500kB", "maximumError": "1MB" }},
                {{ "type": "anyComponentStyle", "maximumWarning": "2kB", "maximumError": "4kB" }}
              ],
              "outputHashing": "all"
            }},
            "development": {{
              "optimization": false,
              "extractLicenses": false,
              "sourceMap": true
            }}
          }},
          "defaultConfiguration": "production"
        }},
        "serve": {{
          "builder": "@angular-devkit/build-angular:dev-server",
          "configurations": {{
            "production": {{ "buildTarget": "{project_slug}:build:production" }},
            "development": {{ "buildTarget": "{project_slug}:build:development" }}
          }},
          "defaultConfiguration": "development"
        }}
      }}
    }}
  }}
}}
"""
    return GeneratedFile(path="angular.json", language="json", content=content)


def _tailwind_config() -> GeneratedFile:
    content = """\
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
"""
    return GeneratedFile(path="tailwind.config.js", language="javascript", content=content)


def _postcss_config() -> GeneratedFile:
    content = """\
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
    return GeneratedFile(path="postcss.config.js", language="javascript", content=content)


# ── src/ entry ────────────────────────────────────────────────────────────────

def _index_html(project_name: str) -> GeneratedFile:
    content = f"""\
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{project_name}</title>
  <base href="/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/x-icon" href="favicon.ico">
</head>
<body>
  <app-root></app-root>
</body>
</html>
"""
    return GeneratedFile(path="src/index.html", language="html", content=content)


def _main_ts() -> GeneratedFile:
    content = """\
import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';

bootstrapApplication(AppComponent, appConfig).catch(err => console.error(err));
"""
    return GeneratedFile(path="src/main.ts", language="typescript", content=content)


# ── app/ ──────────────────────────────────────────────────────────────────────

def _app_config() -> GeneratedFile:
    content = """\
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withFetch()),
  ]
};
"""
    return GeneratedFile(path="src/app/app.config.ts", language="typescript", content=content)


def _app_routes(entity_slug_name: str) -> GeneratedFile:
    content = f"""\
import {{ Routes }} from '@angular/router';

export const routes: Routes = [
  {{
    path: '',
    loadComponent: () =>
      import('./pages/home/home.component').then(m => m.HomeComponent),
  }},
  {{
    path: '{entity_slug_name}',
    loadComponent: () =>
      import('./pages/{entity_slug_name}-list/{entity_slug_name}-list.component').then(
        m => m.{pascal(entity_slug_name)}ListComponent,
      ),
  }},
  {{
    path: '**',
    redirectTo: '',
  }},
];
"""
    return GeneratedFile(path="src/app/app.routes.ts", language="typescript", content=content)


def _app_component(project_name: str) -> GeneratedFile:
    content = f"""\
import {{ Component }} from '@angular/core';
import {{ RouterOutlet, RouterLink }} from '@angular/router';

@Component({{
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink],
  template: `
    <nav class="bg-indigo-600 text-white px-6 py-3 flex gap-6 shadow">
      <span class="font-bold text-lg">{project_name}</span>
      <a routerLink="/" class="hover:underline">Inicio</a>
    </nav>
    <main class="p-6">
      <router-outlet />
    </main>
  `,
}})
export class AppComponent {{}}
"""
    return GeneratedFile(path="src/app/app.component.ts", language="typescript", content=content)


def _home_component(project_name: str) -> GeneratedFile:
    content = f"""\
import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-home',
  standalone: true,
  template: `
    <div class="max-w-xl mx-auto mt-16 text-center">
      <h1 class="text-4xl font-bold text-indigo-700 mb-4">{project_name}</h1>
      <p class="text-gray-600 text-lg">
        Bienvenido a tu proyecto Angular. Modifica este componente para empezar.
      </p>
    </div>
  `,
}})
export class HomeComponent {{}}
"""
    return GeneratedFile(path="src/app/pages/home/home.component.ts", language="typescript", content=content)


def _entity_list_component(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ Component, OnInit, inject }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';
import {{ {entity_pascal_name}Service }} from '../../services/{entity_slug_name}.service';
import {{ {entity_pascal_name} }} from '../../models/{entity_slug_name}.model';

@Component({{
  selector: 'app-{entity_slug_name}-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-4xl mx-auto">
      <h2 class="text-2xl font-bold text-gray-800 mb-6">{entity_pascal_name}s</h2>

      <div *ngIf="loading" class="text-center text-gray-500 py-8">Cargando...</div>

      <div *ngIf="error" class="bg-red-50 border border-red-200 text-red-700 rounded p-4 mb-4">
        {{{{ error }}}}
      </div>

      <ul class="divide-y divide-gray-200 bg-white shadow rounded-lg">
        <li *ngFor="let item of items" class="px-6 py-4 flex justify-between items-center">
          <div>
            <p class="font-medium text-gray-900">{{{{ item.name }}}}</p>
            <p *ngIf="item.description" class="text-sm text-gray-500">{{{{ item.description }}}}</p>
          </div>
          <span class="text-xs px-2 py-1 rounded-full"
                [class.bg-green-100]="item.status === 'active'"
                [class.text-green-700]="item.status === 'active'"
                [class.bg-gray-100]="item.status !== 'active'"
                [class.text-gray-600]="item.status !== 'active'">
            {{{{ item.status ?? 'activo' }}}}
          </span>
        </li>
        <li *ngIf="!loading && items.length === 0" class="px-6 py-8 text-center text-gray-400">
          No hay {entity_plural} todavía.
        </li>
      </ul>
    </div>
  `,
}})
export class {entity_pascal_name}ListComponent implements OnInit {{
  private service = inject({entity_pascal_name}Service);

  items: {entity_pascal_name}[] = [];
  loading = true;
  error: string | null = null;

  ngOnInit(): void {{
    this.service.getAll().subscribe({{
      next: (data) => {{ this.items = data; this.loading = false; }},
      error: (err) => {{
        this.error = 'No se pudieron cargar los datos.';
        this.loading = false;
        console.error(err);
      }},
    }});
  }}
}}
"""
    return GeneratedFile(
        path=f"src/app/pages/{entity_slug_name}-list/{entity_slug_name}-list.component.ts",
        language="typescript",
        content=content,
    )


def _entity_service(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ Injectable, inject }} from '@angular/core';
import {{ HttpClient }} from '@angular/common/http';
import {{ Observable }} from 'rxjs';
import {{ environment }} from '../../environments/environment';
import {{ {entity_pascal_name} }} from '../models/{entity_slug_name}.model';

@Injectable({{ providedIn: 'root' }})
export class {entity_pascal_name}Service {{
  private http = inject(HttpClient);
  private apiUrl = `${{environment.apiUrl}}/api/{entity_plural}`;

  getAll(): Observable<{entity_pascal_name}[]> {{
    return this.http.get<{entity_pascal_name}[]>(this.apiUrl);
  }}

  getById(id: string): Observable<{entity_pascal_name}> {{
    return this.http.get<{entity_pascal_name}>(`${{this.apiUrl}}/${{id}}`);
  }}

  create(data: Partial<{entity_pascal_name}>): Observable<{entity_pascal_name}> {{
    return this.http.post<{entity_pascal_name}>(this.apiUrl, data);
  }}

  update(id: string, data: Partial<{entity_pascal_name}>): Observable<{entity_pascal_name}> {{
    return this.http.patch<{entity_pascal_name}>(`${{this.apiUrl}}/${{id}}`, data);
  }}

  remove(id: string): Observable<void> {{
    return this.http.delete<void>(`${{this.apiUrl}}/${{id}}`);
  }}
}}
"""
    return GeneratedFile(path=f"src/app/services/{entity_slug_name}.service.ts", language="typescript", content=content)


def _entity_model(entity_slug_name: str, entity_pascal_name: str, primary: dict) -> GeneratedFile:
    content = f"""\
export interface {entity_pascal_name} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt?: string;
  updatedAt?: string;
}}
"""
    return GeneratedFile(path=f"src/app/models/{entity_slug_name}.model.ts", language="typescript", content=content)


def _environment_ts() -> GeneratedFile:
    content = """\
export const environment = {
  production: false,
  apiUrl: 'http://localhost:3000',
};
"""
    return GeneratedFile(path="src/environments/environment.ts", language="typescript", content=content)


def _environment_prod_ts() -> GeneratedFile:
    content = """\
export const environment = {
  production: true,
  apiUrl: '/api',
};
"""
    return GeneratedFile(path="src/environments/environment.prod.ts", language="typescript", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
# Angular
.angular/
dist/
node_modules/
.env
*.js.map
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)
