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
    return this.configService.get<string>("AI_SERVICE_URL", "http://127.0.0.1:8000");
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
}
