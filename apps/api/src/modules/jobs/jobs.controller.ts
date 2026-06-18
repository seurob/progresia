import { Body, Controller, Get, HttpCode, Param, Post, UseGuards } from "@nestjs/common";
import { InjectQueue } from "@nestjs/bullmq";
import { ApiBearerAuth, ApiAcceptedResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { Queue } from "bullmq";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
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
    private readonly jobsService: JobsService
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

  @Get(":jobId")
  @ApiOkResponse({ description: "Returns the status of a job." })
  getStatus(@Param("jobId") jobId: string) {
    return this.jobsService.getStatus(jobId);
  }
}
