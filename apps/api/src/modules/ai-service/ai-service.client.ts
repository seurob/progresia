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

@Injectable()
export class AiServiceClient {
  constructor(private readonly configService: ConfigService) {}

  async generateOpenSpec(payload: AiIdeaRequest): Promise<AiOpenSpecResponse> {
    const baseUrl = this.configService.get<string>("AI_SERVICE_URL", "http://127.0.0.1:8000");
    const response = await fetch(`${baseUrl}/generate-openspec`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new BadGatewayException(`AI service failed: ${response.status} ${text}`);
    }

    return response.json() as Promise<AiOpenSpecResponse>;
  }
}
