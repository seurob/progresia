import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronRight, Loader2, Plus, Send, Sparkles, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";
import { api, getErrorMessage } from "../lib/api";
import { Project, Workspace } from "../types/api";

/* ─── Types ─────────────────────────────────────────────────────────────── */

type ChatStep =
  | "greeting" | "name" | "idea"
  | "product_type" | "objective" | "level"
  | "architecture" | "data_ai" | "deployment"
  | "features" | "summary" | "submitting";

type TechLevel = "BEGINNER" | "INTERMEDIATE";

interface Message { role: "ai" | "user"; text: string; }

interface WizardData {
  name: string;
  idea: string;
  level: TechLevel | "";
  productType: string;
  mainObjective: string;
  techPreference: string;
  mandatoryTechs: string;
  architectureStyle: string;
  dataNeeds: string[];
  aiNeeds: string;
  deploymentTarget: string;
  expectedResults: string[];
  features: string[];
  needsAuth: boolean;
  needsAdminPanel: boolean;
  needsAi: boolean;
}

const EMPTY_DATA: WizardData = {
  name: "", idea: "", level: "",
  productType: "", mainObjective: "", techPreference: "",
  mandatoryTechs: "", architectureStyle: "",
  dataNeeds: [], aiNeeds: "", deploymentTarget: "",
  expectedResults: [],
  features: [], needsAuth: true, needsAdminPanel: false, needsAi: false
};

const STEPS: ChatStep[] = [
  "greeting", "name", "idea",
  "product_type", "objective", "level",
  "architecture", "data_ai", "deployment",
  "features", "summary"
];

/* ─── Sector / product detection ────────────────────────────────────────── */

const SECTOR_MAP: [RegExp, string][] = [
  [/educaci|aprend|curso|alumno|profesor|clase|formaci|escuela|academia|e-learning/i, "Educacion y formacion"],
  [/salud|médic|clínic|paciente|hospital|farmaci|bienestar|doctor|consulta|telemedicina/i, "Salud y bienestar"],
  [/tienda|venta|compra|ecommerce|catálogo|producto|pedido|carrito|retail/i, "E-commerce y retail"],
  [/financ|pago|cobro|factura|banco|inversión|fintech|préstamo|ahorro/i, "Finanzas y fintech"],
  [/empres|rrhh|recursos humanos|empleado|nómina|reclutamiento/i, "RRHH y empresas"],
  [/inmobil|piso|alquiler|propiedad|vivienda|hipoteca/i, "Inmobiliaria"],
  [/logístic|envío|transport|entrega|ruta|almacén|flota/i, "Logistica y transporte"],
  [/hotel|hostel|turismo|viaje|restaurante|reserva|huésped/i, "Hosteleria y turismo"],
];

function detectSector(text: string): string {
  for (const [re, sector] of SECTOR_MAP) if (re.test(text)) return sector;
  return "Tecnologia e IT";
}
function extractTargetUsers(idea: string): string {
  const m = idea.match(/para\s+([^.,\n]{8,60})/i);
  if (m) return m[1].trim();
  const m2 = idea.match(/(?:usuarios?|clientes?)\s+(?:que|de|con)\s+([^.,\n]{5,50})/i);
  if (m2) return m2[1].trim();
  return "Usuarios finales de la plataforma";
}

/* ─── Copy helpers ───────────────────────────────────────────────────────── */

const SECTOR_INSIGHTS: Record<string, string> = {
  "Educacion y formacion": "Sector: **Educación y formación** — la clave es el **progreso visible**. El usuario necesita saber dónde está y qué le falta. Un sistema de tracking bien hecho vale más que 20 funcionalidades.",
  "Salud y bienestar": "Sector: **Salud y bienestar** — la **confianza es el producto**. Datos protegidos, flujos sin ambigüedad, cumplimiento RGPD desde el día 1.",
  "E-commerce y retail": "Sector: **E-commerce y retail** — el reto real es la **conversión**. Un checkout sin fricción vale más que 20 funcionalidades extra.",
  "Finanzas y fintech": "Sector: **Fintech** — regulación, seguridad y confianza. Resuelve **un único flujo financiero** excepcionalmente bien.",
  "RRHH y empresas": "Sector: **RRHH y empresas** — hay dos audiencias: la empresa (ROI medible) y el empleado (**ahorro de tiempo real**).",
  "Logistica y transporte": "Sector: **Logística** — la **visibilidad en tiempo real** es el mayor dolor. Si puedes mostrar dónde está algo en todo momento, tienes el 70% del valor.",
  "Hosteleria y turismo": "Sector: **Hostelería y turismo** — automatiza lo repetitivo (reservas, check-in, comunicación) para que el equipo se centre en la experiencia.",
  "Inmobiliaria": "Sector: **Inmobiliaria** — proceso largo y emocional. Aclara cada paso y reduce la incertidumbre. La **firma digital** es el diferenciador clave.",
  "Tecnologia e IT": "Sector: **Tecnología e IT** — los devs perdonan la UI, no los bugs. Prioriza **developer experience y fiabilidad** sobre UX pulida.",
};

const NAME_NOT_VALID = [
  "Eso suena a una idea, no a un nombre. Necesito algo como **\"GestiónPro\"**, **\"EduFlow\"** o **\"ClinicaOnline\"** — el nombre con el que reconocerías este proyecto.",
  "Parece una descripción. El nombre es más corto: **\"AppSalud\"**, **\"TallerGest\"**, **\"LegalDesk\"**… ¿Cómo se llama tu proyecto?",
  "Necesito el **nombre**, no una descripción. Algo breve para el repositorio, el logo o el dominio."
];
let _nameIdx = 0;

const SENTENCE_WORDS = /\b(quiero|tengo|hacer|necesito|hay|como|para|una|que|mi|esto|eso|hola|ok|sí|si|no|ayuda|help|test|prueba|gracias|hago|crear|voy|idea|proyecto|problema|resuelve|gestionar)\b/gi;

function looksLikeProjectName(val: string): boolean {
  const words = val.trim().split(/\s+/);
  if (words.length > 5 || val.length > 60) return false;
  return (val.match(SENTENCE_WORDS) ?? []).length < 2;
}
function looksLikeFeature(val: string): boolean {
  const words = val.trim().split(/\s+/);
  return words.length >= 2 && val.trim().length >= 8;
}

/* ─── Option cards data ──────────────────────────────────────────────────── */

const PRODUCT_TYPES = [
  { value: "web",          icon: "🌐", label: "Aplicación web",       hint: "SaaS, portal, panel, intranet" },
  { value: "mobile",       icon: "📱", label: "App móvil",            hint: "iOS, Android o multiplataforma" },
  { value: "desktop",      icon: "🖥️", label: "Escritorio",           hint: "Tauri, Electron, app nativa" },
  { value: "api",          icon: "⚡", label: "API / Backend",        hint: "Servicio REST, GraphQL, microservicio" },
  { value: "saas",         icon: "🚀", label: "SaaS / Producto",      hint: "Suscripción, múltiples clientes" },
  { value: "ai_tool",      icon: "🤖", label: "Herramienta IA",       hint: "Agentes, RAG, chat con documentos" },
  { value: "educational",  icon: "📚", label: "Proyecto educativo",   hint: "Para aprender o portfolio académico" },
  { value: "documentary",  icon: "📄", label: "Portal documental",    hint: "Contenido, wiki, base de conocimiento" },
];

const OBJECTIVES = [
  { value: "learn",          icon: "🎓", label: "Aprender una tecnología",    hint: "El objetivo es dominar el stack" },
  { value: "class_project",  icon: "📝", label: "Proyecto de clase / TFG",    hint: "Entrega académica o evaluación" },
  { value: "mvp",            icon: "🚀", label: "Construir un MVP real",       hint: "Validar el producto con usuarios" },
  { value: "validate",       icon: "🔍", label: "Validar una idea de negocio", hint: "Prototipo para inversores o clientes" },
  { value: "portfolio",      icon: "💼", label: "Portfolio profesional",       hint: "Mostrar habilidades a empleadores" },
  { value: "internal",       icon: "⚙️", label: "Herramienta interna",        hint: "Para uso del equipo o empresa" },
  { value: "startup",        icon: "💡", label: "Base para startup",           hint: "Arquitectura preparada para crecer" },
];

const ARCHITECTURE_OPTIONS = [
  { value: "single",       icon: "🏠", label: "Aplicación única",         hint: "Next.js, Laravel, Django — todo integrado" },
  { value: "modular",      icon: "🧩", label: "Monolito modular",         hint: "Una app, pero bien organizada por módulos" },
  { value: "frontend_api", icon: "⚡", label: "Frontend + API separados", hint: "React/Vue + NestJS/FastAPI/Laravel" },
  { value: "ai_service",   icon: "🤖", label: "Frontend + API + IA",      hint: "Arquitectura con servicio de IA dedicado" },
  { value: "mobile_api",   icon: "📱", label: "App móvil + API",          hint: "Flutter/React Native conectado a backend" },
  { value: "desktop_api",  icon: "🖥️", label: "Escritorio + API",         hint: "Tauri/Electron + backend propio" },
];

const DATA_OPTIONS = [
  { value: "relational", label: "Base de datos relacional", hint: "PostgreSQL, MySQL — datos estructurados" },
  { value: "document",   label: "Base de datos documental", hint: "MongoDB — datos flexibles o jerárquicos" },
  { value: "cache",      label: "Caché / Cola de mensajes", hint: "Redis — sesiones, jobs, rate limiting" },
  { value: "vector",     label: "Búsqueda semántica / RAG", hint: "pgvector, Qdrant, Chroma — IA + documentos" },
];

const AI_OPTIONS = [
  { value: "none",           label: "No necesito IA",           hint: "Proyecto sin integración de IA" },
  { value: "online",         label: "IA online",                hint: "OpenAI, Groq, Gemini, OpenRouter" },
  { value: "local",          label: "IA local",                 hint: "Ollama, LM Studio — sin coste de API" },
  { value: "hybrid",         label: "IA híbrida",               hint: "Local + online según la tarea" },
  { value: "chat_docs",      label: "Chat con documentos",      hint: "RAG básico sobre archivos PDF/web" },
  { value: "rag",            label: "RAG documental",           hint: "Base vectorial + embeddings + LLM" },
  { value: "agents",         label: "Agentes especializados",   hint: "LangGraph, LangChain agents, multi-agente" },
  { value: "recommendation", label: "Que la IA recomiende",     hint: "Según el proyecto, propongo la mejor opción" },
];

const DEPLOYMENT_OPTIONS = [
  { value: "local",          label: "Solo local",              hint: "Solo necesito que funcione en mi máquina" },
  { value: "docker_local",   label: "Docker local",            hint: "Docker Compose para entorno reproducible" },
  { value: "vps",            label: "VPS / Servidor propio",   hint: "DigitalOcean, Hetzner, OVH + nginx/Traefik" },
  { value: "cloud",          label: "Plataforma cloud",        hint: "Vercel, Railway, Render, Fly.io — rápido y fácil" },
  { value: "recommendation", label: "Que la IA recomiende",    hint: "Según el nivel y el proyecto, elijo lo mejor" },
];

const EXPECTED_RESULTS_OPTIONS = [
  { value: "specs_pdf",       label: "📄 Especificaciones + PDF",          hint: "Requisitos, arquitectura, OpenSpec descargable" },
  { value: "zip",             label: "📦 Carpeta ZIP del proyecto",        hint: "Código base estructurado y listo" },
  { value: "docker",          label: "🐳 Proyecto ejecutable con Docker",  hint: "docker-compose.yml funcional" },
  { value: "github",          label: "🐙 Listo para GitHub",               hint: "Issues, milestones, .gitignore, README" },
  { value: "learning",        label: "🎓 Itinerario de aprendizaje",       hint: "Tutorial paso a paso con comandos reales" },
  { value: "ai_instructions", label: "🤖 Instrucciones para IA",          hint: "Carpeta SDD — contexto para Claude, Copilot..." },
];

/* ─── Queue-based chat hook ──────────────────────────────────────────────── */

function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [typing, setTyping] = useState(false);
  const queueRef = useRef<{ text: string; onDone?: () => void }[]>([]);
  const runningRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const aliveRef = useRef(true);

  useEffect(() => {
    aliveRef.current = true;
    return () => {
      aliveRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      queueRef.current = [];
      runningRef.current = false;
    };
  }, []);

  const drain = useCallback(() => {
    if (runningRef.current || queueRef.current.length === 0 || !aliveRef.current) return;
    runningRef.current = true;
    const { text, onDone } = queueRef.current.shift()!;
    setTyping(true);
    const delay = Math.min(400 + text.replace(/\*\*/g, "").length * 12, 2000);
    timerRef.current = setTimeout(() => {
      if (!aliveRef.current) return;
      setMessages(prev => [...prev, { role: "ai", text }]);
      setTyping(false);
      runningRef.current = false;
      onDone?.();
      timerRef.current = setTimeout(drain, 120);
    }, delay);
  }, []);

  const pushAI = useCallback((text: string, onDone?: () => void) => {
    if (!aliveRef.current) return;
    queueRef.current.push({ text, onDone });
    drain();
  }, [drain]);

  const pushUser = useCallback((text: string) => {
    setMessages(prev => [...prev, { role: "user", text }]);
  }, []);

  return { messages, typing, pushAI, pushUser };
}

/* ─── Sub-components ─────────────────────────────────────────────────────── */

function StepDots({ step }: { readonly step: ChatStep }) {
  const tracked = STEPS.slice(1);
  const idx = tracked.indexOf(step);
  if (idx < 0) return null;
  return (
    <div className="flex items-center gap-1.5">
      {tracked.map((_, i) => (
        <span key={i} className={`h-1.5 rounded-full transition-all ${
          i < idx ? "w-4 bg-(--c-accent)" : i === idx ? "w-3 bg-(--c-accent) opacity-80" : "w-1.5 bg-(--c-border-med)"
        }`} />
      ))}
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map(i => (
        <span key={i} className="size-2 rounded-full bg-(--c-accent) opacity-60"
          style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
      ))}
    </div>
  );
}

function Bubble({ msg }: { readonly msg: Message }) {
  const isAI = msg.role === "ai";
  const parts = msg.text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <div className={`flex ${isAI ? "justify-start" : "justify-end"}`}>
      {isAI && (
        <span className="mr-2 mt-1 flex size-7 shrink-0 items-center justify-center rounded-full bg-(--c-accent) text-[10px] font-bold text-(--c-accent-on)">
          IA
        </span>
      )}
      <div className={`max-w-[84%] rounded-2xl px-4 py-2.5 text-sm leading-6 ${
        isAI
          ? "rounded-tl-sm bg-(--c-surface) text-(--c-text)"
          : "rounded-tr-sm bg-(--c-accent) text-(--c-accent-on)"
      }`}>
        {parts.map((p, i) =>
          p.startsWith("**") && p.endsWith("**")
            ? <strong key={i}>{p.slice(2, -2)}</strong>
            : p.split("\n").map((line, j, arr) => (
                <span key={`${i}-${j}`}>{line}{j < arr.length - 1 && <br />}</span>
              ))
        )}
      </div>
    </div>
  );
}

function OptionCard({
  icon, label, hint, selected, onClick, multiSelect = false
}: {
  readonly icon?: string;
  readonly label: string;
  readonly hint?: string;
  readonly selected: boolean;
  readonly onClick: () => void;
  readonly multiSelect?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-start gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
        selected
          ? "border-(--c-accent) bg-(--c-active-bg) ring-1 ring-(--c-accent)"
          : "border-(--c-border-subtle) hover:border-(--c-border-med) hover:bg-(--c-surface-2)"
      }`}
    >
      <span className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-${multiSelect ? "sm" : "full"} border-2 ${
        selected ? "border-(--c-accent) bg-(--c-accent)" : "border-(--c-border-med)"
      }`}>
        {selected && <span className={`${multiSelect ? "size-2.5 rounded-sm" : "size-2 rounded-full"} bg-(--c-accent-on)`} />}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">
          {icon && <span className="mr-1.5">{icon}</span>}
          {label}
        </p>
        {hint && <p className="mt-0.5 text-xs text-(--c-text-muted)">{hint}</p>}
      </div>
    </button>
  );
}

/* ─── Main page ──────────────────────────────────────────────────────────── */

export function NewProjectPage() {
  const navigate = useNavigate();
  const { messages, typing, pushAI, pushUser } = useChat();
  const [step, setStep] = useState<ChatStep>("greeting");
  const [data, setData] = useState<WizardData>(EMPTY_DATA);
  const [textInput, setTextInput] = useState("");
  const [featureInput, setFeatureInput] = useState("");
  const [featureError, setFeatureError] = useState("");
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => (await api.get<Workspace[]>("/workspaces")).data
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing, step]);

  useEffect(() => {
    pushAI(
      `Soy **ProgresIA Studio**, tu asistente para construir proyectos de software con metodología SDD.\n\nVoy a guiarte paso a paso para definir:\n\n📋 Requisitos y arquitectura recomendada\n📑 Especificación técnica completa (OpenSpec)\n🐛 Issues de GitHub organizados por fases\n📚 Tutorial paso a paso con comandos reales\n💻 Código base + carpeta ZIP lista\n📄 Documentación SDD para continuar con IA\n\nEmpecemos. ¿Cuál es el **nombre** de tu proyecto?`,
      () => setStep("name")
    );
  }, [pushAI]);

  /* ── Step handlers ───────────────────────────────────────────────────── */

  function submitName() {
    const val = textInput.trim();
    if (val.length < 2) return;
    pushUser(val);
    setTextInput("");
    if (!looksLikeProjectName(val)) {
      pushAI(NAME_NOT_VALID[_nameIdx++ % NAME_NOT_VALID.length]);
      return;
    }
    const len = val.length;
    const reaction = len <= 5
      ? `**"${val}"** — corto y directo. Fácil de recordar, fácil de escribir.`
      : len <= 12
      ? `**"${val}"** — claro y con personalidad propia.`
      : `**"${val}"** — tiene nombre de proyecto serio.`;
    setData(d => ({ ...d, name: val }));
    pushAI(reaction);
    pushAI(
      `Cuéntame la idea en 2-3 frases.\n\nIncluye: **qué problema resuelve**, **para quién** y **qué tipo de aplicación es**.\n\n💡 *No necesitas saber las tecnologías todavía — primero la idea, después la arquitectura.*`,
      () => setStep("idea")
    );
  }

  function submitIdea() {
    const val = textInput.trim();
    if (val.length < 15) return;
    pushUser(val);
    setTextInput("");
    const sector = detectSector(val);
    setData(d => ({ ...d, idea: val }));
    const insight = SECTOR_INSIGHTS[sector] ?? `Sector detectado: **${sector}**.`;
    const extra = val.split(/\s+/).length < 15 ? `\n\n💡 *Cuanto más detallada la descripción, mejor será la especificación generada.*` : "";
    pushAI(insight + extra);
    pushAI(
      `¿Qué tipo de producto estás construyendo?`,
      () => setStep("product_type")
    );
  }

  function submitProductType(pt: string) {
    const opt = PRODUCT_TYPES.find(o => o.value === pt);
    pushUser(`${opt?.icon ?? ""} ${opt?.label ?? pt}`);
    setData(d => ({ ...d, productType: pt }));
    pushAI(
      `¿Cuál es el **objetivo principal** de este proyecto?`,
      () => setStep("objective")
    );
  }

  function submitObjective(obj: string) {
    const opt = OBJECTIVES.find(o => o.value === obj);
    pushUser(`${opt?.icon ?? ""} ${opt?.label ?? obj}`);
    setData(d => ({ ...d, mainObjective: obj }));
    pushAI(
      `¿Cuál es tu **nivel técnico** actual?\n\nEsto determina la arquitectura recomendada, la complejidad del stack y el detalle del tutorial generado.`,
      () => setStep("level")
    );
  }

  function submitLevel(level: TechLevel) {
    const labels: Record<TechLevel, string> = { BEGINNER: "Principiante", INTERMEDIATE: "Intermedio" };
    pushUser(labels[level]);
    setData(d => ({ ...d, level }));
    const reactions: Record<TechLevel, string> = {
      BEGINNER: `Bien. Recomendaré stacks con menor curva de aprendizaje — Laravel, Django, Next.js o React+Express — con tutoriales paso a paso que explican cada comando.\n\nEl proyecto será sencillo pero profesional: una arquitectura comprensible con buenas prácticas desde el día 1.`,
      INTERMEDIATE: `Perfecto. Iremos a una arquitectura moderna con buenas prácticas: separación frontend/backend, TypeScript, contenedorización y CI básica desde el principio.\n\nEl tutorial asumirá experiencia con el stack y se centrará en las decisiones de diseño, no en los fundamentos.`,
    };
    pushAI(reactions[level]);
    pushAI(
      `¿Qué **arquitectura** prefieres para este proyecto?`,
      () => setStep("architecture")
    );
  }

  function submitArchitecture(arch: string) {
    const opt = ARCHITECTURE_OPTIONS.find(o => o.value === arch);
    pushUser(`${opt?.icon ?? ""} ${opt?.label ?? arch}`);
    setData(d => ({ ...d, architectureStyle: arch, needsAi: d.needsAi }));
    pushAI(
      `Última parte técnica: **datos e IA**.\n\n¿Qué tipo de base de datos necesitas? ¿Y necesitas integración con inteligencia artificial?`,
      () => setStep("data_ai")
    );
  }

  function submitDataAI(d_needs: string[], ai: string) {
    const aiOpt = AI_OPTIONS.find(o => o.value === ai);
    pushUser(`Datos: ${d_needs.length > 0 ? d_needs.join(", ") : "ninguna BD"} · IA: ${aiOpt?.label ?? ai}`);
    const needsAiVal = ai !== "none";
    setData(d => ({ ...d, dataNeeds: d_needs, aiNeeds: ai, needsAi: needsAiVal }));
    pushAI(
      `¿Cómo quieres **desplegar** el proyecto?`,
      () => setStep("deployment")
    );
  }

  function submitDeployment(dep: string) {
    const opt = DEPLOYMENT_OPTIONS.find(o => o.value === dep);
    pushUser(opt?.label ?? dep);
    setData(d => ({ ...d, deploymentTarget: dep }));
    pushAI(
      `Ya casi. Las **funcionalidades esenciales** del MVP.\n\n**¿Qué 3-5 funciones son imprescindibles?** Sin ellas el producto no tendría valor.\n\n💡 *Sé específico: "Gestión de reservas con calendario" > "Gestión de reservas".*`,
      () => setStep("features")
    );
  }

  function addFeature() {
    const val = featureInput.trim();
    if (!val) return;
    if (!looksLikeFeature(val)) {
      setFeatureError("La funcionalidad debe ser descriptiva (al menos 2 palabras).");
      return;
    }
    if (data.features.includes(val)) {
      setFeatureError("Ya tienes esa funcionalidad.");
      return;
    }
    setFeatureError("");
    setData(d => {
      const next = [...d.features, val];
      if (next.length === 2) {
        const n = next.length;
        const hasPay = next.some(f => /pago|cobro|factura|stripe/i.test(f));
        const notes: string[] = [];
        if (n > 7) notes.push(`⚠️ ${n} funcionalidades es mucho para un MVP. Considera cuáles van al backlog.`);
        if (hasPay) notes.push(`💡 Si tienes pagos, necesitarás autenticación. Actívala en el resumen.`);
        if (notes.length > 0) pushAI(notes.join(" "));
      }
      return { ...d, features: next };
    });
    setFeatureInput("");
  }

  function removeFeature(f: string) {
    setData(d => ({ ...d, features: d.features.filter(x => x !== f) }));
  }

  function submitFeatures() {
    if (data.features.length < 2) return;
    pushUser(`${data.features.length} funcionalidades: ${data.features.slice(0, 3).join(", ")}${data.features.length > 3 ? "…" : ""}`);
    const sector = detectSector(data.idea);
    const lvl = { BEGINNER: "Principiante", INTERMEDIATE: "Intermedio" }[data.level as TechLevel] ?? data.level;
    const archOpt = ARCHITECTURE_OPTIONS.find(o => o.value === data.architectureStyle);
    const summary =
      `Todo listo. Esto es lo que construiremos:\n\n` +
      `**"${data.name}"** — ${sector}\n` +
      `💡 ${data.idea.slice(0, 100)}${data.idea.length > 100 ? "…" : ""}\n\n` +
      `🎯 Nivel: ${lvl} · 🏗️ ${archOpt?.label ?? data.architectureStyle} · ⚡ ${data.features.length} funcionalidades\n\n` +
      `**Generaremos en orden:**\n` +
      `1. Análisis de requisitos funcionales y no funcionales\n` +
      `2. Propuestas de tecnología — elige el stack que mejor encaja\n` +
      `3. Arquitectura detallada y OpenSpec completo\n` +
      `4. Issues de GitHub con milestones por fase\n` +
      `5. Tutorial paso a paso con comandos reales\n` +
      `6. Código base + carpeta SDD con instrucciones para IA\n` +
      `7. Bundle ZIP descargable\n\n` +
      `¿Qué resultado esperas obtener? (puedes marcar varios)`;
    pushAI(summary, () => setStep("summary"));
  }

  async function submitProject() {
    setSubmitting(true);
    setServerError(null);
    try {
      const ws = workspacesQuery.data?.[0];
      if (!ws) throw new Error("No se encontró workspace");

      const sector = detectSector(data.idea);
      const complexity = data.level === "BEGINNER" ? "simple" : "standard";
      const targetUsers = extractTargetUsers(data.idea);

      const project = (await api.post<Project>("/projects", {
        workspaceId: ws.id,
        name: data.name,
        sector,
        productType: data.productType || "SaaS operativo",
        description: data.idea
      })).data;

      await api.post("/ideas", {
        projectId: project.id,
        problem: data.idea,
        targetUsers,
        coreFeatures: data.features,
        complexity,
        needsAuth: data.needsAuth,
        needsAdminPanel: data.needsAdminPanel,
        needsAi: data.needsAi,
        // Structured fields
        mainObjective: data.mainObjective,
        techPreference: data.techPreference || "ai_recommends",
        mandatoryTechs: data.mandatoryTechs || undefined,
        architectureStyle: data.architectureStyle,
        dataNeeds: data.dataNeeds,
        aiNeeds: data.aiNeeds || "recommendation",
        deploymentTarget: data.deploymentTarget || "recommendation",
        expectedResults: data.expectedResults
      });

      navigate(`/projects/${project.slug}`);
    } catch (err) {
      setServerError(getErrorMessage(err));
      setSubmitting(false);
    }
  }

  /* ── Input area per step ─────────────────────────────────────────────── */

  function renderInput() {
    if (typing || step === "greeting" || step === "submitting") return null;

    if (step === "name") {
      return (
        <div className="flex gap-2">
          <input className="input flex-1 text-sm" placeholder="Nombre de tu proyecto..."
            value={textInput} onChange={e => setTextInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && submitName()} autoFocus />
          <button className="icon-button self-end" onClick={submitName} disabled={textInput.trim().length < 2}>
            <Send size={16} />
          </button>
        </div>
      );
    }

    if (step === "idea") {
      return (
        <div className="flex gap-2">
          <textarea
            className="input min-h-20 flex-1 resize-none text-sm"
            placeholder="Ej: Plataforma para gestores de flotas que necesitan rastrear vehículos en tiempo real..."
            value={textInput}
            onChange={e => setTextInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && e.metaKey && submitIdea()}
            autoFocus
          />
          <button className="icon-button self-end" onClick={submitIdea} disabled={textInput.trim().length < 15}>
            <Send size={16} />
          </button>
        </div>
      );
    }

    if (step === "product_type") {
      return (
        <div className="grid grid-cols-2 gap-2">
          {PRODUCT_TYPES.map(o => (
            <OptionCard key={o.value} icon={o.icon} label={o.label} hint={o.hint}
              selected={data.productType === o.value}
              onClick={() => submitProductType(o.value)} />
          ))}
        </div>
      );
    }

    if (step === "objective") {
      return (
        <div className="grid gap-2">
          {OBJECTIVES.map(o => (
            <OptionCard key={o.value} icon={o.icon} label={o.label} hint={o.hint}
              selected={data.mainObjective === o.value}
              onClick={() => submitObjective(o.value)} />
          ))}
        </div>
      );
    }

    if (step === "level") {
      const levels: { level: TechLevel; label: string; description: string }[] = [
        { level: "BEGINNER",     label: "🌱 Principiante", description: "Primeros proyectos reales — arquitecturas sencillas y tutoriales detallados" },
        { level: "INTERMEDIATE", label: "⚡ Intermedio",   description: "Con experiencia — arquitectura moderna, buenas prácticas, CI desde el día 1" },
      ];
      return (
        <div className="grid gap-2">
          {levels.map(l => (
            <OptionCard key={l.level} label={l.label} hint={l.description}
              selected={data.level === l.level}
              onClick={() => submitLevel(l.level)} />
          ))}
        </div>
      );
    }

    if (step === "architecture") {
      return (
        <div className="grid gap-2">
          {ARCHITECTURE_OPTIONS.map(o => (
            <OptionCard key={o.value} icon={o.icon} label={o.label} hint={o.hint}
              selected={data.architectureStyle === o.value}
              onClick={() => submitArchitecture(o.value)} />
          ))}
        </div>
      );
    }

    if (step === "data_ai") {
      return <DataAIStep data={data} onSubmit={submitDataAI} />;
    }

    if (step === "deployment") {
      return (
        <div className="grid gap-2">
          {DEPLOYMENT_OPTIONS.map(o => (
            <OptionCard key={o.value} label={o.label} hint={o.hint}
              selected={data.deploymentTarget === o.value}
              onClick={() => submitDeployment(o.value)} />
          ))}
        </div>
      );
    }

    if (step === "features") {
      return (
        <div className="grid gap-3">
          {data.features.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {data.features.map(f => (
                <span key={f} className="flex items-center gap-1 rounded-full border border-(--c-border-med) bg-(--c-surface-2) px-2.5 py-1 text-xs">
                  {f}
                  <button onClick={() => removeFeature(f)} className="text-(--c-text-faint) hover:text-(--c-text)">
                    <X size={11} />
                  </button>
                </span>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <input className="input flex-1 text-sm"
              placeholder="Ej: Gestión de reservas con calendario y notificaciones..."
              value={featureInput}
              onChange={e => { setFeatureInput(e.target.value); setFeatureError(""); }}
              onKeyDown={e => e.key === "Enter" && addFeature()}
              autoFocus />
            <button className="icon-button self-end" onClick={addFeature} disabled={!featureInput.trim()}>
              <Plus size={16} />
            </button>
          </div>
          {featureError && <p className="text-xs text-amber-400">{featureError}</p>}
          <p className={`text-xs ${data.features.length >= 2 ? "text-(--c-text-faint)" : "text-amber-400"}`}>
            {data.features.length < 2
              ? `Añade al menos 2 funcionalidades (llevas ${data.features.length})`
              : `${data.features.length} funcionalidades ✓ — añade más o continúa`}
          </p>
          <button className="primary-button justify-center" onClick={submitFeatures}
            disabled={data.features.length < 2}>
            Continuar <ChevronRight size={16} />
          </button>
        </div>
      );
    }

    if (step === "summary") {
      return (
        <div className="grid gap-3">
          {/* Expected results */}
          <div className="grid gap-1.5 rounded-xl border border-(--c-border-subtle) p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-(--c-text-muted)">¿Qué quieres obtener?</p>
            {EXPECTED_RESULTS_OPTIONS.map(o => (
              <label key={o.value} className="flex cursor-pointer items-start gap-3 rounded-lg p-2 transition-colors hover:bg-(--c-surface-2)">
                <input type="checkbox"
                  checked={data.expectedResults.includes(o.value)}
                  onChange={e => {
                    setData(d => ({
                      ...d,
                      expectedResults: e.target.checked
                        ? [...d.expectedResults, o.value]
                        : d.expectedResults.filter(r => r !== o.value)
                    }));
                  }}
                  className="mt-0.5 size-4 accent-(--c-accent)" />
                <div>
                  <span className="text-sm">{o.label}</span>
                  <p className="mt-0.5 text-xs text-(--c-text-muted)">{o.hint}</p>
                </div>
              </label>
            ))}
          </div>

          {/* Technical modules */}
          <div className="grid gap-1.5 rounded-xl border border-(--c-border-subtle) p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-(--c-text-muted)">Módulos técnicos</p>
            {[
              { key: "needsAuth" as const,        icon: "🔐", label: "Autenticación (JWT)", tip: "Registro, login, sesiones por usuario" },
              { key: "needsAdminPanel" as const,   icon: "⚙️", label: "Panel de administración", tip: "Gestión de usuarios y contenido" },
              { key: "needsAi" as const,           icon: "🤖", label: "Módulo de IA", tip: "Análisis, sugerencias o automatización" },
            ].map(({ key, icon, label, tip }) => (
              <label key={key} className="flex cursor-pointer items-start gap-3 rounded-lg p-2 transition-colors hover:bg-(--c-surface-2)">
                <input type="checkbox"
                  checked={data[key] as boolean}
                  onChange={e => setData(d => ({ ...d, [key]: e.target.checked }))}
                  className="mt-0.5 size-4 accent-(--c-accent)" />
                <div>
                  <span className="text-sm">{icon} {label}</span>
                  <p className="mt-0.5 text-xs text-(--c-text-muted)">{tip}</p>
                </div>
              </label>
            ))}
          </div>

          {serverError && (
            <p className="rounded-lg border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-300">{serverError}</p>
          )}

          <button className="primary-button justify-center py-3.5 text-base" onClick={submitProject} disabled={submitting}>
            {submitting ? (
              <><Loader2 size={18} className="animate-spin" /> Creando proyecto...</>
            ) : (
              <><Sparkles size={18} /> Generar MVP completo con IA</>
            )}
          </button>
          <button className="secondary-button justify-center text-sm"
            onClick={() => { setStep("name"); setData(EMPTY_DATA); setTextInput(""); setFeatureInput(""); }}>
            Empezar de nuevo
          </button>
        </div>
      );
    }

    return null;
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col" style={{ height: "calc(100vh - 9rem)" }}>
      <div className="mb-3 flex items-center justify-between">
        <Link className="subtle-link inline-flex items-center gap-1.5 text-sm" to="/">
          <ArrowLeft size={15} /> Volver
        </Link>
        {step !== "greeting" && <StepDots step={step} />}
      </div>

      <div className="flex-1 overflow-y-auto rounded-xl border border-(--c-border-subtle) bg-(--c-bg) p-4">
        <div className="grid gap-3">
          {messages.map((msg, i) => <Bubble key={i} msg={msg} />)}
          {typing && (
            <div className="flex items-start gap-2">
              <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-(--c-accent) text-[10px] font-bold text-(--c-accent-on)">IA</span>
              <div className="rounded-2xl rounded-tl-sm bg-(--c-surface)"><TypingDots /></div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {(() => {
        const node = renderInput();
        return node
          ? <div className="mt-3 max-h-[45vh] overflow-y-auto rounded-xl border border-(--c-border-subtle) bg-(--c-surface) p-4">{node}</div>
          : null;
      })()}
    </div>
  );
}

/* ─── Data + AI combined step ───────────────────────────────────────────── */

function DataAIStep({
  data, onSubmit
}: {
  readonly data: WizardData;
  readonly onSubmit: (dataNeeds: string[], ai: string) => void;
}) {
  const [localDataNeeds, setLocalDataNeeds] = useState<string[]>(data.dataNeeds);
  const [localAi, setLocalAi] = useState(data.aiNeeds || "");

  function toggle(val: string) {
    setLocalDataNeeds(prev =>
      prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val]
    );
  }

  function canSubmit() { return localAi !== ""; }

  return (
    <div className="grid gap-3">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-(--c-text-muted)">Base de datos (selección múltiple)</p>
        <div className="grid gap-1.5">
          {DATA_OPTIONS.map(o => (
            <OptionCard key={o.value} label={o.label} hint={o.hint} multiSelect
              selected={localDataNeeds.includes(o.value)}
              onClick={() => toggle(o.value)} />
          ))}
        </div>
      </div>
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-(--c-text-muted)">Inteligencia artificial</p>
        <div className="grid gap-1.5">
          {AI_OPTIONS.map(o => (
            <OptionCard key={o.value} label={o.label} hint={o.hint}
              selected={localAi === o.value}
              onClick={() => setLocalAi(o.value)} />
          ))}
        </div>
      </div>
      <button className="primary-button justify-center" onClick={() => onSubmit(localDataNeeds, localAi)} disabled={!canSubmit()}>
        Continuar <ChevronRight size={16} />
      </button>
    </div>
  );
}
