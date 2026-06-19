import json
import logging
import re

from fastapi import APIRouter, HTTPException, status

from app.agents.architecture_agent import ArchitectureAgent
from app.agents.issue_generator_agent import IssueGeneratorAgent
from app.agents.codegen_agent import CodeGenerationAgent
from app.agents.product_agent import ProductAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.tutorial_agent import TutorialAgent
from app.core.llm import get_llm
from app.schemas.architecture import ArchitectureRecommendation, ArchitectureRequest
from app.schemas.issues import IssueGenerationRequest, IssueGenerationResponse
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse
from app.schemas.idea import IdeaRequest
from app.schemas.openspec import OpenSpecResponse
from app.schemas.requirements import RequirementsResponse
from app.schemas.suggestion import FeatureSuggestionRequest, FeatureSuggestionResponse
from app.schemas.tutorial import TutorialRequest, TutorialResponse

logger = logging.getLogger(__name__)

_SECTOR_FALLBACK: dict[str, list[str]] = {
    "Educacion y formacion": ["Registro de alumnos y profesores","Reserva y cancelacion de clases","Calendario de disponibilidad","Sistema de pagos y facturas","Evaluaciones y calificaciones","Mensajeria entre usuarios","Sala de videoconferencia integrada","Panel de progreso del alumno","Notificaciones por email","Generacion de certificados"],
    "Salud y bienestar": ["Historial clinico del paciente","Agenda de citas con recordatorios","Teleconsulta por video","Prescripciones digitales","Gestion de inventario medico","Portal del paciente","Integracion con wearables","Facturacion y seguros","Informes clinicos","Chat medico-paciente"],
    "E-commerce y retail": ["Catalogo de productos con filtros","Carrito y proceso de compra","Pasarela de pago segura","Gestion de inventario","Seguimiento de pedidos","Panel de vendedor","Valoraciones y resenas","Cupones y descuentos","Programa de fidelizacion","Soporte y devoluciones"],
    "Finanzas y fintech": ["Dashboard financiero personalizado","Transferencias y pagos","Historial de transacciones","Alertas de gastos","Analisis de inversiones","Integracion bancaria open banking","Firma digital de contratos","Informes fiscales","Seguridad con 2FA","Chat con asesor financiero"],
    "RRHH y empresas": ["Gestion de empleados y organigramas","Control de asistencia y fichaje","Nominas y compensaciones","Gestion de vacaciones y ausencias","Evaluacion del desempeno","Onboarding digital","Portal del empleado","Formacion interna","Reclutamiento y seleccion","Informes de RRHH"],
    "Logistica y transporte": ["Seguimiento de envios en tiempo real","Gestion de flota de vehiculos","Optimizacion de rutas con IA","Portal de clientes","Gestion de almacen","Facturacion automatica","Notificaciones de entrega","Control de incidencias","Integracion con marketplaces","Dashboard logistico"],
    "Hosteleria y turismo": ["Reservas online de habitaciones","Gestion de disponibilidad y tarifas","Check-in y check-out digital","Canal de comunicacion con huespedes","Sistema de puntos y fidelizacion","Gestion de resenias","Facturacion y cobros","Panel de limpieza y mantenimiento","Integracion con OTAs","Analisis de ocupacion"],
    "Inmobiliaria": ["Listado y busqueda de propiedades","Tour virtual 360","Gestion de contratos digitales","Portal de propietarios e inquilinos","Firma electronica","Calculo de hipotecas","Agenda de visitas","Gestion de pagos y alquileres","Valoracion automatica de propiedades","CRM inmobiliario"],
    "Tecnologia e IT": ["Gestion de proyectos y sprints","Seguimiento de incidencias y bugs","Documentacion tecnica wiki","CI/CD y despliegues","Monitorizacion y alertas","Facturacion por tiempo","Portal de clientes","Repositorio de codigo","Gestion de licencias","Dashboard de KPIs"],
}
_DEFAULT_FEATURES = ["Registro y autenticacion de usuarios","Dashboard principal con metricas","Gestion de perfiles","Busqueda y filtros avanzados","Notificaciones por email","Panel de administracion","Exportacion de datos","API documentada","Historial de actividad","Integracion con herramientas externas"]

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "progresia-ai-service"}


@router.post("/analyze-idea")
def analyze_idea(payload: IdeaRequest) -> dict[str, object]:
    return ProductAgent().analyze(payload)


@router.post("/generate-requirements")
def generate_requirements(payload: IdeaRequest) -> RequirementsResponse:
    return RequirementsAgent().generate(payload)


@router.post("/generate-openspec")
def generate_openspec(payload: IdeaRequest) -> OpenSpecResponse:
    result = SupervisorAgent().run(payload)

    if result["decision"] == "ask_more_questions":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La idea necesita al menos una funcionalidad para generar el OpenSpec.",
        )

    if result["openspec"] is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El agente supervisor no pudo generar el OpenSpec.",
        )

    return result["openspec"]


@router.post("/generate-code")
def generate_code(payload: CodeGenerationRequest) -> CodeGenerationResponse:
    return CodeGenerationAgent().generate(payload)


@router.post("/suggest-features")
def suggest_features(payload: FeatureSuggestionRequest) -> FeatureSuggestionResponse:
    """Use LLM to suggest relevant features; falls back to curated sector lists."""
    llm = get_llm("general")
    if llm is not None:
        prompt = (
            f"Eres experto en producto digital. Sugiere exactamente 10 funcionalidades específicas para:\n"
            f"Sector: {payload.sector}\n"
            f"Problema: {payload.problem}\n"
            f"Usuarios: {payload.target_users}\n\n"
            "Responde ÚNICAMENTE con un JSON array de strings, sin texto adicional.\n"
            "Las funcionalidades deben ser concretas, en español, orientadas al usuario final.\n"
            'Ejemplo: ["Reserva online de citas","Sistema de pagos integrado",...]'
        )
        try:
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            match = re.search(r"\[[^\]]*\]", content, re.DOTALL)
            if match:
                features = json.loads(match.group())
                if isinstance(features, list) and features:
                    return FeatureSuggestionResponse(features=[str(f) for f in features[:10]])
        except Exception as exc:
            logger.warning("Feature suggestion LLM call failed: %s", exc)

    fallback = _SECTOR_FALLBACK.get(payload.sector, _DEFAULT_FEATURES)
    return FeatureSuggestionResponse(features=fallback)


@router.post("/recommend-architecture")
def recommend_architecture(payload: ArchitectureRequest) -> ArchitectureRecommendation:
    """Analyzes the project idea and recommends the most suitable architecture."""
    return ArchitectureAgent().recommend(payload)


@router.post("/generate-issues")
def generate_issues(payload: IssueGenerationRequest) -> IssueGenerationResponse:
    """Transforms an OpenSpec into structured GitHub Issues with milestones and labels."""
    return IssueGeneratorAgent().generate(payload)


@router.post("/generate-tutorial")
def generate_tutorial(payload: TutorialRequest) -> TutorialResponse:
    """Generates a step-by-step implementation tutorial from an OpenSpec and architecture type."""
    return TutorialAgent().generate(payload)
