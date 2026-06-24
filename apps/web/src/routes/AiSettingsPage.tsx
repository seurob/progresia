import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Cpu,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  fetchLlmConfig,
  fetchOllamaModels,
  fetchProviderModels,
  updateLlmConfig,
} from "../features/llm-config/api";
import { ModelControls } from "../features/llm-config/ModelControls";
import type {
  CloudProvider,
  LlmConfig,
  OllamaModels,
  ProviderName,
} from "../features/llm-config/types";

const PROVIDER_LABELS: Record<string, string> = {
  groq: "Groq",
  openai: "OpenAI",
  gemini: "Google Gemini",
  ollama: "Ollama (local)",
};

const PROVIDER_COLORS: Record<string, string> = {
  groq: "text-orange-400",
  openai: "text-emerald-400",
  gemini: "text-sky-400",
  ollama: "text-violet-400",
};

const TASK_LABELS: Record<string, string> = {
  reasoning: "Razonamiento",
  code: "Codigo",
  spec: "Especificacion",
  general: "General",
};

function formatBytes(bytes: number): string {
  if (bytes < 1e9) return `${(bytes / 1e6).toFixed(0)} MB`;
  return `${(bytes / 1e9).toFixed(1)} GB`;
}

export function AiSettingsPage() {
  const queryClient = useQueryClient();
  const [pendingOverride, setPendingOverride] = useState<ProviderName | "auto">("auto");
  const [cloudOrderDraft, setCloudOrderDraft] = useState<CloudProvider[]>();
  const [modelDrafts, setModelDrafts] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  const configQuery = useQuery({
    queryKey: ["llm-config"],
    queryFn: fetchLlmConfig,
  });
  const ollamaQuery = useQuery({
    queryKey: ["ollama-models"],
    queryFn: fetchOllamaModels,
    retry: false,
    staleTime: 30_000,
  });
  const providerModelsQuery = useQuery({
    queryKey: ["provider-models"],
    queryFn: fetchProviderModels,
    staleTime: 5 * 60_000,
  });

  const config = configQuery.data;
  useEffect(() => {
    if (!config) return;
    setPendingOverride(config.override_provider ?? "auto");
    setCloudOrderDraft(config.cloud_order);
  }, [config]);

  const mutation = useMutation({
    mutationFn: updateLlmConfig,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["llm-config"] });
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    },
  });

  if (configQuery.isLoading) {
    return <LoadingState />;
  }

  if (configQuery.isError || !config) {
    return <ErrorState />;
  }

  const resolvedConfig = config;
  const ollama = ollamaQuery.data;
  const providers = resolvedConfig.providers;
  const ollamaModels = ollama?.available
    ? ollama.models.map(model => model.name)
    : [];
  const cloudOrder = cloudOrderDraft ?? resolvedConfig.cloud_order;

  function saveConfiguration() {
    const payload: Record<string, unknown> = {
      override_provider: pendingOverride === "auto" ? null : pendingOverride,
      cloud_order: cloudOrder,
    };
    for (const [key, value] of Object.entries(modelDrafts)) {
      if (value.trim()) payload[key] = value.trim();
    }
    mutation.mutate(payload);
  }

  function resetModelOverrides() {
    mutation.mutate({ reset_models: true });
    setModelDrafts({});
    setCloudOrderDraft(resolvedConfig.cloud_order);
  }

  function reorderCloudProvider(slotIndex: number, newProvider: CloudProvider) {
    setCloudOrderDraft(previous => {
      const order = [...(previous ?? resolvedConfig.cloud_order)];
      const currentIndex = order.indexOf(newProvider);
      [order[slotIndex], order[currentIndex]] = [order[currentIndex], order[slotIndex]];
      return order;
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header>
        <h1 className="text-xl font-semibold text-zinc-100">Configuracion IA</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Controla el proveedor, el orden de fallback y los modelos usados por el pipeline.
          Los cambios se mantienen hasta reiniciar el servicio.
        </p>
      </header>

      <ProviderSelector
        config={resolvedConfig}
        ollama={ollama}
        activeOverride={pendingOverride}
        cloudOrder={cloudOrder}
        onChange={setPendingOverride}
      />

      <RoutingTable config={resolvedConfig} />

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
              Prioridad y modelos
            </h2>
            <p className="mt-1 text-xs text-zinc-600">
              El orden cloud se usa como fallback automatico. Codigo prioriza Ollama.
            </p>
          </div>
          <button
            type="button"
            onClick={resetModelOverrides}
            className="text-xs text-zinc-500 hover:text-zinc-300"
          >
            Resetear modelos
          </button>
        </div>

        <ModelControls
          cloudOrder={cloudOrder}
          providers={providers}
          providerModels={providerModelsQuery.data ?? {}}
          ollamaModels={ollamaModels}
          modelDrafts={modelDrafts}
          onCloudOrderChange={reorderCloudProvider}
          onModelChange={(key, value) =>
            setModelDrafts(previous => ({ ...previous, [key]: value }))
          }
        />
      </section>

      <OllamaStatus
        config={resolvedConfig}
        ollama={ollama}
        isFetching={ollamaQuery.isFetching}
        onRefresh={() => ollamaQuery.refetch()}
      />

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
          type="button"
          onClick={saveConfiguration}
          disabled={mutation.isPending}
          className="flex items-center gap-2 rounded-md bg-emerald-500 px-5 py-2 text-sm font-semibold text-zinc-950 hover:bg-emerald-400 disabled:opacity-60"
        >
          {mutation.isPending ? (
            <>
              <RefreshCw size={14} className="animate-spin" /> Guardando...
            </>
          ) : (
            <>
              <Cpu size={14} /> Aplicar configuracion
            </>
          )}
        </button>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex h-64 items-center justify-center">
      <RefreshCw className="animate-spin text-zinc-500" size={22} />
    </div>
  );
}

function ErrorState() {
  return (
    <div className="flex h-64 flex-col items-center justify-center gap-3 text-zinc-400">
      <AlertCircle size={28} />
      <p className="text-sm">No se pudo conectar con el servicio de IA.</p>
    </div>
  );
}

interface ProviderSelectorProps {
  readonly config: LlmConfig;
  readonly ollama?: OllamaModels;
  readonly activeOverride: ProviderName | "auto";
  readonly cloudOrder: CloudProvider[];
  readonly onChange: (provider: ProviderName | "auto") => void;
}

function ProviderSelector({
  config,
  ollama,
  activeOverride,
  cloudOrder,
  onChange,
}: ProviderSelectorProps) {
  const options: Array<ProviderName | "auto"> = [
    "auto",
    "groq",
    "openai",
    "gemini",
    "ollama",
  ];
  const availableOptions = options.filter(option => {
    if (option === "auto") return true;
    if (option === "ollama") return ollama?.available ?? false;
    return config.providers.find(provider => provider.name === option)?.has_key ?? false;
  });
  const fallbackOrder =
    activeOverride === "auto"
      ? [...cloudOrder, "ollama"]
      : [
          activeOverride,
          ...cloudOrder.filter(name => name !== activeOverride),
          ...(activeOverride === "ollama" ? [] : ["ollama" as const]),
        ];

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-zinc-400">
        Proveedor activo
      </h2>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {availableOptions.map(option => {
          const active = activeOverride === option;
          return (
            <button
              key={option}
              type="button"
              onClick={() => onChange(option)}
              className={`flex items-center gap-3 rounded-md border px-4 py-3 text-left transition-colors ${
                active
                  ? "border-emerald-500/60 bg-emerald-500/10 text-zinc-100"
                  : "border-zinc-700 bg-zinc-800/50 text-zinc-300 hover:border-zinc-600"
              }`}
            >
              <span className={`size-2 rounded-full ${active ? "bg-emerald-400" : "bg-zinc-600"}`} />
              <span className="text-sm font-medium">
                {option === "auto" ? "Automatico" : PROVIDER_LABELS[option]}
              </span>
            </button>
          );
        })}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
        {fallbackOrder.map((provider, index) => (
          <span key={`${provider}-${index}`} className="flex items-center gap-2">
            <span className={PROVIDER_COLORS[provider] ?? "text-zinc-400"}>
              {index + 1}. {PROVIDER_LABELS[provider] ?? provider}
            </span>
            {index < fallbackOrder.length - 1 && <span className="text-zinc-700">-&gt;</span>}
          </span>
        ))}
      </div>
    </section>
  );
}

function RoutingTable({ config }: { readonly config: LlmConfig }) {
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-zinc-400">
        Enrutamiento de tareas
      </h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
            <th className="pb-2">Tarea</th>
            <th className="pb-2">Proveedor</th>
            <th className="pb-2">Modelo</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/50">
          {Object.entries(config.task_routing).map(([task, provider]) => {
            const providerInfo = config.providers.find(item => item.name === provider);
            const model =
              task === "code" && provider === "ollama"
                ? providerInfo?.code_model
                : providerInfo?.model;
            return (
              <tr key={task}>
                <td className="py-2.5">{TASK_LABELS[task] ?? task}</td>
                <td className={`py-2.5 ${PROVIDER_COLORS[provider] ?? "text-zinc-300"}`}>
                  {PROVIDER_LABELS[provider] ?? provider}
                </td>
                <td className="py-2.5 font-mono text-xs text-zinc-500">{model ?? "-"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

interface OllamaStatusProps {
  readonly config: LlmConfig;
  readonly ollama?: OllamaModels;
  readonly isFetching: boolean;
  readonly onRefresh: () => void;
}

function OllamaStatus({ config, ollama, isFetching, onRefresh }: OllamaStatusProps) {
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
          Ollama - modelos locales
        </h2>
        <button
          type="button"
          onClick={onRefresh}
          disabled={isFetching}
          className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300"
        >
          <RefreshCw size={13} className={isFetching ? "animate-spin" : ""} />
          Actualizar
        </button>
      </div>

      {ollama?.available ? (
        <>
          <div className="mb-3 flex items-center gap-2 text-sm text-emerald-400">
            <Wifi size={15} />
            <span>
              Disponible en <code className="font-mono text-xs">{ollama.base_url}</code>
            </span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
                <th className="pb-2">Modelo</th>
                <th className="pb-2">Tamano</th>
                <th className="pb-2">Parametros</th>
                <th className="pb-2">Cuantizacion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {ollama.models.map(model => (
                <tr key={model.name}>
                  <td className="py-2.5 font-mono text-xs text-violet-300">{model.name}</td>
                  <td className="py-2.5 text-xs text-zinc-400">
                    {model.size ? formatBytes(model.size) : "-"}
                  </td>
                  <td className="py-2.5 text-xs text-zinc-400">{model.parameter_size ?? "-"}</td>
                  <td className="py-2.5 text-xs text-zinc-400">
                    {model.quantization_level ?? "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <WifiOff size={15} />
            <span>
              No disponible en{" "}
              <code className="font-mono text-xs">
                {ollama?.base_url ?? config.ollama_base_url}
              </code>
            </span>
          </div>
          <div className="rounded-md border border-zinc-800 bg-zinc-950 p-4">
            <p className="mb-2 text-xs font-semibold text-zinc-300">Instalacion local</p>
            <ol className="space-y-2 text-xs text-zinc-400">
              <li className="flex gap-2">
                <ChevronRight size={13} />
                Instala desde{" "}
                <a
                  href="https://ollama.com"
                  target="_blank"
                  rel="noreferrer"
                  className="text-violet-400 hover:underline"
                >
                  ollama.com
                </a>
              </li>
              <li className="flex gap-2">
                <ChevronRight size={13} />
                <code>ollama pull llama3.1</code>
              </li>
              <li className="flex gap-2">
                <ChevronRight size={13} />
                <code>ollama pull qwen2.5-coder</code>
              </li>
            </ol>
          </div>
        </div>
      )}
    </section>
  );
}
