import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, ChevronRight, Cpu, RefreshCw, Wifi, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ProviderInfo {
  name: string;
  has_key: boolean;
  model: string;
  default_model: string;
  code_model?: string | null;
  default_code_model?: string | null;
}

interface LlmConfig {
  override_provider: string | null;
  providers: ProviderInfo[];
  task_routing: { reasoning: string; code: string; spec: string; general: string };
  ollama_base_url: string;
}

interface OllamaModel {
  name: string;
  size?: number | null;
  parameter_size?: string | null;
  quantization_level?: string | null;
}

interface OllamaModels {
  available: boolean;
  base_url: string;
  models: OllamaModel[];
  error?: string | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const PROVIDER_LABELS: Record<string, string> = {
  groq: "Groq",
  openai: "OpenAI",
  gemini: "Google Gemini",
  ollama: "Ollama (local)"
};

const PROVIDER_COLORS: Record<string, string> = {
  groq: "text-orange-400",
  openai: "text-emerald-400",
  gemini: "text-sky-400",
  ollama: "text-violet-400"
};

const TASK_LABELS: Record<string, string> = {
  reasoning: "Razonamiento",
  code: "Código",
  spec: "Especificación",
  general: "General"
};

function formatBytes(bytes: number): string {
  if (bytes < 1e9) return `${(bytes / 1e6).toFixed(0)} MB`;
  return `${(bytes / 1e9).toFixed(1)} GB`;
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────

async function fetchConfig(): Promise<LlmConfig> {
  const { data } = await api.get<LlmConfig>("/llm-config");
  return data;
}

async function fetchOllama(): Promise<OllamaModels> {
  const { data } = await api.get<OllamaModels>("/llm-config/ollama-models");
  return data;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function AiSettingsPage() {
  const qc = useQueryClient();
  const [pendingOverride, setPendingOverride] = useState<string | undefined>(undefined);
  const [modelDrafts, setModelDrafts] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  const { data: config, isLoading, isError } = useQuery<LlmConfig>({
    queryKey: ["llm-config"],
    queryFn: fetchConfig
  });

  useEffect(() => {
    if (config && pendingOverride === undefined) {
      setPendingOverride(config.override_provider ?? "auto");
    }
  }, [config, pendingOverride]);

  const { data: ollama, refetch: refetchOllama, isFetching: ollamaFetching } = useQuery({
    queryKey: ["ollama-models"],
    queryFn: fetchOllama,
    retry: false,
    staleTime: 30_000
  });

  const mutation = useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const { data } = await api.patch<LlmConfig>("/llm-config", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["llm-config"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    }
  });

  const activeOverride = pendingOverride ?? config?.override_provider ?? "auto";

  function handleSave() {
    const payload: Record<string, unknown> = {
      override_provider: activeOverride === "auto" ? null : activeOverride
    };
    for (const [k, v] of Object.entries(modelDrafts)) {
      if (v.trim()) payload[k] = v.trim();
    }
    mutation.mutate(payload);
  }

  function handleReset() {
    mutation.mutate({ reset_models: true });
    setModelDrafts({});
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="animate-spin text-zinc-500" size={22} />
      </div>
    );
  }

  if (isError || !config) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 text-zinc-400">
        <AlertCircle size={28} />
        <p className="text-sm">No se pudo conectar con el AI service.</p>
      </div>
    );
  }

  const providers = config.providers;

  return (
    <div className="mx-auto max-w-3xl space-y-8">

      {/* ── Header ── */}
      <div>
        <h1 className="text-xl font-semibold text-zinc-100">Configuración IA</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Controla qué modelo de lenguaje usa el pipeline en tiempo real.
          Los cambios son inmediatos pero se resetean al reiniciar el servicio.
        </p>
      </div>

      {/* ── Provider selector ── */}
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-zinc-400">
          Proveedor activo
        </h2>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {(["auto", "groq", "openai", "gemini", "ollama"] as const).map((opt) => {
            const isActive = activeOverride === opt;
            const providerInfo = providers.find(p => p.name === opt);
            const hasKey = opt === "auto" || opt === "ollama" || (providerInfo?.has_key ?? false);
            return (
              <button
                key={opt}
                onClick={() => setPendingOverride(opt)}
                disabled={!hasKey}
                className={`flex items-center gap-3 rounded-md border px-4 py-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                  isActive
                    ? "border-emerald-500/60 bg-emerald-500/10 text-zinc-100"
                    : "border-zinc-700 bg-zinc-800/50 text-zinc-300 hover:border-zinc-600 hover:bg-zinc-800"
                }`}
              >
                <span className={`size-2 shrink-0 rounded-full ${isActive ? "bg-emerald-400" : "bg-zinc-600"}`} />
                <span className="text-sm font-medium">
                  {opt === "auto" ? "Automático" : PROVIDER_LABELS[opt]}
                </span>
              </button>
            );
          })}
        </div>
        {activeOverride === "auto" && (
          <p className="mt-3 text-xs text-zinc-500">
            Modo automático: cada tarea usa el proveedor óptimo según la tabla de enrutamiento.
          </p>
        )}
        {activeOverride !== "auto" && (
          <p className="mt-3 text-xs text-zinc-500">
            Forzado: <span className={`font-medium ${PROVIDER_COLORS[activeOverride] ?? "text-zinc-300"}`}>
              {PROVIDER_LABELS[activeOverride] ?? activeOverride}
            </span> se usará para todas las tareas. Si falla, el pipeline cae al enrutamiento automático.
          </p>
        )}
      </section>

      {/* ── Task routing ── */}
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-zinc-400">
          Enrutamiento de tareas
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="pb-2 text-left text-xs font-medium text-zinc-500">Tarea</th>
                <th className="pb-2 text-left text-xs font-medium text-zinc-500">Proveedor resuelto</th>
                <th className="pb-2 text-left text-xs font-medium text-zinc-500">Modelo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {Object.entries(config.task_routing).map(([task, provider]) => {
                const provInfo = providers.find(p => p.name === provider);
                const model = task === "code" && provider === "ollama"
                  ? (provInfo?.code_model ?? provInfo?.model)
                  : provInfo?.model;
                return (
                  <tr key={task}>
                    <td className="py-2.5 pr-4 text-zinc-300">{TASK_LABELS[task] ?? task}</td>
                    <td className="py-2.5 pr-4">
                      <span className={`font-medium ${PROVIDER_COLORS[provider] ?? "text-zinc-300"}`}>
                        {PROVIDER_LABELS[provider] ?? provider}
                      </span>
                    </td>
                    <td className="py-2.5 font-mono text-xs text-zinc-500">{model ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Providers + model overrides ── */}
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
            Modelos configurados
          </h2>
          <button
            onClick={handleReset}
            className="text-xs text-zinc-500 underline-offset-2 hover:text-zinc-300 hover:underline"
          >
            Resetear overrides
          </button>
        </div>
        <div className="space-y-3">
          {providers.map((p) => {
            const isOllama = p.name === "ollama";
            const fields = isOllama
              ? [
                  { key: "ollama_reasoning_model", label: "Razonamiento", current: p.model, default: p.default_model },
                  { key: "ollama_code_model", label: "Código", current: p.code_model ?? "", default: p.default_code_model ?? "" }
                ]
              : [{ key: `${p.name}_model`, label: "Modelo", current: p.model, default: p.default_model }];

            return (
              <div key={p.name} className="rounded-md border border-zinc-800 bg-zinc-950/50 px-4 py-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className={`text-sm font-semibold ${PROVIDER_COLORS[p.name] ?? "text-zinc-300"}`}>
                    {PROVIDER_LABELS[p.name] ?? p.name}
                  </span>
                  {p.has_key && !isOllama ? (
                    <span className="flex items-center gap-1 text-xs text-emerald-400">
                      <CheckCircle2 size={11} /> API key configurada
                    </span>
                  ) : isOllama ? (
                    <span className="text-xs text-zinc-500">sin API key — requiere servidor local</span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-amber-400">
                      <AlertCircle size={11} /> Sin API key
                    </span>
                  )}
                </div>
                <div className="space-y-2">
                  {fields.map(({ key, label, current, default: dflt }) => (
                    <div key={key} className="flex items-center gap-2">
                      {isOllama && (
                        <span className="w-24 shrink-0 text-xs text-zinc-500">{label}</span>
                      )}
                      <input
                        className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 font-mono text-xs text-zinc-200 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
                        placeholder={dflt}
                        value={modelDrafts[key] ?? current}
                        onChange={e => setModelDrafts(d => ({ ...d, [key]: e.target.value }))}
                      />
                      {current !== dflt && (
                        <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-400">
                          override
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Ollama status ── */}
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
            Ollama — modelos locales
          </h2>
          <button
            onClick={() => refetchOllama()}
            disabled={ollamaFetching}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300"
          >
            <RefreshCw size={13} className={ollamaFetching ? "animate-spin" : ""} />
            Actualizar
          </button>
        </div>

        {ollama?.available ? (
          <>
            <div className="mb-3 flex items-center gap-2 text-sm text-emerald-400">
              <Wifi size={15} />
              <span>Ollama disponible en <code className="font-mono text-xs">{ollama.base_url}</code></span>
            </div>
            {ollama.models.length === 0 ? (
              <p className="text-sm text-zinc-400">
                No hay modelos instalados. Instala con{" "}
                <code className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs">ollama pull llama3.1</code>
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800">
                      <th className="pb-2 text-left text-xs font-medium text-zinc-500">Modelo</th>
                      <th className="pb-2 text-left text-xs font-medium text-zinc-500">Tamaño</th>
                      <th className="pb-2 text-left text-xs font-medium text-zinc-500">Parámetros</th>
                      <th className="pb-2 text-left text-xs font-medium text-zinc-500">Cuantización</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50">
                    {ollama.models.map((m) => (
                      <tr key={m.name}>
                        <td className="py-2.5 pr-4 font-mono text-xs text-violet-300">{m.name}</td>
                        <td className="py-2.5 pr-4 text-xs text-zinc-400">
                          {m.size ? formatBytes(m.size) : "—"}
                        </td>
                        <td className="py-2.5 pr-4 text-xs text-zinc-400">{m.parameter_size ?? "—"}</td>
                        <td className="py-2.5 text-xs text-zinc-400">{m.quantization_level ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <WifiOff size={15} />
              <span>
                Ollama no disponible en <code className="font-mono text-xs">{ollama?.base_url ?? config.ollama_base_url}</code>
              </span>
            </div>
            <div className="rounded-md border border-zinc-800 bg-zinc-950 p-4">
              <p className="mb-2 text-xs font-semibold text-zinc-300">Cómo instalar Ollama:</p>
              <ol className="space-y-1.5 text-xs text-zinc-400">
                <li className="flex items-start gap-2">
                  <ChevronRight size={13} className="mt-0.5 shrink-0 text-zinc-600" />
                  Descarga Ollama desde{" "}
                  <a href="https://ollama.com" target="_blank" rel="noreferrer" className="text-violet-400 hover:underline">
                    ollama.com
                  </a>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight size={13} className="mt-0.5 shrink-0 text-zinc-600" />
                  <code className="rounded bg-zinc-800 px-1.5 py-0.5">ollama pull llama3.1</code>
                  <span className="text-zinc-500">— razonamiento (~4.7 GB)</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight size={13} className="mt-0.5 shrink-0 text-zinc-600" />
                  <code className="rounded bg-zinc-800 px-1.5 py-0.5">ollama pull qwen2.5-coder</code>
                  <span className="text-zinc-500">— generación de código (~4.7 GB)</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight size={13} className="mt-0.5 shrink-0 text-zinc-600" />
                  <code className="rounded bg-zinc-800 px-1.5 py-0.5">ollama serve</code>
                  <span className="text-zinc-500">— arranca el servidor local</span>
                </li>
              </ol>
            </div>
          </div>
        )}
      </section>

      {/* ── Save bar ── */}
      <div className="sticky bottom-8 flex items-center justify-end gap-3 rounded-lg border border-zinc-700 bg-zinc-950/95 p-4 shadow-xl backdrop-blur">
        {saved && (
          <span className="flex items-center gap-1.5 text-sm text-emerald-400">
            <CheckCircle2 size={15} />
            Guardado
          </span>
        )}
        {mutation.isError && (
          <span className="flex items-center gap-1.5 text-sm text-red-400">
            <AlertCircle size={15} />
            Error al guardar
          </span>
        )}
        <button
          onClick={handleSave}
          disabled={mutation.isPending}
          className="flex items-center gap-2 rounded-md bg-emerald-500 px-5 py-2 text-sm font-semibold text-zinc-950 hover:bg-emerald-400 disabled:opacity-60"
        >
          {mutation.isPending ? (
            <><RefreshCw size={14} className="animate-spin" /> Guardando…</>
          ) : (
            <><Cpu size={14} /> Aplicar configuración</>
          )}
        </button>
      </div>

    </div>
  );
}
