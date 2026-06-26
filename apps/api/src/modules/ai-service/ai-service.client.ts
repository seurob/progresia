import { BadGatewayException, Injectable } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";

export interface AiIdeaRequest {
  name: string;
  sector: string;
  problem: string;
  target_users: string;
  core_features: string[];
  needs_auth: boolean;
  needs_admin_panel: boolean;
  needs_ai: boolean;
  /** BEGINNER | INTERMEDIATE | ADVANCED — drives architecture and tutorial depth */
  technical_level?: string;
  /** Forwarded from a stored ARCHITECTURE spec so OpenSpecAgent can embed the chosen stack. */
  architecture_type?: string;
  /** web | mobile | desktop | api | saas | ai_tool — constrains stack selection in all agents */
  product_type?: string;
}

export interface AiOpenSpecResponse {
  project_name: string;
  spec: Record<string, unknown>;
}

export interface AiRequirementItem {
  id: string;
  title: string;
  description: string;
}

export interface AiRequirementsResponse {
  project_name: string;
  functional_requirements: AiRequirementItem[];
  non_functional_requirements: AiRequirementItem[];
  user_stories: Array<{ id: string; actor: string; goal: string; benefit: string }>;
}

export interface AiCodeGenRequest {
  project_name: string;
  sector: string;
  modules: string[];
  requirements: Array<{ id: string; title: string; description: string }>;
  needs_auth: boolean;
  needs_admin_panel: boolean;
  needs_ai: boolean;
  stack: string[];
  architecture_type?: string;
  /** BEGINNER | INTERMEDIATE | ADVANCED — routes to Express scaffold for BEGINNER */
  technical_level?: string;
  data_entities?: Array<{ name: string; description?: string; fields?: string[]; relations?: string[] }>;
  api_endpoints?: Array<{ method: string; path: string; description: string; auth_required?: boolean }>;
}

export interface AiIssueGenerationRequest {
  project_name: string;
  sector: string;
  openspec: Record<string, unknown>;
}

export interface AiGitHubIssue {
  title: string;
  body: string;
  labels: string[];
  priority: string;
  milestone: string | null;
}

export interface AiIssueGenerationResponse {
  project_name: string;
  milestones: string[];
  issues: AiGitHubIssue[];
  total: number;
}

export interface AiArchitectureRequest {
  project_name: string;
  sector: string;
  problem: string;
  target_users: string;
  key_features: string[];
  needs_auth: boolean;
  needs_admin_panel: boolean;
  needs_ai: boolean;
  preferred_stack: string;
  /** BEGINNER | INTERMEDIATE | ADVANCED — constrains which architectures to recommend */
  technical_level?: string;
  /** web | mobile | desktop | api | saas | ai_tool — bypasses LLM for mobile/desktop */
  product_type?: string;
  /** single | modular | frontend_api | ai_service | mobile_api | desktop_api */
  architecture_style?: string;
  /** relational | document | cache | vector */
  data_needs?: string[];
  /** none | online | local | hybrid | chat_docs | rag | agents | recommendation */
  ai_needs?: string;
  /** local | docker_local | vps | cloud | recommendation */
  deployment_target?: string;
}

export interface AiTechStackItem {
  name: string;
  version: string;
  purpose: string;
  official_docs: string;
}

export interface AiLearningResource {
  title: string;
  url: string;
  type: string;
  level: string;
}

export interface AiUpgradeSignal {
  signal: string;
  reason: string;
  next_step: string;
}

export interface AiArchitectureRecommendation {
  architecture_type: string;
  name: string;
  justification: string;
  tech_stack: AiTechStackItem[];
  alternatives: string[];
  difficulty: string;
  risks: string[];
  first_steps: string[];
  educational_notes: string[];
  learning_path: AiLearningResource[];
  when_to_upgrade: AiUpgradeSignal[];
}

export interface AiTutorialStep {
  action: string;
  command?: string | null;
  notes?: string | null;
}

export interface AiTutorialPhase {
  title: string;
  description: string;
  steps: AiTutorialStep[];
}

export interface AiTutorialRequest {
  project_name: string;
  sector: string;
  architecture_type: string;
  stack: string[];
  modules: string[];
  requirements: Array<{ id: string; title: string; description: string }>;
  needs_auth: boolean;
  needs_admin_panel: boolean;
}

export interface AiTutorialResponse {
  project_name: string;
  architecture_type: string;
  phases: AiTutorialPhase[];
  total_steps: number;
}

export interface AiGeneratedFile {
  path: string;
  language: string;
  content: string;
}

export interface AiCodeGenResponse {
  project_name: string;
  files: AiGeneratedFile[];
}

export interface AiTechProposalRequest {
  name: string;
  sector: string;
  level: string;
  product_type: string;
  main_objective: string;
  architecture_style: string;
  data_needs: string[];
  ai_needs: string;
  deployment_target: string;
  core_features: string[];
  mandatory_techs?: string;
}

export interface AiTechProposal {
  id: number;
  name: string;
  tagline: string;
  stack: string[];
  difficulty: string;
  description: string;
  advantages: string[];
  limitations: string[];
  recommended_for: string;
  learning_outcomes: string[];
  docker_ready: boolean;
  ai_ready: boolean;
  estimated_setup_minutes: number;
}

export interface AiTechProposalResponse {
  proposals: AiTechProposal[];
  recommended_id: number;
  recommendation_reason: string;
}

@Injectable()
export class AiServiceClient {
  constructor(private readonly configService: ConfigService) {}

  private get baseUrl(): string {
    return this.configService.get<string>("AI_SERVICE_URL", "http://127.0.0.1:8003");
  }

  private async request<T>(method: string, path: string, payload?: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      ...(payload !== undefined ? { body: JSON.stringify(payload) } : {})
    });

    if (!response.ok) {
      const text = await response.text();
      throw new BadGatewayException(`AI service failed: ${response.status} ${text}`);
    }

    return response.json() as Promise<T>;
  }

  private async post<T>(path: string, payload: unknown): Promise<T> {
    return this.request<T>("POST", path, payload);
  }

  private async get<T>(path: string): Promise<T> {
    return this.request<T>("GET", path);
  }

  private async patch<T>(path: string, payload: unknown): Promise<T> {
    return this.request<T>("PATCH", path, payload);
  }

  async generateRequirements(payload: AiIdeaRequest): Promise<AiRequirementsResponse> {
    return this.post<AiRequirementsResponse>("/generate-requirements", payload);
  }

  async generateOpenSpec(payload: AiIdeaRequest): Promise<AiOpenSpecResponse> {
    return this.post<AiOpenSpecResponse>("/generate-openspec", payload);
  }

  async generateCode(payload: AiCodeGenRequest): Promise<AiCodeGenResponse> {
    return this.post<AiCodeGenResponse>("/generate-code", payload);
  }

  async suggestFeatures(payload: {
    sector: string;
    problem: string;
    target_users: string;
  }): Promise<{ features: string[] }> {
    return this.post<{ features: string[] }>("/suggest-features", payload);
  }

  async recommendArchitecture(payload: AiArchitectureRequest): Promise<AiArchitectureRecommendation> {
    return this.post<AiArchitectureRecommendation>("/recommend-architecture", payload);
  }

  async generateIssues(payload: AiIssueGenerationRequest): Promise<AiIssueGenerationResponse> {
    return this.post<AiIssueGenerationResponse>("/generate-issues", payload);
  }

  async generateTutorial(payload: AiTutorialRequest): Promise<AiTutorialResponse> {
    return this.post<AiTutorialResponse>("/generate-tutorial", payload);
  }

  async proposeTech(payload: AiTechProposalRequest): Promise<AiTechProposalResponse> {
    return this.post<AiTechProposalResponse>("/propose-tech", payload);
  }

  async getLlmConfig(): Promise<AiLlmConfigResponse> {
    return this.get<AiLlmConfigResponse>("/config/llm");
  }

  async updateLlmConfig(payload: AiLlmConfigUpdate): Promise<AiLlmConfigResponse> {
    return this.patch<AiLlmConfigResponse>("/config/llm", payload);
  }

  async getOllamaModels(): Promise<AiOllamaModelsResponse> {
    return this.get<AiOllamaModelsResponse>("/ollama/models");
  }

  async getProviderModels(): Promise<Record<string, string[]>> {
    return this.get<Record<string, string[]>>("/config/llm/provider-models");
  }
}

// ── LLM config types ──────────────────────────────────────────────────────────

export interface AiProviderInfo {
  name: string;
  has_key: boolean;
  model: string;
  default_model: string;
  code_model?: string | null;
  default_code_model?: string | null;
}

export interface AiTaskRouting {
  reasoning: string;
  code: string;
  spec: string;
  general: string;
}

export interface AiLlmConfigResponse {
  override_provider: string | null;
  providers: AiProviderInfo[];
  task_routing: AiTaskRouting;
  ollama_base_url: string;
  cloud_order: string[];
}

export interface AiLlmConfigUpdate {
  override_provider?: string | null;
  groq_model?: string | null;
  openai_model?: string | null;
  gemini_model?: string | null;
  ollama_reasoning_model?: string | null;
  ollama_code_model?: string | null;
  cloud_order?: string[] | null;
  reset_models?: boolean;
}

export interface AiOllamaModel {
  name: string;
  size?: number | null;
  modified_at?: string | null;
  parameter_size?: string | null;
  quantization_level?: string | null;
}

export interface AiOllamaModelsResponse {
  available: boolean;
  base_url: string;
  models: AiOllamaModel[];
  error?: string | null;
}
