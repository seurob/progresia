import { Body, Controller, Get, Patch, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import {
  AiLlmConfigResponse,
  AiLlmConfigUpdate,
  AiOllamaModelsResponse,
  AiServiceClient
} from "../ai-service/ai-service.client";

@ApiTags("llm-config")
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller("llm-config")
export class LlmConfigController {
  constructor(private readonly aiService: AiServiceClient) {}

  @Get()
  @ApiOkResponse({ description: "Current LLM provider configuration and task routing." })
  getConfig(): Promise<AiLlmConfigResponse> {
    return this.aiService.getLlmConfig();
  }

  @Patch()
  @ApiOkResponse({ description: "Updated LLM configuration (takes effect immediately)." })
  updateConfig(@Body() dto: AiLlmConfigUpdate): Promise<AiLlmConfigResponse> {
    return this.aiService.updateLlmConfig(dto);
  }

  @Get("ollama-models")
  @ApiOkResponse({ description: "Models available in the local Ollama instance." })
  getOllamaModels(): Promise<AiOllamaModelsResponse> {
    return this.aiService.getOllamaModels();
  }

  @Get("provider-models")
  @ApiOkResponse({ description: "Available chat models for each configured provider." })
  getProviderModels(): Promise<Record<string, string[]>> {
    return this.aiService.getProviderModels();
  }
}
