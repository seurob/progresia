import { Body, Controller, Get, Param, Post, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiCreatedResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
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
}
