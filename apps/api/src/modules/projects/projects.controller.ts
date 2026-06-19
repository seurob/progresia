import { Body, Controller, Delete, Get, HttpCode, HttpStatus, Param, Post, Put, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiCreatedResponse, ApiNoContentResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
import { CreateProjectDto } from "./dto/create-project.dto";
import { UpdateProjectDto } from "./dto/update-project.dto";
import { ProjectsService } from "./projects.service";

@ApiTags("projects")
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller("projects")
export class ProjectsController {
  constructor(private readonly projectsService: ProjectsService) {}

  @Post()
  @ApiCreatedResponse({ description: "Creates a project in an accessible workspace." })
  create(@CurrentUser() user: JwtUser, @Body() dto: CreateProjectDto) {
    return this.projectsService.create(user.sub, dto);
  }

  @Get()
  @ApiOkResponse({ description: "Lists projects visible to the current user." })
  list(@CurrentUser() user: JwtUser) {
    return this.projectsService.listForUser(user.sub);
  }

  @Get(":id")
  @ApiOkResponse({ description: "Returns a project by id if accessible." })
  findOne(@CurrentUser() user: JwtUser, @Param("id") id: string) {
    return this.projectsService.findOne(user.sub, id);
  }

  @Put(":id")
  @ApiOkResponse({ description: "Updates a project by id if accessible." })
  update(@CurrentUser() user: JwtUser, @Param("id") id: string, @Body() dto: UpdateProjectDto) {
    return this.projectsService.update(user.sub, id, dto);
  }

  @Delete(":id")
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiNoContentResponse({ description: "Deletes a project and all its associated data." })
  remove(@CurrentUser() user: JwtUser, @Param("id") id: string) {
    return this.projectsService.remove(user.sub, id);
  }
}
