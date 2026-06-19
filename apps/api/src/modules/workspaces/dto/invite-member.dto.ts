import { ApiProperty } from "@nestjs/swagger";
import { IsEmail, IsIn } from "class-validator";
import { Role } from "@prisma/client";

export class InviteMemberDto {
  @ApiProperty({ example: "collaborator@example.com" })
  @IsEmail()
  email!: string;

  @ApiProperty({ enum: ["COLLABORATOR", "REVIEWER"] })
  @IsIn(["COLLABORATOR", "REVIEWER"])
  role!: Role;
}
