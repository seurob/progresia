import { Processor, WorkerHost } from "@nestjs/bullmq";
import { ModuleRef } from "@nestjs/core";
import { Job } from "bullmq";
import { AiJobData, AiJobName, AI_QUEUE } from "./jobs.types";

@Processor(AI_QUEUE)
export class AiJobsProcessor extends WorkerHost {
  constructor(private readonly moduleRef: ModuleRef) {
    super();
  }

  async process(job: Job<AiJobData, unknown, AiJobName>): Promise<unknown> {
    const { userId, projectId } = job.data;

    switch (job.name) {
      case "generate-requirements": {
        const { SpecificationsService } = await import("../specifications/specifications.service");
        const svc = this.moduleRef.get(SpecificationsService, { strict: false });
        return svc.generateRequirements(userId, projectId);
      }
      case "generate-openspec": {
        const { SpecificationsService } = await import("../specifications/specifications.service");
        const svc = this.moduleRef.get(SpecificationsService, { strict: false });
        return svc.generateOpenSpec(userId, projectId);
      }
      case "generate-code": {
        const { ArtifactsService } = await import("../artifacts/artifacts.service");
        const svc = this.moduleRef.get(ArtifactsService, { strict: false });
        return svc.generateCode(userId, projectId);
      }
      case "recommend-architecture": {
        const { SpecificationsService } = await import("../specifications/specifications.service");
        const svc = this.moduleRef.get(SpecificationsService, { strict: false });
        return svc.generateArchitecture(userId, projectId);
      }
      case "generate-issues": {
        const { SpecificationsService } = await import("../specifications/specifications.service");
        const svc = this.moduleRef.get(SpecificationsService, { strict: false });
        return svc.generateIssues(userId, projectId);
      }
      case "generate-tutorial": {
        const { SpecificationsService } = await import("../specifications/specifications.service");
        const svc = this.moduleRef.get(SpecificationsService, { strict: false });
        return svc.generateTutorial(userId, projectId);
      }
      default:
        throw new Error(`Unknown job name: ${job.name}`);
    }
  }
}
