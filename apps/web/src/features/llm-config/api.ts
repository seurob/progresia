import { api } from "../../lib/api";
import type { LlmConfig, OllamaModels, ProviderModelCatalog } from "./types";

export async function fetchLlmConfig(): Promise<LlmConfig> {
  const { data } = await api.get<LlmConfig>("/llm-config");
  return data;
}

export async function fetchOllamaModels(): Promise<OllamaModels> {
  const { data } = await api.get<OllamaModels>("/llm-config/ollama-models");
  return data;
}

export async function fetchProviderModels(): Promise<ProviderModelCatalog> {
  const { data } = await api.get<ProviderModelCatalog>("/llm-config/provider-models");
  return data;
}

export async function updateLlmConfig(payload: Record<string, unknown>): Promise<LlmConfig> {
  const { data } = await api.patch<LlmConfig>("/llm-config", payload);
  return data;
}
