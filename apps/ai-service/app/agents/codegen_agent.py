import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import TaskType, get_llm
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert fullstack developer generating a project scaffold for an MVP.

Given a project specification, generate the key starter files for a monorepo with:
- React 19 + Vite + TypeScript frontend (apps/web)
- NestJS + Prisma + PostgreSQL backend (apps/api)
- FastAPI + Python AI service (apps/ai-service) — only if needs_ai is true
- Docker Compose for local infrastructure

Generate EXACTLY these files (no more, no less):
1. docker-compose.yml — PostgreSQL + Redis services
2. apps/api/src/app.module.ts — NestJS root module importing the right feature modules
3. apps/api/prisma/schema.prisma — Prisma schema with models for the core domain
4. apps/web/src/App.tsx — React root with routes for the main pages
5. apps/web/src/pages/DashboardPage.tsx — Main dashboard with a list of the core entities
6. README.md — Setup instructions and architecture overview

Use the modules list to name entities. Keep each file under 80 lines.
Respond in the same language as the project name."""


def _build_human_message(req: CodeGenerationRequest) -> str:
    modules = ", ".join(req.modules) if req.modules else "Core entities"
    stack = ", ".join(req.stack)
    reqs = "\n".join(
        f"  - {r.get('id', '')}: {r.get('title', '')}" for r in req.requirements[:8]
    )
    return f"""Project: {req.project_name}
Sector: {req.sector}
Modules / bounded contexts: {modules}
Tech stack: {stack}
Needs auth: {req.needs_auth}
Needs admin panel: {req.needs_admin_panel}
Needs AI service: {req.needs_ai}

Top requirements:
{reqs if reqs else "  (none provided)"}"""


class CodeGenerationAgent:
    def generate(
        self,
        req: CodeGenerationRequest,
        llm: BaseChatModel | None = None,
        task: TaskType = "code",
    ) -> CodeGenerationResponse:
        resolved_llm = llm if llm is not None else get_llm(task)

        if resolved_llm is not None:
            try:
                structured = resolved_llm.with_structured_output(CodeGenerationResponse)
                result = structured.invoke([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=_build_human_message(req)),
                ])
                if isinstance(result, CodeGenerationResponse) and result.files:
                    return result
            except Exception as exc:
                logger.warning("LLM code generation failed, using scaffold fallback: %s", exc)

        return self._scaffold_fallback(req)

    def _scaffold_fallback(self, req: CodeGenerationRequest) -> CodeGenerationResponse:
        slug = req.project_name.lower().replace(" ", "-")
        modules_comment = ", ".join(req.modules) if req.modules else "Core"

        files: list[GeneratedFile] = [
            GeneratedFile(
                path="docker-compose.yml",
                language="yaml",
                content=f"""services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: {slug}
      POSTGRES_PASSWORD: {slug}
      POSTGRES_DB: {slug}_db
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  postgres_data:
""",
            ),
            GeneratedFile(
                path="apps/api/src/app.module.ts",
                language="typescript",
                content=f"""import {{ Module }} from '@nestjs/common';
import {{ ConfigModule }} from '@nestjs/config';
import {{ PrismaModule }} from './database/prisma.module';
import {{ AuthModule }} from './modules/auth/auth.module';
// TODO: add feature modules — {modules_comment}

@Module({{
  imports: [
    ConfigModule.forRoot({{ isGlobal: true }}),
    PrismaModule,
    AuthModule,
  ],
}})
export class AppModule {{}}
""",
            ),
            GeneratedFile(
                path="apps/api/prisma/schema.prisma",
                language="prisma",
                content=f"""generator client {{
  provider = "prisma-client-js"
}}

datasource db {{
  provider = "postgresql"
  url      = env("DATABASE_URL")
}}

{"model User { id String @id @default(uuid()) email String @unique name String passwordHash String createdAt DateTime @default(now()) }" if req.needs_auth else ""}

// TODO: add domain models for {modules_comment}
""",
            ),
            GeneratedFile(
                path="apps/web/src/App.tsx",
                language="typescript",
                content=f"""import {{ BrowserRouter, Route, Routes }} from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
{"import LoginPage from './pages/LoginPage';" if req.needs_auth else ""}

export default function App() {{
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={{<DashboardPage />}} />
        {"<Route path='/login' element={<LoginPage />} />" if req.needs_auth else ""}
      </Routes>
    </BrowserRouter>
  );
}}
""",
            ),
            GeneratedFile(
                path="apps/web/src/pages/DashboardPage.tsx",
                language="typescript",
                content=f"""// {req.project_name} — Dashboard
// Modules: {modules_comment}

export default function DashboardPage() {{
  return (
    <main>
      <h1>{req.project_name}</h1>
      <p>Sector: {req.sector}</p>
      {{/* TODO: implement dashboard for {modules_comment} */}}
    </main>
  );
}}
""",
            ),
            GeneratedFile(
                path="README.md",
                language="markdown",
                content=f"""# {req.project_name}

> Generated by ProgresIA Studio

## Stack

{chr(10).join(f'- {t}' for t in req.stack)}

## Setup

```bash
docker compose up -d
cd apps/api && npm install && npx prisma migrate dev
cd apps/web && npm install && npm run dev
```

## Modules

{chr(10).join(f'- {m}' for m in req.modules) if req.modules else '- (pending definition)'}
""",
            ),
        ]

        return CodeGenerationResponse(project_name=req.project_name, files=files)
