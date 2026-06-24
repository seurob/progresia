import { Body, Controller, Get, Param, Post, Res, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiCreatedResponse, ApiOkResponse, ApiProduces, ApiTags } from "@nestjs/swagger";
import { Response } from "express";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
import { CreateSpecificationDto } from "./dto/create-specification.dto";
import { SpecificationsService } from "./specifications.service";

@ApiTags("specifications")
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller("specifications")
export class SpecificationsController {
  constructor(private readonly specificationsService: SpecificationsService) {}

  @Post()
  @ApiCreatedResponse({ description: "Creates a project specification." })
  create(@CurrentUser() user: JwtUser, @Body() dto: CreateSpecificationDto) {
    return this.specificationsService.create(user.sub, dto);
  }

  @Get("project/:projectId")
  @ApiOkResponse({ description: "Lists specifications for a project." })
  listByProject(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.specificationsService.listByProject(user.sub, projectId);
  }

  @Get(":specificationId/export-pdf")
  @ApiProduces("application/pdf")
  @ApiOkResponse({ description: "Downloads a generated specification as a PDF document." })
  async exportPdf(
    @CurrentUser() user: JwtUser,
    @Param("specificationId") specificationId: string,
    @Res() res: Response
  ) {
    const { filename, buffer } = await this.specificationsService.exportPdf(user.sub, specificationId);

    res.set({
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Content-Length": buffer.length.toString()
    });

    res.send(buffer);
  }

  @Get(":specificationId/export-md")
  @ApiProduces("text/markdown")
  @ApiOkResponse({ description: "Downloads a generated specification as a Markdown document." })
  async exportMd(
    @CurrentUser() user: JwtUser,
    @Param("specificationId") specificationId: string,
    @Res() res: Response
  ) {
    const { filename, content } = await this.specificationsService.exportMd(user.sub, specificationId);
    const buffer = Buffer.from(content, "utf-8");

    res.set({
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Content-Length": buffer.length.toString()
    });

    res.send(buffer);
  }

  @Post("project/:projectId/generate-requirements")
  @ApiCreatedResponse({ description: "Generates and stores a Requirements specification through the AI service." })
  generateRequirements(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.specificationsService.generateRequirements(user.sub, projectId);
  }

  @Post("project/:projectId/generate-openspec")
  @ApiCreatedResponse({ description: "Generates and stores an OpenSpec specification through the AI service." })
  generateOpenSpec(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.specificationsService.generateOpenSpec(user.sub, projectId);
  }

  @Post("project/:projectId/propose-tech")
  @ApiCreatedResponse({ description: "Returns 3 tech stack proposals for the project. Synchronous — fast catalog fallback guarantees sub-200ms response." })
  proposeTech(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.specificationsService.proposeTech(user.sub, projectId);
  }
}
