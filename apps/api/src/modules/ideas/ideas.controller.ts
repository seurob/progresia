import { Body, Controller, Get, Param, Post, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiCreatedResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
import { CreateIdeaDto } from "./dto/create-idea.dto";
import { IdeasService } from "./ideas.service";

@ApiTags("ideas")
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller("ideas")
export class IdeasController {
  constructor(private readonly ideasService: IdeasService) {}

  @Post()
  @ApiCreatedResponse({ description: "Creates or replaces idea intake for a project." })
  create(@CurrentUser() user: JwtUser, @Body() dto: CreateIdeaDto) {
    return this.ideasService.upsert(user.sub, dto);
  }

  @Get("project/:projectId")
  @ApiOkResponse({ description: "Returns idea intake for a project." })
  findByProject(@CurrentUser() user: JwtUser, @Param("projectId") projectId: string) {
    return this.ideasService.findByProject(user.sub, projectId);
  }
}
