import { Body, Controller, Get, Header, HttpCode, Param, Post, Res, UseGuards } from "@nestjs/common";
import { InjectQueue } from "@nestjs/bullmq";
import { ApiBearerAuth, ApiAcceptedResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { Response } from "express";
import { Queue } from "bullmq";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
import { AiServiceClient } from "../ai-service/ai-service.client";
import { EnqueueJobDto } from "./dto/enqueue-job.dto";
import { JobsService } from "./jobs.service";
import { AI_QUEUE, AiJobName } from "./jobs.types";

@ApiTags("jobs")
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller("jobs")
export class JobsController {
  constructor(
    @InjectQueue(AI_QUEUE) private readonly aiQueue: Queue,
    private readonly jobsService: JobsService,
    private readonly aiClient: AiServiceClient
  ) {}

  private async enqueue(user: JwtUser, dto: EnqueueJobDto, name: AiJobName) {
    const job = await this.aiQueue.add(name, { userId: user.sub, projectId: dto.projectId });
    return { jobId: job.id };
  }

  @Post("generate-requirements")
  @HttpCode(202)
  @ApiAcceptedResponse({ description: "Requirements generation job queued." })
  generateRequirements(@CurrentUser() user: JwtUser, @Body() dto: EnqueueJobDto) {
    return this.enqueue(user, dto, "generate-requirements");
  }

  @Post("generate-openspec")
  @HttpCode(202)
  @ApiAcceptedResponse({ description: "OpenSpec generation job queued." })
  generateOpenSpec(@CurrentUser() user: JwtUser, @Body() dto: EnqueueJobDto) {
    return this.enqueue(user, dto, "generate-openspec");
  }

  @Post("generate-code")
  @HttpCode(202)
  @ApiAcceptedResponse({ description: "Code generation job queued." })
  generateCode(@CurrentUser() user: JwtUser, @Body() dto: EnqueueJobDto) {
    return this.enqueue(user, dto, "generate-code");
  }

  @Post("recommend-architecture")
  @HttpCode(202)
  @ApiAcceptedResponse({ description: "Architecture recommendation job queued." })
  recommendArchitecture(@CurrentUser() user: JwtUser, @Body() dto: EnqueueJobDto) {
    return this.enqueue(user, dto, "recommend-architecture");
  }

  @Post("generate-issues")
  @HttpCode(202)
  @ApiAcceptedResponse({ description: "GitHub Issues generation job queued." })
  generateIssues(@CurrentUser() user: JwtUser, @Body() dto: EnqueueJobDto) {
    return this.enqueue(user, dto, "generate-issues");
  }

  @Post("generate-tutorial")
  @HttpCode(202)
  @ApiAcceptedResponse({ description: "Tutorial generation job queued." })
  generateTutorial(@CurrentUser() user: JwtUser, @Body() dto: EnqueueJobDto) {
    return this.enqueue(user, dto, "generate-tutorial");
  }

  @Post("suggest-features")
  @ApiOkResponse({ description: "AI-generated feature suggestions for a project idea." })
  suggestFeatures(
    @Body() body: { sector: string; problem: string; targetUsers: string }
  ) {
    return this.aiClient.suggestFeatures({
      sector: body.sector,
      problem: body.problem,
      target_users: body.targetUsers
    });
  }

  @Get(":jobId")
  @Header("Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate")
  @Header("Pragma", "no-cache")
  @Header("Expires", "0")
  @ApiOkResponse({ description: "Returns the status of a job." })
  getStatus(@Param("jobId") jobId: string, @Res({ passthrough: true }) res: Response) {
    res.setHeader("ETag", `"job-${jobId}-${Date.now()}"`);
    return this.jobsService.getStatus(jobId);
  }
}
