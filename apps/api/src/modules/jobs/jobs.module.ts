import { BullModule } from "@nestjs/bullmq";
import { Module } from "@nestjs/common";
import { ModuleRef } from "@nestjs/core";
import { AiJobsProcessor } from "./ai-jobs.processor";
import { JobsController } from "./jobs.controller";
import { JobsService } from "./jobs.service";
import { AI_QUEUE } from "./jobs.types";

@Module({
  imports: [BullModule.registerQueue({ name: AI_QUEUE })],
  providers: [
    {
      provide: AiJobsProcessor,
      useFactory: (moduleRef: ModuleRef) => new AiJobsProcessor(moduleRef),
      inject: [ModuleRef]
    },
    JobsService
  ],
  controllers: [JobsController],
  exports: [JobsService, BullModule]
})
export class JobsModule {}
