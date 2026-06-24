"""Main fallback scaffold generator dispatcher.

Detects the appropriate stack, logs the failure reason, and delegates to
the correct stack builder.
"""
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

logger = logging.getLogger(__name__)


class FallbackGenerator:
    """Generador determinista de scaffolds para cuando el LLM falla.

    Detecta el stack más apropiado a partir del CodeGenerationRequest,
    registra el motivo del fallo en los logs y genera el scaffold.
    """

    def generate(
        self,
        req: CodeGenerationRequest,
        reason: str = "LLM_UNAVAILABLE",
    ) -> CodeGenerationResponse:
        """Genera un scaffold determinista para el proyecto.

        Args:
            req: La solicitud de generación de código.
            reason: Motivo del fallo del LLM (para diagnóstico en logs).

        Returns:
            CodeGenerationResponse con los archivos generados.
        """
        stack = detect_stack(req)
        logger.warning(
            "Fallback scaffold activado. Motivo: %s | Stack: %s | Proyecto: %s",
            reason,
            stack.value,
            req.project_name,
        )
        files = self._build(stack, req)
        return CodeGenerationResponse(project_name=req.project_name, files=files)

    def _build(
        self, stack: ScaffoldStack, req: CodeGenerationRequest
    ) -> list[GeneratedFile]:
        """Despacha la generación al builder correcto según el stack detectado."""
        builders = {
            ScaffoldStack.NEXTJS: build_nextjs,
            ScaffoldStack.REACT_VITE: build_react_vite,
            ScaffoldStack.NESTJS: build_nestjs,
            ScaffoldStack.EXPRESS: build_express,
            ScaffoldStack.FASTAPI_AI: build_fastapi_ai,
            ScaffoldStack.LARAVEL: build_laravel,
            ScaffoldStack.MOBILE: build_mobile,
            ScaffoldStack.DESKTOP: build_desktop,
            ScaffoldStack.UNIVERSAL: build_universal,
        }
        builder = builders.get(stack, build_universal)
        return builder(req)
