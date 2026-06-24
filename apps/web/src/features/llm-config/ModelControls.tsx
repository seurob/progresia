import type {
  CloudProvider,
  ProviderInfo,
  ProviderModelCatalog,
} from "./types";

const PROVIDER_LABELS: Record<CloudProvider, string> = {
  groq: "Groq",
  openai: "OpenAI",
  gemini: "Google Gemini",
};

interface ModelControlsProps {
  readonly cloudOrder: CloudProvider[];
  readonly providers: ProviderInfo[];
  readonly providerModels: ProviderModelCatalog;
  readonly ollamaModels: string[];
  readonly modelDrafts: Record<string, string>;
  readonly onCloudOrderChange: (slotIndex: number, provider: CloudProvider) => void;
  readonly onModelChange: (key: string, value: string) => void;
}

export function ModelControls({
  cloudOrder,
  providers,
  providerModels,
  ollamaModels,
  modelDrafts,
  onCloudOrderChange,
  onModelChange,
}: ModelControlsProps) {
  const availableCloudNames: CloudProvider[] = ["groq", "openai", "gemini"];

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        {cloudOrder.map((providerName, index) => {
          const provider = providers.find(item => item.name === providerName);
          const modelKey = `${providerName}_model`;
          const currentModel = modelDrafts[modelKey] ?? provider?.model ?? "";
          const models = providerModels[providerName] ?? [];

          return (
            <div
              key={providerName}
              className="grid gap-2 rounded border border-zinc-800 bg-zinc-950/50 p-3 sm:grid-cols-[2rem_10rem_1fr]"
            >
              <span className="self-center text-center font-mono text-xs text-zinc-500">
                {index + 1}
              </span>
              <select
                value={providerName}
                onChange={event =>
                  onCloudOrderChange(index, event.target.value as CloudProvider)
                }
                className="rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-200"
              >
                {availableCloudNames.map(name => (
                  <option key={name} value={name}>
                    {PROVIDER_LABELS[name]}
                  </option>
                ))}
              </select>
              <ModelSelect
                value={currentModel}
                options={models}
                fallback={provider?.default_model ?? ""}
                onChange={value => onModelChange(modelKey, value)}
              />
            </div>
          );
        })}
      </div>

      {ollamaModels.length > 0 && (
        <OllamaModelSlots
          providers={providers}
          ollamaModels={ollamaModels}
          modelDrafts={modelDrafts}
          onChange={onModelChange}
        />
      )}
    </div>
  );
}

interface ModelSelectProps {
  readonly value: string;
  readonly options: string[];
  readonly fallback: string;
  readonly onChange: (value: string) => void;
}

function ModelSelect({ value, options, fallback, onChange }: ModelSelectProps) {
  const uniqueOptions = Array.from(new Set([value, ...options].filter(Boolean)));

  if (uniqueOptions.length <= 1) {
    return (
      <input
        value={value}
        placeholder={fallback}
        onChange={event => onChange(event.target.value)}
        className="rounded border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-200"
      />
    );
  }

  return (
    <select
      value={value}
      onChange={event => onChange(event.target.value)}
      className="rounded border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-200"
    >
      {uniqueOptions.map(model => (
        <option key={model} value={model}>
          {model}
        </option>
      ))}
    </select>
  );
}

interface OllamaModelSlotsProps {
  readonly providers: ProviderInfo[];
  readonly ollamaModels: string[];
  readonly modelDrafts: Record<string, string>;
  readonly onChange: (key: string, value: string) => void;
}

function OllamaModelSlots({
  providers,
  ollamaModels,
  modelDrafts,
  onChange,
}: OllamaModelSlotsProps) {
  const ollamaInfo = providers.find(provider => provider.name === "ollama");
  const reasoningModel =
    modelDrafts.ollama_reasoning_model ?? ollamaInfo?.model ?? "";
  const codeModel =
    modelDrafts.ollama_code_model ?? ollamaInfo?.code_model ?? "";
  const slots = [
    {
      key: "ollama_reasoning_model",
      label: "Local - razonamiento",
      current: reasoningModel,
      other: codeModel,
    },
    {
      key: "ollama_code_model",
      label: "Local - codigo",
      current: codeModel,
      other: reasoningModel,
    },
  ];

  return (
    <div className="space-y-2 border-t border-zinc-800 pt-4">
      {slots.map(({ key, label, current, other }) => (
        <div key={key} className="flex items-center gap-3">
          <span className="w-36 shrink-0 text-xs text-zinc-500">{label}</span>
          <ModelSelect
            value={current}
            options={ollamaModels.filter(model => model !== other)}
            fallback=""
            onChange={value => onChange(key, value)}
          />
        </div>
      ))}
    </div>
  );
}
