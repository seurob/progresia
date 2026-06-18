import { Controller, Get, Param, Post, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiCreatedResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
import { ArtifactsService } from "./artifacts.service";

@ApiTags("artifacts")
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller("artifacts")
export class ArtifactsController {
  constructor(private readonly artifactsService: ArtifactsService) {}

  @Post("project/:projectId/generate")
  @ApiCreatedResponse({ description: "Generates and stores an artifact bundle manifest." })
  generate(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.artifactsService.generateBundle(user.sub, projectId);
  }

  @Get("project/:projectId")
  @ApiOkResponse({ description: "Lists artifact bundles for a project." })
  listByProject(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.artifactsService.listByProject(user.sub, projectId);
  }
}
