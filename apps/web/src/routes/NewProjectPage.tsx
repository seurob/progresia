import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, ChevronRight, Loader2, Plus, Send, Sparkles, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";
import { api, getErrorMessage } from "../lib/api";
import { Project, Workspace } from "../types/api";

/* ─── Types ───────────────────────────────────────────────────────────── */

type ChatStep =
  | "greeting" | "name" | "sector" | "productType"
  | "problem" | "users" | "features" | "modules" | "summary" | "submitting";

interface Message { role: "ai" | "user"; text: string; }

interface WizardData {
  name: string; sector: string; productType: string;
  problem: string; targetUsers: string;
  features: string[]; needsAuth: boolean; needsAdminPanel: boolean; needsAi: boolean;
}

const EMPTY_DATA: WizardData = {
  name: "", sector: "", productType: "SaaS operativo",
  problem: "", targetUsers: "",
  features: [], needsAuth: true, needsAdminPanel: false, needsAi: false
};

const STEPS: ChatStep[] = ["greeting","name","sector","productType","problem","users","features","modules","summary"];

/* ─── Static content ──────────────────────────────────────────────────── */

const SECTORS = [
  "Educacion y formacion", "Salud y bienestar", "E-commerce y retail",
  "Finanzas y fintech", "RRHH y empresas", "Inmobiliaria",
  "Logistica y transporte", "Hosteleria y turismo", "Tecnologia e IT", "Otro"
];

const PRODUCT_TYPES = [
  "SaaS operativo", "Marketplace", "Plataforma de servicios",
  "Herramienta interna", "API / Backend", "Aplicacion movil"
];

/* ─── AI message content ──────────────────────────────────────────────── */

const SECTOR_INSIGHTS: Record<string, string> = {
  "Educacion y formacion": "🎓 Perfecto — tenemos un **template real de academia online** preconfigurado para este sector. Recibirás 36 archivos con autenticación de alumnos/instructores, gestión de cursos con módulos y lecciones, sistema de matriculación, seguimiento de progreso y datos de demostración. Ejecutable en 5 minutos.",
  "Salud y bienestar": "En salud, **la confianza es el producto**. Tu MVP debe transmitir seguridad desde el primer clic: datos protegidos, flujos sin ambigüedad y comunicación médico-paciente clara. Todo lo demás es secundario.",
  "E-commerce y retail": "En e-commerce el reto real no es el catálogo, es la **conversión y la retención**. Un checkout sin fricción y un sistema de seguimiento de pedidos claro valen más que 20 funcionalidades extra.",
  "Finanzas y fintech": "Fintech tiene la barrera de entrada más alta: regulación, seguridad y confianza. Para el MVP céntrate en resolver **un único flujo financiero** excepcionalmente bien, sin intentar ser un banco.",
  "RRHH y empresas": "Los productos de RRHH tienen un comprador (empresa) y un usuario (empleado) distintos. Tu MVP debe convencer al comprador con datos y ROI, y al usuario con **ahorro de tiempo real**.",
  "Logistica y transporte": "En logística, la visibilidad en tiempo real es el mayor dolor. Si puedes mostrar dónde está un envío o un vehículo en todo momento, tienes el 70% del valor del producto.",
  "Hosteleria y turismo": "El sector hostelero tiene márgenes finos y muchos sistemas legacy. Tu mayor oportunidad: **automatizar lo repetitivo** (reservas, check-in, comunicación) para que el equipo se centre en la experiencia del huésped.",
  "Inmobiliaria": "En inmobiliaria, el proceso de compra/alquiler es largo y emocional. Un MVP que aclare cada paso y reduzca la incertidumbre del cliente tiene mucho potencial. La firma digital y el tour virtual son los diferenciadores clave.",
  "Tecnologia e IT": "Productos para equipos técnicos tienen ventaja: toleran un MVP más rugoso si resuelve el problema bien. Prioriza **developer experience y fiabilidad** sobre UX pulida. Los devs perdonan la UI, no los bugs.",
};

const DEFAULT_SECTOR_INSIGHT = "Cada sector tiene sus particularidades, pero la regla universal del MVP aplica aquí: resuelve un problema concreto para un tipo de usuario específico, y hazlo excepcionalmente bien.";

const PRODUCT_TYPE_INSIGHTS: Record<string, string> = {
  "SaaS operativo": "SaaS operativo: modelo de negocio probado, recurrente y escalable. La clave es un **onboarding rápido** — si el usuario no ve valor en los primeros 5 minutos, se va.",
  "Marketplace": "Los marketplaces tienen el clásico problema del huevo y la gallina: necesitas oferta y demanda al mismo tiempo. Para el MVP, enfoca en **un lado primero** (oferta o demanda) y luego expande.",
  "Plataforma de servicios": "Las plataformas de servicios viven de la **eficiencia de la intermediación**. Tu MVP debe hacer que el match entre proveedor y cliente sea más rápido y confiable que la alternativa actual.",
  "Herramienta interna": "Las herramientas internas tienen una ventaja enorme: ya tienes los usuarios (tu equipo). El estándar de UX puede ser más bajo, pero la **fiabilidad** tiene que ser máxima.",
  "API / Backend": "Una API es un producto para desarrolladores. Tu documentación es tu UX. Prioriza: SDKs claros, ejemplos reales, tiempo de respuesta < 200ms y **zero downtime** desde el día 1.",
  "Aplicacion movil": "Apps móviles tienen costes de distribución altos (App Store review, instalación). Para el MVP considera primero una **PWA** — misma experiencia, más fácil de iterar y sin friction de descarga.",
};

const SENTENCE_WORDS = /\b(quiero|tengo|hacer|necesito|hay|como|para|una|que|mi|esto|eso|hola|ok|sí|si|no|ayuda|help|test|prueba|gracias|hago|crear|voy|idea|proyecto)\b/gi;
const NOT_A_NAME_RESPONSES = [
  `Eso suena a una idea, no a un nombre. 😄 Necesito algo como **"GestiónPro"**, **"EduFlow"** o **"ClinicaOnline"** — el nombre con el que reconocerías este proyecto. ¿Cuál es?`,
  `Mmm, eso parece una descripción. El nombre es más corto: **"AppSalud"**, **"TallerGest"**, **"LegalDesk"**… ¿Cómo quieres llamar a tu proyecto?`,
  `Necesito el **nombre del proyecto**, no una descripción. Algo breve que lo identifique, como lo llamarías en el repositorio o en el logo. ¿Cómo se llama?`
];
let _notNameIdx = 0;

function looksLikeProjectName(val: string): boolean {
  const words = val.trim().split(/\s+/);
  if (words.length > 5) return false;
  if (val.length > 60) return false;
  const matches = val.match(SENTENCE_WORDS) ?? [];
  if (matches.length >= 2) return false;
  return true;
}

function notANameMsg(): string {
  return NOT_A_NAME_RESPONSES[_notNameIdx++ % NOT_A_NAME_RESPONSES.length];
}

function nameReactionMsg(name: string): string {
  const len = name.length;
  if (len <= 5) return `**"${name}"** es corto y directo. Fácil de recordar, fácil de escribir. Buena señal para un producto.`;
  if (len <= 12) return `**"${name}"** suena bien. Claro, con personalidad propia.`;
  return `**"${name}"** — tiene nombre de proyecto serio. Podrías considerar una versión más corta para el dominio, pero para empezar funciona perfectamente.`;
}

function sectorMsg(name: string): string {
  return `¿En qué **sector o industria** opera "${name}"?`;
}

function problemReactionMsg(problem: string): string {
  const words = problem.trim().split(" ").length;
  if (words < 10) return `Dame un poco más de detalle si puedes. Cuanto más concreto sea el problema, más relevante será el código que genere.`;
  if (words < 25) return `Bien. Problema definido. Ahora necesito saber quién lo padece.`;
  return `Excelente descripción. Con este nivel de detalle el agente de IA puede generar funcionalidades que de verdad resuelven esto, no genéricas.`;
}

function usersReactionMsg(users: string): string {
  const lower = users.toLowerCase();
  if (/admin|gestor|gerente|director|coordinador/.test(lower)) {
    return `Con **gestores** como usuarios principales: prioriza dashboards de control, exportación de datos y permisos por rol. La UX puede ser densa — no es una consumer app.`;
  }
  if (/cliente|consumidor|usuario final|particular/.test(lower)) {
    return `Usuarios finales exigen **UX simple y mobile-first**. El MVP necesita menos features pero mejor experiencia. Un solo flujo que funcione perfecto vale más que diez a medias.`;
  }
  if (/profesor|docente|educador/.test(lower)) {
    return `Los profesores valoran lo que les ahorra tiempo real, no más tecnología. Automatizar la gestión y comunicación tiene **ROI inmediato** para ellos.`;
  }
  if (/médico|doctor|sanitario|clínico/.test(lower)) {
    return `Profesionales de salud tienen poco tiempo y cero tolerancia a errores. La **fiabilidad** y los flujos rápidos pesan más que el diseño. Cada clic extra es fricción costosa.`;
  }
  if (/developer|técnico|dev|programador/.test(lower)) {
    return `Usuarios técnicos son los más exigentes con la **consistencia y la documentación**. Prefieren una API bien documentada a una UI bonita.`;
  }
  return `Con ese perfil de usuario, prioriza **onboarding rápido** y que funcione desde el día 1 sin formación. La curva de aprendizaje baja es la killer feature.`;
}

function featuresReactionMsg(features: string[]): string {
  const n = features.length;
  const hasAuth = features.some(f => /auth|login|registro|usuario/i.test(f));
  const hasPay = features.some(f => /pago|cobro|factura|stripe/i.test(f));
  const hasDash = features.some(f => /dashboard|métrica|analíti|report/i.test(f));

  const notes: string[] = [];
  if (n > 8) notes.push(`⚠️ ${n} funcionalidades es mucho para un MVP. Considera cuáles son realmente v1 y cuáles van al backlog.`);
  if (n >= 2 && n <= 5) notes.push(`Foco perfecto. Un MVP con ${n} funcionalidades bien ejecutadas puede lanzarse en semanas.`);
  if (hasPay && !hasAuth) notes.push(`💡 Si tienes pagos, necesitarás autenticación sí o sí. Considera añadirla.`);
  if (hasDash) notes.push(`El dashboard de métricas es una excelente herramienta para validar con usuarios e inversores.`);
  if (!hasAuth && n >= 3) notes.push(`💡 La mayoría de estos flujos necesitan saber quién es el usuario. Considera autenticación.`);

  return notes.length > 0 ? notes.join(" ") : `**${n} funcionalidades** bien seleccionadas. Esto forma un MVP sólido y coherente.`;
}

function summaryMsg(d: WizardData): string {
  const mods = [d.needsAuth && "Autenticación", d.needsAdminPanel && "Panel admin", d.needsAi && "IA"].filter(Boolean).join(", ") || "ninguno extra";
  return `Perfecto. He analizado toda tu descripción y esto es lo que construiremos:\n\n**"${d.name}"** — ${d.sector} · ${d.productType}\n\n❓ **Problema:** ${d.problem.slice(0,120)}${d.problem.length > 120 ? "…" : ""}\n👥 **Usuarios:** ${d.targetUsers}\n⚡ **${d.features.length} funcionalidades** definidas\n🔧 **Módulos extra:** ${mods}\n\n¿Lo confirmamos y generamos el MVP completo?`;
}

/* ─── Queue-based chat hook ───────────────────────────────────────────── */

function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [typing, setTyping] = useState(false);
  const queueRef = useRef<{ text: string; onDone?: () => void }[]>([]);
  const runningRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const aliveRef = useRef(true);

  // Cancel pending timers and clear queue on unmount (fixes React StrictMode double-fire)
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
    const delay = Math.min(600 + text.replace(/\*\*/g, "").length * 18, 2400);
    timerRef.current = setTimeout(() => {
      if (!aliveRef.current) return;
      setMessages(prev => [...prev, { role: "ai", text }]);
      setTyping(false);
      runningRef.current = false;
      onDone?.();
      timerRef.current = setTimeout(drain, 180);
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

/* ─── Sub-components ──────────────────────────────────────────────────── */

function StepDots({ step }: { readonly step: ChatStep }) {
  const idx = STEPS.indexOf(step);
  const total = STEPS.length - 2; // exclude greeting and submitting
  const current = Math.max(0, idx - 1);
  return (
    <div className="flex items-center gap-1.5" title={`Paso ${current + 1} de ${total}`}>
      {Array.from({ length: total }).map((_, i) => (
        <span key={i} className={`h-1.5 rounded-full transition-all ${
          i < current ? "w-4 bg-(--c-accent)" : i === current ? "w-3 bg-(--c-accent) opacity-80" : "w-1.5 bg-(--c-border-med)"
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

const ACADEMIA_KEYWORDS = ["educac", "formac", "ensena", "academia", "curso", "escuela", "capacitac"];
const isAcademia = (sector: string) => ACADEMIA_KEYWORDS.some(k => sector.toLowerCase().includes(k));

function TechCard({ data }: { readonly data: WizardData }) {
  const academia = isAcademia(data.sector);
  const items = academia
    ? [
        { label: "Template", value: "Academia online (sector real)" },
        { label: "Stack", value: "tRPC · Next.js 14 · PostgreSQL · Docker" },
        { label: "Archivos", value: "36 ficheros listos para ejecutar" },
        { label: "Auth", value: "✓ Alumnos, Instructores y Admin (JWT)" },
        { label: "Cursos", value: "✓ Módulos, lecciones, progreso" },
        { label: "Matriculación", value: "✓ Enrollment + seguimiento por lección" },
        { label: "Datos demo", value: "✓ Seed con 2 cursos + 3 usuarios" },
        { label: "Deploy", value: "Docker Compose + nginx listos" },
        { label: "Setup", value: "5 min: npm install && docker compose up" },
      ]
    : [
        { label: "Stack", value: "tRPC · Next.js 14 · PostgreSQL · Docker" },
        { label: "Archivos", value: "22 ficheros listos para ejecutar" },
        { label: "Auth", value: data.needsAuth ? "✓ Incluida (JWT + sesiones)" : "Sin autenticación" },
        { label: "Admin", value: data.needsAdminPanel ? "✓ Panel de administración" : "—" },
        { label: "IA", value: data.needsAi ? "✓ Módulo con Ollama/LangChain" : "—" },
        { label: "Deploy", value: "Docker Compose + nginx listos" },
        { label: "Setup", value: "5 min: npm install && docker compose up" },
      ];
  return (
    <div className="overflow-hidden rounded-xl border border-(--c-border-subtle) bg-(--c-surface-2)">
      <div className="flex items-center gap-2 border-b border-(--c-border-subtle) px-4 py-2.5">
        <Sparkles size={14} className="text-(--c-accent)" />
        <span className="text-xs font-semibold uppercase tracking-wide text-(--c-text-muted)">Lo que recibirás</span>
      </div>
      <div className="grid gap-0.5 p-1">
        {items.filter(it => it.value !== "—").map(it => (
          <div key={it.label} className="flex items-baseline justify-between rounded-lg px-3 py-1.5">
            <span className="text-xs text-(--c-text-muted)">{it.label}</span>
            <span className="text-xs font-medium text-(--c-text)">{it.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeaturePicker({
  suggested, selected, onToggle, customInput, onCustomInput, onAddCustom, loadingSuggestions
}: {
  readonly suggested: string[];
  readonly selected: string[];
  readonly onToggle: (f: string) => void;
  readonly customInput: string;
  readonly onCustomInput: (v: string) => void;
  readonly onAddCustom: () => void;
  readonly loadingSuggestions: boolean;
}) {
  return (
    <div className="grid gap-3">
      {loadingSuggestions ? (
        <div className="flex items-center gap-2 text-sm text-(--c-text-muted)">
          <Loader2 size={15} className="animate-spin text-(--c-accent)" />
          Analizando tu sector para sugerir funcionalidades relevantes...
        </div>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          {suggested.map(f => {
            const active = selected.includes(f);
            return (
              <button key={f} onClick={() => onToggle(f)}
                className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 text-left text-sm transition-colors ${
                  active ? "border-(--c-border-strong) bg-(--c-surface-2) font-medium" : "border-(--c-border-subtle) hover:border-(--c-border-med)"
                }`}>
                <span className={`mt-0.5 flex size-4 shrink-0 items-center justify-center rounded border ${
                  active ? "border-(--c-accent) bg-(--c-accent) text-(--c-accent-on)" : "border-(--c-border-med)"
                }`}>
                  {active && <Check size={10} />}
                </span>
                {f}
              </button>
            );
          })}
        </div>
      )}

      <div className="flex gap-2">
        <input className="input flex-1 text-sm" placeholder="Añade una funcionalidad propia..."
          value={customInput} onChange={e => onCustomInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && onAddCustom()} />
        <button className="icon-button" onClick={onAddCustom} disabled={!customInput.trim()} title="Añadir">
          <Plus size={16} />
        </button>
      </div>

      {selected.filter(f => !suggested.includes(f)).length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selected.filter(f => !suggested.includes(f)).map(f => (
            <span key={f} className="flex items-center gap-1 rounded-full border border-(--c-border-med) bg-(--c-surface-2) px-2.5 py-1 text-xs">
              {f}
              <button onClick={() => onToggle(f)} className="text-(--c-text-faint) hover:text-(--c-text)"><X size={11} /></button>
            </span>
          ))}
        </div>
      )}

      <p className={`text-xs ${selected.length >= 2 ? "text-(--c-text-faint)" : "text-amber-400"}`}>
        {selected.length < 2
          ? `Selecciona al menos 2 funcionalidades (llevas ${selected.length})`
          : `${selected.length} funcionalidades seleccionadas ✓`}
      </p>
    </div>
  );
}

/* ─── Main page ───────────────────────────────────────────────────────── */

export function NewProjectPage() {
  const navigate = useNavigate();
  const { messages, typing, pushAI, pushUser } = useChat();
  const [step, setStep] = useState<ChatStep>("greeting");
  const [data, setData] = useState<WizardData>(EMPTY_DATA);
  const [textInput, setTextInput] = useState("");
  const [suggestedFeatures, setSuggestedFeatures] = useState<string[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [customFeatureInput, setCustomFeatureInput] = useState("");
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
    // pushAI is safe to call here: the useChat cleanup cancels any in-flight
    // timers on StrictMode's simulated unmount, so the second mount starts fresh.
    pushAI(
      `¡Hola! Soy **ProgresIA**, tu co-fundador técnico virtual.\n\nMi trabajo es convertir tu idea en un **MVP completo**: requisitos, arquitectura, código y documentación — todo adaptado a tu sector y generado con IA.\n\nCuéntame, ¿cómo se llama el proyecto que tienes en mente?`,
      () => setStep("name")
    );
  }, [pushAI]);

  /* ── Feature suggestions ──────────────────────────────────────────── */

  const fetchSuggestions = useCallback(async (sector: string, problem: string, targetUsers: string) => {
    setLoadingSuggestions(true);
    try {
      const res = await api.post<{ features: string[] }>("/jobs/suggest-features", { sector, problem, targetUsers });
      setSuggestedFeatures(res.data.features ?? []);
    } catch {
      setSuggestedFeatures([
        "Registro y autenticacion de usuarios", "Dashboard con metricas clave",
        "Gestion de perfiles y preferencias", "Busqueda y filtros avanzados",
        "Notificaciones por email", "Panel de administracion",
        "Exportacion de datos", "Historial de actividad"
      ]);
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  /* ── Step handlers ──────────────────────────────────────────────────── */

  function submitName() {
    const val = textInput.trim();
    if (val.length < 2) return;
    pushUser(val);
    setTextInput("");
    if (!looksLikeProjectName(val)) {
      pushAI(notANameMsg());
      return;
    }
    setData(d => ({ ...d, name: val }));
    pushAI(nameReactionMsg(val));
    pushAI(sectorMsg(val), () => setStep("sector"));
  }

  function submitSector(sector: string) {
    pushUser(sector);
    setData(d => ({ ...d, sector }));
    const insight = SECTOR_INSIGHTS[sector] ?? DEFAULT_SECTOR_INSIGHT;
    pushAI(insight);
    pushAI(`¿Qué **tipo de producto** es "${data.name}"?`, () => setStep("productType"));
  }

  function submitProductType(type: string) {
    pushUser(type);
    setData(d => ({ ...d, productType: type }));
    const insight = PRODUCT_TYPE_INSIGHTS[type];
    if (insight) {
      pushAI(insight);
    }
    pushAI(
      `Ahora lo más importante: ¿cuál es el **problema concreto** que resuelves?\n\nSé específico — "gestionar X de forma manual lleva Y horas" es mejor que "mejorar la eficiencia". Cuanto más preciso, mejor será el código.`,
      () => setStep("problem")
    );
  }

  function submitProblem() {
    const val = textInput.trim();
    if (val.length < 10) return;
    pushUser(val);
    setData(d => ({ ...d, problem: val }));
    setTextInput("");
    pushAI(problemReactionMsg(val));
    pushAI(
      `¿**Quién** lo va a usar? Descríbeme los perfiles de usuario.\n\n_Ejemplo: "gestores de almacén que hoy hacen seguimiento en hojas de cálculo"_`,
      () => setStep("users")
    );
  }

  function submitUsers() {
    const val = textInput.trim();
    if (val.length < 2) return;
    pushUser(val);
    const newData = { ...data, targetUsers: val };
    setData(newData);
    setTextInput("");
    pushAI(usersReactionMsg(val));
    pushAI(
      `Basándome en el sector **${newData.sector}** y tu descripción, voy a sugerirte funcionalidades relevantes para "${newData.name}".\n\n✨ Selecciona las que necesitas y añade las tuyas propias.`,
      () => {
        setStep("features");
        void fetchSuggestions(newData.sector, newData.problem, newData.targetUsers);
      }
    );
  }

  function toggleFeature(f: string) {
    setData(d => ({
      ...d,
      features: d.features.includes(f) ? d.features.filter(x => x !== f) : [...d.features, f]
    }));
  }

  function addCustomFeature() {
    const val = customFeatureInput.trim();
    if (!val || data.features.includes(val)) return;
    setData(d => ({ ...d, features: [...d.features, val] }));
    setCustomFeatureInput("");
  }

  function submitFeatures() {
    if (data.features.length < 2) return;
    pushUser(`${data.features.length} funcionalidades seleccionadas`);
    pushAI(featuresReactionMsg(data.features));
    pushAI(
      `Casi lo tenemos. ¿Qué **módulos técnicos** incluye el proyecto?`,
      () => setStep("modules")
    );
  }

  function submitModules() {
    const mods = [data.needsAuth && "Autenticación JWT", data.needsAdminPanel && "Panel admin", data.needsAi && "Módulo IA"].filter(Boolean);
    pushUser(mods.length ? mods.join(", ") : "Sin módulos extra");
    pushAI(summaryMsg(data), () => setStep("summary"));
  }

  async function submitProject() {
    setSubmitting(true);
    setServerError(null);
    try {
      const ws = workspacesQuery.data?.[0];
      if (!ws) throw new Error("No se encontró workspace");

      const project = (await api.post<Project>("/projects", {
        workspaceId: ws.id,
        name: data.name,
        sector: data.sector,
        productType: data.productType,
        description: data.problem
      })).data;

      await api.post("/ideas", {
        projectId: project.id,
        problem: data.problem,
        targetUsers: data.targetUsers,
        coreFeatures: data.features,
        complexity: "standard",
        needsAuth: data.needsAuth,
        needsAdminPanel: data.needsAdminPanel,
        needsAi: data.needsAi
      });

      navigate(`/projects/${project.slug}`);
    } catch (err) {
      setServerError(getErrorMessage(err));
      setSubmitting(false);
    }
  }

  /* ── Input per step ─────────────────────────────────────────────────── */

  function renderInput() {
    if (typing || step === "greeting") return null;

    if (step === "name" || step === "problem" || step === "users") {
      const isTextarea = step === "problem";
      const placeholder =
        step === "name" ? "Nombre de tu proyecto..." :
        step === "problem" ? "Describe el problema que resuelves con detalle..." :
        "Describe los perfiles de usuario...";
      const onSubmit = step === "name" ? submitName : step === "problem" ? submitProblem : submitUsers;
      const minLen = step === "name" ? 2 : 10;

      return (
        <div className="flex gap-2">
          {isTextarea ? (
            <textarea className="input min-h-24 flex-1 resize-none text-sm" placeholder={placeholder}
              value={textInput} onChange={e => setTextInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && e.metaKey && onSubmit()} autoFocus />
          ) : (
            <input className="input flex-1 text-sm" placeholder={placeholder}
              value={textInput} onChange={e => setTextInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && onSubmit()} autoFocus />
          )}
          <button className="icon-button self-end" onClick={onSubmit}
            disabled={textInput.trim().length < minLen}>
            <Send size={16} />
          </button>
        </div>
      );
    }

    if (step === "sector") {
      return (
        <div className="grid grid-cols-2 gap-2">
          {SECTORS.map(s => (
            <button key={s} onClick={() => submitSector(s)} className="secondary-button justify-start text-sm">{s}</button>
          ))}
        </div>
      );
    }

    if (step === "productType") {
      return (
        <div className="grid grid-cols-2 gap-2">
          {PRODUCT_TYPES.map(t => (
            <button key={t} onClick={() => submitProductType(t)} className="secondary-button justify-start text-sm">{t}</button>
          ))}
        </div>
      );
    }

    if (step === "features") {
      return (
        <div className="grid gap-3">
          <FeaturePicker suggested={suggestedFeatures} selected={data.features} onToggle={toggleFeature}
            customInput={customFeatureInput} onCustomInput={setCustomFeatureInput}
            onAddCustom={addCustomFeature} loadingSuggestions={loadingSuggestions} />
          <button className="primary-button justify-center" onClick={submitFeatures}
            disabled={data.features.length < 2 || loadingSuggestions}>
            Continuar <ChevronRight size={16} />
          </button>
        </div>
      );
    }

    if (step === "modules") {
      return (
        <div className="grid gap-3">
          <div className="grid gap-1.5 rounded-xl border border-(--c-border-subtle) p-4">
            {[
              { key: "needsAuth", label: "Sistema de registro y login (JWT)", icon: "🔐", tip: "Imprescindible si cada usuario tiene sus propios datos" },
              { key: "needsAdminPanel", label: "Panel de administración interno", icon: "⚙️", tip: "Para gestionar usuarios, contenido y configuración" },
              { key: "needsAi", label: "Módulo de inteligencia artificial", icon: "🤖", tip: "Análisis, sugerencias o automatización con Ollama/LangChain" }
            ].map(({ key, label, icon, tip }) => (
              <label key={key} className="flex cursor-pointer items-start gap-3 rounded-lg p-2.5 transition-colors hover:bg-(--c-surface-2)">
                <input type="checkbox"
                  checked={data[key as keyof WizardData] as boolean}
                  onChange={e => setData(d => ({ ...d, [key]: e.target.checked }))}
                  className="mt-0.5 size-4 accent-(--c-accent)" />
                <div>
                  <span className="text-sm">{icon} {label}</span>
                  <p className="mt-0.5 text-xs text-(--c-text-muted)">{tip}</p>
                </div>
              </label>
            ))}
          </div>
          <button className="primary-button justify-center" onClick={submitModules}>
            Ver resumen <ChevronRight size={16} />
          </button>
        </div>
      );
    }

    if (step === "summary") {
      return (
        <div className="grid gap-3">
          <TechCard data={data} />
          {serverError && (
            <p className="rounded-lg border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-300">{serverError}</p>
          )}
          <button className="primary-button justify-center py-3.5 text-base" onClick={submitProject} disabled={submitting}>
            {submitting ? (
              <><Loader2 size={18} className="animate-spin" /> Creando proyecto...</>
            ) : (
              <><Sparkles size={18} /> Crear y generar mi MVP con IA</>
            )}
          </button>
          <button className="secondary-button justify-center text-sm"
            onClick={() => { setStep("name"); setData(EMPTY_DATA); setTextInput(""); }}>
            Empezar de nuevo
          </button>
        </div>
      );
    }

    return null;
  }

  /* ─────────────────────────────────────────────────────────────── */

  return (
    <div className="mx-auto flex max-w-2xl flex-col" style={{ height: "calc(100vh - 9rem)" }}>
      <div className="mb-3 flex items-center justify-between">
        <Link className="subtle-link inline-flex items-center gap-1.5 text-sm" to="/">
          <ArrowLeft size={15} /> Volver
        </Link>
        {step !== "greeting" && step !== "name" && <StepDots step={step} />}
      </div>

      {/* Chat area */}
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

      {/* Input area — capped so chat area always stays visible */}
      {(() => { const node = renderInput(); return node ? <div className="mt-3 max-h-[48vh] overflow-y-auto rounded-xl border border-(--c-border-subtle) bg-(--c-surface) p-4">{node}</div> : null; })()}

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
