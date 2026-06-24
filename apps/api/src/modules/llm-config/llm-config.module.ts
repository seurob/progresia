import { Module } from "@nestjs/common";
import { AiServiceModule } from "../ai-service/ai-service.module";
import { LlmConfigController } from "./llm-config.controller";

@Module({
  imports: [AiServiceModule],
  controllers: [LlmConfigController]
})
export class LlmConfigModule {}
