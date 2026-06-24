"""Express + TypeScript + Prisma + PostgreSQL scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.prisma import generate_prisma_schema, generate_seed_ts
from app.agents.fallback.shared.docker import generate_docker_compose, generate_node_dockerfile
from app.agents.fallback.shared.readme import generate_readme


def build_express(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Express + TypeScript + Prisma."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal = pascal(primary.get("name", "Item"))
    entity_camel = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    files: list[GeneratedFile] = [
        _package_json(project_slug, req.needs_auth),
        _tsconfig(),
        _index_ts(project_slug),
        _entity_routes(entity_slug_name, entity_pascal, entity_camel, entity_plural),
        _entity_controller(entity_slug_name, entity_pascal, entity_camel, entity_plural),
        _entity_service(entity_slug_name, entity_pascal, entity_camel),
        _entity_schema(entity_slug_name, entity_pascal),
        _error_handler(),
        _validate_middleware(),
        _prisma_service(),
        _types_index(req.modules, req.data_entities),
        generate_prisma_schema(
            req.modules, req.needs_auth, req.data_entities or None,
            schema_path="prisma/schema.prisma"
        ),
        generate_seed_ts(
            req.data_entities or [primary], req.project_name,
            seed_path="prisma/seed.ts"
        ),
        _env_example(project_slug),
        _gitignore(),
        generate_readme(
            req,
            stack_summary="Express · TypeScript · Prisma · PostgreSQL",
            setup_commands=[
                "docker compose up -d",
                "npm install",
                "npx prisma migrate dev --name init",
                "npx prisma db seed",
                "npm run dev",
            ],
            env_vars=[
                ("DATABASE_URL", f"postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"),
                ("JWT_SECRET", "genera con: openssl rand -hex 32"),
                ("PORT", "3000"),
                ("CORS_ORIGIN", "http://localhost:5173"),
            ],
            api_port=3000,
        ),
        generate_node_dockerfile(port=3000, entry="dist/index.js", needs_prisma=True),
        generate_docker_compose(project_slug, needs_postgres=True, api_port=3000),
    ]

    if req.needs_auth:
        files.append(_auth_middleware())
        files.append(_auth_routes(project_slug))

    return files


def _package_json(project_slug: str, needs_auth: bool) -> GeneratedFile:
    auth_deps = '"bcryptjs": "^2.4.3",\n    "jsonwebtoken": "^9.0.2",' if needs_auth else ""
    auth_dev_deps = '"@types/bcryptjs": "^2.4.6",\n    "@types/jsonwebtoken": "^9.0.7",' if needs_auth else ""

    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "tsx watch src/index.ts",
    "build": "tsc -p tsconfig.json",
    "start": "node dist/index.js",
    "db:migrate": "prisma migrate dev",
    "db:seed": "tsx prisma/seed.ts",
    "db:studio": "prisma studio"
  }},
  "dependencies": {{
    "@prisma/client": "^5.22.0",
    {auth_deps}
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.21.0",
    "zod": "^3.23.0"
  }},
  "devDependencies": {{
    "@types/cors": "^2.8.17",
    {auth_dev_deps}
    "@types/express": "^5.0.0",
    "@types/node": "^22.0.0",
    "prisma": "^5.22.0",
    "tsx": "^4.19.2",
    "typescript": "^5.7.0"
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
    "moduleResolution": "node",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "sourceMap": true
  },
  "include": ["src", "prisma"],
  "exclude": ["node_modules", "dist"]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _index_ts(project_slug: str) -> GeneratedFile:
    content = """\
import "dotenv/config";
import express from "express";
import cors from "cors";
import { errorHandler } from "./middleware/errorHandler";
import { itemRoutes } from "./routes/item.routes";

// Punto de entrada de la API Express
const app = express();
const PORT = Number(process.env.PORT ?? 3000);

// Middleware
app.use(cors({ origin: process.env.CORS_ORIGIN ?? "http://localhost:5173" }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rutas
app.get("/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});
app.use("/api/items", itemRoutes);

// Manejo de errores (debe ir al final)
app.use(errorHandler);

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Servidor activo en http://0.0.0.0:${PORT}`);
});

export default app;
"""
    return GeneratedFile(path="src/index.ts", language="typescript", content=content)


def _entity_routes(entity_slug: str, entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ Router }} from "express";
import {{ {entity_pascal}Controller }} from "../controllers/{entity_slug}.controller";
import {{ validateBody }} from "../middleware/validate";
import {{ create{entity_pascal}Schema, update{entity_pascal}Schema }} from "../schemas/{entity_slug}.schema";

// Rutas CRUD para {entity_pascal}
const router = Router();
const ctrl = new {entity_pascal}Controller();

router.get("/", ctrl.findAll.bind(ctrl));
router.get("/:id", ctrl.findOne.bind(ctrl));
router.post("/", validateBody(create{entity_pascal}Schema), ctrl.create.bind(ctrl));
router.put("/:id", validateBody(update{entity_pascal}Schema), ctrl.update.bind(ctrl));
router.delete("/:id", ctrl.remove.bind(ctrl));

export const {entity_camel}Routes = router;
// Alias para compatibilidad con src/index.ts
export const itemRoutes = router;
"""
    return GeneratedFile(path=f"src/routes/{entity_slug}.routes.ts", language="typescript", content=content)


def _entity_controller(entity_slug: str, entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ Request, Response, NextFunction }} from "express";
import {{ {entity_pascal}Service }} from "../services/{entity_slug}.service";

// Controlador para {entity_pascal} — delega la lógica al servicio
export class {entity_pascal}Controller {{
  private service = new {entity_pascal}Service();

  async findAll(_req: Request, res: Response, next: NextFunction) {{
    try {{
      const items = await this.service.findAll();
      res.json(items);
    }} catch (err) {{
      next(err);
    }}
  }}

  async findOne(req: Request, res: Response, next: NextFunction) {{
    try {{
      const item = await this.service.findOne(req.params.id);
      if (!item) return res.status(404).json({{ error: "No encontrado" }});
      res.json(item);
    }} catch (err) {{
      next(err);
    }}
  }}

  async create(req: Request, res: Response, next: NextFunction) {{
    try {{
      const item = await this.service.create(req.body);
      res.status(201).json(item);
    }} catch (err) {{
      next(err);
    }}
  }}

  async update(req: Request, res: Response, next: NextFunction) {{
    try {{
      const item = await this.service.update(req.params.id, req.body);
      res.json(item);
    }} catch (err) {{
      next(err);
    }}
  }}

  async remove(req: Request, res: Response, next: NextFunction) {{
    try {{
      await this.service.remove(req.params.id);
      res.status(204).send();
    }} catch (err) {{
      next(err);
    }}
  }}
}}
"""
    return GeneratedFile(path=f"src/controllers/{entity_slug}.controller.ts", language="typescript", content=content)


def _entity_service(entity_slug: str, entity_pascal: str, entity_camel: str) -> GeneratedFile:
    content = f"""\
import {{ prisma }} from "./prisma.service";

// Servicio para {entity_pascal} — contiene la lógica de negocio
export class {entity_pascal}Service {{
  async findAll() {{
    return prisma.{entity_camel}.findMany({{
      orderBy: {{ createdAt: "desc" }},
    }});
  }}

  async findOne(id: string) {{
    return prisma.{entity_camel}.findUnique({{ where: {{ id }} }});
  }}

  async create(data: {{ name: string; description?: string }}) {{
    return prisma.{entity_camel}.create({{ data }});
  }}

  async update(id: string, data: {{ name?: string; description?: string }}) {{
    return prisma.{entity_camel}.update({{
      where: {{ id }},
      data,
    }});
  }}

  async remove(id: string) {{
    return prisma.{entity_camel}.delete({{ where: {{ id }} }});
  }}
}}
"""
    return GeneratedFile(path=f"src/services/{entity_slug}.service.ts", language="typescript", content=content)


def _entity_schema(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
import {{ z }} from "zod";

// Esquemas de validación con Zod para {entity_pascal}
export const create{entity_pascal}Schema = z.object({{
  name: z.string().min(1, "El nombre es obligatorio").max(200),
  description: z.string().max(1000).optional(),
}});

export const update{entity_pascal}Schema = create{entity_pascal}Schema.partial();

export type Create{entity_pascal}Input = z.infer<typeof create{entity_pascal}Schema>;
export type Update{entity_pascal}Input = z.infer<typeof update{entity_pascal}Schema>;
"""
    return GeneratedFile(path=f"src/schemas/{entity_slug}.schema.ts", language="typescript", content=content)


def _error_handler() -> GeneratedFile:
    content = """\
import { Request, Response, NextFunction } from "express";

// Middleware centralizado de manejo de errores
// Debe registrarse al final de la cadena de middleware en app.use()
export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
) {
  console.error("Error:", err.message);

  // Error de validación de Zod
  if (err.name === "ZodError") {
    return res.status(400).json({ error: "Datos inválidos", details: err.message });
  }

  // Error de Prisma: registro no encontrado
  if (err.message.includes("Record to update not found") || err.message.includes("No Record found")) {
    return res.status(404).json({ error: "Registro no encontrado" });
  }

  res.status(500).json({ error: "Error interno del servidor" });
}
"""
    return GeneratedFile(path="src/middleware/errorHandler.ts", language="typescript", content=content)


def _validate_middleware() -> GeneratedFile:
    content = """\
import { Request, Response, NextFunction } from "express";
import { ZodSchema } from "zod";

// Middleware de validación del cuerpo de la petición con Zod
export function validateBody(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        error: "Datos de entrada inválidos",
        details: result.error.flatten(),
      });
    }
    req.body = result.data; // Sobreescribe con los datos validados y transformados
    next();
  };
}
"""
    return GeneratedFile(path="src/middleware/validate.ts", language="typescript", content=content)


def _prisma_service() -> GeneratedFile:
    content = """\
import { PrismaClient } from "@prisma/client";

// Singleton de Prisma Client — reutiliza la misma instancia durante el ciclo de vida
export const prisma = new PrismaClient({
  log: process.env.NODE_ENV === "development" ? ["query", "error"] : ["error"],
});
"""
    return GeneratedFile(path="src/services/prisma.service.ts", language="typescript", content=content)


def _types_index(modules: list[str], data_entities: list[dict]) -> GeneratedFile:
    if data_entities:
        type_blocks = []
        for entity in data_entities[:8]:
            entity_name = pascal(entity.get("name", "Item"))
            type_blocks.append(f"""\
export interface {entity_name} {{
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  createdAt: Date;
  updatedAt: Date;
}}""")
        types_content = "\n\n".join(type_blocks)
    else:
        types_content = "\n\n".join(
            f"""\
export interface {pascal(m)} {{
  id: string;
  name: string;
  description?: string | null;
  createdAt: Date;
  updatedAt: Date;
}}"""
            for m in modules[:5]
        )

    content = f"""\
// Tipos TypeScript compartidos

{types_content}
"""
    return GeneratedFile(path="src/types/index.ts", language="typescript", content=content)


def _auth_middleware() -> GeneratedFile:
    content = """\
import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

interface JwtPayload {
  sub: string;
  email: string;
}

// Extiende la interfaz Request para incluir el usuario autenticado
declare global {
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

// Middleware de autenticación JWT
export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const auth = req.headers.authorization;
  if (!auth?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Token no proporcionado" });
  }

  const token = auth.slice(7);
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET ?? "dev") as JwtPayload;
    req.user = payload;
    next();
  } catch {
    res.status(401).json({ error: "Token inválido o expirado" });
  }
}
"""
    return GeneratedFile(path="src/middleware/auth.ts", language="typescript", content=content)


def _auth_routes(project_slug: str) -> GeneratedFile:
    content = """\
import { Router } from "express";
import { prisma } from "../services/prisma.service";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { z } from "zod";
import { validateBody } from "../middleware/validate";

const router = Router();

const registerSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  password: z.string().min(8),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

// POST /auth/register
router.post("/register", validateBody(registerSchema), async (req, res, next) => {
  try {
    const { email, name, password } = req.body;
    const hash = await bcrypt.hash(password, 12);
    const user = await prisma.user.create({
      data: { email, name, passwordHash: hash },
      select: { id: true, email: true, name: true },
    });
    const token = jwt.sign({ sub: user.id, email: user.email }, process.env.JWT_SECRET ?? "dev", {
      expiresIn: "7d",
    });
    res.status(201).json({ user, token });
  } catch (err) {
    next(err);
  }
});

// POST /auth/login
router.post("/login", validateBody(loginSchema), async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) return res.status(401).json({ error: "Credenciales incorrectas" });
    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) return res.status(401).json({ error: "Credenciales incorrectas" });
    const token = jwt.sign({ sub: user.id, email: user.email }, process.env.JWT_SECRET ?? "dev", {
      expiresIn: "7d",
    });
    const { passwordHash: _, ...safeUser } = user;
    res.json({ user: safeUser, token });
  } catch (err) {
    next(err);
  }
});

export const authRoutes = router;
"""
    return GeneratedFile(path="src/routes/auth.routes.ts", language="typescript", content=content)


def _env_example(project_slug: str) -> GeneratedFile:
    content = f"""\
# Base de datos PostgreSQL
DATABASE_URL="postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"

# Servidor
PORT=3000
CORS_ORIGIN="http://localhost:5173"

# JWT
JWT_SECRET="genera con: openssl rand -hex 32"
"""
    return GeneratedFile(path=".env.example", language="env", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
dist/
.env
.env.local
*.log
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
