"""Node.js + TypeScript + PostgreSQL (raw SQL, sin ORM) scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.docker import generate_node_dockerfile
from app.agents.fallback.shared.readme import generate_readme


def build_node_postgres(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Node.js + pg con SQL puro — sin ORM, sin Prisma."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    return [
        _package_json(project_slug),
        _tsconfig(),
        _index_ts(project_slug),
        _db_config(),
        _entity_model(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _entity_routes(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _entity_controller(entity_slug_name, entity_pascal_name, entity_camel_name, entity_plural),
        _error_handler(),
        _types_index(entity_pascal_name),
        _schema_sql(entity_slug_name, entity_pascal_name, entity_plural),
        _seed_sql(entity_plural),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Copia a .env y ajusta los valores\n\n"
                f"DATABASE_URL=postgresql://user:password@localhost:5432/{project_slug}_db\n"
                "PORT=3000\n"
                "CORS_ORIGIN=http://localhost:5173\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Node.js · TypeScript · pg (PostgreSQL nativo) · Sin ORM",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Docker Desktop — https://docker.com",
            ],
            setup_commands=[
                "docker compose up -d                    # levanta PostgreSQL",
                "npm install",
                "cp .env.example .env                   # ajusta DATABASE_URL",
                "# Crea las tablas (requiere psql o cliente SQL):",
                "psql $DATABASE_URL -f sql/schema.sql",
                "psql $DATABASE_URL -f sql/seed.sql",
                "npm run dev",
            ],
            env_vars=[
                ("DATABASE_URL", f"postgresql://user:password@localhost:5432/{project_slug}_db"),
                ("PORT", "3000"),
            ],
            api_port=3000,
        ),
        generate_node_dockerfile(port=3000, entry="dist/index.js", needs_prisma=False),
        _docker_compose(project_slug),
    ]


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "tsx watch src/index.ts",
    "build": "tsc -p tsconfig.json",
    "start": "node dist/index.js"
  }},
  "dependencies": {{
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.19.2",
    "pg": "^8.12.0",
    "zod": "^3.23.8"
  }},
  "devDependencies": {{
    "@types/cors": "^2.8.17",
    "@types/express": "^4.17.21",
    "@types/node": "^20.14.2",
    "@types/pg": "^8.11.6",
    "tsx": "^4.15.6",
    "typescript": "^5.4.5"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "lib": ["ES2022"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _index_ts(project_slug: str) -> GeneratedFile:
    content = f"""\
import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import {{ router as entityRouter }} from './routes';
import {{ errorHandler }} from './middleware/errorHandler';

const app = express();
const PORT = Number(process.env.PORT ?? 3000);

app.use(cors({{ origin: process.env.CORS_ORIGIN ?? '*' }}));
app.use(express.json());

app.get('/health', (_req, res) => res.json({{ status: 'ok', project: '{project_slug}' }}));
app.use('/api', entityRouter);
app.use(errorHandler);

app.listen(PORT, () => {{
  console.log(`🚀 {project_slug} running on http://localhost:${{PORT}}`);
}});

export default app;
"""
    return GeneratedFile(path="src/index.ts", language="typescript", content=content)


def _db_config() -> GeneratedFile:
    content = """\
import {{ Pool }} from 'pg';

// Pool de conexiones a PostgreSQL — se reutiliza entre peticiones
export const db = new Pool({{
  connectionString: process.env.DATABASE_URL,
  max: 10,          // máximo de conexiones simultáneas
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 5_000,
}});

db.on('error', (err) => {{
  console.error('Error inesperado en el pool de PostgreSQL:', err);
}});
"""
    return GeneratedFile(path="src/config/database.ts", language="typescript", content=content)


def _entity_model(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ db }} from '../config/database';
import type {{ {entity_pascal_name} }} from '../types';

// Todas las queries usan SQL parametrizado ($1, $2…) para evitar inyección SQL

export async function findAll{entity_pascal_name}s(): Promise<{entity_pascal_name}[]> {{
  const result = await db.query<{entity_pascal_name}>(
    'SELECT * FROM {entity_plural} ORDER BY created_at DESC',
  );
  return result.rows;
}}

export async function find{entity_pascal_name}ById(id: string): Promise<{entity_pascal_name} | null> {{
  const result = await db.query<{entity_pascal_name}>(
    'SELECT * FROM {entity_plural} WHERE id = $1',
    [id],
  );
  return result.rows[0] ?? null;
}}

export async function create{entity_pascal_name}(data: {{
  name: string;
  description?: string | null;
  status?: string;
}}): Promise<{entity_pascal_name}> {{
  const result = await db.query<{entity_pascal_name}>(
    `INSERT INTO {entity_plural} (name, description, status)
     VALUES ($1, $2, $3)
     RETURNING *`,
    [data.name, data.description ?? null, data.status ?? 'active'],
  );
  return result.rows[0];
}}

export async function update{entity_pascal_name}(
  id: string,
  data: Partial<{{ name: string; description: string | null; status: string }}>,
): Promise<{entity_pascal_name} | null> {{
  const fields: string[] = [];
  const values: unknown[] = [];
  let idx = 1;

  if (data.name !== undefined)        {{ fields.push(`name = $${{idx++}}`);        values.push(data.name); }}
  if (data.description !== undefined) {{ fields.push(`description = $${{idx++}}`); values.push(data.description); }}
  if (data.status !== undefined)      {{ fields.push(`status = $${{idx++}}`);      values.push(data.status); }}
  if (fields.length === 0) return find{entity_pascal_name}ById(id);

  fields.push(`updated_at = NOW()`);
  values.push(id);

  const result = await db.query<{entity_pascal_name}>(
    `UPDATE {entity_plural} SET ${{fields.join(', ')}} WHERE id = $${{idx}} RETURNING *`,
    values,
  );
  return result.rows[0] ?? null;
}}

export async function delete{entity_pascal_name}(id: string): Promise<boolean> {{
  const result = await db.query(
    'DELETE FROM {entity_plural} WHERE id = $1',
    [id],
  );
  return (result.rowCount ?? 0) > 0;
}}
"""
    return GeneratedFile(path=f"src/models/{entity_slug_name}.model.ts", language="typescript", content=content)


def _entity_routes(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ Router }} from 'express';
import * as ctrl from './controllers/{entity_slug_name}.controller';

export const router = Router();

// Rutas CRUD para {entity_plural}
router.get('/{entity_plural}', ctrl.list);
router.post('/{entity_plural}', ctrl.create);
router.get('/{entity_plural}/:id', ctrl.getOne);
router.patch('/{entity_plural}/:id', ctrl.update);
router.delete('/{entity_plural}/:id', ctrl.remove);
"""
    return GeneratedFile(path="src/routes/index.ts", language="typescript", content=content)


def _entity_controller(entity_slug_name: str, entity_pascal_name: str, entity_camel_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import type {{ Request, Response, NextFunction }} from 'express';
import {{ z }} from 'zod';
import {{
  findAll{entity_pascal_name}s,
  find{entity_pascal_name}ById,
  create{entity_pascal_name},
  update{entity_pascal_name},
  delete{entity_pascal_name},
}} from '../models/{entity_slug_name}.model';

const createSchema = z.object({{
  name: z.string().min(1).max(200),
  description: z.string().optional().nullable(),
  status: z.enum(['active', 'inactive', 'archived']).optional(),
}});

const updateSchema = createSchema.partial();

export async function list(_req: Request, res: Response, next: NextFunction) {{
  try {{
    const items = await findAll{entity_pascal_name}s();
    res.json(items);
  }} catch (e) {{
    next(e);
  }}
}}

export async function getOne(req: Request, res: Response, next: NextFunction) {{
  try {{
    const item = await find{entity_pascal_name}ById(req.params.id);
    if (!item) return res.status(404).json({{ error: '{entity_pascal_name} no encontrado' }});
    res.json(item);
  }} catch (e) {{
    next(e);
  }}
}}

export async function create(req: Request, res: Response, next: NextFunction) {{
  try {{
    const parsed = createSchema.safeParse(req.body);
    if (!parsed.success) return res.status(422).json({{ errors: parsed.error.format() }});
    const item = await create{entity_pascal_name}(parsed.data);
    res.status(201).json(item);
  }} catch (e) {{
    next(e);
  }}
}}

export async function update(req: Request, res: Response, next: NextFunction) {{
  try {{
    const parsed = updateSchema.safeParse(req.body);
    if (!parsed.success) return res.status(422).json({{ errors: parsed.error.format() }});
    const item = await update{entity_pascal_name}(req.params.id, parsed.data);
    if (!item) return res.status(404).json({{ error: '{entity_pascal_name} no encontrado' }});
    res.json(item);
  }} catch (e) {{
    next(e);
  }}
}}

export async function remove(req: Request, res: Response, next: NextFunction) {{
  try {{
    const deleted = await delete{entity_pascal_name}(req.params.id);
    if (!deleted) return res.status(404).json({{ error: '{entity_pascal_name} no encontrado' }});
    res.status(204).send();
  }} catch (e) {{
    next(e);
  }}
}}
"""
    return GeneratedFile(path=f"src/controllers/{entity_slug_name}.controller.ts", language="typescript", content=content)


def _error_handler() -> GeneratedFile:
    content = """\
import type { Request, Response, NextFunction } from 'express';

export function errorHandler(
  err: unknown,
  _req: Request,
  res: Response,
  _next: NextFunction,
): void {
  console.error(err);
  const message = err instanceof Error ? err.message : 'Error interno del servidor';
  res.status(500).json({ error: message });
}
"""
    return GeneratedFile(path="src/middleware/errorHandler.ts", language="typescript", content=content)


def _types_index(entity_pascal_name: str) -> GeneratedFile:
    content = f"""\
export interface {entity_pascal_name} {{
  id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: Date;
  updated_at: Date;
}}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _schema_sql(entity_slug_name: str, entity_pascal_name: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
-- Esquema SQL para {entity_pascal_name}
-- Ejecuta este archivo con: psql $DATABASE_URL -f sql/schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- para gen_random_uuid()

CREATE TABLE IF NOT EXISTS {entity_plural} (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(200)  NOT NULL,
    description TEXT,
    status      VARCHAR(50)   NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Índice para búsquedas por nombre
CREATE INDEX IF NOT EXISTS idx_{entity_plural}_name ON {entity_plural} (name);
-- Índice para filtrar por estado
CREATE INDEX IF NOT EXISTS idx_{entity_plural}_status ON {entity_plural} (status);
"""
    return GeneratedFile(path="sql/schema.sql", language="sql", content=content)


def _seed_sql(entity_plural: str) -> GeneratedFile:
    content = f"""\
-- Datos de ejemplo para {entity_plural}
-- Ejecuta con: psql $DATABASE_URL -f sql/seed.sql

INSERT INTO {entity_plural} (name, description, status) VALUES
  ('Ejemplo 1', 'Primer elemento de prueba', 'active'),
  ('Ejemplo 2', 'Segundo elemento de prueba', 'active'),
  ('Ejemplo 3', 'Tercer elemento — archivado', 'archived')
ON CONFLICT DO NOTHING;
"""
    return GeneratedFile(path="sql/seed.sql", language="sql", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.env
*.js.map
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)


def _docker_compose(project_slug: str) -> GeneratedFile:
    safe = project_slug.replace("-", "_")
    content = f"""\
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://{safe}:{safe}@db:5432/{safe}_db
      PORT: 3000
      CORS_ORIGIN: http://localhost:5173
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./sql:/app/sql

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: {safe}
      POSTGRES_PASSWORD: {safe}
      POSTGRES_DB: {safe}_db
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./sql/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {safe}"]
      interval: 10s
      retries: 5

volumes:
  pg_data:
"""
    return GeneratedFile(path="docker-compose.yml", language="yaml", content=content)
