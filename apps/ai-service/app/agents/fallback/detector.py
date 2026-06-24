"""Stack detector for the fallback scaffold system.

Determines which stack to use based on architecture_type, stack list,
and requirements text from the CodeGenerationRequest.
"""
from enum import Enum

from app.schemas.codegen import CodeGenerationRequest


class ScaffoldStack(str, Enum):
    """Stacks disponibles para la generación determinista de scaffolds."""
    NEXTJS = "nextjs"
    REACT_VITE = "react_vite"
    NESTJS = "nestjs"
    EXPRESS = "express"
    FASTAPI_AI = "fastapi_ai"
    LARAVEL = "laravel"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    UNIVERSAL = "universal"


def detect_stack(req: CodeGenerationRequest) -> ScaffoldStack:
    """Detecta el stack más apropiado para la generación del scaffold.

    Orden de prioridad:
    1. MOBILE — Flutter, React Native, Expo
    2. DESKTOP — Electron, Tauri
    3. LARAVEL — Laravel, PHP, Blade
    4. FASTAPI_AI — FastAPI, Django, Python, RAG, LLM
    5. NESTJS — NestJS
    6. NEXTJS — Next.js, Academia, tRPC
    7. EXPRESS — Express, React+Express
    8. REACT_VITE — React SPA
    9. UNIVERSAL — fallback por defecto
    """
    arch = (req.architecture_type or "").upper()
    stack_lower = " ".join(req.stack).lower()
    reqs_text = " ".join(
        r.get("title", "") + " " + r.get("description", "")
        for r in req.requirements[:10]
    ).lower()

    combined = f"{stack_lower} {reqs_text}"

    # 1. MOBILE
    if (
        any(k in arch for k in ("FLUTTER", "REACT_NATIVE", "MOBILE", "EXPO"))
        or any(k in stack_lower for k in ("react native", "expo", "flutter", "react-native"))
    ):
        return ScaffoldStack.MOBILE

    # 2. DESKTOP
    if (
        any(k in arch for k in ("ELECTRON", "TAURI", "DESKTOP"))
        or any(k in stack_lower for k in ("electron", "tauri"))
    ):
        return ScaffoldStack.DESKTOP

    # 3. LARAVEL
    if (
        any(k in arch for k in ("LARAVEL",))
        or any(k in stack_lower for k in ("laravel", "php", "blade", "eloquent"))
    ):
        return ScaffoldStack.LARAVEL

    # 4. FASTAPI / AI
    if (
        any(k in arch for k in ("FASTAPI", "DJANGO", "PYTHON", "FASTAPI_AI"))
        or any(k in stack_lower for k in ("fastapi", "django", "flask", "python", "langchain", "rag", "chromadb"))
        or any(k in combined for k in ("chat", "rag", "embeddings", "llm", "ai agent", "agente ia"))
    ):
        return ScaffoldStack.FASTAPI_AI

    # 5. NESTJS
    if (
        "NESTJS" in arch
        or "nestjs" in stack_lower
        or "nest.js" in stack_lower
    ):
        return ScaffoldStack.NESTJS

    # 6. NEXTJS
    if (
        any(k in arch for k in ("NEXTJS", "NEXTJS_APP", "ACADEMIA"))
        or any(k in stack_lower for k in ("next.js", "nextjs", "trpc", "t3"))
    ):
        return ScaffoldStack.NEXTJS

    # 7. EXPRESS
    if (
        any(k in arch for k in ("REACT_EXPRESS", "EXPRESS"))
        or any(k in stack_lower for k in ("express",))
    ):
        return ScaffoldStack.EXPRESS

    # 8. REACT_VITE
    if any(k in stack_lower for k in ("react", "vite", "spa")):
        return ScaffoldStack.REACT_VITE

    # 9. UNIVERSAL (default)
    return ScaffoldStack.UNIVERSAL
