import { ApiProperty } from "@nestjs/swagger";
import { IsString, MinLength } from "class-validator";

export class CreateWorkspaceDto {
  @ApiProperty({ example: "ProgresIA Lab" })
  @IsString()
  @MinLength(2)
  name!: string;
}
