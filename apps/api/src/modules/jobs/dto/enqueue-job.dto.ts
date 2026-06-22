import { ApiProperty } from "@nestjs/swagger";
import { IsString, MinLength } from "class-validator";

export class EnqueueJobDto {
  @ApiProperty({ description: "UUID or slug of the project" })
  @IsString()
  @MinLength(1)
  projectId!: string;
}
