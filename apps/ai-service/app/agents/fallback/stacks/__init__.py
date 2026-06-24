"""Stack-specific scaffold generators for the fallback system."""
from app.agents.fallback.stacks.nextjs import build_nextjs
from app.agents.fallback.stacks.react_vite import build_react_vite
from app.agents.fallback.stacks.nestjs import build_nestjs
from app.agents.fallback.stacks.express_ts import build_express
from app.agents.fallback.stacks.fastapi_ai import build_fastapi_ai
from app.agents.fallback.stacks.laravel import build_laravel
from app.agents.fallback.stacks.mobile import build_mobile
from app.agents.fallback.stacks.desktop import build_desktop
from app.agents.fallback.stacks.universal import build_universal

__all__ = [
    "build_nextjs",
    "build_react_vite",
    "build_nestjs",
    "build_express",
    "build_fastapi_ai",
    "build_laravel",
    "build_mobile",
    "build_desktop",
    "build_universal",
]
