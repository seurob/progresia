import { Injectable, NotFoundException } from "@nestjs/common";
import { InjectQueue } from "@nestjs/bullmq";
import { Queue } from "bullmq";
import { AI_QUEUE } from "./jobs.types";

export interface JobStatus {
  id: string | undefined;
  name: string;
  status: string;
  progress: unknown;
  result?: unknown;
  failReason?: string;
}

@Injectable()
export class JobsService {
  constructor(@InjectQueue(AI_QUEUE) private readonly aiQueue: Queue) {}

  async getStatus(jobId: string): Promise<JobStatus> {
    const job = await this.aiQueue.getJob(jobId);
    if (!job) throw new NotFoundException(`Job ${jobId} not found`);

    const state = await job.getState();
    return {
      id: job.id,
      name: job.name,
      status: state,
      progress: job.progress,
      result: state === "completed" ? job.returnvalue : undefined,
      failReason: state === "failed" ? job.failedReason : undefined
    };
  }
}
