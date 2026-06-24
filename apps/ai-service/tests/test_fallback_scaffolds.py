import pytest

from app.agents.fallback.detector import ScaffoldStack, detect_stack
from app.agents.fallback.generator import FallbackGenerator
from app.schemas.codegen import CodeGenerationRequest


STACK_CASES = [
    ("NEXTJS_APP", ["Next.js"], ScaffoldStack.NEXTJS),
    ("REACT_VITE", ["React", "Vite"], ScaffoldStack.REACT_VITE),
    ("NESTJS_REACT", ["NestJS"], ScaffoldStack.NESTJS),
    ("REACT_EXPRESS", ["Express"], ScaffoldStack.EXPRESS),
    ("FASTAPI_AI", ["FastAPI"], ScaffoldStack.FASTAPI_AI),
    ("LARAVEL_MONOLITH", ["Laravel"], ScaffoldStack.LARAVEL),
    ("REACT_NATIVE", ["React Native"], ScaffoldStack.MOBILE),
    ("ELECTRON", ["Electron"], ScaffoldStack.DESKTOP),
    ("ANGULAR", ["Angular"], ScaffoldStack.ANGULAR),
    ("TAURI", ["Tauri"], ScaffoldStack.TAURI),
    ("NODE_POSTGRES", ["Node.js", "PostgreSQL"], ScaffoldStack.NODE_POSTGRES),
    ("FIREBASE_REACT", ["Firebase"], ScaffoldStack.FIREBASE),
    ("SUPABASE_NEXTJS", ["Supabase"], ScaffoldStack.SUPABASE),
    ("SVELTEKIT", ["SvelteKit"], ScaffoldStack.SVELTEKIT),
    ("FLASK_REST", ["Flask"], ScaffoldStack.FLASK),
    ("VUE_VITE", ["Vue", "Vite"], ScaffoldStack.VUE_VITE),
    ("ASTRO_STATIC", ["Astro"], ScaffoldStack.ASTRO),
    ("GO_GIN", ["Go", "Gin"], ScaffoldStack.GO_GIN),
    ("UNKNOWN", ["Unknown"], ScaffoldStack.UNIVERSAL),
]


def request_for(architecture: str, stack: list[str]) -> CodeGenerationRequest:
    return CodeGenerationRequest(
        project_name="Fallback smoke test",
        sector="General",
        modules=["Auth", "Projects"],
        requirements=[],
        needs_auth=True,
        stack=stack,
        architecture_type=architecture,
    )


@pytest.mark.parametrize(("architecture", "stack", "expected"), STACK_CASES)
def test_detects_supported_stack(
    architecture: str,
    stack: list[str],
    expected: ScaffoldStack,
) -> None:
    assert detect_stack(request_for(architecture, stack)) == expected


@pytest.mark.parametrize(("architecture", "stack", "expected"), STACK_CASES)
def test_generated_scaffold_has_required_files_and_unique_paths(
    architecture: str,
    stack: list[str],
    expected: ScaffoldStack,
) -> None:
    request = request_for(architecture, stack)
    assert detect_stack(request) == expected

    result = FallbackGenerator().generate(request)
    paths = [file.path for file in result.files]

    assert "README.md" in paths
    assert ".env.example" in paths
    assert len(paths) == len(set(paths))


def test_beginner_web_projects_use_express_scaffold() -> None:
    request = request_for("NESTJS_REACT", ["NestJS", "React"]).model_copy(
        update={"technical_level": "BEGINNER"}
    )

    assert detect_stack(request) == ScaffoldStack.EXPRESS


def test_nestjs_scaffold_includes_runtime_modules_and_dependencies() -> None:
    result = FallbackGenerator().generate(request_for("NESTJS_REACT", ["NestJS"]))
    files = {file.path: file.content for file in result.files}

    assert "src/prisma/prisma.module.ts" in files
    assert "src/prisma/prisma.service.ts" in files
    assert "src/health/health.module.ts" in files
    assert "@nestjs/jwt" in files["package.json"]
    assert "bcryptjs" in files["package.json"]
    assert "AuthModule" in files["src/app.module.ts"]
