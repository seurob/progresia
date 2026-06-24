"""Stack detector for the fallback scaffold system."""
from enum import Enum

from app.schemas.codegen import CodeGenerationRequest


class ScaffoldStack(str, Enum):
    """Stacks disponibles para la generación determinista de scaffolds."""
    NEXTJS        = "nextjs"
    REACT_VITE    = "react_vite"
    NESTJS        = "nestjs"
    EXPRESS       = "express"
    FASTAPI_AI    = "fastapi_ai"
    LARAVEL       = "laravel"
    MOBILE        = "mobile"
    DESKTOP       = "desktop"
    UNIVERSAL     = "universal"
    ANGULAR       = "angular"
    TAURI         = "tauri"
    NODE_POSTGRES = "node_postgres"
    FIREBASE      = "firebase"
    SUPABASE      = "supabase"
    SVELTEKIT     = "sveltekit"
    FLASK         = "flask"
    VUE_VITE      = "vue_vite"
    ASTRO         = "astro"
    GO_GIN        = "go_gin"


# (stack, arch_type_substrings, stack_keywords, free-text_keywords)
# Evaluated in order; first match wins.
_RULES: list[tuple[ScaffoldStack, tuple, tuple, tuple]] = [
    (ScaffoldStack.MOBILE,        ("FLUTTER", "REACT_NATIVE", "MOBILE", "EXPO"),              ("react native", "expo", "flutter", "react-native"),           ()),
    (ScaffoldStack.DESKTOP,       ("ELECTRON", "DESKTOP"),                                    ("electron",),                                                  ()),
    (ScaffoldStack.TAURI,         ("TAURI",),                                                 ("tauri",),                                                     ()),
    (ScaffoldStack.GO_GIN,        ("GO_GIN", "GO_FIBER", "GOLANG"),                           ("golang", "gin framework", "go + gin", "gorm"),                ()),
    (ScaffoldStack.LARAVEL,       ("LARAVEL",),                                               ("laravel", "php", "blade", "eloquent"),                        ()),
    (ScaffoldStack.FLASK,         ("FLASK", "FLASK_REST"),                                    ("flask",),                                                     ()),
    (ScaffoldStack.FASTAPI_AI,    ("FASTAPI", "DJANGO", "PYTHON", "FASTAPI_AI"),              ("fastapi", "django", "python", "langchain", "rag", "chromadb"), ("chat", "rag", "embeddings", "llm", "ai agent", "agente ia")),
    (ScaffoldStack.FIREBASE,      ("FIREBASE", "FIREBASE_REACT"),                             ("firebase", "firestore", "cloud functions"),                   ()),
    (ScaffoldStack.SUPABASE,      ("SUPABASE", "SUPABASE_NEXTJS"),                            ("supabase",),                                                  ()),
    (ScaffoldStack.ANGULAR,       ("ANGULAR", "ANGULAR_NESTJS", "ANGULAR_FASTAPI"),           ("angular",),                                                   ()),
    (ScaffoldStack.VUE_VITE,      ("VUE_VITE", "VUE_FASTAPI", "VUE_LARAVEL", "VUE_NESTJS"),  ("vue", "nuxt", "pinia"),                                       ()),
    (ScaffoldStack.SVELTEKIT,     ("SVELTE_KIT", "SVELTEKIT"),                               ("svelte", "sveltekit"),                                        ()),
    (ScaffoldStack.ASTRO,         ("ASTRO", "ASTRO_STATIC"),                                  ("astro",),                                                     ("static site", "landing page", "blog", "portfolio", "marketing")),
    (ScaffoldStack.NODE_POSTGRES, ("NODE_POSTGRES", "NODE_PG"),                               (),                                                             ()),
    (ScaffoldStack.NESTJS,        ("NESTJS",),                                                ("nestjs", "nest.js"),                                          ()),
    (ScaffoldStack.NEXTJS,        ("NEXTJS", "NEXTJS_APP", "ACADEMIA"),                       ("next.js", "nextjs", "trpc", "t3"),                            ()),
    (ScaffoldStack.EXPRESS,       ("REACT_EXPRESS", "EXPRESS"),                               ("express",),                                                   ()),
    (ScaffoldStack.REACT_VITE,    (),                                                         ("react", "vite", "spa"),                                       ()),
]


def detect_stack(req: CodeGenerationRequest) -> ScaffoldStack:
    """Detecta el stack más apropiado para la generación del scaffold.

    Evalúa la tabla _RULES en orden de prioridad; devuelve el primer match.
    UNIVERSAL es el fallback cuando ninguna regla coincide.
    """
    arch = (req.architecture_type or "").upper()
    stack_lower = " ".join(req.stack).lower()
    combined = stack_lower + " " + " ".join(
        r.get("title", "") + " " + r.get("description", "")
        for r in req.requirements[:10]
    ).lower()

    for stack_val, arch_keys, stack_keys, text_keys in _RULES:
        if (
            any(k in arch for k in arch_keys)
            or any(k in stack_lower for k in stack_keys)
            or any(k in combined for k in text_keys)
        ):
            return stack_val

    return ScaffoldStack.UNIVERSAL
