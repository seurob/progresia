import { BullModule } from "@nestjs/bullmq";
import { Module } from "@nestjs/common";
import { AiServiceModule } from "../ai-service/ai-service.module";
import { AiJobsProcessor } from "./ai-jobs.processor";
import { JobsController } from "./jobs.controller";
import { JobsService } from "./jobs.service";
import { AI_QUEUE } from "./jobs.types";

@Module({
  imports: [BullModule.registerQueue({ name: AI_QUEUE }), AiServiceModule],
  providers: [AiJobsProcessor, JobsService],
  controllers: [JobsController],
  exports: [JobsService, BullModule]
})
export class JobsModule {}
