import { Body, Controller, Delete, Get, HttpCode, HttpStatus, Param, Post, UseGuards } from "@nestjs/common";
import { ApiBearerAuth, ApiCreatedResponse, ApiNoContentResponse, ApiOkResponse, ApiTags } from "@nestjs/swagger";
import { CurrentUser } from "../../common/auth/current-user.decorator";
import { JwtAuthGuard } from "../../common/auth/jwt-auth.guard";
import { JwtUser } from "../../common/auth/types";
import { CreateWorkspaceDto } from "./dto/create-workspace.dto";
import { InviteMemberDto } from "./dto/invite-member.dto";
import { WorkspacesService } from "./workspaces.service";

@ApiTags("workspaces")
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller("workspaces")
export class WorkspacesController {
  constructor(private readonly workspacesService: WorkspacesService) {}

  @Post()
  @ApiCreatedResponse({ description: "Creates a workspace for the current user." })
  create(@CurrentUser() user: JwtUser, @Body() dto: CreateWorkspaceDto) {
    return this.workspacesService.create(user.sub, dto);
  }

  @Get()
  @ApiOkResponse({ description: "Lists workspaces where the current user is a member." })
  list(@CurrentUser() user: JwtUser) {
    return this.workspacesService.listForUser(user.sub);
  }

  @Get(":workspaceId/members")
  @ApiOkResponse({ description: "Lists members of a workspace." })
  listMembers(@Param("workspaceId") workspaceId: string, @CurrentUser() user: JwtUser) {
    return this.workspacesService.listMembers(workspaceId, user.sub);
  }

  @Post(":workspaceId/members")
  @ApiCreatedResponse({ description: "Invites a user to the workspace by email." })
  inviteMember(
    @Param("workspaceId") workspaceId: string,
    @CurrentUser() user: JwtUser,
    @Body() dto: InviteMemberDto
  ) {
    return this.workspacesService.inviteMember(workspaceId, user.sub, dto);
  }

  @Delete(":workspaceId/members/:userId")
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiNoContentResponse({ description: "Removes a member from the workspace." })
  async removeMember(
    @Param("workspaceId") workspaceId: string,
    @Param("userId") targetUserId: string,
    @CurrentUser() user: JwtUser
  ) {
    await this.workspacesService.removeMember(workspaceId, user.sub, targetUserId);
  }
}
