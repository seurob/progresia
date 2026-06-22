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
  /** Forwarded from a stored ARCHITECTURE spec so OpenSpecAgent can embed the chosen stack. */
  architecture_type?: string;
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

@Injectable()
export class AiServiceClient {
  constructor(private readonly configService: ConfigService) {}

  private get baseUrl(): string {
    return this.configService.get<string>("AI_SERVICE_URL", "http://127.0.0.1:8001");
  }

  private async post<T>(path: string, payload: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new BadGatewayException(`AI service failed: ${response.status} ${text}`);
    }

    return response.json() as Promise<T>;
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
}
