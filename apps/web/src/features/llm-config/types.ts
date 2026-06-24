export type CloudProvider = "groq" | "openai" | "gemini";
export type ProviderName = CloudProvider | "ollama";

export interface ProviderInfo {
  name: ProviderName;
  has_key: boolean;
  model: string;
  default_model: string;
  code_model?: string | null;
  default_code_model?: string | null;
}

export interface LlmConfig {
  override_provider: ProviderName | null;
  providers: ProviderInfo[];
  task_routing: Record<string, string>;
  ollama_base_url: string;
  cloud_order: CloudProvider[];
}

export interface OllamaModel {
  name: string;
  size?: number | null;
  parameter_size?: string | null;
  quantization_level?: string | null;
}

export interface OllamaModels {
  available: boolean;
  base_url: string;
  models: OllamaModel[];
  error?: string | null;
}

export type ProviderModelCatalog = Partial<Record<CloudProvider, string[]>>;
