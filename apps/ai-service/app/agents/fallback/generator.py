"""Main fallback scaffold generator dispatcher."""
import logging

from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile
from app.agents.fallback.detector import ScaffoldStack, detect_stack
from app.agents.fallback.stacks.nextjs import build_nextjs
from app.agents.fallback.stacks.react_vite import build_react_vite
from app.agents.fallback.stacks.nestjs import build_nestjs
from app.agents.fallback.stacks.express_ts import build_express
from app.agents.fallback.stacks.fastapi_ai import build_fastapi_ai
from app.agents.fallback.stacks.laravel import build_laravel
from app.agents.fallback.stacks.mobile import build_mobile
from app.agents.fallback.stacks.desktop import build_desktop
from app.agents.fallback.stacks.universal import build_universal
from app.agents.fallback.stacks.angular import build_angular
from app.agents.fallback.stacks.tauri import build_tauri
from app.agents.fallback.stacks.node_postgres import build_node_postgres
from app.agents.fallback.stacks.firebase import build_firebase
from app.agents.fallback.stacks.supabase import build_supabase
from app.agents.fallback.stacks.sveltekit import build_sveltekit
from app.agents.fallback.stacks.flask_app import build_flask
from app.agents.fallback.stacks.vue_vite import build_vue_vite
from app.agents.fallback.stacks.astro import build_astro
from app.agents.fallback.stacks.go_gin import build_go_gin

logger = logging.getLogger(__name__)

_BUILDERS = {
    ScaffoldStack.NEXTJS:        build_nextjs,
    ScaffoldStack.REACT_VITE:    build_react_vite,
    ScaffoldStack.NESTJS:        build_nestjs,
    ScaffoldStack.EXPRESS:       build_express,
    ScaffoldStack.FASTAPI_AI:    build_fastapi_ai,
    ScaffoldStack.LARAVEL:       build_laravel,
    ScaffoldStack.MOBILE:        build_mobile,
    ScaffoldStack.DESKTOP:       build_desktop,
    ScaffoldStack.UNIVERSAL:     build_universal,
    ScaffoldStack.ANGULAR:       build_angular,
    ScaffoldStack.TAURI:         build_tauri,
    ScaffoldStack.NODE_POSTGRES: build_node_postgres,
    ScaffoldStack.FIREBASE:      build_firebase,
    ScaffoldStack.SUPABASE:      build_supabase,
    ScaffoldStack.SVELTEKIT:     build_sveltekit,
    ScaffoldStack.FLASK:         build_flask,
    ScaffoldStack.VUE_VITE:      build_vue_vite,
    ScaffoldStack.ASTRO:         build_astro,
    ScaffoldStack.GO_GIN:        build_go_gin,
}


class FallbackGenerator:
    """Generador determinista de scaffolds para cuando el LLM falla."""

    def generate(
        self,
        req: CodeGenerationRequest,
        reason: str = "LLM_UNAVAILABLE",
    ) -> CodeGenerationResponse:
        stack = detect_stack(req)
        logger.warning(
            "Fallback scaffold activado. Motivo: %s | Stack: %s | Proyecto: %s",
            reason,
            stack.value,
            req.project_name,
        )
        builder = _BUILDERS.get(stack, build_universal)
        files: list[GeneratedFile] = builder(req)
        return CodeGenerationResponse(project_name=req.project_name, files=files)
