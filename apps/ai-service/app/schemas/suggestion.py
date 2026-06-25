from pydantic import BaseModel


class FeatureSuggestionRequest(BaseModel):
    sector: str
    problem: str
    target_users: str


class FeatureSuggestionResponse(BaseModel):
    features: list[str]


# Curated feature lists per sector — used when the LLM is unavailable.
SECTOR_FALLBACK: dict[str, list[str]] = {
    "Educacion y formacion": ["Registro de alumnos y profesores", "Reserva y cancelacion de clases", "Calendario de disponibilidad", "Sistema de pagos y facturas", "Evaluaciones y calificaciones", "Mensajeria entre usuarios", "Sala de videoconferencia integrada", "Panel de progreso del alumno", "Notificaciones por email", "Generacion de certificados"],
    "Salud y bienestar": ["Historial clinico del paciente", "Agenda de citas con recordatorios", "Teleconsulta por video", "Prescripciones digitales", "Gestion de inventario medico", "Portal del paciente", "Integracion con wearables", "Facturacion y seguros", "Informes clinicos", "Chat medico-paciente"],
    "E-commerce y retail": ["Catalogo de productos con filtros", "Carrito y proceso de compra", "Pasarela de pago segura", "Gestion de inventario", "Seguimiento de pedidos", "Panel de vendedor", "Valoraciones y resenas", "Cupones y descuentos", "Programa de fidelizacion", "Soporte y devoluciones"],
    "Finanzas y fintech": ["Dashboard financiero personalizado", "Transferencias y pagos", "Historial de transacciones", "Alertas de gastos", "Analisis de inversiones", "Integracion bancaria open banking", "Firma digital de contratos", "Informes fiscales", "Seguridad con 2FA", "Chat con asesor financiero"],
    "RRHH y empresas": ["Gestion de empleados y organigramas", "Control de asistencia y fichaje", "Nominas y compensaciones", "Gestion de vacaciones y ausencias", "Evaluacion del desempeno", "Onboarding digital", "Portal del empleado", "Formacion interna", "Reclutamiento y seleccion", "Informes de RRHH"],
    "Logistica y transporte": ["Seguimiento de envios en tiempo real", "Gestion de flota de vehiculos", "Optimizacion de rutas con IA", "Portal de clientes", "Gestion de almacen", "Facturacion automatica", "Notificaciones de entrega", "Control de incidencias", "Integracion con marketplaces", "Dashboard logistico"],
    "Hosteleria y turismo": ["Reservas online de habitaciones", "Gestion de disponibilidad y tarifas", "Check-in y check-out digital", "Canal de comunicacion con huespedes", "Sistema de puntos y fidelizacion", "Gestion de resenias", "Facturacion y cobros", "Panel de limpieza y mantenimiento", "Integracion con OTAs", "Analisis de ocupacion"],
    "Inmobiliaria": ["Listado y busqueda de propiedades", "Tour virtual 360", "Gestion de contratos digitales", "Portal de propietarios e inquilinos", "Firma electronica", "Calculo de hipotecas", "Agenda de visitas", "Gestion de pagos y alquileres", "Valoracion automatica de propiedades", "CRM inmobiliario"],
    "Tecnologia e IT": ["Gestion de proyectos y sprints", "Seguimiento de incidencias y bugs", "Documentacion tecnica wiki", "CI/CD y despliegues", "Monitorizacion y alertas", "Facturacion por tiempo", "Portal de clientes", "Repositorio de codigo", "Gestion de licencias", "Dashboard de KPIs"],
}

DEFAULT_FEATURES: list[str] = ["Registro y autenticacion de usuarios", "Dashboard principal con metricas", "Gestion de perfiles", "Busqueda y filtros avanzados", "Notificaciones por email", "Panel de administracion", "Exportacion de datos", "API documentada", "Historial de actividad", "Integracion con herramientas externas"]
