"""NestJS 11 + TypeScript + Prisma + PostgreSQL + Swagger scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.prisma import generate_prisma_schema, generate_seed_ts
from app.agents.fallback.shared.docker import generate_docker_compose, generate_node_dockerfile
from app.agents.fallback.shared.readme import generate_readme


def build_nestjs(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold NestJS 11 completo."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal = pascal(primary.get("name", "Item"))
    entity_camel = camel(primary.get("name", "Item"))
    entity_slug = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug)

    files: list[GeneratedFile] = [
        _package_json(project_slug),
        _tsconfig(),
        _tsconfig_build(),
        _main_ts(project_slug),
        _app_module(entity_slug, entity_pascal, req.needs_auth),
        _prisma_module(),
        _prisma_service(),
        _entity_module(entity_slug, entity_pascal, entity_camel),
        _entity_controller(entity_slug, entity_pascal, entity_camel, entity_plural),
        _entity_service(entity_slug, entity_pascal, entity_camel),
        _create_dto(entity_slug, entity_pascal),
        _update_dto(entity_slug, entity_pascal),
        _health_controller(),
        _health_module(),
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
            stack_summary="NestJS 11 · TypeScript · Prisma · PostgreSQL · Swagger",
            setup_commands=[
                "docker compose up -d",
                "npm install",
                "npx prisma migrate dev --name init",
                "npx prisma db seed",
                "npm run build",
                "node dist/main",
            ],
            env_vars=[
                ("DATABASE_URL", f"postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"),
                ("JWT_SECRET", "genera con: openssl rand -hex 32"),
                ("PORT", "3000"),
            ],
            api_port=3000,
        ),
        generate_node_dockerfile(port=3000, entry="dist/main.js", needs_prisma=True),
        generate_docker_compose(project_slug, needs_postgres=True, api_port=3000),
    ]

    if req.needs_auth:
        files += _auth_files(project_slug)

    return files


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "build": "nest build",
    "start": "nest start",
    "start:dev": "nest start --watch",
    "start:prod": "node dist/main",
    "lint": "eslint src",
    "test": "jest",
    "db:migrate": "prisma migrate dev",
    "db:seed": "ts-node prisma/seed.ts",
    "db:studio": "prisma studio"
  }},
  "dependencies": {{
    "@nestjs/common": "^11.0.0",
    "@nestjs/core": "^11.0.0",
    "@nestjs/platform-fastify": "^11.0.0",
    "@nestjs/swagger": "^8.0.0",
    "@prisma/client": "^5.22.0",
    "bcryptjs": "^2.4.3",
    "class-transformer": "^0.5.1",
    "class-validator": "^0.14.1",
    "@nestjs/jwt": "^11.0.0",
    "reflect-metadata": "^0.2.2",
    "rxjs": "^7.8.1"
  }},
  "devDependencies": {{
    "@nestjs/cli": "^11.0.0",
    "@types/node": "^22.0.0",
    "@types/bcryptjs": "^2.4.6",
    "prisma": "^5.22.0",
    "ts-node": "^10.9.2",
    "typescript": "^5.7.0"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "compilerOptions": {
    "module": "commonjs",
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "target": "ES2022",
    "sourceMap": true,
    "outDir": "./dist",
    "baseUrl": "./",
    "incremental": true,
    "skipLibCheck": true,
    "strictNullChecks": true,
    "noImplicitAny": true,
    "strictBindCallApply": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true
  }
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _tsconfig_build() -> GeneratedFile:
    content = """\
{
  "extends": "./tsconfig.json",
  "exclude": ["node_modules", "test", "dist", "**/*spec.ts"]
}
"""
    return GeneratedFile(path="tsconfig.build.json", language="json", content=content)


def _main_ts(project_slug: str) -> GeneratedFile:
    content = f"""\
import {{ NestFactory }} from "@nestjs/core";
import {{
  FastifyAdapter,
  NestFastifyApplication,
}} from "@nestjs/platform-fastify";
import {{ ValidationPipe }} from "@nestjs/common";
import {{ SwaggerModule, DocumentBuilder }} from "@nestjs/swagger";
import {{ AppModule }} from "./app.module";

async function bootstrap() {{
  const app = await NestFactory.create<NestFastifyApplication>(
    AppModule,
    new FastifyAdapter({{ logger: true }})
  );

  // Habilitar CORS para el frontend
  app.enableCors({{
    origin: process.env.WEB_URL ?? "http://localhost:5173",
  }});

  // Validación global con class-validator
  app.useGlobalPipes(
    new ValidationPipe({{
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }})
  );

  // Documentación Swagger en /api/docs
  const config = new DocumentBuilder()
    .setTitle("{project_slug} API")
    .setDescription("API REST generada con ProgresIA Studio")
    .setVersion("1.0")
    .addBearerAuth()
    .build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup("api/docs", app, document);

  const port = Number(process.env.PORT ?? 3000);
  await app.listen(port, "0.0.0.0");
  console.log(`API activa en http://0.0.0.0:${{port}}`);
  console.log(`Swagger en http://0.0.0.0:${{port}}/api/docs`);
}}

bootstrap();
"""
    return GeneratedFile(path="src/main.ts", language="typescript", content=content)


def _app_module(
    entity_slug: str,
    entity_pascal: str,
    needs_auth: bool,
) -> GeneratedFile:
    auth_import = 'import { AuthModule } from "./auth/auth.module";\n' if needs_auth else ""
    auth_module = ", AuthModule" if needs_auth else ""
    content = f"""\
import {{ Module }} from "@nestjs/common";
import {{ PrismaModule }} from "./prisma/prisma.module";
import {{ {entity_pascal}Module }} from "./{entity_slug}/{entity_slug}.module";
import {{ HealthModule }} from "./health/health.module";
{auth_import}

@Module({{
  imports: [PrismaModule, {entity_pascal}Module, HealthModule{auth_module}],
}})
export class AppModule {{}}
"""
    return GeneratedFile(path="src/app.module.ts", language="typescript", content=content)


def _prisma_module() -> GeneratedFile:
    return GeneratedFile(
        path="src/prisma/prisma.module.ts",
        language="typescript",
        content="""\
import { Global, Module } from "@nestjs/common";
import { PrismaService } from "./prisma.service";

@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
""",
    )


def _prisma_service() -> GeneratedFile:
    return GeneratedFile(
        path="src/prisma/prisma.service.ts",
        language="typescript",
        content="""\
import { Injectable, OnModuleDestroy, OnModuleInit } from "@nestjs/common";
import { PrismaClient } from "@prisma/client";

@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy
{
  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
""",
    )


def _entity_module(entity_slug: str, entity_pascal: str, entity_camel: str) -> GeneratedFile:
    content = f"""\
import {{ Module }} from "@nestjs/common";
import {{ {entity_pascal}Controller }} from "./{entity_slug}.controller";
import {{ {entity_pascal}Service }} from "./{entity_slug}.service";
import {{ PrismaModule }} from "../prisma/prisma.module";

@Module({{
  imports: [PrismaModule],
  controllers: [{entity_pascal}Controller],
  providers: [{entity_pascal}Service],
}})
export class {entity_pascal}Module {{}}
"""
    return GeneratedFile(path=f"src/{entity_slug}/{entity_slug}.module.ts", language="typescript", content=content)


def _entity_controller(entity_slug: str, entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Param,
  Body,
  HttpCode,
  HttpStatus,
}} from "@nestjs/common";
import {{ ApiTags, ApiOperation, ApiBearerAuth }} from "@nestjs/swagger";
import {{ {entity_pascal}Service }} from "./{entity_slug}.service";
import {{ Create{entity_pascal}Dto }} from "./dto/create-{entity_slug}.dto";
import {{ Update{entity_pascal}Dto }} from "./dto/update-{entity_slug}.dto";

@ApiTags("{entity_plural}")
@Controller("{entity_plural}")
export class {entity_pascal}Controller {{
  constructor(private readonly {entity_camel}Service: {entity_pascal}Service) {{}}

  @Get()
  @ApiOperation({{ summary: "Obtener todos los registros" }})
  findAll() {{
    return this.{entity_camel}Service.findAll();
  }}

  @Get(":id")
  @ApiOperation({{ summary: "Obtener un registro por ID" }})
  findOne(@Param("id") id: string) {{
    return this.{entity_camel}Service.findOne(id);
  }}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({{ summary: "Crear un nuevo registro" }})
  create(@Body() dto: Create{entity_pascal}Dto) {{
    return this.{entity_camel}Service.create(dto);
  }}

  @Put(":id")
  @ApiOperation({{ summary: "Actualizar un registro" }})
  update(@Param("id") id: string, @Body() dto: Update{entity_pascal}Dto) {{
    return this.{entity_camel}Service.update(id, dto);
  }}

  @Delete(":id")
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({{ summary: "Eliminar un registro" }})
  remove(@Param("id") id: string) {{
    return this.{entity_camel}Service.remove(id);
  }}
}}
"""
    return GeneratedFile(path=f"src/{entity_slug}/{entity_slug}.controller.ts", language="typescript", content=content)


def _entity_service(entity_slug: str, entity_pascal: str, entity_camel: str) -> GeneratedFile:
    content = f"""\
import {{ Injectable, NotFoundException }} from "@nestjs/common";
import {{ PrismaService }} from "../prisma/prisma.service";
import {{ Create{entity_pascal}Dto }} from "./dto/create-{entity_slug}.dto";
import {{ Update{entity_pascal}Dto }} from "./dto/update-{entity_slug}.dto";

@Injectable()
export class {entity_pascal}Service {{
  constructor(private readonly prisma: PrismaService) {{}}

  async findAll() {{
    return this.prisma.{entity_camel}.findMany({{
      orderBy: {{ createdAt: "desc" }},
    }});
  }}

  async findOne(id: string) {{
    const item = await this.prisma.{entity_camel}.findUnique({{ where: {{ id }} }});
    if (!item) throw new NotFoundException(`{entity_pascal} con ID ${{id}} no encontrado`);
    return item;
  }}

  async create(dto: Create{entity_pascal}Dto) {{
    return this.prisma.{entity_camel}.create({{
      data: dto,
    }});
  }}

  async update(id: string, dto: Update{entity_pascal}Dto) {{
    await this.findOne(id); // Verifica que existe
    return this.prisma.{entity_camel}.update({{
      where: {{ id }},
      data: dto,
    }});
  }}

  async remove(id: string) {{
    await this.findOne(id); // Verifica que existe
    await this.prisma.{entity_camel}.delete({{ where: {{ id }} }});
  }}
}}
"""
    return GeneratedFile(path=f"src/{entity_slug}/{entity_slug}.service.ts", language="typescript", content=content)


def _create_dto(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
import {{ IsString, IsOptional, MinLength, MaxLength }} from "class-validator";
import {{ ApiProperty, ApiPropertyOptional }} from "@nestjs/swagger";

export class Create{entity_pascal}Dto {{
  @ApiProperty({{ description: "Nombre del {entity_pascal.lower()}", example: "{entity_pascal} de ejemplo" }})
  @IsString()
  @MinLength(1)
  @MaxLength(200)
  name!: string;

  @ApiPropertyOptional({{ description: "Descripción opcional" }})
  @IsOptional()
  @IsString()
  @MaxLength(1000)
  description?: string;
}}
"""
    return GeneratedFile(path=f"src/{entity_slug}/dto/create-{entity_slug}.dto.ts", language="typescript", content=content)


def _update_dto(entity_slug: str, entity_pascal: str) -> GeneratedFile:
    content = f"""\
import {{ PartialType }} from "@nestjs/swagger";
import {{ Create{entity_pascal}Dto }} from "./create-{entity_slug}.dto";

// PartialType hace todos los campos opcionales para el UPDATE
export class Update{entity_pascal}Dto extends PartialType(Create{entity_pascal}Dto) {{}}
"""
    return GeneratedFile(path=f"src/{entity_slug}/dto/update-{entity_slug}.dto.ts", language="typescript", content=content)


def _health_controller() -> GeneratedFile:
    return GeneratedFile(
        path="src/health/health.controller.ts",
        language="typescript",
        content="""\
import { Controller, Get } from "@nestjs/common";
import { ApiTags, ApiOperation } from "@nestjs/swagger";

@ApiTags("health")
@Controller("health")
export class HealthController {
  @Get()
  @ApiOperation({ summary: "Comprueba que el servidor está activo" })
  check() {
    return {
      status: "ok",
      timestamp: new Date().toISOString(),
    };
  }
}
""",
    )


def _health_module() -> GeneratedFile:
    return GeneratedFile(
        path="src/health/health.module.ts",
        language="typescript",
        content="""\
import { Module } from "@nestjs/common";
import { HealthController } from "./health.controller";

@Module({
  controllers: [HealthController],
})
export class HealthModule {}
""",
    )


def _auth_files(project_slug: str) -> list[GeneratedFile]:
    """Genera los archivos de autenticación JWT básica."""
    return [
        GeneratedFile(
            path="src/auth/auth.module.ts",
            language="typescript",
            content="""\
import { Module } from "@nestjs/common";
import { JwtModule } from "@nestjs/jwt";
import { AuthController } from "./auth.controller";
import { AuthService } from "./auth.service";
import { PrismaModule } from "../prisma/prisma.module";

@Module({
  imports: [
    PrismaModule,
    JwtModule.register({
      secret: process.env.JWT_SECRET ?? "dev_secret",
      signOptions: { expiresIn: "7d" },
    }),
  ],
  controllers: [AuthController],
  providers: [AuthService],
  exports: [AuthService],
})
export class AuthModule {}
""",
        ),
        GeneratedFile(
            path="src/auth/auth.service.ts",
            language="typescript",
            content="""\
import { Injectable, UnauthorizedException } from "@nestjs/common";
import { JwtService } from "@nestjs/jwt";
import { PrismaService } from "../prisma/prisma.service";
import * as bcrypt from "bcryptjs";

@Injectable()
export class AuthService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwt: JwtService
  ) {}

  async register(email: string, password: string, name: string) {
    const hash = await bcrypt.hash(password, 12);
    const user = await this.prisma.user.create({
      data: { email, passwordHash: hash, name },
      select: { id: true, email: true, name: true, createdAt: true },
    });
    const token = this.jwt.sign({ sub: user.id, email: user.email });
    return { user, token };
  }

  async login(email: string, password: string) {
    const user = await this.prisma.user.findUnique({ where: { email } });
    if (!user) throw new UnauthorizedException("Credenciales incorrectas");
    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) throw new UnauthorizedException("Credenciales incorrectas");
    const token = this.jwt.sign({ sub: user.id, email: user.email });
    const { passwordHash: _, ...safeUser } = user;
    return { user: safeUser, token };
  }
}
""",
        ),
        GeneratedFile(
            path="src/auth/auth.controller.ts",
            language="typescript",
            content="""\
import { Controller, Post, Body } from "@nestjs/common";
import { ApiTags, ApiOperation } from "@nestjs/swagger";
import { AuthService } from "./auth.service";
import { IsEmail, IsString, MinLength } from "class-validator";
import { ApiProperty } from "@nestjs/swagger";

class RegisterDto {
  @ApiProperty() @IsEmail() email!: string;
  @ApiProperty() @IsString() @MinLength(2) name!: string;
  @ApiProperty() @IsString() @MinLength(8) password!: string;
}

class LoginDto {
  @ApiProperty() @IsEmail() email!: string;
  @ApiProperty() @IsString() password!: string;
}

@ApiTags("auth")
@Controller("auth")
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post("register")
  @ApiOperation({ summary: "Registrar nuevo usuario" })
  register(@Body() dto: RegisterDto) {
    return this.authService.register(dto.email, dto.password, dto.name);
  }

  @Post("login")
  @ApiOperation({ summary: "Iniciar sesión" })
  login(@Body() dto: LoginDto) {
    return this.authService.login(dto.email, dto.password);
  }
}
""",
        ),
    ]


def _env_example(project_slug: str) -> GeneratedFile:
    content = f"""\
# Base de datos PostgreSQL
DATABASE_URL="postgresql://{project_slug}:{project_slug}@localhost:5432/{project_slug}_db"

# API
PORT=3000
WEB_URL="http://localhost:5173"

# JWT
JWT_SECRET="genera con: openssl rand -hex 32"
JWT_EXPIRES_IN="7d"
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
