import { Body, Controller, Get, Param, Post, Res, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiCreatedResponse, ApiOkResponse, ApiProduces, ApiTags } from "@nestjs/swagger";
import { Response } from "express";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
import { PushToGithubDto } from "./dto/push-to-github.dto";
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

  @Post("project/:projectId/generate-code")
  @ApiCreatedResponse({ description: "Generates fullstack code scaffold from latest OpenSpec." })
  generateCode(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.artifactsService.generateCode(user.sub, projectId);
  }

  @Post(":bundleId/push-to-github")
  @ApiCreatedResponse({ description: "Creates a GitHub repo and pushes the generated code as an initial commit. The token is used transiently and never stored." })
  pushToGithub(
    @CurrentUser() user: JwtUser,
    @Param("bundleId") bundleId: string,
    @Body() dto: PushToGithubDto
  ) {
    return this.artifactsService.pushToGithub(user.sub, bundleId, dto);
  }

  @Get(":bundleId/export-url")
  @ApiOkResponse({ description: "Uploads the ZIP to MinIO and returns a pre-signed download URL (1 hour TTL)." })
  exportUrl(@CurrentUser() user: JwtUser, @Param("bundleId") bundleId: string) {
    return this.artifactsService.exportZipUrl(user.sub, bundleId);
  }

  @Get(":bundleId/export")
  @ApiProduces("application/zip")
  @ApiOkResponse({ description: "Downloads the artifact bundle as a ZIP file." })
  async export(
    @CurrentUser() user: JwtUser,
    @Param("bundleId") bundleId: string,
    @Res() res: Response
  ) {
    const buffer = await this.artifactsService.exportZip(user.sub, bundleId);

    res.set({
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="progresia-artifact-${bundleId}.zip"`,
      "Content-Length": buffer.length.toString()
    });

    res.send(buffer);
  }
}
